"""Compute velocity, cycle time, and custom metric trends from Jira data."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import config


def _parse_iso(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def _get_story_points(issue: dict[str, Any]) -> float:
    """Extract story points from issue fields. Returns 0 if missing or non-numeric."""
    fields = issue.get("fields") or {}
    raw = fields.get(config.JIRA_STORY_POINTS_FIELD)
    if raw is None:
        return 0.0
    try:
        return float(raw)
    except (TypeError, ValueError):
        return 0.0


def _is_done(issue: dict[str, Any]) -> bool:
    """True if issue is in a Done/Resolved-like status."""
    fields = issue.get("fields") or {}
    status = fields.get("status") or {}
    name = (status.get("name") or "").lower()
    return name in ("done", "closed", "resolved", "complete")


def compute_velocity(
    sprints: list[dict[str, Any]],
    sprint_issues: dict[int, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    """
    Velocity per sprint: sum of story points for completed issues.
    Returns list of {sprint_id, sprint_name, start_date, end_date, velocity, issue_count}.
    """
    rows = []
    for sprint in sprints:
        sid = sprint.get("id")
        if sid is None:
            continue
        issues = sprint_issues.get(sid) or []
        points = 0.0
        count = 0
        for iss in issues:
            if _is_done(iss):
                points += _get_story_points(iss)
                count += 1
        rows.append({
            "sprint_id": sid,
            "sprint_name": sprint.get("name") or f"Sprint {sid}",
            "start_date": sprint.get("startDate"),
            "end_date": sprint.get("endDate"),
            "velocity": round(points, 1),
            "issue_count": count,
        })
    return rows


def _cycle_time_from_changelog(issue: dict[str, Any]) -> float | None:
    """
    Cycle time in days: from first transition into "In Progress" (or similar) to "Done".
    Uses changelog; returns None if not computable.
    """
    histories = (issue.get("changelog") or {}).get("histories") or []
    in_progress_at: datetime | None = None
    done_at: datetime | None = None
    done_statuses = {"done", "closed", "resolved", "complete"}

    for h in histories:
        created = _parse_iso(h.get("created"))
        if not created:
            continue
        for item in h.get("items") or []:
            if item.get("field") != "status":
                continue
            to_val = (item.get("toString") or "").lower()
            from_val = (item.get("fromString") or "").lower()
            if in_progress_at is None and (
                "progress" in to_val or "in progress" in to_val or to_val == "in progress"
            ):
                in_progress_at = created
            if to_val in done_statuses:
                done_at = created
                break

    if in_progress_at is not None and done_at is not None and done_at >= in_progress_at:
        delta = done_at - in_progress_at
        return round(delta.total_seconds() / (24 * 3600), 1)
    return None


def compute_cycle_time(issues_with_changelog: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Cycle time stats across issues. issues_with_changelog: list from get_issue(expand="changelog").
    Returns {mean_days, median_days, min_days, max_days, sample_size, values (list of days)}.
    """
    values: list[float] = []
    for issue in issues_with_changelog:
        if not issue.get("key"):
            continue
        days = _cycle_time_from_changelog(issue)
        if days is not None:
            values.append(days)
    if not values:
        return {
            "mean_days": None,
            "median_days": None,
            "min_days": None,
            "max_days": None,
            "sample_size": 0,
            "values": [],
        }
    n = len(values)
    sorted_vals = sorted(values)
    mean_days = round(sum(values) / n, 1)
    median_days = round(sorted_vals[n // 2] if n % 2 else (sorted_vals[n // 2 - 1] + sorted_vals[n // 2]) / 2, 1)
    return {
        "mean_days": mean_days,
        "median_days": median_days,
        "min_days": round(min(values), 1),
        "max_days": round(max(values), 1),
        "sample_size": n,
        "values": sorted_vals,
    }


def get_done_issue_keys_for_changelog(
    sprints: list[dict[str, Any]],
    sprint_issues: dict[int, list[dict[str, Any]]],
    max_count: int = 100,
) -> list[str]:
    """Return issue keys of done issues (for changelog fetch), up to max_count, recent first."""
    seen: set[str] = set()
    keys: list[str] = []
    for sprint in reversed(sprints):
        sid = sprint.get("id")
        if sid is None:
            continue
        for iss in sprint_issues.get(sid) or []:
            if _is_done(iss) and len(keys) < max_count:
                key = (iss.get("key") or "").strip()
                if key and key not in seen:
                    seen.add(key)
                    keys.append(key)
        if len(keys) >= max_count:
            break
    return keys


def compute_custom_trends(
    _sprints: list[dict[str, Any]],
    _sprint_issues: dict[int, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    """
    Placeholder for custom metric trends. Extend with your custom field and aggregation.
    Returns list of {sprint_id, sprint_name, <custom_metric_key>: value}.
    """
    return []


def build_metrics_dict(
    sprints: list[dict[str, Any]],
    sprint_issues: dict[int, list[dict[str, Any]]],
    issues_with_changelog: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build the single metrics dict used by both HTML and MD reporters."""
    velocity = compute_velocity(sprints, sprint_issues)
    cycle_time = compute_cycle_time(issues_with_changelog)
    custom = compute_custom_trends(sprints, sprint_issues)
    return {
        "velocity": velocity,
        "cycle_time": cycle_time,
        "custom_trends": custom,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
