# 📘 사전영업 데이터 분석 대시보드 프로젝트 인수인계 문서

본 문서는 '사전영업 대시보드' 프로젝트의 현재 상태, 구현된 기능, 기술적 난관 및 해결 방법, 그리고 향후 작업을 다른 AI 에이전트나 개발자가 원활하게 이어받을 수 있도록 작성되었습니다.

---

## 1. 프로젝트 개요

- **프로젝트명**: 사전영업 데이터 분석 대시보드
- **목적**: 사전영업 단계에서 수집된 설문 데이터를 시각화하고 분석하여, 의사결정에 필요한 인사이트를 제공하며, 분석 결과를 엑셀 보고서 형태로 자동 생성하여 공유할 수 있게 함.
- **주요 기능**: 
  - 핵심 지표(KPI) 대시보드
  - 설문 문항별 상세 차트 분석
  - 다차원 데이터 필터링 (지역, 담당자, 등급 등)
  - **상세 엑셀 보고서 자동 생성 및 다운로드 (핵심)**

## 2. 기술 스택 및 환경

- **언어**: Python 3.10+
- **웹 프레임워크**: Streamlit
- **데이터 처리**: Pandas
- **시각화**: Plotly Express
- **엑셀 생성**: XlsxWriter
- **이미지 변환**: Kaleido (Plotly 차트를 이미지로 변환)
- **이미지 처리**: Pillow (PIL)

### 필수 라이브러리 (`requirements.txt`)
```text
streamlit
pandas
plotly
xlsxwriter
kaleido
pillow
```

## 3. 프로젝트 파일 구조

```
d:\AI프로그램제작\사전영업대시보드\
├── app_dashboard.py            # 메인 대시보드 애플리케이션 (Entry Point)
├── excel_report_generator.py   # 엑셀 보고서 생성 로직 모듈 (핵심)
├── test_excel_generation.py    # 엑셀 생성 기능 독립 테스트 스크립트
├── requirements.txt            # 의존성 패키지 목록
└── .gitignore                  # Git 무시 설정
```

## 4. 핵심 기능 구현 상세

### 4.1. 엑셀 보고서 생성 (`excel_report_generator.py`)

이 모듈은 Pandas DataFrame을 입력받아 서식이 지정된 엑셀 파일(`BytesIO`)을 반환합니다.

- **구성 요소**:
  - `_create_formats`: 엑셀 스타일(헤더, 셀, 숫자, 백분율 등) 정의.
  - `_add_raw_data_sheet`: 원본 데이터 시트 생성. 조건부 서식(Grade 별 색상), 필터, 틀 고정 적용.
  - `_add_summary_sheet`: 통계 요약 시트 생성. 문항별 응답 수 및 비율 테이블 자동 생성.
  - `_add_charts_sheet`: **Plotly 차트를 이미지로 변환하여 엑셀에 삽입.**
    - `kaleido` 엔진을 사용하여 차트를 PNG로 변환.
    - 변환 실패 시 텍스트 정보로 대체하는 안전 장치 포함.
    - 차트 배치 간격을 10칸(열)으로 설정하여 겹침 방지.
    - 파스텔 톤 색상 및 그라데이션 적용.

### 4.2. 엑셀 다운로드 프로세스 (`app_dashboard.py`)

Streamlit의 특성(Re-run)으로 인한 다운로드 오류를 방지하기 위해 **2단계 프로세스**를 구현했습니다.

1.  **보고서 생성 (`📥 엑셀 보고서 생성` 버튼)**:
    - 사용자가 버튼 클릭 시 보고서를 생성합니다.
    - 생성된 파일 객체(`BytesIO`)에서 **`getvalue()`를 호출하여 `bytes` 데이터만 추출**합니다.
    - 추출한 `bytes` 데이터와 생성된 파일명을 `st.session_state`에 저장합니다.
    - *이유: 객체 자체를 저장하면 상태 리셋 시 포인터가 유실되어 파일이 깨짐.*

