"""Compute velocity, cycle time, and custom metric trends from Jira data."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.core import config, schema

logger = logging.getLogger(__name__)

_DEFAULT_DONE = frozenset(("done", "closed", "resolved", "complete"))
_DEFAULT_IN_PROGRESS = frozenset(("in progress",))


def _parse_iso(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def _get_story_points(
    issue: dict[str, Any],
    story_points_field: str | None = None,
) -> float:
    """Extract story points from issue fields. Returns 0 if missing or non-numeric."""
    field_key = story_points_field or schema.DEFAULT_STORY_POINTS_FIELD_ID
    fields = issue.get("fields") or {}
    raw = fields.get(field_key)
    if raw is None:
        return 0.0
    if isinstance(raw, dict):
        for key in ("value", "number", "estimate", "amount"):
            if key in raw:
                raw = raw[key]
                break
    try:
        return float(raw)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 0.0


def _is_done(
    issue: dict[str, Any],
    done_statuses: frozenset[str] | None = None,
) -> bool:
    """True if issue is in a Done/Resolved-like status or has a resolutiondate.

    The resolutiondate fallback handles KANBAN boards that use custom terminal
    status names (e.g. "Released", "Deployed") not present in done_statuses.
    fetch_kanban_data() pre-filters issues by resolutiondate, so every returned
    issue is resolved by definition regardless of its status name.
    """
    statuses = done_statuses or _DEFAULT_DONE
    fields = issue.get("fields") or {}
    status = fields.get("status") or {}
    name = (status.get("name") or "").lower()
    if name in statuses:
        return True
    return bool(fields.get("resolutiondate"))


def deduplicate_sprint_issues(
    sprints: list[dict[str, Any]],
    sprint_issues: dict[int | str, list[dict[str, Any]]],
) -> dict[int | str, list[dict[str, Any]]]:
    """Return sprint_issues with each issue key kept only in its last (highest) sprint.

    When the Jira API returns the same issue for multiple sprints, it should count
    only toward the most recent sprint. The sprints list is assumed to be ordered
    chronologically (oldest first), so the last occurrence wins.
    """
    # Map each issue key to the last sprint ID it appears in (last write wins)
    issue_last_sprint: dict[str, int | str] = {}
    for sprint in sprints:
        sid = sprint.get("id")
        if sid is None:
            continue
        for iss in sprint_issues.get(sid) or []:
            key = iss.get("key") or ""
            if key:
                issue_last_sprint[key] = sid

    # Rebuild: keep each issue only in its mapped (last) sprint.
    # Issues without a key are untrackable and stay wherever they appear.
    result: dict[int | str, list[dict[str, Any]]] = {}
    for sprint in sprints:
        sid = sprint.get("id")
        if sid is None:
            continue
        kept = []
        for iss in sprint_issues.get(sid) or []:
            key = iss.get("key") or ""
            if not key or issue_last_sprint.get(key) == sid:
                kept.append(iss)
        result[sid] = kept
    return result


def compute_velocity(
    sprints: list[dict[str, Any]],
    sprint_issues: dict[int | str, list[dict[str, Any]]],
    story_points_field: str | None = None,
    done_statuses: frozenset[str] | None = None,
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
            if _is_done(iss, done_statuses):
                points += _get_story_points(iss, story_points_field)
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


def _get_labels(issue: dict[str, Any]) -> list[str]:
    """Return the list of label strings on an issue (empty if absent)."""
    fields = issue.get("fields") or {}
    labels = fields.get("labels") or []
    return [str(lbl) for lbl in labels if lbl]


def compute_ai_assistance_trend(
    sprints: list[dict[str, Any]],
    sprint_issues: dict[int | str, list[dict[str, Any]]],
    ai_assisted_label: str | None = None,
    ai_exclude_labels: list[str] | None = None,
    story_points_field: str | None = None,
    done_statuses: frozenset[str] | None = None,
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
            if not _is_done(iss, done_statuses):
                continue
            labels = _get_labels(iss)
            if exclude_set and exclude_set.intersection(labels):
                continue
            pts = _get_story_points(iss, story_points_field)
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
    sprint_issues: dict[int | str, list[dict[str, Any]]],
    ai_assisted_label: str | None = None,
    ai_tool_labels: list[str] | None = None,
    ai_action_labels: list[str] | None = None,
    done_statuses: frozenset[str] | None = None,
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
            if not _is_done(iss, done_statuses) or key in seen_keys:
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


_DAU_SCORE_MAP: dict[str, float] = {
    "Every day (5 days)": 5.0,
    "Most days (3–4 days)": 3.5,
    "Rarely (1–2 days)": 1.5,
    "Not used": 0.0,
}

_DAU_MAX_SCORE = 5.0


def _load_dau_records(responses_dir: str | Path) -> list[dict[str, Any]]:
    """Load all dau_*.json files from *responses_dir* and return parsed dicts.

    Defensively derives the ``week`` field from ``timestamp`` for any record
    that is missing it (e.g. raw survey files not yet normalised).
    """
    import json
    from datetime import datetime, timezone

    def _derive_week(iso_ts: str) -> str:
        dt = datetime.fromisoformat(iso_ts).astimezone(timezone.utc)
        iso_year, iso_week, _ = dt.isocalendar()
        return f"{iso_year}-W{iso_week:02d}"

    path = Path(responses_dir)
    records: list[dict[str, Any]] = []
    if path.is_dir():
        for fpath in sorted(path.glob("dau_*.json")):
            try:
                data = json.loads(fpath.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    if not data.get("week") and data.get("timestamp"):
                        try:
                            data["week"] = _derive_week(data["timestamp"])
                        except Exception:  # nosec B110
                            pass
                    records.append(data)
            except Exception:  # nosec B112
                continue
    return records


def _dedup_by_user_week(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Keep only the latest response per (username, week) pair."""
    best: dict[tuple[str, str], dict[str, Any]] = {}
    for rec in records:
        key = (rec.get("username", ""), rec.get("week", ""))
        existing = best.get(key)
        if existing is None or rec.get("timestamp", "") > existing.get("timestamp", ""):
            best[key] = rec
    return list(best.values())


