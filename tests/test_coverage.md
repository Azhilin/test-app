# Test Coverage — AI Adoption Metrics Report

## Test Pyramid

```
              /  E2E  \              ~21 tests  (subprocess, server, Playwright UI)
             /----------\
            / Integration \          ~6 tests   (module boundaries, mocked I/O)
           /----------------\
          /    Contracts      \      ~10 tests  (data shape verification)
         /--------------------\
        /      Component        \    ~38 tests  (mocked Jira, real server)
       /--------------------------\
      /          Unit               \  ~28 tests (pure functions, no I/O)
     /------------------------------\
    /        Existing (~71)           \
   /------------------------------------\
```

## Coverage Matrix

| Module              | Unit | Component | Contract | Integration | E2E |
|---------------------|------|-----------|----------|-------------|-----|
| `app/config.py`     |  Y   |     -     |    -     |      Y      |  -  |
| `app/metrics.py`    |  Y   |     -     |    Y     |      Y      |  -  |
| `app/report_html.py`|  -   |     Y     |    Y     |      Y      |  -  |
| `app/report_md.py`  |  -   |     Y     |    -     |      Y      |  -  |
| `app/jira_client.py`|  -   |     Y     |    -     |      Y      |  -  |
| `server.py`         |  -   |     Y     |    -     |      Y      |  Y  |
| `main.py`           |  Y   |     -     |    -     |      Y      |  Y  |
| `ui/index.html`     |  -   |     -     |    -     |      -      |  Y  |

## Running Tests

```bash
# All tests
pytest tests/ -v

# Fast suite (unit + component + contract)
pytest tests/ -v -m "not integration and not e2e"

# Integration only
pytest tests/ -v -m integration

# E2E only
pytest tests/ -v -m e2e

# Coverage report
pytest tests/ -v --cov=app --cov=main --cov=server --cov-report=term-missing
```

## Test Files

| File                      | Level       | Count | Covers                                |
|---------------------------|-------------|-------|---------------------------------------|
| `test_config.py`          | Unit        |  ~10  | Config loading, validation            |
| `test_metrics.py`         | Unit        |  ~55  | All metrics functions incl. AI        |
| `test_report_html.py`     | Component   |  ~30  | HTML template rendering, visibility   |
| `test_report_md.py`       | Component   |  ~15  | Markdown generation                   |
| `test_main_helpers.py`    | Unit        |   3   | `_timestamp_folder_name()`            |
| `test_jira_client.py`     | Component   |  ~18  | All jira_client functions (mocked)    |
| `test_server.py`          | Component   |  ~15  | HTTP routes, CORS, SSE                |
| `test_contracts.py`       | Contract    |  ~10  | Data shapes across boundaries         |
| `test_integration.py`     | Integration |   6   | Full pipeline, filter flow, server    |
| `test_e2e.py`             | E2E         |   3   | CLI subprocess, server health         |
| `test_e2e_ui.py`          | E2E         |  ~18  | Playwright browser UI tests           |
| `test_imports.py`         | Smoke       |   6   | Module imports                        |
