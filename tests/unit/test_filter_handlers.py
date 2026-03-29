"""Unit tests for Jira filter management handler methods in app.server.

Covers JFM-D-001/002, JFM-D-003, JFM-D-004, JFM-P-002 through JFM-P-010 (unit-testable slice),
and JFM-FUT-001.
"""

from __future__ import annotations

import importlib
import io
import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Shared helpers (mirror the pattern in tests/unit/test_server_handlers.py)
# ---------------------------------------------------------------------------


def _import_app_server_safe():
    orig_argv = sys.argv
    sys.argv = ["server.py"]
    sys.modules.pop("app.server", None)
    try:
        import app.server as srv

        importlib.reload(srv)
    finally:
        sys.argv = orig_argv
    return srv


def _make_handler(
    monkeypatch,
    tmp_path: Path,
    body: dict | None = None,
    raw: bytes | None = None,
    path: str = "/",
):
    srv = _import_app_server_safe()
    monkeypatch.setattr(srv, "ROOT", tmp_path)

    payload = raw if raw is not None else json.dumps(body or {}).encode()
    handler = object.__new__(srv.Handler)
    handler.headers = {"Content-Length": str(len(payload))}
    handler.rfile = io.BytesIO(payload)
    handler.wfile = io.BytesIO()
    handler._status = None
    handler._sent_headers = []
    handler.path = path

    def _send_response(status: int):
        handler._status = status

    def _send_header(name: str, value: str):
        handler._sent_headers.append((name, value))

    handler.send_response = _send_response
    handler.send_header = _send_header
    handler.end_headers = lambda: None
    return srv, handler


def _json_response(handler) -> tuple[int, dict]:
    return handler._status, json.loads(handler.wfile.getvalue().decode())


def _ensure_config_dir(tmp_path: Path) -> Path:
    config_dir = tmp_path / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


# ---------------------------------------------------------------------------
# JFM-D-001, JFM-D-002 — Default filter entry content
# ---------------------------------------------------------------------------


def test_default_filter_entry_is_present_and_correct(monkeypatch, tmp_path):
    """_load_filters() returns exactly one default entry with the correct name and params."""
    srv, handler = _make_handler(monkeypatch, tmp_path)
    _ensure_config_dir(tmp_path)

    filters = handler._load_filters()

    defaults = [f for f in filters if f.get("is_default")]
    assert len(defaults) == 1, "Exactly one default filter expected"
    d = defaults[0]
    # JFM-D-001
    assert d["filter_name"] == "Default_Jira_Filter"
    assert d["slug"] == "default_jira_filter"
    # JFM-D-002: sensible parameter defaults
    params = d.get("params", {})
    assert params.get("JIRA_FILTER_STATUS") == "Done"
    assert params.get("JIRA_CLOSED_SPRINTS_ONLY") == "true"
    assert params.get("schema_name") == "Default_Jira_Cloud"


# ---------------------------------------------------------------------------
# JFM-P-002 — Auto-create config file when missing
# ---------------------------------------------------------------------------


def test_load_filters_creates_file_when_missing(monkeypatch, tmp_path):
    """_load_filters() creates config/jira_filters.json with the default when the file is absent."""
    srv, handler = _make_handler(monkeypatch, tmp_path)
    config_dir = _ensure_config_dir(tmp_path)
    filters_path = config_dir / "jira_filters.json"

    assert not filters_path.exists()

    filters = handler._load_filters()

    assert filters_path.exists()
    on_disk = json.loads(filters_path.read_text(encoding="utf-8"))
    assert isinstance(on_disk, list)
    assert any(f.get("is_default") for f in on_disk)
    assert any(f.get("is_default") for f in filters)


# ---------------------------------------------------------------------------
# JFM-D-003 — Default always injected even if absent from the file
# ---------------------------------------------------------------------------


def test_load_filters_injects_default_when_absent_from_file(monkeypatch, tmp_path):
    """_load_filters() prepends the default entry at position 0 if the file has no is_default entry."""
    srv, handler = _make_handler(monkeypatch, tmp_path)
    config_dir = _ensure_config_dir(tmp_path)
    filters_path = config_dir / "jira_filters.json"
    user_filters = [
        {"filter_name": "My Filter", "slug": "my_filter", "is_default": False, "jql": "project = X"}
    ]
    filters_path.write_text(json.dumps(user_filters, indent=2), encoding="utf-8")

    filters = handler._load_filters()

    assert filters[0].get("is_default") is True
    assert filters[0]["filter_name"] == "Default_Jira_Filter"


# ---------------------------------------------------------------------------
# JFM-D-004 — Default filter cannot be deleted
# ---------------------------------------------------------------------------


