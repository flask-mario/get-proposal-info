"""슬래시 커맨드 핸들러: /proposal-search"""

import traceback

from slack_app.bolt_app import app
from slack_app.messages import (
    format_error_message,
    format_help_message,
    format_search_response,
)
from search.searcher import search
from sheets.request_logger import log_request_async


@app.command("/proposal-search")
def handle_proposal_search(ack, body, say, client):
    """제안서 시맨틱 검색 슬래시 커맨드."""
    ack()

    query = body.get("text", "").strip()
    user_id = body.get("user_id", "")
    channel_id = body.get("channel_id", "")

    # 빈 쿼리 또는 help
    if not query or query.lower() in ("help", "도움말"):
        say(blocks=format_help_message(), text="제안서 검색 도움말")
        return

    # 사용자 이름, 채널 이름 조회
    user_name = _get_user_name(client, user_id)
    channel_name = _get_channel_name(client, channel_id)

    try:
        result = search(query)
        blocks = format_search_response(result)
        say(blocks=blocks, text=f"제안서 검색 결과: {query}")

        # 비동기 로깅
        log_request_async(
            slack_user_id=user_id,
            slack_user_name=user_name,
            slack_channel_id=channel_name,
            query_text=query,
            query_expanded=result.get("query_expanded", ""),
            results_count=result.get("results_count", 0),
            top_score=result.get("top_score", 0),
            response_time_ms=result.get("response_time_ms", 0),
            result_doc_ids=[r.get("doc_id", "") for r in result.get("results", [])],
        )
    except Exception as e:
        traceback.print_exc()
        say(
            blocks=format_error_message(str(e)),
            text=f"검색 오류: {e}",
        )
        log_request_async(
            slack_user_id=user_id,
            slack_user_name=user_name,
            slack_channel_id=channel_name,
            query_text=query,
            error=str(e),
        )


def _get_user_name(client, user_id: str) -> str:
    """Slack 사용자 표시 이름 조회."""
    try:
        info = client.users_info(user=user_id)
        profile = info["user"]["profile"]
        return profile.get("display_name") or profile.get("real_name") or user_id
    except Exception:
        return user_id


def _get_channel_name(client, channel_id: str) -> str:
    """Slack 채널 표시 이름 조회."""
    try:
        info = client.conversations_info(channel=channel_id)
        return info["channel"].get("name") or channel_id
    except Exception:
        return channel_id
