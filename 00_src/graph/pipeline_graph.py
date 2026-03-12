"""
pipeline_graph.py

LangGraph 파이프라인: 도서관 포털 조회 → 도서 검색 → HTML 파싱

그래프 구조:
  resolve_catalog → search_book → parse_html → END

주요 기능:
- resolve_catalog: catalog_index.yaml에서 place로 도서관 포털 URL 조회
- search_book: LLM 기반 브라우저 자동화로 도서 검색 및 HTML 저장
- parse_html: BeautifulSoup으로 HTML 파싱하여 도서 정보 추출
- 검색 결과 캐싱: 동일한 (place, title) 조합의 결과를 24시간 동안 캐시

CLI 실행:
  PYTHONPATH=00_src python -m graph.pipeline_graph --place gangnam --title "어린 왕자"
  PYTHONPATH=00_src python -m graph.pipeline_graph --place gangnam --title "어린 왕자" --no-cache
"""

from __future__ import annotations
from typing import Dict, Any, Optional
import os
from datetime import datetime
import argparse

# LangGraph 기본 컴포넌트
from langgraph.graph import StateGraph, END

# 제작한 노드 함수
from nodes.resolve_catalog import resolve_catalog
from nodes.search_book import search_book
from nodes.parse_html import parse_html

# 캐시 유틸리티
from utils.cache import (
    get_cached_result,
    save_to_cache,
    get_cache_meta,
    clear_expired_cache,
    DEFAULT_MAX_AGE_HOURS,
)


def build_graph():
    """
    그래프: get_library_portal → search_book → parse_html → END
    """
    graph = StateGraph(dict)  # 상태는 단순히 dict로 사용

    graph.add_node("get_library_portal", resolve_catalog)
    graph.add_node("search_book", search_book)
    graph.add_node("parse_html", parse_html)

    graph.set_entry_point("get_library_portal")
    graph.add_edge("get_library_portal", "search_book")
    graph.add_edge("search_book", "parse_html")
    graph.add_edge("parse_html", END)

    return graph.compile()

app = build_graph()

# Node metadata for progress tracking
NODE_INFO = {
    "get_library_portal": {
        "file": "resolve_catalog.py",
        "function": "resolve_catalog()",
        "label": "Resolving library portal URL",
    },
    "search_book": {
        "file": "search_book.py",
        "function": "search_book()",
        "label": "Searching library portal via Playwright",
    },
    "parse_html": {
        "file": "parse_html.py",
        "function": "parse_html()",
        "label": "Parsing HTML with BeautifulSoup",
    },
}

PIPELINE_ORDER = ["get_library_portal", "search_book", "parse_html"]


def _node_detail(node_name: str, state: Dict[str, Any]) -> str:
    """Extract a short summary from a completed node's state."""
    if node_name == "get_library_portal":
        url = state.get("catalog_home_url", "")
        if url:
            try:
                return f"Portal → {url.split('//')[1].split('/')[0]}"
            except Exception:
                return f"Portal → {url}"
        return "Portal resolution failed"
    elif node_name == "search_book":
        total = state.get("total_pages", 0)
        size = state.get("html_size", 0)
        return f"Saved {total} HTML page(s) ({size:,} bytes)"
    elif node_name == "parse_html":
        books = state.get("parsed_books", [])
        return f"Extracted {len(books)} book record(s)"
    return "Done"


