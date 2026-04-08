"""Tests for app.metrics: pure computation, no Jira connection required."""

from __future__ import annotations

import pytest

from app.core import metrics
from tests.conftest import make_issue, make_issue_with_labels, make_sprint

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# _is_done
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "status,expected",
    [
        ("Done", True),
        ("done", True),
        ("Closed", True),
        ("Resolved", True),
        ("Complete", True),
        ("In Progress", False),
        ("To Do", False),
        ("", False),
        ("Released", False),  # custom status, no resolutiondate
    ],
)
def test_is_done(status, expected):
    issue = make_issue("X-1", status=status)
    assert metrics._is_done(issue) is expected


def test_is_done_missing_fields():
    assert metrics._is_done({}) is False
    assert metrics._is_done({"fields": {}}) is False
    assert metrics._is_done({"fields": {"status": {}}}) is False


def test_is_done_resolutiondate_fallback():
    """Issues with resolutiondate are done regardless of status name (covers KANBAN custom statuses)."""
    issue = make_issue("K-1", status="Released")
    issue["fields"]["resolutiondate"] = "2024-03-01T10:00:00.000+0000"
    assert metrics._is_done(issue) is True


def test_is_done_no_resolutiondate_custom_status():
    """Custom terminal status name without resolutiondate is not considered done."""
    issue = make_issue("K-2", status="Released")
    assert metrics._is_done(issue) is False


def test_compute_velocity_kanban_periods():
    """KANBAN week periods with resolved issues (custom status + resolutiondate) count correctly."""
    period = {
        "id": "week-2024-W14",
        "name": "2024-W14",
        "startDate": "2024-04-01",
        "endDate": "2024-04-07",
    }
    issue = make_issue("K-1", status="Released", points=5.0)
    issue["fields"]["resolutiondate"] = "2024-04-03T10:00:00.000+0000"
    result = metrics.compute_velocity([period], {"week-2024-W14": [issue]})
    assert result[0]["velocity"] == 5.0
    assert result[0]["issue_count"] == 1


# ---------------------------------------------------------------------------
# _get_story_points
# ---------------------------------------------------------------------------


def test_get_story_points_numeric_float():
    issue = make_issue("X-1", points=8.0)
    assert metrics._get_story_points(issue) == 8.0


def test_get_story_points_integer_stored_as_int():
    issue = make_issue("X-1", points=None)
    issue["fields"]["customfield_10016"] = 3
    assert metrics._get_story_points(issue) == 3.0


def test_get_story_points_none():
    issue = make_issue("X-1", points=None)
    assert metrics._get_story_points(issue) == 0.0


def test_get_story_points_non_numeric_string():
    issue = make_issue("X-1", points=None)
    issue["fields"]["customfield_10016"] = "many"
    assert metrics._get_story_points(issue) == 0.0


def test_get_story_points_missing_field():
    issue = {"key": "X-1", "fields": {}}
    assert metrics._get_story_points(issue) == 0.0


def test_get_story_points_custom_field(monkeypatch):
    monkeypatch.setattr("app.core.schema.DEFAULT_STORY_POINTS_FIELD_ID", "customfield_99999")
    issue = {"key": "X-1", "fields": {"customfield_99999": 13.0}}
    assert metrics._get_story_points(issue) == 13.0


def test_get_story_points_nested_value_dict():
    issue = {"key": "X-1", "fields": {"customfield_10016": {"value": 8}}}
    assert metrics._get_story_points(issue) == 8.0


# ---------------------------------------------------------------------------
# compute_velocity
# ---------------------------------------------------------------------------


def test_compute_velocity_all_done():
    sprint = make_sprint(1, "Sprint 1")
    issues = [make_issue("X-1", "Done", 5.0), make_issue("X-2", "Done", 3.0)]
    result = metrics.compute_velocity([sprint], {1: issues})
    assert len(result) == 1
    assert result[0]["velocity"] == 8.0
    assert result[0]["issue_count"] == 2


def test_compute_velocity_mixed_statuses():
    sprint = make_sprint(1)
    issues = [
        make_issue("X-1", "Done", 5.0),
        make_issue("X-2", "In Progress", 3.0),
        make_issue("X-3", "To Do", 2.0),
    ]
    result = metrics.compute_velocity([sprint], {1: issues})
    assert result[0]["velocity"] == 5.0
    assert result[0]["issue_count"] == 1


