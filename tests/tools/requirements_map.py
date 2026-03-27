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
        "id": "IR-04",
        "description": "docs/product/schemas/ folder included (may be empty)",
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

# ── All requirements combined ──────────────────────────────────────────────

ALL_REQUIREMENTS: dict[str, list[dict]] = {
    "technical_requirements": TECHNICAL_REQUIREMENTS,
    "installation_requirements": INSTALLATION_REQUIREMENTS,
    "app_non_functional_requirements": NON_FUNCTIONAL_REQUIREMENTS,
    "dau_survey_requirements": DAU_SURVEY_REQUIREMENTS,
}