def run_once(
    place: str,
    title: str,
    use_cache: bool = True,
    max_cache_age_hours: int = DEFAULT_MAX_AGE_HOURS,
    progress_callback=None,
) -> Dict[str, Any]:
    """
    그래프를 한 번 실행한다.

    입력:
      - place: 'gangnam' | 'songpa' | 'seocho' 등
      - title: 책 제목(검색어)
      - use_cache: 캐시 사용 여부 (기본 True)
      - max_cache_age_hours: 캐시 최대 유효 시간 (기본 24시간)
      - progress_callback: 진행 콜백 fn(file, function, status, detail)

    출력: 최종 state(dict)
    """
    _cb = progress_callback or (lambda **kw: None)

    # 캐시 확인
    if use_cache:
        _cb(file="cache.py", function="get_cached_result()", status="start", detail="Checking result cache...")
        cached_jsonl = get_cached_result(place, title, max_cache_age_hours)
        if cached_jsonl:
            meta = get_cache_meta(place, title)
            count = meta.get("result_count", "?") if meta else "?"
            _cb(file="cache.py", function="get_cached_result()", status="done", detail=f"Cache hit — {count} books cached")
            print(f"[pipeline] ✅ 캐시 히트! {place}/{title}")
            return {
                "place": place,
                "title": title,
                "out_jsonl": cached_jsonl,
                "from_cache": True,
                "cache_meta": meta,
                "ok": True,
                "parse_success": True,
                "parsed_books": _load_jsonl(cached_jsonl),
            }
        else:
            _cb(file="cache.py", function="get_cached_result()", status="done", detail="Cache miss — starting fresh search")
            print(f"[pipeline] 캐시 미스: {place}/{title}")

    initial_state: Dict[str, Any] = {"place": place, "title": title}

    # 저장 경로 설정
    date_str = datetime.now().strftime("%Y-%m-%d")
    default_raw_dir = os.path.join("00_src", "data", "raw", date_str)
    default_parsed_dir = os.path.join("00_src", "data", "parsed", date_str)
    try:
        os.makedirs(default_raw_dir, exist_ok=True)
        os.makedirs(default_parsed_dir, exist_ok=True)
    except Exception:
        pass

    default_jsonl = os.path.join(default_parsed_dir, f"{place}_results.jsonl")
    initial_state["out_jsonl"] = default_jsonl

    # Pipeline execution — stream for real-time node tracking
    if progress_callback:
        result_state = dict(initial_state)
        first = NODE_INFO[PIPELINE_ORDER[0]]
        _cb(file=first["file"], function=first["function"], status="start", detail=first["label"])

        for stream_event in app.stream(initial_state):
            for node_name, state_update in stream_event.items():
                result_state.update(state_update)
                if node_name in NODE_INFO:
                    info = NODE_INFO[node_name]
                    _cb(file=info["file"], function=info["function"], status="done", detail=_node_detail(node_name, state_update))
                    idx = PIPELINE_ORDER.index(node_name)
                    if idx + 1 < len(PIPELINE_ORDER):
                        nxt = NODE_INFO[PIPELINE_ORDER[idx + 1]]
                        _cb(file=nxt["file"], function=nxt["function"], status="start", detail=nxt["label"])
    else:
        result_state = app.invoke(initial_state)

    # 검색 성공 시 캐시에 저장
    if result_state.get("parse_success") and result_state.get("out_jsonl"):
        jsonl_path = result_state.get("out_jsonl")
        if os.path.exists(jsonl_path):
            _cb(file="cache.py", function="save_to_cache()", status="start", detail="Saving results to cache...")
            save_to_cache(
                place=place,
                title=title,
                jsonl_path=jsonl_path,
                extra_meta={"search_time": datetime.now().isoformat(timespec="seconds")}
            )
            _cb(file="cache.py", function="save_to_cache()", status="done", detail="Cached (TTL: 24h)")

    result_state["from_cache"] = False
    return result_state


