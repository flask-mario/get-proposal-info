"""01.META_DATA 시트 전체 로드 + 로컬 캐시."""

import json
import os
import time

from config.settings import CACHE_DIR, METADATA_COLUMNS, SHEET_METADATA
from sheets.client import get_sheet


def load_metadata(use_cache=True, cache_ttl=3600):
    """메타데이터 전체 로드. 캐시가 유효하면 캐시에서 로드.

    Args:
        use_cache: 로컬 캐시 사용 여부
        cache_ttl: 캐시 유효 시간 (초, 기본 1시간)

    Returns:
        list[dict]: 각 행이 dict인 메타데이터 목록
    """
    cache_path = os.path.join(CACHE_DIR, "metadata.json")

    if use_cache and os.path.exists(cache_path):
        age = time.time() - os.path.getmtime(cache_path)
        if age < cache_ttl:
            print(f"[Loader] 캐시에서 로드 (age: {age:.0f}s)")
            with open(cache_path, "r", encoding="utf-8") as f:
                return json.load(f)

    print(f"[Loader] Google Sheets에서 '{SHEET_METADATA}' 로드 중...")
    ws = get_sheet(SHEET_METADATA)
    rows = ws.get_all_values()

    if not rows:
        print("[Loader] 시트가 비어 있습니다.")
        return []

    headers = rows[0]
    records = []
    for row in rows[1:]:
        record = {}
        for i, header in enumerate(headers):
            record[header] = row[i] if i < len(row) else ""
        records.append(record)

    print(f"[Loader] {len(records)}건 로드 완료")

    # 캐시 저장
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    print(f"[Loader] 캐시 저장: {cache_path}")

    return records
