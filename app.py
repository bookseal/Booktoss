"""
app.py

BookToss: 서울 도서관 통합 검색 Streamlit 애플리케이션

사용자 위치 기반으로 강남/서초/송파 지역 도서관에서 원하는 도서를 검색하고,
대출 가능 여부와 도서관 위치 정보를 제공하는 웹 애플리케이션입니다.
"""

import streamlit as st
import os
import sys
import json
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import requests
from dotenv import load_dotenv
from math import radians, sin, cos, sqrt, atan2
import urllib

# ============================================================================
# 설정 및 상수
# ============================================================================

load_dotenv()

KAKAO_REST_KEY = os.getenv("KAKAO_REST_KEY")
KAKAO_API_KEY = os.getenv("KAKAO_API_KEY")
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
HEADERS = {"Authorization": f"KakaoAK {KAKAO_REST_KEY}"}
ALLOWED_REGION_TO_PLACE = {
            "강남구": "gangnam",
            "서초구": "seocho",
            "송파구": "songpa"
        }

LIBRARY_ADDRESS_MAP = {
    "도곡정보문화도서관": "서울특별시 강남구 도곡로18길 57",
    "개포하늘꿈도서관": "서울특별시 강남구 개포로110길 54",
    "논현도서관": "서울특별시 강남구 학동로43길 17",
    "논현문화마루도서관": "서울특별시 강남구 논현로131길 40",
    "논현문화마루도서관 (별관)": "서울특별시 강남구 학동로 169",
    "대치1동작은도서관": "서울특별시 강남구 남부순환로391길 19",
    "대치도서관": "서울특별시 강남구 삼성로 212",
    "못골도서관": "서울특별시 강남구 자곡로 116",
    "못골한옥어린이도서관": "서울특별시 강남구 자곡로7길 3",
    "삼성도서관": "서울특별시 강남구 봉은사로 616",
    "세곡도서관": "서울특별시 강남구 밤고개로 286",
    "세곡마루도서관": "서울특별시 강남구 헌릉로590길 68",
    "역삼2동작은도서관": "서울특별시 강남구 언주로 314",
    "역삼도서관": "서울특별시 강남구 역삼로7길 16",
    "역삼푸른솔도서관": "서울특별시 강남구 테헤란로8길 36",
    "열린도서관": "서울특별시 강남구 일원로 115",
    "일원라온영어구립도서관": "서울특별시 강남구 영동대로 22",
    "정다운도서관": "서울특별시 강남구 학동로67길 11",
    "즐거운도서관": "서울특별시 강남구 도곡로77길 23",
    "청담도서관": "서울특별시 강남구 압구정로79길 26",
    "행복한도서관": "서울특별시 강남구 영동대로65길 24",
    "개포4동주민도서관": "서울특별시 강남구 개포로38길 12",
    "도곡2동주민도서관": "서울특별시 강남구 남부순환로378길 34-9",
    "신사동주민도서관": "서울특별시 강남구 압구정로 128",
    "압구정동주민도서관": "서울특별시 강남구 압구정로 151",
    "일원본동주민도서관": "서울특별시 강남구 광평로 126",
    "개포1동주민도서관": "서울특별시 강남구 선릉로 35",

    "서초구립반포도서관": "서울특별시 서초구 고무래로 34",
    "서초구립내곡도서관": "서울특별시 서초구 청계산로7길 9-20",
    "서초구립양재도서관": "서울특별시 서초구 양재천로 33",
    "서초청소년도서관": "서울특별시 서초구 효령로77길 37",
    "방배숲환경도서관": "서울특별시 서초구 서초대로 160-7",
    "서이도서관": "서초구 서초대로70길 51",
    "잠원도서관": "서울특별시 서초구 나루터로 38",
    "방배도서관": "서울특별시 서초구 방배로 40",
    "서초그림책도서관": "서울특별시 서초구 명달로 150",
    "서초1동 작은도서관": "서울특별시 서초구 사임당로 89",
    "서초3동 작은도서관": "서울특별시 서초구 반포대로 58",
    "서초4동 작은도서관": "서울특별시 서초구 서운로26길 3",
    "반포1동 작은도서관": "서울특별시 서초구 사평대로 273",
    "반포2동 작은도서관": "서울특별시 서초구 신반포로 127",
    "반포3동 작은도서관": "서울특별시 서초구 신반포로23길 78",
    "반포4동 작은도서관": "서울특별시 서초구 사평대로28길 70",
    "방배본동 작은도서관": "서울특별시 서초구 동광로19길 38",
    "방배1동 작은도서관": "서울특별시 서초구 효령로29길 43",
    "방배2동 작은도서관": "서울특별시 서초구 청두곶길 36",
    "방배4동 작은도서관": "서울특별시 서초구 방배로 173",
    "양재1동 작은도서관": "서울특별시 서초구 바우뫼로 41",
    "양재2동 작은도서관": "서울특별시 서초구 강남대로12길 44",
    "서초구 전자도서관": "서울특별시 서초구 고무래로 34",

    "송파글마루도서관": "서울특별시 송파구 충민로 120",
    "송파어린이도서관": "서울특별시 송파구 올림픽로 105",
    "송파위례도서관": "서울특별시 송파구 위례광장로 210",
    "거마도서관": "서울특별시 송파구 거마로2길 19",
    "돌마리도서관": "서울특별시 송파구 백제고분로37길 16",
    "소나무언덕1호도서관": "서울특별시 송파구 올림픽로47길 9",
    "소나무언덕2호도서관": "서울특별시 송파구 석촌호수로 155",
    "소나무언덕3호도서관": "서울특별시 송파구 성내천로 319",
    "소나무언덕4호도서관": "서울특별시 송파구 송이로 34",
    "소나무언덕잠실본동도서관": "서울특별시 송파구 탄천동로 205",
    "송파어린이영어도서관": "서울특별시 송파구 오금로 1",
    "가락몰도서관": "서울특별시 송파구 양재대로 932",
    "풍납1동바람드리작은도서관": "서울특별시 송파구 풍성로5길 16",
    "거여1동다독다독작은도서관": "서울특별시 송파구 오금로53길 32",
    "거여2동향나무골작은도서관": "서울특별시 송파구 거마로2길 19",
    "마천1동새마을작은도서관": "서울특별시 송파구 마천로 303",
    "마천2동글수레작은도서관": "서울특별시 송파구 마천로 287",
    "방이1동조롱박작은도서관": "서울특별시 송파구 위례성대로16길 22",
    "방이2동새마을작은도서관": "서울특별시 송파구 올림픽로34길 5-13",
    "오륜동오륜작은도서관": "서울특별시 송파구 양재대로 1232",
    "오금동오동나무작은도서관": "서울특별시 송파구 중대로25길 5",
    "송파1동새마을작은도서관": "서울특별시 송파구 백제고분로 392",
    "송파2동송이골작은도서관": "서울특별시 송파구 송이로 32",
    "석촌동꿈다락작은도서관": "서울특별시 송파구 백제고분로37길 16",
    "삼전동삼학사작은도서관": "서울특별시 송파구 백제고분로 236",
    "가락본동글향기작은도서관": "서울특별시 송파구 송파대로28길 39",
    "가락2동로즈마리작은도서관": "서울특별시 송파구 중대로20길 6",
    "문정1동느티나무작은도서관": "서울특별시 송파구 동남로 116",
    "문정2동숯내작은도서관": "서울특별시 송파구 중대로 16",
    "장지동새마을작은도서관": "서울특별시 송파구 새말로19길 6",
    "잠실본동새내꿈작은도서관": "서울특별시 송파구 백제고분로 145",
    "잠실3동파랑새작은도서관": "서울특별시 송파구 잠실로 51-31",
    "잠실4동새마을작은도서관": "서울특별시 송파구 올림픽로35길 16",
    "잠실6동장미마을작은도서관": "서울특별시 송파구 올림픽로35길 120",
    "잠실7동부렴마을작은도서관": "서울특별시 송파구 올림픽로 44"
}

