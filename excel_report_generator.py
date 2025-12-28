"""
엑셀 보고서 자동 생성 모듈
설문조사 데이터와 차트를 포함한 엑셀 파일을 자동으로 생성합니다.
"""

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from io import BytesIO
import xlsxwriter
from datetime import datetime


class ExcelReportGenerator:
    """엑셀 보고서 생성기"""
    
    def __init__(self, df):
        """
        초기화
        
        Parameters:
        -----------
        df : pandas.DataFrame
            보고서에 포함될 데이터프레임
        """
        self.df = df
        self.output = BytesIO()
        
    def create_report(self, report_type="전체"):
        """
        엑셀 보고서 생성
        
        Parameters:
        -----------
        report_type : str
            보고서 유형 ("전체", "데이터만", "요약만")
            
        Returns:
        --------
        BytesIO
            생성된 엑셀 파일의 바이트 스트림
        """
        try:
            # Workbook 생성
            workbook = xlsxwriter.Workbook(self.output, {'in_memory': True})
            
            # 서식 정의
            formats = self._create_formats(workbook)
            
            # 데이터 시트는 항상 생성 (우선순위 높음)
            try:
                if report_type in ["전체", "데이터만"]:
                    # 1. 원본 데이터 시트
                    self._add_raw_data_sheet(workbook, formats)
                    
                    # 2. 통계 요약 시트
                    self._add_summary_sheet(workbook, formats)
            except Exception as e:
                # 데이터 시트 생성 실패 시 에러 시트 생성
                error_sheet = workbook.add_worksheet('오류')
                error_sheet.write(0, 0, f'데이터 시트 생성 중 오류 발생: {str(e)}')
                error_sheet.write(1, 0, '원본 데이터를 확인해주세요.')
            
            # 차트 시트는 선택사항 (실패해도 보고서는 생성됨)
            if report_type in ["전체"]:
                try:
                    # 3. 차트 시트 (전체 보고서일 때만)
                    self._add_charts_sheet(workbook, formats)
                except Exception as e:
                    # 차트 생성 실패해도 보고서는 생성
                    # 차트 시트에 오류 메시지 추가
                    try:
                        error_sheet = workbook.add_worksheet('차트_오류')
                        error_sheet.write(0, 0, f'차트 생성 중 오류 발생: {str(e)}')
                        error_sheet.write(1, 0, 'kaleido 패키지가 설치되어 있는지 확인해주세요.')
                        error_sheet.write(2, 0, '설치 명령: pip install kaleido')
                    except:
                        pass  # 차트 오류 시트 생성도 실패하면 무시
            
            workbook.close()
            self.output.seek(0)
            
            return self.output
            
        except Exception as e:
            # 치명적인 오류 - 새로운 BytesIO로 간단한 에러 메시지 생성
            error_output = BytesIO()
            error_workbook = xlsxwriter.Workbook(error_output, {'in_memory': True})
            error_sheet = error_workbook.add_worksheet('오류')
            error_sheet.write(0, 0, '엑셀 보고서 생성 중 치명적인 오류가 발생했습니다.')
            error_sheet.write(1, 0, f'오류 내용: {str(e)}')
            error_sheet.write(2, 0, '개발자에게 문의해주세요.')
            error_workbook.close()
            error_output.seek(0)
            return error_output
    
    def _create_formats(self, workbook):
        """엑셀 서식 정의"""
        formats = {
            'header': workbook.add_format({
                'bold': True,
                'bg_color': '#4472C4',
                'font_color': 'white',
                'border': 1,
                'align': 'center',
                'valign': 'vcenter'
            }),
            'title': workbook.add_format({
                'bold': True,
                'font_size': 14,
                'bg_color': '#D9E1F2',
                'border': 1
            }),
            'cell': workbook.add_format({
                'border': 1,
                'align': 'left',
                'valign': 'vcenter'
            }),
            'number': workbook.add_format({
                'border': 1,
                'align': 'right',
                'valign': 'vcenter',
                'num_format': '#,##0'
            }),
            'percent': workbook.add_format({
                'border': 1,
                'align': 'right',
                'valign': 'vcenter',
                'num_format': '0.0%'
            }),
            'grade_s': workbook.add_format({
                'border': 1,
                'bg_color': '#C6EFCE',
                'font_color': '#006100'
            }),
            'grade_a': workbook.add_format({
                'border': 1,
                'bg_color': '#FFEB9C',
                'font_color': '#9C5700'
            }),
            'grade_b': workbook.add_format({
                'border': 1,
                'bg_color': '#FFC7CE',
                'font_color': '#9C0006'
            }),
        }
        return formats
    
    def _add_raw_data_sheet(self, workbook, formats):
        """원본 데이터 시트 추가"""
        worksheet = workbook.add_worksheet('원본 데이터')
        
        # 열 헤더 작성
        columns = self.df.columns.tolist()
        for col_num, col_name in enumerate(columns):
            worksheet.write(0, col_num, col_name, formats['header'])
        
        # 데이터 작성
        for row_num, row_data in enumerate(self.df.itertuples(index=False), start=1):
            for col_num, value in enumerate(row_data):
                # 날짜 처리
                if isinstance(value, pd.Timestamp):
                    worksheet.write(row_num, col_num, value.strftime('%Y-%m-%d'), formats['cell'])
                # Grade 열에 조건부 서식
                elif columns[col_num] == 'Grade':
                    if value == 1:
                        worksheet.write(row_num, col_num, 'S급', formats['grade_s'])
                    elif value == 2:
                        worksheet.write(row_num, col_num, 'A급', formats['grade_a'])
                    elif value == 3:
                        worksheet.write(row_num, col_num, 'B급', formats['grade_b'])
                    else:
                        worksheet.write(row_num, col_num, value, formats['cell'])
                # 숫자 처리
                elif isinstance(value, (int, float)) and not pd.isna(value):
                    worksheet.write(row_num, col_num, value, formats['number'])
                else:
                    worksheet.write(row_num, col_num, str(value) if not pd.isna(value) else '', formats['cell'])
        
        # 열 너비 자동 조정
        for col_num, col_name in enumerate(columns):
            max_len = max(
                len(str(col_name)),
                self.df[col_name].astype(str).str.len().max() if len(self.df) > 0 else 0
            )
            worksheet.set_column(col_num, col_num, min(max_len + 2, 30))
        
        # 필터 설정
        worksheet.autofilter(0, 0, len(self.df), len(columns) - 1)
        worksheet.freeze_panes(1, 0)
    
    def _add_summary_sheet(self, workbook, formats):
        """통계 요약 시트 추가"""
        worksheet = workbook.add_worksheet('통계 요약')
        
        row = 0
        
        # 제목
        worksheet.merge_range(row, 0, row, 3, '📊 사전영업 데이터 분석 요약', formats['title'])
        row += 2
        
        # 1. 핵심 지표
        worksheet.write(row, 0, '항목', formats['header'])
        worksheet.write(row, 1, '값', formats['header'])
        row += 1
        
        total = len(self.df)
        worksheet.write(row, 0, '총 응답 수', formats['cell'])
        worksheet.write(row, 1, total, formats['number'])
        row += 1
        
        if 'Q6_Intent' in self.df.columns:
            avg_intent = self.df['Q6_Intent'].mean()
            worksheet.write(row, 0, '평균 분양 의향 점수', formats['cell'])
            worksheet.write(row, 1, round(avg_intent, 2), formats['number'])
            row += 1
            
            high_intent = len(self.df[self.df['Q6_Intent'] >= 6])
            worksheet.write(row, 0, 'S급 고객 (6점 이상)', formats['cell'])
            worksheet.write(row, 1, high_intent, formats['number'])
            row += 1
            
            conversion = (high_intent / total * 100) if total > 0 else 0
            worksheet.write(row, 0, 'S급 전환율', formats['cell'])
            worksheet.write(row, 1, conversion / 100, formats['percent'])
            row += 2
        
        # 2. 문항별 응답 분포
        question_cols = {
            'Q1_Label': 'Q1. 사업지 인지도',
            'Q2_Label': 'Q2. 정보 습득 경로',
            'Q3_Label': 'Q3. 만족 장점',
            'Q4_Label': 'Q4. 구매 목적',
            'Q5_Label': 'Q5. 선호 평형',
            'Q7_Label': 'Q7. 청약 예정',
            'Q8_Label': 'Q8. 희망 분양가',
        }
        
        for col, title in question_cols.items():
            if col in self.df.columns:
                row += 1
                worksheet.merge_range(row, 0, row, 3, title, formats['title'])
                row += 1
                
                worksheet.write(row, 0, '응답', formats['header'])
                worksheet.write(row, 1, '건수', formats['header'])
                worksheet.write(row, 2, '비율', formats['header'])
                row += 1
                
                counts = self.df[col].value_counts()
                for answer, count in counts.items():
                    worksheet.write(row, 0, str(answer), formats['cell'])
                    worksheet.write(row, 1, count, formats['number'])
                    worksheet.write(row, 2, count / total, formats['percent'])
                    row += 1
        
        # 열 너비 설정
        worksheet.set_column(0, 0, 30)
        worksheet.set_column(1, 2, 15)
    
    def _add_charts_sheet(self, workbook, formats):
        """차트 이미지 시트 추가"""
        try:
            worksheet = workbook.add_worksheet('차트')
            
            row = 0
            
            # 제목
            worksheet.merge_range(row, 0, row, 5, '📈 데이터 시각화 차트', formats['title'])
            row += 2
            
            # 차트 데이터 준비
            charts_to_create = []
            
            # Q1 차트
            if 'Q1_Label' in self.df.columns and not self.df['Q1_Label'].dropna().empty:
                charts_to_create.append(('Q1_사업지인지도', 'Q1_Label', 'Q1. 사업지 인지도', 'pie'))
            
            # Q2 차트
            if 'Q2_Label' in self.df.columns and not self.df['Q2_Label'].dropna().empty:
                charts_to_create.append(('Q2_정보습득경로', 'Q2_Label', 'Q2. 정보 습득 경로', 'bar'))
            
            # Q3 차트
            if 'Q3_Label' in self.df.columns and not self.df['Q3_Label'].dropna().empty:
                charts_to_create.append(('Q3_만족장점', 'Q3_Label', 'Q3. 만족 장점', 'bar'))
            
            # Q4 차트
            if 'Q4_Label' in self.df.columns and not self.df['Q4_Label'].dropna().empty:
                charts_to_create.append(('Q4_구매목적', 'Q4_Label', 'Q4. 구매 목적', 'bar'))
            
            # Q5 차트
            if 'Q5_Label' in self.df.columns and not self.df['Q5_Label'].dropna().empty:
                charts_to_create.append(('Q5_선호평형', 'Q5_Label', 'Q5. 선호 평형', 'pie'))
            
            # Q6 차트
            if 'Q6_Intent' in self.df.columns and not self.df['Q6_Intent'].dropna().empty:
                charts_to_create.append(('Q6_계약의향', 'Q6_Intent', 'Q6. 계약 의향 점수 분포', 'intent'))

            # Q7 차트
            if 'Q7_Label' in self.df.columns and not self.df['Q7_Label'].dropna().empty:
                charts_to_create.append(('Q7_청약자격', 'Q7_Label', 'Q7. 청약 자격', 'pie'))
                
            # Q8 차트
            if 'Q8_Label' in self.df.columns and not self.df['Q8_Label'].dropna().empty:
                charts_to_create.append(('Q8_희망분양가', 'Q8_Label', 'Q8. 희망 분양가', 'bar'))
            
            # 차트가 하나도 없으면 메시지 표시
            if not charts_to_create:
                worksheet.write(row, 0, '생성 가능한 차트가 없습니다. 데이터를 확인해주세요.', formats['cell'])
                return
            
            # 차트 이미지 삽입 (2열 레이아웃)
            col = 0
            successful_charts = 0
            failed_charts = []
            
            for chart_info in charts_to_create:
                try:
                    name, column, title, chart_type = chart_info
                    
                    # 차트 생성
                    if chart_type == 'pie':
                        fig = self._create_pie_chart(self.df, column, title)
                    elif chart_type == 'bar':
                        fig = self._create_bar_chart(self.df, column, title)
                    elif chart_type == 'intent':
                        fig = self._create_intent_chart(self.df)
                    else:
                        continue
                    
                    # 차트를 이미지로 변환 (kaleido 필요)
                    try:
                        # 0.2.1 버전 이상 호환성 고려하여 engine 명시 안함 (기본값 사용) 또는 kaleido 명시
                        # 여기서는 안전하게 기본 to_image 사용 (내부적으로 kaleido 호출)
                        img_bytes = fig.to_image(format="png", width=600, height=400)
                        
                        # 이미지 삽입
                        worksheet.insert_image(row, col, f'{name}.png', {'image_data': BytesIO(img_bytes)})
                        successful_charts += 1
                        
                    except Exception as k_err:
                        # 이미지 변환 실패 시 텍스트로 대체 표시
                        failed_charts.append((name, str(k_err)))
                        worksheet.write(row, col, f'❌ {title} 이미지 변환 실패', formats['cell'])
                        worksheet.write(row+1, col, f'원인: {str(k_err)}', formats['cell'])
                        
                        # 텍스트 요약 정보라도 표시
                        if column in self.df.columns and chart_type != 'intent':
                            counts = self.df[column].value_counts().head(5)
                            r_offset = 3
                            for val, cnt in counts.items():
                                worksheet.write(row+r_offset, col, f"{val}: {cnt}", formats['cell'])
                                r_offset += 1

                    # 다음 위치 계산 (2열 레이아웃) -> 간격을 넓힘 (이미지 너비 고려)
                    col += 10  # 3칸 -> 10칸으로 변경 (약 640px 확보)
                    if col >= 20: # 2개 배치 후 줄바꿈 (0, 10 이므로 20 되면 줄바꿈)
                        col = 0
                        row += 22  # 이미지 높이만큼 이동
                        
                except Exception as e:
                    # 차트 생성 자체 실패
                    worksheet.write(row, col, f'{title} 데이터 처리 오류', formats['cell'])
                    col += 10
                    if col >= 20:
                        col = 0
                        row += 22
            
            # 결과 메시지
            result_row = row + 25 if col == 0 else row + 40
            if successful_charts > 0:
                worksheet.write(result_row, 0, 
                    f'✅ {successful_charts}개의 차트가 성공적으로 생성되었습니다.', 
                    formats['cell'])
            
            if failed_charts:
                result_row += 1
                worksheet.write(result_row, 0, 
                    f'⚠️ {len(failed_charts)}개의 차트 이미지 변환 실패 (서버 로그 확인 필요)', 
                    formats['cell'])
                    
        except Exception as e:
            # 차트 시트 전체 생성 실패 시
            worksheet.write(0, 0, f'차트 시트 생성 중 오류 발생: {str(e)}', formats['cell'])
            worksheet.write(1, 0, '보고서의 데이터와 통계 요약 시트는 보존되었습니다.', formats['cell'])

    
    def _create_pie_chart(self, df, column, title):
        """파이 차트 생성"""
        counts = df[column].value_counts().reset_index()
        counts.columns = ['Answer', 'Count']
        
        # 색상 적용
        fig = px.pie(counts, values='Count', names='Answer', title=title, hole=0.4,
                     color_discrete_sequence=px.colors.qualitative.Pastel)
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(showlegend=True, height=400)
        
        return fig
    
    def _create_bar_chart(self, df, column, title):
        """막대 차트 생성"""
        counts = df[column].value_counts().reset_index()
        counts.columns = ['Answer', 'Count']
        
        # 항목별 다른 색상 적용
        fig = px.bar(counts, x='Answer', y='Count', title=title, text='Count',
                     color='Answer', color_discrete_sequence=px.colors.qualitative.Pastel)
        fig.update_traces(textposition='outside')
        fig.update_layout(showlegend=False, height=400)
        
        return fig
    
    def _create_intent_chart(self, df):
        """계약 의향 점수 차트 생성"""
        q6_counts = df['Q6_Intent'].value_counts().sort_index().reset_index()
        q6_counts.columns = ['Score', 'Count']
        
        # 점수에 따라 색상 그라데이션 적용 (Blues)
        fig = px.bar(q6_counts, x='Score', y='Count', title='Q6. 계약 의향 점수 분포', text='Count',
                     color='Count', color_continuous_scale='Blues')
        fig.update_traces(textposition='outside')
        fig.update_xaxes(dtick=1)
        fig.update_layout(showlegend=False, height=400, coloraxis_showscale=False)
        
        return fig


def generate_excel_report(df, report_type="전체"):
    """
    엑셀 보고서 생성 헬퍼 함수
    
    Parameters:
    -----------
    df : pandas.DataFrame
        보고서에 포함될 데이터
    report_type : str
        보고서 유형 ("전체", "데이터만", "요약만")
    
    Returns:
    --------
    BytesIO
        생성된 엑셀 파일
    """
    generator = ExcelReportGenerator(df)
    return generator.create_report(report_type)
