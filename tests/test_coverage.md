# Test Coverage — AI Adoption Metrics Report

## Test Pyramid

```
              /  E2E  \              21 tests  (10%)  (subprocess, server, Playwright UI)  → tests/e2e/
             /----------\
            / Integration \           6 tests   (3%)  (module boundaries, mocked I/O)       → tests/integration/
           /----------------\
          /    Component      \      73 tests  (36%)  (filesystem, HTTP, data shapes)        → tests/component/
         /--------------------\
        /        Unit            \   104 tests  (51%)  (pure functions, no I/O)               → tests/unit/
       /------------------------\
                                     ────────────────
                                     204 tests total
```

## Coverage Matrix

| Module              | Unit | Component | Integration | E2E |
|---------------------|------|-----------|----------|-------------|-----|
| `app/config.py`     |  Y   |     -     |      Y      |  -  |
| `app/metrics.py`    |  Y   |     Y     |      Y      |  -  |
| `app/report_html.py`|  -   |     Y     |      Y      |  -  |
| `app/report_md.py`  |  -   |     Y     |      Y      |  -  |
| `app/jira_client.py`|  Y   |     Y     |      Y      |  -  |
| `server.py`         |  -   |     Y     |      Y      |  Y  |
| `main.py`           |  Y   |     -     |      Y      |  Y  |
| `ui/index.html`     |  -   |     -     |      -      |  Y  |

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

```
tests\run_unit_tests.bat
tests\run_component_tests.bat
tests\run_integration_tests.bat
tests\run_e2e_tests.bat
```

## Test Files

| File                               | Layer       | Count | Covers                                |
|------------------------------------|-------------|-------|---------------------------------------|
| `unit/test_config.py`              | Unit        |   14 | Config loading, validation            |
| `unit/test_metrics.py`             | Unit        |   57 | All metrics functions incl. AI        |
| `unit/test_main_helpers.py`        | Unit        |    3 | `_timestamp_folder_name()`            |
| `unit/test_jira_client.py`         | Unit        |   19 | All jira_client functions (mocked)    |
| `unit/test_imports.py`             | Unit        |    6 | Module imports (smoke)                |
| `component/test_report_html.py`    | Component   |   31 | HTML template rendering, visibility   |
| `component/test_report_md.py`      | Component   |   16 | Markdown generation                   |
| `component/test_server.py`         | Component   |   14 | HTTP routes, CORS, SSE                |
| `component/test_contracts.py`      | Component   |   12 | Data shapes across boundaries         |
| `integration/test_integration.py`  | Integration |    6 | Full pipeline, filter flow, server    |
| `e2e/test_e2e.py`                  | E2E         |    3 | CLI subprocess, server health         |
| `e2e/test_e2e_ui.py`               | E2E         |   18 | Playwright browser UI tests           |
