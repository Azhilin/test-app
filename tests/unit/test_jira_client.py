"""Tests for app.jira_client: Jira API wrapper (all Jira calls mocked)."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from app.core import jira_client
from tests.conftest import make_sprint

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# create_client
# ---------------------------------------------------------------------------


def test_create_client_returns_jira_instance(monkeypatch):
    monkeypatch.setattr("app.core.config.JIRA_URL", "https://test.atlassian.net")
    monkeypatch.setattr("app.core.config.JIRA_EMAIL", "user@test.com")
    monkeypatch.setattr("app.core.config.JIRA_API_TOKEN", "tok123")
    monkeypatch.setattr("app.core.config.JIRA_SSL_CERT", True)
    with patch("app.core.jira_client.Jira") as MockJira:
        jira_client.create_client()
        MockJira.assert_called_once_with(
            url="https://test.atlassian.net",
            username="user@test.com",
            password="tok123",
            verify_ssl=True,
            timeout=55,
        )


def test_create_client_uses_config_values(monkeypatch):
    monkeypatch.setattr("app.core.config.JIRA_URL", "https://other.atlassian.net")
    monkeypatch.setattr("app.core.config.JIRA_EMAIL", "other@test.com")
    monkeypatch.setattr("app.core.config.JIRA_API_TOKEN", "other_tok")
    monkeypatch.setattr("app.core.config.JIRA_SSL_CERT", True)
    with patch("app.core.jira_client.Jira") as MockJira:
        jira_client.create_client()
        args = MockJira.call_args
        assert args.kwargs["url"] == "https://other.atlassian.net"
        assert args.kwargs["username"] == "other@test.com"


def test_create_client_passes_verify_ssl(monkeypatch):
    monkeypatch.setattr("app.core.config.JIRA_URL", "https://test.atlassian.net")
    monkeypatch.setattr("app.core.config.JIRA_EMAIL", "user@test.com")
    monkeypatch.setattr("app.core.config.JIRA_API_TOKEN", "tok123")
    monkeypatch.setattr("app.core.config.JIRA_SSL_CERT", "/some/path/jira_ca_bundle.pem")
    with patch("app.core.jira_client.Jira") as MockJira:
        jira_client.create_client()
        args = MockJira.call_args
        assert args.kwargs["verify_ssl"] == "/some/path/jira_ca_bundle.pem"


# ---------------------------------------------------------------------------
# get_board_id
# ---------------------------------------------------------------------------


def test_get_board_id_from_config(monkeypatch, mock_jira):
    monkeypatch.setattr("app.core.config.JIRA_BOARD_ID", 42)
    assert jira_client.get_board_id(mock_jira) == 42
    mock_jira.get_all_agile_boards.assert_not_called()


def test_get_board_id_raises_when_not_configured(monkeypatch, mock_jira):
    monkeypatch.setattr("app.core.config.JIRA_BOARD_ID", None)
    with pytest.raises(ValueError, match="JIRA_BOARD_ID is not set"):
        jira_client.get_board_id(mock_jira)
    mock_jira.get_all_agile_boards.assert_not_called()


# ---------------------------------------------------------------------------
# get_sprints
# ---------------------------------------------------------------------------


def test_get_sprints_sorted_desc_by_start_date(monkeypatch, mock_jira):
    monkeypatch.setattr("app.core.config.JIRA_SPRINT_COUNT", 10)
    mock_jira.get_all_sprints_from_board.side_effect = [
        {
            "values": [
                {"id": 1, "name": "S1", "startDate": "2026-01-01"},
                {"id": 2, "name": "S2", "startDate": "2026-02-01"},
            ]
        },
        {"values": []},
    ]
    result = jira_client.get_sprints(mock_jira, 1)
    assert result[0]["name"] == "S2"
    assert result[1]["name"] == "S1"


def test_get_sprints_capped_at_sprint_count(monkeypatch, mock_jira):
    monkeypatch.setattr("app.core.config.JIRA_SPRINT_COUNT", 2)
    mock_jira.get_all_sprints_from_board.side_effect = [
        {"values": [{"id": i, "name": f"S{i}", "startDate": f"2026-0{i}-01"} for i in range(1, 6)]},
        {"values": []},
    ]
    result = jira_client.get_sprints(mock_jira, 1)
    assert len(result) == 2


def test_get_sprints_empty(monkeypatch, mock_jira):
    monkeypatch.setattr("app.core.config.JIRA_SPRINT_COUNT", 10)
    mock_jira.get_all_sprints_from_board.side_effect = [
        {"values": []},
        {"values": []},
    ]
    assert jira_client.get_sprints(mock_jira, 1) == []


def test_get_sprints_returns_newest_when_paginated(monkeypatch, mock_jira):
    """When closed sprints span multiple pages, the NEWEST sprints are returned, not the oldest."""
    monkeypatch.setattr("app.core.config.JIRA_SPRINT_COUNT", 2)
    # First page is full (50 items, all old) → triggers a second page fetch
    old_sprints = [{"id": i, "name": f"S{i}", "startDate": f"{1970 + i}-01-01"} for i in range(1, 51)]
    # Second page has 3 newer sprints (fewer than 50 → pagination stops)
    new_sprints = [
        {"id": 51, "name": "S51", "startDate": "2025-01-01"},
        {"id": 52, "name": "S52", "startDate": "2025-02-01"},
        {"id": 53, "name": "S53", "startDate": "2025-03-01"},
    ]
    mock_jira.get_all_sprints_from_board.side_effect = [
        {"values": old_sprints},   # page 1: closed (full page → fetch next)
        {"values": new_sprints},   # page 2: closed (partial → stop)
        {"values": []},            # active
    ]
    result = jira_client.get_sprints(mock_jira, 1)
    assert len(result) == 2
    assert result[0]["name"] == "S53"
    assert result[1]["name"] == "S52"


def test_get_sprints_excludes_active_when_closed_only(monkeypatch, mock_jira):
    monkeypatch.setattr("app.core.config.JIRA_SPRINT_COUNT", 10)
    monkeypatch.setattr("app.core.config.JIRA_CLOSED_SPRINTS_ONLY", True)
    mock_jira.get_all_sprints_from_board.side_effect = [
        {"values": [{"id": 1, "name": "ClosedS", "startDate": "2026-01-01"}]},
        {"values": []},  # pagination end
        {"values": [{"id": 99, "name": "ActiveS", "startDate": "2026-03-01"}]},  # active
    ]
    result = jira_client.get_sprints(mock_jira, 1)
    names = [s["name"] for s in result]
    assert "ActiveS" not in names
    assert "ClosedS" in names


def test_get_sprints_includes_active_when_closed_only_false(monkeypatch, mock_jira):
    monkeypatch.setattr("app.core.config.JIRA_SPRINT_COUNT", 10)
    monkeypatch.setattr("app.core.config.JIRA_CLOSED_SPRINTS_ONLY", False)
    # One partial closed page (stops pagination), then active sprint
    mock_jira.get_all_sprints_from_board.side_effect = [
        {"values": [{"id": 1, "name": "ClosedS", "startDate": "2026-01-01"}]},  # closed (partial → stop)
        {"values": [{"id": 99, "name": "ActiveS", "startDate": "2026-03-01"}]},  # active
    ]
    result = jira_client.get_sprints(mock_jira, 1)
    names = [s["name"] for s in result]
    assert "ActiveS" in names
    assert "ClosedS" in names


def test_get_sprints_active_sprint_comes_first(monkeypatch, mock_jira):
    """Active sprint must be index 0 so the template's .reverse() places it rightmost in charts."""
    monkeypatch.setattr("app.core.config.JIRA_SPRINT_COUNT", 10)
    monkeypatch.setattr("app.core.config.JIRA_CLOSED_SPRINTS_ONLY", False)
    mock_jira.get_all_sprints_from_board.side_effect = [
        {
            "values": [
                {"id": 1, "name": "S1", "state": "closed", "startDate": "2026-01-01"},
                {"id": 2, "name": "S2", "state": "closed", "startDate": "2026-02-01"},
            ]
        },
        {"values": [{"id": 3, "name": "S3-active", "state": "active", "startDate": "2026-03-01"}]},
    ]
    result = jira_client.get_sprints(mock_jira, 1)
    assert result[0]["name"] == "S3-active", "Active sprint must be first; template .reverse() puts it rightmost"
    assert result[1]["name"] == "S2"
    assert result[2]["name"] == "S1"


