"""Tests for app.config: env var parsing and validate_config()."""

from __future__ import annotations

import importlib
import os
from pathlib import Path
from unittest.mock import patch

import pytest

pytestmark = pytest.mark.unit


@pytest.fixture(autouse=True)
def _restore_config():
    """Reload app.config with stock env after each test to prevent module-state leakage."""
    yield
    _reload_config(
        {
            "JIRA_URL": "https://x.atlassian.net",
            "JIRA_EMAIL": "a@b.com",
            "JIRA_API_TOKEN": "t",
        }
    )


def _reload_config(env: dict):
    """Reload app.core.config with a patched environment, return the module."""
    with (
        patch.dict(os.environ, env, clear=True),
        patch("dotenv.load_dotenv", lambda *args, **kwargs: None),
        patch("dotenv.dotenv_values", return_value={}),
    ):
        import app.core.config as cfg

        importlib.reload(cfg)
        return cfg


def test_validate_config_all_set():
    cfg = _reload_config(
        {
            "JIRA_URL": "https://example.atlassian.net",
            "JIRA_EMAIL": "user@example.com",
            "JIRA_API_TOKEN": "secret",
            "JIRA_BOARD_ID": "42",
        }
    )
    assert cfg.validate_config() == []


def test_validate_config_missing_url():
    cfg = _reload_config(
        {
            "JIRA_URL": "",
            "JIRA_EMAIL": "user@example.com",
            "JIRA_API_TOKEN": "secret",
            "JIRA_BOARD_ID": "42",
        }
    )
    errors = cfg.validate_config()
    assert any("JIRA_URL" in e for e in errors)
    assert len(errors) == 1


def test_validate_config_missing_email():
    cfg = _reload_config(
        {
            "JIRA_URL": "https://example.atlassian.net",
            "JIRA_EMAIL": "",
            "JIRA_API_TOKEN": "secret",
            "JIRA_BOARD_ID": "42",
        }
    )
    errors = cfg.validate_config()
    assert any("JIRA_EMAIL" in e for e in errors)
    assert len(errors) == 1


def test_validate_config_missing_token():
    cfg = _reload_config(
        {
            "JIRA_URL": "https://example.atlassian.net",
            "JIRA_EMAIL": "user@example.com",
            "JIRA_API_TOKEN": "",
            "JIRA_BOARD_ID": "42",
        }
    )
    errors = cfg.validate_config()
    assert any("JIRA_API_TOKEN" in e for e in errors)
    assert len(errors) == 1


def test_validate_config_all_missing():
    cfg = _reload_config({"JIRA_URL": "", "JIRA_EMAIL": "", "JIRA_API_TOKEN": ""})
    assert len(cfg.validate_config()) == 4


def test_board_id_numeric():
    cfg = _reload_config(
        {
            "JIRA_URL": "https://x.atlassian.net",
            "JIRA_EMAIL": "a@b.com",
            "JIRA_API_TOKEN": "t",
            "JIRA_BOARD_ID": "42",
        }
    )
    assert cfg.JIRA_BOARD_ID == 42


def test_board_id_non_numeric():
    cfg = _reload_config(
        {
            "JIRA_URL": "https://x.atlassian.net",
            "JIRA_EMAIL": "a@b.com",
            "JIRA_API_TOKEN": "t",
            "JIRA_BOARD_ID": "abc",
        }
    )
    assert cfg.JIRA_BOARD_ID is None


def test_sprint_count_default():
    cfg = _reload_config(
        {
            "JIRA_URL": "https://x.atlassian.net",
            "JIRA_EMAIL": "a@b.com",
            "JIRA_API_TOKEN": "t",
        }
    )
    assert cfg.JIRA_SPRINT_COUNT == 10


def test_sprint_count_custom():
    cfg = _reload_config(
        {
            "JIRA_URL": "https://x.atlassian.net",
            "JIRA_EMAIL": "a@b.com",
            "JIRA_API_TOKEN": "t",
            "JIRA_SPRINT_COUNT": "5",
        }
    )
    assert cfg.JIRA_SPRINT_COUNT == 5


