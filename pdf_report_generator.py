"""
PDF 보고서 생성 모듈
- AI 인사이트 포함
- 주요 통계 및 차트 포함
- 한글 지원
"""

import io
from fpdf import FPDF
from datetime import datetime
import pandas as pd

# 한글 폰트 경로 (Windows 기본 폰트)
FONT_PATH = "C:/Windows/Fonts/malgun.ttf"


class PDFReport(FPDF):
    """한글 지원 PDF 보고서 클래스"""
    
    def __init__(self):
        super().__init__()
        # 한글 폰트 등록
        try:
            self.add_font("Malgun", "", FONT_PATH, uni=True)
            self.add_font("Malgun", "B", "C:/Windows/Fonts/malgunbd.ttf", uni=True)
            self.font_name = "Malgun"
        except Exception:
            # 폰트 로드 실패 시 기본 폰트 사용
            self.font_name = "Helvetica"
    
    def header(self):
        """페이지 헤더"""
        self.set_font(self.font_name, "B", 10)
        self.set_text_color(100, 100, 100)
        self.cell(0, 10, "사전영업 데이터 분석 보고서", 0, 1, "R")
        self.line(10, 18, 200, 18)
        self.ln(5)
    
    def footer(self):
        """페이지 푸터"""
        self.set_y(-15)
        self.set_font(self.font_name, "", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f"페이지 {self.page_no()}/{{nb}}", 0, 0, "C")
    
    def chapter_title(self, title):
        """챕터 제목"""
        self.set_font(self.font_name, "B", 14)
        self.set_text_color(30, 60, 114)
        self.cell(0, 10, title, 0, 1, "L")
        self.ln(2)
    
    def section_title(self, title):
        """섹션 제목"""
        self.set_font(self.font_name, "B", 11)
        self.set_text_color(50, 50, 50)
        self.cell(0, 8, title, 0, 1, "L")
        self.ln(1)
    
    def add_table(self, headers, data):
        """표 추가 (기본 cell 방식)"""
        self.set_font(self.font_name, "B", 9)
        self.set_fill_color(52, 73, 94)
        self.set_text_color(255, 255, 255)
        
        # 헤더
        col_width = 190 / len(headers)
        for header in headers:
            self.cell(col_width, 8, str(header), 1, 0, "C", fill=True)
        self.ln()
        
        # 데이터
        self.set_font(self.font_name, "", 9)
        self.set_text_color(0, 0, 0)
        fill = False
        for row in data:
            if fill:
                self.set_fill_color(245, 245, 245)
            else:
                self.set_fill_color(255, 255, 255)
            for item in row:
                self.cell(col_width, 7, str(item), 1, 0, "C", fill=True)
            self.ln()
            fill = not fill