def test_delete_default_filter_is_blocked(monkeypatch, tmp_path):
    """_handle_delete_filter('default_jira_filter') returns ok=False."""
    srv, handler = _make_handler(monkeypatch, tmp_path)
    _ensure_config_dir(tmp_path)

    handler._handle_delete_filter("default_jira_filter")
    status, data = _json_response(handler)

    assert status == 200
    assert data["ok"] is False
    assert "Cannot delete the default filter" in data["error"]


# ---------------------------------------------------------------------------
# JFM-P-009 — Unknown slug returns "Filter not found"
# ---------------------------------------------------------------------------


def test_delete_unknown_slug_returns_not_found(monkeypatch, tmp_path):
    """_handle_delete_filter() returns ok=False for an unknown slug."""
    srv, handler = _make_handler(monkeypatch, tmp_path)
    _ensure_config_dir(tmp_path)

    handler._handle_delete_filter("no_such_slug")
    status, data = _json_response(handler)

    assert status == 200
    assert data["ok"] is False
    assert "Filter not found" in data["error"]


# ---------------------------------------------------------------------------
# JFM-P-005 — Reject missing JIRA_PROJECT
# ---------------------------------------------------------------------------


def test_post_filter_rejects_blank_project(monkeypatch, tmp_path):
    """_handle_post_filter() returns ok=False when JIRA_PROJECT is missing or blank."""
    srv, handler = _make_handler(
        monkeypatch,
        tmp_path,
        body={"name": "My Filter", "params": {"JIRA_PROJECT": ""}},
    )
    _ensure_config_dir(tmp_path)

    handler._handle_post_filter()
    status, data = _json_response(handler)

    assert status == 200
    assert data["ok"] is False
    assert "JIRA_PROJECT is required" in data["error"]


# ---------------------------------------------------------------------------
# JFM-P-003 — POST creates a new entry
# ---------------------------------------------------------------------------


def test_post_filter_creates_new_entry(monkeypatch, tmp_path):
    """_handle_post_filter() appends a new entry and returns updated=False."""
    srv, handler = _make_handler(
        monkeypatch,
        tmp_path,
        body={"name": "Sprint Filter", "params": {"JIRA_PROJECT": "PROJ"}},
    )
    _ensure_config_dir(tmp_path)

    handler._handle_post_filter()
    status, data = _json_response(handler)

    assert status == 200
    assert data["ok"] is True
    assert data["updated"] is False
    assert data["slug"] == "sprint_filter"

    on_disk = json.loads((tmp_path / "config" / "jira_filters.json").read_text(encoding="utf-8"))
    user_entries = [f for f in on_disk if not f.get("is_default")]
    assert len(user_entries) == 1
    assert user_entries[0]["filter_name"] == "Sprint Filter"


# ---------------------------------------------------------------------------
# JFM-P-004 — POST upserts by name (updates existing entry)
# ---------------------------------------------------------------------------


def test_post_filter_updates_existing_entry(monkeypatch, tmp_path):
    """Second POST with the same name returns updated=True and replaces the entry in-place."""
    _ensure_config_dir(tmp_path)

    # First POST
    srv, handler1 = _make_handler(
        monkeypatch,
        tmp_path,
        body={"name": "Sprint Filter", "params": {"JIRA_PROJECT": "PROJ"}},
    )
    handler1._handle_post_filter()

    # Second POST with same name, different project
    _, handler2 = _make_handler(
        monkeypatch,
        tmp_path,
        body={"name": "Sprint Filter", "params": {"JIRA_PROJECT": "PROJ2"}},
    )
    handler2._handle_post_filter()
    status, data = _json_response(handler2)

    assert status == 200
    assert data["ok"] is True
    assert data["updated"] is True

    on_disk = json.loads((tmp_path / "config" / "jira_filters.json").read_text(encoding="utf-8"))
    user_entries = [f for f in on_disk if not f.get("is_default")]
    assert len(user_entries) == 1
    assert "PROJ2" in user_entries[0]["jql"]


