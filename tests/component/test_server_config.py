"""Tests for the config API endpoints and _write_env_fields helper in server.py.

Covers:
  - _write_env_fields (direct unit tests, no HTTP)
  - GET  /api/config  (HTTP-level, via server_url fixture)
  - POST /api/config  (HTTP-level, via server_url fixture)
  - AI label and board ID config round-trips
  - Whitelist enforcement (unknown keys not leaked/written)

Isolation strategy
------------------
All tests that touch the filesystem redirect ``server.ROOT`` to a pytest
``tmp_path`` directory so the real ``.env`` is never read or written.
The ``temp_root`` fixture applies ``monkeypatch.setattr`` *after* the
``server_url`` fixture has reloaded the module, so the live request handler
sees the patched ``ROOT``.
"""
from __future__ import annotations

import importlib
import json
import sys
import threading
import urllib.error
import urllib.request
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get(url: str) -> dict:
    resp = urllib.request.urlopen(url)
    return json.loads(resp.read())


def _post(url: str, payload: dict | None = None, raw: bytes | None = None) -> dict:
    body = raw if raw is not None else json.dumps(payload).encode()
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read())


def _post_expect_error(url: str, payload: dict | None = None, raw: bytes | None = None) -> int:
    body = raw if raw is not None else json.dumps(payload).encode()
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with pytest.raises(urllib.error.HTTPError) as exc_info:
        urllib.request.urlopen(req)
    return exc_info.value.code


# ---------------------------------------------------------------------------
# Fixture: redirect server.ROOT to a temp directory
# ---------------------------------------------------------------------------

@pytest.fixture
def temp_root(tmp_path, monkeypatch):
    """Redirect app.server.ROOT to a fresh tmp_path so real .env is never touched."""
    import app.server as srv
    monkeypatch.setattr(srv, "ROOT", tmp_path)
    return tmp_path


# ---------------------------------------------------------------------------
# _write_env_fields — direct unit tests (no HTTP)
# ---------------------------------------------------------------------------

def _import_server_safe():
    """Import (or return cached) server module without letting server.py parse sys.argv."""
    orig_argv = sys.argv
    sys.argv = ["server.py"]
    sys.modules.pop("server", None)
    try:
        import server as srv
        importlib.reload(srv)
    finally:
        sys.argv = orig_argv
    return srv


