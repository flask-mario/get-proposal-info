import os
from dotenv import load_dotenv

load_dotenv()

# ── Slack ────────────────────────────────────────────────
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET")
SLACK_APP_TOKEN = os.getenv("SLACK_APP_TOKEN")

# ── Google Sheets ────────────────────────────────────────
GOOGLE_SHEETS_ID = os.getenv("GOOGLE_SHEETS_ID", "")
GOOGLE_SERVICE_ACCOUNT_FILE = os.getenv(
    "GOOGLE_SERVICE_ACCOUNT_FILE", "credentials/service_account.json"
)

# ── GCP / Vertex AI ─────────────────────────────────────
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "")
GCP_LOCATION = os.getenv("GCP_LOCATION", "asia-northeast3")

# ── Sheet Names ──────────────────────────────────────────
SHEET_METADATA = "01.META_DATA"
SHEET_REQUESTS = "21.requests"

# ── Embedding Model ──────────────────────────────────────
EMBEDDING_MODEL = "text-multilingual-embedding-002"
EMBEDDING_DIMENSION = 768
EMBEDDING_BATCH_SIZE = 20

# ── LLM (Reranker / Summarizer) ─────────────────────────
LLM_MODEL = "gemini-2.0-flash"
LLM_LOCATION = os.getenv("LLM_LOCATION", "us-central1")

# ── Search Thresholds ────────────────────────────────────
SEARCH_TOP_K = 30
DEDUP_TOP_K = 10
SIMILARITY_THRESHOLD = 0.3
RERANK_TOP_N = 5
DEDUP_NAME_THRESHOLD = 0.6
LIST_MODE_MAX_RESULTS = 20

# ── Paths ────────────────────────────────────────────────
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
EMBEDDINGS_DIR = os.path.join(DATA_DIR, "embeddings")
CACHE_DIR = os.path.join(DATA_DIR, "cache")

# ── META_DATA Column Schema (A~AK, 37 columns) ─────────
METADATA_COLUMNS = [
    "문서ID", "파일ID", "문서유형", "고객사명", "프로젝트명",
    "서비스유형", "도메인", "프로젝트규모", "수주여부", "수주금액",
    "작성일자", "담당부문", "작성자", "재사용모듈태그", "등록일시",
    "검증자", "최종위치", "파일링크", "상태", "요약",
    "프로젝트기간_시작", "프로젝트기간_종료", "사업역할", "공동수행사", "프로젝트범위",
    "주요기술스택", "클라우드플랫폼", "개발언어", "데이터베이스", "특화기술",
    "정량성과1_지표명", "정량성과1_수치", "정량성과2_지표명", "정량성과2_수치", "정성성과",
    "검색키워드", "유사프로젝트참조",
]

# ── Embedding에 사용할 핵심 필드 (라벨: 컬럼명) ──────────
EMBEDDING_FIELDS = {
    "고객사": "고객사명",
    "프로젝트": "프로젝트명",
    "서비스유형": "서비스유형",
    "도메인": "도메인",
    "요약": "요약",
    "기술스택": "주요기술스택",
    "클라우드": "클라우드플랫폼",
    "개발언어": "개발언어",
    "데이터베이스": "데이터베이스",
    "특화기술": "특화기술",
    "키워드": "검색키워드",
    "범위": "프로젝트범위",
    "담당부문": "담당부문",
    "사업역할": "사업역할",
}

# ── Slack 응답에 표시할 필드 ──────────────────────────────
DISPLAY_FIELDS = {
    "고객사": "고객사명",
    "프로젝트": "프로젝트명",
    "서비스유형": "서비스유형",
    "도메인": "도메인",
    "기술스택": "주요기술스택",
    "클라우드": "클라우드플랫폼",
    "수주여부": "수주여부",
    "담당부문": "담당부문",
}

# ── Requests 로깅 컬럼 ───────────────────────────────────
REQUEST_LOG_COLUMNS = [
    "request_id", "timestamp", "slack_user_id", "slack_user_name",
    "slack_channel_name", "query_text", "query_expanded", "results_count",
    "top_score", "response_time_ms", "result_doc_ids", "feedback", "error",
]
