"""
search_book.py

LangGraph 노드: LLM 기반 브라우저 자동화로 도서관 포털에서 도서를 검색하고 HTML을 저장한다.
"""

from __future__ import annotations
import os
from typing import Any, Dict, List, Optional
import urllib.parse as _urlparse  # 도메인 추출용
from datetime import datetime
from pathlib import Path

# Agent 모드용 라이브러리 (로컬 브라우저 직접 제어)
try:
    from browser_use import Agent, ChatOpenAI, Browser  # type: ignore
except Exception:
    Agent = None  # type: ignore
    ChatOpenAI = None  # type: ignore
    Browser = None  # type: ignore

# .env 자동 로드(있으면)
try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:
    pass

try:
    from browser_use_sdk import BrowserUseClient  # type: ignore
except Exception:
    BrowserUseClient = None  # 런타임에 미설치면 '실행 계획'만 반환하여 디버깅 가능

SELECTORS_PATH = "00_src/configs/selectors.yaml"

# Quick SPA readiness keywords for Korean library sites
SPA_READY_KEYWORDS = ["검색결과", "소장", "대출", "상세보기"]

def _build_browser_use_task(catalog_home_url: str, title: str) -> str:
    """
    브라우저 자동화 태스크 프롬프트를 생성한다.
    
    Args:
        catalog_home_url: 도서관 포털 홈 URL
        title: 검색할 도서 제목
    
    Returns:
        LLM 에이전트가 실행할 태스크 지시문
    """
    return f"""
1) navigate to "{catalog_home_url}"
2) if a VISIBLE search input exists (placeholder/aria-label/label text includes: 검색|도서|자료), DO NOT WAIT: focus it immediately.
   else wait up to 10s for SPA to load; if still hidden, STOP with no_results. DO NOT REFRESH.
3) type "{title}" and press Enter. if not submitted, click the search/돋보기 button ONCE (no repeats).
4) if URL changed OR the page contains any of [검색결과, 소장, 대출, 건], STOP immediately with success (done).
5) NEVER repeat the same action twice. at most 2 attempts TOTAL. do not open new tabs. do not save HTML.
"""

