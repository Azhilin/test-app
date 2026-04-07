"""Jira Cloud API client wrapper for fetching boards, sprints, and issues."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
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
    """Return the configured board ID. Raises if JIRA_BOARD_ID is not set."""
    if config.JIRA_BOARD_ID is not None:
        logger.debug("Using configured board ID: %s", config.JIRA_BOARD_ID)
        return config.JIRA_BOARD_ID
    raise ValueError(
        "JIRA_BOARD_ID is not set. Add it to config/defaults.env or .env."
    )


def get_sprints(jira: Jira, board_id: int) -> list[dict[str, Any]]:
    """Return recent sprints for the board, limited by JIRA_SPRINT_COUNT.
    When JIRA_CLOSED_SPRINTS_ONLY is True (default), only closed sprints are returned.
    """
    logger.debug("Fetching sprints for board %s (limit=%s)", board_id, config.JIRA_SPRINT_COUNT)
    # Paginate through ALL closed sprints so we can sort and take the NEWEST ones.
    # A single limited fetch returns the oldest sprints first, not the most recent.
    all_closed: list[dict[str, Any]] = []
    start = 0
    page_size = 50
    while True:
        result = jira.get_all_sprints_from_board(board_id, state="closed", start=start, limit=page_size)
        if result is None:
            break
        values = result.get("values") or []
        all_closed.extend(values)
        if result.get("isLast", False) or len(values) < page_size:
            break
        start += page_size
    result_active = jira.get_all_sprints_from_board(board_id, state="active", start=0, limit=10)
    active = (result_active.get("values") or []) if result_active is not None else []
    ordered = sorted(all_closed, key=lambda s: s.get("startDate") or "", reverse=True)
    if not config.JIRA_CLOSED_SPRINTS_ONLY:
        ordered = (active + ordered)[: config.JIRA_SPRINT_COUNT]
    else:
        ordered = ordered[: config.JIRA_SPRINT_COUNT]
    logger.debug("Fetched %s sprint(s) (%s closed fetched, %s active)", len(ordered), len(all_closed), len(active))
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


def fetch_kanban_data(jira: Jira) -> tuple[list[dict[str, Any]], dict[int | str, list[dict[str, Any]]]]:
    """
    Fetch KANBAN board data grouped by time periods (weeks) instead of sprints.
    Returns a tuple of (periods_list, period_id -> list of issues) with same shape as fetch_sprint_data.
    Each period represents an ISO week going backward from today.
    If JIRA_FILTER_ID is set, only issues matching that filter's JQL are included.
    """
    board_id = get_board_id(jira)
    logger.debug("Fetching KANBAN data for board %s (as time periods)", board_id)

    # Note: board_info could be fetched here for logging, but it's optional

    # Create synthetic time periods (weeks going backward from today)
    today = datetime.utcnow().date()
    periods: list[dict[str, Any]] = []
    period_issues: dict[int | str, list[dict[str, Any]]] = {}

    filter_jql = get_filter_jql(jira)
    if filter_jql:
        logger.debug("Applying filter JQL: %s", filter_jql)

    for week_offset in range(config.JIRA_SPRINT_COUNT):
        # Calculate the week start and end dates
        week_end = today - timedelta(days=week_offset * 7)
        week_start = week_end - timedelta(days=6)
        week_num = week_start.isocalendar()[1]
        week_year = week_start.isocalendar()[0]
        period_label = f"{week_year}-W{week_num:02d}"
        period_id = f"week-{period_label}"

        # Build JQL to fetch issues resolved/completed in this week
        jql_date_range = f'resolutiondate >= "{week_start}" AND resolutiondate <= "{week_end}"'
        combined_jql = jql_date_range
        if filter_jql:
            combined_jql = f"({jql_date_range}) AND ({filter_jql})"

        # Fetch issues for this period
        all_issues: list[dict[str, Any]] = []
        start = 0
        limit = 50
        logger.debug("Fetching issues for period %s (jql=%r)", period_label, combined_jql)
        while True:
            try:
                result = jira.jql(combined_jql, start=start, limit=limit)
                if result is None:
                    break
                issues = result.get("issues") or []
                all_issues.extend(issues)
                total = result.get("total", 0)
                if start + len(issues) >= total or len(issues) == 0:
                    break
                start += limit
            except Exception as exc:
                logger.warning("Error fetching issues for period %s: %s", period_label, _sanitise_error(str(exc)))
                break

        period_issues[period_id] = all_issues
        periods.append(
            {
                "id": period_id,
                "name": period_label,
                "state": "closed",  # KANBAN periods are always "closed" (historical)
                "startDate": str(week_start),
                "endDate": str(week_end),
            }
        )
        logger.debug("Period %s: fetched %s issue(s)", period_label, len(all_issues))

    total_issues = sum(len(v) for v in period_issues.values())
    logger.debug(
        "KANBAN data ready: %s period(s), %s total issue(s)",
        len(periods),
        total_issues,
    )
    return periods, period_issues
