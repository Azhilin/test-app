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


def generate_md(metrics: dict, output_path: Path = DEFAULT_OUTPUT) -> None:
    """Build Markdown from metrics dict and write to output_path."""
    parts = [
        "# AI Adoption Metrics Report",
        "",
        f"Reported Date:  {(metrics.get('generated_at') or '')[:10]}",
        "",
    ]

    velocity = metrics.get("velocity") or []
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

        headers = ["Sprint", "Start", "End", "Velocity (points)", "Issues done"]
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

    ct = metrics.get("cycle_time") or {}
    sample = ct.get("sample_size") or 0
    parts.append("## Cycle time")
    parts.append("")
    if sample > 0:
        parts.append(
            _md_table(
                ["Metric", "Value"],
                [
                    ["Mean (days)", ct.get("mean_days", "—")],
                    ["Median (days)", ct.get("median_days", "—")],
                    ["Min (days)", ct.get("min_days", "—")],
                    ["Max (days)", ct.get("max_days", "—")],
                    ["Sample size", str(sample)],
                ],
            )
        )
    else:
        parts.append("*No cycle time data (need issues with changelog).*")
    parts.append("")

    custom = metrics.get("custom_trends") or []
    if custom:
        parts.append("## Custom trends")
        parts.append("")
        headers = ["Sprint"] + [k for k in custom[0] if k not in ("sprint_id", "sprint_name")]
        rows = [[row.get("sprint_name", "")] + [row.get(k, "") for k in headers[1:]] for row in custom]
        parts.append(_md_table(headers, rows))
        parts.append("")

    output_path.write_text("\n".join(parts), encoding="utf-8")