TIMEOUT = 5   # API 요청 타임아웃 (초)
TOP_N_MAP = 1  # 지도에 표시할 도서관 개수

# ============================================================================
# 페이지 설정
# ============================================================================

st.set_page_config(
    page_title="Book Toss - 도서관 검색",
    page_icon="📚",
)

# 커스텀 CSS
st.markdown("""
    <style>
        .main-header {
            text-align: center;
            padding: 2rem 0 1rem 0;
        }
        .main-title {
            font-size: 3rem;
            font-weight: 700;
            background: linear-gradient(120deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.5rem;
        }
        .subtitle {
            font-size: 1.2rem;
            color: #666;
            margin-bottom: 2rem;
        }
        .search-card {
            background: white;
            padding: 2rem;
            border-radius: 15px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.07);
            margin-bottom: 2rem;
        }
        .result-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1rem;
            border-radius: 12px;
            margin-bottom: 1.5rem;
        }
        .info-box {
            background: #f8f9fa;
            border-left: 4px solid #667eea;
            padding: 1rem;
            border-radius: 6px;
            margin: 1rem 0;
        }
        .stButton>button {
            width: 100%;
            background: linear-gradient(120deg, #667eea 0%, #764ba2 100%);
            color: white;
            font-weight: 600;
            vertical-align: top;
            padding: 0.5rem;
            border-radius: 10px;
            border: none;
            font-size: 1.1rem;
        }
        .stButton>button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 12px rgba(102,126,234,0.3);
        }
        .library-item {
            background: rgb(190 190 190 / 20%);
            border-radius: 10px;
            padding: 1rem;
            margin-bottom: 0.6rem;
        }
        .library-item.available {
            background: rgb(204 204 255/ 40%);
        }
        .distance-badge {
            display: inline-block;
            background: #667eea;
            color: white;
            padding: 0.3rem 0.8rem;
            margin: 0 0.3rem;
            vertical-align: 3px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 600;
        }
        .status-badge {
            display: inline-block;
            padding: 0.3rem 0.8rem;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 600;
        }
        .status-available {
            background: #d4edda;
            color: #155724;
        }
        .status-unavailable {
            background: #f8d7da;
            color: #721c24;
        }
    </style>
    """, unsafe_allow_html=True)

# ============================================================================
# 유틸리티 함수
# ============================================================================

import time as _time

_trace_start_times: Dict[str, float] = {}

def _write_trace(file: str, func: str, status: str, detail: str = ""):
    """Write a styled pipeline execution trace line inside st.status."""
    ts = datetime.now().strftime("%H:%M:%S")
    key = f"{file}:{func}"

    if status == "start":
        _trace_start_times[key] = _time.time()
        icon, color = "▶", "#89b4fa"
    elif status == "done":
        icon, color = "✓", "#a6e3a1"
    elif status == "error":
        icon, color = "✗", "#f38ba8"
    else:
        icon, color = "•", "#cdd6f4"

    elapsed = ""
    if status in ("done", "error") and key in _trace_start_times:
        secs = _time.time() - _trace_start_times.pop(key)
        elapsed = f'<span style="color:#585b70;font-size:0.78rem;"> {secs:.1f}s</span>'

    st.markdown(
        f'<div style="font-family:\'JetBrains Mono\',\'Fira Code\',monospace;'
        f'font-size:0.82rem;padding:2px 0;line-height:1.7;">'
        f'<span style="color:#585b70;">[{ts}]</span> '
        f'<span style="color:{color};">{icon}</span> '
        f'<span style="color:#cba6f7;">{file}</span> '
        f'<span style="color:#585b70;">›</span> '
        f'<span style="color:#89dceb;">{func}</span> '
        f'<span style="color:#a6adc8;">— {detail}</span>'
        f'{elapsed}</div>',
        unsafe_allow_html=True,
    )