# ---------------------------------------------------------------------------
# get_filter_jql
# ---------------------------------------------------------------------------


def test_get_filter_jql_none(monkeypatch, mock_jira):
    monkeypatch.setattr("app.core.config.JIRA_FILTER_ID", None)
    assert jira_client.get_filter_jql(mock_jira) == ""


def test_get_filter_jql_valid(monkeypatch, mock_jira):
    monkeypatch.setattr("app.core.config.JIRA_FILTER_ID", 123)
    mock_jira.get_filter.return_value = {"jql": "project = MYPROJ"}
    assert jira_client.get_filter_jql(mock_jira) == "project = MYPROJ"


def test_get_filter_jql_api_error(monkeypatch, mock_jira):
    monkeypatch.setattr("app.core.config.JIRA_FILTER_ID", 123)
    mock_jira.get_filter.side_effect = Exception("API error")
    assert jira_client.get_filter_jql(mock_jira) == ""


# ---------------------------------------------------------------------------
# get_issues_for_sprint
# ---------------------------------------------------------------------------


def test_get_issues_for_sprint_single_page(mock_jira):
    mock_jira.get_all_issues_for_sprint_in_board.return_value = {
        "issues": [{"key": "T-1"}, {"key": "T-2"}],
        "total": 2,
    }
    result = jira_client.get_issues_for_sprint(mock_jira, 1, 10)
    assert len(result) == 2