def search_book(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    LangGraph 노드: 도서관 포털에서 도서를 검색하고 결과 HTML을 저장한다.
    
    Args:
        state: LangGraph 상태 (catalog_home_url, title, place 필요)
    
    Returns:
        업데이트된 상태 (ok, page_url, saved_html_path, html_size 포함)
    """
    # 핵심 입력
    home = str(state.get("catalog_home_url", "")).strip()
    title = str(state.get("title", "")).strip()
    place = str(state.get("place", "")).strip()
    if not place:
        # fallback: try to infer later from saved filename; still keep non-empty token for downstream
        place = state["place"] = "unknown"
    if not home or not title:
        return {**state, "ok": False, "result_hint": "invalid_input", "page_url": None}

    # 텔레메트리 비활성(불필요 백오프 방지) - 모든 변수 강제 설정
    os.environ["POSTHOG_DISABLED"] = "1"
    os.environ["ANONYMIZED_TELEMETRY"] = "false"
    os.environ["TELEMETRY_DISABLED"] = "1"
    os.environ["DO_NOT_TRACK"] = "1"

    # 브라우저 제한: 홈 URL에서 도메인 추출
    def _derive_allowed_from_home(url: str) -> List[str]:
        try:
            netloc = _urlparse.urlparse(url).netloc
            if netloc and "." in netloc:
                base = netloc.split(":")[0]
                parts = base.split(".")
                if len(parts) >= 2:
                    return [base, f"*.{'.'.join(parts[-2:])}"]
                return [base]
        except Exception:
            pass
        return ["*.go.kr", "*.or.kr"]  # fallback
    
    allowed = state.get("allowed_domains") or _derive_allowed_from_home(home)

    # 브라우저 생성 (HEADLESS 환경변수로 headless 모드 제어, 기본값: True for Linux)
    browser = None
    if Browser is not None:
        # 환경변수 HEADLESS가 "false" 또는 "0"이면 headless=False, 그 외에는 True
        headless_env = os.environ.get("HEADLESS", "true").lower()
        use_headless = headless_env not in ("false", "0", "no")
        
        try:
            browser = Browser(
                headless=use_headless,
                allowed_domains=allowed,
                window_size={"width": 1280, "height": 900},
                keep_alive=True,
                minimum_wait_page_load_time=0.5, # 페이지 로딩 대기 시간
                wait_for_network_idle_page_load_time=0.8, # 네트워크 아이들 대기 시간
                wait_between_actions=0.2, # 액션 간 대기 시간
                highlight_elements=False,
            )
            print(f"[search_book] Browser 생성 완료 (headless={use_headless})")
        except Exception as e:
            print(f"[search_book] ❌ Browser 생성 실패: {e}")
            browser = None

    # LLM (소형 모델)
    if Agent is None or ChatOpenAI is None:
        # 라이브러리 미설치 시 계획만 반환
        task_preview = _build_browser_use_task(home, title)  # , {}, [30, 60, 90] - 제거됨
        return {**state, "ok": False, "result_hint": "plan_only", "page_url": None, "log": ["browser_use Agent 미설치"], "task_prompt": task_preview}
    llm = ChatOpenAI(model=state.get("llm_model", "gpt-5-mini"))

    # 1단계: 규칙 기반(아주 짧은 태스크, max_steps=8)
    task_rules = _build_browser_use_task(home, title)  # , {}, [30, 60, 90] - 제거됨
    agent_rules = Agent(task=task_rules, llm=llm, browser=browser) if browser else Agent(task=task_rules, llm=llm)

    import asyncio
    try:
        # asyncio 내에서 CDP/URL/HTML 추출하는 함수
        async def run_and_extract():
            history = await agent_rules.run(max_steps=int(state.get("max_steps_rules", 8)))
            
            # SPA 로딩 완료 대기: 네트워크 아이들 + 본문 키워드 등장 대기(최대 10s)
            try:
                await browser.wait_for_network_idle(timeout=10000)
            except Exception:
                await asyncio.sleep(1.5)

            # 추가: 본문에 라이브러리 결과 키워드가 나타날 때까지 폴링(최대 10s)
            ready = False
            for _ in range(20):  # 20 * 0.5s = 10s
                try:
                    page = await browser.get_current_page()
                    body_text = await page.evaluate("() => document.body ? document.body.innerText : ''")
                    if any(k in body_text for k in SPA_READY_KEYWORDS):
                        ready = True
                        break
                except Exception:
                    pass
                await asyncio.sleep(0.5)

            print(f"[search_book] SPA 로딩 대기 완료 ({'성공' if ready else '타임아웃'})")
            
            # 추가 대기: 검색 결과 데이터가 완전히 로드될 시간 확보 (5초)
            if ready:
                print(f"[search_book] 검색 결과 데이터 로딩 대기 중... (5초)")
                await asyncio.sleep(5)
            
            # page_url 추출
            page_url = None
            
            if browser:
                try:
                    page_url = await browser.get_current_page_url()
                    print(f"[search_book] URL: {page_url}")
                except Exception as e:
                    print(f"[search_book] URL 추출 실패: {e}")
            
            # HTML 추출 및 저장 (browser-use page.evaluate 사용)
            saved_path = None
            html_size = 0
            
            if browser:
                try:
                    print(f"[search_book] HTML 추출 시작...")
                    page = await browser.get_current_page()
                    html_content = await page.evaluate("() => document.documentElement.outerHTML")
                    
                    if html_content:
                        # 저장 경로 생성
                        today = datetime.now().strftime("%Y-%m-%d")
                        timestamp = int(datetime.now().timestamp())
                        dir_path = f"00_src/data/raw/{today}"
                        os.makedirs(dir_path, exist_ok=True)
                        
                        filename = f"{place}_{timestamp}_results.html"
                        saved_path = os.path.join(dir_path, filename)
                        
                        # 파일 저장
                        with open(saved_path, "w", encoding="utf-8") as f:
                            f.write(html_content)
                        
                        # 메타데이터 사이드카 저장(.meta.json)
                        try:
                            meta = {
                                "place": place,
                                "page_url": page_url,
                                "captured_at": datetime.now().isoformat(timespec="seconds")
                            }
                            with open(saved_path + ".meta.json", "w", encoding="utf-8") as mf:
                                import json as _json
                                mf.write(_json.dumps(meta, ensure_ascii=False))
                        except Exception as _e:
                            print(f"[search_book] 메타 저장 경고: {_e}")
                        
                        html_size = len(html_content)
                        print(f"[search_book] ✅ HTML 저장 완료 (페이지 1): {saved_path} ({html_size:,} bytes)")
                    else:
                        print(f"[search_book] ⚠️ HTML 내용이 비어있음")
                        
                except Exception as e:
                    print(f"[search_book] ❌ HTML 추출/저장 실패: {e}")
                    import traceback
                    traceback.print_exc()
            
            # ========== 다중 페이지 처리: JavaScript 직접 실행으로 마지막 페이지까지 ==========
            saved_html_paths = [saved_path]  # 1페이지 경로 저장
            
            # 공통 변수 준비
            today = datetime.now().strftime("%Y-%m-%d")
            base_timestamp = int(datetime.now().timestamp())
            dir_path = Path(f"00_src/data/raw/{today}")
            
            if browser:
                current_page = 1
                max_pages = 10  # 안전장치 (무한 루프 방지) 최대 10페이지까지만 저장함.
                
                while current_page < max_pages:
                    try:
                        next_page_num = current_page + 1
                        print(f"[search_book] 🔍 {next_page_num}페이지 버튼 찾는 중...")
                        
                        # JavaScript로 다음 페이지 버튼 클릭 (다중 패턴 지원, 화살표 함수 형식)
                        js_code = f"""() => {{
    // 패턴 1: 송파구 스타일 - javascript:fnList(N)
    let link = document.querySelector('a[href*="fnList({next_page_num})"]');
    if (link) {{
        link.click();
        return 'clicked_fnList';
    }}
    
    // 패턴 2: 강남구 스타일 - button.pgNum
    let pgNumButtons = document.querySelectorAll('button.pgNum');
    for (let btn of pgNumButtons) {{
        if (btn.textContent.trim() === '{next_page_num}') {{
            btn.click();
            return 'clicked_pgNum';
        }}
    }}
    
    // 패턴 3: 서초구 스타일 - button with @click
    let allButtons = document.querySelectorAll('button');
    for (let btn of allButtons) {{
        if (btn.textContent.trim() === '{next_page_num}') {{
            btn.click();
            return 'clicked_button';
        }}
    }}
    
    // 패턴 4: 일반 링크 (텍스트가 N인 모든 <a> 태그)
    let allLinks = document.querySelectorAll('a');
    for (let a of allLinks) {{
        if (a.textContent.trim() === '{next_page_num}' && a.href.includes('javascript')) {{
            a.click();
            return 'clicked_link';
        }}
    }}
    
    return 'not_found';
}}"""
                        
                        # JavaScript 실행 (playwright page.evaluate 사용)
                        page = await browser.get_current_page()
                        click_result = await page.evaluate(js_code)
                        clicked = click_result != "not_found"
                        
                        print(f"[search_book] {'✅' if clicked else '📍'} {next_page_num}페이지 클릭 결과: {click_result}")
                        
                        if not clicked:
                            # 다음 버튼 없음 → 마지막 페이지 도달
                            print(f"[search_book] 📍 마지막 페이지 도달 (현재: {current_page}페이지)")
                            break
                        
                        current_page = next_page_num
                        
                        # 페이지 로딩 대기 (SPA 사이트를 위해 충분한 시간 확보)
                        print(f"[search_book] {current_page}페이지 로딩 대기 중... (7초)")
                        await asyncio.sleep(7)
                        
                        # HTML 추출 (browser-use page.evaluate 사용)
                        print(f"[search_book] {current_page}페이지 HTML 추출 중...")
                        page = await browser.get_current_page()
                        page_html_content = await page.evaluate("() => document.documentElement.outerHTML")
                        
                        if page_html_content and len(page_html_content) > 1000:
                            # 파일명 생성
                            page_filename = f"{place}_{base_timestamp}_results_page{current_page}.html"
                            page_path = dir_path / page_filename
                            
                            # HTML 저장
                            page_path.write_text(page_html_content, encoding="utf-8")
                            page_size = len(page_html_content)
                            print(f"[search_book] ✅ {current_page}페이지 HTML 저장 완료: {page_path} ({page_size:,} bytes)")
                            
                            saved_html_paths.append(str(page_path))
                        else:
                            print(f"[search_book] ⚠️ {current_page}페이지 HTML 추출 실패 또는 내용 부족")
                            break  # HTML 추출 실패하면 중단
                        
                    except Exception as e:
                        print(f"[search_book] ⚠️ {current_page}페이지 처리 실패: {e}")
                        import traceback
                        traceback.print_exc()
                        break  # 에러 발생 시 중단
            
            # 브라우저 종료 (async 컨텍스트 내부에서)
            if browser:
                try:
                    print(f"[search_book] 브라우저 종료 중...")
                    await browser.stop()  # BrowserSession은 close() 대신 stop() 사용
                    print(f"[search_book] ✅ 브라우저 종료 완료")
                except Exception as e:
                    print(f"[search_book] ⚠️ 브라우저 종료 경고: {e}")
            
            return history, page_url, saved_html_paths, html_size
        
        # asyncio 실행
        history1, page_url, saved_html_paths, html_size = asyncio.run(run_and_extract())
        
        total_pages = len(saved_html_paths)
        print(f"[search_book] 📊 총 {total_pages}개 페이지 HTML 저장 완료")
        
        return {
            **state, 
            "ok": True, 
            "result_hint": "results_detected", 
            "page_url": page_url, 
            "saved_html_path": saved_html_paths[0] if saved_html_paths else None,  # 1페이지 경로 (하위 호환)
            "saved_html_paths": saved_html_paths,  # 전체 페이지 경로 리스트
            "total_pages": total_pages,
            "html_size": html_size, 
            "used_frame": None, 
            "markers": [], 
            "log": [f"rules_steps={len(history1) if isinstance(history1, list) else 'unknown'}"], 
            "place": place
        }
    except Exception as e1:
        # 2단계: 유연 태스크(한 번만), max_steps=15
        task_llm = f"수정된 시도: 위와 동일하지만 다른 경로도 허용. 실패 시 즉시 종료.\n" + _build_browser_use_task(home, title)  # , {}, [30, 60, 90] - 제거됨
        agent_llm = Agent(task=task_llm, llm=llm, browser=browser) if browser else Agent(task=task_llm, llm=llm)
        try:
            # asyncio 내에서 CDP/URL/HTML 추출하는 함수 (LLM 경로)
            async def run_and_extract_llm():
                history = await agent_llm.run(max_steps=int(state.get("max_steps_llm", 15)))
                
                # SPA 로딩 완료 대기: 네트워크 아이들 + 본문 키워드 등장 대기(최대 10s)
                try:
                    await browser.wait_for_network_idle(timeout=10000)
                except Exception:
                    await asyncio.sleep(1.5)

                # 추가: 본문에 라이브러리 결과 키워드가 나타날 때까지 폴링(최대 10s)
                ready = False
                for _ in range(20):  # 20 * 0.5s = 10s
                    try:
                        page = await browser.get_current_page()
                        body_text = await page.evaluate("() => document.body ? document.body.innerText : ''")
                        if any(k in body_text for k in SPA_READY_KEYWORDS):
                            ready = True
                            break
                    except Exception:
                        pass
                    await asyncio.sleep(0.5) # 루프를 돌면서 0.5초마다 한번씩 DOM이 완성 되기를 기다린다.

                print(f"[search_book LLM] SPA 로딩 대기 완료 ({'성공' if ready else '타임아웃'})")
                
                # 추가 대기: 검색 결과 데이터가 완전히 로드될 시간 확보 (5초)
                if ready:
                    print(f"[search_book LLM] 검색 결과 데이터 로딩 대기 중... (5초)")
                    await asyncio.sleep(5)
                
                # page_url 추출
                page_url = None
                
                if browser:
                    try:
                        page_url = await browser.get_current_page_url()
                        print(f"[search_book LLM] URL: {page_url}")
                    except Exception as e:
                        print(f"[search_book LLM] URL 추출 실패: {e}")
                
                # HTML 추출 및 저장 (browser-use page.evaluate 사용)
                saved_path = None
                html_size = 0
                
                if browser:
                    try:
                        print(f"[search_book LLM] HTML 추출 시작...")
                        page = await browser.get_current_page()
                        html_content = await page.evaluate("() => document.documentElement.outerHTML")
                        
                        if html_content:
                            today = datetime.now().strftime("%Y-%m-%d")
                            timestamp = int(datetime.now().timestamp())
                            dir_path = f"00_src/data/raw/{today}"
                            os.makedirs(dir_path, exist_ok=True)
                            
                            filename = f"{place}_{timestamp}_results.html"
                            saved_path = os.path.join(dir_path, filename)
                            
                            with open(saved_path, "w", encoding="utf-8") as f:
                                f.write(html_content)
                            
                            # 메타데이터 사이드카 저장(.meta.json)
                            try:
                                meta = {
                                    "place": place,
                                    "page_url": page_url,
                                    "captured_at": datetime.now().isoformat(timespec="seconds")
                                }
                                with open(saved_path + ".meta.json", "w", encoding="utf-8") as mf:
                                    import json as _json
                                    mf.write(_json.dumps(meta, ensure_ascii=False))
                            except Exception as _e:
                                print(f"[search_book LLM] 메타 저장 경고: {_e}")
                            
                            html_size = len(html_content)
                            print(f"[search_book LLM] ✅ HTML 저장 완료: {saved_path} ({html_size:,} bytes)")
                        else:
                            print(f"[search_book LLM] ⚠️ HTML 내용이 비어있음")
                            
                    except Exception as e:
                        print(f"[search_book LLM] ❌ HTML 추출/저장 실패: {e}")
                        import traceback
                        traceback.print_exc()
                
                # 브라우저 종료 (async 컨텍스트 내부에서)
                if browser:
                    try:
                        print(f"[search_book] 브라우저 종료 중...")
                        await browser.stop()  # BrowserSession은 close() 대신 stop() 사용
                        print(f"[search_book] ✅ 브라우저 종료 완료")
                    except Exception as e:
                        print(f"[search_book] ⚠️ 브라우저 종료 경고: {e}")
                
                return history, page_url, saved_path, html_size
            
            history2, page_url, saved_html_path, html_size = asyncio.run(run_and_extract_llm())
            
            return {**state, "ok": True, "result_hint": "results_detected", "page_url": page_url, "saved_html_path": saved_html_path, "html_size": html_size, "used_frame": None, "markers": [], "log": [f"llm_steps={len(history2) if isinstance(history2, list) else 'unknown'}", str(e1)], "place": place}
        except Exception as e2:
            return {**state, "ok": False, "result_hint": "execution_error", "page_url": None, "saved_html_path": None, "html_size": 0, "used_frame": None, "markers": [], "log": ["rules_failed", str(e1), "llm_failed", str(e2)]}
