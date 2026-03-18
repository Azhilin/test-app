"""Load configuration from environment."""
import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root
_env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(_env_path)

JIRA_URL = os.getenv("JIRA_URL", "").rstrip("/")
JIRA_EMAIL = os.getenv("JIRA_EMAIL", "")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN", "")

# Optional: board ID (numeric). If unset, script will use first available board.
_board_id = os.getenv("JIRA_BOARD_ID", "").strip()
JIRA_BOARD_ID = int(_board_id) if _board_id.isdigit() else None

# Number of past sprints to include in report
_sprint_count = os.getenv("JIRA_SPRINT_COUNT", "10").strip()
JIRA_SPRINT_COUNT = int(_sprint_count) if _sprint_count.isdigit() else 10


def validate_config() -> list[str]:
    """Return list of validation errors; empty if config is valid."""
    errors = []
    if not JIRA_URL:
        errors.append("JIRA_URL is not set")
    if not JIRA_EMAIL:
        errors.append("JIRA_EMAIL is not set")
    if not JIRA_API_TOKEN:
        errors.append("JIRA_API_TOKEN is not set")
    return errors
