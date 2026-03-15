"""검색 오케스트레이터 — 전체 검색 파이프라인 조합."""

import time

from embedding.cache import cache_exists, load_embeddings
from embedding.embedder import embed_query
from embedding.index import VectorIndex
from search.query_processor import expand_query, detect_domain_filter, detect_list_mode
from search.dedup import dedup_candidates
from search.reranker import rerank
from config.settings import SEARCH_TOP_K, DEDUP_TOP_K, SIMILARITY_THRESHOLD, LIST_MODE_MAX_RESULTS

_index = None
_records = None


def _get_index():
    """벡터 인덱스 싱글턴 로드."""
    global _index
    if _index is None:
        if not cache_exists():
            raise RuntimeError(
                "임베딩 캐시가 없습니다. 먼저 'python scripts/build_embeddings.py'를 실행하세요."
            )
        vectors, doc_ids, texts = load_embeddings()
        _index = VectorIndex(vectors, doc_ids, texts)
    return _index


def get_records():
    """메타데이터 레코드 로드 (검색 결과에 원본 데이터 매핑용)."""
    global _records
    if _records is None:
        from sheets.loader import load_metadata
        _records = load_metadata(use_cache=True)
    return _records


def search(query: str) -> dict:
    """시맨틱 검색 파이프라인.

    흐름: 쿼리 확장 → 임베딩 → 벡터검색(top-30) → 중복제거(top-10) → 리랭킹(top-5)

    Returns:
        dict: {
            "query": str,
            "query_expanded": str,
            "results": list[dict],
            "answer": str,
            "results_count": int,
            "top_score": float,
            "response_time_ms": int,
        }
    """
    start = time.time()
    index = _get_index()
    records = get_records()

    # 1. 쿼리 동의어 확장 + 목록 모드 감지
    query_expanded = expand_query(query)
    is_list_mode = detect_list_mode(query)

    # 2. 쿼리 임베딩
    query_vector = embed_query(query_expanded)

    # 3. 벡터 검색 (넉넉하게 top-30)
    candidates = index.search(
        query_vector, top_k=SEARCH_TOP_K, threshold=SIMILARITY_THRESHOLD
    )

    # 3.5 도메인 필터 보충 검색
    domain_keywords = detect_domain_filter(query)
    if domain_keywords:
        index_size = len(index.doc_ids)
        matching_indices = [
            i for i, r in enumerate(records)
            if i < index_size and any(kw in r.get("도메인", "") for kw in domain_keywords)
        ]
        if matching_indices:
            filtered_results = index.search_by_indices(
                query_vector, matching_indices,
                top_k=SEARCH_TOP_K, threshold=SIMILARITY_THRESHOLD,
            )
            existing_ids = {c["doc_id"] for c in candidates}
            for fr in filtered_results:
                if fr["doc_id"] not in existing_ids:
                    candidates.append(fr)
            candidates.sort(key=lambda x: x["score"], reverse=True)

    # 4. 후보에 원본 메타데이터 매핑
    for c in candidates:
        idx = c["index"]
        if idx < len(records):
            c["metadata"] = records[idx]

    # 4.5 고객사명·프로젝트명이 둘 다 비어있는 후보 제거
    candidates = [
        c for c in candidates
        if c.get("metadata", {}).get("고객사명") or c.get("metadata", {}).get("프로젝트명")
    ]

    if is_list_mode:
        # 목록 모드: 리랭커 건너뛰기 → dedup 후 compact 목록 반환
        candidates = dedup_candidates(candidates, max_results=LIST_MODE_MAX_RESULTS)
        elapsed_ms = int((time.time() - start) * 1000)
        top_score = candidates[0]["score"] if candidates else 0.0

        return {
            "query": query,
            "query_expanded": query_expanded,
            "results": candidates,
            "answer": "",
            "results_count": len(candidates),
            "top_score": top_score,
            "response_time_ms": elapsed_ms,
            "is_list_mode": True,
        }

    # 5. 중복 제거 (유사 프로젝트명 통합, 최신 우선 → top-10)
    candidates = dedup_candidates(candidates, max_results=DEDUP_TOP_K)

    # 6. LLM 리랭킹 + 요약
    reranked = rerank(query, candidates)

    # 리랭킹 결과에 원본 후보 데이터 매핑 (doc_id 기반, fallback: 0-indexed)
    candidates_by_doc_id = {c["doc_id"]: c for c in candidates}

    enriched_results = []
    for r in reranked.get("results", []):
        # 1차: doc_id로 매핑
        candidate = candidates_by_doc_id.get(r.get("doc_id"))
        # 2차 fallback: index로 매핑
        if candidate is None:
            orig_idx = r.get("index", 0)
            if isinstance(orig_idx, int) and 0 <= orig_idx < len(candidates):
                candidate = candidates[orig_idx]
        if candidate is not None:
            enriched_results.append({
                **r,
                "doc_id": candidate["doc_id"],
                "score": candidate["score"],
                "metadata": candidate.get("metadata", {}),
            })

    elapsed_ms = int((time.time() - start) * 1000)
    top_score = candidates[0]["score"] if candidates else 0.0

    return {
        "query": query,
        "query_expanded": query_expanded,
        "results": enriched_results,
        "answer": reranked.get("answer", ""),
        "results_count": len(enriched_results),
        "top_score": top_score,
        "response_time_ms": elapsed_ms,
    }