def test_compute_velocity_no_issues():
    sprint = make_sprint(1)
    result = metrics.compute_velocity([sprint], {1: []})
    assert result[0]["velocity"] == 0.0
    assert result[0]["issue_count"] == 0


def test_compute_velocity_missing_sprint_id():
    sprint = {"name": "Bad Sprint"}  # no "id"
    result = metrics.compute_velocity([sprint], {})
    assert result == []


def test_compute_velocity_sprint_absent_from_issues_dict():
    sprint = make_sprint(42)
    result = metrics.compute_velocity([sprint], {})
    assert result[0]["velocity"] == 0.0


def test_compute_velocity_rounding():
    sprint = make_sprint(1)
    issues = [make_issue("X-1", "Done", 1.05), make_issue("X-2", "Done", 1.05)]
    result = metrics.compute_velocity([sprint], {1: issues})
    assert result[0]["velocity"] == round(2.1, 1)


def test_compute_velocity_preserves_sprint_name():
    sprint = make_sprint(7, "My Sprint")
    result = metrics.compute_velocity([sprint], {7: []})
    assert result[0]["sprint_name"] == "My Sprint"


# ---------------------------------------------------------------------------
# build_metrics_dict
# ---------------------------------------------------------------------------


def test_build_metrics_dict_keys():
    sprint = make_sprint(1)
    issue = make_issue("X-1", "Done", 5.0)
    result = metrics.build_metrics_dict([sprint], {1: [issue]})
    expected_keys = {
        "velocity",
        "generated_at",
        "ai_assistance_trend",
        "ai_usage_details",
        "ai_assisted_label",
        "ai_exclude_labels",
        "dau",
        "schema_name",
        "filter_name",
        "filter_id",
        "filter_jql",
        "project_key",
        "project_type",
        "estimation_type",
    }
    assert expected_keys.issubset(result.keys())


def test_build_metrics_dict_generated_at_is_iso():
    from datetime import datetime

    result = metrics.build_metrics_dict([], {})
    ts = result["generated_at"]
    # Should parse without error
    parsed = datetime.fromisoformat(ts)
    assert parsed.tzinfo is not None


# ---------------------------------------------------------------------------
# _parse_iso
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "input_val,expected_not_none",
    [
        ("2026-03-01T10:00:00+00:00", True),
        ("2026-03-01T10:00:00Z", True),
        ("", False),
        (None, False),
        ("not-a-date", False),
    ],
)
def test_parse_iso(input_val, expected_not_none):
    result = metrics._parse_iso(input_val)
    if expected_not_none:
        assert result is not None
        assert result.tzinfo is not None
    else:
        assert result is None


# ---------------------------------------------------------------------------
# _get_labels
# ---------------------------------------------------------------------------


def test_get_labels_normal():
    issue = make_issue_with_labels("X-1", labels=["bug", "AI_assistance"])
    assert metrics._get_labels(issue) == ["bug", "AI_assistance"]


def test_get_labels_empty_list():
    issue = make_issue_with_labels("X-1", labels=[])
    assert metrics._get_labels(issue) == []


def test_get_labels_missing_key():
    issue = {"key": "X-1", "fields": {}}
    assert metrics._get_labels(issue) == []


def test_get_labels_missing_fields():
    issue = {"key": "X-1"}
    assert metrics._get_labels(issue) == []


# ---------------------------------------------------------------------------
# compute_ai_assistance_trend
# ---------------------------------------------------------------------------


def test_ai_trend_ai_labeled_done_issues():
    sprint = make_sprint(1, "S1")
    issues = [
        make_issue_with_labels("X-1", "Done", 5.0, ["AI_assistance"]),
        make_issue_with_labels("X-2", "Done", 3.0, []),
    ]
    result = metrics.compute_ai_assistance_trend(
        [sprint],
        {1: issues},
        ai_assisted_label="AI_assistance",
        ai_exclude_labels=[],
    )
    assert len(result) == 1
    assert result[0]["total_sp"] == 8.0
    assert result[0]["ai_sp"] == 5.0
    assert result[0]["ai_pct"] == 62.5


def test_ai_trend_no_done_issues():
    sprint = make_sprint(1)
    issues = [make_issue_with_labels("X-1", "In Progress", 5.0, ["AI_assistance"])]
    result = metrics.compute_ai_assistance_trend(
        [sprint],
        {1: issues},
        ai_assisted_label="AI_assistance",
        ai_exclude_labels=[],
    )
    assert result[0]["total_sp"] == 0.0
    assert result[0]["ai_pct"] == 0.0


