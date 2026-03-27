"""Tests for app.metrics: pure computation, no Jira connection required."""

from __future__ import annotations

import pytest

from app.core import metrics
from tests.conftest import make_issue, make_issue_with_changelog, make_issue_with_labels, make_sprint

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
    ],
)
def test_is_done(status, expected):
    issue = make_issue("X-1", status=status)
    assert metrics._is_done(issue) is expected


def test_is_done_missing_fields():
    assert metrics._is_done({}) is False
    assert metrics._is_done({"fields": {}}) is False
    assert metrics._is_done({"fields": {"status": {}}}) is False


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
# compute_cycle_time
# ---------------------------------------------------------------------------


def test_compute_cycle_time_empty():
    result = metrics.compute_cycle_time([])
    assert result["sample_size"] == 0
    assert result["mean_days"] is None
    assert result["values"] == []


def test_compute_cycle_time_single_issue():
    issue = make_issue_with_changelog(
        "X-1",
        in_progress_ts="2026-03-01T09:00:00+00:00",
        done_ts="2026-03-03T09:00:00+00:00",  # 2 days exactly
    )
    result = metrics.compute_cycle_time([issue])
    assert result["sample_size"] == 1
    assert result["mean_days"] == 2.0
    assert result["min_days"] == 2.0
    assert result["max_days"] == 2.0


def test_compute_cycle_time_reversed_timestamps_excluded():
    """done before in_progress → should be excluded (done_at < in_progress_at)."""
    issue = make_issue_with_changelog(
        "X-1",
        in_progress_ts="2026-03-05T09:00:00+00:00",
        done_ts="2026-03-01T09:00:00+00:00",  # earlier than in_progress
    )
    result = metrics.compute_cycle_time([issue])
    assert result["sample_size"] == 0


def test_compute_cycle_time_odd_median():
    issues = [
        make_issue_with_changelog("X-1", "2026-03-01T00:00:00+00:00", "2026-03-02T00:00:00+00:00"),  # 1d
        make_issue_with_changelog("X-2", "2026-03-01T00:00:00+00:00", "2026-03-04T00:00:00+00:00"),  # 3d
        make_issue_with_changelog("X-3", "2026-03-01T00:00:00+00:00", "2026-03-06T00:00:00+00:00"),  # 5d
    ]
    result = metrics.compute_cycle_time(issues)
    assert result["median_days"] == 3.0


def test_compute_cycle_time_even_median():
    issues = [
        make_issue_with_changelog("X-1", "2026-03-01T00:00:00+00:00", "2026-03-03T00:00:00+00:00"),  # 2d
        make_issue_with_changelog("X-2", "2026-03-01T00:00:00+00:00", "2026-03-05T00:00:00+00:00"),  # 4d
    ]
    result = metrics.compute_cycle_time(issues)
    assert result["median_days"] == 3.0


def test_cycle_time_uses_first_done_after_in_progress():
    issue = {
        "key": "X-1",
        "fields": {"status": {"name": "Done"}},
        "changelog": {
            "histories": [
                {
                    "created": "2026-03-05T00:00:00+00:00",
                    "items": [{"field": "status", "fromString": "Review", "toString": "Done"}],
                },
                {
                    "created": "2026-03-01T00:00:00+00:00",
                    "items": [{"field": "status", "fromString": "To Do", "toString": "In Progress"}],
                },
                {
                    "created": "2026-03-03T00:00:00+00:00",
                    "items": [{"field": "status", "fromString": "In Progress", "toString": "Done"}],
                },
            ]
        },
    }

    assert metrics._cycle_time_from_changelog(issue) == 2.0


# ---------------------------------------------------------------------------
# get_done_issue_keys_for_changelog
# ---------------------------------------------------------------------------


def test_get_done_issue_keys_filters_non_done():
    sprint = make_sprint(1)
    issues = [make_issue("X-1", "Done"), make_issue("X-2", "In Progress")]
    result = metrics.get_done_issue_keys_for_changelog([sprint], {1: issues})
    assert result == ["X-1"]


def test_get_done_issue_keys_deduplicates_across_sprints():
    s1, s2 = make_sprint(1), make_sprint(2)
    issues = [make_issue("X-1", "Done")]
    result = metrics.get_done_issue_keys_for_changelog([s1, s2], {1: issues, 2: issues})
    assert result.count("X-1") == 1


def test_get_done_issue_keys_respects_max_count():
    sprint = make_sprint(1)
    issues = [make_issue(f"X-{i}", "Done") for i in range(10)]
    result = metrics.get_done_issue_keys_for_changelog([sprint], {1: issues}, max_count=3)
    assert len(result) == 3


# ---------------------------------------------------------------------------
# build_metrics_dict
# ---------------------------------------------------------------------------


def test_build_metrics_dict_keys():
    sprint = make_sprint(1)
    issue = make_issue("X-1", "Done", 5.0)
    issue_cl = make_issue_with_changelog("X-1", "2026-03-01T00:00:00+00:00", "2026-03-03T00:00:00+00:00")
    result = metrics.build_metrics_dict([sprint], {1: [issue]}, [issue_cl])
    expected_keys = {
        "velocity",
        "cycle_time",
        "custom_trends",
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
    }
    assert set(result.keys()) == expected_keys


def test_build_metrics_dict_generated_at_is_iso():
    from datetime import datetime

    result = metrics.build_metrics_dict([], {}, [])
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
# _cycle_time_from_changelog
# ---------------------------------------------------------------------------


def test_cycle_time_no_changelog():
    issue = {"key": "X-1", "fields": {}}
    assert metrics._cycle_time_from_changelog(issue) is None


