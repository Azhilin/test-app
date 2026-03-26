# Test Coverage — AI Adoption Metrics Report

## Test Pyramid

```text
              /  E2E  \              69 tests  (24%)  (subprocess, server, Playwright UI)  → tests/e2e/
             /----------\
            / Integration \           6 tests   (2%)  (module boundaries, mocked I/O)       → tests/integration/
           /----------------\
          /    Component      \      77 tests  (26%)  (filesystem, HTTP, data shapes)        → tests/component/
         /--------------------\
        /        Unit            \   140 tests  (48%)  (pure functions, no I/O)               → tests/unit/
       /------------------------\
                                     ────────────────
                                     292 tests total
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
| `ui/index.html`               |  -   |     -     |      -      |  Y  |

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
| `unit/test_config.py`             | Unit        |   21  | Config loading, validation          |
| `unit/test_cert_validation.py`    | Unit        |    5  | Certificate validation helpers      |
| `unit/test_cli.py`                | Unit        |    3  | `app.cli.main()` orchestration      |
| `unit/test_metrics.py`            | Unit        |   60  | All metrics functions incl. AI      |
| `unit/test_main_helpers.py`       | Unit        |    5  | `_timestamp_folder_name()`          |
| `unit/test_jira_client.py`        | Unit        |   21  | All jira_client functions (mocked)  |
| `unit/test_server_handlers.py`    | Unit        |   18  | Internal `app.server` handler logic |
| `unit/test_imports.py`            | Unit        |    7  | Module imports (smoke)              |
| `component/test_report_html.py`   | Component   |   31  | HTML template rendering, visibility |
| `component/test_report_md.py`     | Component   |   16  | Markdown generation                 |
| `component/test_server.py`        | Component   |   18  | HTTP routes, CORS, SSE              |
| `component/test_contracts.py`     | Component   |   12  | Data shapes across boundaries       |
| `integration/test_integration.py` | Integration |    6  | Full pipeline, filter flow, server  |
| `e2e/test_e2e.py`                 | E2E         |    3  | CLI subprocess, server health       |
| `e2e/test_e2e_ui.py`              | E2E         |   21  | Playwright browser UI tests         |
