# Test Coverage — AI Adoption Metrics Report

## Test Pyramid

```text
              /  E2E  \              69 tests  (22%)  (subprocess, server, Playwright UI)  → tests/e2e/
             /----------\
            / Integration \           15 tests   (5%)  (module boundaries, mocked I/O)       → tests/integration/
           /----------------\
          /    Component      \      77 tests  (24%)  (filesystem, HTTP, data shapes)        → tests/component/
         /--------------------\
        /        Unit            \   156 tests  (49%)  (pure functions, no I/O)               → tests/unit/
       /------------------------\
                                     ────────────────
                                     317 tests total
```

## Coverage Matrix

| Module                        | Unit | Component | Integration | E2E |
|-------------------------------|------|-----------|-------------|-----|
| `app/core/config.py`          |  Y   |     -     |      Y      |  -  |
| `app/core/metrics.py`         |  Y   |     Y     |      Y      |  -  |
| `app/core/jira_client.py`     |  Y   |     Y     |      Y      |  -  |
| `app/reporters/report_html.py`|  -   |     Y     |      Y      |  -  |
| `app/reporters/report_md.py`  |  -   |     Y     |      Y      |  -  |
| `app/server.py`               |  Y   |     Y     |      Y      |  Y  |
| `app/cli.py`                  |  Y   |     -     |      Y      |  Y  |
| `app/utils/cert_utils.py`     |  Y   |     Y     |      -      |  -  |
| `main.py`                     |  Y   |     -     |      Y      |  Y  |
| `tools/fetch_ssl_cert.py`     |  -   |     -     |      Y      |  -  |
| `ui/index.html`               |  -   |     -     |      -      |  Y  |
| `ui/dau_survey.html`          |  -   |     -     |      -      |  Y  |

## Running Tests

```bash
# All tests
pytest tests/ -v

# By layer — folder path
pytest tests/unit/ -v
pytest tests/component/ -v
pytest tests/integration/ -v
pytest tests/e2e/ -v

# By layer — marker (same result, useful in CI)
pytest tests/ -v -m unit
pytest tests/ -v -m component
pytest tests/ -v -m integration
pytest tests/ -v -m e2e

# Fast suite (unit + component only)
pytest tests/ -v -m "not integration and not e2e"

# Coverage report
pytest tests/ -v --cov=app --cov=main --cov=server --cov-report=term-missing
```

### On-demand batch files (Windows)

```text
tests\run_unit_tests.bat
tests\run_component_tests.bat
tests\run_integration_tests.bat
tests\run_e2e_tests.bat
```

## Test Files

| File                              | Layer       | Count | Covers                              |
|-----------------------------------|-------------|-------|-------------------------------------|
| `unit/test_config.py`             | Unit        |   26  | Config loading, validation          |
| `unit/test_cert_validation.py`    | Unit        |    5  | Certificate validation helpers      |
| `unit/test_cli.py`                | Unit        |    3  | `app.cli.main()` orchestration      |
| `unit/test_metrics.py`            | Unit        |   60  | All metrics functions incl. AI      |
| `unit/test_main_helpers.py`       | Unit        |    5  | `_timestamp_folder_name()`          |
| `unit/test_jira_client.py`        | Unit        |   28  | All jira_client functions (mocked)  |
| `unit/test_server_handlers.py`    | Unit        |   22  | Internal `app.server` handler logic |
| `unit/test_imports.py`            | Unit        |    7  | Module imports (smoke)              |
| `component/test_report_html.py`   | Component   |   31  | HTML template rendering, visibility |
| `component/test_report_md.py`     | Component   |   16  | Markdown generation                 |
| `component/test_server.py`        | Component   |   18  | HTTP routes, CORS, SSE              |
| `component/test_contracts.py`     | Component   |   12  | Data shapes across boundaries       |
| `integration/test_integration.py` | Integration |    6  | Full pipeline, filter flow, server  |
| `integration/test_fetch_ssl_cert.py` | Integration |    9  | fetch_ssl_cert function + CLI smoke |
| `e2e/test_e2e.py`                 | E2E         |    3  | CLI subprocess, server health       |
| `e2e/test_e2e_ui.py`              | E2E         |   21  | Playwright browser UI tests         || `e2e/test_dau_survey_ui.py`      | E2E         |   19  | DAU survey form Playwright tests    |
| `e2e/test_e2e_connection.py`     | E2E         |   26  | Connection panel Playwright tests   |

## Requirements Coverage

### Summary

| Source | Total | ✅ Covered | 🔶 Partial | ❌ Gap | ⬜ N/T | Functional % |
|--------|-------|-----------|------------|-------|--------|--------------|
| Technical Requirements | 47 | 25 | 0 | 0 | 22 | 100% |
| Installation Requirements | 38 | 5 | 0 | 0 | 33 | 100% |
| **All** | **85** | **30** | **0** | **0** | **55** | **100%** |

### Technical Requirements