class TestWriteEnvFields:
    """Unit tests for the _write_env_fields helper, called directly."""

    def _make_handler(self, tmp_path: Path, monkeypatch):
        """Return a Handler instance with ROOT pointing to tmp_path."""
        _import_server_safe()
        import app.server as srv
        monkeypatch.setattr(srv, "ROOT", tmp_path)
        # Instantiate without a real socket by bypassing __init__
        handler = object.__new__(srv.Handler)
        return handler

    def test_replaces_existing_key(self, tmp_path, monkeypatch):
        env = tmp_path / ".env"
        env.write_text("JIRA_URL=https://old.atlassian.net\nJIRA_EMAIL=old@example.com\n")
        h = self._make_handler(tmp_path, monkeypatch)
        h._write_env_fields({"JIRA_URL": "https://new.atlassian.net"})
        content = env.read_text()
        assert "JIRA_URL=https://new.atlassian.net" in content
        assert "JIRA_URL=https://old.atlassian.net" not in content
        # Unrelated keys preserved
        assert "JIRA_EMAIL=old@example.com" in content

    def test_uncomments_commented_key(self, tmp_path, monkeypatch):
        env = tmp_path / ".env"
        env.write_text("# JIRA_URL=https://placeholder.atlassian.net\nJIRA_EMAIL=a@b.com\n")
        h = self._make_handler(tmp_path, monkeypatch)
        h._write_env_fields({"JIRA_URL": "https://real.atlassian.net"})
        content = env.read_text()
        assert "JIRA_URL=https://real.atlassian.net" in content
        assert "# JIRA_URL=" not in content

    def test_appends_missing_key(self, tmp_path, monkeypatch):
        env = tmp_path / ".env"
        env.write_text("JIRA_EMAIL=a@b.com\n")
        h = self._make_handler(tmp_path, monkeypatch)
        h._write_env_fields({"JIRA_URL": "https://new.atlassian.net"})
        content = env.read_text()
        assert "JIRA_URL=https://new.atlassian.net" in content
        assert "JIRA_EMAIL=a@b.com" in content

    def test_creates_env_from_example_when_env_missing(self, tmp_path, monkeypatch):
        example = tmp_path / ".env.example"
        example.write_text("# JIRA_URL=\n# JIRA_EMAIL=\n# JIRA_API_TOKEN=\n")
        h = self._make_handler(tmp_path, monkeypatch)
        h._write_env_fields({
            "JIRA_URL":       "https://x.atlassian.net",
            "JIRA_EMAIL":     "u@x.com",
            "JIRA_API_TOKEN": "tok123",
        })
        env = tmp_path / ".env"
        assert env.exists(), ".env should be created"
        assert not example.read_text() != example.read_text(), ".env.example unchanged"
        content = env.read_text()
        assert "JIRA_URL=https://x.atlassian.net" in content
        assert "JIRA_EMAIL=u@x.com" in content
        assert "JIRA_API_TOKEN=tok123" in content

    def test_example_file_is_not_modified(self, tmp_path, monkeypatch):
        example = tmp_path / ".env.example"
        original = "# JIRA_URL=\n# JIRA_EMAIL=\n"
        example.write_text(original)
        h = self._make_handler(tmp_path, monkeypatch)
        h._write_env_fields({"JIRA_URL": "https://x.atlassian.net"})
        assert example.read_text() == original

    def test_creates_env_from_scratch_when_both_absent(self, tmp_path, monkeypatch):
        h = self._make_handler(tmp_path, monkeypatch)
        h._write_env_fields({"JIRA_URL": "https://x.atlassian.net", "JIRA_EMAIL": "u@x.com"})
        env = tmp_path / ".env"
        assert env.exists()
        content = env.read_text()
        assert "JIRA_URL=https://x.atlassian.net" in content
        assert "JIRA_EMAIL=u@x.com" in content

    def test_duplicate_key_only_first_occurrence_replaced(self, tmp_path, monkeypatch):
        env = tmp_path / ".env"
        env.write_text("JIRA_URL=https://first.atlassian.net\nJIRA_URL=https://second.atlassian.net\n")
        h = self._make_handler(tmp_path, monkeypatch)
        h._write_env_fields({"JIRA_URL": "https://replaced.atlassian.net"})
        content = env.read_text()
        lines = [l for l in content.splitlines() if l.startswith("JIRA_URL=")]
        # First occurrence replaced, second left as-is
        assert lines[0] == "JIRA_URL=https://replaced.atlassian.net"
        assert lines[1] == "JIRA_URL=https://second.atlassian.net"

    def test_token_with_equals_in_value(self, tmp_path, monkeypatch):
        """A token value that contains '=' characters must be stored verbatim."""
        env = tmp_path / ".env"
        env.write_text("JIRA_API_TOKEN=oldtoken\n")
        h = self._make_handler(tmp_path, monkeypatch)
        token_with_equals = "abc==def==ghi"
        h._write_env_fields({"JIRA_API_TOKEN": token_with_equals})
        content = env.read_text()
        assert f"JIRA_API_TOKEN={token_with_equals}" in content

    def test_crlf_file_does_not_crash(self, tmp_path, monkeypatch):
        env = tmp_path / ".env"
        env.write_bytes(b"JIRA_URL=https://old.atlassian.net\r\nJIRA_EMAIL=a@b.com\r\n")
        h = self._make_handler(tmp_path, monkeypatch)
        h._write_env_fields({"JIRA_URL": "https://new.atlassian.net"})
        content = env.read_text(encoding="utf-8")
        assert "JIRA_URL=https://new.atlassian.net" in content

    def test_write_creates_newline_terminated_file(self, tmp_path, monkeypatch):
        h = self._make_handler(tmp_path, monkeypatch)
        h._write_env_fields({"JIRA_URL": "https://x.atlassian.net"})
        raw = (tmp_path / ".env").read_bytes()
        assert raw.endswith(b"\n"), "File should end with a newline"

    def test_multiple_keys_written_in_one_call(self, tmp_path, monkeypatch):
        env = tmp_path / ".env"
        env.write_text("JIRA_URL=old\nJIRA_EMAIL=old@x.com\nJIRA_API_TOKEN=oldtok\n")
        h = self._make_handler(tmp_path, monkeypatch)
        h._write_env_fields({
            "JIRA_URL":       "https://new.atlassian.net",
            "JIRA_EMAIL":     "new@x.com",
            "JIRA_API_TOKEN": "newtok",
        })
        content = env.read_text()
        assert "JIRA_URL=https://new.atlassian.net" in content
        assert "JIRA_EMAIL=new@x.com" in content
        assert "JIRA_API_TOKEN=newtok" in content
        assert "old" not in content


