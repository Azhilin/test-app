"""Jira Cloud API client wrapper for fetching boards, sprints, and issues."""
from __future__ import annotations

from typing import Any

from atlassian import Jira

import config


def create_client() -> Jira:
    """Create and return an authenticated Jira client."""
    return Jira(
        url=config.JIRA_URL,
        username=config.JIRA_EMAIL,
        password=config.JIRA_API_TOKEN,
    )


def get_board_id(jira: Jira) -> int:
    """Return the board ID to use (config or first available board)."""
    if config.JIRA_BOARD_ID is not None:
        return config.JIRA_BOARD_ID
    boards = jira.boards()
    if not boards.get("values"):
        raise ValueError("No boards found. Set JIRA_BOARD_ID or use an account with board access.")
    return int(boards["values"][0]["id"])


def get_sprints(jira: Jira, board_id: int) -> list[dict[str, Any]]:
    """Return recent sprints for the board (closed + open), limited by JIRA_SPRINT_COUNT."""
    result = jira.sprints(board_id, extended=True)
    sprints = result.get("values") or []
    # Prefer closed sprints for velocity; include open for current
    closed = [s for s in sprints if s.get("state") == "closed"]
    open_sprints = [s for s in sprints if s.get("state") != "closed"]
    ordered = sorted(closed, key=lambda s: s.get("startDate") or "", reverse=True)
    ordered = (ordered + open_sprints)[: config.JIRA_SPRINT_COUNT]
    return ordered


def get_issues_for_sprint(jira: Jira, board_id: int, sprint_id: int) -> list[dict[str, Any]]:
    """Return issues in the sprint (backlog + completed). Includes basic fields."""
    result = jira.get_sprint_issues(board_id, sprint_id)
    return result.get("issues") or []


def get_issue_with_changelog(jira: Jira, issue_key: str) -> dict[str, Any]:
    """Fetch a single issue with changelog for cycle time calculation."""
    return jira.issue(issue_key, expand="changelog")


def get_issues_with_changelog(
    jira: Jira, issue_keys: list[str]
) -> list[dict[str, Any]]:
    """Fetch multiple issues with changelog. Returns list in same order as keys."""
    out = []
    for key in issue_keys:
        try:
            out.append(get_issue_with_changelog(jira, key))
        except Exception:
            out.append({})  # Skip failed issues; metrics can tolerate missing
    return out


def fetch_sprint_data(jira: Jira) -> tuple[list[dict[str, Any]], dict[int, list[dict[str, Any]]]]:
    """
    Fetch sprints and their issues for the configured board.
    Returns (sprints_list, sprint_id -> list of issue dicts).
    """
    board_id = get_board_id(jira)
    sprints = get_sprints(jira, board_id)
    sprint_issues: dict[int, list[dict[str, Any]]] = {}
    for sprint in sprints:
        sid = sprint.get("id")
        if sid is None:
            continue
        issues = get_issues_for_sprint(jira, board_id, sid)
        sprint_issues[sid] = issues
    return sprints, sprint_issues
