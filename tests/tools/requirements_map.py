"""
tests/tools/requirements_map.py
===============================
Structured mapping of requirements from technical_requirements.md and
installation_requirements.md to test functions.

Each entry has:
    id          — stable identifier (TR-xx or IR-xx)
    description — one-line requirement statement
    type        — "functional" | "operational" | "informational"
    section     — section heading in the source document
    tests       — list of test references (file::function or file-level)
    status      — "covered" | "partial" | "gap" | "not-testable"
                  (auto-derived from type + tests by the coverage script)

Maintenance
-----------
When a requirement is added/changed in the docs, update the corresponding
entry here.  When a new test covers a requirement, add its reference to
the ``tests`` list.  Then run ``python tests/tools/test_coverage.py`` to
regenerate the Requirements Coverage section in tests/coverage/test_coverage.md.
"""

from __future__ import annotations

# ── status helpers ──────────────────────────────────────────────────────────

FUNCTIONAL = "functional"
OPERATIONAL = "operational"
INFORMATIONAL = "informational"


def _derive_status(req: dict) -> str:
    """Derive display status from requirement type and test list."""
    if req["type"] in (OPERATIONAL, INFORMATIONAL):
        return "not-testable"
    if not req["tests"]:
        return "gap"
    if req.get("partial"):
        return "partial"
    return "covered"


# ── Technical Requirements ──────────────────────────────────────────────────

TECHNICAL_REQUIREMENTS: list[dict] = [
    # --- 1. Operating System ---
    {
        "id": "TR-01",
        "description": "Windows 10/11 supported as primary platform with batch launchers",
        "type": FUNCTIONAL,
        "section": "Operating System",
        "tests": [
            "e2e/test_e2e.py::test_server_health_check",
        ],
    },
    {
        "id": "TR-02",
        "description": "macOS supported with manual venv setup",
        "type": OPERATIONAL,
        "section": "Operating System",
        "tests": [],
    },
    {
        "id": "TR-03",
        "description": "Linux supported with manual venv setup",
        "type": OPERATIONAL,
        "section": "Operating System",
        "tests": [],
    },
    # --- 2. Runtime Prerequisites ---
    {
        "id": "TR-04",
        "description": "Python 3.12 or later required",
        "type": FUNCTIONAL,
        "section": "Runtime Prerequisites",
        "tests": [
            "unit/test_imports.py",
        ],
    },
    {
        "id": "TR-05",
        "description": "project_setup.bat auto-installs Python 3.12 per-user (no admin)",
        "type": OPERATIONAL,
        "section": "Runtime Prerequisites",
        "tests": [],
    },
    {
        "id": "TR-06",
        "description": "pip bundled with Python 3.12+ (no separate install)",
        "type": INFORMATIONAL,
        "section": "Runtime Prerequisites",
        "tests": [],
    },
    {
        "id": "TR-07",
        "description": "atlassian-python-api >= 3.41.0 installed for Jira client",
        "type": FUNCTIONAL,
        "section": "Runtime Prerequisites",
        "tests": [
            "unit/test_imports.py::test_import_app_jira_client",
            "unit/test_jira_client.py",
        ],
    },
    {
        "id": "TR-08",
        "description": "python-dotenv >= 1.0.0 loads .env config",
        "type": FUNCTIONAL,
        "section": "Runtime Prerequisites",
        "tests": [
            "unit/test_config.py",
        ],
    },
    {
        "id": "TR-09",
        "description": "jinja2 >= 3.1.0 for HTML report templating",
        "type": FUNCTIONAL,
        "section": "Runtime Prerequisites",
        "tests": [
            "unit/test_imports.py::test_import_app_report_html",
            "component/test_report_html.py",
        ],
    },
    {
        "id": "TR-10",
        "description": "requests >= 2.28.0 available (transitive dependency)",
        "type": FUNCTIONAL,
        "section": "Runtime Prerequisites",
        "tests": [
            "unit/test_imports.py",
        ],
    },
    {
        "id": "TR-11",
        "description": "pandas >= 2.0.0 installed (future metric computation)",
        "type": INFORMATIONAL,
        "section": "Runtime Prerequisites",
        "tests": [],
    },
    {
        "id": "TR-12",
        "description": "cryptography >= 42.0.0 for PEM certificate validation",
        "type": FUNCTIONAL,
        "section": "Runtime Prerequisites",
        "tests": [
            "unit/test_cert_validation.py",
        ],
    },
    {
        "id": "TR-13",
        "description": "Dev: pytest >= 8.0.0 as test runner",
        "type": FUNCTIONAL,
        "section": "Runtime Prerequisites",
        "tests": [
            "unit/test_imports.py",
        ],
    },
    {
        "id": "TR-14",
        "description": "Dev: pytest-mock >= 3.12.0 for mocker fixture",
        "type": FUNCTIONAL,
        "section": "Runtime Prerequisites",
        "tests": [
            "unit/test_jira_client.py",
        ],
    },
    {
        "id": "TR-15",
        "description": "Dev: pytest-playwright >= 0.6.2 for E2E browser tests",
        "type": FUNCTIONAL,
        "section": "Runtime Prerequisites",
        "tests": [
            "e2e/test_e2e_ui.py",
        ],
    },
    {
        "id": "TR-16",
        "description": "Dev: pytest-cov >= 5.0.0 for coverage reporting",
        "type": INFORMATIONAL,
        "section": "Runtime Prerequisites",
        "tests": [],
    },
    {
        "id": "TR-17",
        "description": "Dev: ruff >= 0.9.0 for linting and formatting",
        "type": INFORMATIONAL,
        "section": "Runtime Prerequisites",
        "tests": [],
    },
    {
        "id": "TR-18",
        "description": "Playwright Chromium installable via playwright install",
        "type": OPERATIONAL,
        "section": "Runtime Prerequisites",
        "tests": [],
    },
    # --- 3. Installation ---
    {
        "id": "TR-19",
        "description": "project_setup.bat detects Python on system PATH",
        "type": OPERATIONAL,
        "section": "Installation",
        "tests": [],
    },
    {
        "id": "TR-20",
        "description": "project_setup.bat creates .venv in project root",
        "type": OPERATIONAL,
        "section": "Installation",
        "tests": [],
    },
    {
        "id": "TR-21",
        "description": "project_setup.bat installs packages from requirements.txt",
        "type": OPERATIONAL,
        "section": "Installation",
        "tests": [],
    },
    {
        "id": "TR-22",
        "description": "start_app.bat starts server and opens http://localhost:8080",
        "type": OPERATIONAL,
        "section": "Installation",
        "tests": [],
    },
    {
        "id": "TR-23",
        "description": "python server.py starts on default port 8080",
        "type": FUNCTIONAL,
        "section": "Installation",
        "tests": [
            "component/test_server.py::test_get_root_returns_200",
            "e2e/test_e2e.py::test_server_health_check",
        ],
    },
    {
        "id": "TR-24",
        "description": "python server.py <PORT> overrides default port",
        "type": FUNCTIONAL,
        "section": "Installation",
        "tests": [
            "e2e/test_e2e.py::test_server_health_check",
        ],
    },
    {
        "id": "TR-25",
        "description": "python main.py generates reports to generated/reports/",
        "type": FUNCTIONAL,
        "section": "Installation",
        "tests": [
            "integration/test_integration.py::test_main_pipeline_success",
            "e2e/test_e2e.py::test_cli_clean_via_subprocess",
        ],
    },
    # --- 4. Browser Requirements ---
    {
        "id": "TR-26",
        "description": "Chrome/Chromium 90+ supported",
        "type": FUNCTIONAL,
        "section": "Browser Requirements",
        "tests": [
            "e2e/test_e2e_ui.py",
        ],
    },
    {
        "id": "TR-27",
        "description": "Microsoft Edge 90+ supported",
        "type": OPERATIONAL,
        "section": "Browser Requirements",
        "tests": [],
    },
    {
        "id": "TR-28",
        "description": "Mozilla Firefox 88+ supported",
        "type": OPERATIONAL,
        "section": "Browser Requirements",
        "tests": [],
    },
    {
        "id": "TR-29",
        "description": "Safari 14+ supported",
        "type": OPERATIONAL,
        "section": "Browser Requirements",
        "tests": [],
    },
    {
        "id": "TR-30",
        "description": "JavaScript must be enabled for UI",
        "type": OPERATIONAL,
        "section": "Browser Requirements",
        "tests": [],
    },
    {
        "id": "TR-31",
        "description": "localhost must not be blocked by browser extensions",
        "type": OPERATIONAL,
        "section": "Browser Requirements",
        "tests": [],
    },
    {
        "id": "TR-32",
        "description": "Configured port must be free on 127.0.0.1",
        "type": OPERATIONAL,
        "section": "Browser Requirements",
        "tests": [],
    },
    # --- 5. Network Requirements ---
    {
        "id": "TR-33",
        "description": "Outbound HTTPS to Jira Cloud (port 443) required",
        "type": OPERATIONAL,
        "section": "Network Requirements",
        "tests": [],
    },
    {
        "id": "TR-34",
        "description": "HTTP server binds to 127.0.0.1 (loopback) by default",
        "type": FUNCTIONAL,
        "section": "Network Requirements",
        "tests": [
            "unit/test_server_handlers.py::test_run_defaults_host_to_loopback",
        ],
    },
    {
        "id": "TR-35",
        "description": "OS-level proxy env vars may be honoured by HTTP client",
        "type": OPERATIONAL,
        "section": "Network Requirements",
        "tests": [],
    },
    # --- 6. Credentials & API Tokens ---
    {
        "id": "TR-36",
        "description": "Three credentials required: JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN",
        "type": FUNCTIONAL,
        "section": "Credentials & API Tokens",
        "tests": [
            "unit/test_config.py::test_validate_config_all_set",
            "unit/test_config.py::test_validate_config_missing_url",
            "unit/test_config.py::test_validate_config_missing_email",
            "unit/test_config.py::test_validate_config_missing_token",
            "unit/test_config.py::test_validate_config_all_missing",
        ],
    },
    {
        "id": "TR-37",
        "description": ".env listed in .gitignore (credentials never committed)",
        "type": INFORMATIONAL,
        "section": "Credentials & API Tokens",
        "tests": [],
    },
    {
        "id": "TR-38",
        "description": "API token masked as *** in all server API responses",
        "type": FUNCTIONAL,
        "section": "Credentials & API Tokens",
        "tests": [
            "test_server_config.py::TestGetConfig::test_token_always_masked_as_stars",
        ],
    },
    {
        "id": "TR-39",
        "description": "Credentials transmitted only to JIRA_URL, never to third parties",
        "type": FUNCTIONAL,
        "section": "Credentials & API Tokens",
        "tests": [
            "unit/test_jira_client.py::test_create_client_uses_config_values",
            "unit/test_jira_client.py::test_create_client_url_kwarg_matches_config_exactly",
            "unit/test_jira_client.py::test_create_client_no_credentials_in_url_kwarg",
            "unit/test_jira_client.py::test_create_client_credentials_in_auth_kwargs_only",
        ],
    },
    {
        "id": "TR-40",
        "description": "Credentials settable via browser UI or .env file editing",
        "type": FUNCTIONAL,
        "section": "Credentials & API Tokens",
        "tests": [
            "e2e/test_e2e_connection.py::test_save_posts_correct_payload",
            "test_server_config.py::TestWriteEnvFields",
        ],
    },
    {
        "id": "TR-41",
        "description": "JIRA_URL must have no trailing slash",
        "type": FUNCTIONAL,
        "section": "Credentials & API Tokens",
        "tests": [
            "unit/test_config.py::test_jira_url_trailing_slash_stripped",
            "unit/test_config.py::test_jira_url_multiple_trailing_slashes_stripped",
            "unit/test_config.py::test_jira_url_no_trailing_slash_unchanged",
            "unit/test_config.py::test_jira_url_empty_string_safe",
            "unit/test_config.py::test_validate_config_warns_trailing_slash",
        ],
    },
    {
        "id": "TR-42",
        "description": "JIRA_EMAIL account needs minimum read access to boards/projects",
        "type": OPERATIONAL,
        "section": "Credentials & API Tokens",
        "tests": [],
    },
    # --- 7. SSL / TLS Certificate Support ---
    {
        "id": "TR-43",
        "description": "config.py detects certs/jira_ca_bundle.pem and passes verify_ssl",
        "type": FUNCTIONAL,
        "section": "SSL / TLS Certificate Support",
        "tests": [
            "unit/test_config.py::test_jira_ssl_cert_returns_true_when_no_file",
            "unit/test_config.py::test_jira_ssl_cert_returns_path_when_file_exists",
        ],
    },
    {
        "id": "TR-44",
        "description": "Cert validity (expiry, days remaining, subject) visible in UI",
        "type": FUNCTIONAL,
        "section": "SSL / TLS Certificate Support",
        "tests": [
            "component/test_server.py::test_cert_status_with_valid_cert_returns_enriched_fields",
            "e2e/test_e2e_ui.py::test_cert_status_badge_valid_cert",
        ],
    },
    {
        "id": "TR-45",
        "description": "Warning shown for expired or invalid certificate",
        "type": FUNCTIONAL,
        "section": "SSL / TLS Certificate Support",
        "tests": [
            "unit/test_cert_validation.py::test_validate_cert_expired",
            "component/test_server.py::test_cert_status_no_cert_returns_exists_false",
        ],
    },
    {
        "id": "TR-46",
        "description": "Auto-fetch cert via UI (Jira Connection tab → Fetch Certificate)",
        "type": FUNCTIONAL,
        "section": "SSL / TLS Certificate Support",
        "tests": [
            "component/test_server.py::test_fetch_cert_missing_url_returns_400",
            "component/test_server.py::test_fetch_cert_invalid_url_returns_400",
            "component/test_server.py::test_fetch_cert_unreachable_host_returns_error",
        ],
    },
    {
        "id": "TR-47",
        "description": "Auto-fetch cert via CLI (python tools/fetch_ssl_cert.py)",
        "type": FUNCTIONAL,
        "section": "SSL / TLS Certificate Support",
        "tests": [
            "integration/test_fetch_ssl_cert.py::test_fetch_cert_happy_path",
            "integration/test_fetch_ssl_cert.py::test_fetch_cert_creates_certs_dir",
            "integration/test_fetch_ssl_cert.py::test_fetch_cert_overwrites_existing",
            "integration/test_fetch_ssl_cert.py::test_fetch_cert_parses_custom_port",
            "integration/test_fetch_ssl_cert.py::test_fetch_cert_exits_when_url_empty",
            "integration/test_fetch_ssl_cert.py::test_fetch_cert_exits_when_hostname_unparseable",
            "integration/test_fetch_ssl_cert.py::test_fetch_cert_exits_on_ssl_error",
            "integration/test_fetch_ssl_cert.py::test_fetch_cert_exits_on_os_error",
            "integration/test_fetch_ssl_cert.py::test_fetch_cert_subprocess_smoke",
        ],
    },
]

