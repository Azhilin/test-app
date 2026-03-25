"""Tests for app.report_md: Markdown output correctness."""
from __future__ import annotations

import pytest

from app.report_md import generate_md, _md_table

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


def test_cycle_time_stats_present(tmp_path, minimal_metrics_dict):
    out = tmp_path / "report.md"
    generate_md(minimal_metrics_dict, out)
    content = out.read_text(encoding="utf-8")
    assert "3.5" in content   # mean
    assert "3.0" in content   # median


def test_no_velocity_data_message(tmp_path, empty_metrics_dict):
    out = tmp_path / "report.md"
    generate_md(empty_metrics_dict, out)
    content = out.read_text(encoding="utf-8")
    assert "No velocity data" in content


def test_no_cycle_time_data_message(tmp_path, empty_metrics_dict):
    out = tmp_path / "report.md"
    generate_md(empty_metrics_dict, out)
    content = out.read_text(encoding="utf-8")
    assert "No cycle time data" in content


def test_bar_chart_present_when_velocity_nonzero(tmp_path, minimal_metrics_dict):
    out = tmp_path / "report.md"
    generate_md(minimal_metrics_dict, out)
    content = out.read_text(encoding="utf-8")
    assert "█" in content


def test_custom_trends_section_absent_when_empty(tmp_path, minimal_metrics_dict):
    out = tmp_path / "report.md"
    generate_md(minimal_metrics_dict, out)
    content = out.read_text(encoding="utf-8")
    assert "## Custom trends" not in content


def test_custom_trends_section_present_when_data(tmp_path, minimal_metrics_dict):
    minimal_metrics_dict["custom_trends"] = [
        {"sprint_id": 1, "sprint_name": "Sprint Alpha", "ai_usage": 42}
    ]
    out = tmp_path / "report.md"
    generate_md(minimal_metrics_dict, out)
    content = out.read_text(encoding="utf-8")
    assert "## Custom trends" in content
    assert "42" in content


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
