"""
고급 분석 모듈 (Advanced Analytics)
- 리드 스코어링 (Lead Scoring)
- RFIE 분석 (Recency, Frequency, Intent, Eligibility)
- 세그먼트 분류
- 경고 시스템
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# ============================================
# 리드 스코어링 (Lead Scoring)
# ============================================

def calculate_lead_score(row, price_range=(13, 16)):
    """
    개별 고객의 리드 스코어 계산
    
    Args:
        row: DataFrame의 한 행
        price_range: 실제 분양가 범위 (억 단위, 예: (13, 16))
    
    Returns:
        int: 리드 스코어 (0-100)
    """
    score = 0
    
    # 1. 계약 의향 점수 (Q6_Intent) - 최대 30점
    intent = row.get('Q6_Intent', 0)
    if pd.notna(intent):
        if intent >= 7:
            score += 30
        elif intent >= 5:
            score += 20
        elif intent >= 3:
            score += 10
    
    # 2. 청약 자격 (Q7_Subscription) - 최대 25점
    # 청약 자격 보유: 특별공급, 1순위, 2순위 (무응답 제외)
    subscription = str(row.get('Q7_Label', '')).strip()
    if pd.notna(subscription) and subscription not in ['', '무응답', '기타', 'nan']:
        score += 25
    
    # 3. 구매 목적 (Q4_Purpose) - 최대 15점
    purpose = row.get('Q4_Label', '')
    if pd.notna(purpose):
        if '실거주' in str(purpose):
            score += 15
        elif '투자' in str(purpose):
            score += 10
        else:
            score += 5
    
    # 4. 희망 분양가 적합성 (Q8_Price) - 최대 20점
    price = row.get('Q8_Price', 0)
    if pd.notna(price):
        # Q8_Price가 분양가 범위 내인지 확인
        # 예: 13~16억 범위
        if price_range[0] <= price <= price_range[1]:
            score += 20
        elif abs(price - sum(price_range)/2) <= 2:  # 범위에서 2억 이내
            score += 10
    
    # 5. 유입 채널 (Q2_Channel) - 최대 15점
    channel = row.get('Q2_Label', '')
    if pd.notna(channel):
        channel_str = str(channel).lower()
        if '지인' in channel_str or '추천' in channel_str:
            score += 15
        elif '현장' in channel_str or '방문' in channel_str:
            score += 12
        elif '온라인' in channel_str or '인터넷' in channel_str:
            score += 8
        else:
            score += 5
    
    return score

def get_lead_grade(score):
    """리드 스코어를 등급으로 변환"""
    if score >= 80:
        return 'A급 🔴'
    elif score >= 60:
        return 'B급 🟠'
    elif score >= 40:
        return 'C급 🟡'
    else:
        return 'D급 ⚪'

def apply_lead_scoring(df, price_range=(13, 16)):
    """
    전체 DataFrame에 리드 스코어링 적용
    
    Returns:
        DataFrame with 'Lead_Score' and 'Lead_Grade' columns
    """
    df_result = df.copy()
    df_result['Lead_Score'] = df_result.apply(
        lambda row: calculate_lead_score(row, price_range), axis=1
    )
    df_result['Lead_Grade'] = df_result['Lead_Score'].apply(get_lead_grade)
    return df_result

def get_lead_score_summary(df):
    """리드 스코어 요약 통계"""
    if 'Lead_Score' not in df.columns:
        df = apply_lead_scoring(df)
    
    summary = {
        '평균_스코어': round(df['Lead_Score'].mean(), 1),
        '최고_스코어': df['Lead_Score'].max(),
        '최저_스코어': df['Lead_Score'].min(),
        'A급_수': len(df[df['Lead_Score'] >= 80]),
        'B급_수': len(df[(df['Lead_Score'] >= 60) & (df['Lead_Score'] < 80)]),
        'C급_수': len(df[(df['Lead_Score'] >= 40) & (df['Lead_Score'] < 60)]),
        'D급_수': len(df[df['Lead_Score'] < 40]),
    }
    
    total = len(df)
    if total > 0:
        summary['A급_비율'] = f"{round(summary['A급_수'] / total * 100, 1)}%"
        summary['B급_비율'] = f"{round(summary['B급_수'] / total * 100, 1)}%"
        summary['C급_비율'] = f"{round(summary['C급_수'] / total * 100, 1)}%"
        summary['D급_비율'] = f"{round(summary['D급_수'] / total * 100, 1)}%"
    
    return summary


# ============================================
# RFIE 분석 (RFM 변형)
# ============================================

def calculate_rfie_scores(df, reference_date=None):
    """
    RFIE (Recency, Frequency, Intent, Eligibility) 분석
    
    - R (Recency): 얼마나 최근에 응답했는가 (1-5점)
    - F (Frequency): 문의 횟수 (현재 데이터에서는 1로 고정, 향후 CRM 연동 시 확장)
    - I (Intent): 계약 의향 점수 (1-5점으로 변환)
    - E (Eligibility): 청약 자격 보유 여부 (0 or 2점)
    
    Returns:
        DataFrame with RFIE scores and segment
    """
    df_result = df.copy()
    
    if reference_date is None:
        reference_date = datetime.now()
    
    # R (Recency) Score
    if 'Date' in df_result.columns:
        df_result['Date_parsed'] = pd.to_datetime(df_result['Date'], errors='coerce')
        max_date = df_result['Date_parsed'].max()
        
        def r_score(date):
            if pd.isna(date):
                return 3  # 중간값
            days_diff = (max_date - date).days
            if days_diff <= 3:
                return 5
            elif days_diff <= 7:
                return 4
            elif days_diff <= 14:
                return 3
            elif days_diff <= 21:
                return 2
            else:
                return 1
        
        df_result['R_Score'] = df_result['Date_parsed'].apply(r_score)
    else:
        df_result['R_Score'] = 3  # 날짜 없으면 중간값
    
    # F (Frequency) Score - 현재는 1회 응답이므로 고정
    df_result['F_Score'] = 3  # 향후 CRM 연동 시 확장
    
    # I (Intent) Score - Q6_Intent를 1-5점으로 변환
    def i_score(intent):
        if pd.isna(intent):
            return 3
        if intent >= 7:
            return 5
        elif intent >= 5:
            return 4
        elif intent >= 3:
            return 3
        elif intent >= 2:
            return 2
        else:
            return 1
    
    if 'Q6_Intent' in df_result.columns:
        df_result['I_Score'] = df_result['Q6_Intent'].apply(i_score)
    else:
        df_result['I_Score'] = 3
    
    # E (Eligibility) Score - 청약 자격
    # 청약 자격 보유: 특별공급, 1순위, 2순위 (무응답 제외)
    def e_score(subscription_label):
        label = str(subscription_label).strip()
        if pd.notna(subscription_label) and label not in ['', '무응답', '기타', 'nan']:
            return 2
        return 0
    
    if 'Q7_Label' in df_result.columns:
        df_result['E_Score'] = df_result['Q7_Label'].apply(e_score)
    else:
        df_result['E_Score'] = 0
    
    # Total RFIE Score
    df_result['RFIE_Score'] = (
        df_result['R_Score'] + 
        df_result['F_Score'] + 
        df_result['I_Score'] + 
        df_result['E_Score']
    )
    
    # RFIE Segment
    def rfie_segment(score):
        if score >= 15:
            return '🏆 Champion'
        elif score >= 12:
            return '⭐ Loyal'
        elif score >= 8:
            return '🌱 Promising'
        elif score >= 5:
            return '💤 At Risk'
        else:
            return '❌ Lost'
    
    df_result['RFIE_Segment'] = df_result['RFIE_Score'].apply(rfie_segment)
    
    return df_result

def get_rfie_summary(df):
    """RFIE 분석 요약"""
    if 'RFIE_Score' not in df.columns:
        df = calculate_rfie_scores(df)
    
    segment_counts = df['RFIE_Segment'].value_counts().to_dict()
    
    summary = {
        '평균_RFIE': round(df['RFIE_Score'].mean(), 1),
        'Champion_수': segment_counts.get('🏆 Champion', 0),
        'Loyal_수': segment_counts.get('⭐ Loyal', 0),
        'Promising_수': segment_counts.get('🌱 Promising', 0),
        'AtRisk_수': segment_counts.get('💤 At Risk', 0),
        'Lost_수': segment_counts.get('❌ Lost', 0),
    }
    
    return summary


# ============================================
# 경고 시스템 (Warning System)
# ============================================

def check_weekly_warnings(current_week_df, previous_week_df):
    """
    주차별 경고 조건 체크
    
    Returns:
        list of warning messages
    """
    warnings = []
    
    # 1. 응답 수 변화
    current_count = len(current_week_df)
    prev_count = len(previous_week_df)
    
    if prev_count > 0:
        change_rate = (current_count - prev_count) / prev_count * 100
        if change_rate <= -20:
            warnings.append(f"⚠️ 응답 수 {abs(change_rate):.1f}% 감소 ({prev_count} → {current_count})")
    
    # 2. 평균 의향 점수 변화
    if 'Q6_Intent' in current_week_df.columns and 'Q6_Intent' in previous_week_df.columns:
        current_intent = current_week_df['Q6_Intent'].mean()
        prev_intent = previous_week_df['Q6_Intent'].mean()
        
        if pd.notna(current_intent) and pd.notna(prev_intent):
            intent_change = current_intent - prev_intent
            if intent_change <= -0.5:
                warnings.append(f"⚠️ 평균 의향 점수 {abs(intent_change):.2f}점 하락 ({prev_intent:.2f} → {current_intent:.2f})")
    
    # 3. S급 비율 변화
    def s_grade_ratio(df):
        if 'Q6_Intent' not in df.columns or len(df) == 0:
            return 0
        return len(df[df['Q6_Intent'] >= 6]) / len(df) * 100
    
    current_s_ratio = s_grade_ratio(current_week_df)
    prev_s_ratio = s_grade_ratio(previous_week_df)
    
    if prev_s_ratio > 0:
        s_change = current_s_ratio - prev_s_ratio
        if s_change <= -5:
            warnings.append(f"⚠️ S급 고객 비율 {abs(s_change):.1f}%p 감소 ({prev_s_ratio:.1f}% → {current_s_ratio:.1f}%)")
    
    return warnings

def generate_alerts(df):
    """
    전체 데이터 기반 알림 생성
    """
    alerts = []
    
    # 평균 의향 점수 체크
    if 'Q6_Intent' in df.columns:
        avg_intent = df['Q6_Intent'].mean()
        if pd.notna(avg_intent) and avg_intent < 5.0:
            alerts.append(f"💡 평균 의향 점수가 {avg_intent:.2f}점으로 낮습니다. 타겟팅 전략 검토가 필요합니다.")
    
    # 청약 자격 보유율 체크 (특별공급, 1순위, 2순위가 청약 자격 보유자)
    if 'Q7_Label' in df.columns:
        # 무응답, 기타를 제외한 나머지가 청약 자격 보유자
        eligible_count = len(df[~df['Q7_Label'].isin(['무응답', '기타'])])
        eligible_ratio = eligible_count / len(df) * 100 if len(df) > 0 else 0
        if eligible_ratio < 30:
            alerts.append(f"💡 청약 자격 보유율이 {eligible_ratio:.1f}%로 낮습니다. 청약 가이드 콘텐츠 강화를 권장합니다.")
    
    # 특정 평형 쏠림 체크
    if 'Q5_Label' in df.columns:
        type_counts = df['Q5_Label'].value_counts()
        if len(type_counts) > 0:
            top_ratio = type_counts.iloc[0] / len(df) * 100 if len(df) > 0 else 0
            if top_ratio >= 50:
                alerts.append(f"💡 '{type_counts.index[0]}' 평형이 {top_ratio:.1f}%로 집중되어 있습니다. 재고 관리에 주의하세요.")
    
    return alerts


# ============================================
# 세그먼트별 요약
# ============================================

def get_segment_summary(df):
    """세그먼트별 상세 요약"""
    if 'Lead_Grade' not in df.columns:
        df = apply_lead_scoring(df)
    
    segments = {}
    
    for grade in ['A급 🔴', 'B급 🟠', 'C급 🟡', 'D급 ⚪']:
        segment_df = df[df['Lead_Grade'] == grade]
        
        if len(segment_df) > 0:
            segment_info = {
                '고객_수': len(segment_df),
                '비율': f"{len(segment_df) / len(df) * 100:.1f}%",
            }
            
            # 주요 특성 분석
            if 'Q5_Label' in segment_df.columns:
                top_type = segment_df['Q5_Label'].value_counts().head(1)
                if not top_type.empty:
                    segment_info['선호_평형'] = top_type.index[0]
            
            if 'Q2_Label' in segment_df.columns:
                top_channel = segment_df['Q2_Label'].value_counts().head(1)
                if not top_channel.empty:
                    segment_info['주요_유입경로'] = top_channel.index[0]
            
            if 'Q4_Label' in segment_df.columns:
                top_purpose = segment_df['Q4_Label'].value_counts().head(1)
                if not top_purpose.empty:
                    segment_info['주요_목적'] = top_purpose.index[0]
            
            segments[grade] = segment_info
    
    return segments
