"""TLS certificate handler mixin — /api/cert-status, /api/fetch-cert."""

from __future__ import annotations

import os
import socket
import ssl
import sys
from urllib.parse import urlparse

import certifi

from ._base import _root


def _get_windows_ca_certs() -> list[str]:
    """Return all CA certificates from the Windows trust store as PEM strings.

    Reads from both the ROOT (trusted root CAs, including GPO-pushed corporate
    CAs) and CA (intermediate CAs) stores via ssl.enum_certificates().
    Returns an empty list on non-Windows platforms or on any error.
    """
    if sys.platform != "win32":
        return []
    pem_parts: list[str] = []
    try:
        for store_name in ("ROOT", "CA"):
            for cert_bytes, encoding_type, _trust in ssl.enum_certificates(store_name):  # type: ignore[attr-defined]
                if encoding_type == "x509_asn":
                    pem_parts.append(ssl.DER_cert_to_PEM_cert(cert_bytes))
    except Exception:  # noqa: BLE001
        pass
    return pem_parts


def _fetch_cert_chain(host: str, port: int) -> str:
    """Return the TLS certificate chain + Windows CA store as concatenated PEM.

    Connects without verification (CERT_NONE) so the chain can be captured
    even when the server's CA is not trusted by certifi — the common case for
    corporate SSL-inspection proxies. Uses get_unverified_chain() (Python 3.13+)
    to return all certs in the chain: leaf, intermediates, and the root CA.
    Falls back to the leaf cert only if the chain API is unavailable.

    On Windows, the Windows ROOT and CA cert stores are appended to the bundle
    via _get_windows_ca_certs(). This captures corporate CA roots pushed by GPO
    that are never transmitted during a TLS handshake (TLS spec: root CAs are
    not sent by the server).
    """
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE  # nosec B501 — intentional: fetching cert for trust bootstrap

    pem_parts: list[str] = []
    with socket.create_connection((host, port), timeout=10) as raw:
        with ctx.wrap_socket(raw, server_hostname=host) as ssock:
            try:
                chain = ssock.get_unverified_chain()
                for cert in chain:
                    pem_parts.append(cert.public_bytes(ssl.ENCODING_PEM).decode("ascii"))
            except (AttributeError, TypeError):
                pass
            if not pem_parts:
                der = ssock.getpeercert(binary_form=True)
                if der:
                    pem_parts.append(ssl.DER_cert_to_PEM_cert(der))

    if not pem_parts:
        pem_parts.append(ssl.get_server_certificate((host, port)))

    # Always include Windows CA certs (captures corporate root CAs from GPO)
    pem_parts.extend(_get_windows_ca_certs())

    return "\n".join(pem_parts)


class CertHandlerMixin:
    def _handle_cert_status(self) -> None:
        """Return whether certs/jira_ca_bundle.pem exists, plus validity metadata."""
        from app.utils.cert_utils import validate_cert

        cert_path = _root() / "certs" / "jira_ca_bundle.pem"
        if not cert_path.is_file():
            self._send_json(200, {"exists": False, "path": "certs/jira_ca_bundle.pem"})
            return
        info = validate_cert(cert_path)
        self._send_json(
            200,
            {
                "exists": True,
                "path": "certs/jira_ca_bundle.pem",
                "valid": info["valid"],
                "expires_at": info["expires_at"],
                "days_remaining": info["days_remaining"],
                "subject": info["subject"],
                **({"error": info["error"]} if "error" in info else {}),
            },
        )

    def _handle_fetch_cert(self) -> None:
        """Fetch the TLS certificate from the Jira host and save it locally."""
        body = self._read_json_body() or {}
        url = str(body.get("url") or os.getenv("JIRA_URL") or "").strip().rstrip("/")

        if not url:
            self._send_json(400, {"ok": False, "error": "url is required"})
            return

        parsed = urlparse(url)
        host = parsed.hostname
        port = parsed.port or 443

        if not host:
            self._send_json(400, {"ok": False, "error": f"Cannot parse hostname from URL: {url!r}"})
            return

        try:
            pem = _fetch_cert_chain(host, port)
        except ssl.SSLError as exc:
            self._send_json(200, {"ok": False, "error": f"SSL error from {host}:{port}: {exc}"})
            return
        except OSError as exc:
            self._send_json(200, {"ok": False, "error": f"Could not connect to {host}:{port}: {exc}"})
            return

        certs_dir = _root() / "certs"
        certs_dir.mkdir(exist_ok=True)
        cert_file = certs_dir / "jira_ca_bundle.pem"

        ca_bundle = open(certifi.where(), encoding="ascii").read()
        bundle = pem + "\n" + ca_bundle
        cert_file.write_bytes(bundle.encode("ascii"))

        self._send_json(200, {"ok": True, "path": "certs/jira_ca_bundle.pem", "host": host})
