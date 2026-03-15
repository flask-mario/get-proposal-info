# HANDOFF.md — 제안서 시맨틱 검색 Slack Bot

> 이 문서는 새로운 agent가 이 프로젝트를 즉시 이해하고 작업을 이어갈 수 있도록 작성되었습니다.

---

## 1. 프로젝트 요약

회사의 **3,519건 제안서 메타데이터**(Google Spreadsheet)를 자연어로 검색하는 Slack Bot.
단순 키워드 매칭이 아닌 **시맨틱 검색**이 핵심이며, Vertex AI Embeddings + Gemini LLM을 사용한다.

| 항목 | 값 |
|------|-----|
| GitHub | https://github.com/flask-mario/get-proposal-info |
| Spreadsheet ID | `1uZvbIISaBx9gQe3KqImegau61lfkuZVvHJYq2UTHIMI` |
| GCP Project | `jamesk-itplanning-250312` |
| Service Account | `proposal-bot@jamesk-itplanning-250312.iam.gserviceaccount.com` |
| Python | 3.13 |
| 진입점 | `proposal_search_bot.py` |

---

## 2. 현재 상태: 완료됨 (Phase 1~5 전체 구현 + Phase 6 검색 품질 개선)

### 성공한 부분

| 항목 | 상태 | 비고 |
|------|------|------|
| 프로젝트 구조 생성 | ✅ | 6개 패키지, 20+ 모듈 |
| Google Sheets 연동 | ✅ | 01.META_DATA (37컬럼, 3519행) 정상 로드 |
| 임베딩 빌드 | ✅ | 3,519벡터 × 768차원, 243초 소요, 10.3MB |
| 벡터 검색 | ✅ | numpy cosine similarity <1ms |
| 쿼리 동의어 확장 | ✅ | 32개 alias (AWS, 금융, AI 등) |
| Gemini 리랭킹 | ✅ | gemini-2.0-flash, 할루시네이션 방지 프롬프트 |
| 중복 제거 (dedup) | ✅ | 영한 정규화 + Jaccard+containment 유사도, 2-pass |
| Slack Bot (Socket Mode) | ✅ | /proposal-search, @멘션, DM 모두 동작 |
| Block Kit 응답 포맷 | ✅ | 관련도 이모지, 파일링크, 종합 답변 |
| 21.requests 로깅 | ✅ | 비동기 로깅, 채널 display name 표시 |
| Slack App 설정 가이드 | ✅ | `docs/slack_app_setup_guide.md` |
| 목록 모드 (Phase 6) | ✅ | "의료 도메인 현황" 등 목록형 쿼리 → compact 리스트 반환 (최대 20건) |
| 도메인 필터 보충 검색 (Phase 6) | ✅ | 도메인 키워드 감지 → 해당 도메인 메타데이터 필터링 보충 검색 |
| 리랭커 doc_id 매핑 수정 (Phase 6) | ✅ | index 기반→doc_id 기반 매핑으로 정확도 개선 |
| app_home_opened 핸들러 (Phase 6) | ✅ | Slack 경고 방지용 빈 핸들러 등록 |
| 빈 메타데이터 후보 필터링 (Phase 6) | ✅ | 고객사명·프로젝트명 둘 다 비어있는 후보 제거 |

### 검증 완료된 테스트 쿼리

```
"AWS 기반 금융 프로젝트"     → 관련 금융 고객사 결과 정상 반환
"쿠버네티스 컨테이너 구축"    → K8s 관련 프로젝트 정상 반환
"공공기관 클라우드 마이그레이션" → 공공 도메인 결과 정상 반환
"케이뱅크"                  → 중복 5건 → 1건으로 정상 dedup
"의료 도메인 제안서 현황"     → 목록 모드로 의료 도메인 제안서 compact 목록 반환
```

---

## 3. 구현 중 발생한 문제와 해결 (반드시 읽을 것)

### 3.1 스프레드시트 컬럼명 불일치
- **문제**: 계획서에 "제안요약"이라고 적혀 있었으나 실제 시트 컬럼은 `"요약"`
- **해결**: `config/settings.py`의 `METADATA_COLUMNS[19]`와 `EMBEDDING_FIELDS`를 `"요약"`으로 수정
- **교훈**: 시트 컬럼명은 반드시 실제 데이터로 확인할 것

