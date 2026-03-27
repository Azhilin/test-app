"""Component-layer fixtures."""

from __future__ import annotations

import pytest


@pytest.fixture
def minimal_metrics_dict() -> dict:
    return {
        "generated_at": "2026-03-25T12:00:00+00:00",
        "velocity": [
            {
                "sprint_id": 1,
                "sprint_name": "Sprint Alpha",
                "start_date": "2026-03-01T00:00:00.000Z",
                "end_date": "2026-03-15T00:00:00.000Z",
                "velocity": 20.0,
                "issue_count": 4,
            }
        ],
        "cycle_time": {
            "mean_days": 3.5,
            "median_days": 3.0,
            "min_days": 1.0,
            "max_days": 6.0,
            "sample_size": 4,
            "values": [1.0, 3.0, 4.0, 6.0],
        },
        "custom_trends": [],
        "ai_assisted_label": "AI_assistance",
        "ai_exclude_labels": [],
        "ai_assistance_trend": [
            {
                "sprint_id": 1,
                "sprint_name": "Sprint Alpha",
                "start_date": "2026-03-01T00:00:00.000Z",
                "end_date": "2026-03-15T00:00:00.000Z",
                "total_sp": 20.0,
                "ai_sp": 10.0,
                "ai_pct": 50.0,
            }
        ],
        "ai_usage_details": {
            "ai_assisted_issue_count": 2,
            "tool_breakdown": [
                {"label": "AI_Tool_Copilot", "count": 2, "pct": 100.0},
            ],
            "action_breakdown": [
                {"label": "AI_Case_CodeGen", "count": 1, "pct": 50.0},
                {"label": "AI_Case_Review", "count": 1, "pct": 50.0},
            ],
        },
        "filter_name": None,
        "filter_id": None,
        "filter_jql": None,
        "project_key": None,
    }


@pytest.fixture
def empty_metrics_dict() -> dict:
    return {
        "generated_at": "2026-03-25T12:00:00+00:00",
        "velocity": [],
        "cycle_time": {
            "mean_days": None,
            "median_days": None,
            "min_days": None,
            "max_days": None,
            "sample_size": 0,
            "values": [],
        },
        "custom_trends": [],
        "ai_assisted_label": "AI_assistance",
        "ai_exclude_labels": [],
        "ai_assistance_trend": [],
        "ai_usage_details": {
            "ai_assisted_issue_count": 0,
            "tool_breakdown": [],
            "action_breakdown": [],
        },
        "filter_name": None,
        "filter_id": None,
        "filter_jql": None,
        "project_key": None,
    }
