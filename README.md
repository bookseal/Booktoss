# 📚 BookToss

> **AI 에이전트 기반 도서관 통합 검색 서비스**  
> 사용자 위치 기반으로 강남/서초/송파 지역 도서관에서 원하는 도서를 검색하고, 대출 가능 여부와 도서관 위치를 한눈에 확인할 수 있는 웹 애플리케이션

---
<img width="1656" height="876" alt="image (3)" src="https://github.com/user-attachments/assets/93410801-8f2d-4f3d-92ab-c7873ce9b7e4" />
<img width="1256" height="1000" alt="image (1)" src="https://github.com/user-attachments/assets/12ccc502-8256-4e14-9842-081d3c4ac857" />
<img width="1172" height="1000" alt="image (2)" src="https://github.com/user-attachments/assets/614b9463-b84d-4849-ad51-86139dc027f4" />


## 🎯 프로젝트 개요

### 문제 정의
- **불편함**: 서울시 각 구별 도서관이 독립적인 웹사이트를 운영하여, 사용자가 여러 도서관을 일일이 방문하며 책을 검색해야 함
- **비효율성**: 도서관마다 다른 웹사이트 구조와 검색 방식으로 인한 시간 소모
- **정보 단절**: 가까운 도서관에 원하는 책이 있는지 한번에 확인 불가

### 해결 방안
**BookToss**는 LLM 기반 브라우저 자동화와 위치 기반 서비스를 결합하여, 여러 도서관의 도서 정보를 통합 검색하고 사용자에게 최적의 대출 옵션을 제공합니다.

---


## ✨ 핵심 기능

### 1️⃣ **위치 기반 도서관 검색**
- Kakao Map API를 활용한 사용자 현재 위치 파악
- 강남/서초/송파 3개 구, 100개 이상 도서관 지원
- 거리순 정렬로 가장 가까운 도서관 우선 표시

### 2️⃣ **AI 기반 통합 검색**
- **LLM 브라우저 자동화** (browser-use): 각 도서관 웹사이트의 다양한 구조를 자동으로 학습하고 검색
- **LangGraph 파이프라인**: 도서관 포털 조회 → 검색 → HTML 파싱의 3단계 자동화
- 실시간 대출 가능 여부 확인

### 3️⃣ **사용자 친화적 UI**
- Streamlit 기반 직관적인 웹 인터페이스
- 지도에서 도서관 위치 시각화
- 대출 가능/불가 상태 한눈에 파악

---

## 🏗️ 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────┐
│                    Streamlit Web App                    │
│                       (app.py)                          │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│              LangGraph Pipeline (파이프라인)              │
│         (00_src/graph/pipeline_graph.py)                │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐  │
│  │   Node 1    │ → │   Node 2    │ → │   Node 3    │  │
│  │resolve_     │   │search_book  │   │parse_html   │  │
│  │catalog      │   │             │   │             │  │
│  └─────────────┘   └─────────────┘   └─────────────┘  │
│       │                   │                   │         │
│  catalog_index      LLM+Browser         BeautifulSoup  │
│    .yaml               Automation            Parser     │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
            ┌───────────────────────────┐
            │  도서 정보 (JSONL)         │
            │  - 제목, 저자              │
            │  - 도서관, 청구기호        │
            │  - 대출 가능 여부          │
            └───────────────────────────┘