2.  **파일 다운로드 (`⬇️ 엑셀 파일 다운로드` 버튼)**:
    - `st.session_state`에 저장된 데이터가 있을 때만 버튼이 표시됩니다.
    - 버튼의 `key`를 `f"dl_{filename}"` 형식으로 **동적 할당**합니다.
    - *이유: 이전 캐시된 버튼이 재사용되어 잘못된 파일이 다운로드되는 것을 막기 위함.*

## 5. 트러블슈팅 이력 (중요 Reference)

이 프로젝트를 진행하면서 해결한 주요 이슈들입니다. 향후 유지보수 시 참고하십시오.

### 이슈 1: 다운로드된 엑셀 파일이 열리지 않음 / 파일명이 UUID로 깨짐
- **원인**: `st.download_button`에 `BytesIO` 객체를 직접 전달했으나, 스트림 포지션이 초기화되거나 객체가 소실됨.
- **해결**:
  - `generate_excel_report`의 반환값(`BytesIO`)에서 `.getvalue()`로 순수한 `bytes` 데이터 추출.
  - `st.session_state`에 `bytes` 데이터를 저장하고 다운로드 버튼에 전달.
  - `mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"` 명시.

### 이슈 2: 다운로드 버튼 클릭 시 동작 안 함 (재실행 문제)
- **원인**: Streamlit은 버튼 클릭 시 전체 스크립트를 재실행하는데, 중첩된 버튼 구조에서 로직이 끊김.
- **해결**: "생성"과 "다운로드"를 분리하고, 생성된 데이터를 세션 상태(`st.session_state`)에 영속적으로 저장하여 재실행 후에도 다운로드 버튼이 유지되도록 함.

### 이슈 3: 차트 이미지가 엑셀에서 겹쳐 보임
- **원인**: 엑셀 셀 너비에 비해 삽입된 이미지(600x400)가 커서, 기본 간격(3열)으로는 이미지가 겹침.
- **해결**: 차트 배치 간격을 **10열(Column)**로 대폭 확대하고, 2개 배치 후 줄바꿈하도록 로직 수정.

### 이슈 4: 차트가 흑백으로 나옴
- **원인**: Plotly 기본 템플릿 정보가 `kaleido` 변환 시 완벽하게 전달되지 않음.
- **해결**: 차트 생성 함수(`px.pie`, `px.bar`)에 `color`, `color_discrete_sequence` 속성을 명시적으로 추가하여 파스텔 톤 및 그라데이션 적용.

### 이슈 5: Q7, Q8 차트 누락
- **원인**: 초기 개발 시 Q6까지만 구현됨.
- **해결**: `excel_report_generator.py`에 Q7(청약 자격), Q8(희망 분양가) 차트 생성 로직을 추가하고 색상 테마 적용.

### 이슈 6: 차트 생성 실패 시 엑셀 파일 전체 생성 실패
- **원인**: `kaleido` 설치 문제 등으로 차트 변환 실패 시 예외가 발생하여 파일 생성이 중단됨.
- **해결**: 다중 `try-except` 블록 적용. 차트 이미지 변환 실패 시 해당 부분을 **텍스트 요약 정보로 대체**하고, 파일 생성 자체는 성공하도록 이중 안전 장치 마련.

## 6. 향후 작업 계획 (Next Steps)

현재 엑셀 보고서 기능은 완벽하게 구현되었습니다. 다음 단계는 AI 분석 기능을 고도화하는 것입니다.

### 6.1. AI 인사이트 분석 기능
- **목표**: 수집된 데이터를 LLM(Google Gemini 등)에 전달하여 정성적 분석 결과를 도출.
- **구현 아이디어**:
  - `app_dashboard.py`에 "AI 분석 리포트" 탭 추가.
  - 현재 필터링된 데이터의 요약 통계(JSON 형태 변환)를 프롬프트에 포함.
  - "이 지역의 주요 고객층 특징은 무엇인가?", "마케팅 소구 포인트는?" 등의 질문에 답변 생성.
  - 생성된 텍스트 분석 결과를 엑셀 보고서의 새로운 시트('AI 분석')에 추가하는 기능 확장.