# ── Installation Requirements ───────────────────────────────────────────────

INSTALLATION_REQUIREMENTS: list[dict] = [
    # --- 1. Zip Contents (all informational) ---
    {
        "id": "IR-01",
        "description": "app/ source code included in release zip",
        "type": INFORMATIONAL,
        "section": "Zip Contents",
        "tests": [],
    },
    {
        "id": "IR-02",
        "description": "templates/ Jinja2 HTML report template included",
        "type": INFORMATIONAL,
        "section": "Zip Contents",
        "tests": [],
    },
    {
        "id": "IR-03",
        "description": "ui/ browser UI files included",
        "type": INFORMATIONAL,
        "section": "Zip Contents",
        "tests": [],
    },
    {
        "id": "IR-05",
        "description": "certs/ placeholder folder with README.txt included",
        "type": INFORMATIONAL,
        "section": "Zip Contents",
        "tests": [],
    },
    {
        "id": "IR-06",
        "description": "main.py CLI entry point included",
        "type": INFORMATIONAL,
        "section": "Zip Contents",
        "tests": [],
    },
    {
        "id": "IR-07",
        "description": "server.py browser UI server entry point included",
        "type": INFORMATIONAL,
        "section": "Zip Contents",
        "tests": [],
    },
    {
        "id": "IR-08",
        "description": "requirements.txt included",
        "type": INFORMATIONAL,
        "section": "Zip Contents",
        "tests": [],
    },
    {
        "id": "IR-09",
        "description": ".env.example configuration template included",
        "type": INFORMATIONAL,
        "section": "Zip Contents",
        "tests": [],
    },
    {
        "id": "IR-10",
        "description": "project_setup.bat one-time setup script included",
        "type": INFORMATIONAL,
        "section": "Zip Contents",
        "tests": [],
    },
    {
        "id": "IR-11",
        "description": "start_app.bat Windows launcher included",
        "type": INFORMATIONAL,
        "section": "Zip Contents",
        "tests": [],
    },
    {
        "id": "IR-12",
        "description": "README.md quickstart guide included",
        "type": INFORMATIONAL,
        "section": "Zip Contents",
        "tests": [],
    },
    {
        "id": "IR-13",
        "description": ".venv/ NOT included in release zip",
        "type": INFORMATIONAL,
        "section": "Zip Contents",
        "tests": [],
    },
    {
        "id": "IR-14",
        "description": "generated/ NOT included in release zip",
        "type": INFORMATIONAL,
        "section": "Zip Contents",
        "tests": [],
    },
    {
        "id": "IR-15",
        "description": "requirements-dev.txt NOT included in release zip",
        "type": INFORMATIONAL,
        "section": "Zip Contents",
        "tests": [],
    },
    {
        "id": "IR-16",
        "description": "Test files NOT included in release zip",
        "type": INFORMATIONAL,
        "section": "Zip Contents",
        "tests": [],
    },
    {
        "id": "IR-17",
        "description": ".env NOT distributed in release zip",
        "type": INFORMATIONAL,
        "section": "Zip Contents",
        "tests": [],
    },
    # --- 2. Installation — Windows ---
    {
        "id": "IR-18",
        "description": "Zip extractable without errors to any destination folder",
        "type": OPERATIONAL,
        "section": "Windows Installation",
        "tests": [],
    },
    {
        "id": "IR-19",
        "description": "Paths with spaces or non-ASCII should be avoided (batch scripts)",
        "type": OPERATIONAL,
        "section": "Windows Installation",
        "tests": [],
    },
    {
        "id": "IR-20",
        "description": "project_setup.bat detects Python 3.10-3.12 on PATH",
        "type": OPERATIONAL,
        "section": "Windows Installation",
        "tests": [],
    },
    {
        "id": "IR-21",
        "description": "project_setup.bat downloads Python 3.12.10 if no compatible version",
        "type": OPERATIONAL,
        "section": "Windows Installation",
        "tests": [],
    },
    {
        "id": "IR-22",
        "description": "Python install via project_setup.bat is per-user (no admin)",
        "type": OPERATIONAL,
        "section": "Windows Installation",
        "tests": [],
    },
    {
        "id": "IR-23",
        "description": "Python installer SHA-256 checksum verified",
        "type": OPERATIONAL,
        "section": "Windows Installation",
        "tests": [],
    },
    {
        "id": "IR-24",
        "description": "Python download enforces TLS 1.2",
        "type": OPERATIONAL,
        "section": "Windows Installation",
        "tests": [],
    },
    {
        "id": "IR-25",
        "description": "project_setup.bat creates .venv/ virtual environment",
        "type": OPERATIONAL,
        "section": "Windows Installation",
        "tests": [],
    },
    {
        "id": "IR-26",
        "description": "project_setup.bat installs packages from requirements.txt",
        "type": OPERATIONAL,
        "section": "Windows Installation",
        "tests": [],
    },
    {
        "id": "IR-27",
        "description": "project_setup.bat optionally installs requirements-dev.txt",
        "type": OPERATIONAL,
        "section": "Windows Installation",
        "tests": [],
    },
    {
        "id": "IR-28",
        "description": "project_setup.bat creates .env from .env.example if absent",
        "type": FUNCTIONAL,
        "section": "Windows Installation",
        "tests": [
            "test_server_config.py::TestWriteEnvFields::test_creates_env_from_example_when_env_missing",
        ],
    },
    {
        "id": "IR-29",
        "description": "project_setup.bat prompts to keep or backup+recreate .env on update",
        "type": OPERATIONAL,
        "section": "Windows Installation",
        "tests": [],
    },
    {
        "id": "IR-30",
        "description": "project_setup.bat writes setup log to generated/logs/",
        "type": OPERATIONAL,
        "section": "Windows Installation",
        "tests": [],
    },
    {
        "id": "IR-31",
        "description": "project_setup.bat closes after 10s or on keypress",
        "type": OPERATIONAL,
        "section": "Windows Installation",
        "tests": [],
    },
    {
        "id": "IR-32",
        "description": "Credentials required in .env before generating reports",
        "type": FUNCTIONAL,
        "section": "Windows Installation",
        "tests": [
            "integration/test_integration.py::test_main_pipeline_config_fail",
            "e2e/test_e2e.py::test_cli_no_credentials_via_subprocess",
        ],
    },
    {
        "id": "IR-33",
        "description": "start_app.bat launches server and opens http://localhost:8080",
        "type": OPERATIONAL,
        "section": "Windows Installation",
        "tests": [],
    },
    # --- 3. Installation — macOS / Linux ---
    {
        "id": "IR-34",
        "description": "venv created with python3.12 -m venv .venv",
        "type": OPERATIONAL,
        "section": "macOS / Linux Installation",
        "tests": [],
    },
    {
        "id": "IR-35",
        "description": "Dependencies installable via .venv/bin/pip install -r requirements.txt",
        "type": OPERATIONAL,
        "section": "macOS / Linux Installation",
        "tests": [],
    },
    {
        "id": "IR-36",
        "description": "Server startable with .venv/bin/python server.py",
        "type": FUNCTIONAL,
        "section": "macOS / Linux Installation",
        "tests": [
            "e2e/test_e2e.py::test_server_health_check",
        ],
    },
    {
        "id": "IR-37",
        "description": "Server startable on custom port (server.py 9000)",
        "type": FUNCTIONAL,
        "section": "macOS / Linux Installation",
        "tests": [
            "e2e/test_e2e.py::test_server_health_check",
        ],
    },
    # --- 4. Update / Reinstall ---
    {
        "id": "IR-38",
        "description": "Update process preserves existing .env credentials",
        "type": FUNCTIONAL,
        "section": "Update / Reinstall",
        "tests": [
            "test_server_config.py::TestWriteEnvFields::test_replaces_existing_key",
            "test_server_config.py::TestWriteEnvFields::test_example_file_is_not_modified",
            "test_server_config.py::TestWriteEnvFields::test_preserves_other_credential_keys_when_updating_url",
            "test_server_config.py::TestWriteEnvFields::test_partial_update_preserves_untouched_key",
            "test_server_config.py::TestWriteEnvFields::test_preserves_unrelated_optional_env_vars",
            "test_server_config.py::TestWriteEnvFields::test_preserves_comment_lines_and_blanks",
        ],
    },
]

# ── Non-Functional Requirements ────────────────────────────────────────────

