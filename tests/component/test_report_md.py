"""Tests for app.report_md: Markdown output correctness."""

from __future__ import annotations

import pytest

from app.reporters.report_md import _md_table, generate_md

pytestmark = pytest.mark.component


def test_file_created(tmp_path, minimal_metrics_dict):
    out = tmp_path / "report.md"
    generate_md(minimal_metrics_dict, out)
    assert out.exists()


def test_title_present(tmp_path, minimal_metrics_dict):
    out = tmp_path / "report.md"
    generate_md(minimal_metrics_dict, out)
    content = out.read_text(encoding="utf-8")
    assert "# AI Adoption Metrics Report" in content


def test_date_present(tmp_path, minimal_metrics_dict):
    out = tmp_path / "report.md"
    generate_md(minimal_metrics_dict, out)
    content = out.read_text(encoding="utf-8")
    assert "2026-03-25" in content


def test_sprint_name_present(tmp_path, minimal_metrics_dict):
    out = tmp_path / "report.md"
    generate_md(minimal_metrics_dict, out)
    content = out.read_text(encoding="utf-8")
    assert "Sprint Alpha" in content


def test_velocity_value_present(tmp_path, minimal_metrics_dict):
    out = tmp_path / "report.md"
    generate_md(minimal_metrics_dict, out)
    content = out.read_text(encoding="utf-8")
    assert "20.0" in content


def test_no_velocity_data_message(tmp_path, empty_metrics_dict):
    out = tmp_path / "report.md"
    generate_md(empty_metrics_dict, out)
    content = out.read_text(encoding="utf-8")
    assert "No velocity data" in content


def test_bar_chart_present_when_velocity_nonzero(tmp_path, minimal_metrics_dict):
    out = tmp_path / "report.md"
    generate_md(minimal_metrics_dict, out)
    content = out.read_text(encoding="utf-8")
    assert "█" in content


# ---------------------------------------------------------------------------
# _md_table
# ---------------------------------------------------------------------------


def test_md_table_header_row():
    table = _md_table(["A", "B"], [])
    lines = table.splitlines()
    assert lines[0] == "| A | B |"


def test_md_table_separator_row():
    table = _md_table(["A", "B"], [])
    lines = table.splitlines()
    assert lines[1] == "| --- | --- |"


def test_md_table_data_row():
    table = _md_table(["X", "Y"], [["foo", "bar"]])
    lines = table.splitlines()
    assert lines[2] == "| foo | bar |"


# ---------------------------------------------------------------------------
# MD report does NOT render AI sections (documents current behavior gap)
# ---------------------------------------------------------------------------


def test_md_report_no_ai_assistance_section(tmp_path, minimal_metrics_dict):
    """MD report currently does not render AI assistance trend section."""
    out = tmp_path / "report.md"
    generate_md(minimal_metrics_dict, out)
    content = out.read_text(encoding="utf-8")
    assert "## AI Assistance" not in content


def test_md_report_no_ai_usage_section(tmp_path, minimal_metrics_dict):
    """MD report currently does not render AI usage details section."""
    out = tmp_path / "report.md"
    generate_md(minimal_metrics_dict, out)
    content = out.read_text(encoding="utf-8")
    assert "## AI Usage" not in content


# ---------------------------------------------------------------------------
# Project type, estimation type, and velocity label in report header
# (RG-PT-005, RG-ET-005, RG-ET-007)
# ---------------------------------------------------------------------------


def test_project_type_shown_in_md_header(tmp_path, minimal_metrics_dict):
    minimal_metrics_dict["project_type"] = "SCRUM"
    out = tmp_path / "report.md"
    generate_md(minimal_metrics_dict, out)
    content = out.read_text(encoding="utf-8")
    assert "Project Type:" in content
    assert "SCRUM" in content


def test_estimation_type_shown_in_md_header(tmp_path, minimal_metrics_dict):
    minimal_metrics_dict["estimation_type"] = "StoryPoints"
    out = tmp_path / "report.md"
    generate_md(minimal_metrics_dict, out)
    content = out.read_text(encoding="utf-8")
    assert "Estimation:" in content
    assert "StoryPoints" in content


def test_velocity_header_label_story_points(tmp_path, minimal_metrics_dict):
    minimal_metrics_dict["estimation_type"] = "StoryPoints"
    out = tmp_path / "report.md"
    generate_md(minimal_metrics_dict, out)
    content = out.read_text(encoding="utf-8")
    assert "Velocity (points)" in content


def test_velocity_header_label_jira_tickets(tmp_path, minimal_metrics_dict):
    minimal_metrics_dict["estimation_type"] = "JiraTickets"
    out = tmp_path / "report.md"
    generate_md(minimal_metrics_dict, out)
    content = out.read_text(encoding="utf-8")
    assert "Velocity (tickets)" in content


# ---------------------------------------------------------------------------
# section_visibility — MD sections hidden when toggled off
# ---------------------------------------------------------------------------

_ALL_HIDDEN = {
    "velocity_trend": False,
    "ai_assistance_trend": False,
    "ai_usage_details": False,
    "dau": False,
}


def test_velocity_section_hidden_when_section_visibility_false(tmp_path, minimal_metrics_dict):
    out = tmp_path / "report.md"
    generate_md(minimal_metrics_dict, out, section_visibility=_ALL_HIDDEN)
    content = out.read_text(encoding="utf-8")
    assert "## Velocity trend" not in content


def test_dau_section_hidden_when_section_visibility_false(tmp_path, minimal_metrics_dict):
    out = tmp_path / "report.md"
    generate_md(minimal_metrics_dict, out, section_visibility=_ALL_HIDDEN)
    content = out.read_text(encoding="utf-8")
    assert "## Daily Active Usage" not in content