### 3.2 Vertex AI 임베딩 토큰 한도 초과
- **문제**: batch_size=100일 때 20,000 토큰 한도 초과 (실제 26,125 토큰)
- **해결**: `EMBEDDING_BATCH_SIZE`를 20으로 축소 + `_embed_batch_with_retry()`에 재귀적 배치 분할 로직 추가
- **코드**: `embedding/embedder.py` — INVALID_ARGUMENT 에러 시 배치를 반으로 나눠 재시도

### 3.3 Gemini 모델 리전 제한
- **문제**: `gemini-2.0-flash`가 `asia-northeast3`에서 404 에러 (사용 불가)
- **해결**: `LLM_LOCATION = "us-central1"` 별도 설정 추가 (GCP_LOCATION과 분리)
- **코드**: `search/reranker.py`에서 `LLM_LOCATION` 사용, `embedding/embedder.py`는 `GCP_LOCATION` 사용
- **주의**: 임베딩은 asia-northeast3, LLM은 us-central1 — 두 리전이 다름

### 3.4 중복 검색 결과
- **문제**: "케이뱅크 앱뱅킹" 관련 결과가 5건 이상 중복 (연도별 갱신, Cloud/클라우드 표기 차이)
- **해결**: `search/dedup.py` 신규 구현
  - 영한 정규화 (`_EN_KR_MAP`: cloud→클라우드 등 21개 매핑)
  - 노이즈 접미사 제거 (사업, 프로젝트, 제안, 용역 등)
  - Jaccard + containment 혼합 유사도
  - **2-pass dedup**: Pass 1에서 교체된 항목이 kept 내부에서 새 중복을 만드는 문제 → Pass 2 반복 정리
- **파이프라인 변경**: 벡터검색 top-30 → dedup top-10 → 리랭킹 top-5 (기존: top-10 → 리랭킹)

### 3.5 gspread API 변경
- **문제**: `ws.update("A1", [data])` 인자 순서 변경 경고
- **해결**: `ws.update([data], "A1")` 형식으로 수정 (`sheets/request_logger.py`)

### 3.6 Python 출력 버퍼링
- **문제**: background 실행 시 로그가 보이지 않음
- **해결**: `PYTHONUNBUFFERED=1` 환경변수로 실행

### 3.7 리랭커 인덱스 매핑 불일치 (Phase 6)
- **문제**: Gemini 리랭커가 반환하는 `index` 값이 dedup 후 후보 배열의 인덱스와 불일치하여 엉뚱한 결과가 매핑됨
- **해결**: 리랭커 프롬프트에 `doc_id`를 포함시키고, 결과 매핑을 `doc_id` 기반 1차 → `index` 기반 2차 fallback 으로 변경
- **코드**: `search/reranker.py` — 프롬프트에 doc_id 추가, `search/searcher.py` — `candidates_by_doc_id` dict로 매핑

### 3.8 카테고리 필터형 쿼리에서 벡터 검색만으로 결과 부족 (Phase 6)
- **문제**: "의료 도메인 제안서 현황" 같은 쿼리에서 벡터 유사도만으로는 해당 도메인의 제안서가 충분히 검색되지 않음
- **해결**: `search/query_processor.py`에 도메인 키워드 감지 추가 + `embedding/index.py`에 `search_by_indices()` 메서드 추가하여 해당 도메인 인덱스만 대상으로 보충 검색
- **파이프라인 변경**: 벡터검색 top-30 → 도메인 필터 보충 → dedup → 리랭킹

### 3.9 빈 메타데이터 결과 노출 (Phase 6)
- **문제**: 고객사명·프로젝트명이 모두 비어있는 빈 행이 검색 결과에 포함됨
- **해결**: `search/searcher.py`에서 메타데이터 매핑 후 고객사명·프로젝트명이 둘 다 비어있는 후보를 필터링

---

## 4. 아키텍처