def _load_jsonl(jsonl_path: str) -> list:
    """JSONL 파일을 읽어서 리스트로 반환"""
    import json
    results = []
    try:
        with open(jsonl_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    results.append(json.loads(line))
    except (IOError, json.JSONDecodeError):
        pass
    return results


# ============================================================================
# 멀티지역 병렬 검색
# ============================================================================

ALL_REGIONS = ["gangnam", "seocho", "songpa"]
REGION_NAMES = {
    "gangnam": "강남구",
    "seocho": "서초구",
    "songpa": "송파구",
}


def run_multi_region(
    title: str,
    regions: list[str] = None,
    use_cache: bool = True,
    max_cache_age_hours: int = DEFAULT_MAX_AGE_HOURS,
    progress_callback: callable = None
) -> Dict[str, Any]:
    """
    여러 지역을 병렬로 검색한다.
    
    Args:
        title: 검색어(도서명)
        regions: 검색할 지역 리스트 (기본: 전체 지역)
        use_cache: 캐시 사용 여부
        max_cache_age_hours: 캐시 최대 유효 시간
        progress_callback: 진행 상태 콜백 함수 (region, status, message)
    
    Returns:
        통합된 검색 결과
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    if regions is None:
        regions = ALL_REGIONS
    
    results_by_region = {}
    errors = {}
    all_books = []
    
    def notify_progress(region: str, status: str, message: str):
        """진행 상태 알림"""
        if progress_callback:
            progress_callback(region, status, message)
        else:
            print(f"[multi-region] {REGION_NAMES.get(region, region)}: {message}")
    
    def search_region(region: str) -> tuple[str, Dict[str, Any]]:
        """단일 지역 검색 (병렬 실행용)"""
        notify_progress(region, "start", "검색 시작...")
        try:
            result = run_once(
                place=region,
                title=title,
                use_cache=use_cache,
                max_cache_age_hours=max_cache_age_hours
            )
            
            if result.get("from_cache"):
                notify_progress(region, "cache_hit", f"캐시에서 {len(result.get('parsed_books', []))}건 로드")
            elif result.get("parse_success"):
                notify_progress(region, "success", f"검색 완료: {len(result.get('parsed_books', []))}건")
            else:
                notify_progress(region, "error", f"검색 실패: {result.get('parse_error', 'unknown')}")
            
            return region, result
        except Exception as e:
            notify_progress(region, "error", f"오류: {str(e)}")
            return region, {"error": str(e), "parse_success": False}
    
    # 병렬 검색 실행
    print(f"[multi-region] {len(regions)}개 지역 병렬 검색 시작: {title}")
    
    with ThreadPoolExecutor(max_workers=len(regions)) as executor:
        futures = {executor.submit(search_region, region): region for region in regions}
        
        for future in as_completed(futures):
            region, result = future.result()
            results_by_region[region] = result
            
            if result.get("parse_success"):
                books = result.get("parsed_books", [])
                # 각 도서에 지역 정보 추가
                for book in books:
                    book["region"] = region
                    book["region_name"] = REGION_NAMES.get(region, region)
                all_books.extend(books)
            elif result.get("error"):
                errors[region] = result.get("error")
    
    # 결과 통합
    print(f"[multi-region] 검색 완료: 총 {len(all_books)}건 (성공: {len(results_by_region) - len(errors)}개 지역)")
    
    return {
        "title": title,
        "regions": regions,
        "results_by_region": results_by_region,
        "all_books": all_books,
        "total_count": len(all_books),
        "success_regions": [r for r in regions if results_by_region.get(r, {}).get("parse_success")],
        "failed_regions": list(errors.keys()),
        "errors": errors,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Library catalog portal lookup → book search → HTML parse")
    parser.add_argument("--place", type=str, help="예: gangnam | songpa | seocho | all (전체)")
    parser.add_argument("--title", type=str, help="검색어(도서명)")
    parser.add_argument("--no-cache", action="store_true", help="캐시 사용 안 함")
    parser.add_argument("--clear-cache", action="store_true", help="만료된 캐시 삭제 후 종료")
    args = parser.parse_args()

    # 캐시 정리 모드
    if args.clear_cache:
        deleted = clear_expired_cache()
        print(f"만료된 캐시 {deleted}개 삭제 완료")
        exit(0)
    
    # 필수 인자 확인
    if not args.place or not args.title:
        parser.error("--place와 --title은 필수입니다.")

    # 멀티지역 검색 (place=all인 경우)
    if args.place.lower() == "all":
        result = run_multi_region(args.title, use_cache=not args.no_cache)
        print(f"\n{'='*50}")
        print(f"📚 멀티지역 검색 결과: {args.title}")
        print(f"{'='*50}")
        print(f"✓ 검색 지역: {', '.join([REGION_NAMES.get(r, r) for r in result['success_regions']])}")
        print(f"✓ 총 발견 도서: {result['total_count']}건")
        
        # 지역별 요약
        for region in result['regions']:
            region_result = result['results_by_region'].get(region, {})
            count = len(region_result.get('parsed_books', []))
            status = "✓" if region_result.get('parse_success') else "✗"
            from_cache = " (캐시)" if region_result.get('from_cache') else ""
            print(f"  {status} {REGION_NAMES.get(region, region)}: {count}건{from_cache}")
        
        exit(0)
    
    # 단일 지역 검색
    result = run_once(args.place, args.title, use_cache=not args.no_cache)
    
    # 1. 도서관 포털 조회 결과
    if result.get("found"):
        print(f"✓ 도서관 포털 URL: {result.get('catalog_home_url')}")
    else:
        print(f"✗ 도서관 포털을 찾을 수 없습니다: {result.get('reason', 'unknown')}")
    
    # 2. 검색 결과
    if result.get("ok"):
        print(f"✓ 검색 성공")
        saved_html_paths = result.get("saved_html_paths", [result.get("saved_html_path")])
        saved_html_paths = [p for p in saved_html_paths if p]
        if saved_html_paths:
            print(f"✓ 저장된 HTML: {len(saved_html_paths)}개")
            for idx, path in enumerate(saved_html_paths, 1):
                print(f"  [{idx}] {path}")
    elif result.get("search_error"):
        print(f"✗ 검색 실패: {result.get('search_error')}")
    
    # 3. 파싱 결과
    if result.get("parse_success"):
        print(f"✓ HTML 파싱 성공")
        parsed_books = result.get("parsed_books", [])
        if parsed_books:
            print(f"✓ 발견된 도서: {len(parsed_books)}건")
    elif result.get("parse_error"):
        print(f"✗ HTML 파싱 실패: {result.get('parse_error')}")