def test_filter_id_numeric():
    cfg = _reload_config(
        {
            "JIRA_URL": "https://x.atlassian.net",
            "JIRA_EMAIL": "a@b.com",
            "JIRA_API_TOKEN": "t",
            "JIRA_FILTER_ID": "99",
        }
    )
    assert cfg.JIRA_FILTER_ID == 99


def test_filter_id_empty():
    cfg = _reload_config(
        {
            "JIRA_URL": "https://x.atlassian.net",
            "JIRA_EMAIL": "a@b.com",
            "JIRA_API_TOKEN": "t",
            "JIRA_FILTER_ID": "",  # explicitly empty to override any .env value
        }
    )
    assert cfg.JIRA_FILTER_ID is None


def test_env_path_points_to_project_root():
    import app.core.config as cfg

    importlib.reload(cfg)
    # _env_path should be <root>/.env, not <root>/app/.env
    assert cfg._env_path.name == ".env"
    assert cfg._env_path.parent.name != "app"


def test_jira_ssl_cert_returns_true_when_no_file():
    with patch.object(Path, "is_file", return_value=False):
        cfg = _reload_config(
            {
                "JIRA_URL": "https://x.atlassian.net",
                "JIRA_EMAIL": "a@b.com",
                "JIRA_API_TOKEN": "t",
            }
        )
    assert cfg.JIRA_SSL_CERT is True


def test_jira_ssl_cert_returns_path_when_file_exists():
    with patch.object(Path, "is_file", return_value=True):
        cfg = _reload_config(
            {
                "JIRA_URL": "https://x.atlassian.net",
                "JIRA_EMAIL": "a@b.com",
                "JIRA_API_TOKEN": "t",
            }
        )
    assert isinstance(cfg.JIRA_SSL_CERT, str)
    assert cfg.JIRA_SSL_CERT.endswith("jira_ca_bundle.pem")


# ---------------------------------------------------------------------------
# TR-41: JIRA_URL trailing-slash handling
# ---------------------------------------------------------------------------


def test_jira_url_trailing_slash_stripped():
    cfg = _reload_config(
        {
            "JIRA_URL": "https://example.atlassian.net/",
            "JIRA_EMAIL": "a@b.com",
            "JIRA_API_TOKEN": "t",
        }
    )
    assert cfg.JIRA_URL == "https://example.atlassian.net"


def test_jira_url_multiple_trailing_slashes_stripped():
    cfg = _reload_config(
        {
            "JIRA_URL": "https://example.atlassian.net///",
            "JIRA_EMAIL": "a@b.com",
            "JIRA_API_TOKEN": "t",
        }
    )
    assert cfg.JIRA_URL == "https://example.atlassian.net"


def test_jira_url_no_trailing_slash_unchanged():
    cfg = _reload_config(
        {
            "JIRA_URL": "https://example.atlassian.net",
            "JIRA_EMAIL": "a@b.com",
            "JIRA_API_TOKEN": "t",
        }
    )
    assert cfg.JIRA_URL == "https://example.atlassian.net"


def test_jira_url_empty_string_safe():
    cfg = _reload_config(
        {
            "JIRA_URL": "",
            "JIRA_EMAIL": "a@b.com",
            "JIRA_API_TOKEN": "t",
        }
    )
    assert cfg.JIRA_URL == ""


def test_validate_config_warns_trailing_slash():
    env = {
        "JIRA_URL": "https://example.atlassian.net/",
        "JIRA_EMAIL": "a@b.com",
        "JIRA_API_TOKEN": "t",
    }
    cfg = _reload_config(env)
    with patch.dict(os.environ, env, clear=True):
        errors = cfg.validate_config()
    assert any("trailing slash" in e.lower() for e in errors)


# AI label config vars
# ---------------------------------------------------------------------------

_BASE_ENV = {"JIRA_URL": "https://x.atlassian.net", "JIRA_EMAIL": "a@b.com", "JIRA_API_TOKEN": "t"}


def test_ai_assisted_label_default():
    cfg = _reload_config(_BASE_ENV)
    assert cfg.AI_ASSISTED_LABEL == "AI_assistance"


