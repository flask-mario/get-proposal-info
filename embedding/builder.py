"""메타데이터 행을 검색용 구조화 텍스트로 변환."""

from config.settings import EMBEDDING_FIELDS


def build_text(record: dict) -> str:
    """메타데이터 dict → 임베딩용 텍스트.

    빈 필드는 제외하여 노이즈 방지.
    행당 200~500 토큰, text-multilingual-embedding-002의 2,048 토큰 한도 내.
    """
    parts = []
    for label, column in EMBEDDING_FIELDS.items():
        value = record.get(column, "").strip()
        if value:
            parts.append(f"{label}: {value}")
    return "\n".join(parts)


def build_texts(records: list[dict]) -> list[str]:
    """메타데이터 목록 → 임베딩용 텍스트 목록."""
    return [build_text(r) for r in records]


def build_doc_id(record: dict) -> str:
    """문서 식별자 생성 (파일ID 또는 인덱스 기반)."""
    return record.get("파일ID", "").strip() or record.get("문서ID", "").strip()