def test_get_issues_for_sprint_pagination(mock_jira):
    mock_jira.get_all_issues_for_sprint_in_board.side_effect = [
        {"issues": [{"key": f"T-{i}"} for i in range(50)], "total": 75},
        {"issues": [{"key": f"T-{i}"} for i in range(50, 75)], "total": 75},
    ]
    result = jira_client.get_issues_for_sprint(mock_jira, 1, 10)
    assert len(result) == 75


def test_get_issues_for_sprint_empty(mock_jira):
    mock_jira.get_all_issues_for_sprint_in_board.return_value = {"issues": [], "total": 0}
    assert jira_client.get_issues_for_sprint(mock_jira, 1, 10) == []


# ---------------------------------------------------------------------------
# fetch_kanban_data
# ---------------------------------------------------------------------------


def test_fetch_kanban_data_jql_uses_resolutiondate(mock_jira, monkeypatch):
    """fetch_kanban_data() must group issues by resolutiondate, not created."""
    monkeypatch.setattr("app.core.config.JIRA_SPRINT_COUNT", 1)
    monkeypatch.setattr(jira_client, "get_board_id", lambda jira: 1)
    mock_jira.jql.return_value = {"issues": [], "total": 0}

    jira_client.fetch_kanban_data(mock_jira)

    called_jql = mock_jira.jql.call_args[0][0]
    assert "resolutiondate" in called_jql
    assert "created" not in called_jql


# ---------------------------------------------------------------------------
# fetch_sprint_data
# ---------------------------------------------------------------------------


