# Test Coverage — AI Adoption Metrics Report

## Requirements Coverage

### Summary

| Source | Total | ✅ Covered | 🔶 Partial | ❌ Gap | ⬜ N/T | Functional % | Detail |
|--------|-------|-----------|------------|-------|--------|--------------|--------|
| Technical Requirements | 47 | 25 | 0 | 0 | 22 | 100% | [→ detail](requirements/technical_requirements_coverage.md) |
| Installation Requirements | 38 | 5 | 0 | 0 | 33 | 100% | [→ detail](requirements/installation_requirements_coverage.md) |
| App Non Functional Requirements | 33 | 23 | 0 | 0 | 10 | 100% | [→ detail](requirements/app_non_functional_requirements_coverage.md) |
| Dau Survey Requirements | 31 | 26 | 0 | 3 | 2 | 90% | [→ detail](requirements/dau_survey_requirements_coverage.md) |
| Jira Connection Requirements | 33 | 23 | 0 | 6 | 4 | 79% | [→ detail](requirements/jira_connection_requirements_coverage.md) |
| Jira Data Fetching Requirements | 22 | 16 | 1 | 2 | 3 | 89% | [→ detail](requirements/jira_data_fetching_requirements_coverage.md) |
| Jira Schema Requirements | 29 | 23 | 0 | 2 | 4 | 92% | [→ detail](requirements/jira_schema_requirements_coverage.md) |
| Jira Filter Management Requirements | 23 | 21 | 0 | 0 | 2 | 100% | [→ detail](requirements/jira_filter_management_requirements_coverage.md) |
| Logging Requirements | 18 | 16 | 0 | 0 | 2 | 100% | [→ detail](requirements/logging_requirements_coverage.md) |
| Report Generation Requirements | 33 | 30 | 0 | 0 | 3 | 100% | [→ detail](requirements/report_generation_requirements_coverage.md) |
| **All** | **307** | **208** | **1** | **13** | **85** | **94%** |  |

## Test Pyramid

```text
              /  E2E  \              102 tests  (19%)  (Playwright browser UI)  → tests/e2e/
             /----------\
            / Integration \           19 tests   (4%)  (cross-module flows, subprocess)       → tests/integration/
           /----------------\
          /    Component      \      155 tests  (29%)  (filesystem, HTTP, data shapes)        → tests/component/
         /--------------------\
        /        Unit            \   254 tests  (48%)  (pure functions, no I/O)               → tests/unit/
       /------------------------\
                                     ────────────────
                                     530 tests total
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
| `app/utils/logging_setup.py`  |  Y   |     -     |      -      |  -  |
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
| `unit/test_config.py`             | Unit        |   44  | Config loading, validation          |
| `unit/test_cert_validation.py`    | Unit        |    5  | Certificate validation helpers      |
| `unit/test_cli.py`                | Unit        |    4  | `app.cli.main()` orchestration      |
| `unit/test_metrics.py`            | Unit        |   57  | All metrics functions incl. AI      |
| `unit/test_main_helpers.py`       | Unit        |    5  | `_timestamp_folder_name()`          |
| `unit/test_jira_client.py`        | Unit        |   28  | All jira_client functions (mocked)  |
| `unit/test_server_handlers.py`    | Unit        |   24  | Internal `app.server` handler logic |
| `unit/test_imports.py`            | Unit        |    8  | Module imports (smoke)              |
| `unit/test_logging_setup.py`      | Unit        |   13  | Logging setup, SUCCESS level, file creation, format |
| `component/test_report_html.py`   | Component   |   28  | HTML template rendering, visibility |
| `component/test_report_md.py`     | Component   |   18  | Markdown generation                 |
| `component/test_server.py`        | Component   |   32  | HTTP routes, CORS, SSE              |
| `component/test_contracts.py`     | Component   |   11  | Data shapes across boundaries       |
| `integration/test_integration.py` | Integration |    6  | Full pipeline, filter flow, server  |
| `integration/test_fetch_ssl_cert.py` | Integration |   10  | fetch_ssl_cert function + CLI smoke |
| `e2e/test_e2e.py`                 | E2E         |    3  | CLI subprocess, server health       |
| `e2e/test_e2e_ui.py`              | E2E         |   32  | Playwright browser UI tests         || `e2e/test_dau_survey_ui.py`      | E2E         |   23  | DAU survey form Playwright tests    |
| `e2e/test_e2e_connection.py`     | E2E         |   41  | Connection panel Playwright tests   |
