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
    "cycle_time",
    "custom_trends",
]


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
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
    template = env.get_template("report.html.j2")
    html = template.render(metrics=metrics, section_visibility=section_visibility)
    output_path.write_text(html, encoding="utf-8")
