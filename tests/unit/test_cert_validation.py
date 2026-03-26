"""Unit tests for app.cert_utils.validate_cert."""
from __future__ import annotations

import datetime
from pathlib import Path

import pytest

from app.cert_utils import validate_cert

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Helpers — generate synthetic PEM certs without touching the filesystem
# ---------------------------------------------------------------------------

def _make_pem(common_name: str, days_from_now: int) -> bytes:
    """Build a self-signed PEM certificate valid for *days_from_now* days."""
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.x509.oid import NameOID

    key = ec.generate_private_key(ec.SECP256R1())
    now = datetime.datetime.now(datetime.timezone.utc)
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, common_name),
    ])
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - datetime.timedelta(days=1))
        .not_valid_after(now + datetime.timedelta(days=days_from_now))
        .sign(key, hashes.SHA256())
    )
    return cert.public_bytes(serialization.Encoding.PEM)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_validate_cert_valid_future(tmp_path):
    pem = _make_pem("*.atlassian.net", 365)
    cert_file = tmp_path / "jira_ca_bundle.pem"
    cert_file.write_bytes(pem)

    result = validate_cert(cert_file)

    assert result["valid"] is True
    assert result["days_remaining"] > 0
    assert result["subject"] == "CN=*.atlassian.net"
    assert result["expires_at"] is not None
    assert "error" not in result


def test_validate_cert_expired(tmp_path):
    pem = _make_pem("expired.example.com", -1)
    cert_file = tmp_path / "jira_ca_bundle.pem"
    cert_file.write_bytes(pem)

    result = validate_cert(cert_file)

    assert result["valid"] is False
    assert result["days_remaining"] < 0
    assert result["expires_at"] is not None
    assert "error" not in result


def test_validate_cert_expiring_soon(tmp_path):
    """Certificate expiring in 5 days is still valid=True (not yet expired).

    days_remaining <= 7 is a UI-only warning threshold; validate_cert itself
    has no 7-day cutoff — it only checks days_remaining >= 0.
    """
    pem = _make_pem("soon.example.com", 5)
    cert_file = tmp_path / "jira_ca_bundle.pem"
    cert_file.write_bytes(pem)

    result = validate_cert(cert_file)

    assert result["valid"] is True          # cert is not expired
    assert result["days_remaining"] <= 7    # UI will render badge-warning for this


def test_validate_cert_missing_file(tmp_path):
    missing = tmp_path / "nonexistent.pem"

    result = validate_cert(missing)

    assert result["valid"] is False
    assert result["error"] is not None
    assert result["expires_at"] is None
    assert result["days_remaining"] is None
    assert result["subject"] is None


def test_validate_cert_corrupt_file(tmp_path):
    cert_file = tmp_path / "bad.pem"
    cert_file.write_bytes(b"this is not a valid PEM certificate")

    result = validate_cert(cert_file)

    assert result["valid"] is False
    assert result["error"] is not None
    assert result["expires_at"] is None
