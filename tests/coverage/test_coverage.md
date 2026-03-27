# Test Coverage — AI Adoption Metrics Report

## Requirements Coverage

### Summary

| Source | Total | ✅ Covered | 🔶 Partial | ❌ Gap | ⬜ N/T | Functional % | Detail |
|--------|-------|-----------|------------|-------|--------|--------------|--------|
| Technical Requirements | 47 | 25 | 0 | 0 | 22 | 100% | [→ detail](requirements/technical_requirements_coverage.md) |
| Installation Requirements | 38 | 5 | 0 | 0 | 33 | 100% | [→ detail](requirements/installation_requirements_coverage.md) |
| App Non Functional Requirements | 33 | 23 | 0 | 0 | 10 | 100% | [→ detail](requirements/app_non_functional_requirements_coverage.md) |
| **All** | **118** | **53** | **0** | **0** | **65** | **100%** |  |

## Test Pyramid

```text
              /  E2E  \              73 tests  (22%)  (subprocess, server, Playwright UI)  → tests/e2e/
             /----------\
            / Integration \           15 tests   (5%)  (module boundaries, mocked I/O)       → tests/integration/
           /----------------\
          /    Component      \      80 tests  (25%)  (filesystem, HTTP, data shapes)        → tests/component/
         /--------------------\
        /        Unit            \   158 tests  (48%)  (pure functions, no I/O)               → tests/unit/
       /------------------------\
                                     ────────────────
                                     326 tests total
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
| `unit/test_cli.py`                | Unit        |    4  | `app.cli.main()` orchestration      |
| `unit/test_metrics.py`            | Unit        |   61  | All metrics functions incl. AI      |
| `unit/test_main_helpers.py`       | Unit        |    5  | `_timestamp_folder_name()`          |
| `unit/test_jira_client.py`        | Unit        |   28  | All jira_client functions (mocked)  |
| `unit/test_server_handlers.py`    | Unit        |   22  | Internal `app.server` handler logic |
| `unit/test_imports.py`            | Unit        |    7  | Module imports (smoke)              |
| `component/test_report_html.py`   | Component   |   31  | HTML template rendering, visibility |
| `component/test_report_md.py`     | Component   |   16  | Markdown generation                 |
| `component/test_server.py`        | Component   |   20  | HTTP routes, CORS, SSE              |
| `component/test_contracts.py`     | Component   |   12  | Data shapes across boundaries       |
| `integration/test_integration.py` | Integration |    6  | Full pipeline, filter flow, server  |
| `integration/test_fetch_ssl_cert.py` | Integration |    9  | fetch_ssl_cert function + CLI smoke |
| `e2e/test_e2e.py`                 | E2E         |    3  | CLI subprocess, server health       |
| `e2e/test_e2e_ui.py`              | E2E         |   24  | Playwright browser UI tests         || `e2e/test_dau_survey_ui.py`      | E2E         |   19  | DAU survey form Playwright tests    |
| `e2e/test_e2e_connection.py`     | E2E         |   27  | Connection panel Playwright tests   |
