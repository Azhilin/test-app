"""Jira Cloud API client wrapper for fetching boards, sprints, and issues."""

from __future__ import annotations

import logging
from typing import Any

from atlassian import Jira

from app.core import config

logger = logging.getLogger(__name__)


def _sanitise_error(msg: str) -> str:
    """Replace known sensitive config values with *** in error strings."""
    for sensitive in (config.JIRA_URL, config.JIRA_EMAIL, config.JIRA_API_TOKEN):
        if sensitive:
            msg = msg.replace(sensitive, "***")
    return msg


def create_client() -> Jira:
    """Create and return an authenticated Jira client."""
    return Jira(
        url=config.JIRA_URL,
        username=config.JIRA_EMAIL,
        password=config.JIRA_API_TOKEN,
        verify_ssl=config.JIRA_SSL_CERT,
        timeout=55,
    )


def get_board_id(jira: Jira) -> int:
    """Return the board ID to use (config or first available board)."""
    if config.JIRA_BOARD_ID is not None:
        logger.debug("Using configured board ID: %s", config.JIRA_BOARD_ID)
        return config.JIRA_BOARD_ID
    logger.debug("No JIRA_BOARD_ID configured; fetching first available board")
    result = jira.get_all_agile_boards(start=0, limit=1)
    if result is None:
        raise ValueError("No boards found. Set JIRA_BOARD_ID or use an account with board access.")
    values = result.get("values") or []
    if not values:
        raise ValueError("No boards found. Set JIRA_BOARD_ID or use an account with board access.")
    board_id = int(values[0]["id"])
    logger.debug("Resolved board ID: %s", board_id)
    return board_id


def get_sprints(jira: Jira, board_id: int) -> list[dict[str, Any]]:
    """Return recent sprints for the board (closed + active), limited by JIRA_SPRINT_COUNT."""
    # Fetch closed first, then active
    logger.debug("Fetching sprints for board %s (limit=%s)", board_id, config.JIRA_SPRINT_COUNT)
    result_closed = jira.get_all_sprints_from_board(board_id, state="closed", start=0, limit=config.JIRA_SPRINT_COUNT)
    result_active = jira.get_all_sprints_from_board(board_id, state="active", start=0, limit=10)
    closed = (result_closed.get("values") or []) if result_closed is not None else []
    active = (result_active.get("values") or []) if result_active is not None else []
    ordered = sorted(closed, key=lambda s: s.get("startDate") or "", reverse=True)
    ordered = (ordered + active)[: config.JIRA_SPRINT_COUNT]
    logger.debug("Fetched %s sprint(s) (%s closed, %s active)", len(ordered), len(closed), len(active))
    return ordered


def get_filter_jql(jira: Jira) -> str:
    """Return the JQL string for the configured filter ID, or empty string if not set."""
    if config.JIRA_FILTER_ID is None:
        return ""
    try:
        f = jira.get_filter(config.JIRA_FILTER_ID)
        return (f.get("jql") or "").strip()
    except Exception as exc:
        logger.warning("Could not fetch JQL for filter %s: %s", config.JIRA_FILTER_ID, _sanitise_error(str(exc)))
        return ""


def get_issues_for_sprint(jira: Jira, board_id: int, sprint_id: int, jql: str = "") -> list[dict[str, Any]]:
    """Return all issues in the sprint (paginated). If jql is set, only issues matching that JQL are returned."""
    all_issues: list[dict[str, Any]] = []
    start = 0
    limit = 50
    logger.debug("Fetching issues for sprint %s (board %s, jql=%r)", sprint_id, board_id, jql or "")
    while True:
        result = jira.get_all_issues_for_sprint_in_board(board_id, sprint_id, jql=jql, start=start, limit=limit)
        if result is None:
            break
        issues = result.get("issues") or []
        all_issues.extend(issues)
        total = result.get("total", 0)
        if start + len(issues) >= total or len(issues) == 0:
            break
        start += len(issues)
    logger.debug("Sprint %s: fetched %s issue(s)", sprint_id, len(all_issues))
    return all_issues


def get_issue_with_changelog(jira: Jira, issue_key: str) -> dict[str, Any]:
    """Fetch a single issue with changelog for cycle time calculation."""
    return jira.get_issue(issue_key, expand="changelog")


def get_issues_with_changelog(jira: Jira, issue_keys: list[str]) -> list[dict[str, Any]]:
    """Fetch multiple issues with changelog. Returns list in same order as keys."""
    logger.debug("Fetching changelog for %s issue(s)", len(issue_keys))
    out = []
    failures = 0
    for key in issue_keys:
        try:
            out.append(get_issue_with_changelog(jira, key))
        except Exception as exc:
            logger.warning("Failed to fetch changelog for %s: %s", key, _sanitise_error(str(exc)))
            failures += 1
            out.append({})  # Skip failed issues; metrics can tolerate missing
    logger.debug(
        "Changelog fetch complete: %s succeeded, %s failed",
        len(issue_keys) - failures,
        failures,
    )
    return out


def fetch_sprint_data(jira: Jira) -> tuple[list[dict[str, Any]], dict[int | str, list[dict[str, Any]]]]:
    """
    Fetch sprints and their issues for the configured board.
    If JIRA_FILTER_ID is set, only issues matching that filter's JQL are included.
    Returns (sprints_list, sprint_id -> list of issue dicts).
    """
    board_id = get_board_id(jira)
    logger.debug("Fetching sprint data for board %s", board_id)
    sprints = get_sprints(jira, board_id)
    filter_jql = get_filter_jql(jira)
    if filter_jql:
        logger.debug("Applying filter JQL: %s", filter_jql)
    sprint_issues: dict[int | str, list[dict[str, Any]]] = {}
    for sprint in sprints:
        sid = sprint.get("id")
        if sid is None:
            continue
        issues = get_issues_for_sprint(jira, board_id, sid, jql=filter_jql)
        sprint_issues[sid] = issues
    total_issues = sum(len(v) for v in sprint_issues.values())
    logger.debug(
        "Sprint data ready: %s sprint(s), %s total issue(s)",
        len(sprints),
        total_issues,
    )
    return sprints, sprint_issues
