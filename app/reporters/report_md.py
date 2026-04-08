"""Generate Markdown report from metrics dict."""

from __future__ import annotations

from pathlib import Path

DEFAULT_OUTPUT = Path(__file__).resolve().parent.parent.parent / "report.md"


def _md_table(headers: list[str], rows: list[list[str]]) -> str:
    """Build a Markdown table."""
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(c) for c in row) + " |")
    return "\n".join(lines)


_SECTION_KEYS = [
    "velocity_trend",
    "ai_assistance_trend",
    "ai_usage_details",
    "dau",
    "dau_trend",
]


def generate_md(
    metrics: dict,
    output_path: Path = DEFAULT_OUTPUT,
    section_visibility: dict | None = None,
) -> None:
    """Build Markdown from metrics dict and write to output_path.

    section_visibility controls which sections appear in the output.
    Defaults to all sections visible.
    """
    if section_visibility is None:
        section_visibility = {k: True for k in _SECTION_KEYS}
    unit_label = "tickets" if metrics.get("estimation_type") == "JiraTickets" else "points"
    parts = [
        "# AI Adoption Metrics Report",
        "",
        f"Reported Date:  {(metrics.get('generated_at') or '')[:10]}",
    ]
    if metrics.get("project_type"):
        parts.append(f"Project Type:   {metrics['project_type']}")
    if metrics.get("estimation_type"):
        parts.append(f"Estimation:     {metrics['estimation_type']}")
    parts.append("")

    velocity = metrics.get("velocity") or []
    if section_visibility.get("velocity_trend", True):
        if velocity:
            parts.append("## Velocity trend")
            parts.append("")
            # Bar chart: proportional bars (max 40 chars width)
            max_vel = max((row.get("velocity") or 0) for row in velocity) or 1
            for row in velocity:
                v = row.get("velocity") or 0
                bar_len = int(40 * v / max_vel) if max_vel else 0
                bar = "█" * bar_len
                parts.append(f"- **{row.get('sprint_name', '')}**: {bar} {v}")
            parts.append("")

            def _date_fmt(s: str | None) -> str:
                return ((s or "")[:10] or "—").strip() or "—"

            headers = ["Sprint", "Start", "End", f"Velocity ({unit_label})", "Issues done"]
            rows = [
                [
                    row.get("sprint_name", ""),
                    _date_fmt(row.get("start_date")),
                    _date_fmt(row.get("end_date")),
                    row.get("velocity", 0),
                    row.get("issue_count", 0),
                ]
                for row in velocity
            ]
            parts.append(_md_table(headers, rows))
            parts.append("")
        else:
            parts.append("## Velocity trend")
            parts.append("")
            parts.append("*No velocity data.*")
            parts.append("")

    dau = metrics.get("dau") or {}
    if section_visibility.get("dau", True) and dau.get("response_count"):
        parts.append("## Daily Active Usage (DAU)")
        parts.append("")
        pct_str = f" ({dau['team_avg_pct']}%)" if dau.get("team_avg_pct") is not None else ""
        parts.append(f"Team average: **{dau['team_avg']} / 5**{pct_str} across {dau['response_count']} response(s)")
        parts.append("")
        if dau.get("by_role"):
            headers = ["Role", "Avg days/week", "Avg %", "Responses"]
            rows = [
                [r["role"], r["avg"], f"{r.get('avg_pct', '')}%" if r.get("avg_pct") is not None else "—", r["count"]]
                for r in dau["by_role"]
            ]
            parts.append(_md_table(headers, rows))
            parts.append("")
        if dau.get("breakdown"):
            headers = ["Answer", "Count", "%"]
            rows = [
                [b["answer"], b["count"], f"{b.get('pct', '')}%" if b.get("pct") is not None else "—"]
                for b in dau["breakdown"]
            ]
            parts.append(_md_table(headers, rows))
            parts.append("")

    dau_trend = metrics.get("dau_trend") or []
    if section_visibility.get("dau_trend", True) and dau_trend:
        parts.append("## DAU Trend")
        parts.append("")
        max_avg = max((row.get("team_avg") or 0) for row in dau_trend) or 1
        for row in dau_trend:
            v = row.get("team_avg") or 0
            bar_len = int(30 * v / max_avg) if max_avg else 0
            bar = "█" * bar_len
            parts.append(f"- **{row.get('week', '')}**: {bar} {v} ({row.get('team_avg_pct', 0)}%)")
        parts.append("")
        headers = ["Week", "Team Avg", "Team Avg %", "Responses"]
        rows = [
            [
                row.get("week", ""),
                row.get("team_avg", 0),
                f"{row.get('team_avg_pct', 0)}%",
                row.get("response_count", 0),
            ]
            for row in dau_trend
        ]
        parts.append(_md_table(headers, rows))
        parts.append("")

    output_path.write_text("\n".join(parts), encoding="utf-8")