def test_ai_assisted_label_custom():
    cfg = _reload_config({**_BASE_ENV, "AI_ASSISTED_LABEL": "ai_helped"})
    assert cfg.AI_ASSISTED_LABEL == "ai_helped"


def test_ai_exclude_labels_empty():
    cfg = _reload_config(_BASE_ENV)
    assert cfg.AI_EXCLUDE_LABELS == []


def test_ai_exclude_labels_parsed():
    cfg = _reload_config({**_BASE_ENV, "AI_EXCLUDE_LABELS": "bug,chore"})
    assert cfg.AI_EXCLUDE_LABELS == ["bug", "chore"]


def test_ai_tool_labels_parsed():
    cfg = _reload_config({**_BASE_ENV, "AI_TOOL_LABELS": "AI_Tool_Copilot,AI_Tool_ChatGPT"})
    assert cfg.AI_TOOL_LABELS == ["AI_Tool_Copilot", "AI_Tool_ChatGPT"]


def test_ai_action_labels_parsed():
    cfg = _reload_config({**_BASE_ENV, "AI_ACTION_LABELS": "AI_Case_CodeGen,AI_Case_Review"})
    assert cfg.AI_ACTION_LABELS == ["AI_Case_CodeGen", "AI_Case_Review"]


def test_jira_schema_name_default():
    cfg = _reload_config(_BASE_ENV)
    assert cfg.JIRA_SCHEMA_NAME is None


def test_jira_schema_name_custom():
    cfg = _reload_config({**_BASE_ENV, "JIRA_SCHEMA_NAME": "My Schema"})
    assert cfg.JIRA_SCHEMA_NAME == "My Schema"


# Report generation config vars
# ---------------------------------------------------------------------------


def test_project_type_default_scrum():
    cfg = _reload_config(_BASE_ENV)
    assert cfg.PROJECT_TYPE == "SCRUM"


def test_project_type_kanban():
    cfg = _reload_config({**_BASE_ENV, "PROJECT_TYPE": "kanban"})
    assert cfg.PROJECT_TYPE == "KANBAN"


def test_project_type_invalid_falls_back():
    cfg = _reload_config({**_BASE_ENV, "PROJECT_TYPE": "waterfall"})
    assert cfg.PROJECT_TYPE == "SCRUM"


def test_estimation_type_default_story_points():
    cfg = _reload_config(_BASE_ENV)
    assert cfg.ESTIMATION_TYPE == "StoryPoints"


def test_estimation_type_jira_tickets():
    cfg = _reload_config({**_BASE_ENV, "ESTIMATION_TYPE": "JiraTickets"})
    assert cfg.ESTIMATION_TYPE == "JiraTickets"


def test_estimation_type_invalid_falls_back():
    cfg = _reload_config({**_BASE_ENV, "ESTIMATION_TYPE": "hours"})
    assert cfg.ESTIMATION_TYPE == "StoryPoints"


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("1", True),
        ("true", True),
        ("True", True),
        ("yes", True),
        ("YES", True),
        ("0", False),
        ("false", False),
        ("no", False),
        ("", True),  # empty → uses default (True)
    ],
)
def test_env_bool_values(raw, expected):
    cfg = _reload_config({**_BASE_ENV, "METRIC_VELOCITY": raw})
    assert cfg.METRIC_VELOCITY is expected


def test_metric_toggles_default_true():
    cfg = _reload_config(_BASE_ENV)
    assert cfg.METRIC_VELOCITY is True
    assert cfg.METRIC_AI_ASSISTANCE_TREND is True
    assert cfg.METRIC_AI_USAGE_DETAILS is True
    assert cfg.METRIC_DAU is True


def test_metric_toggles_explicit_false():
    env = {
        **_BASE_ENV,
        "METRIC_VELOCITY": "false",
        "METRIC_AI_ASSISTANCE_TREND": "no",
        "METRIC_AI_USAGE_DETAILS": "false",
        "METRIC_DAU": "no",
    }
    cfg = _reload_config(env)
    assert cfg.METRIC_VELOCITY is False
    assert cfg.METRIC_AI_ASSISTANCE_TREND is False
    assert cfg.METRIC_AI_USAGE_DETAILS is False
    assert cfg.METRIC_DAU is False
