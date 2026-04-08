"""Generate HTML report from metrics dict."""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

DEFAULT_OUTPUT = Path(__file__).resolve().parent.parent.parent / "report.html"
TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent / "templates"


_SECTION_KEYS = [
    "velocity_trend",
    "ai_assistance_trend",
    "ai_usage_details",
    "dau",
    "dau_trend",
]


def _build_display_labels(project_type: str | None, estimation_type: str | None) -> dict:
    """Return adaptive display strings based on project type and estimation type.

    KANBAN reports use throughput/period terminology; SCRUM reports use velocity/sprint.
    """
    is_kanban = (project_type or "").upper() == "KANBAN"
    unit_label = "tickets" if estimation_type == "JiraTickets" else "points"
    if is_kanban:
        return {
            "velocity_section_title": "Throughput trend",
            "period_column": "Period",
            "velocity_chart_label": f"Throughput ({unit_label})",
            "avg_velocity_chart_label": "Average Throughput",
            "per_period_phrase": "per period",
        }
    return {
        "velocity_section_title": "Velocity trend",
        "period_column": "Sprint",
        "velocity_chart_label": f"Velocity ({unit_label})",
        "avg_velocity_chart_label": "Average Velocity",
        "per_period_phrase": "per sprint",
    }


def generate_html(
    metrics: dict,
    output_path: Path = DEFAULT_OUTPUT,
    section_visibility: dict | None = None,
) -> None:
    """Render Jinja2 template with metrics and write report to output_path.

    section_visibility controls which sections appear in the output.
    Defaults to all sections visible.
    """
    if section_visibility is None:
        section_visibility = {k: True for k in _SECTION_KEYS}
    display_labels = _build_display_labels(metrics.get("project_type"), metrics.get("estimation_type"))
    # Template renders trusted Jira metric data — no user-supplied HTML content
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))  # nosec B701
    template = env.get_template("report.html.j2")
    html = template.render(
        metrics=metrics,
        section_visibility=section_visibility,
        display_labels=display_labels,
    )
    output_path.write_text(html, encoding="utf-8")