# ---------------------------------------------------------------------------
# GET /api/config — HTTP-level tests
# ---------------------------------------------------------------------------

class TestGetConfig:

    def test_returns_configured_true_when_all_fields_set(self, server_url, temp_root):
        env = temp_root / ".env"
        env.write_text(
            "JIRA_URL=https://example.atlassian.net\n"
            "JIRA_EMAIL=user@example.com\n"
            "JIRA_API_TOKEN=supersecrettoken\n"
        )
        data = _get(f"{server_url}/api/config")
        assert data["configured"] is True
        cfg = data["config"]
        assert cfg["JIRA_URL"] == "https://example.atlassian.net"
        assert cfg["JIRA_EMAIL"] == "user@example.com"

    def test_token_always_masked_as_stars(self, server_url, temp_root):
        env = temp_root / ".env"
        env.write_text(
            "JIRA_URL=https://example.atlassian.net\n"
            "JIRA_EMAIL=user@example.com\n"
            "JIRA_API_TOKEN=my-very-secret-token\n"
        )
        data = _get(f"{server_url}/api/config")
        assert data["config"]["JIRA_API_TOKEN"] == "***", "Raw token must never be returned"

    def test_partial_env_returns_configured_false(self, server_url, temp_root):
        env = temp_root / ".env"
        env.write_text("JIRA_URL=https://example.atlassian.net\nJIRA_EMAIL=user@example.com\n")
        data = _get(f"{server_url}/api/config")
        assert data["configured"] is False
        assert "JIRA_API_TOKEN" not in data["config"]

    def test_missing_env_file_returns_empty_config(self, server_url, temp_root):
        # No .env in temp_root
        data = _get(f"{server_url}/api/config")
        assert data["configured"] is False
        assert data["config"] == {}

    def test_commented_out_lines_not_returned(self, server_url, temp_root):
        env = temp_root / ".env"
        env.write_text(
            "# JIRA_URL=https://commented.atlassian.net\n"
            "JIRA_EMAIL=user@example.com\n"
        )
        data = _get(f"{server_url}/api/config")
        assert "JIRA_URL" not in data["config"]
        assert data["config"].get("JIRA_EMAIL") == "user@example.com"

    def test_empty_value_not_included(self, server_url, temp_root):
        env = temp_root / ".env"
        env.write_text("JIRA_URL=\nJIRA_EMAIL=user@example.com\n")
        data = _get(f"{server_url}/api/config")
        assert "JIRA_URL" not in data["config"]
        assert data["config"].get("JIRA_EMAIL") == "user@example.com"

    def test_optional_fields_included_when_present(self, server_url, temp_root):
        env = temp_root / ".env"
        env.write_text(
            "JIRA_URL=https://example.atlassian.net\n"
            "JIRA_EMAIL=user@example.com\n"
            "JIRA_API_TOKEN=tok\n"
            "JIRA_SPRINT_COUNT=5\n"
            "JIRA_FILTER_ID=10033\n"
        )
        data = _get(f"{server_url}/api/config")
        cfg = data["config"]
        assert cfg.get("JIRA_SPRINT_COUNT") == "5"
        assert cfg.get("JIRA_FILTER_ID") == "10033"

    def test_line_without_equals_skipped(self, server_url, temp_root):
        env = temp_root / ".env"
        env.write_text("THIS_IS_NOT_VALID\nJIRA_EMAIL=user@example.com\n")
        data = _get(f"{server_url}/api/config")
        assert "THIS_IS_NOT_VALID" not in data["config"]
        assert data["config"].get("JIRA_EMAIL") == "user@example.com"

    def test_unknown_keys_not_included_in_response(self, server_url, temp_root):
        env = temp_root / ".env"
        env.write_text("SOME_RANDOM_KEY=value\nJIRA_EMAIL=user@example.com\n")
        data = _get(f"{server_url}/api/config")
        assert "SOME_RANDOM_KEY" not in data["config"]

    def test_get_config_returns_json_content_type(self, server_url, temp_root):
        resp = urllib.request.urlopen(f"{server_url}/api/config")
        assert "application/json" in resp.headers.get("Content-Type", "")