NON_FUNCTIONAL_REQUIREMENTS: list[dict] = [
    # --- 1. Performance ---
    {
        "id": "NFR-P-001",
        "description": "Report generation completes within 60s for 10 sprints / 500 issues",
        "type": FUNCTIONAL,
        "section": "Performance",
        "tests": [
            "component/test_report_performance.py::test_report_generation_completes_within_time_limit",
        ],
    },
    {
        "id": "NFR-P-002",
        "description": "HTML and Markdown reports generated in parallel via ThreadPoolExecutor",
        "type": FUNCTIONAL,
        "section": "Performance",
        "tests": [
            "unit/test_cli.py::test_main_generates_reports_in_parallel",
        ],
    },
    {
        "id": "NFR-P-003",
        "description": "Jira connection test times out after no more than 12 seconds",
        "type": FUNCTIONAL,
        "section": "Performance",
        "tests": [
            "unit/test_jira_client.py::test_create_client_passes_timeout",
        ],
    },
    {
        "id": "NFR-P-004",
        "description": "SSE events forwarded to browser within 1 second of stdout write",
        "type": OPERATIONAL,
        "section": "Performance",
        "tests": [],
    },
    {
        "id": "NFR-P-005",
        "description": "Data fetch bounded: sprint count capped, issues paged, changelog limited",
        "type": FUNCTIONAL,
        "section": "Performance",
        "tests": [
            "unit/test_jira_client.py::test_get_sprints_capped_at_sprint_count",
        ],
    },
    # --- 2. Security ---
    {
        "id": "NFR-S-001",
        "description": "API token always returned as *** in GET /api/config responses",
        "type": FUNCTIONAL,
        "section": "Security",
        "tests": [
            "test_server_config.py::TestGetConfig::test_token_always_masked_as_stars",
        ],
    },
    {
        "id": "NFR-S-002",
        "description": "Path traversal on /generated/reports/ rejected with HTTP 404",
        "type": FUNCTIONAL,
        "section": "Security",
        "tests": [
            "unit/test_server_handlers.py::test_resolve_report_path_rejects_path_traversal",
        ],
    },
    {
        "id": "NFR-S-003",
        "description": "HTTP server binds exclusively to 127.0.0.1 by default",
        "type": FUNCTIONAL,
        "section": "Security",
        "tests": [
            "unit/test_server_handlers.py::test_run_defaults_host_to_loopback",
        ],
    },
    {
        "id": "NFR-S-004",
        "description": "Schema file requests restricted to safe filenames and .json extension",
        "type": FUNCTIONAL,
        "section": "Security",
        "tests": [
            "unit/test_server_handlers.py::test_get_schema_detail_rejects_path_traversal",
            "unit/test_server_handlers.py::test_delete_schema_rejects_invalid_filename",
        ],
    },
    {
        "id": "NFR-S-005",
        "description": ".env and .env.backup-* listed in .gitignore, never committed",
        "type": INFORMATIONAL,
        "section": "Security",
        "tests": [],
    },
    {
        "id": "NFR-S-006",
        "description": "Credentials not included in exception messages, CLI stderr, or SSE events",
        "type": FUNCTIONAL,
        "section": "Security",
        "tests": [
            "unit/test_jira_client.py::test_sanitise_error_replaces_url",
            "unit/test_jira_client.py::test_sanitise_error_replaces_email_and_token",
            "unit/test_jira_client.py::test_sanitise_error_handles_none_config_values",
        ],
    },
    # --- 3. Usability ---
    {
        "id": "NFR-U-001",
        "description": "Report generation progress displayed in real time without buffering",
        "type": OPERATIONAL,
        "section": "Usability",
        "tests": [],
    },
    {
        "id": "NFR-U-002",
        "description": "Jira credentials pre-fill on next browser session after Save",
        "type": FUNCTIONAL,
        "section": "Usability",
        "tests": [
            "e2e/test_e2e_connection.py::test_save_posts_correct_payload",
            "e2e/test_e2e_connection.py::test_saved_credentials_prefill_on_reload",
        ],
    },
    {
        "id": "NFR-U-003",
        "description": "Generated HTML report is fully self-contained (inline CSS and data)",
        "type": FUNCTIONAL,
        "section": "Usability",
        "tests": [
            "component/test_report_html.py",
        ],
    },
    {
        "id": "NFR-U-004",
        "description": "Past reports listed on Generate tab, sorted newest first with links",
        "type": FUNCTIONAL,
        "section": "Usability",
        "tests": [
            "component/test_server.py::test_get_reports_returns_empty_list_when_no_reports",
            "component/test_server.py::test_get_reports_returns_sorted_list",
        ],
    },
    {
        "id": "NFR-U-005",
        "description": "Connection failures and errors display human-readable messages in UI",
        "type": FUNCTIONAL,
        "section": "Usability",
        "tests": [
            "unit/test_server_handlers.py::test_handle_generate_emits_error_event_for_nonzero_exit",
            "unit/test_server_handlers.py::test_handle_generate_emits_error_when_main_file_missing",
        ],
    },
    # --- 4. Reliability & Error Handling ---
    {
        "id": "NFR-R-001",
        "description": "Missing required config detected before any Jira API call is made",
        "type": FUNCTIONAL,
        "section": "Reliability & Error Handling",
        "tests": [
            "unit/test_config.py::test_validate_config_all_set",
            "unit/test_config.py::test_validate_config_missing_url",
            "unit/test_config.py::test_validate_config_missing_email",
            "unit/test_config.py::test_validate_config_missing_token",
            "integration/test_integration.py::test_main_pipeline_config_fail",
        ],
    },
    {
        "id": "NFR-R-002",
        "description": "Jira connectivity failure reported as SSE error; server continues",
        "type": FUNCTIONAL,
        "section": "Reliability & Error Handling",
        "tests": [
            "component/test_server.py::test_test_connection_http_error",
            "unit/test_server_handlers.py::test_handle_generate_emits_error_event_for_nonzero_exit",
        ],
    },
    {
        "id": "NFR-R-003",
        "description": "Client disconnect mid-stream caught and suppressed; no unhandled exception",
        "type": FUNCTIONAL,
        "section": "Reliability & Error Handling",
        "tests": [
            "unit/test_server_handlers.py::test_client_disconnect_tuple_includes_all_error_types",
            "unit/test_server_handlers.py::test_serve_file_catches_client_disconnect",
            "component/test_server.py::test_handle_error_swallows_connection_aborted_error",
        ],
    },
    {
        "id": "NFR-R-004",
        "description": "Changelog fetch failure for one issue skipped; full report still generated",
        "type": FUNCTIONAL,
        "section": "Reliability & Error Handling",
        "tests": [
            "unit/test_jira_client.py::test_get_issues_with_changelog_skips_failures",
        ],
    },
    {
        "id": "NFR-R-005",
        "description": "SSE stream always sends final event: close before connection ends",
        "type": FUNCTIONAL,
        "section": "Reliability & Error Handling",
        "tests": [
            "component/test_server.py::test_generate_ends_with_close_event",
        ],
    },
    # --- 5. Data Privacy ---
    {
        "id": "NFR-D-001",
        "description": "All credentials stored on local machine only; not sent to third parties",
        "type": INFORMATIONAL,
        "section": "Data Privacy",
        "tests": [],
    },
    {
        "id": "NFR-D-002",
        "description": "DAU survey responses stored locally only; not sent externally",
        "type": INFORMATIONAL,
        "section": "Data Privacy",
        "tests": [],
    },
    {
        "id": "NFR-D-003",
        "description": "No usage telemetry, analytics, or crash reporting sent anywhere",
        "type": INFORMATIONAL,
        "section": "Data Privacy",
        "tests": [],
    },
    {
        "id": "NFR-D-004",
        "description": "Credential backup files (.env.backup-*) excluded from version control",
        "type": INFORMATIONAL,
        "section": "Data Privacy",
        "tests": [],
    },
    # --- 6. Compatibility ---
    {
        "id": "NFR-C-001",
        "description": "All unit and component tests pass on Python 3.10, 3.11, and 3.12",
        "type": OPERATIONAL,
        "section": "Compatibility",
        "tests": [],
    },
    {
        "id": "NFR-C-002",
        "description": "Windows installation requires no administrator rights",
        "type": OPERATIONAL,
        "section": "Compatibility",
        "tests": [],
    },
    {
        "id": "NFR-C-003",
        "description": "Browser UI functions correctly in Chrome/Edge/Firefox/Safari 90+/88+/14+",
        "type": OPERATIONAL,
        "section": "Compatibility",
        "tests": [],
    },
    {
        "id": "NFR-C-004",
        "description": "CLI and browser UI produce identical metric values from same data",
        "type": FUNCTIONAL,
        "section": "Compatibility",
        "tests": [
            "unit/test_metrics.py::test_build_metrics_dict_is_deterministic",
        ],
    },
    # --- 7. Accessibility ---
    {
        "id": "NFR-A-001",
        "description": "All interactive UI regions carry correct ARIA role attributes",
        "type": FUNCTIONAL,
        "section": "Accessibility",
        "tests": [
            "e2e/test_e2e_ui.py::test_keyboard_arrow_right_navigation",
        ],
    },
    {
        "id": "NFR-A-002",
        "description": "Dynamic content updates use aria-live='polite' for screen readers",
        "type": FUNCTIONAL,
        "section": "Accessibility",
        "tests": [
            "e2e/test_e2e_ui.py::test_dynamic_regions_have_aria_live",
        ],
    },
    {
        "id": "NFR-A-003",
        "description": "Required form fields carry aria-required='true'",
        "type": FUNCTIONAL,
        "section": "Accessibility",
        "tests": [
            "e2e/test_e2e_ui.py::test_required_fields_have_aria_required",
        ],
    },
    {
        "id": "NFR-A-004",
        "description": "Decorative UI elements carry aria-hidden='true'",
        "type": FUNCTIONAL,
        "section": "Accessibility",
        "tests": [
            "e2e/test_e2e_ui.py::test_decorative_icons_have_aria_hidden",
        ],
    },
]

# ── DAU Survey Requirements ─────────────────────────────────────────────────

