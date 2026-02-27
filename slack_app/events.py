"""이벤트 핸들러: @봇 멘션 + DM."""

import re
import traceback

from slack_app.bolt_app import app
from slack_app.messages import (
    format_error_message,
    format_help_message,
    format_search_response,
)
from search.searcher import search
from sheets.request_logger import log_request_async


@app.event("app_mention")
def handle_mention(event, say, client):
    """@봇 멘션 이벤트 핸들러."""
    text = event.get("text", "")
    user_id = event.get("user", "")
    channel_id = event.get("channel", "")

    # 멘션 제거하여 순수 쿼리 추출
    query = re.sub(r"<@[A-Z0-9]+>", "", text).strip()

    if not query or query.lower() in ("help", "도움말"):
        say(blocks=format_help_message(), text="제안서 검색 도움말")
        return

    _do_search(query, user_id, channel_id, say, client)


@app.event("message")
def handle_dm(event, say, client):
    """DM 메시지 핸들러."""
    # DM만 처리 (channel_type == "im")
    if event.get("channel_type") != "im":
        return
    # 봇 자신의 메시지 무시
    if event.get("bot_id"):
        return

    query = event.get("text", "").strip()
    user_id = event.get("user", "")
    channel_id = event.get("channel", "")

    if not query or query.lower() in ("help", "도움말"):
        say(blocks=format_help_message(), text="제안서 검색 도움말")
        return

    _do_search(query, user_id, channel_id, say, client)


def _do_search(query: str, user_id: str, channel_id: str, say, client):
    """공통 검색 실행 로직."""
    user_name = _get_user_name(client, user_id)
    channel_name = _get_channel_name(client, channel_id)

    try:
        result = search(query)
        blocks = format_search_response(result)
        say(blocks=blocks, text=f"제안서 검색 결과: {query}")

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