def generate_pdf_report(df, ai_insight=None, lead_summary=None, rfie_summary=None):
    """
    PDF 보고서 생성
    """
    pdf = PDFReport()
    pdf.alias_nb_pages()
    
    # 폰트 확인
    if pdf.font_name == "Helvetica" and ai_insight:
        ai_insight = "[한글 폰트 로드 실패로 인해 영어/숫자만 표시될 수 있습니다]\n" + ai_insight

    pdf.add_page()
    
    # ========== 표지 ==========
    pdf.set_y(60)
    pdf.set_font(pdf.font_name, "B", 24)
    pdf.set_text_color(30, 60, 114)
    pdf.cell(0, 15, "사전영업 데이터 분석 보고서", 0, 1, "C")
    
    pdf.set_font(pdf.font_name, "", 14)
    pdf.set_text_color(100, 100, 100)
    pdf.ln(10)
    pdf.cell(0, 10, f"분석 기간: {get_date_range(df)}", 0, 1, "C")
    pdf.cell(0, 10, f"보고서 생성일: {datetime.now().strftime('%Y년 %m월 %d일 %H:%M')}", 0, 1, "C")
    pdf.cell(0, 10, f"총 응답 수: {len(df):,}명", 0, 1, "C")
    
    pdf.ln(40)
    pdf.set_font(pdf.font_name, "", 10)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 10, "Powered by AI Analytics", 0, 1, "C")
    
    # ========== 1. 핵심 요약 ==========
    pdf.add_page()
    pdf.chapter_title("1. 핵심 요약")
    
    # 주요 지표
    pdf.section_title("주요 지표")
    
    stats = get_key_stats(df)
    
    # 통계표
    summary_table = [
        ["항목", "지표값"],
        ["총 응답 수", f"{stats['total']:,}명"],
        ["평균 의향 점수", f"{stats['avg_intent']:.2f}점"],
        ["S급 고객 수", f"{stats['s_grade']:,}명 ({stats['s_grade_pct']:.1f}%)"],
        ["청약 자격 보유율", f"{stats['eligible_pct']:.1f}%"],
    ]
    pdf.add_table(summary_table[0], summary_table[1:])
    pdf.ln(5)
    
    # 리드 스코어링 요약
    if lead_summary:
        pdf.section_title("리드 스코어링 결과")
        lead_data = [
            ["등급", "고객 수", "비율"],
            ["A급 (80점↑)", f"{lead_summary.get('A급_수', 0)}명", lead_summary.get('A급_비율', '0%')],
            ["B급 (60~79점)", f"{lead_summary.get('B급_수', 0)}명", lead_summary.get('B급_비율', '0%')],
            ["C급 (40~59점)", f"{lead_summary.get('C급_수', 0)}명", lead_summary.get('C급_비율', '0%')],
            ["D급 (40점↓)", f"{lead_summary.get('D급_수', 0)}명", lead_summary.get('D급_비율', '0%')],
        ]
        pdf.add_table(lead_data[0], lead_data[1:])
        pdf.ln(5)
    
    # RFIE 요약
    if rfie_summary:
        pdf.section_title("RFIE 세그먼트 분포")
        rfie_data = [
            ["세그먼트", "고객 수", "설명"],
            ["Champion", f"{rfie_summary.get('Champion_수', 0)}명", "VIP 고객"],
            ["Loyal", f"{rfie_summary.get('Loyal_수', 0)}명", "충성도 높음"],
            ["Promising", f"{rfie_summary.get('Promising_수', 0)}명", "육성 대상"],
            ["At Risk", f"{rfie_summary.get('AtRisk_수', 0)}명", "리마인드 필요"],
            ["Lost", f"{rfie_summary.get('Lost_수', 0)}명", "이탈 위험"],
        ]
        pdf.add_table(rfie_data[0], rfie_data[1:])
        pdf.ln(10)
    
    # ========== 2. 설문 분석 ==========
    pdf.add_page()
    pdf.chapter_title("2. 설문 분석 상세")
    
    # Q1 인지도
    if 'Q1_Label' in df.columns:
        pdf.section_title("Q1. 사업지 인지도")
        q1_data = df['Q1_Label'].value_counts()
        table_rows = [[label, f"{count}명", f"{count/len(df)*100:.1f}%"] 
                      for label, count in q1_data.items()]
        pdf.add_table(["응답", "인원", "비율"], table_rows[:5])
        pdf.ln(5)
    
    # Q2 정보 습득 경로
    if 'Q2_Label' in df.columns:
        pdf.section_title("Q2. 정보 습득 경로")
        q2_data = df['Q2_Label'].value_counts()
        table_rows = [[label, f"{count}명", f"{count/len(df)*100:.1f}%"] 
                      for label, count in q2_data.items()]
        pdf.add_table(["경로", "인원", "비율"], table_rows[:7])
        pdf.ln(5)
    
    # Q4 구매 목적
    if 'Q4_Label' in df.columns:
        pdf.section_title("Q4. 구매 목적")
        q4_data = df['Q4_Label'].value_counts()
        table_rows = [[label, f"{count}명", f"{count/len(df)*100:.1f}%"] 
                      for label, count in q4_data.items()]
        pdf.add_table(["목적", "인원", "비율"], table_rows[:5])
        pdf.ln(5)
    
    # Q5 선호 평형
    if 'Q5_Label' in df.columns:
        pdf.section_title("Q5. 선호 평형")
        q5_data = df['Q5_Label'].value_counts()
        table_rows = [[label, f"{count}명", f"{count/len(df)*100:.1f}%"] 
                      for label, count in q5_data.items()]
        pdf.add_table(["평형", "인원", "비율"], table_rows[:5])
        pdf.ln(5)
    
    # Q7 청약 자격
    if 'Q7_Label' in df.columns:
        pdf.section_title("Q7. 청약 자격")
        q7_data = df['Q7_Label'].value_counts()
        table_rows = [[label, f"{count}명", f"{count/len(df)*100:.1f}%"] 
                      for label, count in q7_data.items()]
        pdf.add_table(["자격", "인원", "비율"], table_rows[:5])
    
    # ========== 3. AI 인사이트 ==========
    if ai_insight and "⚠️" not in ai_insight and "❌" not in ai_insight:
        pdf.add_page()
        pdf.chapter_title("3. AI 분석 인사이트")
        
        clean_insight = clean_markdown(ai_insight)
        
        pdf.set_font(pdf.font_name, "", 10)
        pdf.set_text_color(0, 0, 0)
        
        for line in clean_insight.split('\n'):
            line = line.strip()
            if not line:
                pdf.ln(2)
                continue
                
            if line.startswith('##') or line.startswith('###'):
                pdf.ln(2)
                pdf.set_font(pdf.font_name, "B", 11)
                pdf.multi_cell(190, 7, line.replace('#', '').strip())
                pdf.set_font(pdf.font_name, "", 10)
            elif line.startswith('**') and line.endswith('**'):
                pdf.set_font(pdf.font_name, "B", 10)
                pdf.multi_cell(190, 6, line.replace('**', '').strip())
                pdf.set_font(pdf.font_name, "", 10)
            elif line.startswith('- ') or line.startswith('* '):
                pdf.multi_cell(190, 6, "  • " + line[2:].strip())
            else:
                pdf.multi_cell(190, 6, line)
    
    # ========== 4. 권장 액션 ==========
    pdf.add_page()
    pdf.chapter_title("4. 권장 액션")
    
    pdf.section_title("즉시 실행 가능한 마케팅 전략")
    pdf.ln(2)
    
    actions = generate_action_items(df, lead_summary, rfie_summary)
    for i, action in enumerate(actions, 1):
        pdf.set_font(pdf.font_name, "B", 10)
        pdf.write(7, f"{i}. ")
        pdf.set_font(pdf.font_name, "", 10)
        pdf.multi_cell(180, 7, action)
        pdf.ln(2)
    
    # PDF 바이트 스트림 반환
    try:
        pdf_bytes = pdf.output()
        return io.BytesIO(pdf_bytes)
    except Exception as e:
        print(f"PDF Output Error: {e}")
        error_pdf = FPDF()
        error_pdf.add_page()
        error_pdf.set_font("Helvetica", size=12)
        error_pdf.cell(200, 10, txt=f"Error: {str(e)}", ln=1, align="C")
        return io.BytesIO(error_pdf.output())