def test_fetch_sprint_data_orchestration(monkeypatch, mock_jira):
    monkeypatch.setattr("app.core.config.JIRA_BOARD_ID", 5)
    monkeypatch.setattr("app.core.config.JIRA_FILTER_ID", None)
    monkeypatch.setattr("app.core.config.JIRA_SPRINT_COUNT", 10)
    mock_jira.get_all_sprints_from_board.side_effect = [
        {"values": [{"id": 10, "name": "S10", "startDate": "2026-01-01"}]},
        {"values": []},
    ]
    mock_jira.get_all_issues_for_sprint_in_board.return_value = {
        "issues": [{"key": "T-1"}],
        "total": 1,
    }

    sprints, sprint_issues = jira_client.fetch_sprint_data(mock_jira)
    assert len(sprints) == 1
    assert 10 in sprint_issues
    assert len(sprint_issues[10]) == 1


def test_fetch_sprint_data_passes_filter_jql_to_each_sprint(monkeypatch, mock_jira):
    sprints = [
        make_sprint(10, "Sprint 10", "2026-01-01", "2026-01-14"),
        make_sprint(11, "Sprint 11", "2026-01-15", "2026-01-28"),
    ]

    monkeypatch.setattr(jira_client, "get_board_id", lambda jira: 5)
    monkeypatch.setattr(jira_client, "get_sprints", lambda jira, board_id: sprints)
    monkeypatch.setattr(jira_client, "get_filter_jql", lambda jira: "project = TEST")

    captured_calls = []

    def _fake_get_issues(jira, board_id, sprint_id, jql=""):
        captured_calls.append((board_id, sprint_id, jql))
        return [{"key": f"T-{sprint_id}"}]

    monkeypatch.setattr(jira_client, "get_issues_for_sprint", _fake_get_issues)

    fetched_sprints, sprint_issues = jira_client.fetch_sprint_data(mock_jira)

    assert fetched_sprints == sprints
    assert captured_calls == [
        (5, 10, "project = TEST"),
        (5, 11, "project = TEST"),
    ]
    assert sprint_issues == {
        10: [{"key": "T-10"}],
        11: [{"key": "T-11"}],
    }


def test_fetch_sprint_data_skips_sprints_without_id(monkeypatch, mock_jira):
    monkeypatch.setattr(jira_client, "get_board_id", lambda jira: 5)
    monkeypatch.setattr(
        jira_client,
        "get_sprints",
        lambda jira, board_id: [
            {"name": "No Id Sprint"},
            make_sprint(12, "Sprint 12", "2026-02-01", "2026-02-14"),
        ],
    )
    monkeypatch.setattr(jira_client, "get_filter_jql", lambda jira: "")

    captured_sprint_ids = []

    def _fake_get_issues(jira, board_id, sprint_id, jql=""):
        captured_sprint_ids.append(sprint_id)
        return [{"key": "T-12"}]

    monkeypatch.setattr(jira_client, "get_issues_for_sprint", _fake_get_issues)

    sprints, sprint_issues = jira_client.fetch_sprint_data(mock_jira)

    assert len(sprints) == 2
    assert captured_sprint_ids == [12]
    assert sprint_issues == {12: [{"key": "T-12"}]}


# ---------------------------------------------------------------------------
# TR-39: Credentials transmitted only to JIRA_URL, never leaked
# ---------------------------------------------------------------------------


def test_create_client_url_kwarg_matches_config_exactly(monkeypatch):
    """The 'url' keyword passed to Jira() must be exactly the configured JIRA_URL."""
    monkeypatch.setattr("app.core.config.JIRA_URL", "https://secure.atlassian.net")
    monkeypatch.setattr("app.core.config.JIRA_EMAIL", "user@test.com")
    monkeypatch.setattr("app.core.config.JIRA_API_TOKEN", "tok")
    monkeypatch.setattr("app.core.config.JIRA_SSL_CERT", True)
    with patch("app.core.jira_client.Jira") as MockJira:
        jira_client.create_client()
        kwargs = MockJira.call_args.kwargs
        assert kwargs["url"] == "https://secure.atlassian.net"


