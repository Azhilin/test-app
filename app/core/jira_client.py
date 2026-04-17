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
    raise ValueError("JIRA_BOARD_ID is not set. Add it to config/defaults.env or .env.")


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


def _find_period_for_date(date_str: str, periods: list[dict[str, Any]]) -> str | None:
    """Return the period id whose [startDate, endDate] range contains date_str, or None.

    ISO date strings compare correctly as plain strings (YYYY-MM-DD lexicographic order).
    """
    if not date_str or len(date_str) < 10:
        return None
    date_prefix = date_str[:10]
    for period in periods:
        if period["startDate"] <= date_prefix <= period["endDate"]:
            return period["id"]
    return None


def fetch_kanban_data(jira: Jira) -> tuple[list[dict[str, Any]], dict[int | str, list[dict[str, Any]]]]:
    """
    Fetch KANBAN board data grouped by ISO calendar weeks instead of sprints.

    KANBAN strategy (differs from SCRUM):
    - Builds N ISO week periods based on JIRA_SPRINT_COUNT and JIRA_CLOSED_SPRINTS_ONLY.
    - Issues a SINGLE JQL query using `updated >= oldest_period_start` — does not rely on
      `resolutiondate`, which many Jira workflows leave unset on Done issues.
    - Groups each issue into its week by completion date: `resolutiondate` if set, else `updated`.
    - Returns (periods, period_issues) with the same shape as fetch_sprint_data so all
      downstream metrics functions (compute_velocity, compute_ai_assistance_trend, etc.) work
      unchanged for both SCRUM and KANBAN.
    """
    board_id = get_board_id(jira)
    logger.debug("Fetching KANBAN data for board %s (as ISO week periods)", board_id)

    # Align to ISO week boundaries (Monday = weekday 0).
    # JIRA_CLOSED_SPRINTS_ONLY controls whether the current partial week is included.
    today = datetime.utcnow().date()
    current_monday = today - timedelta(days=today.weekday())
    periods: list[dict[str, Any]] = []

    for i in range(config.JIRA_SPRINT_COUNT):
        if config.JIRA_CLOSED_SPRINTS_ONLY:
            # Skip current week; use the N most recently completed ISO weeks.
            week_start = current_monday - timedelta(weeks=i + 1)
            week_end = week_start + timedelta(days=6)
            state = "closed"
        else:
            # Period 0 is the current (possibly partial) week; subsequent periods are complete.
            week_start = current_monday - timedelta(weeks=i)
            week_end = today if i == 0 else week_start + timedelta(days=6)
            state = "active" if i == 0 else "closed"

        iso = week_start.isocalendar()
        period_label = f"{iso[0]}-W{iso[1]:02d}"
        period_id = f"week-{period_label}"
        periods.append(
            {
                "id": period_id,
                "name": period_label,
                "state": state,
                "startDate": str(week_start),
                "endDate": str(week_end),
            }
        )

    # Prefer a Jira-hosted filter; fall back to the local JQL forwarded by the generate handler.
    filter_jql = get_filter_jql(jira) or config.JIRA_FILTER_JQL
    if filter_jql:
        logger.debug("Applying filter JQL: %s", filter_jql)

    # Single JQL query covering the full period window.
    # Use `updated` instead of `resolutiondate` — many Jira workflows (especially team-managed
    # projects) do not set resolutiondate when an issue transitions to a Done-category status.
    oldest_start = periods[-1]["startDate"]
    date_constraint = f'updated >= "{oldest_start}"'
    combined_jql = f"({filter_jql}) AND {date_constraint}" if filter_jql else date_constraint
    logger.debug("Fetching KANBAN issues (jql=%r)", combined_jql)

    # Use the v3 search/jql endpoint (v2 /search was removed from Jira Cloud, returns HTTP 410).
    # Pagination is cursor-based via nextPageToken, not offset-based.
    all_issues: list[dict[str, Any]] = []
    next_page_token: str | None = None
    limit = 50
    search_url = jira.resource_url("search/jql", api_version=3)
    while True:
        try:
            params: dict[str, Any] = {"jql": combined_jql, "fields": "*all", "maxResults": limit}
            if next_page_token is not None:
                params["nextPageToken"] = next_page_token
            result = jira.get(search_url, params=params)
            if result is None:
                break
            issues = result.get("issues") or []
            all_issues.extend(issues)
            next_page_token = result.get("nextPageToken")
            if not next_page_token or len(issues) == 0:
                break
        except Exception as exc:
            logger.warning("Error fetching KANBAN issues: %s", _sanitise_error(str(exc)))
            break

    logger.debug("Fetched %s total KANBAN issue(s)", len(all_issues))

    # Group issues into week periods by their completion date.
    # Use resolutiondate when set (most accurate), else fall back to updated.
    period_issues: dict[int | str, list[dict[str, Any]]] = {p["id"]: [] for p in periods}
    for issue in all_issues:
        fields = issue.get("fields") or {}
        done_date = (fields.get("resolutiondate") or fields.get("updated") or "")[:10]
        pid = _find_period_for_date(done_date, periods)
        if pid is not None:
            period_issues[pid].append(issue)

    placed = sum(len(v) for v in period_issues.values())
    logger.debug("KANBAN data ready: %s period(s), %s issue(s) placed in periods", len(periods), placed)
    return periods, period_issues
