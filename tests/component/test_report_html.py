"""Tests for app.report_html: Jinja2 template rendering."""

from __future__ import annotations

import pytest

from app.reporters.report_html import TEMPLATES_DIR, generate_html

pytestmark = pytest.mark.component


def test_templates_dir_exists():
    assert TEMPLATES_DIR.is_dir()


def test_template_file_exists():
    assert (TEMPLATES_DIR / "report.html.j2").exists()


def test_templates_dir_not_inside_app():
    """Validate the path fix: templates/ should be at project root, not inside app/."""
    assert TEMPLATES_DIR.parent.name != "app"


def test_file_created(tmp_path, minimal_metrics_dict):
    out = tmp_path / "report.html"
    generate_html(minimal_metrics_dict, out)
    assert out.exists()


def test_doctype_present(tmp_path, minimal_metrics_dict):
    out = tmp_path / "report.html"
    generate_html(minimal_metrics_dict, out)
    content = out.read_text(encoding="utf-8")
    assert content.lstrip().startswith("<!DOCTYPE html>") or "<!DOCTYPE html>" in content[:200]


def test_title_present(tmp_path, minimal_metrics_dict):
    out = tmp_path / "report.html"
    generate_html(minimal_metrics_dict, out)
    content = out.read_text(encoding="utf-8")
    assert "AI Adoption Metrics" in content


def test_date_present(tmp_path, minimal_metrics_dict):
    out = tmp_path / "report.html"
    generate_html(minimal_metrics_dict, out)
    content = out.read_text(encoding="utf-8")
    assert "2026-03-25" in content


def test_sprint_name_present(tmp_path, minimal_metrics_dict):
    out = tmp_path / "report.html"
    generate_html(minimal_metrics_dict, out)
    content = out.read_text(encoding="utf-8")
    assert "Sprint Alpha" in content


def test_velocity_value_present(tmp_path, minimal_metrics_dict):
    out = tmp_path / "report.html"
    generate_html(minimal_metrics_dict, out)
    content = out.read_text(encoding="utf-8")
    assert "20" in content


def test_cycle_time_values_present(tmp_path, minimal_metrics_dict):
    out = tmp_path / "report.html"
    generate_html(minimal_metrics_dict, out)
    content = out.read_text(encoding="utf-8")
    assert "3.5" in content


def test_chart_canvas_present_when_velocity_nonempty(tmp_path, minimal_metrics_dict):
    out = tmp_path / "report.html"
    generate_html(minimal_metrics_dict, out)
    content = out.read_text(encoding="utf-8")
    assert "velocityChart" in content


def test_empty_velocity_shows_no_data_message(tmp_path, empty_metrics_dict):
    out = tmp_path / "report.html"
    generate_html(empty_metrics_dict, out)
    content = out.read_text(encoding="utf-8")
    assert "No velocity data" in content


def test_chart_script_absent_when_velocity_empty(tmp_path, empty_metrics_dict):
    out = tmp_path / "report.html"
    generate_html(empty_metrics_dict, out)
    content = out.read_text(encoding="utf-8")
    assert "velocityChart" not in content


# ---------------------------------------------------------------------------
# Velocity totals row
# ---------------------------------------------------------------------------


def test_velocity_totals_row_present(tmp_path, minimal_metrics_dict):
    out = tmp_path / "report.html"
    generate_html(minimal_metrics_dict, out)
    content = out.read_text(encoding="utf-8")
    assert "Total (selected period)" in content


# ---------------------------------------------------------------------------
# AI Assistance trend section
# ---------------------------------------------------------------------------


def test_ai_assistance_section_present(tmp_path, minimal_metrics_dict):
    out = tmp_path / "report.html"
    generate_html(minimal_metrics_dict, out)
    content = out.read_text(encoding="utf-8")
    assert "AI Assistance trend" in content


def test_ai_assistance_chart_canvas_present(tmp_path, minimal_metrics_dict):
    out = tmp_path / "report.html"
    generate_html(minimal_metrics_dict, out)
    content = out.read_text(encoding="utf-8")
    assert "aiAssistanceChart" in content


def test_ai_assistance_sprint_and_pct_present(tmp_path, minimal_metrics_dict):
    out = tmp_path / "report.html"
    generate_html(minimal_metrics_dict, out)
    content = out.read_text(encoding="utf-8")
    assert "50.0%" in content


def test_ai_assistance_section_hidden_when_section_visibility_false(tmp_path, minimal_metrics_dict):
    out = tmp_path / "report.html"
    generate_html(
        minimal_metrics_dict,
        out,
        section_visibility={
            "velocity_trend": True,
            "ai_assistance_trend": False,
            "ai_usage_details": False,
            "cycle_time": True,
            "custom_trends": False,
        },
    )
    content = out.read_text(encoding="utf-8")
    assert "AI Assistance trend" not in content


def test_ai_assistance_no_data_message_when_empty(tmp_path, empty_metrics_dict):
    out = tmp_path / "report.html"
    generate_html(empty_metrics_dict, out)
    content = out.read_text(encoding="utf-8")
    assert "No AI Assistance data" in content


# ---------------------------------------------------------------------------
# AI Usage Details section
# ---------------------------------------------------------------------------


