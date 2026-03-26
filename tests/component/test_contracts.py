"""Contract tests: verify data shapes crossing module boundaries."""
from __future__ import annotations

import re

import pytest

from app import metrics
from app.report_html import TEMPLATES_DIR
from tests.conftest import (
    make_sprint,
    make_issue,
    make_issue_with_labels,
    make_issue_with_changelog,
)

pytestmark = pytest.mark.component


# ---------------------------------------------------------------------------
# Sprint dict shape
# ---------------------------------------------------------------------------

def test_sprint_factory_has_keys_used_by_compute_velocity():
    sprint = make_sprint(1, "Sprint 1", "2026-01-01", "2026-01-14")
    required_keys = {"id", "name", "startDate", "endDate"}
    assert required_keys.issubset(sprint.keys())


def test_sprint_factory_has_keys_used_by_ai_trend():
    sprint = make_sprint(1, "Sprint 1", "2026-01-01", "2026-01-14")
    # compute_ai_assistance_trend accesses the same keys as compute_velocity
    assert sprint.get("id") is not None
    assert "name" in sprint
    assert "startDate" in sprint
    assert "endDate" in sprint


# ---------------------------------------------------------------------------
# Issue dict shape
# ---------------------------------------------------------------------------

def test_issue_factory_matches_is_done_expectations():
    issue = make_issue("X-1", "Done", 5.0)
    assert metrics._is_done(issue) is True
    assert metrics._get_story_points(issue) == 5.0


def test_issue_with_labels_factory_matches_get_labels():
    issue = make_issue_with_labels("X-1", labels=["AI_assistance", "AI_Tool_Copilot"])
    labels = metrics._get_labels(issue)
    assert "AI_assistance" in labels
    assert "AI_Tool_Copilot" in labels


# ---------------------------------------------------------------------------
# metrics_dict shape
# ---------------------------------------------------------------------------

def test_build_metrics_dict_has_all_expected_keys():
    sprint = make_sprint(1)
    issue = make_issue("X-1", "Done", 5.0)
    cl = make_issue_with_changelog("X-1", "2026-03-01T00:00:00+00:00", "2026-03-03T00:00:00+00:00")
    result = metrics.build_metrics_dict([sprint], {1: [issue]}, [cl])
    expected_keys = {
        "velocity", "cycle_time", "custom_trends", "generated_at",
        "ai_assistance_trend", "ai_usage_details",
        "ai_assisted_label", "ai_exclude_labels",
        "filter_name", "filter_id", "filter_jql", "project_key",
    }
    assert set(result.keys()) == expected_keys


def test_velocity_row_has_required_keys():
    sprint = make_sprint(1)
    issue = make_issue("X-1", "Done", 5.0)
    result = metrics.build_metrics_dict([sprint], {1: [issue]}, [])
    row = result["velocity"][0]
    required = {"sprint_id", "sprint_name", "start_date", "end_date", "velocity", "issue_count"}
    assert required.issubset(row.keys())


def test_ai_trend_row_has_required_keys():
    sprint = make_sprint(1)
    issue = make_issue("X-1", "Done", 5.0)
    result = metrics.build_metrics_dict([sprint], {1: [issue]}, [])
    row = result["ai_assistance_trend"][0]
    required = {"sprint_id", "sprint_name", "start_date", "end_date", "total_sp", "ai_sp", "ai_pct"}
    assert required.issubset(row.keys())


# ---------------------------------------------------------------------------
# cycle_time dict shape
# ---------------------------------------------------------------------------

def test_cycle_time_has_exact_keys():
    result = metrics.compute_cycle_time([])
    expected = {"mean_days", "median_days", "min_days", "max_days", "sample_size", "values"}
    assert set(result.keys()) == expected


# ---------------------------------------------------------------------------
# ai_usage_details shape
# ---------------------------------------------------------------------------

def test_ai_usage_details_shape():
    sprint = make_sprint(1)
    issue = make_issue_with_labels("X-1", "Done", 5.0, ["AI_assistance", "AI_Tool_Copilot"])
    result = metrics.compute_ai_usage_details(
        [sprint], {1: [issue]},
        ai_assisted_label="AI_assistance",
        ai_tool_labels=["AI_Tool_Copilot"],
        ai_action_labels=["AI_Case_CodeGen"],
    )
    assert "ai_assisted_issue_count" in result
    assert "tool_breakdown" in result
    assert "action_breakdown" in result
    if result["tool_breakdown"]:
        row = result["tool_breakdown"][0]
        assert {"label", "count", "pct"} == set(row.keys())


# ---------------------------------------------------------------------------
# Template contract: metrics.* references match build_metrics_dict output
# ---------------------------------------------------------------------------

def test_template_variables_exist_in_metrics_dict():
    """Parse report.html.j2 for metrics.X references and verify they exist in build_metrics_dict output."""
    template_path = TEMPLATES_DIR / "report.html.j2"
    content = template_path.read_text(encoding="utf-8")

    # Find all metrics.<key> references (top-level only)
    pattern = re.compile(r"metrics\.(\w+)")
    referenced_keys = set(pattern.findall(content))

    # Build a real metrics dict
    sprint = make_sprint(1, "S1", "2026-01-01", "2026-01-14")
    issue = make_issue("X-1", "Done", 5.0)
    cl = make_issue_with_changelog("X-1", "2026-03-01T00:00:00+00:00", "2026-03-03T00:00:00+00:00")
    metrics_dict = metrics.build_metrics_dict([sprint], {1: [issue]}, [cl])

    for key in referenced_keys:
        assert key in metrics_dict, f"Template references metrics.{key} but it's missing from build_metrics_dict()"


# ---------------------------------------------------------------------------
# cert_utils.validate_cert response shape
# ---------------------------------------------------------------------------

def _make_test_pem(days: int = 90) -> bytes:
    import datetime
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.x509.oid import NameOID

    key = ec.generate_private_key(ec.SECP256R1())
    now = datetime.datetime.now(datetime.timezone.utc)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "test.example.com")])
    cert = (
        x509.CertificateBuilder()
        .subject_name(name).issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - datetime.timedelta(days=1))
        .not_valid_after(now + datetime.timedelta(days=days))
        .sign(key, hashes.SHA256())
    )
    return cert.public_bytes(serialization.Encoding.PEM)


def test_validate_cert_response_has_all_keys_when_valid(tmp_path):
    """validate_cert() returns the full set of keys consumed by _handle_cert_status."""
    from app.cert_utils import validate_cert

    cert_file = tmp_path / "jira_ca_bundle.pem"
    cert_file.write_bytes(_make_test_pem(90))

    result = validate_cert(cert_file)

    assert {"valid", "expires_at", "days_remaining", "subject"}.issubset(result.keys())
    assert result["valid"] is True
    assert isinstance(result["expires_at"], str)
    assert isinstance(result["days_remaining"], int)
    assert result["subject"] == "CN=test.example.com"


def test_validate_cert_response_has_all_keys_when_missing(tmp_path):
    """validate_cert() on a missing file returns the error-shape consumed by _handle_cert_status."""
    from app.cert_utils import validate_cert

    result = validate_cert(tmp_path / "nonexistent.pem")

    assert {"valid", "expires_at", "days_remaining", "subject", "error"}.issubset(result.keys())
    assert result["valid"] is False
