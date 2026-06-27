# CLAUDE.md — BookToss v2 working agreement

BookToss(서울 도서관 100+곳을 한 번에 검색하는 AI 에이전트)를 **처음부터 다시**,
**Upstage Solar** 위에서 만든다. 작업은 **튜토리얼 주도(tutorial-driven)** 로 진행한다:
Claude가 각 단계의 튜토리얼 HTML을 먼저 써주고, 사람은 그걸 보며 따라 한다. (따라 할 todo 같은 느낌)

원본 해커톤 프로젝트는 `docs/v1/`에 보존돼 있다 — 바퀴를 재발명하지 말고 거기서 골라 쓴다
(특히 `docs/v1/00_src/configs/catalog_index.yaml` 도서관 URL 맵, 파싱 규칙).

## 마일스톤 루프 (매 버전마다 이 순서로)

1. **Issue** — `gh issue create`. 본문에 그 버전의 할 일을 **체크리스트**로 적는다 (계획).
2. **튜토리얼 먼저** — `docs/index.html`에 그 버전 섹션을 **코드보다 먼저** 쓴다.
   Claude가 "이렇게 하면 된다"를 적고, 사람이 읽고 따라간다.
3. **Branch** — `git checkout -b <type>/<slug>` (main에서 분기).
4. **Code** — 실제 구현. 끝나면 튜토리얼 섹션에 막혔던 지점/명령어를 채운다.
5. **PR** — `gh pr create`, 본문에 `Closes #N`.
6. **Merge** — **squash** 머지 + 브랜치 삭제. main의 `/docs`에서 Pages가 자동 재배포된다.

> 작은 변경(문서 한 줄이라도)도 이 루프를 탄다. 워크플로는 작은 데서 연습해 둔다.

## 컨벤션

- **버전 스킴**: `v0.0.1` → `v0.1.0`. 각 버전은 *끝나면 눈으로 확인되는 결과물* 하나.
  전체 로드맵은 튜토리얼 페이지 `#roadmap` 섹션에 있다.
- **브랜치 네이밍**: `docs/…`, `feat/…`, `fix/…`, `chore/…`.
- **커밋**: 마지막 줄에 `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`.
- **머지**: 기본 squash. PR↔issue는 `Closes #N`으로 묶는다.
- **금지**: 사용자가 요청하지 않는 한 main에 직접 push 하지 않는다 (항상 PR 경유).

## 학습 + Upstage 피드백 루프

이 프로젝트의 숨은 목적: 사용자가 **Upstage 지원서의 "제품 체험 후 평가" 문항**을 채울 근거를 모은다.
그래서 Claude는 다음을 지킨다:

- **코드 전달 방식**: learning mode지만 `TODO(human)`으로 넘기지 않는다. 사용자가 따라 칠 수 있게
  **완성된 코드를 출력(채팅)으로 제시**한다. 사용자가 직접 타이핑하며 익힌다.
- **매 대화/단계마다** Upstage 제품(Solar = Chat/Reasoning, Document Digitization, Information Extraction,
  Console/DX)을 만지는 순간에 맞춰 **메타인지 질문 1~2개**를 던진다 (짧게, 한 줄 답이면 충분).
- 사용자의 답은 루트 `upstage-notes.md`에 **최신순**으로 누적한다. 각 엔트리에 `날짜시간 · 버전/브랜치 ·
  제품영역 태그`를 박는다. 출처(어떤 작업 때의 인상인지)는 git이 추적하므로 SHA는 손으로 안 적는다.

## 튜토리얼 페이지

- `docs/index.html` — **단일 스크롤 페이지** 하나. 방문자는 클릭하지 않고 스크롤로 본다.
  섹션 순서: hero+목차 → 소개(what) → 왜 Solar → 전체 그림 → 로드맵 → (버전별 섹션이 아래로 누적).
- `docs/assets/style.css` — 공용 스타일. `.nojekyll`로 Jekyll 우회(손으로 쓴 정적 HTML).
- 본문 언어는 한국어, 명령어/코드는 영어.
- **세 독자**를 위해 쓴다: 따라 하는 개발자 · 포트폴리오 방문자 · Claude(다음 단계 맥락).
- 배포: GitHub Pages, 소스 = `main` 브랜치 `/docs`. main에 push되면 자동 갱신.
  (소스 변경/푸시가 자동 빌드를 안 할 때가 있으니, 안 바뀌면 빌드 커밋 SHA를 main HEAD와 대조.)

## 기술 스택 (목표)

| 레이어 | 기술 | 메모 |
|---|---|---|
| LLM | **Upstage Solar** (`solar-pro2`) | OpenAI 호환. `base_url=https://api.upstage.ai/v1`, key `UPSTAGE_API_KEY` (`.env`) |
| 브라우저 | Playwright (+ 필요 시 browser-use) | 도서관 사이트 자동 검색 |
| 파이프라인 | LangGraph | `resolve_catalog → search_book → parse_html` |
| 앱 | Streamlit | 웹 UI · 지도 |

## 저장소 메모

- 소유자 `bookseal`. 기본 브랜치 `main`. Pages: https://bookseal.github.io/Booktoss/
- 큰 바이너리(`docs/v1/*.mp4|hwp|pdf`)와 `docs/v1/00_src/data/raw/`는 gitignore — git에 넣지 않는다.
- 옛 작업 브랜치 `linux-compat`, `playwright-only`는 v1 실험 잔재 (참고용).