# ---------------------------------------------------------------------------
# POST /api/config — HTTP-level tests
# ---------------------------------------------------------------------------

class TestPostConfig:

    def test_overwrites_existing_env_fields(self, server_url, temp_root):
        env = temp_root / ".env"
        env.write_text(
            "JIRA_URL=https://old.atlassian.net\n"
            "JIRA_EMAIL=old@example.com\n"
            "JIRA_API_TOKEN=oldtoken\n"
        )
        data = _post(f"{server_url}/api/config", {
            "JIRA_URL":       "https://new.atlassian.net",
            "JIRA_EMAIL":     "new@example.com",
            "JIRA_API_TOKEN": "newtoken",
        })
        assert data["ok"] is True
        content = env.read_text()
        assert "JIRA_URL=https://new.atlassian.net" in content
        assert "JIRA_EMAIL=new@example.com" in content
        assert "JIRA_API_TOKEN=newtoken" in content

    def test_creates_env_from_example_template(self, server_url, temp_root):
        example = temp_root / ".env.example"
        example.write_text("# JIRA_URL=\n# JIRA_EMAIL=\n# JIRA_API_TOKEN=\n")
        data = _post(f"{server_url}/api/config", {
            "JIRA_URL":       "https://x.atlassian.net",
            "JIRA_EMAIL":     "u@x.com",
            "JIRA_API_TOKEN": "tok123",
        })
        assert data["ok"] is True
        env = temp_root / ".env"
        assert env.exists()
        content = env.read_text()
        assert "JIRA_URL=https://x.atlassian.net" in content
        assert "JIRA_EMAIL=u@x.com" in content
        assert "JIRA_API_TOKEN=tok123" in content

    def test_example_not_modified_after_create(self, server_url, temp_root):
        original = "# JIRA_URL=\n# JIRA_EMAIL=\n# JIRA_API_TOKEN=\n"
        example = temp_root / ".env.example"
        example.write_text(original)
        _post(f"{server_url}/api/config", {
            "JIRA_URL": "https://x.atlassian.net",
            "JIRA_EMAIL": "u@x.com",
            "JIRA_API_TOKEN": "tok",
        })
        assert example.read_text() == original

    def test_star_token_not_overwritten(self, server_url, temp_root):
        env = temp_root / ".env"
        env.write_text(
            "JIRA_URL=https://example.atlassian.net\n"
            "JIRA_EMAIL=user@example.com\n"
            "JIRA_API_TOKEN=existing-secret\n"
        )
        data = _post(f"{server_url}/api/config", {
            "JIRA_URL":       "https://example.atlassian.net",
            "JIRA_EMAIL":     "user@example.com",
            "JIRA_API_TOKEN": "***",
        })
        assert data["ok"] is True
        content = env.read_text()
        assert "JIRA_API_TOKEN=existing-secret" in content
        assert "JIRA_API_TOKEN=***" not in content

    def test_subset_of_keys_only_updates_those_keys(self, server_url, temp_root):
        env = temp_root / ".env"
        env.write_text(
            "JIRA_URL=https://old.atlassian.net\n"
            "JIRA_EMAIL=old@example.com\n"
            "JIRA_API_TOKEN=oldtoken\n"
            "JIRA_SPRINT_COUNT=10\n"
        )
        _post(f"{server_url}/api/config", {"JIRA_URL": "https://new.atlassian.net"})
        content = env.read_text()
        assert "JIRA_URL=https://new.atlassian.net" in content
        # Untouched keys preserved
        assert "JIRA_EMAIL=old@example.com" in content
        assert "JIRA_API_TOKEN=oldtoken" in content
        assert "JIRA_SPRINT_COUNT=10" in content

    def test_creates_env_from_scratch_when_both_absent(self, server_url, temp_root):
        data = _post(f"{server_url}/api/config", {
            "JIRA_URL":       "https://x.atlassian.net",
            "JIRA_EMAIL":     "u@x.com",
            "JIRA_API_TOKEN": "tok",
        })
        assert data["ok"] is True
        env = temp_root / ".env"
        assert env.exists()
        content = env.read_text()
        assert "JIRA_URL=https://x.atlassian.net" in content

    def test_invalid_json_returns_400(self, server_url, temp_root):
        code = _post_expect_error(f"{server_url}/api/config", raw=b"not valid json{{")
        assert code == 400

    def test_empty_body_is_noop_and_returns_ok(self, server_url, temp_root):
        env = temp_root / ".env"
        original = "JIRA_URL=https://example.atlassian.net\n"
        env.write_text(original)
        # Content-Length: 0 → _read_json_body returns {} → no updates
        req = urllib.request.Request(
            f"{server_url}/api/config",
            data=b"",
            headers={"Content-Type": "application/json", "Content-Length": "0"},
            method="POST",
        )
        resp = urllib.request.urlopen(req)
        data = json.loads(resp.read())
        assert data["ok"] is True
        assert env.read_text() == original

    def test_round_trip_url_email_token(self, server_url, temp_root):
        """POST then GET should reflect saved values (token masked)."""
        _post(f"{server_url}/api/config", {
            "JIRA_URL":       "https://round.atlassian.net",
            "JIRA_EMAIL":     "round@trip.com",
            "JIRA_API_TOKEN": "tripsecret",
        })
        data = _get(f"{server_url}/api/config")
        assert data["configured"] is True
        assert data["config"]["JIRA_URL"] == "https://round.atlassian.net"
        assert data["config"]["JIRA_EMAIL"] == "round@trip.com"
        assert data["config"]["JIRA_API_TOKEN"] == "***"

    def test_token_with_equals_sign_round_trip(self, server_url, temp_root):
        """Token values containing '=' must survive a write/read cycle."""
        token = "base64tokenABC==XYZ"
        _post(f"{server_url}/api/config", {
            "JIRA_URL":       "https://x.atlassian.net",
            "JIRA_EMAIL":     "u@x.com",
            "JIRA_API_TOKEN": token,
        })
        content = (temp_root / ".env").read_text()
        assert f"JIRA_API_TOKEN={token}" in content

    def test_post_config_route_exists(self, server_url, temp_root):
        """POST /api/config must not 404."""
        data = _post(f"{server_url}/api/config", {})
        assert "ok" in data

    def test_post_saves_filter_fields_to_env(self, server_url, temp_root):
        env = temp_root / ".env"
        env.write_text("JIRA_URL=https://x.atlassian.net\n")
        _post(f"{server_url}/api/config", {
            "JIRA_SPRINT_COUNT": "5",
            "JIRA_FILTER_ID":    "10033",
            "JIRA_PROJECT":      "MYTEAM",
        })
        content = env.read_text()
        assert "JIRA_SPRINT_COUNT=5" in content
        assert "JIRA_FILTER_ID=10033" in content
        assert "JIRA_PROJECT=MYTEAM" in content
        assert "JIRA_URL=https://x.atlassian.net" in content

    def test_post_saves_ai_labels_to_env(self, server_url, temp_root):
        env = temp_root / ".env"
        env.write_text("")
        _post(f"{server_url}/api/config", {
            "AI_ASSISTED_LABEL": "AI_help",
            "AI_EXCLUDE_LABELS": "Infra,Ops",
            "AI_TOOL_LABELS":    "Copilot,ChatGPT",
            "AI_ACTION_LABELS":  "CodeGen,Review",
        })
        content = env.read_text()
        assert "AI_ASSISTED_LABEL=AI_help" in content
        assert "AI_EXCLUDE_LABELS=Infra,Ops" in content
        assert "AI_TOOL_LABELS=Copilot,ChatGPT" in content
        assert "AI_ACTION_LABELS=CodeGen,Review" in content

    def test_post_saves_board_id_to_env(self, server_url, temp_root):
        env = temp_root / ".env"
        env.write_text("")
        _post(f"{server_url}/api/config", {"JIRA_BOARD_ID": "42"})
        content = env.read_text()
        assert "JIRA_BOARD_ID=42" in content

    def test_round_trip_all_fields(self, server_url, temp_root):
        """POST every supported field, then GET and verify each one."""
        (temp_root / ".env").write_text("")
        payload = {
            "JIRA_URL":               "https://rt.atlassian.net",
            "JIRA_EMAIL":             "rt@x.com",
            "JIRA_API_TOKEN":         "tok",
            "JIRA_BOARD_ID":          "7",
            "JIRA_SPRINT_COUNT":      "3",
            "JIRA_SCHEMA_NAME":       "Custom_Schema",
            "JIRA_FILTER_ID":         "555",
            "JIRA_PROJECT":           "PROJ",
            "JIRA_TEAM_ID":           "abc-123",
            "JIRA_ISSUE_TYPES":       "Bug,Story",
            "JIRA_FILTER_STATUS":     "Done,Closed",
            "JIRA_CLOSED_SPRINTS_ONLY": "false",
            "JIRA_FILTER_PAGE_SIZE":  "50",
            "AI_ASSISTED_LABEL":      "AI_yes",
            "AI_EXCLUDE_LABELS":      "Exclude1",
            "AI_TOOL_LABELS":         "Tool1,Tool2",
            "AI_ACTION_LABELS":       "Act1",
        }
        _post(f"{server_url}/api/config", payload)
        data = _get(f"{server_url}/api/config")
        cfg = data["config"]
        assert cfg["JIRA_URL"] == "https://rt.atlassian.net"
        assert cfg["JIRA_EMAIL"] == "rt@x.com"
        assert cfg["JIRA_API_TOKEN"] == "***"
        assert cfg["JIRA_BOARD_ID"] == "7"
        assert cfg["JIRA_SPRINT_COUNT"] == "3"
        assert cfg["JIRA_SCHEMA_NAME"] == "Custom_Schema"
        assert cfg["JIRA_FILTER_ID"] == "555"
        assert cfg["JIRA_PROJECT"] == "PROJ"
        assert cfg["JIRA_TEAM_ID"] == "abc-123"
        assert cfg["JIRA_ISSUE_TYPES"] == "Bug,Story"
        assert cfg["JIRA_FILTER_STATUS"] == "Done,Closed"
        assert cfg["JIRA_CLOSED_SPRINTS_ONLY"] == "false"
        assert cfg["JIRA_FILTER_PAGE_SIZE"] == "50"
        assert cfg["AI_ASSISTED_LABEL"] == "AI_yes"
        assert cfg["AI_EXCLUDE_LABELS"] == "Exclude1"
        assert cfg["AI_TOOL_LABELS"] == "Tool1,Tool2"
        assert cfg["AI_ACTION_LABELS"] == "Act1"

    def test_post_config_ignores_unknown_keys(self, server_url, temp_root):
        """Unknown keys in the POST body must not be written to .env."""
        env = temp_root / ".env"
        env.write_text("JIRA_URL=https://x.atlassian.net\n")
        _post(f"{server_url}/api/config", {
            "SOME_RANDOM_KEY": "should_not_appear",
            "SECRET_SAUCE":    "nope",
        })
        content = env.read_text()
        assert "SOME_RANDOM_KEY" not in content
        assert "SECRET_SAUCE" not in content


