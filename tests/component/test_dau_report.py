"""Component tests for the DAU section in both report renderers.

Requirements covered:
    DAU-F-023, DAU-F-024, DAU-F-025, DAU-F-026
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app.reporters.report_html import generate_html
from app.reporters.report_md import generate_md

pytestmark = pytest.mark.component


# ---------------------------------------------------------------------------
# Markdown renderer (DAU-F-023 / DAU-F-024)
# ---------------------------------------------------------------------------


def test_md_has_dau_heading_when_data_present(minimal_metrics_dict: dict, tmp_path: Path) -> None:
    out = tmp_path / "report.md"
    generate_md(minimal_metrics_dict, out)
    assert "## Daily Active Usage (DAU)" in out.read_text(encoding="utf-8")


def test_md_dau_shows_team_avg(minimal_metrics_dict: dict, tmp_path: Path) -> None:
    out = tmp_path / "report.md"
    generate_md(minimal_metrics_dict, out)
    assert "3.5 / 5" in out.read_text(encoding="utf-8")


def test_md_dau_shows_role_in_table(minimal_metrics_dict: dict, tmp_path: Path) -> None:
    out = tmp_path / "report.md"
    generate_md(minimal_metrics_dict, out)
    content = out.read_text(encoding="utf-8")
    assert "Developer" in content
    assert "4.25" in content


def test_md_dau_section_absent_when_no_responses(empty_metrics_dict: dict, tmp_path: Path) -> None:
    out = tmp_path / "report.md"
    generate_md(empty_metrics_dict, out)
    assert "## Daily Active Usage" not in out.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# HTML renderer (DAU-F-025 / DAU-F-026)
# ---------------------------------------------------------------------------


def test_html_has_dau_section_when_data_present(minimal_metrics_dict: dict, tmp_path: Path) -> None:
    out = tmp_path / "report.html"
    generate_html(minimal_metrics_dict, out)
    content = out.read_text(encoding="utf-8")
    assert "Daily Active Usage (DAU)" in content
    assert "dauRoleChart" in content


def test_html_dau_shows_team_avg(minimal_metrics_dict: dict, tmp_path: Path) -> None:
    out = tmp_path / "report.html"
    generate_html(minimal_metrics_dict, out)
    assert "3.5 / 5" in out.read_text(encoding="utf-8")


def test_html_dau_section_absent_when_no_responses(empty_metrics_dict: dict, tmp_path: Path) -> None:
    out = tmp_path / "report.html"
    generate_html(empty_metrics_dict, out)
    assert "dauRoleChart" not in out.read_text(encoding="utf-8")


def test_html_dau_section_hidden_when_visibility_false(minimal_metrics_dict: dict, tmp_path: Path) -> None:
    out = tmp_path / "report.html"
    generate_html(
        minimal_metrics_dict,
        out,
        section_visibility={
            "velocity_trend": True,
            "ai_assistance_trend": True,
            "ai_usage_details": True,
            "cycle_time": True,
            "custom_trends": True,
            "dau": False,
        },
    )
    assert "dauRoleChart" not in out.read_text(encoding="utf-8")
