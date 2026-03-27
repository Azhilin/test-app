# Technical Requirements — Coverage Detail

> Source document: [docs/product/requirements/technical_requirements.md](../../../docs/product/requirements/technical_requirements.md)  
> Back to summary: [tests/coverage/test_coverage.md](../test_coverage.md)

**Total:** 47 | **✅ Covered:** 25 | **🔶 Partial:** 0 | **❌ Gap:** 0 | **⬜ N/T:** 22 | **Functional:** 100%


#### Operating System

| ID | Requirement | Status | Tests |
|----|-------------|--------|-------|
| TR-01 | Windows 10/11 supported as primary platform with batch launchers | ✅ | `e2e/test_e2e.py::test_server_health_check` |
| TR-02 | macOS supported with manual venv setup | ⬜ | — |
| TR-03 | Linux supported with manual venv setup | ⬜ | — |

#### Runtime Prerequisites

| ID | Requirement | Status | Tests |
|----|-------------|--------|-------|
| TR-04 | Python 3.12 or later required | ✅ | `unit/test_imports.py` |
| TR-05 | project_setup.bat auto-installs Python 3.12 per-user (no admin) | ⬜ | — |
| TR-06 | pip bundled with Python 3.12+ (no separate install) | ⬜ | — |
| TR-07 | atlassian-python-api >= 3.41.0 installed for Jira client | ✅ | `unit/test_imports.py::test_import_app_jira_client`, `unit/test_jira_client.py` |
| TR-08 | python-dotenv >= 1.0.0 loads .env config | ✅ | `unit/test_config.py` |
| TR-09 | jinja2 >= 3.1.0 for HTML report templating | ✅ | `unit/test_imports.py::test_import_app_report_html`, `component/test_report_html.py` |
| TR-10 | requests >= 2.28.0 available (transitive dependency) | ✅ | `unit/test_imports.py` |
| TR-11 | pandas >= 2.0.0 installed (future metric computation) | ⬜ | — |
| TR-12 | cryptography >= 42.0.0 for PEM certificate validation | ✅ | `unit/test_cert_validation.py` |
| TR-13 | Dev: pytest >= 8.0.0 as test runner | ✅ | `unit/test_imports.py` |
| TR-14 | Dev: pytest-mock >= 3.12.0 for mocker fixture | ✅ | `unit/test_jira_client.py` |
| TR-15 | Dev: pytest-playwright >= 0.6.2 for E2E browser tests | ✅ | `e2e/test_e2e_ui.py` |
| TR-16 | Dev: pytest-cov >= 5.0.0 for coverage reporting | ⬜ | — |
| TR-17 | Dev: ruff >= 0.9.0 for linting and formatting | ⬜ | — |
| TR-18 | Playwright Chromium installable via playwright install | ⬜ | — |

#### Installation

| ID | Requirement | Status | Tests |
|----|-------------|--------|-------|
| TR-19 | project_setup.bat detects Python on system PATH | ⬜ | — |
| TR-20 | project_setup.bat creates .venv in project root | ⬜ | — |
| TR-21 | project_setup.bat installs packages from requirements.txt | ⬜ | — |
| TR-22 | start_app.bat starts server and opens http://localhost:8080 | ⬜ | — |
| TR-23 | python server.py starts on default port 8080 | ✅ | `component/test_server.py::test_get_root_returns_200`, `e2e/test_e2e.py::test_server_health_check` |
| TR-24 | python server.py <PORT> overrides default port | ✅ | `e2e/test_e2e.py::test_server_health_check` |
| TR-25 | python main.py generates reports to generated/reports/ | ✅ | `integration/test_integration.py::test_main_pipeline_success`, `e2e/test_e2e.py::test_cli_clean_via_subprocess` |

#### Browser Requirements

| ID | Requirement | Status | Tests |
|----|-------------|--------|-------|
| TR-26 | Chrome/Chromium 90+ supported | ✅ | `e2e/test_e2e_ui.py` |
| TR-27 | Microsoft Edge 90+ supported | ⬜ | — |
| TR-28 | Mozilla Firefox 88+ supported | ⬜ | — |
| TR-29 | Safari 14+ supported | ⬜ | — |
| TR-30 | JavaScript must be enabled for UI | ⬜ | — |
| TR-31 | localhost must not be blocked by browser extensions | ⬜ | — |
| TR-32 | Configured port must be free on 127.0.0.1 | ⬜ | — |

#### Network Requirements

