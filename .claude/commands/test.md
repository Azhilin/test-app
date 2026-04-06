# /test

Run the full CI test suite (lint + type checking + security + unit + component tests).

## Usage

```bash
/test                    # run unit + component + lint + mypy + bandit
/test --integration      # also include integration tests
/test --e2e              # also include e2e tests
/test --all              # run everything
```

## Implementation

Delegates to `python tests/runners/run_all_checks.py` with optional flags. This runner:
- Runs ruff (format check), mypy (type check), and bandit (security check) in parallel
- Runs pytest with appropriate markers and thread pool
- Sets PYTHONPATH correctly
- Handles Windows/Unix differences
- Returns unified exit code

## Test Conventions

**Test factories** in `tests/conftest.py` are plain functions — call directly in test body (do not inject as fixtures):
- `make_sprint(id, name="", start=None, end=None)` — omit state; metrics don't filter on it
- `make_issue(key, status="Done", points=5.0, story_points_field="customfield_10016")`
- `make_issue_with_changelog(key, in_progress_ts=None, done_ts=None)` — timestamps must be ISO-8601 with timezone offset; naive datetimes cause cycle time to return `None`
- `make_issue_with_labels(key, status="Done", points=5.0, labels=None, story_points_field="customfield_10016")` — use for all AI metrics tests

**Pytest fixtures** (inject via function arg, not call):
- `minimal_metrics_dict` — metrics dict with sample data
- `empty_metrics_dict` — metrics dict with no velocity/cycle-time data

**Config tests** use `importlib.reload(config)` with `monkeypatch.setenv()` / `delenv()` to re-parse module-level constants.

**Coverage stats** in `tests/coverage/test_coverage.md` are auto-generated — never hand-edit. Run `/coverage` to refresh.

## Related

- `/coverage` — Update test coverage stats
- `/lint` — Run lint + type checking only (faster feedback during development)
