"""Unit tests for app.server.cert_handlers module-level helpers."""

from __future__ import annotations

import ssl
import sys

import pytest

from app.server.cert_handlers import _get_windows_ca_certs

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# _get_windows_ca_certs
# ---------------------------------------------------------------------------


def test_get_windows_ca_certs_returns_empty_on_non_windows(monkeypatch: pytest.MonkeyPatch) -> None:
    """On non-Windows platforms, _get_windows_ca_certs must return an empty list."""
    monkeypatch.setattr(sys, "platform", "linux")
    result = _get_windows_ca_certs()
    assert result == []


def test_get_windows_ca_certs_returns_empty_on_enum_certificates_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """If ssl.enum_certificates raises, _get_windows_ca_certs returns [] (never raises)."""
    monkeypatch.setattr(sys, "platform", "win32")

    def _boom(*_args: object) -> None:
        raise OSError("access denied")

    monkeypatch.setattr(ssl, "enum_certificates", _boom, raising=False)
    result = _get_windows_ca_certs()
    assert result == []


@pytest.mark.skipif(sys.platform != "win32", reason="Windows cert store only available on Windows")
@pytest.mark.windows_only
def test_get_windows_ca_certs_returns_pem_list_on_windows() -> None:
    """On an actual Windows machine, the function returns a non-empty list of PEM strings."""
    result = _get_windows_ca_certs()
    assert isinstance(result, list)
    assert len(result) > 0
    for pem in result:
        assert pem.startswith("-----BEGIN CERTIFICATE-----"), f"Expected PEM cert; got: {pem[:80]!r}"


@pytest.mark.skipif(sys.platform != "win32", reason="Windows cert store only available on Windows")
@pytest.mark.windows_only
def test_get_windows_ca_certs_mocked_returns_pem_strings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """With a mocked ssl.enum_certificates, confirm DER→PEM conversion and x509_asn filter."""
    # Minimal valid DER bytes for a dummy cert (just needs to survive DER_cert_to_PEM_cert)
    # ssl.DER_cert_to_PEM_cert simply base64-encodes with headers — any bytes are valid input
    fake_der = b"\x30\x82\x01\x00"  # truncated — fine for a header-only round-trip
    fake_pem = ssl.DER_cert_to_PEM_cert(fake_der)

    def _mock_enum(store_name: str):  # type: ignore[override]
        if store_name == "ROOT":
            yield (fake_der, "x509_asn", True)
            yield (b"ignored", "pkcs_7_asn", True)  # wrong encoding — should be skipped
        # CA store yields nothing

    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setattr(ssl, "enum_certificates", _mock_enum, raising=False)

    result = _get_windows_ca_certs()
    assert result == [fake_pem]