def _render_parse_preview(raw_html: str, parsed_data: Dict):
    """Render a highlighted HTML block showing what BeautifulSoup extracted."""
    import html as _html

    # Color map for each field
    FIELD_COLORS = {
        "title":       ("#667eea", "Title"),
        "author":      ("#a6e3a1", "Author"),
        "library":     ("#cba6f7", "Library"),
        "status":      ("#fab387", "Status"),
        "call_number": ("#89dceb", "Call#"),
    }

    # Escape raw HTML for display
    escaped = _html.escape(raw_html)

    # Highlight each extracted value in the escaped HTML
    for field, (color, label) in FIELD_COLORS.items():
        value = parsed_data.get(field)
        if value and isinstance(value, str):
            safe_val = _html.escape(value)
            if safe_val in escaped:
                escaped = escaped.replace(
                    safe_val,
                    f'<mark style="background:{color}22;border-bottom:2px solid {color};'
                    f'border-radius:2px;padding:0 2px;" title="{label}">{safe_val}</mark>',
                    1,  # only first occurrence
                )

    # Build legend
    legend_items = []
    for field, (color, label) in FIELD_COLORS.items():
        val = parsed_data.get(field)
        if val:
            legend_items.append(
                f'<span style="display:inline-block;margin:2px 6px 2px 0;'
                f'padding:2px 8px;border-radius:4px;font-size:0.78rem;'
                f'background:{color}22;border-left:3px solid {color};">'
                f'<b>{label}</b>: {_html.escape(str(val))}</span>'
            )

    avail = parsed_data.get("available", False)
    avail_badge = (
        '<span style="background:#a6e3a122;color:#a6e3a1;padding:2px 8px;border-radius:10px;'
        'font-size:0.78rem;font-weight:600;">✓ Available</span>'
        if avail else
        '<span style="background:#f38ba822;color:#f38ba8;padding:2px 8px;border-radius:10px;'
        'font-size:0.78rem;font-weight:600;">✗ Checked out</span>'
    )
    legend_items.append(avail_badge)

    # Render component
    component_html = f"""
    <div style="font-family:system-ui,sans-serif;">
      <div style="margin-bottom:10px;line-height:2;">
        {''.join(legend_items)}
      </div>
      <div style="background:#1e1e2e;color:#cdd6f4;padding:14px;border-radius:8px;
                  font-family:'JetBrains Mono','Fira Code',monospace;font-size:0.75rem;
                  line-height:1.6;overflow-x:auto;white-space:pre-wrap;word-break:break-all;
                  max-height:350px;overflow-y:auto;border:1px solid #313244;">
{escaped}
      </div>
    </div>"""
    st.components.v1.html(component_html, height=440, scrolling=True)

def calculate_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """두 좌표 간 거리 계산 (Haversine 공식, km 단위)"""
    R = 6371  # 지구 반지름 (km)

    lat1, lng1, lat2, lng2 = map(radians, [lat1, lng1, lat2, lng2])
    dlat = lat2 - lat1
    dlng = lng2 - lng1

    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlng/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))

    return R * c


