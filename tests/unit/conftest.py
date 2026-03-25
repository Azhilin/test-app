"""Unit-layer fixtures."""
from __future__ import annotations

import pytest


@pytest.fixture
def mock_jira():
    """Return a MagicMock with spec=Jira and common stubs."""
    from unittest.mock import MagicMock
    from atlassian import Jira

    jira = MagicMock(spec=Jira)
    jira.get_all_agile_boards.return_value = {"values": [{"id": 1, "name": "Board 1"}]}
    jira.get_all_sprints_from_board.return_value = {"values": []}
    jira.get_all_issues_for_sprint_in_board.return_value = {"issues": [], "total": 0}
    jira.get_filter.return_value = {"jql": "project = TEST"}
    jira.get_issue.return_value = {"key": "TEST-1", "fields": {}, "changelog": {"histories": []}}
    return jira
