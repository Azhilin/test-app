#!/usr/bin/env python3
"""Fetch and save the TLS certificate from the configured Jira host.

Run once before first use — or whenever the Jira TLS certificate changes:

    python tools/fetch_ssl_cert.py

The certificate is saved to certs/jira_ca_bundle.pem and is picked up
automatically by the Jira API client (via JIRA_SSL_CERT in app/config.py).
"""
import os
import ssl
import sys
from pathlib import Path
from urllib.parse import urlparse

import certifi

ROOT = Path(__file__).resolve().parent.parent


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

    print(f"Fetching TLS certificate from {host}:{port} ...")

    try:
        pem = ssl.get_server_certificate((host, port))
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