DAU_SURVEY_REQUIREMENTS: list[dict] = [
    # --- 1. Survey UI ---
    {
        "id": "DAU-F-001",
        "description": "Username is a required text field",
        "type": FUNCTIONAL,
        "section": "Survey UI",
        "tests": [
            "e2e/test_dau_survey_ui.py::test_submit_button_initially_disabled",
            "e2e/test_dau_survey_ui.py::test_submit_enabled_only_when_all_fields_are_valid",
        ],
    },
    {
        "id": "DAU-F-002",
        "description": "Username accepts only alphanumeric characters, minimum 2 characters",
        "type": FUNCTIONAL,
        "section": "Survey UI",
        "tests": [
            "e2e/test_dau_survey_ui.py::test_username_rejects_underscore",
            "e2e/test_dau_survey_ui.py::test_username_rejects_space",
            "e2e/test_dau_survey_ui.py::test_username_too_short_shows_error",
            "e2e/test_dau_survey_ui.py::test_username_valid_input_applies_valid_class",
        ],
    },
    {
        "id": "DAU-F-003",
        "description": "Username is persisted across sessions via localStorage",
        "type": FUNCTIONAL,
        "section": "Survey UI",
        "tests": [
            "e2e/test_dau_survey_ui.py::test_username_saved_to_localstorage_after_submit",
            "e2e/test_dau_survey_ui.py::test_username_restored_from_localstorage_on_page_load",
        ],
    },
    {
        "id": "DAU-F-004",
        "description": "Role is a required dropdown with exactly 5 options",
        "type": FUNCTIONAL,
        "section": "Survey UI",
        "tests": [
            "e2e/test_dau_survey_ui.py::test_submit_enabled_only_when_all_fields_are_valid",
            "e2e/test_dau_survey_ui.py::test_confirmation_displays_submitted_data",
        ],
    },
    {
        "id": "DAU-F-005",
        "description": "Usage frequency is a required radio selection with exactly 4 options",
        "type": FUNCTIONAL,
        "section": "Survey UI",
        "tests": [
            "e2e/test_dau_survey_ui.py::test_radio_card_click_marks_it_selected",
            "e2e/test_dau_survey_ui.py::test_submit_enabled_only_when_all_fields_are_valid",
        ],
    },
    {
        "id": "DAU-F-006",
        "description": "Progress bar reflects number of completed fields out of 3",
        "type": FUNCTIONAL,
        "section": "Survey UI",
        "tests": [
            "e2e/test_dau_survey_ui.py::test_progress_starts_at_zero",
            "e2e/test_dau_survey_ui.py::test_progress_increments_with_each_field",
        ],
    },
    {
        "id": "DAU-F-007",
        "description": "Submit button is disabled until all 3 fields are valid",
        "type": FUNCTIONAL,
        "section": "Survey UI",
        "tests": [
            "e2e/test_dau_survey_ui.py::test_submit_button_initially_disabled",
            "e2e/test_dau_survey_ui.py::test_submit_enabled_only_when_all_fields_are_valid",
        ],
    },
    {
        "id": "DAU-F-008",
        "description": "Confirmation screen is shown after a successful save",
        "type": FUNCTIONAL,
        "section": "Survey UI",
        "tests": [
            "e2e/test_dau_survey_ui.py::test_submit_hides_form_and_shows_confirmation",
            "e2e/test_dau_survey_ui.py::test_confirmation_displays_submitted_data",
        ],
    },
    {
        "id": "DAU-F-009",
        "description": "Keyboard navigation works within the radio group",
        "type": FUNCTIONAL,
        "section": "Survey UI",
        "tests": [
            "e2e/test_dau_survey_ui.py::test_radio_card_keyboard_navigation",
        ],
    },
    # --- 2. Submission and Storage ---
    {
        "id": "DAU-F-010",
        "description": "Survey data is saved via the File System Access API when supported",
        "type": FUNCTIONAL,
        "section": "Submission and Storage",
        "tests": [
            "e2e/test_dau_survey_ui.py::test_submit_writes_valid_json_to_mocked_fs",
        ],
    },
    {
        "id": "DAU-F-011",
        "description": "Survey data falls back to a browser download when the FS API is unavailable",
        "type": FUNCTIONAL,
        "section": "Submission and Storage",
        "tests": [
            "e2e/test_dau_survey_ui.py::test_fs_api_unavailable_falls_back_to_download",
        ],
    },
    {
        "id": "DAU-F-012",
        "description": "If the FS API directory picker is cancelled, the form remains intact",
        "type": FUNCTIONAL,
        "section": "Submission and Storage",
        "tests": [
            "e2e/test_dau_survey_ui.py::test_fs_api_abort_keeps_form_intact",
        ],
    },
    {
        "id": "DAU-F-013",
        "description": "If the FS API call fails for a non-cancel reason, the app falls back to download",
        "type": FUNCTIONAL,
        "section": "Submission and Storage",
        "tests": [
            "e2e/test_dau_survey_ui.py::test_fs_api_non_abort_error_falls_back_to_download",
        ],
    },
    {
        "id": "DAU-F-014",
        "description": "Output filename encodes the respondent and submission time",
        "type": FUNCTIONAL,
        "section": "Submission and Storage",
        "tests": [
            "e2e/test_dau_survey_ui.py::test_filename_matches_dau_username_timestamp_pattern",
        ],
    },
    {
        "id": "DAU-F-015",
        "description": "Submission payload matches the defined schema",
        "type": FUNCTIONAL,
        "section": "Submission and Storage",
        "tests": [
            "e2e/test_dau_survey_ui.py::test_submit_writes_valid_json_to_mocked_fs",
            "e2e/test_dau_survey_ui.py::test_submit_timestamp_format",
            "e2e/test_dau_survey_ui.py::test_submit_week_field_format",
        ],
    },
    {
        "id": "DAU-F-016",
        "description": "Response files are saved to generated/ by default",
        "type": FUNCTIONAL,
        "section": "Submission and Storage",
        "tests": [],
    },
    # --- 3. Metrics Computation ---
    {
        "id": "DAU-F-017",
        "description": "compute_dau_metrics() reads all dau_*.json files from the given directory",
        "type": FUNCTIONAL,
        "section": "Metrics Computation",
        "tests": [
            "unit/test_dau_metrics.py::test_empty_dir_returns_zero_count",
            "unit/test_dau_metrics.py::test_missing_dir_returns_zero_count",
            "unit/test_dau_metrics.py::test_three_response_files_counted",
            "unit/test_dau_metrics.py::test_non_dau_files_are_ignored",
            "unit/test_dau_metrics.py::test_malformed_json_file_is_skipped",
        ],
    },
    {
        "id": "DAU-F-018",
        "description": "compute_dau_metrics maps each usage answer to its score and computes the team average",
        "type": FUNCTIONAL,
        "section": "Metrics Computation",
        "tests": [
            "unit/test_dau_metrics.py::test_mixed_scores_correct_avg",
            "unit/test_dau_metrics.py::test_all_not_used_avg_is_zero",
            "unit/test_dau_metrics.py::test_unknown_usage_falls_back_to_zero",
        ],
    },
    {
        "id": "DAU-F-019",
        "description": "compute_dau_metrics returns a by_role list with per-role averages and counts",
        "type": FUNCTIONAL,
        "section": "Metrics Computation",
        "tests": [
            "unit/test_dau_metrics.py::test_by_role_sorted_alphabetically",
            "unit/test_dau_metrics.py::test_by_role_correct_avg_and_count",
        ],
    },
    {
        "id": "DAU-F-020",
        "description": "compute_dau_metrics returns a breakdown list with per-answer counts",
        "type": FUNCTIONAL,
        "section": "Metrics Computation",
        "tests": [
            "unit/test_dau_metrics.py::test_breakdown_sorted_descending_by_count",
        ],
    },
    {
        "id": "DAU-F-021",
        "description": "build_metrics_dict() includes a dau key",
        "type": FUNCTIONAL,
        "section": "Metrics Computation",
        "tests": [
            "unit/test_dau_metrics.py::test_build_metrics_dict_includes_dau_key",
        ],
    },
    {
        "id": "DAU-F-022",
        "description": "The responses directory is configurable via DAU_RESPONSES_DIR environment variable",
        "type": FUNCTIONAL,
        "section": "Metrics Computation",
        "tests": [
            "unit/test_dau_metrics.py::test_dau_responses_dir_env_var_overrides_default",
        ],
    },
    # --- 4. Report Rendering ---
    {
        "id": "DAU-F-023",
        "description": "The HTML report includes a DAU section",
        "type": FUNCTIONAL,
        "section": "Report Rendering",
        "tests": [
            "component/test_dau_report.py::test_html_has_dau_section_when_data_present",
            "component/test_dau_report.py::test_html_dau_shows_team_avg",
        ],
    },
    {
        "id": "DAU-F-024",
        "description": "The HTML report DAU section is omitted when there are no responses",
        "type": FUNCTIONAL,
        "section": "Report Rendering",
        "tests": [
            "component/test_dau_report.py::test_html_dau_section_absent_when_no_responses",
            "component/test_dau_report.py::test_html_dau_section_hidden_when_visibility_false",
        ],
    },
    {
        "id": "DAU-F-025",
        "description": "The Markdown report includes a ## Daily Active Usage (DAU) section",
        "type": FUNCTIONAL,
        "section": "Report Rendering",
        "tests": [
            "component/test_dau_report.py::test_md_has_dau_heading_when_data_present",
            "component/test_dau_report.py::test_md_dau_shows_team_avg",
            "component/test_dau_report.py::test_md_dau_shows_role_in_table",
        ],
    },
    {
        "id": "DAU-F-026",
        "description": "The Markdown DAU section is omitted when there are no responses",
        "type": FUNCTIONAL,
        "section": "Report Rendering",
        "tests": [
            "component/test_dau_report.py::test_md_dau_section_absent_when_no_responses",
        ],
    },
    # --- 5. Non-Functional Requirements ---
    {
        "id": "DAU-NFR-001",
        "description": "All survey data is stored locally; no data is sent to any external service",
        "type": FUNCTIONAL,
        "section": "Non-Functional Requirements",
        "tests": [],
    },
    {
        "id": "DAU-NFR-002",
        "description": "Response files are excluded from version control",
        "type": OPERATIONAL,
        "section": "Non-Functional Requirements",
        "tests": [],
    },
    {
        "id": "DAU-NFR-003",
        "description": "No server process is required to submit the survey",
        "type": FUNCTIONAL,
        "section": "Non-Functional Requirements",
        "tests": [
            "e2e/test_dau_survey_ui.py::test_survey_page_loads_with_title",
        ],
    },
    {
        "id": "DAU-NFR-004",
        "description": "Survey page styling is consistent with the existing report aesthetic",
        "type": OPERATIONAL,
        "section": "Non-Functional Requirements",
        "tests": [],
    },
    {
        "id": "DAU-NFR-005",
        "description": "Form fields carry ARIA labels and the confirmation screen uses a live region",
        "type": FUNCTIONAL,
        "section": "Non-Functional Requirements",
        "tests": [],
    },
]

# ── Jira Connection Requirements ───────────────────────────────────────────