def format_duration(seconds: Optional[int]) -> str:
    """초 단위 시간을 한국어로 읽기 좋은 문자열로 변환"""
    if seconds is None:
        return "정보 없음"
    minutes = max(1, (int(seconds) + 59) // 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}시간 {minutes}분" if minutes else f"{hours}시간"
    return f"{minutes}분"


def format_distance(route_distance_m: Optional[float], fallback_distance_km: float) -> str:
    """경로 거리(미터)와 직선거리(km)를 기반으로 표시 문자열 생성"""
    if route_distance_m:
        if route_distance_m >= 1000:
            return f"{route_distance_m / 1000:.1f} km"
        return f"{int(route_distance_m)} m"
    return f"{fallback_distance_km:.2f} km"


def parse_jsonl(jsonl_text: str) -> List[Dict]:
    """JSONL 텍스트를 파싱"""
    results = []
    for line in jsonl_text.strip().split('\n'):
        if line.strip():
            try:
                results.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return results


def get_coordinates(address: str) -> Optional[Tuple[float, float, str]]:
    """주소를 좌표로 변환 (Google Geocoding API)"""
    if not GOOGLE_MAPS_API_KEY:
        st.error("GOOGLE_MAPS_API_KEY 환경변수가 설정되지 않았습니다.")
        return None
        
    try:
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {
            "address": address,
            "key": GOOGLE_MAPS_API_KEY,
            "language": "ko"
        }
        response = requests.get(url, params=params, timeout=TIMEOUT)
        response.raise_for_status()
        
        data = response.json()
        if data.get("status") != "OK" or not data.get("results"):
            return None
            
        doc = data["results"][0]
        location = doc["geometry"]["location"]
        lng = float(location["lng"])
        lat = float(location["lat"])
        
        display_name = doc.get("formatted_address", "")
        region = ""
        if "강남구" in display_name:
            region = "강남구"
        elif "서초구" in display_name:
            region = "서초구"
        elif "송파구" in display_name:
            region = "송파구"
        else:
            region = "강남구"  # 기본값
        
        return (lng, lat, region)
    except Exception as e:
        st.error(f"좌표 변환 중 오류: {e}")
        return None

def get_library_with_distance(library_name: str, user_lat: float, user_lng: float) -> Optional[Dict]:
    """도서관 정보 및 거리 계산"""
    if library_name not in LIBRARY_ADDRESS_MAP:
        return None
    
    address = LIBRARY_ADDRESS_MAP[library_name]
    coords = get_coordinates(address)
    
    if not coords:
        return None
    
    lib_lng, lib_lat, _ = coords

    route_info = route_points(user_lng, user_lat, lib_lng, lib_lat)
    polyline_points = None
    route_duration = None
    route_distance_m = None
    straight_distance_km = None

    if route_info:
        polyline_points, route_duration, route_distance_m = route_info

    if route_distance_m is not None:
        distance_km = route_distance_m / 1000
    else:
        straight_distance_km = calculate_distance(user_lat, user_lng, lib_lat, lib_lng)
        distance_km = straight_distance_km

    result = {
        "name": library_name,
        "address": address,
        "lat": lib_lat,
        "lng": lib_lng,
        "distance": distance_km,
        "duration": route_duration,
        "route_distance_m": route_distance_m,
        "polyline_points": polyline_points,
    }
    if straight_distance_km is not None:
        result["straight_distance"] = straight_distance_km

    return result


def process_book_results(
    jsonl_data: str, user_lat: float, user_lng: float, include_unavailable: bool = False
) -> Tuple[List[Dict], List[Dict], List[Dict], Optional[str]]:
    """
    도서 검색 결과 처리 및 도서관별 거리 계산
    
    Args:
        jsonl_data: JSONL 형식의 검색 결과
        user_lat: 사용자 위도
        user_lng: 사용자 경도
        include_unavailable: 대출불가 도서도 포함할지 여부
    
    Returns:
        (map_libraries, available_libraries, unavailable_libraries, first_cover_image)
    """
    results = parse_jsonl(jsonl_data)
    first_cover_image = next(
        (item.get("cover_image") for item in results if item.get("cover_image")), None
    )

    # 도서관별로 그룹화
    available_by_lib = {}  # 대출 가능
    unavailable_by_lib = {}  # 대출 불가
    
    for item in results:
        lib_name = item.get("library")
        if not lib_name:
            continue
        
        if item.get("available", False):
            if lib_name not in available_by_lib:
                available_by_lib[lib_name] = []
            available_by_lib[lib_name].append(item)
        else:
            if lib_name not in unavailable_by_lib:
                unavailable_by_lib[lib_name] = []
            unavailable_by_lib[lib_name].append(item)

    # 대출 가능 도서관 좌표 및 거리 계산
    available_library_coords = []
    for lib_name in available_by_lib.keys():
        lib_info = get_library_with_distance(lib_name, user_lat, user_lng)
        if lib_info:
            lib_info["books"] = available_by_lib[lib_name]
            lib_info["available_count"] = len(available_by_lib[lib_name])
            available_library_coords.append(lib_info)
    
    # 대출 불가 도서관 좌표 및 거리 계산
    unavailable_library_coords = []
    if include_unavailable:
        for lib_name in unavailable_by_lib.keys():
            # 이미 대출 가능 목록에 있는 도서관은 제외
            if lib_name in available_by_lib:
                # 대출 가능 도서관에 대출불가 도서 추가
                for lib_info in available_library_coords:
                    if lib_info["name"] == lib_name:
                        lib_info["unavailable_books"] = unavailable_by_lib[lib_name]
                        break
            else:
                lib_info = get_library_with_distance(lib_name, user_lat, user_lng)
                if lib_info:
                    lib_info["books"] = []
                    lib_info["unavailable_books"] = unavailable_by_lib[lib_name]
                    lib_info["available_count"] = 0
                    unavailable_library_coords.append(lib_info)
    
    # 이동 시간 우선 정렬(경로 정보가 없으면 거리 기준으로 대체)
    available_library_coords.sort(key=lambda lib: (0, lib["duration"]) if lib["duration"] is not None else (1, lib["distance"]))
    unavailable_library_coords.sort(key=lambda lib: (0, lib["duration"]) if lib["duration"] is not None else (1, lib["distance"]))

    # 지도용 (상위 N개)
    map_libraries = available_library_coords[:TOP_N_MAP]
    
    return map_libraries, available_library_coords, unavailable_library_coords, first_cover_image

def route_points(start_lng, start_lat, end_lng, end_lat):
    """Google Directions API로 이동 경로 및 소요 시간/거리 조회 (자동차 기준)"""
    if not GOOGLE_MAPS_API_KEY:
        return None

    url = "https://maps.googleapis.com/maps/api/directions/json"
    params = {
        "origin": f"{start_lat},{start_lng}",
        "destination": f"{end_lat},{end_lng}",
        "mode": "driving",
        "language": "ko",
        "key": GOOGLE_MAPS_API_KEY
    }

    def _show_route_warning():
        if not st.session_state.get("_route_warning_shown"):
            st.warning("길찾기 정보를 불러오지 못해 직선거리로 대체합니다.")
            st.session_state["_route_warning_shown"] = True

    try:
        res = requests.get(url, params=params, timeout=TIMEOUT)
        res.raise_for_status()
    except requests.RequestException as exc:
        _show_route_warning()
        print(f"[route_points] request error: {exc}")
        return None

    data = res.json()
    if data.get("status") != "OK" or not data.get("routes"):
        _show_route_warning()
        return None

    route = data["routes"][0]
    leg = route["legs"][0]
    
    # encoded polyline for the entire route
    overview_polyline = route.get("overview_polyline", {}).get("points", "")
    polyline_points = None
    
    if overview_polyline:
        # Decode google encoded polyline into list of [lat, lng]
        # Using a simple decoder inline
        def decode_polyline(polyline_str):
            index, lat, lng = 0, 0, 0
            coordinates = []
            changes = {'latitude': 0, 'longitude': 0}
            while index < len(polyline_str):
                for unit in ['latitude', 'longitude']:
                    shift, result = 0, 0
                    while True:
                        byte = ord(polyline_str[index]) - 63
                        index += 1
                        result |= (byte & 0x1f) << shift
                        shift += 5
                        if not byte >= 0x20:
                            break
                    if (result & 1):
                        changes[unit] += ~(result >> 1)
                    else:
                        changes[unit] += (result >> 1)
                lat += changes['latitude']
                lng += changes['longitude']
                coordinates.append([lat / 100000.0, lng / 100000.0])
            return coordinates
            
        coords = decode_polyline(overview_polyline)
        # JS expects format like: [{lat: ..., lng: ...}, ...] or array of arrays
        # Google Maps JS API Polyline path takes array of {lat, lng} objects:
        polyline_points = ",\n".join([f"{{lat: {lat}, lng: {lng}}}" for lat, lng in coords])

    # duration in seconds, distance in meters
    duration = leg.get("duration", {}).get("value")
    distance = leg.get("distance", {}).get("value")

    return polyline_points, duration, distance

def generate_map_html(user_lat: float, user_lng: float, 
                     library_coords: List[Dict], book_name: str) -> str:
    """오픈스트리트맵(Leaflet) 맵 HTML 생성"""

    markers_js = f"""
        var userLatLng = [{user_lat}, {user_lng}];
        var redIcon = new L.Icon({{
            iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
            shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
            iconSize: [25, 41],
            iconAnchor: [12, 41],
            popupAnchor: [1, -34],
            shadowSize: [41, 41]
        }});

        L.marker(userLatLng, {{icon: redIcon}}).addTo(map)
            .bindPopup("<b>내 위치</b>")
            .openPopup();
            
        bounds.push(userLatLng);
    """
    
    for idx, lib in enumerate(library_coords):

        duration_text = format_duration(lib.get("duration"))
        distance_text = format_distance(
            lib.get("route_distance_m"),
            lib.get("straight_distance", lib["distance"])
        )

        info_html = f"""
        <div style="font-size:13px; font-family:'Malgun Gothic',sans-serif; min-width:180px;">
            <div style="font-weight:bold; font-size:15px; margin-bottom:5px; padding-bottom:5px; border-bottom:1px solid #ccc;">
                {lib['name']}
            </div>
            <div>📍 {lib['address']}</div>
            <div style="margin-top:4px;">🚘 이동시간: {duration_text}</div>
            <div style="margin-top:4px;">📏 이동거리: {distance_text}</div>
            <div style="margin-top:6px;">
                <a href='https://map.kakao.com/link/from/내위치,{user_lat},{user_lng}/to/{lib['name']},{lib['lat']},{lib['lng']}' target='_blank' style='color:#667eea; text-decoration:none; font-weight:bold;'>
                    ⤴️ 카카오맵에서 길찾기
                </a>
            </div>
        </div>
        """

        polyline_js = ""
        if lib.get("polyline_points"):
            polyline_js = f"""
                var linePath_{idx} = [
                    {lib['polyline_points']}
                ];

                L.polyline(linePath_{idx}, {{
                    color: '#0078ff',
                    weight: 5,
                    opacity: 0.8
                }}).addTo(map);
            """
        
        markers_js += f"""
            (function() {{
                var libLatLng_{idx} = [{lib['lat']}, {lib['lng']}];
                var blueIcon = new L.Icon({{
                    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png',
                    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
                    iconSize: [25, 41],
                    iconAnchor: [12, 41],
                    popupAnchor: [1, -34],
                    shadowSize: [41, 41]
                }});

                L.marker(libLatLng_{idx}, {{icon: blueIcon}}).addTo(map)
                    .bindPopup(`{info_html}`);

                {polyline_js}
                
                bounds.push(libLatLng_{idx});
            }})();
        """
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8"/>
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <style>
            body {{ margin: 0; padding: 0; }}
            #map {{ width: 100%; height: 550px; border-radius: 10px; }}
        </style>
    </head>
    <body>
        <div id="map"></div>
        <script>
            var map = L.map('map').setView([{user_lat}, {user_lng}], 13);
            L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                maxZoom: 19,
                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            }}).addTo(map);
            
            var bounds = [];
            {markers_js}
            
            if (bounds.length > 0) {{
                map.fitBounds(bounds, {{padding: [30, 30]}});
            }}
        </script>
    </body>
    </html>
    """

def _render_book_card(book: Dict, available: bool = True):
    """도서 카드 렌더링 헬퍼 함수"""
    cover_img = book.get('cover_image') or "https://public.seocholib.or.kr/resources/images/cover/no-image-MO.png"
    
    # 상태 배지
    if available:
        status_badge = '<span style="background:#d4edda;color:#155724;padding:2px 8px;border-radius:10px;font-size:0.8rem;">대출가능</span>'
    else:
        return_date = book.get('return_date', '')
        if return_date:
            status_badge = f'<span style="background:#f8d7da;color:#721c24;padding:2px 8px;border-radius:10px;font-size:0.8rem;">반납예정: {return_date}</span>'
        else:
            status_badge = '<span style="background:#f8d7da;color:#721c24;padding:2px 8px;border-radius:10px;font-size:0.8rem;">대출중</span>'
    
    # 스타일 (대출불가는 투명도 적용)
    opacity = "1" if available else "0.7"
    
    st.markdown(f"""
    <div style="display:flex; align-items:flex-start; gap:0.8rem; margin-bottom:0.8rem; opacity:{opacity};">
        <img src="{cover_img}" alt="book cover" width="90" height="120"
        style="border-radius:6px; object-fit:cover; flex-shrink:0;">
        <div>
            <div style="font-weight:bold; font-size:1.2rem;">{book['title']} {status_badge}</div>
            <div style="margin-top:0.3rem;">· 저자: {book.get('author', 'N/A')}</div>
            <div>· 청구기호: {book.get('call_number', '홈페이지에서 확인하세요.')}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def show_library_search_button(book_name: str, user_region: str):
    """지역별 도서관 검색 버튼을 표시"""
    encoded_book = urllib.parse.quote(book_name)

    library_urls = {
        "강남구": f"https://library.gangnam.go.kr/intro/menu/10003/program/30001/plusSearchResultList.do?searchType=SIMPLE&searchMenuCollectionCategory=&searchCategory=ALL&searchKey=ALL&searchKeyword={encoded_book}&searchLibrary=ALL",
        "서초구": f"https://public.seocholib.or.kr/KeywordSearchResult/{encoded_book}",
        "송파구": f"https://www.splib.or.kr/intro/menu/10003/program/30001/plusSearchSimple.do"
    }

    # 현재 지역에 맞는 URL 찾기
    for region, url in library_urls.items():
        if region.startswith(user_region):
            st.link_button(
                f"🔗 {region} 통합도서관에서 직접 검색하기",
                url,
                width='stretch'
            )
            break  # 찾으면 반복 종료