def compute_dau_metrics(responses_dir: str | Path) -> dict[str, Any]:
    """Load DAU survey responses from disk and compute aggregate metrics."""
    from collections import Counter

    records = _dedup_by_user_week(_load_dau_records(responses_dir))

    if not records:
        return {
            "team_avg": None,
            "team_avg_pct": None,
            "response_count": 0,
            "by_role": [],
            "breakdown": [],
        }

    scores = [_DAU_SCORE_MAP.get(record.get("usage", ""), 0.0) for record in records]
    team_avg = round(sum(scores) / len(scores), 2)
    team_avg_pct = round(team_avg / _DAU_MAX_SCORE * 100, 1)

    role_data: dict[str, list[float]] = {}
    for record, score in zip(records, scores):
        role = record.get("role") or "Unknown"
        role_data.setdefault(role, []).append(score)
    by_role = sorted(
        [
            {
                "role": role,
                "avg": round(sum(vals) / len(vals), 2),
                "avg_pct": round(sum(vals) / len(vals) / _DAU_MAX_SCORE * 100, 1),
                "count": len(vals),
            }
            for role, vals in role_data.items()
        ],
        key=lambda item: str(item.get("role", "")),
    )

    total = len(records)
    counts: Counter[str] = Counter(record.get("usage", "") for record in records)
    breakdown = sorted(
        [
            {
                "answer": answer,
                "count": count,
                "pct": round(count / total * 100, 1),
            }
            for answer, count in counts.items()
        ],
        key=lambda item: -int(str(item["count"])),
    )

    return {
        "team_avg": team_avg,
        "team_avg_pct": team_avg_pct,
        "response_count": len(records),
        "by_role": by_role,
        "breakdown": breakdown,
    }