JIRA_CONNECTION_REQUIREMENTS: list[dict] = [
    # --- 1. Authentication ---
    {
        "id": "JCR-A-001",
        "description": "Valid Basic Auth credentials are accepted by Jira",
        "type": FUNCTIONAL,
        "section": "Authentication",
        "tests": [
            "component/test_server.py::test_test_connection_valid_creds",
        ],
    },
    {
        "id": "JCR-A-002",
        "description": "An invalid API token is rejected with a clear error",
        "type": FUNCTIONAL,
        "section": "Authentication",
        "tests": [
            "component/test_server.py::test_test_connection_http_error",
        ],
    },
    {
        "id": "JCR-A-003",
        "description": "An unrecognised Jira email is rejected with a clear error",
        "type": FUNCTIONAL,
        "section": "Authentication",
        "tests": [
            "component/test_server.py::test_test_connection_http_error",
        ],
    },
    {
        "id": "JCR-A-004",
        "description": "The API token is never echoed in any server response",
        "type": FUNCTIONAL,
        "section": "Authentication",
        "tests": [],
    },
    {
        "id": "JCR-A-005",
        "description": "Credentials are sanitised before logging or raising exceptions",
        "type": FUNCTIONAL,
        "section": "Authentication",
        "tests": [
            "unit/test_jira_client.py::test_sanitise_error_replaces_url",
            "unit/test_jira_client.py::test_sanitise_error_replaces_email_and_token",
            "unit/test_jira_client.py::test_sanitise_error_handles_none_config_values",
        ],
    },
    # --- 2. Configuration & Validation ---
    {
        "id": "JCR-C-001",
        "description": "Missing JIRA_URL is detected before any network call",
        "type": FUNCTIONAL,
        "section": "Configuration & Validation",
        "tests": [
            "unit/test_config.py::test_validate_config_missing_url",
            "integration/test_integration.py::test_main_pipeline_config_fail",
        ],
    },
    {
        "id": "JCR-C-002",
        "description": "Missing JIRA_EMAIL is detected before any network call",
        "type": FUNCTIONAL,
        "section": "Configuration & Validation",
        "tests": [
            "unit/test_config.py::test_validate_config_missing_email",
        ],
    },
    {
        "id": "JCR-C-003",
        "description": "Missing JIRA_API_TOKEN is detected before any network call",
        "type": FUNCTIONAL,
        "section": "Configuration & Validation",
        "tests": [
            "unit/test_config.py::test_validate_config_missing_token",
        ],
    },
    {
        "id": "JCR-C-004",
        "description": "JIRA_URL trailing slashes are stripped automatically",
        "type": FUNCTIONAL,
        "section": "Configuration & Validation",
        "tests": [
            "unit/test_config.py::test_jira_url_trailing_slash_stripped",
            "unit/test_config.py::test_jira_url_multiple_trailing_slashes_stripped",
        ],
    },
    {
        "id": "JCR-C-005",
        "description": "JIRA_BOARD_ID is optional; app auto-discovers the first board",
        "type": FUNCTIONAL,
        "section": "Configuration & Validation",
        "tests": [
            "unit/test_jira_client.py::test_get_board_id_from_api",
        ],
    },
    {
        "id": "JCR-C-006",
        "description": "JIRA_SPRINT_COUNT defaults to 10 when not set",
        "type": FUNCTIONAL,
        "section": "Configuration & Validation",
        "tests": [
            "unit/test_config.py::test_sprint_count_default",
        ],
    },
    {
        "id": "JCR-C-007",
        "description": "JIRA_FILTER_ID is optional; absent value causes no error",
        "type": FUNCTIONAL,
        "section": "Configuration & Validation",
        "tests": [
            "unit/test_config.py::test_filter_id_empty",
        ],
    },
    # --- 3. Test-Connection Endpoint ---
    {
        "id": "JCR-T-001",
        "description": "Valid credentials return user details",
        "type": FUNCTIONAL,
        "section": "Test-Connection Endpoint",
        "tests": [
            "component/test_server.py::test_test_connection_valid_creds",
            "integration/test_integration.py::test_server_test_connection_json_shape",
        ],
    },
    {
        "id": "JCR-T-002",
        "description": "Missing required fields return HTTP 400",
        "type": FUNCTIONAL,
        "section": "Test-Connection Endpoint",
        "tests": [
            "component/test_server.py::test_test_connection_missing_fields",
        ],
    },
    {
        "id": "JCR-T-003",
        "description": "Malformed JSON body returns HTTP 400",
        "type": FUNCTIONAL,
        "section": "Test-Connection Endpoint",
        "tests": [
            "component/test_server.py::test_test_connection_invalid_json",
        ],
    },
    {
        "id": "JCR-T-004",
        "description": "An empty request body returns HTTP 400",
        "type": FUNCTIONAL,
        "section": "Test-Connection Endpoint",
        "tests": [
            "component/test_server.py::test_test_connection_empty_body",
        ],
    },
    {
        "id": "JCR-T-005",
        "description": "An unreachable host returns ok: false with an error message",
        "type": FUNCTIONAL,
        "section": "Test-Connection Endpoint",
        "tests": [
            "component/test_server.py::test_test_connection_http_error",
        ],
    },
    {
        "id": "JCR-T-006",
        "description": "Jira HTTP 401 / 403 is surfaced to the caller",
        "type": FUNCTIONAL,
        "section": "Test-Connection Endpoint",
        "tests": [
            "component/test_server.py::test_test_connection_http_error",
        ],
    },
    {
        "id": "JCR-T-007",
        "description": "The test-connection request times out after at most 12 seconds",
        "type": FUNCTIONAL,
        "section": "Test-Connection Endpoint",
        "tests": [],
    },
    {
        "id": "JCR-T-008",
        "description": "An unexpected server-side exception returns HTTP 500",
        "type": FUNCTIONAL,
        "section": "Test-Connection Endpoint",
        "tests": [],
    },
    # --- 4. SSL / TLS Certificate Handling ---
    {
        "id": "JCR-SSL-001",
        "description": "A custom CA bundle is used when present",
        "type": FUNCTIONAL,
        "section": "SSL / TLS Certificate Handling",
        "tests": [
            "unit/test_config.py::test_jira_ssl_cert_returns_path_when_file_exists",
            "unit/test_jira_client.py::test_create_client_passes_verify_ssl",
        ],
    },
    {
        "id": "JCR-SSL-002",
        "description": "The system CA store is used when no custom cert is present",
        "type": FUNCTIONAL,
        "section": "SSL / TLS Certificate Handling",
        "tests": [
            "unit/test_config.py::test_jira_ssl_cert_returns_true_when_no_file",
        ],
    },
    {
        "id": "JCR-SSL-003",
        "description": "Certificate validity is reported by cert_utils.validate_cert()",
        "type": FUNCTIONAL,
        "section": "SSL / TLS Certificate Handling",
        "tests": [
            "component/test_server.py::test_cert_status_with_valid_cert_returns_enriched_fields",
        ],
    },
    {
        "id": "JCR-SSL-004",
        "description": "The test-connection request uses the same SSL context as the Jira client",
        "type": FUNCTIONAL,
        "section": "SSL / TLS Certificate Handling",
        "tests": [],
    },
    {
        "id": "JCR-SSL-005",
        "description": "An expired custom CA bundle is reported but does not block client creation",
        "type": FUNCTIONAL,
        "section": "SSL / TLS Certificate Handling",
        "tests": [],
        "partial": True,
    },
    {
        "id": "JCR-SSL-006",
        "description": "Fetch Certificate happy path delivers a parseable, valid cert badge",
        "type": FUNCTIONAL,
        "section": "SSL / TLS Certificate Handling",
        "tests": [
            "e2e/test_e2e_connection.py::test_fetch_cert_success_updates_badge",
            "e2e/test_e2e_connection.py::test_positive_e2e_fetch_cert_then_badge_shows_valid",
            "component/test_server.py::test_fetch_cert_saves_pem_without_crlf_line_endings",
        ],
    },
    {
        "id": "JCR-SSL-007",
        "description": "Standard Jira Cloud positive E2E: absent cert file is an acceptable state",
        "type": FUNCTIONAL,
        "section": "SSL / TLS Certificate Handling",
        "tests": [
            "e2e/test_e2e_connection.py::test_positive_e2e_no_cert_is_acceptable_state",
        ],
    },
    # --- 5. Client Timeouts ---
    {
        "id": "JCR-TO-001",
        "description": "The Jira API client uses a 55-second connection timeout",
        "type": FUNCTIONAL,
        "section": "Client Timeouts",
        "tests": [
            "unit/test_jira_client.py::test_create_client_returns_jira_instance",
        ],
    },
    {
        "id": "JCR-TO-002",
        "description": "The test-connection endpoint enforces a 12-second timeout",
        "type": FUNCTIONAL,
        "section": "Client Timeouts",
        "tests": [],
    },
    # --- 6. Future Enhancements ---
    {
        "id": "JCR-FUT-001",
        "description": "OAuth 2.0 3LO authentication support",
        "type": OPERATIONAL,
        "section": "Future Enhancements",
        "tests": [],
    },
    {
        "id": "JCR-FUT-002",
        "description": "Configurable test-connection timeout via JIRA_TEST_CONNECTION_TIMEOUT env var",
        "type": OPERATIONAL,
        "section": "Future Enhancements",
        "tests": [],
    },
    {
        "id": "JCR-FUT-003",
        "description": "Block report generation when certs/jira_ca_bundle.pem is expired",
        "type": OPERATIONAL,
        "section": "Future Enhancements",
        "tests": [],
    },
    {
        "id": "JCR-FUT-004",
        "description": "Automatic retry on HTTP 429 with exponential backoff",
        "type": OPERATIONAL,
        "section": "Future Enhancements",
        "tests": [],
    },
]

# ── Jira Data Fetching Requirements ────────────────────────────────────────

JIRA_DATA_FETCHING_REQUIREMENTS: list[dict] = [
    # --- 1. Board Discovery ---
    {
        "id": "JDF-B-001",
        "description": "JIRA_BOARD_ID from config is used without making an API call",
        "type": FUNCTIONAL,
        "section": "Board Discovery",
        "tests": [
            "unit/test_jira_client.py::test_get_board_id_from_config",
        ],
    },
    {
        "id": "JDF-B-002",
        "description": "The first accessible board is auto-discovered when no JIRA_BOARD_ID is configured",
        "type": FUNCTIONAL,
        "section": "Board Discovery",
        "tests": [
            "unit/test_jira_client.py::test_get_board_id_from_api",
        ],
    },
    {
        "id": "JDF-B-003",
        "description": "An empty boards list raises a ValueError with an actionable message",
        "type": FUNCTIONAL,
        "section": "Board Discovery",
        "tests": [
            "unit/test_jira_client.py::test_get_board_id_no_boards_raises",
        ],
    },
    # --- 2. Sprint Fetching ---
    {
        "id": "JDF-SP-001",
        "description": "Closed and active sprints are both returned",
        "type": FUNCTIONAL,
        "section": "Sprint Fetching",
        "tests": [
            "unit/test_jira_client.py::test_get_sprints_sorted_desc_by_start_date",
        ],
    },
    {
        "id": "JDF-SP-002",
        "description": "Sprints are sorted by startDate descending (newest first)",
        "type": FUNCTIONAL,
        "section": "Sprint Fetching",
        "tests": [
            "unit/test_jira_client.py::test_get_sprints_sorted_desc_by_start_date",
        ],
    },
    {
        "id": "JDF-SP-003",
        "description": "Sprint count is capped at JIRA_SPRINT_COUNT",
        "type": FUNCTIONAL,
        "section": "Sprint Fetching",
        "tests": [
            "unit/test_jira_client.py::test_get_sprints_capped_at_sprint_count",
        ],
    },
    {
        "id": "JDF-SP-004",
        "description": "An empty sprint list is tolerated without crashing",
        "type": FUNCTIONAL,
        "section": "Sprint Fetching",
        "tests": [
            "unit/test_jira_client.py::test_get_sprints_empty",
        ],
    },
    # --- 3. Issue Fetching ---
    {
        "id": "JDF-I-001",
        "description": "All issues are retrieved across multiple pages",
        "type": FUNCTIONAL,
        "section": "Issue Fetching",
        "tests": [
            "unit/test_jira_client.py::test_get_issues_for_sprint_pagination",
        ],
    },
    {
        "id": "JDF-I-002",
        "description": "A filter JQL constraint is applied when JIRA_FILTER_ID is set",
        "type": FUNCTIONAL,
        "section": "Issue Fetching",
        "tests": [
            "unit/test_jira_client.py::test_fetch_sprint_data_passes_filter_jql_to_each_sprint",
        ],
    },
    {
        "id": "JDF-I-003",
        "description": "All sprint issues are returned when no filter is set",
        "type": FUNCTIONAL,
        "section": "Issue Fetching",
        "tests": [
            "unit/test_jira_client.py::test_get_issues_for_sprint_single_page",
        ],
    },
    {
        "id": "JDF-I-004",
        "description": "An empty issue list for a sprint is tolerated",
        "type": FUNCTIONAL,
        "section": "Issue Fetching",
        "tests": [
            "unit/test_jira_client.py::test_get_issues_for_sprint_empty",
        ],
    },
    {
        "id": "JDF-I-005",
        "description": "A network failure during pagination terminates the loop safely",
        "type": FUNCTIONAL,
        "section": "Issue Fetching",
        "tests": [],
    },
    # --- 4. Changelog Fetching ---
    {
        "id": "JDF-CL-001",
        "description": "Changelog with status transition history is returned per issue",
        "type": FUNCTIONAL,
        "section": "Changelog Fetching",
        "tests": [
            "unit/test_jira_client.py::test_get_issue_with_changelog_expand_param",
        ],
    },
    {
        "id": "JDF-CL-002",
        "description": "Fetching changelogs for multiple issues returns a list in key order",
        "type": FUNCTIONAL,
        "section": "Changelog Fetching",
        "tests": [
            "unit/test_jira_client.py::test_get_issues_with_changelog_multiple_keys",
        ],
    },
    {
        "id": "JDF-CL-003",
        "description": "A per-issue changelog failure logs a warning and appends {}",
        "type": FUNCTIONAL,
        "section": "Changelog Fetching",
        "tests": [
            "unit/test_jira_client.py::test_get_issues_with_changelog_skips_failures",
        ],
    },
    {
        "id": "JDF-CL-004",
        "description": "Changelog timestamps must be timezone-aware ISO-8601 strings",
        "type": FUNCTIONAL,
        "section": "Changelog Fetching",
        "tests": [],
    },
    # --- 5. Filter JQL Resolution ---
    {
        "id": "JDF-F-001",
        "description": "A valid filter ID resolves to its JQL string",
        "type": FUNCTIONAL,
        "section": "Filter JQL Resolution",
        "tests": [
            "unit/test_jira_client.py::test_get_filter_jql_valid",
        ],
    },
    {
        "id": "JDF-F-002",
        "description": "A None filter ID returns an empty string without making an API call",
        "type": FUNCTIONAL,
        "section": "Filter JQL Resolution",
        "tests": [
            "unit/test_jira_client.py::test_get_filter_jql_none",
        ],
    },
    {
        "id": "JDF-F-003",
        "description": "An invalid or inaccessible filter ID returns an empty string without crashing",
        "type": FUNCTIONAL,
        "section": "Filter JQL Resolution",
        "tests": [
            "unit/test_jira_client.py::test_get_filter_jql_api_error",
        ],
        "partial": True,
    },
    # --- 6. Future Enhancements ---
    {
        "id": "JDF-FUT-001",
        "description": "Log a warning when filter JQL fetch fails silently",
        "type": OPERATIONAL,
        "section": "Future Enhancements",
        "tests": [],
    },
    {
        "id": "JDF-FUT-002",
        "description": "Automatic retry on HTTP 429 with exponential backoff",
        "type": OPERATIONAL,
        "section": "Future Enhancements",
        "tests": [],
    },
    {
        "id": "JDF-FUT-003",
        "description": "Configurable issue page size via JIRA_FILTER_PAGE_SIZE env var",
        "type": OPERATIONAL,
        "section": "Future Enhancements",
        "tests": [],
    },
]