# ============================================================================
# 검색 히스토리 관리
# ============================================================================

MAX_HISTORY_SIZE = 5  # 최대 히스토리 저장 개수

def add_to_history(address: str, book_name: str, is_multi_region: bool):
    """검색 기록 추가"""
    if "search_history" not in st.session_state:
        st.session_state["search_history"] = []
    
    history = st.session_state["search_history"]
    
    # 중복 제거 (같은 검색어가 있으면 제거 후 맨 앞에 추가)
    new_entry = {
        "address": address,
        "book_name": book_name,
        "is_multi_region": is_multi_region,
        "timestamp": datetime.now().isoformat(timespec="seconds")
    }
    
    # 기존에 같은 검색이 있으면 제거
    history = [h for h in history if not (h["address"] == address and h["book_name"] == book_name)]
    
    # 맨 앞에 추가
    history.insert(0, new_entry)
    
    # 최대 개수 제한
    st.session_state["search_history"] = history[:MAX_HISTORY_SIZE]


def get_history() -> List[Dict]:
    """검색 기록 조회"""
    return st.session_state.get("search_history", [])


# ============================================================================
# UI 렌더링
# ============================================================================

# 사이드바 - 검색 히스토리
with st.sidebar:
    st.markdown("### 📜 최근 검색")
    
    history = get_history()
    
    if not history:
        st.caption("검색 기록이 없습니다.")
    else:
        for idx, h in enumerate(history):
            # 멀티지역 표시
            region_badge = "🌐" if h.get("is_multi_region") else "📍"
            
            # 검색 버튼
            btn_label = f"{region_badge} {h['book_name'][:15]}{'...' if len(h['book_name']) > 15 else ''}"
            
            if st.button(btn_label, key=f"history_{idx}", use_container_width=True):
                # 검색 정보를 session_state에 설정
                st.session_state["address"] = h["address"]
                st.session_state["book_name"] = h["book_name"]
                st.session_state["search_all_regions"] = h.get("is_multi_region", False)
                st.rerun()
            
            # 상세 정보 표시
            st.caption(f"└ {h['address'][:20]}{'...' if len(h['address']) > 20 else ''}")
    
    st.markdown("---")
    
    # 캐시 정보 표시
    st.markdown("### 💾 캐시 정보")
    sys.path.insert(0, "00_src")
    from utils.cache import list_cached_searches
    
    cached = list_cached_searches()
    if cached:
        st.caption(f"캐시된 검색: {len(cached)}개")
        for c in cached[:3]:
            age_text = f"{c['age_hours']:.1f}시간 전"
            st.caption(f"• {c['title'][:12]}... ({age_text})")
    else:
        st.caption("캐시된 검색이 없습니다.")

