"""Block Kit 메시지 포맷터."""

from config.settings import DISPLAY_FIELDS


def format_search_response(search_result: dict) -> list[dict]:
    """검색 결과를 Slack Block Kit 메시지로 변환.

    Args:
        search_result: searcher.search()의 반환값

    Returns:
        list[dict]: Slack Block Kit blocks
    """
    blocks = []
    query = search_result["query"]
    answer = search_result.get("answer", "")
    results = search_result.get("results", [])
    results_count = search_result.get("results_count", 0)
    response_time = search_result.get("response_time_ms", 0)
    top_score = search_result.get("top_score", 0)

    # 헤더
    blocks.append({
        "type": "header",
        "text": {"type": "plain_text", "text": f"제안서 검색 결과", "emoji": True},
    })

    # 쿼리 정보
    blocks.append({
        "type": "context",
        "elements": [
            {"type": "mrkdwn", "text": f"*검색어:* {query} | *결과:* {results_count}건 | *응답시간:* {response_time}ms"},
        ],
    })

    # 종합 답변
    if answer:
        blocks.append({"type": "divider"})
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*종합 답변*\n{answer}"},
        })

    # 개별 결과
    if results:
        blocks.append({"type": "divider"})
        for r in results:
            meta = r.get("metadata", {})
            relevance = r.get("relevance", "")
            score = r.get("score", 0)
            summary = r.get("summary", "")

            relevance_emoji = {"high": ":large_green_circle:", "medium": ":large_yellow_circle:", "low": ":white_circle:"}.get(relevance, ":white_circle:")

            # 프로젝트 제목
            project = meta.get("프로젝트명", "N/A")
            client_name = meta.get("고객사명", "N/A")
            title = f"{relevance_emoji} *{client_name}* — {project}"

            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": title},
            })

            # 핵심 필드
            fields = []
            for label, col in DISPLAY_FIELDS.items():
                value = meta.get(col, "")
                if value and col not in ("고객사명", "프로젝트명"):
                    fields.append({"type": "mrkdwn", "text": f"*{label}:* {value}"})

            if fields:
                # Slack은 fields를 최대 10개까지 허용
                blocks.append({
                    "type": "section",
                    "fields": fields[:10],
                })

            # 요약
            if summary:
                blocks.append({
                    "type": "context",
                    "elements": [
                        {"type": "mrkdwn", "text": f"_{summary}_"},
                    ],
                })

            # 파일 링크
            file_link = meta.get("파일링크", "")
            if file_link:
                blocks.append({
                    "type": "context",
                    "elements": [
                        {"type": "mrkdwn", "text": f":link: <{file_link}|원본 파일 열기>"},
                    ],
                })

            blocks.append({"type": "divider"})
    else:
        blocks.append({"type": "divider"})
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": ":mag: 관련 제안서를 찾지 못했습니다. 다른 키워드로 검색해보세요."},
        })

    return blocks


def format_error_message(error_msg: str) -> list[dict]:
    """에러 메시지를 Block Kit으로 변환."""
    return [
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f":warning: *오류가 발생했습니다*\n{error_msg}"},
        },
    ]


def format_loading_message() -> list[dict]:
    """로딩 메시지."""
    return [
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": ":hourglass_flowing_sand: 검색 중입니다... 잠시만 기다려주세요."},
        },
    ]


def format_help_message() -> list[dict]:
    """도움말 메시지."""
    return [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "제안서 검색 도움말"},
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    "*사용 방법*\n"
                    "• `/proposal-search <검색어>` — 슬래시 커맨드로 검색\n"
                    "• `@제안서검색봇 <검색어>` — 멘션으로 검색\n"
                    "• DM으로 검색어 입력 — 1:1 대화로 검색\n\n"
                    "*검색 예시*\n"
                    "• `AWS 기반 금융 프로젝트`\n"
                    "• `쿠버네티스 마이그레이션 사례`\n"
                    "• `공공기관 클라우드 전환`\n"
                    "• `AI 데이터 분석 플랫폼`\n\n"
                    "*팁*\n"
                    "• 자연어로 질문하면 더 정확한 결과를 얻을 수 있습니다\n"
                    "• 클라우드, 도메인, 기술 키워드를 조합하면 좋습니다"
                ),
            },
        },
    ]
