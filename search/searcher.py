"""검색 오케스트레이터 — 전체 검색 파이프라인 조합."""

import time

from embedding.cache import cache_exists, load_embeddings
from embedding.embedder import embed_query
from embedding.index import VectorIndex
from search.query_processor import expand_query
from search.dedup import dedup_candidates
from search.reranker import rerank
from config.settings import SEARCH_TOP_K, DEDUP_TOP_K, SIMILARITY_THRESHOLD

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

    # 1. 쿼리 동의어 확장
    query_expanded = expand_query(query)

    # 2. 쿼리 임베딩
    query_vector = embed_query(query_expanded)

    # 3. 벡터 검색 (넉넉하게 top-30)
    candidates = index.search(
        query_vector, top_k=SEARCH_TOP_K, threshold=SIMILARITY_THRESHOLD
    )

    # 4. 후보에 원본 메타데이터 매핑
    for c in candidates:
        idx = c["index"]
        if idx < len(records):
            c["metadata"] = records[idx]

    # 5. 중복 제거 (유사 프로젝트명 통합, 최신 우선 → top-10)
    candidates = dedup_candidates(candidates, max_results=DEDUP_TOP_K)

    # 6. LLM 리랭킹 + 요약
    reranked = rerank(query, candidates)

    # 리랭킹 결과에 원본 후보 데이터 매핑
    enriched_results = []
    for r in reranked.get("results", []):
        orig_idx = r.get("index", 0)
        if orig_idx < len(candidates):
            candidate = candidates[orig_idx]
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