# 헤더
st.markdown("""
    <div class="main-header">
        <div class="main-title">📚 Book Toss</div>
        <div class="subtitle">내 근처 공공 도서관을 쉽게 찾아보세요</div>
    </div>
    """, unsafe_allow_html=True)

# 검색 폼
col1, col2 = st.columns([2, 2])

with col1:
    address = st.text_input(
        "📍 내 주소",
        value="개포로 416",
        placeholder="서울특별시 강남구 개포로 416"
    )

with col2:
    book_name = st.text_input(
        "📖 찾고 싶은 도서",
        value="트랜드 코리아 2025",
        placeholder="트렌드 코리아 2025"
    )

# 검색 옵션 및 버튼
opt_col1, opt_col2, opt_col3 = st.columns([2, 2, 1])

with opt_col1:
    search_all_regions = st.checkbox(
        "🌐 전체 지역 검색",
        value=False,
        help="체크하면 강남구, 서초구, 송파구 모든 도서관에서 검색합니다."
    )

with opt_col2:
    show_unavailable = st.checkbox(
        "📚 대출불가 도서도 표시",
        value=False,
        help="대출 중인 도서도 함께 표시합니다. 반납예정일을 확인할 수 있어요."
    )

with opt_col3:
    search_btn = st.button("🔍 검색하기", use_container_width=True)

# 검색 실행
if search_btn:
    if not address.strip():
        st.warning("📍 주소를 입력해주세요")
        st.stop()
    elif not book_name.strip():
        st.warning("📖 도서명을 입력해주세요")
        st.stop()
    else:
        st.session_state["address"] = address.strip()
        st.session_state["book_name"] = book_name.strip()
        st.session_state["search_all_regions"] = search_all_regions
        st.session_state["show_unavailable"] = show_unavailable
        # 검색 히스토리에 추가
        add_to_history(address.strip(), book_name.strip(), search_all_regions)

