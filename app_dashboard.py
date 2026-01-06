import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
try:
    from excel_report_generator import generate_excel_report
except ImportError as e:
    # 디버깅을 위한 상세 에러 출력
    st.error(f"라이브러리 로딩 오류 (Excel Report): {e}")
    # 디버깅 정보 출력
    import os
    st.write(f"Current Directory: {os.getcwd()}")
    st.write(f"Directory Content: {os.listdir()}")
    generate_excel_report = None
except Exception as e:
    st.error(f"알 수 없는 오류 (Excel Report): {e}")
    generate_excel_report = None
from ai_analyzer import generate_ai_insight

# Page Config
st.set_page_config(page_title="사전영업 대시보드", page_icon="📊", layout="wide")

st.title("📊 사전영업 데이터 분석 대시보드")
st.markdown("---")

@st.cache_data
def load_data(file_source, _file_mtime=None):
    """
    Load data from Excel file with cache busting based on file modification time.
    _file_mtime parameter ensures cache is invalidated when file is updated.
    """
    try:
        # Load '고객설문지DB' sheet
        df = pd.read_excel(file_source, sheet_name='고객설문지DB', header=0)
        
        # Filter valid rows (Q1 existence)
        q1_col_name = df.columns[4] 
        df = df[df[q1_col_name].notna()]
        
        return df
    except Exception as e:
        # st.error(f"데이터 로드 중 오류 발생: {e}") 
        return None

# Sidebar File Uploader
st.sidebar.header("📂 데이터 파일 (Data Source)")
uploaded_file = st.sidebar.file_uploader("엑셀 파일 업로드", type=['xlsx'])

if uploaded_file:
    df = load_data(uploaded_file)
    st.sidebar.success("업로드된 파일을 사용합니다.")
else:
    # Use relative path for Cross-platform / Cloud compatibility
    import os
    # Filename in GitHub is 'DB.xlsx' inside '설문조사 DB' folder
    base_dir = os.path.dirname(__file__)
    default_path = os.path.join(base_dir, '설문조사 DB', 'DB.xlsx')
    
    # Try alternate if not found (for local backwards compatibility)
    if not os.path.exists(default_path):
        default_path = os.path.join(base_dir, '설문조사 DB', 'DEFINE_DB.xlsx')
    
    # Get file modification time for cache busting
    if os.path.exists(default_path):
        file_mtime = os.path.getmtime(default_path)
        df = load_data(default_path, _file_mtime=file_mtime)
    else:
        df = None
        st.error("데이터 파일을 찾을 수 없습니다.")

