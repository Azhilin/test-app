"""Load configuration from environment."""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root
_env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(_env_path)

# SSL certificate: use local cert bundle when present, else fall back to default CA store
_cert_file = Path(__file__).resolve().parent.parent.parent / "certs" / "jira_ca_bundle.pem"
JIRA_SSL_CERT: str | bool = str(_cert_file) if _cert_file.is_file() else True

JIRA_URL = os.getenv("JIRA_URL", "").rstrip("/")
JIRA_EMAIL = os.getenv("JIRA_EMAIL", "")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN", "")

# Optional: board ID (numeric). If unset, script will use first available board.
_board_id = os.getenv("JIRA_BOARD_ID", "").strip()
JIRA_BOARD_ID = int(_board_id) if _board_id.isdigit() else None

# Number of past sprints to include in report
_sprint_count = os.getenv("JIRA_SPRINT_COUNT", "10").strip()
JIRA_SPRINT_COUNT = int(_sprint_count) if _sprint_count.isdigit() else 10

# Story points field key (varies by instance; common: customfield_10016)
JIRA_STORY_POINTS_FIELD = os.getenv("JIRA_STORY_POINTS_FIELD", "customfield_10016").strip() or "customfield_10016"

# Optional: Jira saved filter ID. When set, only issues matching this filter are included
# (filter's JQL is applied to sprint issues).
_filter_id = os.getenv("JIRA_FILTER_ID", "").strip()
JIRA_FILTER_ID = int(_filter_id) if _filter_id.isdigit() else None

# AI Adoption metrics labels
# Label that marks an issue as AI-assisted (default: AI_assistance)
AI_ASSISTED_LABEL = os.getenv("AI_ASSISTED_LABEL", "AI_assistance").strip() or "AI_assistance"
# Comma-separated labels whose issues are excluded from the AI% denominator
AI_EXCLUDE_LABELS = [lbl.strip() for lbl in os.getenv("AI_EXCLUDE_LABELS", "").split(",") if lbl.strip()]
# Comma-separated labels identifying AI tools (e.g. AI_Tool_Copilot,AI_Tool_ChatGPT)
AI_TOOL_LABELS = [lbl.strip() for lbl in os.getenv("AI_TOOL_LABELS", "").split(",") if lbl.strip()]
# Comma-separated labels identifying AI use-cases (e.g. AI_Case_CodeGen,AI_Case_Review)
AI_ACTION_LABELS = [lbl.strip() for lbl in os.getenv("AI_ACTION_LABELS", "").split(",") if lbl.strip()]


def validate_config() -> list[str]:
    """Return list of validation errors; empty if config is valid."""
    errors = []
    if not JIRA_URL:
        errors.append("JIRA_URL is not set")
    if not JIRA_EMAIL:
        errors.append("JIRA_EMAIL is not set")
    if not JIRA_API_TOKEN:
        errors.append("JIRA_API_TOKEN is not set")
    # Warn (not block) when raw JIRA_URL had trailing slash(es) — they were
    # silently stripped by the rstrip("/") above.
    raw_url = os.getenv("JIRA_URL", "")
    if raw_url and raw_url != raw_url.rstrip("/"):
        errors.append("JIRA_URL had a trailing slash (auto-stripped)")
    return errors