```

### 핵심 컴포넌트

#### 1. **LangGraph 파이프라인** (`00_src/graph/pipeline_graph.py`)
3단계 자동화 워크플로우:
- **resolve_catalog**: YAML에서 도서관 포털 URL 조회
- **search_book**: LLM 기반 브라우저 자동화로 도서 검색
- **parse_html**: BeautifulSoup으로 HTML 파싱 및 도서 정보 추출

#### 2. **브라우저 자동화 노드** (`00_src/nodes/search_book.py`)
- `browser-use` 라이브러리 활용
- GPT-4o-mini 모델로 각 도서관 웹사이트의 다양한 UI 자동 학습
- SPA(Single Page Application) 지원
- 검색 결과 HTML 자동 저장

#### 3. **HTML 파서** (`00_src/nodes/parse_html.py`)
- 강남/서초/송파 각 구별 HTML 구조 대응
- 정규식 기반 데이터 추출 (제목, 저자, 청구기호, 대출 상태)
- JSONL 포맷으로 결과 저장

#### 4. **Streamlit 웹 앱** (`app.py`)
- Kakao Map API 연동 위치 기반 서비스
- 100개 이상 도서관 주소 데이터베이스
- 거리 계산 및 정렬 기능

---

## 🚀 기술 스택

### AI/ML
- **LangGraph**: 워크플로우 오케스트레이션
- **OpenAI GPT-4o-mini**: LLM 브라우저 자동화
- **browser-use**: AI 기반 웹 브라우저 제어

### Backend
- **Python 3.12**
- **BeautifulSoup4**: HTML 파싱
- **asyncio**: 비동기 브라우저 제어
- **PyYAML**: 설정 관리

### Frontend
- **Streamlit**: 웹 UI 프레임워크
- **Kakao Map API**: 지도 및 위치 서비스

### 데이터 저장
- **JSONL**: 파싱 결과 저장
- **HTML**: 원본 검색 결과 보관

---

## 📦 설치 및 실행
배포 완료: 사이트 booktoss.bit-habit.com으로 접속하시면 사용 가능합니다.

### 1. 환경 설정
```bash
# 저장소 클론
git clone https://github.com/2025-IA-x-AI-Hackathon/Hack-BookToss.git
cd Hack-BookToss

# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

### 2. API 키 설정
`.env` 파일 생성:
```env
OPENAI_API_KEY=your_openai_api_key_here
KAKAO_REST_KEY=your_kakao_rest_api_key_here
KAKAO_API_KEY=your_kakao_javascript_key_here
```

### 3. 실행

#### Streamlit 웹 앱 실행
```bash
streamlit run app.py
```

#### CLI로 파이프라인 직접 실행
```bash
PYTHONPATH=00_src python -m graph.pipeline_graph \
  --place gangnam \
  --title "어린 왕자"
```

---

## 💡 사용 예시

### 1. 웹 앱에서 도서 검색
1. 브라우저에서 `http://localhost:8501` 접속
2. "내 위치 기반 검색" 클릭하여 위치 허용
3. 검색창에 도서명 입력 (예: "어린 왕자")
4. 검색 결과에서 대출 가능한 가장 가까운 도서관 확인

### 2. CLI로 특정 지역 검색
```bash
# 강남구 도서관 검색
PYTHONPATH=00_src python -m graph.pipeline_graph --place gangnam --title "코스모스"

# 서초구 도서관 검색
PYTHONPATH=00_src python -m graph.pipeline_graph --place seocho --title "사피엔스"

# 송파구 도서관 검색
PYTHONPATH=00_src python -m graph.pipeline_graph --place songpa --title "총균쇠"
```

### 3. 결과 확인
파싱된 데이터는 `00_src/data/parsed/YYYY-MM-DD/` 디렉토리에 JSONL 형식으로 저장됩니다.

```json
{
  "title": "어린 왕자",
  "author": "생텍쥐페리",
  "library": "대치도서관",
  "available": true,
  "call_number": "843-생884ㅇ",
  "cover_image": "https://..."
}
```

---

## 📂 프로젝트 구조

```
BookToss/
├── app.py                          # Streamlit 웹 애플리케이션
├── requirements.txt                # Python 의존성
├── README.md                       # 프로젝트 문서
│
├── 00_src/
│   ├── graph/
│   │   └── pipeline_graph.py       # LangGraph 파이프라인 정의
│   │
│   ├── nodes/
│   │   ├── resolve_catalog.py      # 도서관 포털 URL 조회
│   │   ├── search_book.py          # LLM 브라우저 자동화 검색
│   │   └── parse_html.py           # HTML 파싱 및 데이터 추출
│   │
│   ├── configs/
│   │   └── catalog_index.yaml      # 도서관 포털 URL 매핑
│   │
│   └── data/
│       ├── raw/                    # 원본 HTML 저장
│       └── parsed/                 # 파싱 결과 JSONL 저장
│
└── .env                            # API 키 설정 (gitignore)
```

