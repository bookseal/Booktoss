"""
search_book.py

LangGraph 노드: Playwright를 사용해 도서관 포털에서 도서를 검색하고 HTML을 저장한다. (browser-use 제거 버전)
"""

from __future__ import annotations
import os
import asyncio
from typing import Any, Dict, List, Optional
import urllib.parse as _urlparse
from datetime import datetime
from pathlib import Path

# .env 자동 로드
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

from playwright.async_api import async_playwright

SELECTORS_PATH = "00_src/configs/selectors.yaml"

# Quick SPA readiness keywords for Korean library sites
SPA_READY_KEYWORDS = ["검색결과", "소장", "대출", "상세보기"]

def search_book(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    LangGraph 노드: 도서관 포털에서 도서를 검색하고 결과 HTML을 저장한다.
    
    Args:
        state: LangGraph 상태 (catalog_home_url, title, place 필요)
    
    Returns:
        업데이트된 상태 (ok, page_url, saved_html_path, html_size 포함)
    """
    home = str(state.get("catalog_home_url", "")).strip()
    title = str(state.get("title", "")).strip()
    place = str(state.get("place", "")).strip()
    if not place:
        place = state["place"] = "unknown"
    if not home or not title:
        return {**state, "ok": False, "result_hint": "invalid_input", "page_url": None}

    # 텔레메트리 관련 설정 제거 (browser-use가 아니므로 불필요)
    
    headless_env = os.environ.get("HEADLESS", "true").lower()
    use_headless = headless_env not in ("false", "0", "no")

    async def run_and_extract():
        history = []
        page_url = None
        saved_html_paths = []
        html_size = 0
        total_pages = 0

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=use_headless)
            context = await browser.new_context(viewport={'width': 1280, 'height': 900})
            page = await context.new_page()

            try:
                print(f"[search_book_playwright] {home} 로 이동 중...")
                await page.goto(home, wait_until='networkidle', timeout=60000)
                history.append(f"Navigated to {home}")
                
                # 매우 포괄적인 검색 입력창 CSS selector
                search_input_selector = (
                    "input[type='text'][placeholder*='검색'], "
                    "input[type='text'][title*='검색'], "
                    "input[type='search'], "
                    "input[title*='검색'], "
                    "input[id*='search'], "
                    "input[id*='Keyword'], "
                    "input[name*='search'], "
                    "input[name*='keyword']"
                )
                
                # 검색 인풋이 보일 때까지 대기
                try:
                    # 첫번째로 일치하는 visible 한 요소
                    search_input = page.locator(search_input_selector).locator('visible=true').first
                    await search_input.wait_for(state='visible', timeout=10000)
                    await search_input.fill(title)
                    history.append(f"Filled '{title}' in search input")
                    print(f"[search_book_playwright] 텍스트 입력 완료: {title}")

                    # 엔터 키 누르기 제출
                    await search_input.press('Enter')
                    history.append("Pressed Enter")
                    
                except Exception as e:
                    print(f"[search_book_playwright] ⚠️ 검색창 찾기 또는 입력 실패: {e}")
                    history.append(f"Failed to submit search: {e}")
                    
                    # 1회 추가 재시도: 그냥 페이지의 모든 input[type='text'] 중 가장 큰 것? 너무 복잡하므로 스킵.

                # SPA 로딩 대기: 타임아웃 10초
                ready = False
                for _ in range(20):
                    try:
                        body_text = await page.evaluate("() => document.body ? document.body.innerText : ''")
                        if any(k in body_text for k in SPA_READY_KEYWORDS):
                            ready = True
                            break
                    except Exception:
                        pass
                    await asyncio.sleep(0.5)

                print(f"[search_book_playwright] 검색 결과 SPA 로딩 대기 완료 ({'성공' if ready else '타임아웃'})")
                
                if ready:
                    await asyncio.sleep(5)
                
                page_url = page.url
                print(f"[search_book_playwright] 현재 URL: {page_url}")

                # 1페이지 추출
                html_content = await page.evaluate("() => document.documentElement.outerHTML")
                
                today = datetime.now().strftime("%Y-%m-%d")
                base_timestamp = int(datetime.now().timestamp())
                dir_path = Path(f"00_src/data/raw/{today}")
                dir_path.mkdir(parents=True, exist_ok=True)
                
                if html_content:
                    filename = f"{place}_{base_timestamp}_results.html"
                    saved_path = dir_path / filename
                    saved_path.write_text(html_content, encoding="utf-8")
                    
                    # Meta 저장
                    meta = {
                        "place": place,
                        "page_url": page_url,
                        "captured_at": datetime.now().isoformat(timespec="seconds")
                    }
                    import json
                    (saved_path.with_suffix('.html.meta.json')).write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")
                    
                    html_size = len(html_content)
                    saved_html_paths.append(str(saved_path))
                    print(f"[search_book_playwright] ✅ 1페이지 HTML 저장 완료: {saved_path} ({html_size:,} bytes)")
                
                # ====== 다중 페이지 (JavaScript 직접 실행) ======
                current_page = 1
                max_pages = 10
                
                while current_page < max_pages:
                    try:
                        next_page_num = current_page + 1
                        print(f"[search_book_playwright] 🔍 {next_page_num}페이지 버튼 찾는 중...")
                        
                        js_code = f"""() => {{
    let link = document.querySelector('a[href*="fnList({next_page_num})"]');
    if (link) {{ link.click(); return 'clicked_fnList'; }}
    
    let pgNumButtons = document.querySelectorAll('button.pgNum');
    for (let btn of pgNumButtons) {{
        if (btn.textContent.trim() === '{next_page_num}') {{ btn.click(); return 'clicked_pgNum'; }}
    }}
    
    let allButtons = document.querySelectorAll('button');
    for (let btn of allButtons) {{
        if (btn.textContent.trim() === '{next_page_num}') {{ btn.click(); return 'clicked_button'; }}
    }}
    
    let allLinks = document.querySelectorAll('a');
    for (let a of allLinks) {{
        if (a.textContent.trim() === '{next_page_num}' && a.href.includes('javascript')) {{ a.click(); return 'clicked_link'; }}
    }}
    return 'not_found';
}}"""
                        click_result = await page.evaluate(js_code)
                        clicked = click_result != "not_found"
                        
                        print(f"[search_book_playwright] {'✅' if clicked else '📍'} {next_page_num}페이지 클릭 결과: {click_result}")
                        
                        if not clicked:
                            print(f"[search_book_playwright] 📍 마지막 페이지 도달 (현재: {current_page}페이지)")
                            break
                        
                        current_page = next_page_num
                        
                        print(f"[search_book_playwright] {current_page}페이지 로딩 대기 중... (7초)")
                        await asyncio.sleep(7)
                        
                        page_html_content = await page.evaluate("() => document.documentElement.outerHTML")
                        
                        if page_html_content and len(page_html_content) > 1000:
                            page_filename = f"{place}_{base_timestamp}_results_page{current_page}.html"
                            page_path = dir_path / page_filename
                            page_path.write_text(page_html_content, encoding="utf-8")
                            print(f"[search_book_playwright] ✅ {current_page}페이지 HTML 저장 완료: {page_path} ({len(page_html_content):,} bytes)")
                            saved_html_paths.append(str(page_path))
                        else:
                            print(f"[search_book_playwright] ⚠️ {current_page}페이지 HTML 추출 실패")
                            break
                            
                    except Exception as e:
                        print(f"[search_book_playwright] ⚠️ {current_page}페이지 처리 실패: {e}")
                        break
                        
            except Exception as e:
                print(f"[search_book_playwright] ❌ 브라우저 작업 실패: {e}")
                history.append(f"Fatal Error: {str(e)}")
            finally:
                await context.close()
                await browser.close()
                
            return history, page_url, saved_html_paths, html_size

    # asyncio
    try:
        history, page_url, saved_html_paths, html_size = asyncio.run(run_and_extract())
        total_pages = len(saved_html_paths)
        print(f"[search_book_playwright] 📊 총 {total_pages}개 페이지 HTML 저장 완료")
        return {
            **state,
            "ok": True,
            "result_hint": "results_detected",
            "page_url": page_url,
            "saved_html_path": saved_html_paths[0] if saved_html_paths else None,
            "saved_html_paths": saved_html_paths,
            "total_pages": total_pages,
            "html_size": html_size,
            "used_frame": None,
            "markers": [],
            "log": history,
            "place": place
        }
    except Exception as final_e:
        return {
            **state,
            "ok": False,
            "result_hint": "execution_error",
            "page_url": None,
            "saved_html_path": None,
            "html_size": 0,
            "used_frame": None,
            "markers": [],
            "log": [str(final_e)],
            "place": place
        }
