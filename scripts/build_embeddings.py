#!/usr/bin/env python3
"""임베딩 전체 빌드 스크립트 (최초 1회 실행)."""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sheets.loader import load_metadata
from embedding.builder import build_texts, build_doc_id
from embedding.embedder import embed_texts
from embedding.cache import save_embeddings


def main():
    start = time.time()

    # 1. 메타데이터 로드
    print("=" * 60)
    print("[Build] 메타데이터 로드 중...")
    records = load_metadata(use_cache=True)
    if not records:
        print("[Build] 메타데이터가 없습니다. 종료.")
        return

    print(f"[Build] {len(records)}건 로드 완료")

    # 2. 텍스트 변환
    print("=" * 60)
    print("[Build] 임베딩용 텍스트 변환 중...")
    texts = build_texts(records)
    doc_ids = [build_doc_id(r) or f"row_{i}" for i, r in enumerate(records)]

    # 빈 텍스트 필터링
    valid = [(did, txt) for did, txt in zip(doc_ids, texts) if txt.strip()]
    if not valid:
        print("[Build] 유효한 텍스트가 없습니다. 종료.")
        return

    doc_ids_valid, texts_valid = zip(*valid)
    doc_ids_valid = list(doc_ids_valid)
    texts_valid = list(texts_valid)
    print(f"[Build] {len(texts_valid)}건 유효 (원본 {len(records)}건 중)")

    # 샘플 출력
    print("-" * 40)
    print("[Build] 샘플 텍스트 (첫 번째):")
    print(texts_valid[0][:500])
    print("-" * 40)

    # 3. 임베딩 생성
    print("=" * 60)
    print("[Build] Vertex AI 임베딩 생성 중...")
    vectors = embed_texts(texts_valid)
    print(f"[Build] 임베딩 완료: shape={vectors.shape}")

    # 4. 캐시 저장
    print("=" * 60)
    save_embeddings(vectors, doc_ids_valid, texts_valid)

    elapsed = time.time() - start
    print("=" * 60)
    print(f"[Build] 전체 완료! {elapsed:.1f}초 소요")
    print(f"[Build] 벡터 수: {len(doc_ids_valid)}, 차원: {vectors.shape[1]}")
    size_mb = vectors.nbytes / 1024 / 1024
    print(f"[Build] 메모리: {size_mb:.1f}MB")


if __name__ == "__main__":
    main()