| ID | Requirement | Status | Tests |
|----|-------------|--------|-------|
| TR-01 | Windows 10/11 supported as primary platform with batch launchers | ✅ | `e2e/test_e2e.py::test_server_health_check` |
| TR-02 | macOS supported with manual venv setup | ⬜ | — |
| TR-03 | Linux supported with manual venv setup | ⬜ | — |
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
| TR-19 | project_setup.bat detects Python on system PATH | ⬜ | — |
| TR-20 | project_setup.bat creates .venv in project root | ⬜ | — |
| TR-21 | project_setup.bat installs packages from requirements.txt | ⬜ | — |
| TR-22 | start_app.bat starts server and opens http://localhost:8080 | ⬜ | — |
| TR-23 | python server.py starts on default port 8080 | ✅ | `component/test_server.py::test_get_root_returns_200`, `e2e/test_e2e.py::test_server_health_check` |
| TR-24 | python server.py <PORT> overrides default port | ✅ | `e2e/test_e2e.py::test_server_health_check` |
| TR-25 | python main.py generates reports to generated/reports/ | ✅ | `integration/test_integration.py::test_main_pipeline_success`, `e2e/test_e2e.py::test_cli_clean_via_subprocess` |
| TR-26 | Chrome/Chromium 90+ supported | ✅ | `e2e/test_e2e_ui.py` |
| TR-27 | Microsoft Edge 90+ supported | ⬜ | — |
| TR-28 | Mozilla Firefox 88+ supported | ⬜ | — |
| TR-29 | Safari 14+ supported | ⬜ | — |
| TR-30 | JavaScript must be enabled for UI | ⬜ | — |
| TR-31 | localhost must not be blocked by browser extensions | ⬜ | — |
| TR-32 | Configured port must be free on 127.0.0.1 | ⬜ | — |
| TR-33 | Outbound HTTPS to Jira Cloud (port 443) required | ⬜ | — |
| TR-34 | HTTP server binds to 127.0.0.1 (loopback) by default | ✅ | `unit/test_server_handlers.py::test_run_defaults_host_to_loopback` |
| TR-35 | OS-level proxy env vars may be honoured by HTTP client | ⬜ | — |
| TR-36 | Three credentials required: JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN | ✅ | `unit/test_config.py::test_validate_config_all_set`, `unit/test_config.py::test_validate_config_missing_url`, `unit/test_config.py::test_validate_config_missing_email`, `unit/test_config.py::test_validate_config_missing_token`, `unit/test_config.py::test_validate_config_all_missing` |
| TR-37 | .env listed in .gitignore (credentials never committed) | ⬜ | — |
| TR-38 | API token masked as *** in all server API responses | ✅ | `test_server_config.py::TestGetConfig::test_token_always_masked_as_stars` |
| TR-39 | Credentials transmitted only to JIRA_URL, never to third parties | ✅ | `unit/test_jira_client.py::test_create_client_uses_config_values`, `unit/test_jira_client.py::test_create_client_url_kwarg_matches_config_exactly`, `unit/test_jira_client.py::test_create_client_no_credentials_in_url_kwarg`, `unit/test_jira_client.py::test_create_client_credentials_in_auth_kwargs_only` |
| TR-40 | Credentials settable via browser UI or .env file editing | ✅ | `e2e/test_e2e_connection.py::test_save_posts_correct_payload`, `test_server_config.py::TestWriteEnvFields` |
| TR-41 | JIRA_URL must have no trailing slash | ✅ | `unit/test_config.py::test_jira_url_trailing_slash_stripped`, `unit/test_config.py::test_jira_url_multiple_trailing_slashes_stripped`, `unit/test_config.py::test_jira_url_no_trailing_slash_unchanged`, `unit/test_config.py::test_jira_url_empty_string_safe`, `unit/test_config.py::test_validate_config_warns_trailing_slash` |
| TR-42 | JIRA_EMAIL account needs minimum read access to boards/projects | ⬜ | — |
| TR-43 | config.py detects certs/jira_ca_bundle.pem and passes verify_ssl | ✅ | `unit/test_config.py::test_jira_ssl_cert_returns_true_when_no_file`, `unit/test_config.py::test_jira_ssl_cert_returns_path_when_file_exists` |
| TR-44 | Cert validity (expiry, days remaining, subject) visible in UI | ✅ | `component/test_server.py::test_cert_status_with_valid_cert_returns_enriched_fields`, `e2e/test_e2e_ui.py::test_cert_status_badge_valid_cert` |
| TR-45 | Warning shown for expired or invalid certificate | ✅ | `unit/test_cert_validation.py::test_validate_cert_expired`, `component/test_server.py::test_cert_status_no_cert_returns_exists_false` |
| TR-46 | Auto-fetch cert via UI (Jira Connection tab → Fetch Certificate) | ✅ | `component/test_server.py::test_fetch_cert_missing_url_returns_400`, `component/test_server.py::test_fetch_cert_invalid_url_returns_400`, `component/test_server.py::test_fetch_cert_unreachable_host_returns_error` |
| TR-47 | Auto-fetch cert via CLI (python tools/fetch_ssl_cert.py) | ✅ | `integration/test_fetch_ssl_cert.py::test_fetch_cert_happy_path`, `integration/test_fetch_ssl_cert.py::test_fetch_cert_creates_certs_dir`, `integration/test_fetch_ssl_cert.py::test_fetch_cert_overwrites_existing`, `integration/test_fetch_ssl_cert.py::test_fetch_cert_parses_custom_port`, `integration/test_fetch_ssl_cert.py::test_fetch_cert_exits_when_url_empty`, `integration/test_fetch_ssl_cert.py::test_fetch_cert_exits_when_hostname_unparseable`, `integration/test_fetch_ssl_cert.py::test_fetch_cert_exits_on_ssl_error`, `integration/test_fetch_ssl_cert.py::test_fetch_cert_exits_on_os_error`, `integration/test_fetch_ssl_cert.py::test_fetch_cert_subprocess_smoke` |

