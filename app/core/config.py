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

# Optional: schema_name in config/jira_schema.json (CLI). When unset, default schema from file is used.
JIRA_SCHEMA_NAME = os.getenv("JIRA_SCHEMA_NAME", "").strip() or None

# Optional: Jira saved filter ID. When set, only issues matching this filter are included
# (filter's JQL is applied to sprint issues).
_filter_id = os.getenv("JIRA_FILTER_ID", "").strip()
JIRA_FILTER_ID = int(_filter_id) if _filter_id.isdigit() else None

# Optional: Jira project key (e.g. "MYPROJ"). Used to scope issue queries and shown in reports.
JIRA_PROJECT = os.getenv("JIRA_PROJECT", "").strip() or None

# DAU survey responses directory (default: config/dau/ in project root)
DAU_RESPONSES_DIR: str = os.getenv(
    "DAU_RESPONSES_DIR",
    str(Path(__file__).resolve().parent.parent.parent / "config" / "dau"),
)

# AI Adoption metrics labels
# Label that marks an issue as AI-assisted (default: AI_assistance)
AI_ASSISTED_LABEL = os.getenv("AI_ASSISTED_LABEL", "AI_assistance").strip() or "AI_assistance"
# Comma-separated labels whose issues are excluded from the AI% denominator
AI_EXCLUDE_LABELS = [lbl.strip() for lbl in os.getenv("AI_EXCLUDE_LABELS", "").split(",") if lbl.strip()]
# Comma-separated labels identifying AI tools (e.g. AI_Tool_Copilot,AI_Tool_ChatGPT)
AI_TOOL_LABELS = [lbl.strip() for lbl in os.getenv("AI_TOOL_LABELS", "").split(",") if lbl.strip()]
# Comma-separated labels identifying AI use-cases (e.g. AI_Case_CodeGen,AI_Case_Review)
AI_ACTION_LABELS = [lbl.strip() for lbl in os.getenv("AI_ACTION_LABELS", "").split(",") if lbl.strip()]

# Project type: SCRUM or KANBAN (default: SCRUM)
_project_type_raw = os.getenv("PROJECT_TYPE", "SCRUM").strip().upper()
PROJECT_TYPE: str = _project_type_raw if _project_type_raw in ("SCRUM", "KANBAN") else "SCRUM"

# Estimation type: StoryPoints or JiraTickets (default: StoryPoints)
_estimation_type_raw = os.getenv("ESTIMATION_TYPE", "StoryPoints").strip()
ESTIMATION_TYPE: str = _estimation_type_raw if _estimation_type_raw in ("StoryPoints", "JiraTickets") else "StoryPoints"


# Metric toggle flags (all default to True)
def _env_bool(key: str, default: bool = True) -> bool:
    val = os.getenv(key, "").strip().lower()
    if not val:
        return default
    return val in ("1", "true", "yes")


METRIC_VELOCITY: bool = _env_bool("METRIC_VELOCITY")
METRIC_CYCLE_TIME: bool = _env_bool("METRIC_CYCLE_TIME")
METRIC_AI_ASSISTANCE_TREND: bool = _env_bool("METRIC_AI_ASSISTANCE_TREND")
METRIC_AI_USAGE_DETAILS: bool = _env_bool("METRIC_AI_USAGE_DETAILS")
METRIC_CUSTOM_TRENDS: bool = _env_bool("METRIC_CUSTOM_TRENDS")
METRIC_DAU: bool = _env_bool("METRIC_DAU")
METRIC_DAU_TREND: bool = _env_bool("METRIC_DAU_TREND")


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
