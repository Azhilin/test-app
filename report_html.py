"""Generate HTML report from metrics dict."""
from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

DEFAULT_OUTPUT = Path(__file__).resolve().parent / "report.html"
TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"


def generate_html(metrics: dict, output_path: Path = DEFAULT_OUTPUT) -> None:
    """Render Jinja2 template with metrics and write report to output_path."""
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
    template = env.get_template("report.html.j2")
    html = template.render(metrics=metrics)
    output_path.write_text(html, encoding="utf-8")
