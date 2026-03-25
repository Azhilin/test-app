"""Tests for app.jira_client: Jira API wrapper (all Jira calls mocked)."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from atlassian import Jira

from app import jira_client
from tests.conftest import make_sprint

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# create_client
# ---------------------------------------------------------------------------

def test_create_client_returns_jira_instance(monkeypatch):
    monkeypatch.setattr("app.config.JIRA_URL", "https://test.atlassian.net")
    monkeypatch.setattr("app.config.JIRA_EMAIL", "user@test.com")
    monkeypatch.setattr("app.config.JIRA_API_TOKEN", "tok123")
    with patch("app.jira_client.Jira") as MockJira:
        jira_client.create_client()
        MockJira.assert_called_once_with(
            url="https://test.atlassian.net",
            username="user@test.com",
            password="tok123",
        )


def test_create_client_uses_config_values(monkeypatch):
    monkeypatch.setattr("app.config.JIRA_URL", "https://other.atlassian.net")
    monkeypatch.setattr("app.config.JIRA_EMAIL", "other@test.com")
    monkeypatch.setattr("app.config.JIRA_API_TOKEN", "other_tok")
    with patch("app.jira_client.Jira") as MockJira:
        jira_client.create_client()
        args = MockJira.call_args
        assert args.kwargs["url"] == "https://other.atlassian.net"
        assert args.kwargs["username"] == "other@test.com"


# ---------------------------------------------------------------------------
# get_board_id
# ---------------------------------------------------------------------------

def test_get_board_id_from_config(monkeypatch, mock_jira):
    monkeypatch.setattr("app.config.JIRA_BOARD_ID", 42)
    assert jira_client.get_board_id(mock_jira) == 42
    mock_jira.get_all_agile_boards.assert_not_called()


def test_get_board_id_from_api(monkeypatch, mock_jira):
    monkeypatch.setattr("app.config.JIRA_BOARD_ID", None)
    mock_jira.get_all_agile_boards.return_value = {"values": [{"id": 99, "name": "My Board"}]}
    assert jira_client.get_board_id(mock_jira) == 99


def test_get_board_id_no_boards_raises(monkeypatch, mock_jira):
    monkeypatch.setattr("app.config.JIRA_BOARD_ID", None)
    mock_jira.get_all_agile_boards.return_value = {"values": []}
    with pytest.raises(ValueError, match="No boards found"):
        jira_client.get_board_id(mock_jira)


# ---------------------------------------------------------------------------
# get_sprints
# ---------------------------------------------------------------------------

def test_get_sprints_sorted_desc_by_start_date(monkeypatch, mock_jira):
    monkeypatch.setattr("app.config.JIRA_SPRINT_COUNT", 10)
    mock_jira.get_all_sprints_from_board.side_effect = [
        {"values": [
            {"id": 1, "name": "S1", "startDate": "2026-01-01"},
            {"id": 2, "name": "S2", "startDate": "2026-02-01"},
        ]},
        {"values": []},
    ]
    result = jira_client.get_sprints(mock_jira, 1)
    assert result[0]["name"] == "S2"
    assert result[1]["name"] == "S1"


def test_get_sprints_capped_at_sprint_count(monkeypatch, mock_jira):
    monkeypatch.setattr("app.config.JIRA_SPRINT_COUNT", 2)
    mock_jira.get_all_sprints_from_board.side_effect = [
        {"values": [
            {"id": i, "name": f"S{i}", "startDate": f"2026-0{i}-01"}
            for i in range(1, 6)
        ]},
        {"values": []},
    ]
    result = jira_client.get_sprints(mock_jira, 1)
    assert len(result) == 2


def test_get_sprints_empty(monkeypatch, mock_jira):
    monkeypatch.setattr("app.config.JIRA_SPRINT_COUNT", 10)
    mock_jira.get_all_sprints_from_board.side_effect = [
        {"values": []},
        {"values": []},
    ]
    assert jira_client.get_sprints(mock_jira, 1) == []


# ---------------------------------------------------------------------------
# get_filter_jql
# ---------------------------------------------------------------------------

def test_get_filter_jql_none(monkeypatch, mock_jira):
    monkeypatch.setattr("app.config.JIRA_FILTER_ID", None)
    assert jira_client.get_filter_jql(mock_jira) == ""


def test_get_filter_jql_valid(monkeypatch, mock_jira):
    monkeypatch.setattr("app.config.JIRA_FILTER_ID", 123)
    mock_jira.get_filter.return_value = {"jql": "project = MYPROJ"}
    assert jira_client.get_filter_jql(mock_jira) == "project = MYPROJ"


def test_get_filter_jql_api_error(monkeypatch, mock_jira):
    monkeypatch.setattr("app.config.JIRA_FILTER_ID", 123)
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
# get_issue_with_changelog
# ---------------------------------------------------------------------------

def test_get_issue_with_changelog_expand_param(mock_jira):
    jira_client.get_issue_with_changelog(mock_jira, "TEST-1")
    mock_jira.get_issue.assert_called_once_with("TEST-1", expand="changelog")


# ---------------------------------------------------------------------------
# get_issues_with_changelog
# ---------------------------------------------------------------------------

def test_get_issues_with_changelog_multiple_keys(mock_jira):
    mock_jira.get_issue.side_effect = [
        {"key": "T-1", "changelog": {"histories": []}},
        {"key": "T-2", "changelog": {"histories": []}},
    ]
    result = jira_client.get_issues_with_changelog(mock_jira, ["T-1", "T-2"])
    assert len(result) == 2
    assert result[0]["key"] == "T-1"


def test_get_issues_with_changelog_skips_failures(mock_jira):
    mock_jira.get_issue.side_effect = [
        {"key": "T-1", "changelog": {"histories": []}},
        Exception("not found"),
        {"key": "T-3", "changelog": {"histories": []}},
    ]
    result = jira_client.get_issues_with_changelog(mock_jira, ["T-1", "T-2", "T-3"])
    assert len(result) == 3
    assert result[0]["key"] == "T-1"
    assert result[1] == {}  # failed issue returns empty dict
    assert result[2]["key"] == "T-3"


# ---------------------------------------------------------------------------
# fetch_sprint_data
# ---------------------------------------------------------------------------

def test_fetch_sprint_data_orchestration(monkeypatch, mock_jira):
    monkeypatch.setattr("app.config.JIRA_BOARD_ID", 5)
    monkeypatch.setattr("app.config.JIRA_FILTER_ID", None)
    monkeypatch.setattr("app.config.JIRA_SPRINT_COUNT", 10)
    mock_jira.get_all_sprints_from_board.side_effect = [
        {"values": [{"id": 10, "name": "S10", "startDate": "2026-01-01"}]},
        {"values": []},
    ]
    mock_jira.get_all_issues_for_sprint_in_board.return_value = {
        "issues": [{"key": "T-1"}], "total": 1,
    }

    sprints, sprint_issues = jira_client.fetch_sprint_data(mock_jira)
    assert len(sprints) == 1
    assert 10 in sprint_issues
    assert len(sprint_issues[10]) == 1