| ID | Requirement | Status | Tests |
|----|-------------|--------|-------|
| TR-33 | Outbound HTTPS to Jira Cloud (port 443) required | ⬜ | — |
| TR-34 | HTTP server binds to 127.0.0.1 (loopback) by default | ✅ | `unit/test_server_handlers.py::test_run_defaults_host_to_loopback` |
| TR-35 | OS-level proxy env vars may be honoured by HTTP client | ⬜ | — |

#### Credentials & API Tokens

| ID | Requirement | Status | Tests |
|----|-------------|--------|-------|
| TR-36 | Three credentials required: JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN | ✅ | `unit/test_config.py::test_validate_config_all_set`, `unit/test_config.py::test_validate_config_missing_url`, `unit/test_config.py::test_validate_config_missing_email`, `unit/test_config.py::test_validate_config_missing_token`, `unit/test_config.py::test_validate_config_all_missing` |
| TR-37 | .env listed in .gitignore (credentials never committed) | ⬜ | — |
| TR-38 | API token masked as *** in all server API responses | ✅ | `test_server_config.py::TestGetConfig::test_token_always_masked_as_stars` |
| TR-39 | Credentials transmitted only to JIRA_URL, never to third parties | ✅ | `unit/test_jira_client.py::test_create_client_uses_config_values`, `unit/test_jira_client.py::test_create_client_url_kwarg_matches_config_exactly`, `unit/test_jira_client.py::test_create_client_no_credentials_in_url_kwarg`, `unit/test_jira_client.py::test_create_client_credentials_in_auth_kwargs_only` |
| TR-40 | Credentials settable via browser UI or .env file editing | ✅ | `e2e/test_e2e_connection.py::test_save_posts_correct_payload`, `test_server_config.py::TestWriteEnvFields` |
| TR-41 | JIRA_URL must have no trailing slash | ✅ | `unit/test_config.py::test_jira_url_trailing_slash_stripped`, `unit/test_config.py::test_jira_url_multiple_trailing_slashes_stripped`, `unit/test_config.py::test_jira_url_no_trailing_slash_unchanged`, `unit/test_config.py::test_jira_url_empty_string_safe`, `unit/test_config.py::test_validate_config_warns_trailing_slash` |
| TR-42 | JIRA_EMAIL account needs minimum read access to boards/projects | ⬜ | — |

#### SSL / TLS Certificate Support

| ID | Requirement | Status | Tests |
|----|-------------|--------|-------|
| TR-43 | config.py detects certs/jira_ca_bundle.pem and passes verify_ssl | ✅ | `unit/test_config.py::test_jira_ssl_cert_returns_true_when_no_file`, `unit/test_config.py::test_jira_ssl_cert_returns_path_when_file_exists` |
| TR-44 | Cert validity (expiry, days remaining, subject) visible in UI | ✅ | `component/test_server.py::test_cert_status_with_valid_cert_returns_enriched_fields`, `e2e/test_e2e_ui.py::test_cert_status_badge_valid_cert` |
| TR-45 | Warning shown for expired or invalid certificate | ✅ | `unit/test_cert_validation.py::test_validate_cert_expired`, `component/test_server.py::test_cert_status_no_cert_returns_exists_false` |
| TR-46 | Auto-fetch cert via UI (Jira Connection tab → Fetch Certificate) | ✅ | `component/test_server.py::test_fetch_cert_missing_url_returns_400`, `component/test_server.py::test_fetch_cert_invalid_url_returns_400`, `component/test_server.py::test_fetch_cert_unreachable_host_returns_error` |
| TR-47 | Auto-fetch cert via CLI (python tools/fetch_ssl_cert.py) | ✅ | `integration/test_fetch_ssl_cert.py::test_fetch_cert_happy_path`, `integration/test_fetch_ssl_cert.py::test_fetch_cert_creates_certs_dir`, `integration/test_fetch_ssl_cert.py::test_fetch_cert_overwrites_existing`, `integration/test_fetch_ssl_cert.py::test_fetch_cert_parses_custom_port`, `integration/test_fetch_ssl_cert.py::test_fetch_cert_exits_when_url_empty`, `integration/test_fetch_ssl_cert.py::test_fetch_cert_exits_when_hostname_unparseable`, `integration/test_fetch_ssl_cert.py::test_fetch_cert_exits_on_ssl_error`, `integration/test_fetch_ssl_cert.py::test_fetch_cert_exits_on_os_error`, `integration/test_fetch_ssl_cert.py::test_fetch_cert_subprocess_smoke` |