def compute_dau_trend(responses_dir: str | Path) -> list[dict[str, Any]]:
    """Compute weekly DAU trend from survey responses.

    Returns a chronologically sorted list of per-week rows:
    ``[{week, team_avg, team_avg_pct, response_count}, ...]``
    """
    records = _load_dau_records(responses_dir)
    if not records:
        return []

    deduped = _dedup_by_user_week(records)

    weeks: dict[str, list[float]] = {}
    for rec in deduped:
        week = rec.get("week", "")
        if not week:
            continue
        score = _DAU_SCORE_MAP.get(rec.get("usage", ""), 0.0)
        weeks.setdefault(week, []).append(score)

    rows: list[dict[str, Any]] = []
    for week in sorted(weeks):
        scores = weeks[week]
        avg = round(sum(scores) / len(scores), 2)
        rows.append(
            {
                "week": week,
                "team_avg": avg,
                "team_avg_pct": round(avg / _DAU_MAX_SCORE * 100, 1),
                "response_count": len(scores),
            }
        )
    return rows


def get_done_issue_keys_for_changelog(
    sprints: list[dict[str, Any]],
    sprint_issues: dict[int | str, list[dict[str, Any]]],
    max_count: int = 100,
    done_statuses: frozenset[str] | None = None,
) -> list[str]:
    """Return up to *max_count* done-issue keys, most recent sprint first.

    Used to select which issues to fetch changelogs for before calling
    ``compute_cycle_time``.
    """
    seen: set[str] = set()
    candidates: list[tuple[str, str]] = []
    for sprint in sprints:
        sid = sprint.get("id")
        if sid is None:
            continue
        end_date = sprint.get("endDate") or ""
        for iss in sprint_issues.get(sid) or []:
            if not _is_done(iss, done_statuses):
                continue
            key = iss.get("key") or ""
            if key and key not in seen:
                seen.add(key)
                candidates.append((end_date, key))
    candidates.sort(key=lambda t: t[0], reverse=True)
    return [key for _, key in candidates[:max_count]]


def _cycle_time_from_changelog(
    issue: dict[str, Any],
    done_statuses: frozenset[str] | None = None,
    in_progress_statuses: frozenset[str] | None = None,
) -> float | None:
    """Return cycle days for *issue* using its changelog, or None if not computable.

    Scans changelog histories in order:
    - ``in_progress_at``: timestamp of the *first* transition into an in-progress status.
    - ``done_at``: timestamp of the *last* transition into a done status.

    Excludes issues whose changelog timestamps are timezone-naive or where
    ``done_at < in_progress_at``.
    """
    ip_statuses = in_progress_statuses or _DEFAULT_IN_PROGRESS
    d_statuses = done_statuses or _DEFAULT_DONE
    changelog = issue.get("changelog") or {}
    histories = changelog.get("histories") or []
    in_progress_at: datetime | None = None
    done_at: datetime | None = None
    for history in histories:
        ts = _parse_iso(history.get("created"))
        if ts is None or ts.tzinfo is None:
            continue
        for item in history.get("items") or []:
            if item.get("field") != "status":
                continue
            to_status = (item.get("toString") or "").lower()
            if to_status in ip_statuses and in_progress_at is None:
                in_progress_at = ts
            if to_status in d_statuses:
                done_at = ts
    if in_progress_at is None or done_at is None:
        return None
    if done_at < in_progress_at:
        return None
    return round((done_at - in_progress_at).total_seconds() / 86400, 1)


def compute_cycle_time(
    issues_with_changelog: list[dict[str, Any]],
    done_statuses: frozenset[str] | None = None,
    in_progress_statuses: frozenset[str] | None = None,
) -> dict[str, Any]:
    """Compute cycle time statistics across issues that carry changelog data.

    Returns::

        {
            "mean_days":   float | None,
            "median_days": float | None,
            "min_days":    float | None,
            "max_days":    float | None,
            "sample_size": int,
            "values":      list[float],   # sorted ascending
        }
    """
    values: list[float] = sorted(
        ct
        for issue in issues_with_changelog
        if (ct := _cycle_time_from_changelog(issue, done_statuses, in_progress_statuses)) is not None
    )
    n = len(values)
    if n == 0:
        return {
            "mean_days": None,
            "median_days": None,
            "min_days": None,
            "max_days": None,
            "sample_size": 0,
            "values": [],
        }
    mean_days = round(sum(values) / n, 1)
    mid = n // 2
    median_days = round((values[mid - 1] + values[mid]) / 2, 1) if n % 2 == 0 else values[mid]
    return {
        "mean_days": mean_days,
        "median_days": median_days,
        "min_days": values[0],
        "max_days": values[-1],
        "sample_size": n,
        "values": values,
    }