### Installation Requirements

| ID | Requirement | Status | Tests |
|----|-------------|--------|-------|
| IR-01 | app/ source code included in release zip | ⬜ | — |
| IR-02 | templates/ Jinja2 HTML report template included | ⬜ | — |
| IR-03 | ui/ browser UI files included | ⬜ | — |
| IR-04 | docs/product/schemas/ folder included (may be empty) | ⬜ | — |
| IR-05 | certs/ placeholder folder with README.txt included | ⬜ | — |
| IR-06 | main.py CLI entry point included | ⬜ | — |
| IR-07 | server.py browser UI server entry point included | ⬜ | — |
| IR-08 | requirements.txt included | ⬜ | — |
| IR-09 | .env.example configuration template included | ⬜ | — |
| IR-10 | project_setup.bat one-time setup script included | ⬜ | — |
| IR-11 | start_app.bat Windows launcher included | ⬜ | — |
| IR-12 | README.md quickstart guide included | ⬜ | — |
| IR-13 | .venv/ NOT included in release zip | ⬜ | — |
| IR-14 | generated/ NOT included in release zip | ⬜ | — |
| IR-15 | requirements-dev.txt NOT included in release zip | ⬜ | — |
| IR-16 | Test files NOT included in release zip | ⬜ | — |
| IR-17 | .env NOT distributed in release zip | ⬜ | — |
| IR-18 | Zip extractable without errors to any destination folder | ⬜ | — |
| IR-19 | Paths with spaces or non-ASCII should be avoided (batch scripts) | ⬜ | — |
| IR-20 | project_setup.bat detects Python 3.10-3.12 on PATH | ⬜ | — |
| IR-21 | project_setup.bat downloads Python 3.12.10 if no compatible version | ⬜ | — |
| IR-22 | Python install via project_setup.bat is per-user (no admin) | ⬜ | — |
| IR-23 | Python installer SHA-256 checksum verified | ⬜ | — |
| IR-24 | Python download enforces TLS 1.2 | ⬜ | — |
| IR-25 | project_setup.bat creates .venv/ virtual environment | ⬜ | — |
| IR-26 | project_setup.bat installs packages from requirements.txt | ⬜ | — |
| IR-27 | project_setup.bat optionally installs requirements-dev.txt | ⬜ | — |
| IR-28 | project_setup.bat creates .env from .env.example if absent | ✅ | `test_server_config.py::TestWriteEnvFields::test_creates_env_from_example_when_env_missing` |
| IR-29 | project_setup.bat prompts to keep or backup+recreate .env on update | ⬜ | — |
| IR-30 | project_setup.bat writes setup log to generated/logs/ | ⬜ | — |
| IR-31 | project_setup.bat closes after 10s or on keypress | ⬜ | — |
| IR-32 | Credentials required in .env before generating reports | ✅ | `integration/test_integration.py::test_main_pipeline_config_fail`, `e2e/test_e2e.py::test_cli_no_credentials_via_subprocess` |
| IR-33 | start_app.bat launches server and opens http://localhost:8080 | ⬜ | — |
| IR-34 | venv created with python3.12 -m venv .venv | ⬜ | — |
| IR-35 | Dependencies installable via .venv/bin/pip install -r requirements.txt | ⬜ | — |
| IR-36 | Server startable with .venv/bin/python server.py | ✅ | `e2e/test_e2e.py::test_server_health_check` |
| IR-37 | Server startable on custom port (server.py 9000) | ✅ | `e2e/test_e2e.py::test_server_health_check` |
| IR-38 | Update process preserves existing .env credentials | ✅ | `test_server_config.py::TestWriteEnvFields::test_replaces_existing_key`, `test_server_config.py::TestWriteEnvFields::test_example_file_is_not_modified`, `test_server_config.py::TestWriteEnvFields::test_preserves_other_credential_keys_when_updating_url`, `test_server_config.py::TestWriteEnvFields::test_partial_update_preserves_untouched_key`, `test_server_config.py::TestWriteEnvFields::test_preserves_unrelated_optional_env_vars`, `test_server_config.py::TestWriteEnvFields::test_preserves_comment_lines_and_blanks` |
