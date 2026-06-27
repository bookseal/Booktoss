# Upstage 제품 체험 노트 (지원서 피드백 원천)

> Upstage 지원서의 "제품 체험 후 평가" 문항을 채우기 위한 **개인 로그**.
> BookToss를 만들며 Solar 등 Upstage 제품을 직접 만질 때마다, 그 순간의 솔직한 인상을 한두 줄 남긴다.
> 공개되지 않도록 `docs/`(GitHub Pages) 밖, 저장소 루트에 둔다. 커밋 히스토리로 "어떤 작업 때 받은 인상인지" 자동 추적된다 (`git log -- upstage-notes.md`).
>
> 제품 영역 태그: `Chat/Reasoning` · `Doc Digitization` · `Info Extraction` · `Console/DX`(콘솔·개발경험)
> 새 엔트리는 **맨 위에** 추가한다 (최신순).

---

## 2026-06-27 · v0.0.2 (`feat/v0.0.2-solar-connect`) · `Console/DX`

**Q. 콘솔에서 `UPSTAGE_API_KEY`를 발급받는 과정 — 막힘 없이 됐나요? OpenAI 등 다른 LLM 콘솔과 비교해 더 쉬웠거나 헷갈렸던 지점은?**

A. 막힘없이 발급됐다. OpenAI보다 간편 — **신용카드 정보를 입력하지 않아도** 키가 나왔다. (진입장벽이 낮아 "일단 써보기"가 쉬움)

**첫 호출 결과:** `python solar.py` 한 번에 성공. base_url만 바꾼 OpenAI SDK가 그대로 동작 → OpenAI 경험이 있으면 학습 비용 0에 가까움.
