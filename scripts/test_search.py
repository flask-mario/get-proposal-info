#!/usr/bin/env python3
"""CLI 검색 테스트 도구.

사용법:
    python scripts/test_search.py "AWS 기반 금융 프로젝트"
    python scripts/test_search.py "쿠버네티스 마이그레이션"
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from search.searcher import search


def main():
    if len(sys.argv) < 2:
        print("사용법: python scripts/test_search.py <검색 쿼리>")
        print('예시: python scripts/test_search.py "AWS 기반 금융 프로젝트"')
        sys.exit(1)

    query = " ".join(sys.argv[1:])
    print(f"\n{'=' * 60}")
    print(f"[검색] 쿼리: {query}")
    print(f"{'=' * 60}")

    result = search(query)

    print(f"\n[결과] 확장 쿼리: {result['query_expanded']}")
    print(f"[결과] 결과 수: {result['results_count']}")
    print(f"[결과] 최고 유사도: {result['top_score']:.4f}")
    print(f"[결과] 응답시간: {result['response_time_ms']}ms")

    print(f"\n{'=' * 60}")
    print(f"[종합 답변]")
    print(result["answer"])

    for r in result["results"]:
        print(f"\n{'-' * 40}")
        print(f"[#{r['rank']}] 관련도: {r.get('relevance', 'N/A')} | 유사도: {r.get('score', 0):.4f}")
        meta = r.get("metadata", {})
        if meta:
            print(f"  고객사: {meta.get('고객사명', 'N/A')}")
            print(f"  프로젝트: {meta.get('프로젝트명', 'N/A')}")
            print(f"  서비스유형: {meta.get('서비스유형', 'N/A')}")
            print(f"  도메인: {meta.get('도메인', 'N/A')}")
            print(f"  기술스택: {meta.get('주요기술스택', 'N/A')}")
            print(f"  클라우드: {meta.get('클라우드플랫폼', 'N/A')}")
        print(f"  요약: {r.get('summary', 'N/A')}")


if __name__ == "__main__":
    main()