def test_create_client_no_credentials_in_url_kwarg(monkeypatch):
    """Credentials must NOT appear embedded in the url parameter."""
    monkeypatch.setattr("app.core.config.JIRA_URL", "https://corp.atlassian.net")
    monkeypatch.setattr("app.core.config.JIRA_EMAIL", "leaky@test.com")
    monkeypatch.setattr("app.core.config.JIRA_API_TOKEN", "supersecret")
    monkeypatch.setattr("app.core.config.JIRA_SSL_CERT", True)
    with patch("app.core.jira_client.Jira") as MockJira:
        jira_client.create_client()
        url_kwarg = MockJira.call_args.kwargs["url"]
        assert "leaky@test.com" not in url_kwarg
        assert "supersecret" not in url_kwarg


def test_create_client_credentials_in_auth_kwargs_only(monkeypatch):
    """Username and password must be passed as separate kwargs, not embedded anywhere else."""
    monkeypatch.setattr("app.core.config.JIRA_URL", "https://corp.atlassian.net")
    monkeypatch.setattr("app.core.config.JIRA_EMAIL", "user@corp.com")
    monkeypatch.setattr("app.core.config.JIRA_API_TOKEN", "secret_token_42")
    monkeypatch.setattr("app.core.config.JIRA_SSL_CERT", True)
    with patch("app.core.jira_client.Jira") as MockJira:
        jira_client.create_client()
        kwargs = MockJira.call_args.kwargs
        assert kwargs["username"] == "user@corp.com"
        assert kwargs["password"] == "secret_token_42"
        # Ensure only the expected keys are passed
        assert set(kwargs.keys()) == {"url", "username", "password", "verify_ssl", "timeout"}


# ── NFR-P-001: Jira client timeout ──────────────────────────────────────


def test_create_client_passes_timeout(monkeypatch):
    """create_client() must pass timeout=55 to the Jira constructor."""
    monkeypatch.setattr("app.core.config.JIRA_URL", "https://j.atlassian.net")
    monkeypatch.setattr("app.core.config.JIRA_EMAIL", "a@b.com")
    monkeypatch.setattr("app.core.config.JIRA_API_TOKEN", "tok")
    monkeypatch.setattr("app.core.config.JIRA_SSL_CERT", True)
    with patch("app.core.jira_client.Jira") as MockJira:
        jira_client.create_client()
        assert MockJira.call_args.kwargs["timeout"] == 55


# ── NFR-S-006: _sanitise_error ──────────────────────────────────────────


def test_sanitise_error_replaces_url(monkeypatch):
    """Jira URL must be masked in error messages."""
    monkeypatch.setattr("app.core.config.JIRA_URL", "https://corp.atlassian.net")
    monkeypatch.setattr("app.core.config.JIRA_EMAIL", "")
    monkeypatch.setattr("app.core.config.JIRA_API_TOKEN", "")
    result = jira_client._sanitise_error("Cannot reach https://corp.atlassian.net/rest/api")
    assert "corp.atlassian.net" not in result
    assert "***" in result


def test_sanitise_error_replaces_email_and_token(monkeypatch):
    """Email and API token must be masked."""
    monkeypatch.setattr("app.core.config.JIRA_URL", "")
    monkeypatch.setattr("app.core.config.JIRA_EMAIL", "user@secret.com")
    monkeypatch.setattr("app.core.config.JIRA_API_TOKEN", "ATATT-xyz-123")
    msg = "401 Unauthorized for user@secret.com token=ATATT-xyz-123"
    result = jira_client._sanitise_error(msg)
    assert "user@secret.com" not in result
    assert "ATATT-xyz-123" not in result


def test_sanitise_error_handles_none_config_values(monkeypatch):
    """Empty/None config values must not cause errors."""
    monkeypatch.setattr("app.core.config.JIRA_URL", None)
    monkeypatch.setattr("app.core.config.JIRA_EMAIL", "")
    monkeypatch.setattr("app.core.config.JIRA_API_TOKEN", None)
    result = jira_client._sanitise_error("some error message")
    assert result == "some error message"