```
Slack User
  │
  ├─ /proposal-search 명령어 ──→ slack_app/commands.py
  ├─ @봇 멘션 ─────────────────→ slack_app/events.py (handle_mention)
  └─ DM ───────────────────────→ slack_app/events.py (handle_dm)
          │
          ▼
    search/searcher.py::search()
          │
          ├─ 1. 동의어 확장 + 모드 감지  search/query_processor.py  (32 aliases, 목록모드/도메인필터 감지)
          ├─ 2. 쿼리 임베딩              embedding/embedder.py      (Vertex AI, ~200ms)
          ├─ 3. 벡터 검색                embedding/index.py         (numpy cosine, <1ms, top-30)
          ├─ 3.5 도메인 필터 보충 검색    embedding/index.py         (search_by_indices, 해당 도메인만)
          ├─ 4. 메타데이터 매핑 + 빈 행 필터  sheets/loader.py      (인덱스→원본 데이터)
          │
          ├─ [목록 모드] → dedup top-20 → compact Block Kit 목록 반환 (리랭커 건너뜀)
          │
          ├─ 5. 중복 제거                search/dedup.py            (유사 프로젝트 통합, top-10)
          └─ 6. LLM 리랭킹              search/reranker.py         (Gemini, ~1-2s, top-5, doc_id 매핑)
          │
          ▼
    slack_app/messages.py → Block Kit 응답
    sheets/request_logger.py → 21.requests 비동기 로깅
```

---

## 5. 파일 구조 및 모듈별 역할

```
26.get_proposal_info/
├── proposal_search_bot.py       # 진입점 (Socket Mode 봇 기동)
├── config/
│   └── settings.py              # 모든 설정: 환경변수, 컬럼 스키마, 임계치, 모델명
├── sheets/
│   ├── client.py                # gspread 싱글턴 (credentials → client → spreadsheet)
│   ├── loader.py                # 01.META_DATA 로드 + JSON 캐시 (TTL 1시간)
│   └── request_logger.py        # 21.requests 비동기 로깅 (daemon thread)
├── embedding/
│   ├── builder.py               # 메타데이터 dict → 라벨:값 텍스트 (14 필드)
│   ├── embedder.py              # Vertex AI API 호출 (배치, 재시도, 분할)
│   ├── cache.py                 # vectors.npy + metadata.json 저장/로드
│   └── index.py                 # VectorIndex 클래스 (L2정규화, dot product)
├── search/
│   ├── query_processor.py       # 동의어 확장 (32 alias 규칙)
│   ├── dedup.py                 # 중복 제거 (영한 정규화, 2-pass, Jaccard+containment)
│   ├── reranker.py              # Gemini 리랭킹 (할루시네이션 방지 프롬프트)
│   └── searcher.py              # 검색 오케스트레이터 (전체 파이프라인 조합)
├── slack_app/
│   ├── bolt_app.py              # Slack Bolt App 인스턴스 + Socket Mode 시작
│   ├── commands.py              # /proposal-search 핸들러
│   ├── events.py                # @멘션 + DM 핸들러
│   └── messages.py              # Block Kit 포맷터 (결과, 에러, 로딩, 도움말)
├── scripts/
│   ├── build_embeddings.py      # 임베딩 전체 빌드 (최초 1회, ~4분)
│   ├── test_search.py           # CLI 검색 테스트
│   └── setup_requests_sheet.py  # 21.requests 헤더 초기화
├── docs/
│   └── slack_app_setup_guide.md # Slack App 생성 가이드 (관리자용)
├── data/
│   ├── embeddings/              # vectors.npy (10.3MB) + metadata.json (3MB) ← .gitignore
│   └── cache/                   # metadata.json (시트 캐시) ← .gitignore
├── credentials/
│   └── service_account.json     # GCP 서비스 계정 키 ← .gitignore
├── .env                         # Slack 토큰, GCP 설정 ← .gitignore
├── .env.example                 # 환경변수 템플릿
├── .gitignore
├── requirements.txt
├── CLAUDE.md                    # 프로젝트 규칙 + 파일 네이밍 컨벤션
└── HANDOFF.md                   # 이 문서
```

---

## 6. 핵심 설정값 (`config/settings.py`)

| 설정 | 값 | 의미 |
|------|-----|------|
| `EMBEDDING_MODEL` | text-multilingual-embedding-002 | 한국어 지원 임베딩 모델 |
| `EMBEDDING_DIMENSION` | 768 | 임베딩 차원 |
| `EMBEDDING_BATCH_SIZE` | 20 | API 배치 크기 (100→20 축소) |
| `LLM_MODEL` | gemini-2.0-flash | 리랭킹/요약 LLM |
| `GCP_LOCATION` | asia-northeast3 | 임베딩 리전 |
| `LLM_LOCATION` | us-central1 | LLM 리전 (**다름!**) |
| `SEARCH_TOP_K` | 30 | 벡터 검색 후보 수 |
| `DEDUP_TOP_K` | 10 | 중복 제거 후 최대 수 |
| `SIMILARITY_THRESHOLD` | 0.3 | 최소 유사도 컷오프 |
| `RERANK_TOP_N` | 5 | 최종 결과 수 |
| `DEDUP_NAME_THRESHOLD` | 0.6 | 동일 고객사 프로젝트명 유사도 임계치 |
| `LIST_MODE_MAX_RESULTS` | 20 | 목록 모드 최대 반환 수 |

