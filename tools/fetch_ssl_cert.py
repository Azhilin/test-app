#!/usr/bin/env python3
"""Fetch and save the TLS certificate from the configured Jira host.

Run once before first use — or whenever the Jira TLS certificate changes:

    python tools/fetch_ssl_cert.py

The certificate is saved to certs/jira_ca_bundle.pem and is picked up
automatically by the Jira API client (via JIRA_SSL_CERT in app/config.py).
"""
import os
import socket
import ssl
import sys
from pathlib import Path
from urllib.parse import urlparse

import certifi

ROOT = Path(__file__).resolve().parent.parent


def _get_windows_ca_certs() -> list[str]:
    """Return all CA certificates from the Windows trust store as PEM strings.

    Reads ROOT and CA stores via ssl.enum_certificates(), which includes
    corporate CA roots pushed by GPO. Returns [] on non-Windows or any error.
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
    """Return TLS certificate chain + Windows CA store as concatenated PEM.

    Uses the same strategy as app.server.cert_handlers._fetch_cert_chain.
    Raises ssl.SSLError or OSError on connection failure.
    """
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE  # nosec B501 — intentional: fetching cert for trust bootstrap

    pem_parts: list[str] = []
    with socket.create_connection((host, port), timeout=10) as raw:
        with ctx.wrap_socket(raw, server_hostname=host) as ssock:
            try:
                chain = ssock.get_unverified_chain()  # Python 3.13+
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
    pem_parts.extend(_get_windows_ca_certs())
    return "\n".join(pem_parts)


def fetch_and_save_cert(jira_url: str, root: Path | None = None) -> str:
    """Fetch the TLS certificate for *jira_url* and write it to ``<root>/certs/jira_ca_bundle.pem``.

    Returns the path to the written PEM file.
    Raises ``SystemExit`` on any error (missing URL, unparseable host, SSL/OS failure).
    """
    root = root or ROOT

    if not jira_url:
        print(
            "ERROR: JIRA_URL is not set.\n"
            "Add it to your .env file (e.g. JIRA_URL=https://your-domain.atlassian.net)\n"
            "then re-run this script.",
            file=sys.stderr,
        )
        sys.exit(1)

    parsed = urlparse(jira_url)
    host = parsed.hostname
    port = parsed.port or 443

    if not host:
        print(
            f"ERROR: Could not parse a hostname from JIRA_URL={jira_url!r}",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"Fetching TLS certificate chain from {host}:{port} ...")

    try:
        pem = _fetch_cert_chain(host, port)
    except ssl.SSLError as exc:
        print(f"ERROR: SSL error while contacting {host}:{port}: {exc}", file=sys.stderr)
        sys.exit(1)
    except OSError as exc:
        print(f"ERROR: Could not connect to {host}:{port}: {exc}", file=sys.stderr)
        sys.exit(1)

    certs_dir = root / "certs"
    certs_dir.mkdir(exist_ok=True)

    cert_file = certs_dir / "jira_ca_bundle.pem"
    ca_bundle = Path(certifi.where()).read_text(encoding="ascii")
    bundle = pem + "\n" + ca_bundle
    cert_file.write_bytes(bundle.encode("ascii"))

    print(f"Certificate saved -> {cert_file}")
    print("Done. The Jira client will use this certificate automatically.")
    return str(cert_file)


if __name__ == "__main__":
    # Load .env so the script works even when run independently
    try:
        from dotenv import load_dotenv
        load_dotenv(ROOT / ".env")
    except ImportError:
        pass  # python-dotenv not installed; rely on environment variables

    url = os.getenv("JIRA_URL", "").strip().rstrip("/")
    fetch_and_save_cert(url)
