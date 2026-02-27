#!/usr/bin/env python3
"""제안서 시맨틱 검색 Slack Bot 진입점 (Socket Mode)."""

from dotenv import load_dotenv

load_dotenv()

from embedding.cache import cache_exists


def main():
    # 임베딩 캐시 확인
    if not cache_exists():
        print("[ProposalSearchBot] 임베딩 캐시가 없습니다!")
        print("[ProposalSearchBot] 먼저 'python scripts/build_embeddings.py'를 실행하세요.")
        return

    # 임베딩 인덱스 미리 로드
    print("[ProposalSearchBot] 벡터 인덱스 로드 중...")
    from search.searcher import _get_index
    _get_index()
    print("[ProposalSearchBot] 벡터 인덱스 로드 완료")

    # Slack 핸들러 등록
    import slack_app.commands  # noqa: F401
    import slack_app.events  # noqa: F401

    from slack_app.bolt_app import start_socket_mode

    print("[ProposalSearchBot] Slack Bot (Socket Mode) 시작...")
    start_socket_mode()


if __name__ == "__main__":
    main()
