"""검색 결과 중복 제거 — 유사 프로젝트명 통합, 최신 결과 우선."""

import re
from datetime import datetime

from config.settings import DEDUP_NAME_THRESHOLD

# 프로젝트명에서 제거할 접미사/노이즈 단어
_NOISE_SUFFIXES = re.compile(r"(사업|프로젝트|제안|용역|과업|건|의\s건)$")
_NOISE_WORDS = {"을", "를", "위한", "에", "대한", "및", "관련", "기반", "수행", "선정"}

# 영한 정규화 맵
_EN_KR_MAP = {
    "cloud": "클라우드",
    "migration": "마이그레이션",
    "platform": "플랫폼",
    "system": "시스템",
    "service": "서비스",
    "infra": "인프라",
    "infrastructure": "인프라",
    "security": "보안",
    "network": "네트워크",
    "database": "데이터베이스",
    "server": "서버",
    "container": "컨테이너",
    "monitoring": "모니터링",
    "consulting": "컨설팅",
    "managed": "매니지드",
    "hybrid": "하이브리드",
    "digital": "디지털",
    "solution": "솔루션",
    "operation": "운영",
    "construction": "구축",
    "development": "개발",
}


def _normalize(text: str) -> str:
    """프로젝트명 정규화: 공백·특수문자 제거, 소문자, 영한 통일."""
    text = re.sub(r"[^\w가-힣]", " ", text.lower())
    # 영한 정규화
    words = text.split()
    normalized = []
    for w in words:
        mapped = _EN_KR_MAP.get(w, w)
        # 접미사 제거 (예: 구축사업 → 구축)
        mapped = _NOISE_SUFFIXES.sub("", mapped)
        if mapped and mapped not in _NOISE_WORDS:
            normalized.append(mapped)
    return " ".join(normalized)


def _tokenize(text: str) -> set[str]:
    """정규화된 텍스트를 토큰 집합으로 변환."""
    normalized = _normalize(text)
    return set(normalized.split())


def _similarity(a: set, b: set) -> float:
    """Jaccard + 포함도(containment) 혼합 유사도.

    max(Jaccard, min-containment) 사용하여
    한쪽이 다른쪽의 부분집합인 경우도 잘 감지.
    """
    if not a or not b:
        return 0.0
    intersection = len(a & b)
    jaccard = intersection / len(a | b)
    containment = intersection / min(len(a), len(b))
    return max(jaccard, containment)


def _parse_date(record: dict) -> datetime:
    """레코드에서 날짜 추출. 등록일시 > 작성일자 순으로 시도."""
    for field in ("등록일시", "작성일자"):
        raw = record.get(field, "").strip()
        if not raw or raw == "-":
            continue
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y. %m. %d", "%Y. %m. %d."):
            try:
                return datetime.strptime(raw, fmt)
            except ValueError:
                continue
    return datetime.min


def _is_dup(a_meta: dict, b_meta: dict) -> bool:
    """두 레코드가 중복인지 판정."""
    a_client = _normalize(a_meta.get("고객사명", ""))
    b_client = _normalize(b_meta.get("고객사명", ""))
    a_tokens = _tokenize(a_meta.get("프로젝트명", ""))
    b_tokens = _tokenize(b_meta.get("프로젝트명", ""))

    sim = _similarity(a_tokens, b_tokens)
    same_client = (a_client == b_client) and a_client != ""
    return (same_client and sim >= DEDUP_NAME_THRESHOLD) or (sim >= 0.85)


def dedup_candidates(candidates: list[dict], max_results: int = 10) -> list[dict]:
    """유사 프로젝트명 중복 제거. 같은 프로젝트는 최신 결과만 유지.

    판정 기준:
    1. 동일 고객사 + 프로젝트명 유사도 >= DEDUP_NAME_THRESHOLD → 중복
    2. 고객사 무관 + 프로젝트명 유사도 >= 0.85 → 중복 (거의 동일한 이름)
    3. 중복 그룹 내에서 가장 최신(등록일시/작성일자) 결과를 유지

    Args:
        candidates: 메타데이터가 매핑된 검색 후보 목록
        max_results: 반환할 최대 결과 수

    Returns:
        중복 제거된 후보 목록
    """
    if not candidates:
        return []

    # Pass 1: 후보를 순회하며 중복 그룹화
    kept = []

    for candidate in candidates:
        meta = candidate.get("metadata", {})
        cand_date = _parse_date(meta)

        is_dup = False
        for i, existing in enumerate(kept):
            ex_meta = existing.get("metadata", {})
            if _is_dup(meta, ex_meta):
                ex_date = _parse_date(ex_meta)
                if cand_date > ex_date:
                    kept[i] = candidate
                is_dup = True
                break

        if not is_dup:
            kept.append(candidate)

    # Pass 2: 교체로 인해 생긴 kept 내부 중복 재정리
    changed = True
    while changed:
        changed = False
        new_kept = []
        for item in kept:
            meta = item.get("metadata", {})
            item_date = _parse_date(meta)
            merged = False
            for j, existing in enumerate(new_kept):
                ex_meta = existing.get("metadata", {})
                if _is_dup(meta, ex_meta):
                    ex_date = _parse_date(ex_meta)
                    if item_date > ex_date:
                        new_kept[j] = item
                    merged = True
                    break
            if not merged:
                new_kept.append(item)
        if len(new_kept) < len(kept):
            changed = True
        kept = new_kept

    return kept[:max_results]