---

## 7. 실행 방법

```bash
# 0. 환경 설정
cd 26.get_proposal_info
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 1. .env 설정 (.env.example 참고)
cp .env.example .env
# SLACK_BOT_TOKEN, SLACK_SIGNING_SECRET, SLACK_APP_TOKEN,
# GOOGLE_SHEETS_ID, GCP_PROJECT_ID 입력

# 2. credentials/service_account.json 배치
# GCP 서비스 계정 키 파일 (Sheets + Vertex AI 권한 필요)

# 3. 임베딩 빌드 (최초 1회, ~4분)
python scripts/build_embeddings.py

# 4. CLI 검색 테스트 (선택)
python scripts/test_search.py "AWS 기반 금융 프로젝트"

# 5. 21.requests 시트 초기화 (선택)
python scripts/setup_requests_sheet.py

# 6. Slack Bot 기동
PYTHONUNBUFFERED=1 python proposal_search_bot.py
```

---

## 8. 스프레드시트 구조

### 01.META_DATA (37 컬럼, A~AK)

```
문서ID, 파일ID, 문서유형, 고객사명, 프로젝트명,
서비스유형, 도메인, 프로젝트규모, 수주여부, 수주금액,
작성일자, 담당부문, 작성자, 재사용모듈태그, 등록일시,
검증자, 최종위치, 파일링크, 상태, 요약,              ← 20번째가 "요약" (NOT "제안요약")
프로젝트기간_시작, 프로젝트기간_종료, 사업역할, 공동수행사, 프로젝트범위,
주요기술스택, 클라우드플랫폼, 개발언어, 데이터베이스, 특화기술,
정량성과1_지표명, 정량성과1_수치, 정량성과2_지표명, 정량성과2_수치, 정성성과,
검색키워드, 유사프로젝트참조
```

### 21.requests (검색 요청 로그, 13 컬럼)

```
request_id, timestamp, slack_user_id, slack_user_name,
slack_channel_name, query_text, query_expanded, results_count,
top_score, response_time_ms, result_doc_ids, feedback, error
```

---

## 9. 의존성 그래프

```
proposal_search_bot.py
  ├── embedding.cache.cache_exists()          # 캐시 존재 확인
  ├── search.searcher._get_index()            # 벡터 인덱스 프리로드
  ├── slack_app.commands                      # import로 핸들러 등록
  ├── slack_app.events                        # import로 핸들러 등록
  └── slack_app.bolt_app.start_socket_mode()  # 봇 시작

search.searcher.search(query)
  ├── search.query_processor.expand_query()
  ├── embedding.embedder.embed_query()
  ├── embedding.index.VectorIndex.search()
  ├── sheets.loader.load_metadata()           # 인덱스→메타데이터 매핑
  ├── search.dedup.dedup_candidates()
  └── search.reranker.rerank()

scripts/build_embeddings.py                   # 오프라인 빌드
  ├── sheets.loader.load_metadata()
  ├── embedding.builder.build_texts()
  ├── embedding.embedder.embed_texts()        # Vertex AI 호출 (배치)
  └── embedding.cache.save_embeddings()
```

---

## 10. 알려진 제약 및 주의사항

### 반드시 알아야 할 것

1. **임베딩 리전 ≠ LLM 리전**: `GCP_LOCATION=asia-northeast3` (임베딩), `LLM_LOCATION=us-central1` (Gemini). 변경 시 양쪽 모두 확인.

2. **임베딩 캐시 필수**: `data/embeddings/vectors.npy` + `metadata.json`이 없으면 봇 기동 불가. `scripts/build_embeddings.py`로 생성. Git에 포함되지 않음 (`.gitignore`).

3. **배치 크기 20 고정**: Vertex AI text-multilingual-embedding-002의 요청당 토큰 한도(20,000) 때문. 100으로 올리면 에러 발생.

