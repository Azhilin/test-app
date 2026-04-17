"""Integration tests: verify module interaction with mocked external boundaries."""

from __future__ import annotations

import json
import urllib.request
from unittest.mock import MagicMock

import pytest

from tests.conftest import make_issue, make_sprint

pytestmark = pytest.mark.integration


# ---------------------------------------------------------------------------
# Full pipeline — success
# ---------------------------------------------------------------------------


def test_main_pipeline_success(monkeypatch, tmp_path):
    """Mock jira_client functions, call main.main(), verify HTML/MD files are created."""
    sprints = [make_sprint(1, "Sprint 1", "2026-01-01", "2026-01-14")]
    issues = [make_issue("T-1", "Done", 5.0)]

    monkeypatch.setattr("app.core.config.JIRA_URL", "https://test.atlassian.net")
    monkeypatch.setattr("app.core.config.JIRA_EMAIL", "u@t.com")
    monkeypatch.setattr("app.core.config.JIRA_API_TOKEN", "tok")
    monkeypatch.setattr("app.core.config.JIRA_BOARD_ID", 42)
    monkeypatch.setattr("app.core.config.JIRA_FILTER_ID", None)

    mock_jira = MagicMock()
    monkeypatch.setattr("app.core.jira_client.create_client", lambda: mock_jira)
    monkeypatch.setattr("app.core.jira_client.fetch_sprint_data", lambda j: (sprints, {1: issues}))

    # Redirect reports to tmp_path
    monkeypatch.setattr("app.cli.REPORTS_DIR", tmp_path / "generated" / "reports")
    monkeypatch.setattr("sys.argv", ["main.py"])

    from main import main

    rc = main()
    assert rc == 0

    reports_dir = tmp_path / "generated" / "reports"
    assert reports_dir.exists()
    subdirs = list(reports_dir.iterdir())
    assert len(subdirs) == 1
    html_files = list(subdirs[0].glob("*.html"))
    md_files = list(subdirs[0].glob("*.md"))
    assert len(html_files) == 1
    assert len(md_files) == 1

    html = html_files[0].read_text(encoding="utf-8")
    assert "Sprint 1" in html
    md = md_files[0].read_text(encoding="utf-8")
    assert "Sprint 1" in md


# ---------------------------------------------------------------------------
# Full pipeline — config failure
# ---------------------------------------------------------------------------


def test_main_pipeline_config_fail(monkeypatch):
    """No credentials → exit 1 with error message."""
    monkeypatch.setattr("app.core.config.JIRA_URL", "")
    monkeypatch.setattr("app.core.config.JIRA_EMAIL", "")
    monkeypatch.setattr("app.core.config.JIRA_API_TOKEN", "")
    monkeypatch.setattr("sys.argv", ["main.py"])

    from main import main

    rc = main()
    assert rc == 1


# ---------------------------------------------------------------------------
# --clean flag
# ---------------------------------------------------------------------------


def test_main_clean_removes_reports(monkeypatch, tmp_path):
    reports_dir = tmp_path / "generated" / "reports"
    reports_dir.mkdir(parents=True)
    (reports_dir / "dummy.txt").write_text("x")

    monkeypatch.setattr("app.cli.REPORTS_DIR", reports_dir)
    monkeypatch.setattr("sys.argv", ["main.py", "--clean"])

    from main import main

    rc = main()
    assert rc == 0
    assert not reports_dir.exists()


# ---------------------------------------------------------------------------
# Filter metadata flow
# ---------------------------------------------------------------------------


def test_filter_metadata_in_html(monkeypatch, tmp_path):
    sprints = [make_sprint(1, "Sprint 1", "2026-01-01", "2026-01-14")]
    issues = [make_issue("T-1", "Done", 5.0)]

    monkeypatch.setattr("app.core.config.JIRA_URL", "https://test.atlassian.net")
    monkeypatch.setattr("app.core.config.JIRA_EMAIL", "u@t.com")
    monkeypatch.setattr("app.core.config.JIRA_API_TOKEN", "tok")
    monkeypatch.setattr("app.core.config.JIRA_BOARD_ID", 7)
    monkeypatch.setattr("app.core.config.JIRA_FILTER_ID", 42)

    mock_jira = MagicMock()
    # Mock the _session.get for filter name
    mock_filter_resp = MagicMock()
    mock_filter_resp.json.return_value = {"name": "My Test Filter"}
    mock_jira._session.get.return_value = mock_filter_resp

    monkeypatch.setattr("app.core.jira_client.create_client", lambda: mock_jira)
    monkeypatch.setattr("app.core.jira_client.fetch_sprint_data", lambda j: (sprints, {1: issues}))
    monkeypatch.setattr("app.core.jira_client.get_filter_jql", lambda j: "project = TEST")

    monkeypatch.setattr("app.cli.REPORTS_DIR", tmp_path / "generated" / "reports")
    monkeypatch.setattr("sys.argv", ["main.py"])

    from main import main

    rc = main()
    assert rc == 0

    subdirs = list((tmp_path / "generated" / "reports").iterdir())
    html_files = list(subdirs[0].glob("*.html"))
    assert len(html_files) == 1
    html = html_files[0].read_text(encoding="utf-8")
    assert "My Test Filter" in html
    assert "42" in html


# ---------------------------------------------------------------------------
# Server test-connection endpoint (real server + mocked urlopen)
# ---------------------------------------------------------------------------


def test_server_test_connection_json_shape(server_url):
    """Verify test-connection returns the expected JSON shape for an error response."""
    body = json.dumps(
        {
            "url": "https://nonexistent-jira-12345.atlassian.net",
            "email": "test@test.com",
            "token": "badtoken",
        }
    ).encode()
    req = urllib.request.Request(
        f"{server_url}/api/test-connection",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    resp = urllib.request.urlopen(req)
    data = json.loads(resp.read())
    assert "ok" in data
    assert isinstance(data["ok"], bool)


# ---------------------------------------------------------------------------
# Server generate endpoint (real server)
# ---------------------------------------------------------------------------


def test_server_generate_sse_format(server_url):
    """Verify generate endpoint returns SSE-formatted response."""
    req = urllib.request.Request(f"{server_url}/api/generate")
    resp = urllib.request.urlopen(req, timeout=30)
    assert "text/event-stream" in resp.headers.get("Content-Type", "")
    body = resp.read().decode()
    # Should contain at least the close event
    assert "event: close" in body
