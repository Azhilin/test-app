"""Component tests for report generation performance (NFR-P-001).

Verifies that building metrics and rendering both HTML and Markdown
reports for a realistic dataset (10 sprints × 50 issues) completes
within 5 seconds.
"""

from __future__ import annotations

import time

import pytest

from app.core.metrics import build_metrics_dict
from app.reporters.report_html import generate_html
from app.reporters.report_md import generate_md
from tests.conftest import make_issue, make_sprint

pytestmark = pytest.mark.component

_SPRINT_COUNT = 10
_ISSUES_PER_SPRINT = 50
_TIME_LIMIT_S = 5.0


def test_report_generation_completes_within_time_limit(tmp_path):
    """build_metrics_dict + generate_html + generate_md finish in under 5 s."""
    sprints = [make_sprint(i, name=f"Sprint {i}") for i in range(1, _SPRINT_COUNT + 1)]
    sprint_issues = {
        s["id"]: [make_issue(f"PERF-{s['id']}-{j}", points=5.0) for j in range(_ISSUES_PER_SPRINT)] for s in sprints
    }

    start = time.monotonic()
    metrics = build_metrics_dict(sprints, sprint_issues, [])
    generate_html(metrics, tmp_path / "report.html")
    generate_md(metrics, tmp_path / "report.md")
    elapsed = time.monotonic() - start

    assert elapsed < _TIME_LIMIT_S, f"Report generation took {elapsed:.2f}s, expected < {_TIME_LIMIT_S}s"