# 결과 표시
if ("address" in st.session_state and "book_name" in st.session_state and
    st.session_state["address"].strip() and st.session_state["book_name"].strip()):
    # st.markdown("---")
    
    stop_event = None  # (level, message)
    show_search_btn = False
    map_libraries: List[Dict] = []
    all_libraries: List[Dict] = []
    first_cover_image: Optional[str] = None
    _pipeline_result = None  # pipeline result for parse preview

    # 전체 지역 검색 여부 확인
    is_multi_region = st.session_state.get("search_all_regions", False)
    search_title = st.session_state["book_name"]
    
    # 진행 상태 표시용 status 컴포넌트 (Pipeline Trace)
    with st.status("🔬 Pipeline Execution", expanded=True) as status:
        # Step 1: 주소 → 좌표 변환
        _write_trace("app.py", "get_coordinates()", "start", "Converting address to coordinates...")

        user_coords = get_coordinates(st.session_state["address"])

        if not user_coords:
            _write_trace("app.py", "get_coordinates()", "error", "Address not found")
            status.update(label="❌ Address resolution failed", state="error")
            stop_event = ("error", "❌ 입력하신 주소를 찾을 수 없거나 주소 정보가 부족합니다. 주소를 다시 확인해주세요.")
        else:
            user_lng, user_lat, user_region = user_coords
            _write_trace("app.py", "get_coordinates()", "done", f"Resolved → {user_region} ({user_lat:.4f}, {user_lng:.4f})")

            # 실제 도서관 검색 실행 (pipeline_graph 연동)
            sys.path.insert(0, "00_src")
            from graph.pipeline_graph import run_once, run_multi_region, REGION_NAMES

            # Step 2: 도서관 검색
            if is_multi_region:
                # 멀티지역 검색 모드
                _write_trace("pipeline_graph.py", "run_multi_region()", "start", "Parallel search across 3 regions...")

                progress_placeholder = st.empty()
                region_status = {"gangnam": "⏳", "seocho": "⏳", "songpa": "⏳"}

                def update_progress(region: str, state: str, message: str):
                    if state == "start":
                        region_status[region] = "🔄"
                    elif state == "cache_hit":
                        region_status[region] = "✅ (캐시)"
                    elif state == "success":
                        region_status[region] = "✅"
                    elif state == "error":
                        region_status[region] = "❌"
                    status_text = " | ".join([
                        f"{REGION_NAMES.get(r, r)}: {s}" for r, s in region_status.items()
                    ])
                    progress_placeholder.write(status_text)

                start_time = _time.time()
                result = run_multi_region(title=search_title, progress_callback=update_progress)
                elapsed_time = _time.time() - start_time

                _write_trace("pipeline_graph.py", "run_multi_region()", "done", f"Found {result.get('total_count', 0)} books ({elapsed_time:.1f}s)")

                if result.get("total_count", 0) > 0:
                    jsonl_data = "\n".join([
                        json.dumps(book, ensure_ascii=False)
                        for book in result.get("all_books", [])
                    ])
                else:
                    status.update(label="❌ No results", state="error")
                    stop_event = ("error", "❌ 검색 결과가 없습니다. 다시 시도해주세요.")

            else:
                # 단일 지역 검색 모드  — pipeline trace callback
                place = ALLOWED_REGION_TO_PLACE.get(user_region)

                if not place:
                    _write_trace("app.py", "region_check", "error", f"Unsupported region: {user_region}")
                    status.update(label="⚠️ 지원하지 않는 지역", state="error")
                    stop_event = ("warning", "😥 입력하신 지역의 서비스는 아직 준비 중입니다. 강남구, 서초구, 송파구 내에서 검색해주세요.")
                else:
                    def pipeline_progress(**kwargs):
                        _write_trace(
                            kwargs.get("file", ""),
                            kwargs.get("function", ""),
                            kwargs.get("status", ""),
                            kwargs.get("detail", ""),
                        )

                    start_time = _time.time()
                    result = run_once(place=place, title=search_title, progress_callback=pipeline_progress)
                    elapsed_time = _time.time() - start_time
                    _pipeline_result = result

                    _write_trace("pipeline_graph.py", "run_once()", "done", f"Pipeline finished in {elapsed_time:.1f}s")

                    # JSONL 데이터 추출
                    jsonl_path = result.get("out_jsonl")
                    if jsonl_path and os.path.exists(jsonl_path):
                        with open(jsonl_path, "r", encoding="utf-8") as f:
                            jsonl_data = f.read()
                        # 파싱 결과가 0건이면 검색 실패 처리
                        if not jsonl_data.strip():
                            _write_trace("app.py", "jsonl_check", "error", "JSONL empty — 0 books parsed from HTML")
                            status.update(label="⚠️ 파싱 결과 없음", state="error")
                            stop_event = ("warning", "⚠️ 도서관 사이트에서 HTML을 가져왔지만 도서 정보를 추출하지 못했습니다. 검색어를 다시 확인해주세요.")
                            show_search_btn = True
                    else:
                        status.update(label="❌ Search failed", state="error")
                        stop_event = ("error", "❌ 도서관 검색에 실패했습니다. 다시 시도해주세요.")

            # Step 3: 결과 분석
            if not stop_event:
                _write_trace("app.py", "process_book_results()", "start", "Calculating distances & sorting libraries...")

                show_unavailable_books = st.session_state.get("show_unavailable", False)

                (
                    map_libraries,
                    all_libraries,
                    unavailable_libraries,
                    first_cover_image,
                ) = process_book_results(jsonl_data, user_lat, user_lng, include_unavailable=show_unavailable_books)

                if not all_libraries and not unavailable_libraries:
                    _write_trace("app.py", "process_book_results()", "done", "No available libraries found")
                    status.update(label="⚠️ 대출 가능한 도서관 없음", state="error")
                    stop_event = ("warning", "⚠️ 현재 대출 가능한 도서관을 찾을 수 없습니다.")
                    show_search_btn = True
                elif not all_libraries and unavailable_libraries:
                    _write_trace("app.py", "process_book_results()", "done", f"0 available, {len(unavailable_libraries)} checked-out")
                    status.update(label=f"⚠️ 대출가능 없음, 대출중 {len(unavailable_libraries)}곳", state="complete")
                else:
                    total = len(all_libraries) + len(unavailable_libraries)
                    _write_trace("app.py", "process_book_results()", "done", f"Found {len(all_libraries)} available + {len(unavailable_libraries)} checked-out libraries")
                    status.update(label=f"✅ Complete — {total} libraries found", state="complete")

    if stop_event:
        level, message = stop_event
        if level == "error":
            st.error(message)
        elif level == "warning":
            st.warning(message)
        else:
            st.info(message)
        if show_search_btn:
            show_library_search_button(st.session_state["book_name"], user_region)
        st.stop()
    else:
        # 결과 카드
        st.write("")
        with st.container(horizontal_alignment="center"):
            if first_cover_image:
                st.image(
                    first_cover_image,
                    width=200,
                    caption=None,
                    clamp=True,
                    channels="RGB",
                    output_format="auto",
                )
        
        # 검색 지역 표시
        if is_multi_region:
            region_text = "강남/서초/송파"
        else:
            region_text = user_region
        
        st.markdown(f"""
        <div class="result-card">
            <h3 style="text-align:center;">📖 {st.session_state['book_name']}</h3>
            <p style="margin:0.5rem 0 0 0; opacity:0.9;text-align:center;">
                {region_text}에서 대출 가능한 도서관 {len(all_libraries)}곳을 찾았어요! 🥳
            </p>
        </div>
        """, unsafe_allow_html=True)

        # 🔬 BeautifulSoup Parsing Preview
        _sample_html = _pipeline_result.get("parse_sample_html") if _pipeline_result else None
        _sample_data = _pipeline_result.get("parse_sample_data") if _pipeline_result else None
        if _sample_html and _sample_data:
            with st.expander("🔬 BeautifulSoup Extraction Preview", expanded=False):
                st.caption("How the parser extracted structured data from raw HTML")
                _render_parse_preview(_sample_html, _sample_data)

        # 지도 표시 (가장 가까운 N개)
        if map_libraries:
            st.markdown(f"#### 🗺️ 가장 가까운 도서관")
            map_html = generate_map_html(
                user_lat, user_lng, map_libraries, st.session_state['book_name']
            )
            st.components.v1.html(map_html, height=570)
        
        # 전체 도서관 목록
        for idx, lib in enumerate(all_libraries):
            is_top = idx < TOP_N_MAP
            status_class = "available" if is_top else ""
            duration_text = format_duration(lib.get("duration"))
            distance_text = format_distance(
                lib.get("route_distance_m"),
                lib.get("straight_distance", lib["distance"])
            )
            distance_badge = f"{duration_text}"
            
            with st.container():
                st.markdown(f"""
                <div class="library-item {status_class}">
                    <h4>
                        {'🥇' if idx == 0 else '🥈' if idx == 1 else ''} {lib['name']}
                        <span class="distance-badge">차로 {distance_badge}</span>
                    </h4>
                    <p style="margin:0 0; display:flex; align-items:center; gap:0.4rem;">
                        <span style="flex:0 1 auto; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">
                            {lib['address']}
                        </span>
                        <a href="https://map.kakao.com/link/from/내위치,{user_lat},{user_lng}/to/{lib['name']},{lib['lat']},{lib['lng']}" 
                        target="_blank"
                        title="길찾기"
                        style="
                            display:inline-flex;
                            align-items:center;
                            justify-content:center;
                            height:1.7rem;
                            border-radius:50%;
                            background: none;
                            font-size:0.8rem;
                            flex-shrink:0;
                        ">
                        길찾기
                        </a>
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                with st.expander(f"📚 대출 가능 도서 {len(lib['books'])}권", expanded=True):
                    for book in lib['books']:
                        _render_book_card(book, available=True)
                
                # 대출불가 도서도 표시 (해당 도서관에 있는 경우)
                unavailable_books = lib.get('unavailable_books', [])
                if unavailable_books and show_unavailable_books:
                    with st.expander(f"📕 대출 중 도서 {len(unavailable_books)}권", expanded=False):
                        for book in unavailable_books:
                            _render_book_card(book, available=False)
                
                st.write("")
        
        # 대출불가 도서관 표시 (대출 가능한 도서가 없는 도서관)
        if unavailable_libraries and show_unavailable_books:
            st.markdown("---")
            st.markdown("#### 📕 대출 중인 도서관")
            st.caption("현재 대출 가능한 도서가 없지만, 반납 후 대출할 수 있는 도서관입니다.")
            
            for lib in unavailable_libraries:
                duration_text = format_duration(lib.get("duration"))
                distance_text = format_distance(
                    lib.get("route_distance_m"),
                    lib.get("straight_distance", lib["distance"])
                )
                
                with st.container():
                    st.markdown(f"""
                    <div class="library-item" style="opacity: 0.7; border-left: 3px solid #f8d7da;">
                        <h4>
                            📕 {lib['name']}
                            <span class="distance-badge" style="background: #999;">차로 {duration_text}</span>
                        </h4>
                        <p style="margin:0 0;">
                            {lib['address']}
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    unavailable_books = lib.get('unavailable_books', [])
                    if unavailable_books:
                        with st.expander(f"📕 대출 중 도서 {len(unavailable_books)}권", expanded=False):
                            for book in unavailable_books:
                                _render_book_card(book, available=False)
                    
                    st.write("")
        
        show_library_search_button(st.session_state["book_name"], user_region)

        # 검색 결과 내보내기
        st.markdown("---")
        st.markdown("#### 💾 검색 결과 내보내기")
        
        # 내보내기 데이터 준비
        export_data = []
        for lib in all_libraries:
            for book in lib.get("books", []):
                export_data.append({
                    "도서명": book.get("title", ""),
                    "저자": book.get("author", ""),
                    "도서관": lib.get("name", ""),
                    "주소": lib.get("address", ""),
                    "대출상태": "대출가능",
                    "청구기호": book.get("call_number", ""),
                    "거리(km)": f"{lib.get('distance', 0):.2f}",
                })
            for book in lib.get("unavailable_books", []):
                export_data.append({
                    "도서명": book.get("title", ""),
                    "저자": book.get("author", ""),
                    "도서관": lib.get("name", ""),
                    "주소": lib.get("address", ""),
                    "대출상태": f"대출중 (반납예정: {book.get('return_date', '미정')})",
                    "청구기호": book.get("call_number", ""),
                    "거리(km)": f"{lib.get('distance', 0):.2f}",
                })
        
        # 대출불가 도서관의 도서도 추가
        for lib in unavailable_libraries:
            for book in lib.get("unavailable_books", []):
                export_data.append({
                    "도서명": book.get("title", ""),
                    "저자": book.get("author", ""),
                    "도서관": lib.get("name", ""),
                    "주소": lib.get("address", ""),
                    "대출상태": f"대출중 (반납예정: {book.get('return_date', '미정')})",
                    "청구기호": book.get("call_number", ""),
                    "거리(km)": f"{lib.get('distance', 0):.2f}",
                })
        
        # 다운로드 버튼
        export_col1, export_col2 = st.columns(2)
        
        with export_col1:
            # CSV 다운로드
            if export_data:
                import csv
                import io
                
                csv_buffer = io.StringIO()
                writer = csv.DictWriter(csv_buffer, fieldnames=export_data[0].keys())
                writer.writeheader()
                writer.writerows(export_data)
                
                st.download_button(
                    label="📄 CSV로 다운로드",
                    data=csv_buffer.getvalue().encode("utf-8-sig"),  # BOM 포함 (Excel 호환)
                    file_name=f"booktoss_{search_title}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv",
                    use_container_width=True,
                )
        
        with export_col2:
            # JSON 다운로드
            if export_data:
                json_data = json.dumps(export_data, ensure_ascii=False, indent=2)
                
                st.download_button(
                    label="📋 JSON으로 다운로드",
                    data=json_data.encode("utf-8"),
                    file_name=f"booktoss_{search_title}_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                    mime="application/json",
                    use_container_width=True,
                )

        # 푸터 안내
        st.markdown("---")
        st.markdown("""
        <div style="text-align:center; color:#999; font-size:0.9rem; padding:1rem 0;">
            💡 <b>TIP:</b> 지도의 도서관 마커를 클릭하면 상세 정보를 확인할 수 있어요
        </div>
        """, unsafe_allow_html=True)