def test_ai_trend_exclude_labels():
    sprint = make_sprint(1)
    issues = [
        make_issue_with_labels("X-1", "Done", 5.0, ["AI_assistance"]),
        make_issue_with_labels("X-2", "Done", 3.0, ["exclude_me"]),
    ]
    result = metrics.compute_ai_assistance_trend(
        [sprint],
        {1: issues},
        ai_assisted_label="AI_assistance",
        ai_exclude_labels=["exclude_me"],
    )
    assert result[0]["total_sp"] == 5.0  # X-2 excluded from denominator
    assert result[0]["ai_sp"] == 5.0
    assert result[0]["ai_pct"] == 100.0


def test_ai_trend_multiple_sprints():
    s1, s2 = make_sprint(1, "S1"), make_sprint(2, "S2")
    i1 = [make_issue_with_labels("X-1", "Done", 5.0, ["AI_assistance"])]
    i2 = [make_issue_with_labels("X-2", "Done", 3.0, [])]
    result = metrics.compute_ai_assistance_trend(
        [s1, s2],
        {1: i1, 2: i2},
        ai_assisted_label="AI_assistance",
        ai_exclude_labels=[],
    )
    assert len(result) == 2
    assert result[0]["ai_sp"] == 5.0
    assert result[1]["ai_sp"] == 0.0


def test_ai_trend_no_ai_label():
    sprint = make_sprint(1)
    issues = [make_issue_with_labels("X-1", "Done", 5.0, [])]
    result = metrics.compute_ai_assistance_trend(
        [sprint],
        {1: issues},
        ai_assisted_label="AI_assistance",
        ai_exclude_labels=[],
    )
    assert result[0]["ai_sp"] == 0.0
    assert result[0]["ai_pct"] == 0.0


# ---------------------------------------------------------------------------
# compute_ai_usage_details
# ---------------------------------------------------------------------------


def test_ai_usage_tool_breakdown():
    sprint = make_sprint(1)
    issues = [
        make_issue_with_labels("X-1", "Done", 5.0, ["AI_assistance", "AI_Tool_Copilot"]),
        make_issue_with_labels("X-2", "Done", 3.0, ["AI_assistance", "AI_Tool_ChatGPT"]),
    ]
    result = metrics.compute_ai_usage_details(
        [sprint],
        {1: issues},
        ai_assisted_label="AI_assistance",
        ai_tool_labels=["AI_Tool_Copilot", "AI_Tool_ChatGPT"],
        ai_action_labels=[],
    )
    assert result["ai_assisted_issue_count"] == 2
    assert len(result["tool_breakdown"]) == 2
    labels = [r["label"] for r in result["tool_breakdown"]]
    assert "AI_Tool_Copilot" in labels
    assert "AI_Tool_ChatGPT" in labels


def test_ai_usage_action_breakdown():
    sprint = make_sprint(1)
    issues = [
        make_issue_with_labels("X-1", "Done", 5.0, ["AI_assistance", "AI_Case_CodeGen"]),
    ]
    result = metrics.compute_ai_usage_details(
        [sprint],
        {1: issues},
        ai_assisted_label="AI_assistance",
        ai_tool_labels=[],
        ai_action_labels=["AI_Case_CodeGen", "AI_Case_Review"],
    )
    assert len(result["action_breakdown"]) == 1
    assert result["action_breakdown"][0]["label"] == "AI_Case_CodeGen"
    assert result["action_breakdown"][0]["count"] == 1


def test_ai_usage_dedup_across_sprints():
    s1, s2 = make_sprint(1), make_sprint(2)
    issue = make_issue_with_labels("X-1", "Done", 5.0, ["AI_assistance", "AI_Tool_Copilot"])
    result = metrics.compute_ai_usage_details(
        [s1, s2],
        {1: [issue], 2: [issue]},  # same issue in two sprints
        ai_assisted_label="AI_assistance",
        ai_tool_labels=["AI_Tool_Copilot"],
        ai_action_labels=[],
    )
    assert result["ai_assisted_issue_count"] == 1  # deduplicated


def test_ai_usage_no_ai_issues():
    sprint = make_sprint(1)
    issues = [make_issue_with_labels("X-1", "Done", 5.0, [])]
    result = metrics.compute_ai_usage_details(
        [sprint],
        {1: issues},
        ai_assisted_label="AI_assistance",
        ai_tool_labels=["AI_Tool_Copilot"],
        ai_action_labels=[],
    )
    assert result["ai_assisted_issue_count"] == 0
    assert result["tool_breakdown"] == []


