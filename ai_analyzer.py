import streamlit as st
import pandas as pd
from google import genai
import json
import numpy as np

# 커스텀 JSON 인코더 (numpy 타입 처리)
def convert_to_serializable(obj):
    """numpy 타입을 Python 기본 타입으로 변환"""
    if isinstance(obj, dict):
        return {k: convert_to_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_serializable(i) for i in obj]
    elif isinstance(obj, (np.integer, np.int64, np.int32)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif pd.isna(obj):
        return None
    else:
        return obj

# 고급 분석 모듈 임포트
from advanced_analytics import (
    apply_lead_scoring,
    get_lead_score_summary,
    calculate_rfie_scores,
    get_rfie_summary,
    get_segment_summary,
    generate_alerts
)

def get_weekly_period(date_series):
    """날짜를 주차별로 그룹화"""
    if date_series.empty:
        return date_series.astype(str)
    
    min_date = date_series.min()
    start_anchor = min_date - pd.Timedelta(days=min_date.weekday())
    
    dates = pd.to_datetime(date_series)
    days_diff = (dates - start_anchor).dt.days
    week_nums = (days_diff // 7) + 1
    
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

def get_data_summary(df):
    """데이터프레임에서 핵심 통계를 추출하여 텍스트로 변환"""
    summary = {
        "총_응답_수": len(df),
        "평균_계약_의향_점수": round(df['Q6_Intent'].mean(), 2) if 'Q6_Intent' in df.columns else "N/A",
        "S급_고객_수": len(df[df['Q6_Intent'] >= 6]) if 'Q6_Intent' in df.columns else 0,
    }
    
    # 주요 문항 최빈값 추출
    for col, label in [('Q1_Label', '인지도'), ('Q2_Label', '정보습득경로'), ('Q4_Label', '구매목적'), ('Q5_Label', '선호평형')]:
        if col in df.columns:
            top_answer = df[col].value_counts().head(1)
            if not top_answer.empty:
                summary[f"최다_{label}"] = f"{top_answer.index[0]} ({top_answer.values[0]}명)"

    return json.dumps(convert_to_serializable(summary), ensure_ascii=False, indent=2)

def get_weekly_trend_summary(df):
    """주차별 트렌드 데이터 생성"""
    if 'Date' not in df.columns:
        return "주차별 데이터 없음 (날짜 컬럼 미존재)"
    
    df_copy = df.copy()
    df_copy['Date'] = pd.to_datetime(df_copy['Date'], errors='coerce')
    df_copy = df_copy.dropna(subset=['Date'])
    
    if df_copy.empty:
        return "주차별 데이터 없음 (유효한 날짜 없음)"
    
    df_copy['Week_Label'] = get_weekly_period(df_copy['Date'])
    
    weekly_stats = []
    for week_label in df_copy['Week_Label'].unique():
        week_df = df_copy[df_copy['Week_Label'] == week_label]
        
        week_stat = {
            "주차": week_label,
            "응답수": len(week_df),
        }
        
        if 'Q6_Intent' in week_df.columns:
            week_stat["평균_의향점수"] = round(week_df['Q6_Intent'].mean(), 2)
            week_stat["S급_비율"] = f"{round(len(week_df[week_df['Q6_Intent'] >= 6]) / len(week_df) * 100, 1)}%"
        
        if 'Q5_Label' in week_df.columns:
            top_type = week_df['Q5_Label'].value_counts().head(1)
            if not top_type.empty:
                week_stat["최다_선호평형"] = top_type.index[0]
        
        if 'Q2_Label' in week_df.columns:
            top_channel = week_df['Q2_Label'].value_counts().head(1)
            if not top_channel.empty:
                week_stat["최다_유입경로"] = top_channel.index[0]
        
        weekly_stats.append(week_stat)
    
    # 주차 순서대로 정렬
    try:
        weekly_stats.sort(key=lambda x: int(x["주차"].split("주차")[0]))
    except:
        pass
    
    return json.dumps(convert_to_serializable(weekly_stats), ensure_ascii=False, indent=2)

def get_advanced_analytics_summary(df):
    """고급 분석 요약 (리드 스코어링 + RFIE + 경고)"""
    result = {}
    
    # 1. 리드 스코어링
    try:
        df_scored = apply_lead_scoring(df)
        result['lead_scoring'] = get_lead_score_summary(df_scored)
        result['segment_details'] = get_segment_summary(df_scored)
    except Exception as e:
        result['lead_scoring'] = f"계산 실패: {str(e)}"
    
    # 2. RFIE 분석
    try:
        df_rfie = calculate_rfie_scores(df)
        result['rfie'] = get_rfie_summary(df_rfie)
    except Exception as e:
        result['rfie'] = f"계산 실패: {str(e)}"
    
    # 3. 경고/알림
    try:
        result['alerts'] = generate_alerts(df)
    except Exception as e:
        result['alerts'] = [f"알림 생성 실패: {str(e)}"]
    
    return json.dumps(convert_to_serializable(result), ensure_ascii=False, indent=2)

def generate_ai_insight(df):
    """
    Google Gemini API를 사용하여 데이터 인사이트 생성 (고급 분석 포함)
    """
    # 1. API Key 확인
    api_key = None
    try:
        if "gemini" in st.secrets and "api_key" in st.secrets["gemini"]:
            api_key = st.secrets["gemini"]["api_key"].strip()
    except Exception:
        pass

    if not api_key:
        return """⚠️ **API Key 설정이 필요합니다.**
        
        `.streamlit/secrets.toml` 파일에 Google Gemini API Key를 설정해주세요.
        
        **API 키 발급**: [Google AI Studio](https://aistudio.google.com/apikey)
        
        ```toml
        [gemini]
        api_key = "여기에_API_키를_입력하세요"
        ```
        """

    # 2. 데이터 요약
    data_summary = get_data_summary(df)
    weekly_trend = get_weekly_trend_summary(df)
    advanced_analytics = get_advanced_analytics_summary(df)
    
    # 3. 프롬프트 구성 (전문가 수준)
    prompt = f"""당신은 10년 경력의 아파트 분양 마케팅 전문 컨설턴트이자 데이터 분석 전문가입니다.

아래는 사전영업 설문 데이터의 핵심 통계, 주차별 트렌드, 그리고 고급 분석 결과입니다.
전문가 관점에서 다음 내용을 분석해 주세요:

## 분석 요청

### 1. 현황 요약
- 현재 사업지의 인지도와 고객 반응 요약
- 리드 스코어링 결과 해석 (A/B/C/D급 분포의 의미)
- RFIE 세그먼트별 고객 특성

### 2. 핵심 타겟 분석
- 가장 집중해야 할 고객 세그먼트
- 세그먼트별 맞춤 공략 전략

### 3. 주차별 트렌드 인사이트
- 응답 수, 의향 점수, S급 비율의 변화 추이
- 긍정적/부정적 신호 포착
- 트렌드 기반 향후 전망

### 4. 경고 및 주의사항
- 즉시 대응이 필요한 이슈
- 리스크 요인

### 5. 액션 아이템
- 즉시 실행 가능한 구체적인 마케팅 전략 3가지

---

## 데이터

### [전체 데이터 통계]
{data_summary}

### [주차별 트렌드]
{weekly_trend}

### [고급 분석 결과 - 리드 스코어링/RFIE/경고]
{advanced_analytics}

---

답변은 경영진 보고용으로 간결하고 명확하게, 마크다운 형식으로 작성해 주세요.
수치와 퍼센트를 적극 활용하고, 각 섹션에 적절한 이모지를 사용해 가독성을 높여주세요."""

    try:
        # 4. Google Gemini API 호출
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        return response.text
        
    except Exception as e:
        return f"❌ AI 분석 중 오류가 발생했습니다: {str(e)}"