def test_cycle_time_empty_histories():
    issue = {"key": "X-1", "fields": {}, "changelog": {"histories": []}}
    assert metrics._cycle_time_from_changelog(issue) is None


def test_cycle_time_only_in_progress():
    issue = {
        "key": "X-1",
        "fields": {},
        "changelog": {
            "histories": [
                {
                    "created": "2026-03-01T10:00:00+00:00",
                    "items": [{"field": "status", "fromString": "To Do", "toString": "In Progress"}],
                }
            ]
        },
    }
    assert metrics._cycle_time_from_changelog(issue) is None


def test_cycle_time_only_done():
    issue = {
        "key": "X-1",
        "fields": {},
        "changelog": {
            "histories": [
                {
                    "created": "2026-03-03T10:00:00+00:00",
                    "items": [{"field": "status", "fromString": "In Progress", "toString": "Done"}],
                }
            ]
        },
    }
    assert metrics._cycle_time_from_changelog(issue) is None


def test_cycle_time_multiple_transitions():
    issue = {
        "key": "X-1",
        "fields": {},
        "changelog": {
            "histories": [
                {
                    "created": "2026-03-01T10:00:00+00:00",
                    "items": [{"field": "status", "fromString": "To Do", "toString": "In Progress"}],
                },
                {
                    "created": "2026-03-02T10:00:00+00:00",
                    "items": [{"field": "status", "fromString": "In Progress", "toString": "To Do"}],
                },
                {
                    "created": "2026-03-03T10:00:00+00:00",
                    "items": [{"field": "status", "fromString": "To Do", "toString": "In Progress"}],
                },
                {
                    "created": "2026-03-05T10:00:00+00:00",
                    "items": [{"field": "status", "fromString": "In Progress", "toString": "Done"}],
                },
            ]
        },
    }
    result = metrics._cycle_time_from_changelog(issue)
    # First In Progress: March 1, Done: March 5 → 4 days
    assert result == 4.0


def test_cycle_time_non_status_fields_ignored():
    issue = {
        "key": "X-1",
        "fields": {},
        "changelog": {
            "histories": [
                {
                    "created": "2026-03-01T10:00:00+00:00",
                    "items": [
                        {"field": "priority", "fromString": "Low", "toString": "High"},
                        {"field": "status", "fromString": "To Do", "toString": "In Progress"},
                    ],
                },
                {
                    "created": "2026-03-03T10:00:00+00:00",
                    "items": [
                        {"field": "assignee", "fromString": "Alice", "toString": "Bob"},
                        {"field": "status", "fromString": "In Progress", "toString": "Done"},
                    ],
                },
            ]
        },
    }
    result = metrics._cycle_time_from_changelog(issue)
    assert result == 2.0


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


def test_cycle_time_custom_statuses():
    issue = {
        "key": "X-1",
        "fields": {},
        "changelog": {
            "histories": [
                {
                    "created": "2026-03-01T10:00:00+00:00",
                    "items": [{"field": "status", "fromString": "To Do", "toString": "Working"}],
                },
                {
                    "created": "2026-03-03T10:00:00+00:00",
                    "items": [{"field": "status", "fromString": "Working", "toString": "Shipped"}],
                },
            ]
        },
    }
    result = metrics._cycle_time_from_changelog(
        issue,
        done_statuses=frozenset(("shipped",)),
        in_progress_statuses=frozenset(("working",)),
    )
    assert result == 2.0


def test_cycle_time_default_statuses_unchanged():
    issue = make_issue_with_changelog(
        "X-1",
        "2026-03-01T09:00:00+00:00",
        "2026-03-03T09:00:00+00:00",
    )
    assert metrics._cycle_time_from_changelog(issue) == 2.0


def test_compute_cycle_time_with_custom_statuses():
    issue = {
        "key": "X-1",
        "fields": {},
        "changelog": {
            "histories": [
                {
                    "created": "2026-03-01T10:00:00+00:00",
                    "items": [{"field": "status", "fromString": "Backlog", "toString": "Active"}],
                },
                {
                    "created": "2026-03-04T10:00:00+00:00",
                    "items": [{"field": "status", "fromString": "Active", "toString": "Finished"}],
                },
            ]
        },
    }
    result = metrics.compute_cycle_time(
        [issue],
        done_statuses=frozenset(("finished",)),
        in_progress_statuses=frozenset(("active",)),
    )
    assert result["sample_size"] == 1
    assert result["mean_days"] == 3.0


def test_get_done_issue_keys_custom_statuses():
    sprint = make_sprint(1)
    issues = [
        {"key": "X-1", "fields": {"status": {"name": "Shipped"}}},
        {"key": "X-2", "fields": {"status": {"name": "Done"}}},
    ]
    result = metrics.get_done_issue_keys_for_changelog(
        [sprint],
        {1: issues},
        done_statuses=frozenset(("shipped",)),
    )
    assert result == ["X-1"]


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
    result = metrics.build_metrics_dict([sprint], {1: [issue]}, [], schema=schema)
    assert result["schema_name"] == "Test Schema"
    assert result["velocity"][0]["velocity"] == 10.0
    assert result["velocity"][0]["issue_count"] == 1


def test_build_metrics_dict_without_schema_backward_compat():
    sprint = make_sprint(1)
    issue = make_issue("X-1", "Done", 5.0)
    result = metrics.build_metrics_dict([sprint], {1: [issue]}, [])
    assert result["schema_name"] is None
    assert result["velocity"][0]["velocity"] == 5.0


# ---------------------------------------------------------------------------
# compute_custom_trends (placeholder)
# ---------------------------------------------------------------------------


def test_compute_custom_trends_returns_empty_list():
    assert metrics.compute_custom_trends([], {}) == []
