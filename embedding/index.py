"""numpy 벡터 인덱스 (cosine similarity)."""

import numpy as np


class VectorIndex:
    """인메모리 벡터 인덱스. cosine similarity 기반 검색."""

    def __init__(self, vectors: np.ndarray, doc_ids: list[str], texts: list[str]):
        self.vectors = vectors
        self.doc_ids = doc_ids
        self.texts = texts
        # L2 정규화 (cosine similarity를 dot product로 계산)
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1, norms)
        self.normalized = vectors / norms

    def search(self, query_vector: np.ndarray, top_k: int = 10, threshold: float = 0.0):
        """코사인 유사도 기반 검색.

        Args:
            query_vector: 쿼리 임베딩 벡터 (768,)
            top_k: 반환할 최대 결과 수
            threshold: 최소 유사도 임계치

        Returns:
            list[dict]: [{"doc_id", "text", "score", "rank"}, ...]
        """
        # 쿼리 벡터 정규화
        q_norm = np.linalg.norm(query_vector)
        if q_norm == 0:
            return []
        q_normalized = query_vector / q_norm

        # dot product = cosine similarity (정규화된 벡터)
        scores = self.normalized @ q_normalized

        # top-k 인덱스
        top_indices = np.argsort(scores)[::-1][:top_k]

        results = []
        for rank, idx in enumerate(top_indices):
            score = float(scores[idx])
            if score < threshold:
                break
            results.append({
                "doc_id": self.doc_ids[idx],
                "text": self.texts[idx],
                "score": score,
                "rank": rank + 1,
                "index": int(idx),
            })

        return results
