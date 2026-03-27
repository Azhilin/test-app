"""Utility for parsing and validating a local PEM certificate file."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path


def validate_cert(cert_path: Path) -> dict:
    """Parse a PEM certificate file and return validity metadata.

    Returns a dict with keys:
        valid (bool), expires_at (str|None), days_remaining (int|None),
        subject (str|None), and optionally error (str) on failure.
    """
    try:
        from cryptography import x509
        from cryptography.x509.oid import NameOID

        pem_bytes = cert_path.read_bytes()
        cert = x509.load_pem_x509_certificate(pem_bytes)

        expires_utc = cert.not_valid_after_utc
        now_utc = datetime.now(UTC)
        days_remaining = (expires_utc - now_utc).days

        try:
            cn_attrs = cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)
            if cn_attrs:
                cn_value = cn_attrs[0].value
                subject = f"CN={cn_value.decode() if isinstance(cn_value, bytes) else cn_value}"
            else:
                subject = cert.subject.rfc4514_string()
        except Exception:  # noqa: BLE001
            subject = cert.subject.rfc4514_string()

        return {
            "valid": days_remaining >= 0,
            "expires_at": expires_utc.date().isoformat(),
            "days_remaining": days_remaining,
            "subject": subject,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "valid": False,
            "expires_at": None,
            "days_remaining": None,
            "subject": None,
            "error": str(exc),
        }
