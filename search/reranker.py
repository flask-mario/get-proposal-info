"""Gemini 리랭커 — 관련도 판정 + 요약 생성 (할루시네이션 방지)."""

import json

from google import genai

from config.settings import GCP_PROJECT_ID, LLM_LOCATION, LLM_MODEL, RERANK_TOP_N

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = genai.Client(
            vertexai=True,
            project=GCP_PROJECT_ID,
            location=LLM_LOCATION,
        )
    return _client


RERANK_PROMPT = """\
당신은 제안서 검색 결과를 평가하는 전문가입니다.

## 엄격한 규칙
1. 아래 제공된 검색 결과 데이터만 사용하여 답변하세요.
2. 데이터에 없는 내용을 추측하거나 만들어내지 마세요.
3. 인터넷 지식이나 학습 데이터를 사용하지 마세요.
4. 관련 없는 결과는 제외하세요.

## 사용자 질의
{query}

## 검색 결과 (유사도 순)
{candidates}

## 지시사항
위 검색 결과 중에서 사용자 질의와 관련된 결과만 선별하세요.

다음 JSON 형식으로 응답하세요:
```json
{{
  "results": [
    {{
      "rank": 1,
      "index": <결과 번호 (0부터 시작)>,
      "doc_id": "<해당 결과의 doc_id>",
      "relevance": "high|medium|low",
      "summary": "<데이터에 근거한 1-2문장 요약>"
    }}
  ],
  "answer": "<질의에 대한 종합 답변 (2-3문장, 데이터만 근거)>"
}}
```

관련 결과가 없으면:
```json
{{
  "results": [],
  "answer": "관련 제안서를 찾지 못했습니다."
}}
```
"""


def rerank(query: str, candidates: list[dict]) -> dict:
    """Gemini로 검색 결과를 리랭킹하고 요약 생성.

    Args:
        query: 사용자 질의
        candidates: 벡터 검색 결과 [{doc_id, text, score, rank, index}, ...]

    Returns:
        dict: {"results": [...], "answer": "..."}
    """
    if not candidates:
        return {"results": [], "answer": "관련 제안서를 찾지 못했습니다."}

    # 후보 텍스트 구성
    candidate_texts = []
    for i, c in enumerate(candidates):
        candidate_texts.append(
            f"[결과 {i}] (doc_id: {c['doc_id']}, 유사도: {c['score']:.3f})\n{c['text']}"
        )
    candidates_str = "\n\n---\n\n".join(candidate_texts)

    prompt = RERANK_PROMPT.format(query=query, candidates=candidates_str)

    client = _get_client()
    response = client.models.generate_content(
        model=LLM_MODEL,
        contents=prompt,
    )

    # JSON 파싱
    text = response.text.strip()
    # 마크다운 코드 블록 제거
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:])
        if text.endswith("```"):
            text = text[:-3].strip()

    try:
        result = json.loads(text)
    except json.JSONDecodeError:
        # 파싱 실패 시 원본 결과 그대로 반환
        print(f"[Reranker] JSON 파싱 실패, 원본 결과 사용")
        return {
            "results": [
                {
                    "rank": i + 1,
                    "index": i,
                    "doc_id": c["doc_id"],
                    "relevance": "medium",
                    "summary": c["text"][:200],
                }
                for i, c in enumerate(candidates[:RERANK_TOP_N])
            ],
            "answer": "검색 결과를 요약하는 데 실패했습니다. 아래 결과를 직접 확인해주세요.",
        }

    # 결과 수 제한
    if "results" in result:
        result["results"] = result["results"][:RERANK_TOP_N]

    return result