# ---------------------------------------------------------------------------
# JFM-P-006 — JQL builder generates correct clauses
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "params,expected_contains,expected_absent",
    [
        ({"JIRA_PROJECT": "PROJ"}, "project = PROJ", None),
        ({"JIRA_PROJECT": "A,B"}, "project IN (A, B)", None),
        ({"JIRA_PROJECT": "PROJ", "JIRA_TEAM_ID": "T1"}, '"Team[Team]" = T1', None),
        (
            {"JIRA_PROJECT": "PROJ", "JIRA_FILTER_STATUS": "Done,Closed"},
            "status IN (Done, Closed)",
            None,
        ),
        (
            {"JIRA_PROJECT": "PROJ", "JIRA_CLOSED_SPRINTS_ONLY": "false"},
            "project = PROJ",
            "sprint in closedSprints()",
        ),
        (
            {"JIRA_PROJECT": "PROJ", "JIRA_ISSUE_TYPES": "Story,Bug"},
            "type IN (Story, Bug)",
            None,
        ),
    ],
)
def test_build_jql_from_params(monkeypatch, tmp_path, params, expected_contains, expected_absent):
    """_build_jql_from_params() produces correct JQL clauses for each param combination."""
    srv, _ = _make_handler(monkeypatch, tmp_path)
    jql = srv.Handler._build_jql_from_params(params)
    assert expected_contains in jql
    if expected_absent:
        assert expected_absent not in jql


# ---------------------------------------------------------------------------
# JFM-P-007 — Schema team JQL field name used when schema_name provided
# ---------------------------------------------------------------------------


def test_post_filter_uses_schema_team_jql_field(monkeypatch, tmp_path):
    """_handle_post_filter() substitutes the schema's team.jql_name in the JQL clause."""
    srv, handler = _make_handler(
        monkeypatch,
        tmp_path,
        body={
            "name": "Team Filter",
            "params": {
                "JIRA_PROJECT": "PROJ",
                "JIRA_TEAM_ID": "T1",
                "schema_name": "Custom_Schema",
            },
        },
    )
    _ensure_config_dir(tmp_path)

    custom_schema = {
        "schema_name": "Custom_Schema",
        "fields": {"team": {"id": "customfield_99", "jql_name": "Team[Engineering]"}},
    }
    with patch("app.core.schema.get_schema", return_value=custom_schema):
        handler._handle_post_filter()

    status, data = _json_response(handler)
    assert status == 200
    assert data["ok"] is True
    assert '"Team[Engineering]"' in data["jql"]


# ---------------------------------------------------------------------------
# JFM-P-010 — Filter data persists across server loads
# ---------------------------------------------------------------------------


def test_filter_data_persists_across_loads(monkeypatch, tmp_path):
    """Entries written by _save_filters() are returned by a fresh _load_filters() call."""
    srv, handler = _make_handler(monkeypatch, tmp_path)
    _ensure_config_dir(tmp_path)

    entries = [
        handler._DEFAULT_FILTER.copy(),
        {
            "filter_name": "Saved Filter",
            "slug": "saved_filter",
            "is_default": False,
            "jql": "project = X",
            "created_at": "2026-01-01T00:00:00",
            "params": {"JIRA_PROJECT": "X"},
        },
    ]
    handler._save_filters(entries)

    # Simulate server restart: fresh handler reads from the same config dir
    _, handler2 = _make_handler(monkeypatch, tmp_path)
    loaded = handler2._load_filters()

    slugs = [f.get("slug") for f in loaded]
    assert "saved_filter" in slugs
    assert "default_jira_filter" in slugs


# ---------------------------------------------------------------------------
# JFM-FUT-001 — _handle_generate() applies filter params to subprocess env
# ---------------------------------------------------------------------------


def test_generate_applies_filter_params_to_subprocess_env(monkeypatch, tmp_path):
    """_handle_generate() merges the selected filter's JIRA_PROJECT and JIRA_TEAM_ID into env."""
    srv, handler = _make_handler(
        monkeypatch, tmp_path, path="/api/generate?filter=sprint_filter"
    )
    config_dir = _ensure_config_dir(tmp_path)

    # Write a filter entry that the handler will load
    filter_entry = {
        "filter_name": "Sprint Filter",
        "slug": "sprint_filter",
        "is_default": False,
        "jql": "project = SPRJ AND status = Done",
        "created_at": "2026-01-01T00:00:00",
        "params": {
            "JIRA_PROJECT": "SPRJ",
            "JIRA_TEAM_ID": "T1",
        },
    }
    filters_path = config_dir / "jira_filters.json"
    filters_path.write_text(
        json.dumps([handler._DEFAULT_FILTER.copy(), filter_entry], indent=2),
        encoding="utf-8",
    )

    captured_env: dict = {}

    class _FakeProc:
        def __init__(self):
            self.stdout = iter([])
            self.returncode = 0

        def wait(self):
            return None

    def _fake_popen(*args, **kwargs):
        captured_env.update(kwargs.get("env") or {})
        return _FakeProc()

    monkeypatch.setattr(srv.subprocess, "Popen", _fake_popen)
    monkeypatch.setattr(srv, "dotenv_values", lambda *args: {})

    handler._handle_generate()

    assert captured_env.get("JIRA_PROJECT") == "SPRJ"
    assert captured_env.get("JIRA_TEAM_ID") == "T1"