# ── Jira Schema Requirements ────────────────────────────────────────────────

JIRA_SCHEMA_REQUIREMENTS: list[dict] = [
    # --- 1. Schema Loading ---
    {
        "id": "JSR-L-001",
        "description": "All schema entries are loaded from config/jira_schema.json",
        "type": FUNCTIONAL,
        "section": "Schema Loading",
        "tests": [
            "unit/test_schema.py::test_load_schemas_returns_list_from_file",
        ],
    },
    {
        "id": "JSR-L-002",
        "description": "A missing schema file returns an empty list",
        "type": FUNCTIONAL,
        "section": "Schema Loading",
        "tests": [
            "unit/test_schema.py::test_load_schemas_missing_file",
        ],
    },
    {
        "id": "JSR-L-003",
        "description": "Malformed JSON in the schema file returns an empty list",
        "type": FUNCTIONAL,
        "section": "Schema Loading",
        "tests": [
            "unit/test_schema.py::test_load_schemas_invalid_json",
        ],
    },
    {
        "id": "JSR-L-004",
        "description": "A schema can be retrieved by name",
        "type": FUNCTIONAL,
        "section": "Schema Loading",
        "tests": [
            "unit/test_schema.py::test_get_schema_found",
            "unit/test_schema.py::test_get_schema_not_found",
        ],
    },
    # --- 2. Active Schema Resolution ---
    {
        "id": "JSR-R-001",
        "description": "A named schema is returned when an explicit name is given",
        "type": FUNCTIONAL,
        "section": "Active Schema Resolution",
        "tests": [
            "unit/test_schema.py::test_get_active_schema_by_name",
        ],
    },
    {
        "id": "JSR-R-002",
        "description": "Default_Jira_Cloud is used as a fallback when no name is given",
        "type": FUNCTIONAL,
        "section": "Active Schema Resolution",
        "tests": [
            "unit/test_schema.py::test_get_active_schema_falls_back_to_default",
        ],
    },
    {
        "id": "JSR-R-003",
        "description": "The hardcoded _DEFAULT_SCHEMA is returned when the file is absent",
        "type": FUNCTIONAL,
        "section": "Active Schema Resolution",
        "tests": [
            "unit/test_schema.py::test_get_active_schema_no_file_returns_hardcoded_default",
            "unit/test_schema.py::test_get_active_schema_hardcoded_uses_builtin_story_points",
        ],
    },
    {
        "id": "JSR-R-004",
        "description": "A non-existent named schema falls back to the default silently",
        "type": FUNCTIONAL,
        "section": "Active Schema Resolution",
        "tests": [],
        "partial": True,
    },
    # --- 3. Schema Save & Delete ---
    {
        "id": "JSR-SD-001",
        "description": "A new schema is appended to the file",
        "type": FUNCTIONAL,
        "section": "Schema Save & Delete",
        "tests": [
            "unit/test_schema.py::test_save_schema_appends_new",
        ],
    },
    {
        "id": "JSR-SD-002",
        "description": "An existing schema is updated in-place",
        "type": FUNCTIONAL,
        "section": "Schema Save & Delete",
        "tests": [
            "unit/test_schema.py::test_save_schema_updates_existing",
        ],
    },
    {
        "id": "JSR-SD-003",
        "description": "The parent directory is created if absent",
        "type": FUNCTIONAL,
        "section": "Schema Save & Delete",
        "tests": [
            "unit/test_schema.py::test_save_schema_creates_file",
        ],
    },
    {
        "id": "JSR-SD-004",
        "description": "Default_Jira_Cloud cannot be deleted",
        "type": FUNCTIONAL,
        "section": "Schema Save & Delete",
        "tests": [
            "unit/test_schema.py::test_delete_schema_refuses_default",
        ],
    },
    {
        "id": "JSR-SD-005",
        "description": "Deleting a non-existent schema name returns False",
        "type": FUNCTIONAL,
        "section": "Schema Save & Delete",
        "tests": [
            "unit/test_schema.py::test_delete_schema_not_found",
        ],
    },
    # --- 4. Field ID & JQL Name Lookups ---
    {
        "id": "JSR-F-001",
        "description": "get_field_id() returns the Jira field ID for a known field key",
        "type": FUNCTIONAL,
        "section": "Field ID & JQL Name Lookups",
        "tests": [
            "unit/test_schema.py::test_get_field_id",
        ],
    },
    {
        "id": "JSR-F-002",
        "description": "get_field_id() returns None for an unknown field key",
        "type": FUNCTIONAL,
        "section": "Field ID & JQL Name Lookups",
        "tests": [
            "unit/test_schema.py::test_get_field_id",
        ],
    },
    {
        "id": "JSR-F-003",
        "description": "get_field_jql_name() falls back to id when jql_name is absent",
        "type": FUNCTIONAL,
        "section": "Field ID & JQL Name Lookups",
        "tests": [
            "unit/test_schema.py::test_get_field_jql_name_falls_back_to_id",
            "unit/test_schema.py::test_get_field_jql_name_with_explicit_jql_name",
        ],
    },
    # --- 5. Status Mappings ---
    {
        "id": "JSR-SM-001",
        "description": "get_done_statuses() returns the configured done status list",
        "type": FUNCTIONAL,
        "section": "Status Mappings",
        "tests": [
            "unit/test_schema.py::test_get_done_statuses",
        ],
    },
    {
        "id": "JSR-SM-002",
        "description": "get_in_progress_statuses() returns the configured in-progress list",
        "type": FUNCTIONAL,
        "section": "Status Mappings",
        "tests": [
            "unit/test_schema.py::test_get_in_progress_statuses",
        ],
    },
    {
        "id": "JSR-SM-003",
        "description": "Default done statuses are returned when status_mapping is absent",
        "type": FUNCTIONAL,
        "section": "Status Mappings",
        "tests": [
            "unit/test_schema.py::test_get_done_statuses_defaults",
        ],
    },
    {
        "id": "JSR-SM-004",
        "description": "Default in-progress statuses are returned when status_mapping is absent",
        "type": FUNCTIONAL,
        "section": "Status Mappings",
        "tests": [
            "unit/test_schema.py::test_get_in_progress_statuses_defaults",
        ],
    },
    # --- 6. Auto-Detection from Jira Fields ---
    {
        "id": "JSR-AD-001",
        "description": "Sprint field is detected by schema.custom identifier",
        "type": FUNCTIONAL,
        "section": "Auto-Detection from Jira Fields",
        "tests": [
            "unit/test_schema.py::test_build_schema_from_fields_detects_sprint",
        ],
    },
    {
        "id": "JSR-AD-002",
        "description": "Story-points field is detected by name pattern when schema.custom is absent",
        "type": FUNCTIONAL,
        "section": "Auto-Detection from Jira Fields",
        "tests": [
            "unit/test_schema.py::test_build_schema_from_fields_detects_story_points_by_name",
        ],
    },
    {
        "id": "JSR-AD-003",
        "description": "Undetected fields retain their _DEFAULT_SCHEMA values",
        "type": FUNCTIONAL,
        "section": "Auto-Detection from Jira Fields",
        "tests": [
            "unit/test_schema.py::test_build_schema_from_fields_preserves_defaults_for_missing",
        ],
    },
    {
        "id": "JSR-AD-004",
        "description": "The team field's jql_name is preserved through auto-detection",
        "type": FUNCTIONAL,
        "section": "Auto-Detection from Jira Fields",
        "tests": [
            "unit/test_schema.py::test_build_schema_from_fields_preserves_team_jql_name",
        ],
    },
    {
        "id": "JSR-AD-005",
        "description": "Null or structurally incomplete entries in the Jira fields response are tolerated",
        "type": FUNCTIONAL,
        "section": "Auto-Detection from Jira Fields",
        "tests": [],
        "partial": True,
    },
    # --- 7. Future Enhancements ---
    {
        "id": "JSR-FUT-001",
        "description": "Validate schema entries on load and surface missing required keys as warnings",
        "type": OPERATIONAL,
        "section": "Future Enhancements",
        "tests": [],
    },
    {
        "id": "JSR-FUT-002",
        "description": "Block duplicate schema_name values on save",
        "type": OPERATIONAL,
        "section": "Future Enhancements",
        "tests": [],
    },
    {
        "id": "JSR-FUT-003",
        "description": "Add a get_schema_names() convenience function",
        "type": OPERATIONAL,
        "section": "Future Enhancements",
        "tests": [],
    },
    {
        "id": "JSR-FUT-004",
        "description": "Emit a warning when a non-existent named schema falls back to the default",
        "type": OPERATIONAL,
        "section": "Future Enhancements",
        "tests": [],
    },
]

