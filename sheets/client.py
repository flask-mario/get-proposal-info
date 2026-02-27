import gspread
from google.oauth2.service_account import Credentials

from config.settings import GOOGLE_SERVICE_ACCOUNT_FILE, GOOGLE_SHEETS_ID

_client = None
_spreadsheet = None

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def get_client():
    global _client
    if _client is None:
        creds = Credentials.from_service_account_file(
            GOOGLE_SERVICE_ACCOUNT_FILE, scopes=SCOPES
        )
        _client = gspread.authorize(creds)
    return _client


def get_spreadsheet():
    global _spreadsheet
    if _spreadsheet is None:
        client = get_client()
        if GOOGLE_SHEETS_ID:
            _spreadsheet = client.open_by_key(GOOGLE_SHEETS_ID)
        else:
            raise ValueError("GOOGLE_SHEETS_ID is not set")
    return _spreadsheet


def get_sheet(name):
    ss = get_spreadsheet()
    return ss.worksheet(name)