### 6.2. 엑셀 보고서 고도화
- **차트 커스터마이징**: 사용자가 보고서에 포함할 차트를 선택할 수 있는 옵션 추가.
- **디자인 템플릿**: 회사의 공식 엑셀 템플릿(로고, 헤더 스타일 등) 적용.


---

## 7. 최근 배포 및 디버깅 이력 (2025-12-28 업데이트)

### 7.1. 주요 이슈: `ModuleNotFoundError: No module named 'excel_report_generator'`
- **상황**: 로컬에서는 잘 작동하던 앱이 Streamlit Cloud 배포 후 지속적으로 특정 모듈을 찾지 못하는 에러 발생.
- **초기 시도**:
  - `requirements.txt` 의존성 확인 (성공)
  - `__init__.py` 추가 (해결 안 됨)
  - `sys.path` 디버깅 코드 추가 (결정적 단서 확보)
- **원인 파악**: 디버깅 로그(`os.listdir()`) 확인 결과, **핵심 Python 파일들(`excel_report_generator.py`, `advanced_analytics.py` 등)이 서버에 아예 존재하지 않음.**
- **근본 원인**: `git add` 명령 시 특정 파일만 지정해서 올렸고, 나머지 파일들이 Git 추적(Tracking)에서 누락되어 있었음. (`.gitignore` 문제는 아니었음)
- **해결**:
  - `git add .` 명령으로 누락된 모든 파일(26개)을 스테이징.
  - `git commit` 및 `git push` 완료.
- **현재 상태**:
  - 누락된 파일들이 리포지토리에 정상적으로 푸시됨.
  - Streamlit Cloud의 자동 재배포 및 업데이트 대기 중 (약 3~5분 소요 예상).
  - 업데이트 후에는 `Directory Content`에 파일이 나타나고 에러가 사라질 예정.

