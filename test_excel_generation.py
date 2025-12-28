"""
엑셀 생성 테스트 스크립트
excel_report_generator.py의 기능을 독립적으로 테스트합니다.
"""

import pandas as pd
import sys
import os

# 현재 디렉토리를 경로에 추가
sys.path.insert(0, os.path.dirname(__file__))

from excel_report_generator import generate_excel_report

# 테스트용 샘플 데이터 생성
print("1. 샘플 데이터 생성 중...")
sample_data = {
    'Date': pd.date_range('2024-01-01', periods=10),
    'Manager': ['김철수', '이영희'] * 5,
    'Spot': ['서대문', '마포'] * 5,
    'Q1_Awareness': [1, 2, 3] * 3 + [1],
    'Q2_Channel': [1, 2, 3, 4, 5] * 2,
    'Q3_Pros': [1, 2, 3, 4, 5] * 2,
    'Q4_Purpose': [1, 2, 3] * 3 + [1],
    'Q5_Type': [1, 2, 3, 4] * 2 + [1, 2],
    'Q6_Intent': [5, 6, 7, 6, 5, 4, 6, 7, 6, 5],
    'Q7_Subscription': [1, 2, 3, 4] * 2 + [1, 2],
    'Q8_Price': [1, 2, 3, 4, 5] * 2,
    'Addr_City': ['서울'] * 10,
    'Addr_Gu': ['서대문구', '마포구'] * 5,
    'Addr_Dong': ['연희동', '망원동'] * 5,
    'Gender': [1, 2] * 5,
    'Grade': [1, 2, 3, 4, 1, 2, 3, 4, 1, 2]
}

# 레이블 열 추가
q1_map = {1: '잘 알고있다', 2: '들어본 적 있다', 3: '처음 알았다'}
q2_map = {1: '외부홍보', 2: '부동산', 3: '가족/지인', 4: '옥외광고', 5: '홈페이지'}
q3_map = {1:'브랜드', 2:'주거쾌적성', 3:'교통환경', 4:'교육환경', 5:'투자가치'}
q4_map = {1: '실거주', 2: '투자', 3: '실거주+투자'}
q5_map = {1: '59㎡', 2: '74㎡', 3: '75㎡', 4: '84㎡'}
q7_map = {1: '특별공급', 2: '1순위', 3: '2순위', 4: '무응답'}
q8_map = {1: '11.5~12억', 2: '12~12.5억', 3: '12.5~13억', 4: '13~13.5억', 5: '14~14.5억'}

df = pd.DataFrame(sample_data)
df['Q1_Label'] = df['Q1_Awareness'].map(q1_map)
df['Q2_Label'] = df['Q2_Channel'].map(q2_map)
df['Q3_Label'] = df['Q3_Pros'].map(q3_map)
df['Q4_Label'] = df['Q4_Purpose'].map(q4_map)
df['Q5_Label'] = df['Q5_Type'].map(q5_map)
df['Q7_Label'] = df['Q7_Subscription'].map(q7_map)
df['Q8_Label'] = df['Q8_Price'].map(q8_map)

print(f"   데이터 행 수: {len(df)}")
print(f"   데이터 열 수: {len(df.columns)}")

# 테스트 1: 데이터만 옵션
print("\n2. '데이터만' 보고서 생성 테스트...")
try:
    excel_bytes = generate_excel_report(df, "데이터만")
    
    # 파일로 저장
    output_file = "test_report_data_only.xlsx"
    with open(output_file, 'wb') as f:
        f.write(excel_bytes.read())
    
    file_size = os.path.getsize(output_file)
    print(f"   ✅ 성공! 파일 생성됨: {output_file}")
    print(f"   파일 크기: {file_size:,} bytes")
    
    # 파일이 정상적으로 열리는지 테스트
    test_df = pd.read_excel(output_file, sheet_name='원본 데이터')
    print(f"   검증: 원본 데이터 시트 읽기 성공 ({len(test_df)} 행)")
    
except Exception as e:
    print(f"   ❌ 실패: {str(e)}")
    import traceback
    traceback.print_exc()

# 테스트 2: 전체 보고서 (차트 제외 테스트를 위해 일단 생략)
print("\n3. 파일 생성 테스트 완료!")
print(f"\n생성된 파일: {os.path.abspath(output_file)}")
print("Excel에서 파일을 열어 내용을 확인하세요.")
