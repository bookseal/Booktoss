"""
cache.py

검색 결과 캐싱 시스템

기능:
- 동일한 (place, title) 조합의 검색 결과를 캐시하여 재사용
- 기본 24시간 이내의 캐시는 유효한 것으로 처리
- API 비용 절감 및 응답 시간 단축

사용법:
    from utils.cache import get_cached_result, save_to_cache, is_cache_valid

    # 캐시 확인
    cached = get_cached_result(place="gangnam", title="어린 왕자")
    if cached:
        return cached  # 캐시된 JSONL 경로 반환

    # 검색 후 캐시 저장
    save_to_cache(place="gangnam", title="어린 왕자", jsonl_path="path/to/results.jsonl")
"""

from __future__ import annotations
from typing import Optional, Dict, Any
from pathlib import Path
from datetime import datetime, timedelta
import hashlib
import json
import os
import shutil


# 기본 캐시 디렉토리
DEFAULT_CACHE_DIR = os.path.join("00_src", "data", "cache")

# 기본 캐시 유효 시간 (시간 단위)
DEFAULT_MAX_AGE_HOURS = 24


def _get_title_hash(title: str) -> str:
    """
    제목을 해시하여 파일명에 사용할 수 있는 문자열 생성
    
    Args:
        title: 검색어(도서명)
    
    Returns:
        8자리 해시 문자열
    """
    return hashlib.md5(title.encode("utf-8")).hexdigest()[:8]


def _get_cache_paths(place: str, title: str, cache_dir: str = DEFAULT_CACHE_DIR) -> tuple[Path, Path]:
    """
    캐시 파일 경로 생성
    
    Returns:
        (jsonl_path, meta_path) 튜플
    """
    title_hash = _get_title_hash(title)
    base_name = f"{place}_{title_hash}"
    
    cache_path = Path(cache_dir)
    jsonl_path = cache_path / f"{base_name}.jsonl"
    meta_path = cache_path / f"{base_name}.meta.json"
    
    return jsonl_path, meta_path


def is_cache_valid(
    place: str,
    title: str,
    max_age_hours: int = DEFAULT_MAX_AGE_HOURS,
    cache_dir: str = DEFAULT_CACHE_DIR
) -> bool:
    """
    캐시가 유효한지 확인
    
    Args:
        place: 지역 코드 (gangnam, seocho, songpa)
        title: 검색어(도서명)
        max_age_hours: 캐시 최대 유효 시간 (기본 24시간)
        cache_dir: 캐시 디렉토리 경로
    
    Returns:
        캐시가 유효하면 True, 아니면 False
    """
    jsonl_path, meta_path = _get_cache_paths(place, title, cache_dir)
    
    # 파일 존재 확인
    if not jsonl_path.exists() or not meta_path.exists():
        return False
    
    # 메타 파일 읽기
    try:
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
        
        # 생성 시간 확인
        created_at = datetime.fromisoformat(meta.get("created_at", ""))
        age = datetime.now() - created_at
        
        if age < timedelta(hours=max_age_hours):
            return True
            
    except (json.JSONDecodeError, ValueError, KeyError):
        pass
    
    return False


def get_cached_result(
    place: str,
    title: str,
    max_age_hours: int = DEFAULT_MAX_AGE_HOURS,
    cache_dir: str = DEFAULT_CACHE_DIR
) -> Optional[str]:
    """
    캐시된 검색 결과 경로 반환
    
    Args:
        place: 지역 코드 (gangnam, seocho, songpa)
        title: 검색어(도서명)
        max_age_hours: 캐시 최대 유효 시간 (기본 24시간)
        cache_dir: 캐시 디렉토리 경로
    
    Returns:
        캐시된 JSONL 파일 경로 (유효한 캐시가 없으면 None)
    """
    if not is_cache_valid(place, title, max_age_hours, cache_dir):
        return None
    
    jsonl_path, _ = _get_cache_paths(place, title, cache_dir)
    return str(jsonl_path)


