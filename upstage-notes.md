# Upstage 제품 체험 노트 (지원서 피드백 원천)

> Upstage 지원서의 "제품 체험 후 평가" 문항을 채우기 위한 **개인 로그**.
> BookToss를 만들며 Solar 등 Upstage 제품을 직접 만질 때마다, 그 순간의 솔직한 인상을 한두 줄 남긴다.
> 공개되지 않도록 `docs/`(GitHub Pages) 밖, 저장소 루트에 둔다. 커밋 히스토리로 "어떤 작업 때 받은 인상인지" 자동 추적된다 (`git log -- upstage-notes.md`).
>
> 제품 영역 태그: `Chat/Reasoning` · `Doc Digitization` · `Info Extraction` · `Console/DX`(콘솔·개발경험)
> 새 엔트리는 **맨 위에** 추가한다 (최신순).

---

## 2026-06-27 · v0.0.2 (`solar-pro2`) · `Chat/Reasoning` · Open Question (제품팀 송부 후보)

> 표준 피드백 형식: 관찰 → 이미 알아본 것 → Solar 쪽 → 열린 질문 → 증거.

- **관찰(Observation):** 미출시 서비스 "BookToss"를 한 문장으로 소개시키자(근거 없는 단발 질문), 준 단서(이름 + "도서관 검색 서비스") 밖의 내용을 **확신처럼** 생성. 추측을 추측이라 표시하지 못함(weak metacognition).
- **이미 알아본 것(What I found):** OpenAI *Why LMs Hallucinate*(2025, arXiv 2509.04664) — 평가가 추측을 보상. Kalai-Vempala *Calibrated LMs Must Hallucinate* — 보정된 모델은 수학적으로 환각 불가피. 완화책: RAG · abstention(R-Tuning "모르겠다") · verbalized confidence(VUC 헤지 표현).
- **Solar 쪽(이미 있는 답):** Upstage **Groundedness Check API** — (context, answer) groundedness를 외부 검증기로 채점 + 신뢰도. RAG와 짝지어 "거의 0 환각".
- **열린 질문(Open Question):** solar-pro2 자체에 abstention/verbalized-confidence가 내장돼 가는가, 아니면 Groundedness Check를 별도로 붙이는 게 권장 경로인가? 근거 없는 단발 프롬프트에서 모델이 스스로 "근거 없음"을 표시하는 방향의 계획은?
- **심각도/증거:** Low (토이 단발 프롬프트). 증거 = main `25db28c` (#9), `solar.py`. 실제 위험은 사용자에게 미고지된 사실을 단정할 때 → v0.1.0 RAG + Groundedness Check로 완화 예정.

---

## 2026-06-27 · v0.0.2 (`solar-pro2`) · `Chat/Reasoning`

**Q. 첫 답변 품질은? (추측을 자연스럽게 했나 / 추측임을 표시했나)**

A. **추측 자체는 좋았다.** 이름 "BookToss"(Book+Toss)가 의미를 잘 담아, 모델이 합리적인 한 문장 카피를 생성. 다만 그게 *추측*이라는 걸 스스로 알리지 못함 — 잘 맞히지만 "내가 모른다는 걸 모르는" 수준. (→ 위 Open Question으로 이어짐)

---

## 2026-06-27 · v0.0.2 (`feat/v0.0.2-solar-connect`) · `Console/DX`

**Q. 콘솔에서 `UPSTAGE_API_KEY`를 발급받는 과정 — 막힘 없이 됐나요? OpenAI 등 다른 LLM 콘솔과 비교해 더 쉬웠거나 헷갈렸던 지점은?**

A. 막힘없이 발급됐다. OpenAI보다 간편 — **신용카드 정보를 입력하지 않아도** 키가 나왔다. (진입장벽이 낮아 "일단 써보기"가 쉬움)

**첫 호출 결과:** `python solar.py` 한 번에 성공. base_url만 바꾼 OpenAI SDK가 그대로 동작 → OpenAI 경험이 있으면 학습 비용 0에 가까움.
