# 📚 BookToss v2

> Rebuild from scratch — searching 100+ Seoul libraries at once with an AI agent,
> this time powered by **Upstage Solar** instead of OpenAI.

---

## 👉 전체 과정은 한 페이지로 정리돼 있습니다

### **▶︎ https://bookseal.github.io/Booktoss/**

빈 폴더에서 시작해 도서관 검색 AI를 한 걸음씩 완성하는 **단계별 튜토리얼**입니다.
스크롤 한 번으로 전 과정을 읽을 수 있고, 명령어를 그대로 따라 하면 누구나 재현할 수 있습니다.
각 단계마다 *무엇을* 했는지뿐 아니라 ***왜*** 그렇게 했는지를 적었습니다.

> 이 README는 입구일 뿐입니다. **실제 내용·코드·설명은 위 페이지에 있습니다.**
> 개발자도, 저장소를 구경하는 사람도, AI 페어(Claude)도 모두 이 페이지를 봅니다.

[![튜토리얼 보러 가기](https://img.shields.io/badge/📖_튜토리얼_보러_가기-bookseal.github.io%2FBooktoss-6ea8fe?style=for-the-badge)](https://bookseal.github.io/Booktoss/)

---

## 한눈에

| | |
|---|---|
| **무엇** | 서울 100+ 도서관을 한 번에 검색하는 AI 에이전트 |
| **이번 변화** | 두뇌를 OpenAI → **Upstage Solar** (`solar-pro2`) 로 교체 |
| **스택(목표)** | Solar · browser-use · LangGraph · Streamlit |
| **방식** | 빈 루트에서 한 step씩 — 과정을 전부 문서화 |

## 진행 상황

| Step | 내용 | 상태 |
|------|------|------|
| 0 | 깨끗한 출발점 — orphan 시작, v1을 `docs/v1/`에 보존 | ✅ |
| 1 | 프로젝트 뼈대 (`src/` 레이아웃 · 의존성 · 환경변수) | ⏳ |

전체 설명은 → **https://bookseal.github.io/Booktoss/**

## v1 원본 (참고용)

`docs/v1/`에 원본 해커톤 프로젝트(`app.py`, `00_src/` LangGraph 파이프라인,
`catalog_index.yaml` 도서관 맵, 발표 자료)가 그대로 보존돼 있습니다. 재사용할
부분(도서관 URL 설정, HTML 파싱 규칙)만 골라 v2로 옮깁니다.
