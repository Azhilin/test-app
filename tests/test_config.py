"""Tests for app.config: env var parsing and validate_config()."""
from __future__ import annotations

import importlib
import os
from unittest.mock import patch


def _reload_config(env: dict):
    """Reload app.config with a patched environment, return the module."""
    with patch.dict(os.environ, env, clear=True):
        import app.config as cfg
        importlib.reload(cfg)
        return cfg


def test_validate_config_all_set():
    cfg = _reload_config({
        "JIRA_URL": "https://example.atlassian.net",
        "JIRA_EMAIL": "user@example.com",
        "JIRA_API_TOKEN": "secret",
    })
    assert cfg.validate_config() == []


def test_validate_config_missing_url():
    cfg = _reload_config({
        "JIRA_URL": "",
        "JIRA_EMAIL": "user@example.com",
        "JIRA_API_TOKEN": "secret",
    })
    errors = cfg.validate_config()
    assert any("JIRA_URL" in e for e in errors)
    assert len(errors) == 1


def test_validate_config_missing_email():
    cfg = _reload_config({
        "JIRA_URL": "https://example.atlassian.net",
        "JIRA_EMAIL": "",
        "JIRA_API_TOKEN": "secret",
    })
    errors = cfg.validate_config()
    assert any("JIRA_EMAIL" in e for e in errors)
    assert len(errors) == 1


def test_validate_config_missing_token():
    cfg = _reload_config({
        "JIRA_URL": "https://example.atlassian.net",
        "JIRA_EMAIL": "user@example.com",
        "JIRA_API_TOKEN": "",
    })
    errors = cfg.validate_config()
    assert any("JIRA_API_TOKEN" in e for e in errors)
    assert len(errors) == 1


def test_validate_config_all_missing():
    cfg = _reload_config({"JIRA_URL": "", "JIRA_EMAIL": "", "JIRA_API_TOKEN": ""})
    assert len(cfg.validate_config()) == 3


def test_board_id_numeric():
    cfg = _reload_config({
        "JIRA_URL": "https://x.atlassian.net",
        "JIRA_EMAIL": "a@b.com",
        "JIRA_API_TOKEN": "t",
        "JIRA_BOARD_ID": "42",
    })
    assert cfg.JIRA_BOARD_ID == 42


def test_board_id_non_numeric():
    cfg = _reload_config({
        "JIRA_URL": "https://x.atlassian.net",
        "JIRA_EMAIL": "a@b.com",
        "JIRA_API_TOKEN": "t",
        "JIRA_BOARD_ID": "abc",
    })
    assert cfg.JIRA_BOARD_ID is None


def test_sprint_count_default():
    cfg = _reload_config({
        "JIRA_URL": "https://x.atlassian.net",
        "JIRA_EMAIL": "a@b.com",
        "JIRA_API_TOKEN": "t",
    })
    assert cfg.JIRA_SPRINT_COUNT == 10


def test_sprint_count_custom():
    cfg = _reload_config({
        "JIRA_URL": "https://x.atlassian.net",
        "JIRA_EMAIL": "a@b.com",
        "JIRA_API_TOKEN": "t",
        "JIRA_SPRINT_COUNT": "5",
    })
    assert cfg.JIRA_SPRINT_COUNT == 5


def test_filter_id_numeric():
    cfg = _reload_config({
        "JIRA_URL": "https://x.atlassian.net",
        "JIRA_EMAIL": "a@b.com",
        "JIRA_API_TOKEN": "t",
        "JIRA_FILTER_ID": "99",
    })
    assert cfg.JIRA_FILTER_ID == 99


def test_filter_id_empty():
    cfg = _reload_config({
        "JIRA_URL": "https://x.atlassian.net",
        "JIRA_EMAIL": "a@b.com",
        "JIRA_API_TOKEN": "t",
        "JIRA_FILTER_ID": "",  # explicitly empty to override any .env value
    })
    assert cfg.JIRA_FILTER_ID is None


def test_env_path_points_to_project_root():
    import app.config as cfg
    importlib.reload(cfg)
    # _env_path should be <root>/.env, not <root>/app/.env
    assert cfg._env_path.name == ".env"
    assert cfg._env_path.parent.name != "app"