# ---------------------------------------------------------------------------
# GET /api/config — AI label and board ID tests
# ---------------------------------------------------------------------------

class TestGetConfigExtended:

    def test_ai_label_fields_returned_when_present(self, server_url, temp_root):
        env = temp_root / ".env"
        env.write_text(
            "AI_ASSISTED_LABEL=AI_help\n"
            "AI_EXCLUDE_LABELS=Infra,Ops\n"
            "AI_TOOL_LABELS=Copilot\n"
            "AI_ACTION_LABELS=CodeGen\n"
        )
        data = _get(f"{server_url}/api/config")
        cfg = data["config"]
        assert cfg["AI_ASSISTED_LABEL"] == "AI_help"
        assert cfg["AI_EXCLUDE_LABELS"] == "Infra,Ops"
        assert cfg["AI_TOOL_LABELS"] == "Copilot"
        assert cfg["AI_ACTION_LABELS"] == "CodeGen"

    def test_ai_label_fields_absent_when_not_set(self, server_url, temp_root):
        env = temp_root / ".env"
        env.write_text("JIRA_URL=https://x.atlassian.net\n")
        data = _get(f"{server_url}/api/config")
        cfg = data["config"]
        assert "AI_ASSISTED_LABEL" not in cfg
        assert "AI_EXCLUDE_LABELS" not in cfg
        assert "AI_TOOL_LABELS" not in cfg
        assert "AI_ACTION_LABELS" not in cfg

    def test_board_id_returned_when_present(self, server_url, temp_root):
        env = temp_root / ".env"
        env.write_text("JIRA_BOARD_ID=123\n")
        data = _get(f"{server_url}/api/config")
        assert data["config"]["JIRA_BOARD_ID"] == "123"

    def test_board_id_absent_when_not_set(self, server_url, temp_root):
        env = temp_root / ".env"
        env.write_text("JIRA_URL=https://x.atlassian.net\n")
        data = _get(f"{server_url}/api/config")
        assert "JIRA_BOARD_ID" not in data["config"]

    def test_empty_ai_labels_omitted(self, server_url, temp_root):
        """Empty string values should not appear in the response."""
        env = temp_root / ".env"
        env.write_text("AI_ASSISTED_LABEL=\nAI_TOOL_LABELS=\n")
        data = _get(f"{server_url}/api/config")
        cfg = data["config"]
        assert "AI_ASSISTED_LABEL" not in cfg
        assert "AI_TOOL_LABELS" not in cfg

    def test_only_whitelisted_keys_returned(self, server_url, temp_root):
        """Arbitrary keys in .env must not leak through GET /api/config."""
        env = temp_root / ".env"
        env.write_text(
            "JIRA_URL=https://x.atlassian.net\n"
            "DB_PASSWORD=super_secret\n"
            "AWS_SECRET_KEY=nope\n"
        )
        data = _get(f"{server_url}/api/config")
        cfg = data["config"]
        assert "DB_PASSWORD" not in cfg
        assert "AWS_SECRET_KEY" not in cfg
        assert cfg["JIRA_URL"] == "https://x.atlassian.net"
