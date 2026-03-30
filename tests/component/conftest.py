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
        "schema_name": None,
        "filter_name": None,
        "filter_id": None,
        "filter_jql": None,
        "project_key": None,
        "dau": {
            "team_avg": 3.5,
            "team_avg_pct": 70.0,
            "response_count": 2,
            "by_role": [{"role": "Developer", "avg": 4.25, "avg_pct": 85.0, "count": 2}],
            "breakdown": [
                {"answer": "Every day (5 days)", "count": 1, "pct": 50.0},
                {"answer": "Most days (3\u20134 days)", "count": 1, "pct": 50.0},
            ],
        },
        "dau_trend": [
            {
                "week": "2026-W13",
                "team_avg": 3.5,
                "team_avg_pct": 70.0,
                "response_count": 2,
            }
        ],
    }


@pytest.fixture
def empty_metrics_dict() -> dict:
    return {
        "generated_at": "2026-03-25T12:00:00+00:00",
        "velocity": [],
        "ai_assisted_label": "AI_assistance",
        "ai_exclude_labels": [],
        "ai_assistance_trend": [],
        "ai_usage_details": {
            "ai_assisted_issue_count": 0,
            "tool_breakdown": [],
            "action_breakdown": [],
        },
        "schema_name": None,
        "filter_name": None,
        "filter_id": None,
        "filter_jql": None,
        "project_key": None,
        "dau": {"team_avg": None, "team_avg_pct": None, "response_count": 0, "by_role": [], "breakdown": []},
        "dau_trend": [],
    }