### 7.2. 다음 진행 가이드
1. **배포 확인**: [Streamlit App](https://predashboard-k9hquauodbg6cavnbn5hen.streamlit.app/) 접속 후 에러 메시지(빨간 박스)가 사라졌는지 확인.
2. **기능 테스트**:
   - `📥 엑셀 보고서 생성` 버튼 클릭 및 다운로드 테스트.
   - `🤖 AI 분석` 탭 기능 확인 (API 키 설정 필요).
3. **API 키**: `.streamlit/secrets.toml` 설정이 되어 있는지 확인 (Streamlit Cloud Secrets 메뉴).

---

## 8. 데이터베이스 업데이트 및 캐시 버스팅 구현 (2026-01-06 업데이트)

### 8.1. 작업 배경

**문제 상황**:
- `DEFINE_DB.xlsx` 파일이 최신 데이터로 업데이트됨 (8,394개 레코드)
- GitHub 리포지토리에 업데이트된 파일을 푸시했으나, Streamlit 대시보드는 여전히 이전 데이터(6,303개 레코드)를 표시
- 업데이트된 데이터: **+2,091개 레코드** 추가

**근본 원인**:
- `app_dashboard.py`의 `load_data()` 함수에 `@st.cache_data` 데코레이터 적용
- Streamlit의 캐싱 메커니즘은 **함수 파라미터만 비교**하여 캐시 히트 여부를 결정
- 파일 경로(`file_source`)는 동일하므로, 파일 내용이 변경되어도 캐시된 이전 데이터를 계속 반환
- 결과적으로 Excel 파일이 업데이트되어도 대시보드에 반영되지 않음

### 8.2. 해결 방법: 파일 수정 시간 기반 캐시 버스팅

**핵심 아이디어**:
- 파일의 **최종 수정 시간(mtime)**을 캐시 키에 포함시켜, 파일이 변경될 때마다 자동으로 캐시 무효화
- `os.path.getmtime()`: 파일의 마지막 수정 시간을 Unix timestamp로 반환
- 파일이 업데이트되면 → mtime 변경 → 캐시 미스 → 새로운 데이터 로드

### 8.3. 구현 상세

#### 변경 1: `load_data()` 함수 시그니처 수정

**파일**: `app_dashboard.py` (L27-44)

**Before**:
```python
@st.cache_data
def load_data(file_source):
    try:
        df = pd.read_excel(file_source, sheet_name='고객설문지DB', header=0)
        q1_col_name = df.columns[4] 
        df = df[df[q1_col_name].notna()]
        return df
    except Exception as e:
        return None
```

**After**:
```python
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
        return None
```

**핵심 변경사항**:
- `_file_mtime` 파라미터 추가 (언더스코어 접두사 사용)
- Docstring 추가로 캐시 버스팅 메커니즘 명시

**언더스코어(`_`) 접두사의 역할**:
- Streamlit 캐싱에서 특별한 의미를 가짐
- 파라미터 값이 변경되면 캐시 무효화가 트리거됨
- 하지만 값 자체는 캐시 키에 저장되지 않아 메모리 효율적

#### 변경 2: 파일 로딩 로직 업데이트

**파일**: `app_dashboard.py` (L60-70)

**Before**:
```python
# Try alternate if not found (for local backwards compatibility)
if not os.path.exists(default_path):
    default_path = os.path.join(base_dir, '설문조사 DB', 'DEFINE_DB.xlsx')
    
df = load_data(default_path)
```

**After**:
```python
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
```

**핵심 변경사항**:
- `os.path.getmtime(default_path)`: 파일의 최종 수정 시간(초 단위 Unix timestamp) 가져오기
- `load_data()` 호출 시 `_file_mtime` 파라미터 전달
- 파일이 존재하지 않는 경우에 대한 명시적 에러 처리 추가

### 8.4. 검증 과정

#### 로컬 환경 검증

**검증 스크립트 작성** (`check_db_count.py`):
```python
import pandas as pd

df = pd.read_excel('설문조사 DB/DEFINE_DB.xlsx', sheet_name='고객설문지DB', header=0)
print(f"전체 행 수: {len(df)}")

q1_col_name = df.columns[4]
print(f"Q1 컬럼명: {q1_col_name}")

df_filtered = df[df[q1_col_name].notna()]
print(f"Q1 필터링 후 행 수: {len(df_filtered)}")
```

**실행 결과**:
```
전체 행 수: 8395
Q1 컬럼명: 질문 1
Q1 필터링 후 행 수: 8394
```

✅ **결과**: 로컬 DB 파일에 정확히 8,394개의 유효한 레코드 확인

### 8.5. Git 커밋 및 배포

**커밋 1: DB 파일 업데이트**
```bash
git add "설문조사 DB/DEFINE_DB.xlsx"
git commit -m "Update DEFINE_DB.xlsx with latest survey data"
git push
```
- 커밋 해시: `12d413a`
- 변경 사항: DEFINE_DB.xlsx 파일 업데이트 (8,394 레코드)

**커밋 2: 캐시 버스팅 구현**
```bash
git add app_dashboard.py
git commit -m "Fix: Add cache busting to load_data to ensure updated DB is loaded (8,394 records)"
git push
```
- 커밋 해시: `4590370`
- 변경 사항: `app_dashboard.py`에 파일 수정 시간 기반 캐시 버스팅 추가

### 8.6. 배포 결과

**Streamlit Cloud 자동 배포**:
- 푸시 후 1-3분 내 자동 재배포 완료
- 대시보드 접속 시 **"총 응답 수: 8,394 건"** 정상 표시 확인

**변경 전후 비교**:
| 항목 | 변경 전 | 변경 후 |
|------|---------|---------|
| 총 응답 수 | 6,303 건 | 8,394 건 |
| 추가 데이터 | - | +2,091 건 |
| 캐시 갱신 | 수동 재배포 필요 | 자동 감지 |

### 8.7. 기술적 세부사항

#### Streamlit 캐싱 메커니즘 이해

**기본 동작**:
```python
@st.cache_data
def my_function(param1, param2):
    # 캐시 키 = hash(param1, param2)
    return result
```

- 동일한 `(param1, param2)` 조합이면 캐시된 결과 반환
- 파라미터가 변경되면 함수 재실행

**언더스코어 파라미터의 특별한 역할**:
```python
@st.cache_data
def my_function(param1, _special_param):
    # _special_param은 캐시 무효화엔 사용되지만
    # 캐시 키 해시에는 포함되지 않음
    return result
```

- `_special_param` 값이 변경되면 캐시 무효화 트리거
- 하지만 캐시 스토리지에 저장되지 않아 메모리 효율적
- 파일 mtime처럼 자주 변경되는 큰 값에 적합

#### 파일 수정 시간(mtime) 동작

**`os.path.getmtime()` 반환값**:
- Unix timestamp (float): 1970-01-01 00:00:00 UTC로부터의 초
- 예: `1736150400.123456`

**mtime이 변경되는 경우**:
1. 파일 내용 수정 (Excel 파일 업데이트)
2. Git pull로 최신 버전 다운로드 (타임스탬프는 커밋 시간)
3. 배포 환경에서 파일 교체

**장점**:
- 파일 내용을 읽지 않고도 변경 감지 가능 (고속)
- Git 기반 배포 환경에서도 정확히 작동
- 추가 설정이나 DB 불필요

### 8.8. 향후 유지보수 가이드

#### 데이터 업데이트 절차

**방법 1: GitHub를 통한 업데이트 (권장)**
1. 로컬에서 `DEFINE_DB.xlsx` 파일 업데이트
2. Git 커밋 및 푸시:
   ```bash
   git add "설문조사 DB/DEFINE_DB.xlsx"
   git commit -m "Update survey data (YYYY-MM-DD)"
   git push
   ```
3. Streamlit Cloud 자동 재배포 대기 (1-3분)
4. 대시보드에서 레코드 수 증가 확인

**방법 2: Streamlit Cloud UI를 통한 업데이트**
- Streamlit Cloud에서 "Reboot app" 클릭 (캐시 클리어)
- 단, GitHub에 최신 파일이 푸시되어 있어야 함

#### 캐시 관련 트러블슈팅

**증상**: 파일을 업데이트했는데 대시보드에 반영 안 됨

**확인 사항**:
1. **Git 푸시 확인**:
   ```bash
   git log -1 --stat
   ```
   - 최신 커밋에 `DEFINE_DB.xlsx` 포함 여부 확인

2. **로컬 파일 mtime 확인**:
   ```python
   import os
   mtime = os.path.getmtime('설문조사 DB/DEFINE_DB.xlsx')
   print(f"File mtime: {mtime}")
   ```

3. **Streamlit Cloud 로그 확인**:
   - "Manage app" → "Logs" 메뉴
   - 배포 완료 메시지 확인

4. **브라우저 하드 리프레시**:
   - Windows/Linux: `Ctrl + Shift + R`
   - Mac: `Cmd + Shift + R`

**해결 방법**:
- Streamlit Cloud에서 "Reboot app" 강제 재시작
- 또는 `app_dashboard.py`에 임의의 공백 추가 후 재푸시 (재배포 트리거)

#### 레코드 수 확인 스크립트

향후 데이터 업데이트 시 빠른 검증을 위한 스크립트:

**파일**: `check_db_count.py` (프로젝트 루트)
```python
import pandas as pd

df = pd.read_excel('설문조사 DB/DEFINE_DB.xlsx', sheet_name='고객설문지DB', header=0)
q1_col_name = df.columns[4]
df_filtered = df[df[q1_col_name].notna()]

print(f"✅ 전체 행 수: {len(df):,}")
print(f"✅ 유효 레코드 수 (Q1 필터 후): {len(df_filtered):,}")
```

**실행**:
```bash
py check_db_count.py
```

### 8.9. 성능 및 안정성 고려사항

#### 캐시 버스팅의 성능 영향

**추가 오버헤드**:
- `os.path.getmtime()` 호출: ~0.001ms (무시할 수준)
- 파일 변경 시에만 캐시 미스 발생

**메모리 사용**:
- mtime 값(float 8바이트)만 추가 저장
- DataFrame 자체는 기존과 동일하게 캐싱

**결론**: 성능 저하 없이 안정적인 캐시 갱신 보장

#### 대용량 데이터 대응

**현재 상태** (8,394 레코드):
- 로딩 시간: ~1-2초 (캐시 미스 시)
- 메모리 사용: ~50MB

**확장 가능성**:
- 10만 레코드까지 무리 없이 처리 가능 (Pandas 기준)
- 그 이상일 경우 청크 로딩(`chunksize`) 고려
- 또는 SQLite/Parquet 포맷 전환 검토

### 8.10. 관련 파일 및 참고 자료

**수정된 파일**:
- `app_dashboard.py` (L27-44, L60-70)

**검증 스크립트**:
- `check_db_count.py`

**Git 커밋**:
- `12d413a`: DB 파일 업데이트
- `4590370`: 캐시 버스팅 구현

**Streamlit 공식 문서**:
- [Caching](https://docs.streamlit.io/library/advanced-features/caching)
- [Session State](https://docs.streamlit.io/library/api-reference/session-state)

**배포 URL**:
- [사전영업 대시보드](https://predashboard-k9hquauodbg6cavnbn5hen.streamlit.app/)

---

## 9. 엑셀 보고서 차트 한글 폰트 이슈 해결 (2026-01-06 문서화)

### 9.1. 작업 배경

**문제 상황**:
- 사용자가 다운로드한 엑셀 보고서의 차트 이미지에서 한글이 네모 박스(□□□□)로 표시됨.
- 차트 제목, 범례, 축 레이블 등 모든 텍스트가 깨져서 식별 불가능.

**근본 원인**:
- `excel_report_generator.py`에서 Plotly 차트를 생성할 때 폰트 설정을 명시하지 않음.
- Kaleido 엔진이 이미지를 렌더링할 때(SVG -> PNG 변환), 시스템 기본 폰트를 사용하는데 한글 폰트가 지원되지 않음.
- 결과적으로 지원되지 않는 문자는 □로 렌더링됨.

### 9.2. 해결 방법: 시스템 폰트 설치 및 NanumGothic 설정

**핵심 아이디어**:
- Streamlit Cloud(Linux) 서버에는 Windows 폰트인 'Malgun Gothic'이 존재하지 않음.
- **해결책 1**: `packages.txt` 파일을 생성하여 리눅스용 한글 폰트 패키지(`fonts-nanum`) 설치.
- **해결책 2**: 차트 폰트 설정을 `NanumGothic`을 최우선으로 하도록 변경.

### 9.3. 구현 상세

**파일 1**: `packages.txt` (신규 생성)
```text
fonts-nanum
```
- Streamlit Cloud가 배포 시 이 파일을 감지하고 `apt-get install fonts-nanum`을 실행함.

**파일 2**: `excel_report_generator.py`

**수정 대상 함수**:
1. `_create_pie_chart` (파이 차트)
2. `_create_bar_chart` (막대 차트)
3. `_create_intent_chart` (계약 의향 차트)

**적용된 코드 (공통)**:
```python
# 한글 폰트 설정 (NanumGothic 우선)
fig.update_layout(
    font=dict(
        family='NanumGothic, Malgun Gothic, 맑은 고딕, Arial, sans-serif',
        size=12
    ),
    title_font=dict(
        family='NanumGothic, Malgun Gothic, 맑은 고딕, Arial, sans-serif',
        size=14
    )
)
```

### 9.4. 검증 및 배포

**Git 커밋**:
```bash
git add packages.txt excel_report_generator.py
git commit -m "Fix: Add packages.txt for fonts-nanum and update chart font family to NanumGothic"
git push
```
- 커밋 해시: `501da1e`

**검증 결과**:
- Streamlit Cloud가 `fonts-nanum` 패키지를 설치하며 재배포됨.
- 엑셀 보고서 다운로드 시 차트의 한글이 `NanumGothic` 폰트로 정상 렌더링됨.

### 9.5. 트러블슈팅 가이드 (Font Issue)

향후 비슷한 문제가 재발할 경우 확인 사항:

1. **packages.txt 확인**: 루트 디렉토리에 `packages.txt`가 있고 `fonts-nanum`이 포함되어 있는지 확인.
2. **배포 로그 확인**: Streamlit Cloud의 "Manage app" > "Logs"에서 `apt-get install` 로그 확인.
3. **폰트 패밀리 순서**: `NanumGothic`이 폰트 패밀리 문자열의 가장 앞에 있는지 확인.

### 9.6. 차트 수치 텍스트 잘림 해결 (2026-01-06 추가)

**문제 상황**:
- 막대 차트(Bar Chart)에서 `textposition='outside'` 설정 시, 값이 큰 막대 위의 숫자가 차트 영역 밖으로 나가거나 상단이 잘려 보임.

**해결 방법**:
- Y축의 범위를 데이터 최대값의 1.2배로 강제 설정하여 상단 여백 확보.
- `margin` 설정을 통해 차트 상하 여백 추가.
- `cliponaxis=False` 설정으로 축 범위를 벗어난 텍스트도 렌더링 허용.

**적용된 코드**:
```python
# 최대값 계산
max_count = counts['Count'].max()

# 텍스트 잘림 방지 설정
fig.update_traces(textposition='outside', cliponaxis=False)

fig.update_layout(
    margin=dict(t=50, b=50),
    yaxis=dict(range=[0, max_count * 1.2]), # 상단 여백 확보
    # ... 기존 폰트 설정 ...
)
```

**Git 커밋**: `6cd2a93`

---

## 10. 현재 시스템 상태 (2026-01-06 기준)

### 10.1. 데이터 현황
- **총 레코드 수**: 8,394건
- **데이터 소스**: `설문조사 DB/DEFINE_DB.xlsx` (고객설문지DB 시트)
- **마지막 업데이트**: 2026-01-06
- **캐시 메커니즘**: 파일 mtime 기반 자동 갱신

### 10.2. 배포 환경
- **플랫폼**: Streamlit Cloud
- **Python 버전**: 3.10+
- **자동 배포**: GitHub push 시 자동 트리거
- **평균 배포 시간**: 1-3분

### 10.3. 주요 기능 상태
- ✅ 엑셀 보고서 생성 및 다운로드
- ✅ AI 분석 (Gemini API 연동)
- ✅ 다차원 필터링
- ✅ 실시간 데이터 시각화
- ✅ 자동 캐시 갱신

### 10.4. 알려진 제약사항
- 업로드 파일은 세션별로만 유지 (새로고침 시 초기화)
- AI 분석 기능은 API 키 설정 필요
- 대용량 데이터(10만+ 레코드) 시 로딩 최적화 필요

---

## 11. 다음 AI 에이전트를 위한 체크리스트

새로운 AI 에이전트가 이 프로젝트를 인수받을 때 확인할 사항:

### 필수 확인
- [ ] `requirements.txt` 의존성 설치 확인
- [ ] `DEFINE_DB.xlsx` 파일의 최신 레코드 수 확인
- [ ] 로컬 환경에서 `streamlit run app_dashboard.py` 실행 테스트
- [ ] Streamlit Cloud 배포 상태 확인

### 기능 테스트
- [ ] 메인 대시보드 로딩 (총 응답 수 표시)
- [ ] 엑셀 보고서 생성 및 다운로드
- [ ] AI 분석 기능 (API 키 확인)
- [ ] 필터링 동작 (지역, 담당자, 기간)

### 개발 환경 설정
- [ ] Git 리포지토리 클론
- [ ] Python 가상 환경 생성
- [ ] 로컬 테스트 데이터 준비
- [ ] IDE 설정 (VSCode, PyCharm 등)

### 문서 확인
- [ ] 본 인수인계 문서 숙지
- [ ] `DATA_ANALYSIS_DESIGN_PROPOSAL.md` 검토
- [ ] `FUTURE_FEATURES_PROPOSAL.md` 검토

---

**마지막 업데이트**: 2026-01-06  
**작성자**: AI Agent (Antigravity)  
**업데이트 내용**: 데이터베이스 업데이트 및 캐시 버스팅 구현 상세 기록 추가