JIRA_FILTER_MANAGEMENT_REQUIREMENTS: list[dict] = [
    # --- 1. Default Filter Template ---
    {
        "id": "JFM-D-001",
        "description": "Default_Jira_Filter entry ships in config/jira_filters.json",
        "type": FUNCTIONAL,
        "section": "Default Filter Template",
        "tests": [
            "tests/unit/test_filter_handlers.py::test_default_filter_entry_is_present_and_correct",
            "tests/component/test_server_filters.py::test_get_filters_default_is_first",
        ],
    },
    {
        "id": "JFM-D-002",
        "description": "Default filter pre-sets sensible parameter defaults",
        "type": FUNCTIONAL,
        "section": "Default Filter Template",
        "tests": [
            "tests/unit/test_filter_handlers.py::test_default_filter_entry_is_present_and_correct",
        ],
    },
    {
        "id": "JFM-D-003",
        "description": "Default filter is always returned by GET /api/filters",
        "type": FUNCTIONAL,
        "section": "Default Filter Template",
        "tests": [
            "tests/unit/test_filter_handlers.py::test_load_filters_injects_default_when_absent_from_file",
            "tests/component/test_server_filters.py::test_get_filters_always_includes_default_after_user_delete",
        ],
    },
    {
        "id": "JFM-D-004",
        "description": "Default filter cannot be deleted",
        "type": FUNCTIONAL,
        "section": "Default Filter Template",
        "tests": [
            "tests/unit/test_filter_handlers.py::test_delete_default_filter_is_blocked",
            "tests/component/test_server_filters.py::test_delete_default_filter_returns_error",
        ],
    },
    # --- 2. Filter Persistence — Server API ---
    {
        "id": "JFM-P-001",
        "description": "GET /api/filters returns all saved filters ordered default-first",
        "type": FUNCTIONAL,
        "section": "Filter Persistence — Server API",
        "tests": [
            "tests/component/test_server_filters.py::test_get_filters_default_is_first",
        ],
    },
    {
        "id": "JFM-P-002",
        "description": "GET /api/filters initialises config file from default template if missing",
        "type": FUNCTIONAL,
        "section": "Filter Persistence — Server API",
        "tests": [
            "tests/unit/test_filter_handlers.py::test_load_filters_creates_file_when_missing",
        ],
    },
    {
        "id": "JFM-P-003",
        "description": "POST /api/filters creates a new filter entry when name is new",
        "type": FUNCTIONAL,
        "section": "Filter Persistence — Server API",
        "tests": [
            "tests/unit/test_filter_handlers.py::test_post_filter_creates_new_entry",
            "tests/component/test_server_filters.py::test_post_filter_creates_new_and_get_returns_it",
        ],
    },
    {
        "id": "JFM-P-004",
        "description": "POST /api/filters updates existing entry when name matches (upsert)",
        "type": FUNCTIONAL,
        "section": "Filter Persistence — Server API",
        "tests": [
            "tests/unit/test_filter_handlers.py::test_post_filter_updates_existing_entry",
            "tests/component/test_server_filters.py::test_post_filter_upserts_on_duplicate_name",
        ],
    },
    {
        "id": "JFM-P-005",
        "description": "POST /api/filters rejects missing JIRA_PROJECT",
        "type": FUNCTIONAL,
        "section": "Filter Persistence — Server API",
        "tests": [
            "tests/unit/test_filter_handlers.py::test_post_filter_rejects_blank_project",
        ],
    },
    {
        "id": "JFM-P-006",
        "description": "POST /api/filters builds correct JQL from params",
        "type": FUNCTIONAL,
        "section": "Filter Persistence — Server API",
        "tests": [
            "tests/unit/test_filter_handlers.py::test_build_jql_from_params[params0-project = PROJ-None]",
            "tests/unit/test_filter_handlers.py::test_build_jql_from_params[params1-project IN (A, B)-None]",
            'tests/unit/test_filter_handlers.py::test_build_jql_from_params[params2-"Team[Team]" = T1-None]',
            "tests/unit/test_filter_handlers.py::test_build_jql_from_params[params3-status IN (Done, Closed)-None]",
            "tests/unit/test_filter_handlers.py"
            "::test_build_jql_from_params[params4-project = PROJ-sprint in closedSprints()]",
            "tests/unit/test_filter_handlers.py::test_build_jql_from_params[params5-type IN (Story, Bug)-None]",
        ],
    },
    {
        "id": "JFM-P-007",
        "description": "POST /api/filters uses schema team JQL field name when schema_name provided",
        "type": FUNCTIONAL,
        "section": "Filter Persistence — Server API",
        "tests": [
            "tests/unit/test_filter_handlers.py::test_post_filter_uses_schema_team_jql_field",
        ],
    },
    {
        "id": "JFM-P-008",
        "description": "DELETE /api/filters/<slug> removes the matching entry",
        "type": FUNCTIONAL,
        "section": "Filter Persistence — Server API",
        "tests": [
            "tests/component/test_server_filters.py::test_delete_filter_removes_entry",
        ],
    },
    {
        "id": "JFM-P-009",
        "description": "DELETE /api/filters/<slug> returns 404-style error for unknown slug",
        "type": FUNCTIONAL,
        "section": "Filter Persistence — Server API",
        "tests": [
            "tests/unit/test_filter_handlers.py::test_delete_unknown_slug_returns_not_found",
            "tests/component/test_server_filters.py::test_delete_unknown_slug_returns_not_found",
        ],
    },
    {
        "id": "JFM-P-010",
        "description": "Filter data persists across application restarts",
        "type": FUNCTIONAL,
        "section": "Filter Persistence — Server API",
        "tests": [
            "tests/unit/test_filter_handlers.py::test_filter_data_persists_across_loads",
            "tests/component/test_server_filters.py::test_filter_persists_across_server_restart",
        ],
    },
    # --- 3. UI — Filter Name Pre-population ---
    {
        "id": "JFM-UI-001",
        "description": "Filter Name field is pre-populated on page load when empty",
        "type": FUNCTIONAL,
        "section": "UI — Filter Name Pre-population",
        "tests": [
            "tests/e2e/test_e2e_filters.py::test_filter_name_prepopulated_on_empty_load",
        ],
    },
    {
        "id": "JFM-UI-002",
        "description": "Pre-population does not overwrite a previously entered or saved value",
        "type": FUNCTIONAL,
        "section": "UI — Filter Name Pre-population",
        "tests": [
            "tests/e2e/test_e2e_filters.py::test_filter_name_not_overwritten_after_user_edit",
        ],
    },
    # --- 4. UI — Filter List Behaviour ---
    {
        "id": "JFM-UI-003",
        "description": "Saved filters loaded and displayed on page load",
        "type": FUNCTIONAL,
        "section": "UI — Filter List Behaviour",
        "tests": [
            "tests/e2e/test_e2e_filters.py::test_filter_list_displayed_on_load",
        ],
    },
    {
        "id": "JFM-UI-004",
        "description": "Default filter does not show a Remove button",
        "type": FUNCTIONAL,
        "section": "UI — Filter List Behaviour",
        "tests": [
            "tests/e2e/test_e2e_filters.py::test_default_filter_has_no_remove_button",
        ],
    },
    {
        "id": "JFM-UI-005",
        "description": "Non-default user filters show a Remove button",
        "type": FUNCTIONAL,
        "section": "UI — Filter List Behaviour",
        "tests": [
            "tests/e2e/test_e2e_filters.py::test_user_filter_has_remove_button",
        ],
    },
    {
        "id": "JFM-UI-006",
        "description": "Removing a filter via the Remove button updates the list immediately",
        "type": FUNCTIONAL,
        "section": "UI — Filter List Behaviour",
        "tests": [
            "tests/e2e/test_e2e_filters.py::test_remove_filter_updates_list",
        ],
    },
    # --- 5. Future Enhancements ---
    {
        "id": "JFM-FUT-001",
        "description": "Apply selected filter params to .env before running main.py",
        "type": FUNCTIONAL,
        "section": "Future Enhancements",
        "tests": [
            "tests/unit/test_filter_handlers.py::test_generate_applies_filter_params_to_subprocess_env",
        ],
    },
    {
        "id": "JFM-FUT-002",
        "description": "Allow reordering of saved filters in the UI",
        "type": OPERATIONAL,
        "section": "Future Enhancements",
        "tests": [],
    },
    {
        "id": "JFM-FUT-003",
        "description": "Export / import filter config as a downloadable JSON file",
        "type": OPERATIONAL,
        "section": "Future Enhancements",
        "tests": [],
    },
]

# ── Logging requirements ───────────────────────────────────────────────────

LOGGING_REQUIREMENTS: list[dict] = [
    # --- 1. Log File ---
    {
        "id": "LOG-01",
        "description": "Each application run writes a unique timestamped log file",
        "type": FUNCTIONAL,
        "section": "Log File",
        "tests": [
            "unit/test_logging_setup.py::test_setup_logging_creates_log_file",
            "unit/test_logging_setup.py::test_setup_logging_log_filename_matches_pattern",
        ],
    },
    {
        "id": "LOG-02",
        "description": "The log directory is created automatically if it does not exist",
        "type": FUNCTIONAL,
        "section": "Log File",
        "tests": [
            "unit/test_logging_setup.py::test_setup_logging_creates_log_directory",
        ],
    },
    # --- 2. Log Format ---
    {
        "id": "LOG-03",
        "description": "All log lines follow a consistent structured format",
        "type": FUNCTIONAL,
        "section": "Log Format",
        "tests": [
            "unit/test_logging_setup.py::test_log_file_format",
        ],
    },
    {
        "id": "LOG-04",
        "description": "File and console output use the same formatter",
        "type": FUNCTIONAL,
        "section": "Log Format",
        "tests": [
            "unit/test_logging_setup.py::test_log_file_format",
        ],
    },
    # --- 3. Output Channels ---
    {
        "id": "LOG-05",
        "description": "All log output reaches both a log file and stdout",
        "type": FUNCTIONAL,
        "section": "Output Channels",
        "tests": [
            "unit/test_logging_setup.py::test_setup_logging_attaches_file_handler",
            "unit/test_logging_setup.py::test_setup_logging_attaches_stream_handler",
        ],
    },
    {
        "id": "LOG-06",
        "description": "Log files are written in UTF-8 encoding",
        "type": FUNCTIONAL,
        "section": "Output Channels",
        "tests": [
            "unit/test_logging_setup.py::test_log_file_format",
        ],
    },
    # --- 4. Log Levels ---
    {
        "id": "LOG-07",
        "description": "The root logger captures all severity levels by default",
        "type": FUNCTIONAL,
        "section": "Log Levels",
        "tests": [
            "unit/test_logging_setup.py::test_setup_logging_sets_debug_level",
        ],
    },
    {
        "id": "LOG-08",
        "description": "A custom SUCCESS level is defined with numeric value 25",
        "type": FUNCTIONAL,
        "section": "Log Levels",
        "tests": [
            "unit/test_logging_setup.py::test_success_level_value",
        ],
    },
    {
        "id": "LOG-09",
        "description": "The SUCCESS level name is registered with the logging system",
        "type": FUNCTIONAL,
        "section": "Log Levels",
        "tests": [
            "unit/test_logging_setup.py::test_success_level_name_registered",
        ],
    },
    {
        "id": "LOG-10",
        "description": "Logger instances expose a .success() convenience method",
        "type": FUNCTIONAL,
        "section": "Log Levels",
        "tests": [
            "unit/test_logging_setup.py::test_logger_has_success_method",
        ],
    },
    # --- 5. Entry-Point Integration ---
    {
        "id": "LOG-11",
        "description": "setup_logging() is invoked from the CLI entry point",
        "type": FUNCTIONAL,
        "section": "Entry-Point Integration",
        "tests": [
            "unit/test_logging_setup.py::test_setup_logging_returns_logger_and_path",
        ],
    },
    {
        "id": "LOG-12",
        "description": "setup_logging() is invoked from the server entry point",
        "type": FUNCTIONAL,
        "section": "Entry-Point Integration",
        "tests": [
            "unit/test_logging_setup.py::test_setup_logging_returns_logger_and_path",
        ],
    },
    # --- 6. Code Quality ---
    {
        "id": "LOG-13",
        "description": "Entry-point modules use the logging system instead of print()",
        "type": FUNCTIONAL,
        "section": "Code Quality",
        "tests": [
            "unit/test_imports.py::test_import_app_logging_setup",
        ],
    },
    {
        "id": "LOG-14",
        "description": "Log call sites use lazy %-style argument formatting",
        "type": FUNCTIONAL,
        "section": "Code Quality",
        "tests": [
            "unit/test_logging_setup.py::test_log_file_format",
        ],
    },
    # --- 7. Security ---
    {
        "id": "LOG-15",
        "description": "Sensitive credentials are not written to log files",
        "type": FUNCTIONAL,
        "section": "Security",
        "tests": [
            "unit/test_logging_setup.py::test_credentials_not_in_log_output",
        ],
    },
    # --- 8. Performance ---
    {
        "id": "LOG-16",
        "description": "Logging overhead does not measurably slow report generation",
        "type": OPERATIONAL,
        "section": "Performance",
        "tests": [],
    },
    # --- 9. Log Retention ---
    {
        "id": "LOG-17",
        "description": "Log files from previous runs are preserved across runs",
        "type": FUNCTIONAL,
        "section": "Log Retention",
        "tests": [
            "unit/test_logging_setup.py::test_setup_logging_creates_log_file",
        ],
    },
    {
        "id": "LOG-18",
        "description": "Log files are excluded from version control",
        "type": OPERATIONAL,
        "section": "Log Retention",
        "tests": [],
    },
]

# ── Report Generation Requirements ─────────────────────────────────────────