if df is not None:
    # --- Columns Mapping ---
    cols = df.columns.tolist()
    
    col_map = {
        cols[1]: 'Date',
        cols[2]: 'Manager',
        cols[3]: 'Spot',
        cols[4]: 'Q1_Awareness',
        cols[5]: 'Q2_Channel',
        cols[6]: 'Q3_Pros',
        cols[7]: 'Q4_Purpose',
        cols[8]: 'Q5_Type',
        cols[9]: 'Q6_Intent',
        cols[10]: 'Q7_Subscription',
        cols[11]: 'Q8_Price',
        cols[12]: 'Addr_City',
        cols[13]: 'Addr_Gu',
        cols[14]: 'Addr_Dong',
        cols[16]: 'Gender',
        cols[17]: 'Grade'
    }
    
    df.rename(columns=col_map, inplace=True)

    # --- Data Cleaning & Mapping ---
    # Ensure Numeric
    for c in ['Q6_Intent', 'Q4_Purpose', 'Q5_Type', 'Q1_Awareness', 'Q2_Channel', 'Q7_Subscription', 'Q8_Price', 'Gender']:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce')

    # Date
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

    # Mapping Dictionaries
    q1_map = {1: '잘 알고있다', 2: '들어본 적 있다', 3: '처음 알았다'}
    q2_map = {1: '외부홍보', 2: '부동산', 3: '가족/지인', 4: '옥외광고', 5: '홈페이지', 6: '온라인광고', 7: '기사'}
    q3_map = {1:'브랜드', 2:'주거쾌적성', 3:'교통환경', 4:'교육환경', 5:'투자가치'}
    q4_map = {1: '실거주', 2: '투자', 3: '실거주+투자'}
    q5_map = {1: '59㎡', 2: '74㎡', 3: '75㎡', 4: '84㎡'}
    q7_map = {1: '특별공급', 2: '1순위', 3: '2순위', 4: '무응답'}
    q8_map = {
        1: '11.5~12억', 2: '12~12.5억', 3: '12.5~13억', 4: '13~13.5억',
        5: '14~14.5억', 6: '14.5~15억', 7: '15~15.5억', 8: '15.5~16억'
    }
    gender_map = {1: '남성', 2: '여성'}

    # Apply Mappings
    if 'Q1_Awareness' in df.columns: df['Q1_Label'] = df['Q1_Awareness'].map(q1_map).fillna('기타')
    if 'Q2_Channel' in df.columns: df['Q2_Label'] = df['Q2_Channel'].map(q2_map).fillna('기타')
    if 'Q3_Pros' in df.columns: df['Q3_Label'] = df['Q3_Pros'].map(q3_map).fillna('기타')
    if 'Q4_Purpose' in df.columns: df['Q4_Label'] = df['Q4_Purpose'].map(q4_map).fillna('기타')
    if 'Q5_Type' in df.columns: df['Q5_Label'] = df['Q5_Type'].map(q5_map).fillna('기타')
    if 'Q7_Subscription' in df.columns: df['Q7_Label'] = df['Q7_Subscription'].map(q7_map).fillna('기타')
    if 'Q8_Price' in df.columns: df['Q8_Label'] = df['Q8_Price'].map(q8_map).fillna('기타')
    if 'Gender' in df.columns: df['Gender_Label'] = df['Gender'].map(gender_map).fillna('미기재')

    # --- Sidebar Filters ---
    st.sidebar.header("🔍 상세 필터 (Filters)")
    
    # Date Filter
    if 'Date' in df.columns:
        valid_dates = df['Date'].dropna()
        if not valid_dates.empty:
            min_d, max_d = valid_dates.min(), valid_dates.max()
            date_range = st.sidebar.date_input("📅 접수 기간", [min_d, max_d])
            if len(date_range) == 2:
                df = df[(df['Date'] >= pd.Timestamp(date_range[0])) & (df['Date'] <= pd.Timestamp(date_range[1]))]

    # Spot Filter
    if 'Spot' in df.columns:
        spots = df['Spot'].dropna().unique()
        sel_spot = st.sidebar.multiselect("🚩 영업 거점", spots)
        if sel_spot:
            df = df[df['Spot'].isin(sel_spot)]
            
    # Manager Filter
    if 'Manager' in df.columns:
        managers = df['Manager'].dropna().unique()
        sel_mgr = st.sidebar.multiselect("👤 담당자/조", managers)
        if sel_mgr:
            df = df[df['Manager'].isin(sel_mgr)]

    # Preserve a copy of df before Sidebar Region Filters
    filtered_base_df = df.copy()

    # Region Filter (Residense) for Sidebar (Visual only for Main Tab usually)
    if 'Addr_City' in df.columns:
        cities = df['Addr_City'].dropna().unique()
        sel_city = st.sidebar.multiselect("🏠 거주지 (시/도)", cities)
        if sel_city:
            df = df[df['Addr_City'].isin(sel_city)]
            
    if 'Addr_Gu' in df.columns:
        # Show Gu only available in current df details (dynamic)
        gus = df['Addr_Gu'].dropna().unique()
        sel_gu = st.sidebar.multiselect("🏠 거주지 (시/군/구)", gus)
        if sel_gu:
            df = df[df['Addr_Gu'].isin(sel_gu)]
    
    # --- Excel Report Download Section ---
    st.sidebar.markdown("---")
    st.sidebar.header("📥 보고서 내보내기")
    
    report_type_options = {
        "📊 전체 보고서 (데이터 + 요약 + 차트)": "전체",
        "📋 데이터만 (원본 + 통계 요약)": "데이터만",
    }
    
    selected_report = st.sidebar.selectbox(
        "보고서 유형 선택",
        list(report_type_options.keys())
    )
    
    if st.sidebar.button("📥 엑셀 보고서 생성", type="primary", use_container_width=True):
        with st.sidebar:
            with st.spinner('보고서 생성 중...'):
                try:
                    # 현재 필터링된 데이터로 보고서 생성
                    report_type = report_type_options[selected_report]
                    
                    if generate_excel_report is None:
                        st.error("엑셀 생성 모듈이 로드되지 않았습니다. 상단 에러 메시지를 확인해주세요.")
                        st.stop()
                        
                    excel_file = generate_excel_report(df, report_type)
                    
                    # 세션 상태에 저장 (BytesIO 대신 bytes 바이트 문자열로 저장)
                    st.session_state['generated_excel'] = excel_file.getvalue()
                    st.session_state['generated_filename'] = f"PreSales_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
                    st.session_state['last_filter_hash'] = hash(str(df.index.tolist())) # 데이터 변경 감지용 (단순화)
                    
                    st.success("✅ 생성 완료! 아래 버튼을 눌러 다운로드하세요.")
                except Exception as e:
                    st.error(f"⚠️ 오류 발생: {str(e)}")
                    st.info("데이터만 옵션을 시도해보세요.")

    # 생성된 파일이 있으면 다운로드 버튼 표시
    if 'generated_excel' in st.session_state and st.session_state['generated_excel'] is not None:
        st.sidebar.download_button(
            label="⬇️ 엑셀 파일 다운로드",
            data=st.session_state['generated_excel'],
            file_name=st.session_state['generated_filename'],
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key=f"dl_{st.session_state['generated_filename']}",
            use_container_width=True
        )

    # --- Metrics ---
    st.header("1. 핵심 현황 (Key Metrics)")
    
    total = len(df)
    avg_intent = df['Q6_Intent'].mean() if 'Q6_Intent' in df.columns else 0
    high_intent = len(df[df['Q6_Intent'] >= 6]) if 'Q6_Intent' in df.columns else 0
    
    # Calculate S+A Grade Count if 'Grade' column exists
    sa_count = high_intent
    sa_label = "가망 고객 (S급)"
    sa_delta = "의향 6점 이상"
    
    if 'Grade' in df.columns:
        # Grade 1(S), 2(A)
        sa_count = len(df[df['Grade'].isin([1, 2])])
        sa_label = "가망 고객 (S/A급)"
        sa_delta = "전체 대비 비율"
        
    conversion = (sa_count / total * 100) if total > 0 else 0
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("총 응답 수", f"{total:,} 건", "Total Leads")
    c2.metric("평균 분양 의향 (Q6)", f"{avg_intent:.1f} 점", "/ 7.0 만점")
    c3.metric(sa_label, f"{sa_count:,} 명", "S+A 등급 합계")
    c4.metric("잠재 전환율", f"{conversion:.1f} %", sa_delta)
    
    st.markdown("---")

    # --- Helper: Weekly Period Calculator (Mon-Sun) ---
    def get_weekly_period(date_series):
        """
        Groups dates into weekly buckets (Monday-Sunday).
        Returns a Series of strings: "1주차 (12/08~12/14)"
        """
        if date_series.empty:
            return date_series.astype(str)

        # 1. Find the global minimum date to determine Week 1's anchor
        # Ensure we anchor to the Monday of the week containing the min date
        min_date = date_series.min()
        # weekday(): Mon=0, Sun=6. 
        # Subtract current weekday to get Monday.
        start_anchor = min_date - pd.Timedelta(days=min_date.weekday())
        
        # 2. Calculate offset in weeks
        # We need to apply the logic row by row or vectorized
        # Vectorized: (date - anchor).dt.days // 7 + 1
        # Only works if date_series is datetime64
        
        dates = pd.to_datetime(date_series)
        days_diff = (dates - start_anchor).dt.days
        week_nums = (days_diff // 7) + 1
        
        # 3. Calculate Start/End date for each week num
        # Week N Start = Anchor + (N-1)*7
        # Week N End   = Week N Start + 6
        
        results = []
        for d, w in zip(dates, week_nums):
            if pd.isna(d):
                results.append("미확인")
                continue
                
            w_start = start_anchor + pd.Timedelta(days=(w-1)*7)
            w_end = w_start + pd.Timedelta(days=6)
            
            period_str = f"{w_start.strftime('%m/%d')}~{w_end.strftime('%m/%d')}"
            results.append(f"{w}주차 ({period_str})")
            
        return pd.Series(results, index=date_series.index)
    
    # --- Reusable Analysis Function ---
    def draw_analysis_tabs(target_df, key_suffix=""):
        if target_df.empty:
            st.warning("분석할 데이터가 없습니다.")
            return

        # Sub-tabs within the analysis view
        t1, t2, t3, t4, t5 = st.tabs(["📊 설문 문항 통합 분석", "🌍 인구/지역 통계", "🏆 상담 등급 분석", "📈 영업 성과 분석", "📅 주차별 추이"])
        
        # Tab 1: Combined Survey (Q1~Q8)
        with t1:
            st.markdown("#### 💡 설문 응답 종합 분석 (Q1~Q8)")
            
            # Row 1: Q1, Q2, Q3
            r1_1, r1_2, r1_3 = st.columns(3)
            with r1_1:
                st.markdown("##### Q1. 사업지 인지도")
                if 'Q1_Label' in target_df.columns:
                     counts = target_df['Q1_Label'].value_counts().reset_index()
                     counts.columns = ['Answer', 'Count']
                     fig = px.pie(counts, values='Count', names='Answer', hole=0.4)
                     fig.update_traces(textposition='inside', textinfo='percent+label')
                     st.plotly_chart(fig, use_container_width=True, key=f"q1_{key_suffix}")
            with r1_2:
                st.markdown("##### Q2. 정보 습득 경로")
                if 'Q2_Label' in target_df.columns:
                     counts = target_df['Q2_Label'].value_counts().reset_index()
                     counts.columns = ['Channel', 'Count']
                     fig = px.bar(counts, x='Channel', y='Count', text='Count')
                     st.plotly_chart(fig, use_container_width=True, key=f"q2_{key_suffix}")
            with r1_3:
                st.markdown("##### Q3. 만족 장점")
                if 'Q3_Label' in target_df.columns:
                    counts = target_df['Q3_Label'].value_counts().reset_index()
                    counts.columns = ['Pros', 'Count']
                    fig = px.bar(counts, x='Pros', y='Count', text='Count')
                    st.plotly_chart(fig, use_container_width=True, key=f"q3_{key_suffix}")

            st.markdown("---")
            
            # Row 2: Q4, Q5, Q6
            r2_1, r2_2, r2_3 = st.columns(3)
            with r2_1:
                st.markdown("##### Q4. 구매 목적")
                if 'Q4_Label' in target_df.columns:
                    counts = target_df['Q4_Label'].value_counts().reset_index()
                    counts.columns = ['Purpose', 'Count']
                    fig = px.bar(counts, x='Purpose', y='Count', color='Purpose', text='Count')
                    st.plotly_chart(fig, use_container_width=True, key=f"q4_{key_suffix}")
            with r2_2:
                st.markdown("##### Q5. 선호 평형")
                if 'Q5_Label' in target_df.columns:
                    counts = target_df['Q5_Label'].value_counts().reset_index()
                    counts.columns = ['Type', 'Count']
                    fig = px.pie(counts, values='Count', names='Type', hole=0.4)
                    fig.update_traces(textposition='inside', textinfo='percent+label')
                    st.plotly_chart(fig, use_container_width=True, key=f"q5_{key_suffix}")
            with r2_3:
                st.markdown("##### Q6. 계약 의향 (1~7점)")
                if 'Q6_Intent' in target_df.columns:
                    q6_counts = target_df['Q6_Intent'].value_counts().sort_index().reset_index()
                    q6_counts.columns = ['Score', 'Count']
                    fig = px.bar(q6_counts, x='Score', y='Count', text='Count')
                    fig.update_xaxes(dtick=1)
                    st.plotly_chart(fig, use_container_width=True, key=f"q6_{key_suffix}")

            st.markdown("---")

            # Row 3: Q7, Q8
            r3_1, r3_2, r3_3 = st.columns(3)
            with r3_1:
                st.markdown("##### Q7. 청약 예정")
                if 'Q7_Label' in target_df.columns:
                    counts = target_df['Q7_Label'].value_counts().reset_index()
                    counts.columns = ['Type', 'Count']
                    fig = px.pie(counts, values='Count', names='Type')
                    fig.update_traces(textposition='inside', textinfo='percent+label')
                    st.plotly_chart(fig, use_container_width=True, key=f"q7_{key_suffix}")
            with r3_2:
                st.markdown("##### Q8. 희망 분양가")
                if 'Q8_Label' in target_df.columns:
                    order = list(q8_map.values())
                    counts = target_df['Q8_Label'].value_counts().reindex(order).fillna(0).reset_index()
                    counts.columns = ['PriceRange', 'Count']
                    fig = px.bar(counts, x='PriceRange', y='Count', text='Count')
                    st.plotly_chart(fig, use_container_width=True, key=f"q8_{key_suffix}")

        # Tab 2: Demographics
        with t2:
            st.markdown("#### 🌍 인구/지역 통계")
            
            st.markdown("##### 일별 및 누계 접수 추이")
            if 'Date' in target_df.columns:
                import plotly.graph_objects as go
                from plotly.subplots import make_subplots
                
                daily = target_df.groupby(target_df['Date'].dt.date).size().reset_index(name='Count')
                daily.columns = ['Date', 'Count']
                daily = daily.sort_values('Date')
                
                # Calculate Cumulative Sum
                daily['Cumulative'] = daily['Count'].cumsum()
                
                # Format Date to Korean string
                daily['Date_Str'] = pd.to_datetime(daily['Date']).dt.strftime('%m월 %d일')
                
                # Create figure with secondary y-axis
                fig = make_subplots(specs=[[{"secondary_y": True}]])
                
                # Add Daily Bar
                fig.add_trace(
                    go.Bar(x=daily['Date_Str'], y=daily['Count'], name="일별 접수", text=daily['Count'], textposition='auto', marker_color='#636EFA', opacity=0.7),
                    secondary_y=False,
                )
                
                # Add Cumulative Line
                fig.add_trace(
                    go.Scatter(x=daily['Date_Str'], y=daily['Cumulative'], name="누계 합계", mode='lines+markers+text', 
                               text=daily['Cumulative'], textposition='top center', line=dict(color='#EF553B', width=3)),
                    secondary_y=True,
                )
                
                fig.update_layout(
                    title_text="일별 접수 및 누계 현황",
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                
                fig.update_xaxes(title_text="접수일자")
                fig.update_yaxes(title_text="일별 접수 (건)", secondary_y=False)
                fig.update_yaxes(title_text="누계 합계 (건)", secondary_y=True)
                
                st.plotly_chart(fig, use_container_width=True, key=f"date_{key_suffix}")
            
            st.markdown("#### 거주 지역 (Top 20)")
            if 'Addr_City' in target_df.columns and 'Addr_Gu' in target_df.columns:
                 target_df['Full_Addr'] = target_df['Addr_City'].astype(str) + " " + target_df['Addr_Gu'].astype(str)
                 counts = target_df['Full_Addr'].value_counts().head(20).reset_index()
                 counts.columns = ['Address', 'Count']
                 fig = px.bar(counts, x='Address', y='Count', text='Count')
                 st.plotly_chart(fig, use_container_width=True, key=f"addr_{key_suffix}")

        # Tab 3: Grade
        with t3:
            st.markdown("#### 🏆 상담 등급 (S/A/B/C)")
            if 'Grade' in target_df.columns:
                g_map = {1:'S (초고관심)', 2:'A (관심)', 3:'B (보통)', 4:'C (관리)'}
                target_df['Grade_Label'] = target_df['Grade'].map(g_map).fillna('미기재')
                
                gc1, gc2 = st.columns([1, 2])
                with gc1:
                    counts = target_df['Grade_Label'].value_counts().reset_index()
                    counts.columns = ['Grade', 'Count']
                    try:
                        counts['Sort'] = counts['Grade'].apply(lambda x: 1 if 'S' in x else (2 if 'A' in x else (3 if 'B' in x else (4 if 'C' in x else 5))))
                        counts = counts.sort_values('Sort')
                    except: pass
                    fig = px.bar(counts, x='Grade', y='Count', color='Grade', text='Count')
                    st.plotly_chart(fig, use_container_width=True, key=f"grd_{key_suffix}")
                with gc2:
                    st.markdown("##### 상세 리스트 (Top 500)")
                    cols = ['Date', 'Manager', 'Addr_Gu', 'Q5_Label', 'Q6_Intent', 'Q4_Label', 'Grade_Label']
                    show_cols = [c for c in cols if c in target_df.columns]
                    
                    # Mapping for Korean Headers
                    header_map = {
                        'Date': '접수일자',
                        'Manager': '담당자',
                        'Addr_Gu': '거주지역(구)',
                        'Q5_Label': '선호평형',
                        'Q6_Intent': '의향점수',
                        'Q4_Label': '구매목적',
                        'Grade_Label': '고객등급'
                    }
                    
                    sorted_list = target_df.sort_values(['Grade', 'Q6_Intent'], ascending=[True, False]).head(500)
                    display_df = sorted_list[show_cols].rename(columns=header_map)
                    st.dataframe(display_df, use_container_width=True)

        # Tab 4: Sales Performance
        with t4:
            st.markdown("#### 📈 영업 성과 및 효율 (Performance)")
            sp_col1, sp_col2 = st.columns(2)
            
            with sp_col1:
                st.markdown("##### 🚩 거점별 수집 실적 (Top 10)")
                if 'Spot' in target_df.columns:
                    spot_counts = target_df['Spot'].value_counts().reset_index().head(10)
                    spot_counts.columns = ['Spot', 'Count']
                    fig = px.bar(spot_counts, x='Spot', y='Count', text='Count', title="거점별 DB 수집량")
                    st.plotly_chart(fig, use_container_width=True, key=f"perf_sp1_{key_suffix}")
                    
                    if 'Grade' in target_df.columns:
                         st.markdown("##### 💎 거점별 우수 등급(S/A) 현황")
                         high_grade = target_df[target_df['Grade'].isin([1, 2])].copy()
                         if not high_grade.empty:
                             g_map_perf = {1:'S (초고관심)', 2:'A (관심)'}
                             high_grade['Grade_Label'] = high_grade['Grade'].map(g_map_perf)
                             spot_grade = high_grade.groupby(['Spot', 'Grade_Label']).size().reset_index(name='Count')
                             fig3 = px.bar(spot_grade, x='Spot', y='Count', color='Grade_Label', text='Count', title="거점별 S/A 등급 확보 수", barmode='group')
                             st.plotly_chart(fig3, use_container_width=True, key=f"perf_sp3_{key_suffix}")
                         else:
                             st.info("S/A 등급 데이터가 없습니다.")

            with sp_col2:
                st.markdown("##### 👤 담당자/조별 실적 (Top 10)")
                if 'Manager' in target_df.columns:
                    mgr_counts = target_df['Manager'].value_counts().reset_index().head(10)
                    mgr_counts.columns = ['Manager', 'Count']
                    fig = px.bar(mgr_counts, x='Manager', y='Count', text='Count', title="담당자별 누적 실적")
                    st.plotly_chart(fig, use_container_width=True, key=f"perf_mp1_{key_suffix}")
                
                st.markdown("##### 상세 성과표")
                if 'Manager' in target_df.columns and 'Q6_Intent' in target_df.columns:
                    mgr_stats = target_df.groupby('Manager').agg(
                        Total_DB=('Manager', 'count'),
                        Avg_Score=('Q6_Intent', 'mean'),
                        S_Count=('Q6_Intent', lambda x: (x>=6).sum())
                    ).reset_index()
                    mgr_stats['S_Ratio'] = (mgr_stats['S_Count'] / mgr_stats['Total_DB'] * 100).round(1)
                    mgr_stats['Avg_Score'] = mgr_stats['Avg_Score'].round(2)
                    mgr_stats = mgr_stats.sort_values('Total_DB', ascending=False)
                    
                    # Mapping for Korean Headers
                    mgr_header_map = {
                        'Manager': '담당자/조',
                        'Total_DB': '총 접수량',
                        'Avg_Score': '평균 의향점수',
                        'S_Count': 'S급(6점이상)',
                        'S_Ratio': 'S급 비율(%)'
                    }
                    st.dataframe(mgr_stats.rename(columns=mgr_header_map), use_container_width=True)

        # Tab 5: Weekly Trend Analysis
        with t5:
            st.markdown("#### 📅 주차별 설문 응답 추이 (Weekly Trend)")
            if 'Date' not in target_df.columns:
                st.warning("날짜(Date) 데이터가 없어 주차별 분석을 할 수 없습니다.")
            else:
                # 1. Calculate Weeks
                # Make a copy to avoid SettingWithCopy warnings on the original df slice
                analysis_df = target_df.copy()
                analysis_df['Week_Label'] = get_weekly_period(pd.to_datetime(analysis_df['Date']))
                
                # 2. Select Question
                q_options = {
                    'Q1_Label': 'Q1. 사업지 인지도',
                    'Q2_Label': 'Q2. 정보 습득 경로',
                    'Q3_Label': 'Q3. 만족 장점',
                    'Q4_Label': 'Q4. 구매 목적',
                    'Q5_Label': 'Q5. 선호 평형',
                    'Q6_Intent': 'Q6. 계약 의향 (점수)',
                    'Q7_Label': 'Q7. 청약 예정',
                    'Q8_Label': 'Q8. 희망 분양가'
                }
                
                # Filter out columns that don't exist
                valid_q_options = {k: v for k, v in q_options.items() if k in analysis_df.columns}
                
                if not valid_q_options:
                     st.error("분석할 설문 문항 데이터가 없습니다.")
                else:
                    # Visualization Options
                    view_type = st.radio("그래프 보기 방식", ["건수 (Count)", "비율 (Percentage)"], horizontal=True, key=f"wk_view_{key_suffix}")
                    st.markdown("---")

                    # Loop through all questions
                    # We will use a 2-column layout
                    cols = st.columns(2)
                    
                    for idx, (q_key, q_title) in enumerate(valid_q_options.items()):
                        # Determine which column to use (0 or 1)
                        col_idx = idx % 2
                        with cols[col_idx]:
                            st.markdown(f"##### {q_title}")
                            
                            # Special handling for Q6 (Score)
                            if q_key == 'Q6_Intent':
                                # For Q6, we show the Average Score Trend Line
                                weekly_avg = analysis_df.groupby('Week_Label')['Q6_Intent'].mean().reset_index()
                                weekly_avg.columns = ['Week', 'Avg_Score']
                                # Sort naturally if possible, else by Week Label
                                try:
                                    weekly_avg['Week_Num'] = weekly_avg['Week'].apply(lambda x: int(x.split('주차')[0]))
                                    weekly_avg = weekly_avg.sort_values('Week_Num')
                                except:
                                    weekly_avg = weekly_avg.sort_values('Week')

                                fig = px.line(weekly_avg, x='Week', y='Avg_Score', markers=True, title="주차별 평균 계약 의향 점수", text='Avg_Score')
                                fig.update_traces(textposition="bottom center", texttemplate='%{text:.2f}')
                                fig.update_yaxes(range=[0, 8])
                                st.plotly_chart(fig, use_container_width=True, key=f"wk_line_{idx}_{key_suffix}")
                                
                                # Optional: Also show distribution below? 
                                # Might be too crowded. Let's stick to Average Line for Q6 in this grid view
                                # OR show distribution instead if user prefers. 
                                # Let's show the Score Distribution Bar Chart as well.
                                counts = analysis_df.groupby(['Week_Label', 'Q6_Intent']).size().reset_index(name='Count')
                                # Sort logic same as below...
                                try:
                                    counts['Week_Num'] = counts['Week_Label'].apply(lambda x: int(x.split('주차')[0]))
                                    counts = counts.sort_values(['Week_Num', 'Q6_Intent'])
                                except:
                                    counts = counts.sort_values(['Week_Label', 'Q6_Intent'])
                                    
                                if "비율" in view_type:
                                     week_totals = counts.groupby('Week_Label')['Count'].transform('sum')
                                     counts['Percent'] = (counts['Count'] / week_totals * 100).round(1)
                                     fig2 = px.bar(counts, x='Week_Label', y='Percent', color='Q6_Intent', text='Percent', title="의향 점수 분포")
                                     fig2.update_traces(texttemplate='%{text}%', textposition='inside')
                                else:
                                     fig2 = px.bar(counts, x='Week_Label', y='Count', color='Q6_Intent', text='Count', title="의향 점수 분포")
                                     fig2.update_traces(textposition='inside')
                                st.plotly_chart(fig2, use_container_width=True, key=f"wk_bar_{idx}_{key_suffix}")

                            else:
                                # Categorical Questions
                                counts = analysis_df.groupby(['Week_Label', q_key]).size().reset_index(name='Count')
                                
                                # Sort Lines
                                try:
                                    counts['Week_Num'] = counts['Week_Label'].apply(lambda x: int(x.split('주차')[0]))
                                    counts = counts.sort_values(['Week_Num', 'Count'], ascending=[True, False])
                                except:
                                    counts = counts.sort_values('Week_Label')

                                if "비율" in view_type:
                                    week_totals = counts.groupby('Week_Label')['Count'].transform('sum')
                                    counts['Percent'] = (counts['Count'] / week_totals * 100).round(1)
                                    fig = px.bar(counts, x='Week_Label', y='Percent', color=q_key, text='Percent')
                                    fig.update_traces(texttemplate='%{text}%', textposition='inside')
                                else:
                                    fig = px.bar(counts, x='Week_Label', y='Count', color=q_key, text='Count')
                                    fig.update_traces(textposition='inside')
                                    
                                st.plotly_chart(fig, use_container_width=True, key=f"wk_chart_{idx}_{key_suffix}")
                            
                            st.markdown("---")


    # --- Top Tabs ---
    main_tabs = st.tabs(["📊 전체 분석", "🟢 서대문구", "🔵 마포구", "🟣 은평구", "📈 고급 분석", "🤖 AI 분석"])
    
    # 1. Main Analysis
    with main_tabs[0]:
        st.subheader("📊 전체 데이터 분석")
        # Apply Sidebar Region Filter ONLY here
        view_df = filtered_base_df.copy()
        if sel_city:
            view_df = view_df[view_df['Addr_City'].isin(sel_city)]
        if sel_gu:
            view_df = view_df[view_df['Addr_Gu'].isin(sel_gu)]
            
        draw_analysis_tabs(view_df, "main")

    # 2. Seodaemun
    with main_tabs[1]:
        st.header("🟢 서대문구 거주 고객 분석")
        target = filtered_base_df[filtered_base_df['Addr_Gu'] == '서대문구']
        st.info(f"선택 기간 내 서대문구 거주 응답 수: {len(target):,} 명")
        draw_analysis_tabs(target, "seo")

    # 3. Mapo
    with main_tabs[2]:
        st.header("🔵 마포구 거주 고객 분석")
        target = filtered_base_df[filtered_base_df['Addr_Gu'] == '마포구']
        st.info(f"선택 기간 내 마포구 거주 응답 수: {len(target):,} 명")
        draw_analysis_tabs(target, "mapo")

    # 4. Eunpyeong
    with main_tabs[3]:
        st.header("🟣 은평구 거주 고객 분석")
        target = filtered_base_df[filtered_base_df['Addr_Gu'] == '은평구']
        st.info(f"선택 기간 내 은평구 거주 응답 수: {len(target):,} 명")
        draw_analysis_tabs(target, "eun")

    # 5. Advanced Analytics Dashboard (Moved to Tab)
    with main_tabs[4]:
        st.header("📈 고급 분석 대시보드")
        st.caption("리드 스코어링, RFIE 세그먼트, 경고 시스템을 통한 심층 분석")
    
    # Import advanced analytics
    try:
        from advanced_analytics import (
            apply_lead_scoring,
            get_lead_score_summary,
            calculate_rfie_scores,
            get_rfie_summary,
            get_segment_summary,
            generate_alerts
        )
        
        # Apply lead scoring
        df_scored = apply_lead_scoring(df)
        lead_summary = get_lead_score_summary(df_scored)
        
        # Apply RFIE
        df_rfie = calculate_rfie_scores(df)
        rfie_summary = get_rfie_summary(df_rfie)
        
        # Create tabs for advanced analytics
        adv_tabs = st.tabs(["🎯 리드 스코어링", "📊 RFIE 세그먼트", "⚠️ 경고/알림"])
        
        # Tab 1: Lead Scoring
        with adv_tabs[0]:
            # 설명 박스 추가
            with st.expander("ℹ️ 리드 스코어링이란?", expanded=False):
                st.markdown("""
                **리드 스코어링**은 각 고객의 **계약 가능성을 0~100점으로 수치화**한 것입니다.
                
                **📊 점수 산정 기준:**
                | 항목 | 기준 | 최대 점수 |
                |------|------|----------|
                | 계약 의향 (Q6) | 7점 이상 → 30점, 5~6점 → 20점 | 30점 |
                | 청약 자격 (Q7) | 1순위/2순위/특별공급 보유 시 | 25점 |
                | 희망 분양가 (Q8) | 분양가 범위 내 | 20점 |
                | 구매 목적 (Q4) | 실거주 → 15점, 투자 → 10점 | 15점 |
                | 유입 경로 (Q2) | 지인 추천 → 15점, 온라인 → 8점 | 10점 |
                
                **🏷️ 등급 분류:**
                - 🔴 **A급 (80점↑)**: 즉시 계약 가능! 바로 전화하세요
                - 🟠 **B급 (60~79점)**: 관심 높음, 48시간 내 연락
                - 🟡 **C급 (40~59점)**: 육성 필요, 주간 뉴스레터
                - ⚪ **D급 (40점↓)**: 장기 관리, 월간 리마인드
                """)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("리드 등급 분포")
                st.caption("고객들이 어떤 등급에 분포하는지 한눈에 파악")
                grade_counts = df_scored['Lead_Grade'].value_counts()
                fig_lead = px.pie(
                    values=grade_counts.values,
                    names=grade_counts.index,
                    color_discrete_sequence=['#FF6B6B', '#FFA94D', '#FFD93D', '#C0C0C0'],
                    hole=0.4
                )
                fig_lead.update_layout(height=350)
                st.plotly_chart(fig_lead, use_container_width=True)
            
            with col2:
                st.subheader("리드 스코어 통계")
                st.caption("등급별 고객 수와 비율")
                st.metric("평균 스코어", f"{lead_summary['평균_스코어']}점", help="전체 고객의 평균 리드 스코어")
                st.metric("A급 고객", f"{lead_summary['A급_수']}명 ({lead_summary.get('A급_비율', '0%')})", help="즉시 계약 가능한 핵심 고객")
                st.metric("B급 고객", f"{lead_summary['B급_수']}명 ({lead_summary.get('B급_비율', '0%')})", help="관심도 높은 잠재 고객")
                st.metric("C급 고객", f"{lead_summary['C급_수']}명 ({lead_summary.get('C급_비율', '0%')})", help="육성이 필요한 고객")
            
            # Segment details
            st.subheader("세그먼트별 특성")
            st.caption("각 등급 고객들의 주요 특성 - 클릭하면 상세 정보 확인")
            segment_details = get_segment_summary(df_scored)
            for grade, info in segment_details.items():
                with st.expander(f"{grade} - {info['고객_수']}명 ({info['비율']})"):
                    cols = st.columns(3)
                    cols[0].write(f"**선호 평형:** {info.get('선호_평형', 'N/A')}")
                    cols[1].write(f"**주요 유입:** {info.get('주요_유입경로', 'N/A')}")
                    cols[2].write(f"**주요 목적:** {info.get('주요_목적', 'N/A')}")
        
        # Tab 2: RFIE Segment
        with adv_tabs[1]:
            # 설명 박스 추가
            with st.expander("ℹ️ RFIE 분석이란?", expanded=False):
                st.markdown("""
                **RFIE 분석**은 고객을 **4가지 관점**에서 평가하여 세그먼트로 분류하는 방법입니다.
                
                **📊 RFIE 구성 요소:**
                | 지표 | 의미 | 점수 기준 |
                |------|------|----------|
                | **R** (Recency) | 최근 응답일 | 최근일수록 높음 (1~5점) |
                | **F** (Frequency) | 접촉 빈도 | 현재 1회 고정 (3점) |
                | **I** (Intent) | 계약 의향 | 의향 점수 기반 (1~5점) |
                | **E** (Eligibility) | 청약 자격 | 보유 시 +2점 |
                
                **🏷️ 세그먼트 분류 (총점 기준):**
                - 🏆 **Champion (15점↑)**: VIP 고객! 즉시 계약 가능
                - ⭐ **Loyal (12~14점)**: 충성도 높음, 추가 설득 필요
                - 🌱 **Promising (8~11점)**: 성장 가능성 있음, 육성 대상
                - 💤 **At Risk (5~7점)**: 관심 저하, 재활성화 필요
                - ❌ **Lost (5점↓)**: 이탈 위험, 장기 관리
                
                **💡 활용 팁:** Champion과 Loyal에 마케팅 자원을 집중하고, At Risk는 리마인드 메시지를 보내세요!
                """)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("RFIE 세그먼트 분포")
                st.caption("각 세그먼트별 고객 수")
                segment_counts = df_rfie['RFIE_Segment'].value_counts()
                fig_rfie = px.bar(
                    x=segment_counts.index,
                    y=segment_counts.values,
                    color=segment_counts.index,
                    color_discrete_sequence=['#FFD700', '#FFA500', '#32CD32', '#87CEEB', '#DC143C']
                )
                fig_rfie.update_layout(height=350, showlegend=False, xaxis_title="세그먼트", yaxis_title="고객 수")
                st.plotly_chart(fig_rfie, use_container_width=True)
            
            with col2:
                st.subheader("RFIE 점수 분포")
                st.caption("고객들의 RFIE 점수가 어떻게 분포하는지")
                fig_hist = px.histogram(df_rfie, x='RFIE_Score', nbins=15, color_discrete_sequence=['#6C5CE7'])
                fig_hist.update_layout(height=350, xaxis_title="RFIE 점수", yaxis_title="고객 수")
                st.plotly_chart(fig_hist, use_container_width=True)
            
            st.subheader("RFIE 통계")
            st.caption("세그먼트별 고객 수 요약")
            rfie_cols = st.columns(5)
            rfie_cols[0].metric("🏆 Champion", f"{rfie_summary['Champion_수']}명", help="최우수 고객, 바로 계약 가능")
            rfie_cols[1].metric("⭐ Loyal", f"{rfie_summary['Loyal_수']}명", help="충성도 높은 고객")
            rfie_cols[2].metric("🌱 Promising", f"{rfie_summary['Promising_수']}명", help="성장 가능성 있는 고객")
            rfie_cols[3].metric("💤 At Risk", f"{rfie_summary['AtRisk_수']}명", help="관심 저하된 고객, 리마인드 필요")
            rfie_cols[4].metric("❌ Lost", f"{rfie_summary['Lost_수']}명", help="이탈 위험 고객")
        
        # Tab 3: Alerts
        with adv_tabs[2]:
            # 설명 박스 추가
            with st.expander("ℹ️ 경고 시스템이란?", expanded=False):
                st.markdown("""
                **경고 시스템**은 데이터에서 **주의가 필요한 패턴을 자동으로 감지**합니다.
                
                **🔍 자동 감지 항목:**
                - 📉 평균 의향 점수가 5.0점 이하로 낮을 때
                - 📋 청약 자격 보유율이 30% 미만일 때
                - 🏠 특정 평형에 50% 이상 쏠릴 때 (재고 리스크)
                
                **💡 활용 방법:**
                - 경고가 뜨면 해당 항목을 즉시 점검하세요
                - 권장 액션을 참고하여 마케팅 전략을 조정하세요
                """)
            
            st.subheader("⚠️ 주의 사항 및 경고")
            st.caption("데이터에서 자동으로 감지된 주의 사항")
            alerts = generate_alerts(df)
            
            if alerts:
                for alert in alerts:
                    st.warning(alert)
            else:
                st.success("✅ 현재 특별한 경고 사항이 없습니다. 모든 지표가 정상 범위입니다.")
            
            st.subheader("📋 권장 액션")
            st.caption("현재 데이터 기반으로 추천하는 즉시 실행 가능한 액션")
            st.info("💡 A급 고객에게 즉시 1:1 전화 상담을 진행하세요.")
            if lead_summary['A급_수'] > 0:
                st.info(f"💡 현재 A급 고객 {lead_summary['A급_수']}명에게 VIP 프로모션을 안내하세요.")
            if rfie_summary['AtRisk_수'] > 0:
                st.info(f"💡 At Risk 고객 {rfie_summary['AtRisk_수']}명에게 리마인드 메시지를 발송하세요.")
    
    except Exception as e:
        st.error(f"고급 분석 모듈 로딩 실패: {str(e)}")

    # 6. AI Analyst (Moved to Tab)
    with main_tabs[5]:
        st.header("🤖 AI 데이터 심층 분석")
        st.caption("Google Gemini AI가 현재 필터링된 데이터를 분석하여 마케팅 인사이트를 제안합니다.")
    
    # Initialize session state for AI result
    if 'ai_result' not in st.session_state:
        st.session_state['ai_result'] = None

    col_ai1, col_ai2 = st.columns([1, 4])
    
    with col_ai1:
        if st.button("🚀 AI 분석 시작", type="primary", use_container_width=True):
            with st.spinner("AI가 데이터를 분석하고 있습니다... (약 10~20초 소요)"):
                st.session_state['ai_result'] = generate_ai_insight(df)
    
    with col_ai2:
        if st.session_state['ai_result'] and "⚠️" not in st.session_state['ai_result'] and "❌" not in st.session_state['ai_result']:
            try:
                from pdf_report_generator import generate_pdf_report
                
                # PDF 생성에 필요한 데이터 준비
                pdf_data = generate_pdf_report(
                    df, 
                    ai_insight=st.session_state['ai_result'],
                    lead_summary=lead_summary,
                    rfie_summary=rfie_summary
                )
                
                st.download_button(
                    label="📥 종합 분석 보고서 다운로드 (PDF)",
                    data=pdf_data,
                    file_name=f"사전영업_종합보고서_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"PDF 생성 중 오류 발생: {e}")

    if st.session_state['ai_result']:
        if "⚠️" in st.session_state['ai_result'] or "❌" in st.session_state['ai_result']:
            st.error(st.session_state['ai_result'])
        else:
            st.success("분석이 완료되었습니다!")
            st.markdown("### 📊 분석 결과 리포트")
            st.markdown(st.session_state['ai_result'])
            st.markdown("---")
            st.caption("※ 이 분석 결과는 AI에 의해 생성되었으며, 실제 전략 수립 시 참고용으로 활용하세요.")

else:
    st.error("데이터를 찾을 수 없습니다.")