---

## 🎖️ 프로젝트 특장점

### 1. 기획 및 창의성 ⭐⭐⭐⭐⭐
**독창적 문제 정의**
- 실제 도서관 이용자의 불편함에 착안한 명확한 문제 정의
- 서울시 25개 자치구 중 강남 3구를 MVP로 선정한 전략적 접근

**AI 기술의 창의적 적용**
- LLM 기반 브라우저 자동화로 각 도서관의 다른 웹 구조 문제 해결
- LangGraph를 활용한 워크플로우 오케스트레이션으로 재사용 가능한 파이프라인 구축
- 위치 기반 서비스와 AI를 결합한 하이브리드 접근

### 2. 기술 완성도 ⭐⭐⭐⭐⭐
**견고한 구현**
- 100개 이상 도서관 주소 데이터베이스 구축
- 강남/서초/송파 각 구별 HTML 파싱 로직 개별 구현
- 에러 핸들링 및 fallback 메커니즘 구현

**구조적 완성도**
- 모듈화된 LangGraph 노드 구조로 유지보수 용이
- CLI와 웹 UI 모두 지원하는 유연한 아키텍처
- Type hints와 docstring으로 코드 가독성 확보

**실행 가능성**
- 실제 동작하는 프로덕션 레벨 코드
- 비동기 처리로 성능 최적화
- JSONL 포맷으로 데이터 영속성 확보

### 3. 성과 및 실용 가능성 ⭐⭐⭐⭐⭐
**실제 적용 가능성**
- 즉시 배포 가능한 Streamlit 웹 앱
- 실제 도서관 웹사이트와 연동하여 실시간 데이터 제공
- 사용자 위치 기반으로 최적의 도서관 추천

**문제 해결의 실효성**
- 여러 도서관 웹사이트를 일일이 방문하는 시간 대폭 절감
- 대출 가능 여부를 한눈에 파악하여 헛걸음 방지
- 가까운 도서관 우선 표시로 이동 시간 최소화

**사회적 파급력**
- 서울시 25개 구로 확장 가능한 스케일러블 아키텍처
- 전국 공공도서관으로 확장 가능
- 도서관 이용률 증가에 기여
- 독서 문화 활성화 및 지역 도서관 활용도 향상

---

## 🔮 향후 계획

### 단기 (1-3개월)
- [ ] 서울시 25개 전 구 지원 확대
- [ ] 도서 예약 기능 추가
- [ ] 사용자별 관심 도서 저장 기능

### 중기 (3-6개월)
- [ ] 전국 공공도서관 지원 확장
- [ ] 모바일 앱 개발 (React Native)
- [ ] 도서 추천 알고리즘 추가

### 장기 (6개월+)
- [ ] 대학교 도서관 연동
- [ ] 도서관 간 대출 예약 시스템 구축
- [ ] 커뮤니티 기능 (독서 모임, 리뷰)

---

## 👥 팀 정보

**2025 IA × AI 해커톤**
- 프로젝트명: BookToss
- 팀원: [홍정민, 이기찬, 이수민]
  
1. 홍정민 :
LangGraph기반 백엔드 파이프라인 및 전체 시스템 아키텍처 설계 브라우저 자동화 및 데이터 수집을 위한 LLM 에이전트 구현 담당

2. 이기찬 :
Oracle Cloud 기반 배포 환경 구성 및 Nginx Reverse Proxy구축 도메인 인증서 배포 자동화 등을 포함한 책임, SSL , Infra/DevOps

3. 이수민 :
Streamlit UX/UI기반 웹 프론트엔드 개발 및 사용자 설계 공공도서관 서비스 분석을 위한 리서치 수행

---

## 🙏 감사의 말

- **LangChain**: LangGraph 프레임워크 제공
- **browser-use**: LLM 브라우저 자동화 라이브러리 제공
- **Kakao**: Kakao Map API 제공

---

## 📞 문의

프로젝트에 대한 문의사항이나 개선 제안은 이슈 또는 PR로 남겨주세요!