4. **Gemini JSON 파싱 실패 폴백**: `search/reranker.py`에서 Gemini가 유효하지 않은 JSON을 반환하면 원본 후보 상위 5개를 그대로 반환.

5. **dedup 2-pass 필수**: Pass 1에서 교체된 항목이 기존 kept 목록과 새 중복을 만들 수 있음. Pass 2에서 반복적으로 정리.

6. **파일 네이밍 컨벤션**: `app.py`, `main.py` 같은 범용 이름 금지. 반드시 목적이 드러나는 이름 사용 (CLAUDE.md 참조).

### 미구현 / 향후 개선 가능 영역

- **임베딩 증분 업데이트**: 현재는 전체 리빌드만 가능. 신규 행만 추가하는 증분 빌드 미구현.
- **피드백 수집**: 21.requests의 `feedback` 컬럼이 비어 있음. Slack 버튼으로 피드백 수집하는 UI 미구현.
- **검색 품질 튜닝**: `SIMILARITY_THRESHOLD`, `DEDUP_NAME_THRESHOLD` 등 임계치를 실사용 데이터로 조정 가능.
- **슬래시 커맨드 자동완성**: Slack API에서 커맨드 힌트/자동완성 미설정.

---

## 11. 환경 변수 목록 (`.env`)

```bash
# Slack (필수)
SLACK_BOT_TOKEN=xoxb-...              # Bot User OAuth Token
SLACK_SIGNING_SECRET=...              # Signing Secret
SLACK_APP_TOKEN=xapp-...              # App-Level Token (Socket Mode)

# Google Sheets (필수)
GOOGLE_SHEETS_ID=1uZvbIIS...          # 스프레드시트 ID
GOOGLE_SERVICE_ACCOUNT_FILE=credentials/service_account.json

# GCP (필수)
GCP_PROJECT_ID=jamesk-itplanning-250312
GCP_LOCATION=asia-northeast3          # 임베딩 리전
LLM_LOCATION=us-central1              # Gemini 리전 (별도!)
```

---

## 12. 트러블슈팅 가이드

| 증상 | 원인 | 해결 |
|------|------|------|
| `RuntimeError: 임베딩 캐시가 없습니다` | data/embeddings/ 비어있음 | `python scripts/build_embeddings.py` 실행 |
| `INVALID_ARGUMENT: token count exceeds` | 임베딩 배치 너무 큼 | `EMBEDDING_BATCH_SIZE=20` 확인 (settings.py) |
| `404 Model not found` (Gemini) | LLM 리전 미지원 | `LLM_LOCATION=us-central1` 확인 |
| `429 RESOURCE_EXHAUSTED` | Vertex AI rate limit | 자동 재시도 동작 (5s→10s→20s 백오프) |
| `Unhandled request app_home_opened` | 핸들러 미등록 | ✅ 해결됨: `slack_app/events.py`에 빈 핸들러 등록 완료 |
| Slack 응답 없음 | 봇이 채널에 미초대 | 채널에서 `/invite @제안서검색봇` |
| 검색 결과 0건 | 유사도 임계치 너무 높음 | `SIMILARITY_THRESHOLD` 값 조정 (현재 0.3) |
| gspread 인증 에러 | 서비스 계정 키 만료/권한 | credentials/service_account.json 갱신, Sheets 공유 확인 |

---

## 13. 패키지 의존성

```
slack_bolt>=1.18.0          # Slack Bolt (Socket Mode)
gspread>=6.0.0              # Google Sheets API
google-auth>=2.28.0         # GCP 인증
google-genai>=1.0.0         # Vertex AI (Embedding + Gemini)
numpy                       # 벡터 연산 (버전 제한 없음)
python-dotenv>=1.0.0        # .env 파일 로드
```

---

## 14. Slack App 필요 권한

Slack App 생성 시 필요한 설정 (상세: `docs/slack_app_setup_guide.md`):

- **Socket Mode**: 활성화 필수
- **Bot Token Scopes**: `chat:write`, `commands`, `app_mentions:read`, `users:read`, `im:history`, `im:write`
- **Slash Command**: `/proposal-search` 등록
- **Event Subscriptions**: `app_mention`, `message.im`
- **App-Level Token**: `connections:write` scope

---

*최종 업데이트: 2026-03-16*
*GitHub: https://github.com/flask-mario/get-proposal-info*
