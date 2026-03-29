---
applyTo: "tests/**/*.py"
---

# Testing instructions

The test suite is intentionally layered. Keep changes in the smallest layer that proves the behavior.

- `tests/unit/` is for pure logic with no I/O.
- `tests/component/` is for filesystem or HTTP behavior without broad orchestration.
- `tests/integration/` is for module integration.
- `tests/e2e/` is for end-to-end flows.

Use existing factories and fixtures from `tests/conftest.py`:

- `make_sprint(...)`, `make_issue(...)`, `make_issue_with_changelog(...)`, and `make_issue_with_labels(...)` are plain helper functions, not fixtures.
- `make_issue_with_labels(key, status, points, labels, story_points_field)` — builds an issue with a `labels` field populated; use for all AI adoption metric tests (`compute_ai_assistance_trend`, `compute_ai_usage_details`). Pass `labels` as `list[str]`; `None` → empty list.
- Changelog timestamps must be timezone-aware ISO-8601 strings or cycle-time parsing will fail.
- Config tests should use `monkeypatch` plus `importlib.reload(config)` to re-read module-level env values.

Coverage stats are auto-generated.
If you add, remove, or rename test functions, run:

```bash
python tests/tools/test_coverage.py
```

Do not hand-edit `tests/coverage/test_coverage.md`.