def _resolve_schema_params(
    schema: dict[str, Any] | None,
) -> tuple[str | None, frozenset[str] | None, frozenset[str] | None]:
    """Extract story_points_field, done_statuses, in_progress_statuses from a schema dict."""
    if schema is None:
        return None, None, None

    from app.core import schema as schema_mod

    sp_field = schema_mod.get_field_id(schema, "story_points")
    done = schema_mod.get_done_statuses(schema)
    ip = schema_mod.get_in_progress_statuses(schema)
    done_fs = frozenset(s.lower() for s in done) if done else None
    ip_fs = frozenset(s.lower() for s in ip) if ip else None
    return sp_field, done_fs, ip_fs


def build_metrics_dict(
    sprints: list[dict[str, Any]],
    sprint_issues: dict[int | str, list[dict[str, Any]]],
    schema: dict[str, Any] | None = None,
    issues_with_changelog: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build the single metrics dict used by both HTML and MD reporters."""
    sp_field, done_fs, ip_fs = _resolve_schema_params(schema)
    sprint_issues = deduplicate_sprint_issues(sprints, sprint_issues)
    logger.debug("Computing metrics: %s sprint(s)", len(sprints))

    velocity = compute_velocity(sprints, sprint_issues, sp_field, done_fs)

    # Auto-fallback: if ESTIMATION_TYPE is StoryPoints but all SP values are 0, use JiraTickets
    estimation_type = config.ESTIMATION_TYPE
    if estimation_type == "StoryPoints":
        total_sp = sum(row["velocity"] for row in velocity)
        if total_sp == 0:
            logger.warning(
                "All story point values are 0; automatically falling back to JiraTickets estimation. "
                "This may indicate that the story points custom field is not configured or has no values."
            )
            estimation_type = "JiraTickets"

    if estimation_type == "JiraTickets":
        for row in velocity:
            row["velocity"] = row["issue_count"]
    logger.debug(
        "Velocity computed for %s sprint(s); totals: %s (estimation_type=%s)",
        len(velocity),
        [f"{r['sprint_name']}={r['velocity']}" for r in velocity],
        estimation_type,
    )

    ai_trend = compute_ai_assistance_trend(
        sprints,
        sprint_issues,
        story_points_field=sp_field,
        done_statuses=done_fs,
    )
    ai_usage = compute_ai_usage_details(
        sprints,
        sprint_issues,
        done_statuses=done_fs,
    )
    cycle_time = compute_cycle_time(issues_with_changelog or [], done_fs, ip_fs)
    dau = compute_dau_metrics(config.DAU_NORMALIZED_DIR)
    dau_trend = compute_dau_trend(config.DAU_NORMALIZED_DIR)
    return {
        "velocity": velocity,
        "cycle_time": cycle_time,
        "ai_assistance_trend": ai_trend,
        "ai_usage_details": ai_usage,
        "ai_assisted_label": config.AI_ASSISTED_LABEL,
        "ai_exclude_labels": config.AI_EXCLUDE_LABELS,
        "dau": dau,
        "dau_trend": dau_trend,
        "schema_name": (schema or {}).get("schema_name"),
        "project_type": config.PROJECT_TYPE,
        "estimation_type": estimation_type,
        "filter_name": None,
        "filter_id": None,
        "filter_jql": None,
        "project_key": None,
        "generated_at": datetime.now(UTC).isoformat(),
    }
