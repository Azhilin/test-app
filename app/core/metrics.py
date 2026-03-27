"""Compute velocity, cycle time, and custom metric trends from Jira data."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.core import config


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
    if isinstance(raw, dict):
        for key in ("value", "number", "estimate", "amount"):
            if key in raw:
                raw = raw[key]
                break
        else:
            return 0.0  # dict with no recognised numeric key
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
        rows.append(
            {
                "sprint_id": sid,
                "sprint_name": sprint.get("name") or f"Sprint {sid}",
                "start_date": sprint.get("startDate"),
                "end_date": sprint.get("endDate"),
                "velocity": round(points, 1),
                "issue_count": count,
            }
        )
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

    for h in sorted(histories, key=lambda item: _parse_iso(item.get("created")) or datetime.max.replace(tzinfo=UTC)):
        created = _parse_iso(h.get("created"))
        if not created:
            continue
        for item in h.get("items") or []:
            if item.get("field") != "status":
                continue
            to_val = (item.get("toString") or "").lower()
            if in_progress_at is None and ("progress" in to_val or "in progress" in to_val or to_val == "in progress"):
                in_progress_at = created
            if in_progress_at is not None and to_val in done_statuses:
                done_at = created
                break
        if in_progress_at is not None and done_at is not None:
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


def _get_labels(issue: dict[str, Any]) -> list[str]:
    """Return the list of label strings on an issue (empty if absent)."""
    fields = issue.get("fields") or {}
    labels = fields.get("labels") or []
    return [str(lbl) for lbl in labels if lbl]


def compute_ai_assistance_trend(
    sprints: list[dict[str, Any]],
    sprint_issues: dict[int, list[dict[str, Any]]],
    ai_assisted_label: str | None = None,
    ai_exclude_labels: list[str] | None = None,
) -> list[dict[str, Any]]:
    """
    Per-sprint AI assistance percentage.

    For each sprint counts done-issue story points:
    - total_sp: all done issues excluding those with any ai_exclude_labels
    - ai_sp: done issues that carry ai_assisted_label (and are not excluded)
    - ai_pct: ai_sp / total_sp * 100, rounded to 1 dp

    Returns list of {sprint_id, sprint_name, start_date, end_date, total_sp, ai_sp, ai_pct}.
    """
    if ai_assisted_label is None:
        ai_assisted_label = config.AI_ASSISTED_LABEL
    if ai_exclude_labels is None:
        ai_exclude_labels = config.AI_EXCLUDE_LABELS

    exclude_set = set(ai_exclude_labels or [])
    rows = []
    for sprint in sprints:
        sid = sprint.get("id")
        if sid is None:
            continue
        issues = sprint_issues.get(sid) or []
        total_sp = 0.0
        ai_sp = 0.0
        for iss in issues:
            if not _is_done(iss):
                continue
            labels = _get_labels(iss)
            if exclude_set and exclude_set.intersection(labels):
                continue
            pts = _get_story_points(iss)
            total_sp += pts
            if ai_assisted_label in labels:
                ai_sp += pts
        ai_pct = round(ai_sp / total_sp * 100, 1) if total_sp > 0 else 0.0
        rows.append(
            {
                "sprint_id": sid,
                "sprint_name": sprint.get("name") or f"Sprint {sid}",
                "start_date": sprint.get("startDate"),
                "end_date": sprint.get("endDate"),
                "total_sp": round(total_sp, 1),
                "ai_sp": round(ai_sp, 1),
                "ai_pct": ai_pct,
            }
        )
    return rows


def compute_ai_usage_details(
    sprints: list[dict[str, Any]],
    sprint_issues: dict[int, list[dict[str, Any]]],
    ai_assisted_label: str | None = None,
    ai_tool_labels: list[str] | None = None,
    ai_action_labels: list[str] | None = None,
) -> dict[str, Any]:
    """
    Aggregate AI tool and use-case breakdown across all done AI-assisted issues.

    Returns {ai_assisted_issue_count, tool_breakdown: [{label, count, pct}], action_breakdown: [...]}.
    Slices are sorted descending by count. Issues not matching any configured label are excluded
    from the respective breakdown (intentionally — keeps pie charts clean).
    """
    if ai_assisted_label is None:
        ai_assisted_label = config.AI_ASSISTED_LABEL
    if ai_tool_labels is None:
        ai_tool_labels = config.AI_TOOL_LABELS
    if ai_action_labels is None:
        ai_action_labels = config.AI_ACTION_LABELS

    seen_keys: set[str] = set()
    ai_issues: list[dict[str, Any]] = []
    for sprint in sprints:
        sid = sprint.get("id")
        if sid is None:
            continue
        for iss in sprint_issues.get(sid) or []:
            key = iss.get("key") or ""
            if not _is_done(iss) or key in seen_keys:
                continue
            if ai_assisted_label in _get_labels(iss):
                seen_keys.add(key)
                ai_issues.append(iss)

    total = len(ai_issues)

    def _breakdown(label_list: list[str]) -> list[dict[str, Any]]:
        counts: dict[str, int] = {lbl: 0 for lbl in label_list}
        for iss in ai_issues:
            for lbl in _get_labels(iss):
                if lbl in counts:
                    counts[lbl] += 1
        rows = [
            {"label": lbl, "count": cnt, "pct": round(cnt / total * 100, 1) if total else 0.0}
            for lbl, cnt in counts.items()
            if cnt > 0
        ]
        return sorted(rows, key=lambda r: r["count"], reverse=True)

    return {
        "ai_assisted_issue_count": total,
        "tool_breakdown": _breakdown(ai_tool_labels) if ai_tool_labels else [],
        "action_breakdown": _breakdown(ai_action_labels) if ai_action_labels else [],
    }


def compute_custom_trends(
    _sprints: list[dict[str, Any]],
    _sprint_issues: dict[int, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    """
    Placeholder for custom metric trends. Extend with your custom field and aggregation.
    Returns list of {sprint_id, sprint_name, <custom_metric_key>: value}.
    """
    return []


# Mapping from survey `usage` answer text to its numeric score
_DAU_SCORE_MAP: dict[str, float] = {
    "Every day (5 days)": 5.0,
    "Most days (3–4 days)": 3.5,
    "Rarely (1–2 days)": 1.5,
    "Not used": 0.0,
}


def compute_dau_metrics(responses_dir: str | Path) -> dict[str, Any]:
    """
    Load all dau_*.json response files from responses_dir and compute team DAU metrics.

    Returns {team_avg, response_count, by_role, breakdown}.
    Returns safe zero-state when directory is empty or missing.
    """
    import json
    from collections import Counter

    path = Path(responses_dir)
    records: list[dict[str, Any]] = []
    if path.is_dir():
        for fpath in sorted(path.glob("dau_*.json")):
            try:
                data = json.loads(fpath.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    records.append(data)
            except Exception:
                continue

    if not records:
        return {"team_avg": None, "response_count": 0, "by_role": [], "breakdown": []}

    scores = [_DAU_SCORE_MAP.get(r.get("usage", ""), 0.0) for r in records]
    team_avg = round(sum(scores) / len(scores), 2)

    # Per-role averages
    role_data: dict[str, list[float]] = {}
    for r, s in zip(records, scores):
        role = r.get("role") or "Unknown"
        role_data.setdefault(role, []).append(s)
    by_role = sorted(
        [
            {"role": role, "avg": round(sum(vals) / len(vals), 2), "count": len(vals)}
            for role, vals in role_data.items()
        ],
        key=lambda x: x["role"],
    )

    # Answer frequency breakdown
    cnt: Counter[str] = Counter(r.get("usage", "") for r in records)
    breakdown = sorted(
        [{"answer": a, "count": c} for a, c in cnt.items()],
        key=lambda x: -x["count"],
    )

    return {
        "team_avg": team_avg,
        "response_count": len(records),
        "by_role": by_role,
        "breakdown": breakdown,
    }


def build_metrics_dict(
    sprints: list[dict[str, Any]],
    sprint_issues: dict[int, list[dict[str, Any]]],
    issues_with_changelog: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build the single metrics dict used by both HTML and MD reporters."""
    velocity = compute_velocity(sprints, sprint_issues)
    cycle_time = compute_cycle_time(issues_with_changelog)
    custom = compute_custom_trends(sprints, sprint_issues)
    ai_trend = compute_ai_assistance_trend(sprints, sprint_issues)
    ai_usage = compute_ai_usage_details(sprints, sprint_issues)
    dau = compute_dau_metrics(config.DAU_RESPONSES_DIR)
    return {
        "velocity": velocity,
        "cycle_time": cycle_time,
        "custom_trends": custom,
        "ai_assistance_trend": ai_trend,
        "ai_usage_details": ai_usage,
        "ai_assisted_label": config.AI_ASSISTED_LABEL,
        "ai_exclude_labels": config.AI_EXCLUDE_LABELS,
        "dau": dau,
        # Metadata fields enriched by main.py after Jira fetch
        "filter_name": None,
        "filter_id": None,
        "filter_jql": None,
        "project_key": None,
        "generated_at": datetime.now(UTC).isoformat(),
    }