def test_ai_usage_empty_labels():
    sprint = make_sprint(1)
    issues = [make_issue_with_labels("X-1", "Done", 5.0, ["AI_assistance"])]
    result = metrics.compute_ai_usage_details(
        [sprint],
        {1: issues},
        ai_assisted_label="AI_assistance",
        ai_tool_labels=[],
        ai_action_labels=[],
    )
    assert result["ai_assisted_issue_count"] == 1
    assert result["tool_breakdown"] == []
    assert result["action_breakdown"] == []


# ---------------------------------------------------------------------------
# Schema-driven parameters
# ---------------------------------------------------------------------------


def test_get_story_points_with_custom_field():
    issue = {"key": "X-1", "fields": {"customfield_99": 13.0}}
    assert metrics._get_story_points(issue, story_points_field="customfield_99") == 13.0


def test_get_story_points_custom_field_missing():
    issue = {"key": "X-1", "fields": {"customfield_10016": 5.0}}
    assert metrics._get_story_points(issue, story_points_field="customfield_99") == 0.0


def test_is_done_with_custom_statuses():
    issue = make_issue("X-1", status="Finished")
    assert metrics._is_done(issue) is False
    assert metrics._is_done(issue, done_statuses=frozenset(("finished",))) is True


def test_is_done_custom_statuses_case_insensitive():
    issue = make_issue("X-1", status="SHIPPED")
    assert metrics._is_done(issue, done_statuses=frozenset(("shipped",))) is True


def test_compute_velocity_custom_field_and_statuses():
    sprint = make_sprint(1)
    issues = [
        {"key": "X-1", "fields": {"status": {"name": "Shipped"}, "cf_sp": 8.0}},
        {"key": "X-2", "fields": {"status": {"name": "Done"}, "cf_sp": 3.0}},
    ]
    result = metrics.compute_velocity(
        [sprint],
        {1: issues},
        story_points_field="cf_sp",
        done_statuses=frozenset(("shipped",)),
    )
    assert result[0]["velocity"] == 8.0
    assert result[0]["issue_count"] == 1


def test_build_metrics_dict_with_schema():
    schema = {
        "schema_name": "Test Schema",
        "fields": {"story_points": {"id": "cf_sp"}},
        "status_mapping": {
            "done_statuses": ["Shipped"],
            "in_progress_statuses": ["Active"],
        },
    }
    sprint = make_sprint(1)
    issue = {"key": "X-1", "fields": {"status": {"name": "Shipped"}, "cf_sp": 10.0}}
    result = metrics.build_metrics_dict([sprint], {1: [issue]}, schema=schema)
    assert result["schema_name"] == "Test Schema"
    assert result["velocity"][0]["velocity"] == 10.0
    assert result["velocity"][0]["issue_count"] == 1


def test_build_metrics_dict_without_schema_backward_compat():
    sprint = make_sprint(1)
    issue = make_issue("X-1", "Done", 5.0)
    result = metrics.build_metrics_dict([sprint], {1: [issue]})
    assert result["schema_name"] is None
    assert result["velocity"][0]["velocity"] == 5.0


def test_build_metrics_dict_jira_tickets_velocity_uses_issue_count(monkeypatch):
    monkeypatch.setattr("app.core.config.ESTIMATION_TYPE", "JiraTickets")
    sprint = make_sprint(1, "Sprint 1")
    issues = [
        make_issue("X-1", "Done", 5.0),
        make_issue("X-2", "Done", 3.0),
        make_issue("X-3", "In Progress", 2.0),
    ]
    result = metrics.build_metrics_dict([sprint], {1: issues})
    row = result["velocity"][0]
    assert row["issue_count"] == 2
    assert row["velocity"] == 2, "JiraTickets mode should use issue_count as velocity"


def test_build_metrics_dict_story_points_velocity_unchanged(monkeypatch):
    monkeypatch.setattr("app.core.config.ESTIMATION_TYPE", "StoryPoints")
    sprint = make_sprint(1, "Sprint 1")
    issues = [make_issue("X-1", "Done", 5.0), make_issue("X-2", "Done", 3.0)]
    result = metrics.build_metrics_dict([sprint], {1: issues})
    row = result["velocity"][0]
    assert row["velocity"] == 8.0, "StoryPoints mode should sum story points"
    assert row["issue_count"] == 2
