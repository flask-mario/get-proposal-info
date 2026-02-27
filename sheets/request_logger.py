"""21.requests 탭 비동기 로깅."""

import threading
import uuid
from datetime import datetime, timezone, timedelta

from config.settings import REQUEST_LOG_COLUMNS, SHEET_REQUESTS

KST = timezone(timedelta(hours=9))


def log_request_async(**kwargs):
    """비동기로 검색 요청을 21.requests 시트에 로깅.

    kwargs:
        slack_user_id, slack_user_name, slack_channel_id,
        query_text, query_expanded, results_count,
        top_score, response_time_ms, result_doc_ids, feedback, error
    """
    thread = threading.Thread(target=_log_request, kwargs=kwargs, daemon=True)
    thread.start()


def _log_request(**kwargs):
    """실제 로깅 로직."""
    try:
        from sheets.client import get_sheet

        ws = get_sheet(SHEET_REQUESTS)

        request_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now(KST).isoformat()
        result_doc_ids = kwargs.get("result_doc_ids", [])
        if isinstance(result_doc_ids, list):
            result_doc_ids = ",".join(str(d) for d in result_doc_ids)

        row = [
            request_id,
            timestamp,
            kwargs.get("slack_user_id", ""),
            kwargs.get("slack_user_name", ""),
            kwargs.get("slack_channel_id", ""),
            kwargs.get("query_text", ""),
            kwargs.get("query_expanded", ""),
            str(kwargs.get("results_count", 0)),
            f"{kwargs.get('top_score', 0):.4f}",
            str(kwargs.get("response_time_ms", 0)),
            result_doc_ids,
            kwargs.get("feedback", ""),
            kwargs.get("error", ""),
        ]

        ws.append_row(row, value_input_option="USER_ENTERED")
    except Exception as e:
        print(f"[Logger] 로깅 실패: {e}")