def get_date_range(df):
    """데이터의 날짜 범위 반환"""
    if 'Date' in df.columns:
        dates = pd.to_datetime(df['Date'], errors='coerce').dropna()
        if not dates.empty:
            min_date = dates.min().strftime('%Y.%m.%d')
            max_date = dates.max().strftime('%Y.%m.%d')
            return f"{min_date} ~ {max_date}"
    return "전체 기간"


def get_key_stats(df):
    """핵심 통계 추출"""
    total = len(df)
    
    avg_intent = 0
    s_grade = 0
    if 'Q6_Intent' in df.columns:
        avg_intent = df['Q6_Intent'].mean()
        s_grade = len(df[df['Q6_Intent'] >= 6])
    
    eligible_count = 0
    if 'Q7_Label' in df.columns:
        eligible_count = len(df[~df['Q7_Label'].isin(['무응답', '기타'])])
    
    return {
        'total': total,
        'avg_intent': avg_intent if pd.notna(avg_intent) else 0,
        's_grade': s_grade,
        's_grade_pct': s_grade / total * 100 if total > 0 else 0,
        'eligible_pct': eligible_count / total * 100 if total > 0 else 0,
    }


def clean_markdown(text):
    """마크다운 기호 정리"""
    text = text.replace('```', '')
    text = text.replace('`', '')
    return text


def generate_action_items(df, lead_summary=None, rfie_summary=None):
    """권장 액션 아이템 생성"""
    actions = []
    
    actions.append("A급 고객에게 즉시 1:1 전화 상담을 진행하세요.")
    
    if lead_summary and lead_summary.get('A급_수', 0) > 0:
        actions.append(f"현재 A급 고객 {lead_summary['A급_수']}명에게 VIP 프로모션을 안내하세요.")
    
    if rfie_summary and rfie_summary.get('AtRisk_수', 0) > 0:
        actions.append(f"At Risk 고객 {rfie_summary['AtRisk_수']}명에게 리마인드 메시지를 발송하세요.")
    
    if 'Q6_Intent' in df.columns:
        avg_intent = df['Q6_Intent'].mean()
        if pd.notna(avg_intent) and avg_intent < 5.0:
            actions.append("평균 의향 점수가 낮습니다. 타겟팅 전략을 재검토하세요.")
    
    if 'Q5_Label' in df.columns:
        type_counts = df['Q5_Label'].value_counts()
        if len(type_counts) > 0:
            top_type = type_counts.index[0]
            top_pct = type_counts.iloc[0] / len(df) * 100
            if top_pct >= 50:
                actions.append(f"'{top_type}' 평형에 수요가 집중되어 있습니다. 해당 평형 재고를 확인하세요.")
    
    actions.append("주간 분석 리포트를 경영진에게 공유하세요.")
    
    return actions