def get_cache_meta(
    place: str,
    title: str,
    cache_dir: str = DEFAULT_CACHE_DIR
) -> Optional[Dict[str, Any]]:
    """
    캐시 메타 정보 반환
    
    Returns:
        메타 정보 딕셔너리 (없으면 None)
    """
    _, meta_path = _get_cache_paths(place, title, cache_dir)
    
    if not meta_path.exists():
        return None
    
    try:
        with open(meta_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None


def save_to_cache(
    place: str,
    title: str,
    jsonl_path: str,
    cache_dir: str = DEFAULT_CACHE_DIR,
    extra_meta: Optional[Dict[str, Any]] = None
) -> str:
    """
    검색 결과를 캐시에 저장
    
    Args:
        place: 지역 코드
        title: 검색어
        jsonl_path: 원본 JSONL 파일 경로
        cache_dir: 캐시 디렉토리 경로
        extra_meta: 추가 메타 정보
    
    Returns:
        캐시된 JSONL 파일 경로
    """
    # 캐시 디렉토리 생성
    cache_path = Path(cache_dir)
    cache_path.mkdir(parents=True, exist_ok=True)
    
    # 캐시 파일 경로
    cached_jsonl, meta_path = _get_cache_paths(place, title, cache_dir)
    
    # JSONL 파일 복사
    source = Path(jsonl_path)
    if source.exists():
        shutil.copy2(source, cached_jsonl)
    
    # 메타 정보 저장
    meta = {
        "place": place,
        "title": title,
        "title_hash": _get_title_hash(title),
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "source_path": str(jsonl_path),
        "cached_path": str(cached_jsonl),
    }
    
    if extra_meta:
        meta.update(extra_meta)
    
    # 결과 건수 계산
    if cached_jsonl.exists():
        with open(cached_jsonl, "r", encoding="utf-8") as f:
            meta["result_count"] = sum(1 for _ in f)
    
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    
    print(f"[cache] 캐시 저장 완료: {cached_jsonl} ({meta.get('result_count', 0)}건)")
    
    return str(cached_jsonl)


def clear_expired_cache(
    max_age_hours: int = DEFAULT_MAX_AGE_HOURS,
    cache_dir: str = DEFAULT_CACHE_DIR
) -> int:
    """
    만료된 캐시 삭제
    
    Returns:
        삭제된 캐시 수
    """
    cache_path = Path(cache_dir)
    if not cache_path.exists():
        return 0
    
    deleted = 0
    now = datetime.now()
    
    for meta_file in cache_path.glob("*.meta.json"):
        try:
            with open(meta_file, "r", encoding="utf-8") as f:
                meta = json.load(f)
            
            created_at = datetime.fromisoformat(meta.get("created_at", ""))
            age = now - created_at
            
            if age >= timedelta(hours=max_age_hours):
                # 메타 파일과 JSONL 파일 삭제
                jsonl_file = meta_file.with_suffix(".jsonl")
                meta_file.unlink(missing_ok=True)
                if jsonl_file.exists():
                    jsonl_file.unlink()
                deleted += 1
                
        except (json.JSONDecodeError, ValueError, IOError):
            continue
    
    if deleted > 0:
        print(f"[cache] 만료된 캐시 {deleted}개 삭제됨")
    
    return deleted


def list_cached_searches(cache_dir: str = DEFAULT_CACHE_DIR) -> list[Dict[str, Any]]:
    """
    캐시된 검색 목록 반환
    
    Returns:
        캐시 메타 정보 리스트
    """
    cache_path = Path(cache_dir)
    if not cache_path.exists():
        return []
    
    results = []
    now = datetime.now()
    
    for meta_file in sorted(cache_path.glob("*.meta.json"), reverse=True):
        try:
            with open(meta_file, "r", encoding="utf-8") as f:
                meta = json.load(f)
            
            # 경과 시간 계산
            created_at = datetime.fromisoformat(meta.get("created_at", ""))
            age = now - created_at
            meta["age_hours"] = age.total_seconds() / 3600
            meta["is_expired"] = age >= timedelta(hours=DEFAULT_MAX_AGE_HOURS)
            
            results.append(meta)
            
        except (json.JSONDecodeError, ValueError, IOError):
            continue
    
    return results
