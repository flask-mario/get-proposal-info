# 제안서 시맨틱 검색 Slack Bot

## 프로젝트 개요
3,519건 제안서 메타데이터(Google Spreadsheet)를 시맨틱 검색하는 Slack Bot.
Vertex AI Embeddings + Gemini LLM 기반.

## 파일 네이밍 컨벤션
- 진입점, 스크립트 등 실행 파일은 **애플리케이션 목적이 드러나는 이름** 사용 (예: `proposal_search_bot.py`, `build_embeddings.py`)
- `app.py`, `main.py`, `server.py` 같은 **범용적/모호한 이름 사용 금지**
- 모듈 파일은 해당 모듈의 **역할을 명확히 표현** (예: `query_processor.py`, `request_logger.py`)
- snake_case 사용, 약어보다 명확한 단어 선호

## 기술 스택
- Python 3.13, slack_bolt (Socket Mode)
- gspread + google-auth (Google Sheets)
- google-genai (Vertex AI Embedding + Gemini LLM)
- numpy (벡터 연산)

## 아키텍처
```
Slack → bolt_app → QueryProcessor → Vertex AI Embedding
  → VectorIndex (numpy cosine similarity)
    → Gemini Reranker → Block Kit 응답 → 21.requests 로깅
```

## 주요 모듈
- `config/settings.py` — 환경변수, 시트명, 모델설정, 임계치
- `sheets/client.py` — gspread 싱글턴 (25.vrb 패턴 동일)
- `sheets/loader.py` — 01.META_DATA 전체 로드 + 로컬 캐시
- `sheets/request_logger.py` — 21.requests 탭 비동기 로깅
- `embedding/builder.py` — 메타데이터 → 검색용 텍스트 변환
- `embedding/embedder.py` — Vertex AI Embedding API 호출
- `embedding/cache.py` — 임베딩 로컬 캐시 (npy + json)
- `embedding/index.py` — numpy 벡터 인덱스 (cosine similarity)
- `search/query_processor.py` — 쿼리 동의어 확장
- `search/reranker.py` — Gemini 리랭커 (할루시네이션 방지)
- `search/searcher.py` — 검색 오케스트레이터
- `slack_app/bolt_app.py` — Slack Bolt 앱 (Socket Mode)
- `slack_app/commands.py` — /proposal-search 슬래시 커맨드
- `slack_app/events.py` — @봇 멘션 이벤트 핸들러
- `slack_app/messages.py` — Block Kit 메시지 포맷터

## 스프레드시트
- ID: env GOOGLE_SHEETS_ID
- 01.META_DATA: 제안서 메타데이터 (37컬럼, ~3500행)
- 21.requests: 검색 요청 로그

## 실행
```bash
# 임베딩 빌드 (최초 1회)
python scripts/build_embeddings.py

# CLI 검색 테스트
python scripts/test_search.py "AWS 기반 금융 프로젝트"

# Slack Bot 기동
python proposal_search_bot.py
```

## 참고
- 25.vrb_slack_dashboard 의 Slack/Sheets 패턴 재활용
- 같은 credentials/service_account.json 사용
