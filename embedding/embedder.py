"""Vertex AI Embedding API 호출."""

import time

import numpy as np
from google import genai

from config.settings import (
    EMBEDDING_BATCH_SIZE,
    EMBEDDING_MODEL,
    GCP_LOCATION,
    GCP_PROJECT_ID,
)

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = genai.Client(
            vertexai=True,
            project=GCP_PROJECT_ID,
            location=GCP_LOCATION,
        )
    return _client


def _embed_batch_with_retry(client, batch, max_retries=3):
    """배치 임베딩 + 재시도 로직."""
    for attempt in range(max_retries):
        try:
            response = client.models.embed_content(
                model=EMBEDDING_MODEL,
                contents=batch,
            )
            return [emb.values for emb in response.embeddings]
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                wait = 2 ** attempt * 5
                print(f"[Embedder] Rate limit, {wait}초 대기 후 재시도 ({attempt + 1}/{max_retries})...")
                time.sleep(wait)
            elif "INVALID_ARGUMENT" in error_msg and "token count" in error_msg:
                # 배치가 너무 큼 → 절반으로 분할
                if len(batch) <= 1:
                    raise
                mid = len(batch) // 2
                print(f"[Embedder] 토큰 초과, 배치 분할 ({len(batch)} → {mid} + {len(batch) - mid})...")
                left = _embed_batch_with_retry(client, batch[:mid], max_retries)
                right = _embed_batch_with_retry(client, batch[mid:], max_retries)
                return left + right
            else:
                raise
    raise RuntimeError(f"임베딩 실패 (최대 재시도 {max_retries}회 초과)")


def embed_texts(texts: list[str]) -> np.ndarray:
    """텍스트 목록을 임베딩 벡터로 변환.

    Returns:
        np.ndarray: shape (len(texts), 768)
    """
    client = _get_client()
    all_embeddings = []
    total_batches = (len(texts) + EMBEDDING_BATCH_SIZE - 1) // EMBEDDING_BATCH_SIZE

    for i in range(0, len(texts), EMBEDDING_BATCH_SIZE):
        batch = texts[i : i + EMBEDDING_BATCH_SIZE]
        batch_num = i // EMBEDDING_BATCH_SIZE + 1
        print(f"[Embedder] 배치 {batch_num}/{total_batches}: {len(batch)}건 임베딩 중...")
        embeddings = _embed_batch_with_retry(client, batch)
        all_embeddings.extend(embeddings)

    return np.array(all_embeddings, dtype=np.float32)


def embed_query(query: str) -> np.ndarray:
    """단일 쿼리를 임베딩 벡터로 변환.

    Returns:
        np.ndarray: shape (768,)
    """
    client = _get_client()
    response = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=[query],
    )
    return np.array(response.embeddings[0].values, dtype=np.float32)
