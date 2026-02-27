"""Slack Bolt 앱 인스턴스 (Socket Mode)."""

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from config.settings import SLACK_APP_TOKEN, SLACK_BOT_TOKEN, SLACK_SIGNING_SECRET

app = App(
    token=SLACK_BOT_TOKEN,
    signing_secret=SLACK_SIGNING_SECRET,
)


def start_socket_mode():
    """Socket Mode로 Bolt 앱 시작."""
    handler = SocketModeHandler(app, SLACK_APP_TOKEN)
    handler.start()
