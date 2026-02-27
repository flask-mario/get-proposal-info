"""임베딩 로컬 캐시 관리 (npy + json)."""

import json
import os

import numpy as np

from config.settings import EMBEDDINGS_DIR


def save_embeddings(vectors: np.ndarray, doc_ids: list[str], texts: list[str]):
    """임베딩 벡터 + 메타데이터를 로컬에 저장."""
    os.makedirs(EMBEDDINGS_DIR, exist_ok=True)

    npy_path = os.path.join(EMBEDDINGS_DIR, "vectors.npy")
    meta_path = os.path.join(EMBEDDINGS_DIR, "metadata.json")

    np.save(npy_path, vectors)

    metadata = {
        "doc_ids": doc_ids,
        "texts": texts,
        "count": len(doc_ids),
        "dimension": int(vectors.shape[1]) if vectors.ndim > 1 else 0,
    }
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    print(f"[Cache] 저장 완료: {len(doc_ids)}건, {npy_path}")


def load_embeddings():
    """로컬 캐시에서 임베딩 로드.

    Returns:
        tuple: (vectors: np.ndarray, doc_ids: list[str], texts: list[str])
               캐시가 없으면 (None, None, None)
    """
    npy_path = os.path.join(EMBEDDINGS_DIR, "vectors.npy")
    meta_path = os.path.join(EMBEDDINGS_DIR, "metadata.json")

    if not os.path.exists(npy_path) or not os.path.exists(meta_path):
        return None, None, None

    vectors = np.load(npy_path)
    with open(meta_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    print(f"[Cache] 로드 완료: {metadata['count']}건, {metadata['dimension']}차원")
    return vectors, metadata["doc_ids"], metadata["texts"]


def cache_exists():
    """캐시 파일이 존재하는지 확인."""
    npy_path = os.path.join(EMBEDDINGS_DIR, "vectors.npy")
    meta_path = os.path.join(EMBEDDINGS_DIR, "metadata.json")
    return os.path.exists(npy_path) and os.path.exists(meta_path)
