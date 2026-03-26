"""Jira Cloud API client wrapper for fetching boards, sprints, and issues."""
from __future__ import annotations

import logging
from typing import Any

from atlassian import Jira

from app import config

logger = logging.getLogger(__name__)


def create_client() -> Jira:
    """Create and return an authenticated Jira client."""
    return Jira(
        url=config.JIRA_URL,
        username=config.JIRA_EMAIL,
        password=config.JIRA_API_TOKEN,
        verify_ssl=config.JIRA_SSL_CERT,
    )


def get_board_id(jira: Jira) -> int:
    """Return the board ID to use (config or first available board)."""
    if config.JIRA_BOARD_ID is not None:
        return config.JIRA_BOARD_ID
    result = jira.get_all_agile_boards(start=0, limit=1)
    values = result.get("values") or []
    if not values:
        raise ValueError("No boards found. Set JIRA_BOARD_ID or use an account with board access.")
    return int(values[0]["id"])


def get_sprints(jira: Jira, board_id: int) -> list[dict[str, Any]]:
    """Return recent sprints for the board (closed + active), limited by JIRA_SPRINT_COUNT."""
    # Fetch closed first, then active
    result_closed = jira.get_all_sprints_from_board(
        board_id, state="closed", start=0, limit=config.JIRA_SPRINT_COUNT
    )
    result_active = jira.get_all_sprints_from_board(
        board_id, state="active", start=0, limit=10
    )
    closed = result_closed.get("values") or []
    active = result_active.get("values") or []
    ordered = sorted(closed, key=lambda s: s.get("startDate") or "", reverse=True)
    ordered = (ordered + active)[: config.JIRA_SPRINT_COUNT]
    return ordered


def get_filter_jql(jira: Jira) -> str:
    """Return the JQL string for the configured filter ID, or empty string if not set."""
    if config.JIRA_FILTER_ID is None:
        return ""
    try:
        f = jira.get_filter(config.JIRA_FILTER_ID)
        return (f.get("jql") or "").strip()
    except Exception:
        return ""


def get_issues_for_sprint(jira: Jira, board_id: int, sprint_id: int, jql: str = "") -> list[dict[str, Any]]:
    """Return all issues in the sprint (paginated). If jql is set, only issues matching that JQL are returned."""
    all_issues: list[dict[str, Any]] = []
    start = 0
    limit = 50
    while True:
        result = jira.get_all_issues_for_sprint_in_board(
            board_id, sprint_id, jql=jql, start=start, limit=limit
        )
        issues = result.get("issues") or []
        all_issues.extend(issues)
        total = result.get("total", 0)
        if start + len(issues) >= total or len(issues) == 0:
            break
        start += len(issues)
    return all_issues


def get_issue_with_changelog(jira: Jira, issue_key: str) -> dict[str, Any]:
    """Fetch a single issue with changelog for cycle time calculation."""
    return jira.get_issue(issue_key, expand="changelog")


def get_issues_with_changelog(
    jira: Jira, issue_keys: list[str]
) -> list[dict[str, Any]]:
    """Fetch multiple issues with changelog. Returns list in same order as keys."""
    out = []
    for key in issue_keys:
        try:
            out.append(get_issue_with_changelog(jira, key))
        except Exception as exc:
            logger.warning("Failed to fetch changelog for %s: %s", key, exc)
            out.append({})  # Skip failed issues; metrics can tolerate missing
    return out


def fetch_sprint_data(jira: Jira) -> tuple[list[dict[str, Any]], dict[int, list[dict[str, Any]]]]:
    """
    Fetch sprints and their issues for the configured board.
    If JIRA_FILTER_ID is set, only issues matching that filter's JQL are included.
    Returns (sprints_list, sprint_id -> list of issue dicts).
    """
    board_id = get_board_id(jira)
    sprints = get_sprints(jira, board_id)
    filter_jql = get_filter_jql(jira)
    sprint_issues: dict[int, list[dict[str, Any]]] = {}
    for sprint in sprints:
        sid = sprint.get("id")
        if sid is None:
            continue
        issues = get_issues_for_sprint(jira, board_id, sid, jql=filter_jql)
        sprint_issues[sid] = issues
    return sprints, sprint_issues