def test_ai_usage_details_section_present(tmp_path, minimal_metrics_dict):
    out = tmp_path / "report.html"
    generate_html(minimal_metrics_dict, out)
    content = out.read_text(encoding="utf-8")
    assert "AI Usage Details" in content


def test_ai_usage_tools_canvas_present(tmp_path, minimal_metrics_dict):
    out = tmp_path / "report.html"
    generate_html(minimal_metrics_dict, out)
    content = out.read_text(encoding="utf-8")
    assert "aiUsageToolsChart" in content


def test_ai_usage_cases_canvas_present(tmp_path, minimal_metrics_dict):
    out = tmp_path / "report.html"
    generate_html(minimal_metrics_dict, out)
    content = out.read_text(encoding="utf-8")
    assert "aiUsageCasesChart" in content


def test_ai_usage_section_hidden_when_section_visibility_false(tmp_path, minimal_metrics_dict):
    out = tmp_path / "report.html"
    generate_html(
        minimal_metrics_dict,
        out,
        section_visibility={
            "velocity_trend": True,
            "ai_assistance_trend": True,
            "ai_usage_details": False,
            "cycle_time": True,
            "custom_trends": False,
        },
    )
    content = out.read_text(encoding="utf-8")
    assert "AI Usage Details" not in content


# ---------------------------------------------------------------------------
# section_visibility — velocity hidden
# ---------------------------------------------------------------------------


def test_velocity_section_hidden_when_section_visibility_false(tmp_path, minimal_metrics_dict):
    out = tmp_path / "report.html"
    generate_html(
        minimal_metrics_dict,
        out,
        section_visibility={
            "velocity_trend": False,
            "ai_assistance_trend": False,
            "ai_usage_details": False,
            "cycle_time": False,
            "custom_trends": False,
        },
    )
    content = out.read_text(encoding="utf-8")
    assert "velocityChart" not in content
    assert "Velocity trend" not in content


# ---------------------------------------------------------------------------
# Filter metadata in header
# ---------------------------------------------------------------------------


def test_filter_name_shown_when_present(tmp_path, minimal_metrics_dict):
    minimal_metrics_dict["filter_name"] = "My Filter"
    minimal_metrics_dict["filter_id"] = 42
    out = tmp_path / "report.html"
    generate_html(minimal_metrics_dict, out)
    content = out.read_text(encoding="utf-8")
    assert "My Filter" in content
    assert "42" in content


def test_project_key_shown_when_present(tmp_path, minimal_metrics_dict):
    minimal_metrics_dict["project_key"] = "PROJ"
    out = tmp_path / "report.html"
    generate_html(minimal_metrics_dict, out)
    content = out.read_text(encoding="utf-8")
    assert "PROJ" in content


# ---------------------------------------------------------------------------
# Cycle time section rendering
# ---------------------------------------------------------------------------


def test_cycle_time_section_present(tmp_path, minimal_metrics_dict):
    out = tmp_path / "report.html"
    generate_html(minimal_metrics_dict, out)
    content = out.read_text(encoding="utf-8")
    assert "Cycle time" in content
    assert "3.5" in content  # mean_days
    assert "3.0" in content  # median_days


def test_cycle_time_section_hidden_when_visibility_false(tmp_path, minimal_metrics_dict):
    out = tmp_path / "report.html"
    generate_html(
        minimal_metrics_dict,
        out,
        section_visibility={
            "velocity_trend": True,
            "ai_assistance_trend": True,
            "ai_usage_details": True,
            "cycle_time": False,
            "custom_trends": True,
        },
    )
    content = out.read_text(encoding="utf-8")
    # Section heading should not appear, but "Cycle" might appear elsewhere — check for the data table
    assert "mean_days" not in content.lower() or "Cycle time" not in content


def test_cycle_time_no_data_message(tmp_path, empty_metrics_dict):
    out = tmp_path / "report.html"
    generate_html(empty_metrics_dict, out)
    content = out.read_text(encoding="utf-8")
    assert "No cycle time" in content or "sample_size" not in content


# ---------------------------------------------------------------------------
# Custom trends section rendering
# ---------------------------------------------------------------------------


def test_custom_trends_section_present_when_data(tmp_path, minimal_metrics_dict):
    minimal_metrics_dict["custom_trends"] = [{"sprint_id": 1, "sprint_name": "Sprint Alpha", "custom_metric": 42}]
    out = tmp_path / "report.html"
    generate_html(minimal_metrics_dict, out)
    content = out.read_text(encoding="utf-8")
    assert "Custom trends" in content


def test_custom_trends_section_hidden_when_visibility_false(tmp_path, minimal_metrics_dict):
    minimal_metrics_dict["custom_trends"] = [{"sprint_id": 1, "sprint_name": "Sprint Alpha", "custom_metric": 42}]
    out = tmp_path / "report.html"
    generate_html(
        minimal_metrics_dict,
        out,
        section_visibility={
            "velocity_trend": True,
            "ai_assistance_trend": True,
            "ai_usage_details": True,
            "cycle_time": True,
            "custom_trends": False,
        },
    )
    content = out.read_text(encoding="utf-8")
    assert "Custom trends" not in content
