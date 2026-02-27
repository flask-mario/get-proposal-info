#!/usr/bin/env python3
"""21.requests 시트 헤더 초기화 스크립트."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from config.settings import REQUEST_LOG_COLUMNS, SHEET_REQUESTS
from sheets.client import get_spreadsheet


def main():
    ss = get_spreadsheet()

    # 시트 존재 여부 확인
    existing = [ws.title for ws in ss.worksheets()]
    if SHEET_REQUESTS in existing:
        print(f"[Setup] '{SHEET_REQUESTS}' 시트가 이미 존재합니다.")
        ws = ss.worksheet(SHEET_REQUESTS)
        headers = ws.row_values(1)
        if headers:
            print(f"[Setup] 기존 헤더: {headers}")
            print("[Setup] 기존 시트를 유지합니다.")
            return
    else:
        print(f"[Setup] '{SHEET_REQUESTS}' 시트 생성 중...")
        ws = ss.add_worksheet(title=SHEET_REQUESTS, rows=1000, cols=len(REQUEST_LOG_COLUMNS))

    # 헤더 작성
    ws.update([REQUEST_LOG_COLUMNS], "A1")

    # 헤더 서식 (볼드 + 고정)
    ws.format("A1:M1", {
        "textFormat": {"bold": True},
        "backgroundColor": {"red": 0.9, "green": 0.9, "blue": 0.9},
    })
    ws.freeze(rows=1)

    print(f"[Setup] '{SHEET_REQUESTS}' 시트 초기화 완료")
    print(f"[Setup] 헤더: {REQUEST_LOG_COLUMNS}")


if __name__ == "__main__":
    main()
