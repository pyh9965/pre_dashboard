import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Page Config
st.set_page_config(page_title="사전영업 대시보드", page_icon="📊", layout="wide")

st.title("📊 사전영업 데이터 분석 대시보드")
st.markdown("---")

@st.cache_data
def load_data(file_source):
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
        
    df = load_data(default_path)

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
    
    # --- Reusable Analysis Function ---
    def draw_analysis_tabs(target_df, key_suffix=""):
        if target_df.empty:
            st.warning("분석할 데이터가 없습니다.")
            return

        # Sub-tabs within the analysis view
        t1, t2, t3, t4 = st.tabs(["📊 설문 문항 통합 분석", "🌍 인구/지역 통계", "🏆 상담 등급 분석", "📈 영업 성과 분석"])
        
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


    # --- Top Tabs ---
    main_tabs = st.tabs(["📊 전체 분석", "🟢 서대문구", "🔵 마포구", "🟣 은평구"])
    
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

else:
    st.error("데이터를 찾을 수 없습니다.")