REPORT_GENERATION_REQUIREMENTS: list[dict] = [
    # ── 1. Filter Selection ──
    {
        "id": "RG-FS-001",
        "description": "Generate tab shows a filter dropdown populated from saved filters",
        "type": FUNCTIONAL,
        "section": "Filter Selection",
        "tests": [
            "unit/test_filter_handlers.py::test_default_filter_entry_is_present_and_correct",
            "component/test_server_filters.py::test_get_filters_default_is_first",
            "e2e/test_e2e_filters.py::test_filter_list_displayed_on_load",
        ],
    },
    {
        "id": "RG-FS-002",
        "description": "Project Default Filter is the pre-selected option when a default filter exists",
        "type": FUNCTIONAL,
        "section": "Filter Selection",
        "tests": [
            "component/test_server_filters.py::test_get_filters_default_is_first",
            "e2e/test_e2e_filters.py::test_filter_name_prepopulated_on_empty_load",
        ],
    },
    {
        "id": "RG-FS-003",
        "description": "Selected filter slug is passed to the /api/generate SSE endpoint",
        "type": FUNCTIONAL,
        "section": "Filter Selection",
        "tests": [
            "unit/test_filter_handlers.py::test_generate_applies_filter_params_to_subprocess_env",
            "e2e/test_e2e_ui.py::test_generate_with_filter_sse_streaming",
        ],
    },
    # ── 2. Project Type ──
    {
        "id": "RG-PT-001",
        "description": "Generate tab shows SCRUM / KANBAN radio buttons",
        "type": FUNCTIONAL,
        "section": "Project Type",
        "tests": [
            "e2e/test_e2e_ui.py::test_project_type_radios_visible",
        ],
    },
    {
        "id": "RG-PT-002",
        "description": "SCRUM is the default project type",
        "type": FUNCTIONAL,
        "section": "Project Type",
        "tests": [
            "unit/test_config.py::test_project_type_default_scrum",
        ],
    },
    {
        "id": "RG-PT-003",
        "description": "Selected project type is sent to the generate endpoint",
        "type": FUNCTIONAL,
        "section": "Project Type",
        "tests": [
            "unit/test_filter_handlers.py::test_generate_applies_filter_params_to_subprocess_env",
        ],
    },
    {
        "id": "RG-PT-004",
        "description": "Project type selection persists across page reloads via localStorage",
        "type": FUNCTIONAL,
        "section": "Project Type",
        "tests": [
            "e2e/test_e2e_ui.py::test_project_type_persists_in_localstorage",
        ],
    },
    {
        "id": "RG-PT-005",
        "description": "Project type is included in the report header",
        "type": FUNCTIONAL,
        "section": "Project Type",
        "tests": [
            "component/test_report_html.py::test_project_type_shown_in_header",
            "component/test_report_md.py::test_project_type_shown_in_md_header",
        ],
    },
    # ── 3. Estimation Type ──
    {
        "id": "RG-ET-001",
        "description": "Generate tab shows StoryPoints / JiraTickets radio buttons",
        "type": FUNCTIONAL,
        "section": "Estimation Type",
        "tests": [
            "e2e/test_e2e_ui.py::test_estimation_type_radios_visible",
        ],
    },
    {
        "id": "RG-ET-002",
        "description": "StoryPoints is the default estimation type",
        "type": FUNCTIONAL,
        "section": "Estimation Type",
        "tests": [
            "unit/test_config.py::test_estimation_type_default_story_points",
        ],
    },
    {
        "id": "RG-ET-003",
        "description": "Selected estimation type is sent to the generate endpoint",
        "type": FUNCTIONAL,
        "section": "Estimation Type",
        "tests": [
            "unit/test_filter_handlers.py::test_generate_applies_filter_params_to_subprocess_env",
        ],
    },
    {
        "id": "RG-ET-004",
        "description": "Estimation type selection persists across page reloads via localStorage",
        "type": FUNCTIONAL,
        "section": "Estimation Type",
        "tests": [
            "e2e/test_e2e_ui.py::test_estimation_type_persists_in_localstorage",
        ],
    },
    {
        "id": "RG-ET-005",
        "description": "Estimation type is included in the report header",
        "type": FUNCTIONAL,
        "section": "Estimation Type",
        "tests": [
            "component/test_report_html.py::test_estimation_type_shown_in_header",
            "component/test_report_md.py::test_estimation_type_shown_in_md_header",
        ],
    },
    {
        "id": "RG-ET-006",
        "description": "When JiraTickets is selected, velocity uses issue count instead of story points",
        "type": FUNCTIONAL,
        "section": "Estimation Type",
        "tests": [
            "unit/test_metrics.py::test_build_metrics_dict_jira_tickets_velocity_uses_issue_count",
            "unit/test_metrics.py::test_build_metrics_dict_story_points_velocity_unchanged",
        ],
    },
    {
        "id": "RG-ET-007",
        "description": "Report labels reflect estimation type",
        "type": FUNCTIONAL,
        "section": "Estimation Type",
        "tests": [
            "component/test_report_html.py::test_velocity_header_reflects_estimation_type_tickets",
            "component/test_report_md.py::test_velocity_header_label_story_points",
            "component/test_report_md.py::test_velocity_header_label_jira_tickets",
        ],
    },
    # ── 4. Metric Toggles ──
    {
        "id": "RG-MT-001",
        "description": "Generate tab shows 6 metric toggle checkboxes",
        "type": FUNCTIONAL,
        "section": "Metric Toggles",
        "tests": [
            "e2e/test_e2e_ui.py::test_metric_toggle_checkboxes_visible",
        ],
    },
    {
        "id": "RG-MT-002",
        "description": "All metric toggles default to enabled",
        "type": FUNCTIONAL,
        "section": "Metric Toggles",
        "tests": [
            "unit/test_config.py::test_metric_toggles_default_true",
        ],
    },
    {
        "id": "RG-MT-003",
        "description": "Disabled metrics are excluded from the generated report",
        "type": FUNCTIONAL,
        "section": "Metric Toggles",
        "tests": [
            "component/test_report_html.py::test_velocity_section_hidden_when_section_visibility_false",
            "component/test_report_html.py::test_ai_assistance_section_hidden_when_section_visibility_false",
            "component/test_report_html.py::test_ai_usage_section_hidden_when_section_visibility_false",
            "component/test_dau_report.py::test_html_dau_section_hidden_when_visibility_false",
        ],
    },
    {
        "id": "RG-MT-004",
        "description": "Metric toggle state is sent to the generate endpoint",
        "type": FUNCTIONAL,
        "section": "Metric Toggles",
        "tests": [
            "unit/test_filter_handlers.py::test_generate_applies_filter_params_to_subprocess_env",
        ],
    },
    {
        "id": "RG-MT-005",
        "description": "Metric toggle state persists across page reloads via localStorage",
        "type": FUNCTIONAL,
        "section": "Metric Toggles",
        "tests": [
            "e2e/test_e2e_ui.py::test_metric_toggles_persist_in_localstorage",
        ],
    },
    {
        "id": "RG-MT-006",
        "description": "At least one metric must be enabled to generate a report",
        "type": FUNCTIONAL,
        "section": "Metric Toggles",
        "tests": [
            "e2e/test_e2e_ui.py::test_generate_button_disabled_when_all_metrics_unchecked",
        ],
    },
    # ── 5. Report Output ──
    {
        "id": "RG-RO-001",
        "description": "HTML report is generated and linked in the UI report list",
        "type": FUNCTIONAL,
        "section": "Report Output",
        "tests": [
            "component/test_report_html.py::test_file_created",
            "component/test_server.py::test_generate_returns_sse_content_type",
            "component/test_server.py::test_generate_ends_with_close_event",
        ],
    },
    {
        "id": "RG-RO-002",
        "description": "MD report is generated alongside the HTML report",
        "type": FUNCTIONAL,
        "section": "Report Output",
        "tests": [
            "component/test_report_md.py::test_file_created",
        ],
    },
    {
        "id": "RG-RO-003",
        "description": "Only HTML reports are linked in the UI",
        "type": FUNCTIONAL,
        "section": "Report Output",
        "tests": [
            "e2e/test_e2e_ui.py::test_reports_list_links_only_html",
        ],
    },
    {
        "id": "RG-RO-004",
        "description": "Section visibility in HTML matches metric toggle state",
        "type": FUNCTIONAL,
        "section": "Report Output",
        "tests": [
            "component/test_report_html.py::test_velocity_section_hidden_when_section_visibility_false",
            "component/test_report_html.py::test_ai_assistance_section_hidden_when_section_visibility_false",
            "component/test_report_html.py::test_ai_usage_section_hidden_when_section_visibility_false",
            "component/test_dau_report.py::test_html_dau_section_hidden_when_visibility_false",
        ],
    },
    {
        "id": "RG-RO-005",
        "description": "Section visibility in MD matches metric toggle state",
        "type": FUNCTIONAL,
        "section": "Report Output",
        "tests": [
            "component/test_report_md.py::test_velocity_section_hidden_when_section_visibility_false",
            "component/test_report_md.py::test_dau_section_hidden_when_section_visibility_false",
        ],
    },
    # ── 6. Configuration ──
    {
        "id": "RG-CF-001",
        "description": "PROJECT_TYPE env var controls default project type",
        "type": FUNCTIONAL,
        "section": "Configuration",
        "tests": [
            "unit/test_config.py::test_project_type_default_scrum",
            "unit/test_config.py::test_project_type_kanban",
            "unit/test_config.py::test_project_type_invalid_falls_back",
        ],
    },
    {
        "id": "RG-CF-002",
        "description": "ESTIMATION_TYPE env var controls default estimation type",
        "type": FUNCTIONAL,
        "section": "Configuration",
        "tests": [
            "unit/test_config.py::test_estimation_type_default_story_points",
            "unit/test_config.py::test_estimation_type_jira_tickets",
            "unit/test_config.py::test_estimation_type_invalid_falls_back",
        ],
    },
    {
        "id": "RG-CF-003",
        "description": "Individual METRIC_* env vars control metric inclusion",
        "type": FUNCTIONAL,
        "section": "Configuration",
        "tests": [
            "unit/test_config.py::test_metric_toggles_default_true",
            "unit/test_config.py::test_metric_toggles_explicit_false",
        ],
    },
    {
        "id": "RG-CF-004",
        "description": "All new env vars have sensible defaults",
        "type": FUNCTIONAL,
        "section": "Configuration",
        "tests": [
            "unit/test_config.py::test_project_type_default_scrum",
            "unit/test_config.py::test_estimation_type_default_story_points",
            "unit/test_config.py::test_metric_toggles_default_true",
        ],
    },
    # ── 7. Non-Functional Requirements ──
    {
        "id": "RG-NFR-001",
        "description": "UI state persistence uses localStorage only",
        "type": OPERATIONAL,
        "section": "Non-Functional Requirements",
        "tests": [],
    },
    {
        "id": "RG-NFR-002",
        "description": "New parameters do not break existing filter overlay mechanism",
        "type": OPERATIONAL,
        "section": "Non-Functional Requirements",
        "tests": [
            "integration/test_integration.py::test_filter_metadata_in_html",
        ],
    },
    {
        "id": "RG-NFR-003",
        "description": "Report generation time is not significantly impacted by new controls",
        "type": OPERATIONAL,
        "section": "Non-Functional Requirements",
        "tests": [
            "component/test_report_performance.py::test_report_generation_completes_within_time_limit",
        ],
    },
]

# ── All requirements combined ──────────────────────────────────────────────

ALL_REQUIREMENTS: dict[str, list[dict]] = {
    "technical_requirements": TECHNICAL_REQUIREMENTS,
    "installation_requirements": INSTALLATION_REQUIREMENTS,
    "app_non_functional_requirements": NON_FUNCTIONAL_REQUIREMENTS,
    "dau_survey_requirements": DAU_SURVEY_REQUIREMENTS,
    "jira_connection_requirements": JIRA_CONNECTION_REQUIREMENTS,
    "jira_data_fetching_requirements": JIRA_DATA_FETCHING_REQUIREMENTS,
    "jira_schema_requirements": JIRA_SCHEMA_REQUIREMENTS,
    "jira_filter_management_requirements": JIRA_FILTER_MANAGEMENT_REQUIREMENTS,
    "logging_requirements": LOGGING_REQUIREMENTS,
    "report_generation_requirements": REPORT_GENERATION_REQUIREMENTS,
}
