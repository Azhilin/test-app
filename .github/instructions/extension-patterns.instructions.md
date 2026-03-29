---
applyTo: "app/core/metrics.py,app/core/schema.py,app/core/config.py,app/reporters/**/*.py,templates/**/*.j2,tests/unit/**/*.py,config/*.json"
---

# Extension patterns

## Adding a new metric

1. Add `compute_<name>(sprints, sprint_issues) -> list[dict]` to `app/core/metrics.py`; include `sprint_id` and `sprint_name` in every row; accept optional schema-driven params (`done_statuses`, `story_points_field`) if the metric depends on configurable field IDs or status names.
2. Call it in `build_metrics_dict()` and add the result to the returned dict.
3. Add rendering section in `app/reporters/report_md.py` (after `custom_trends`).
4. Add rendering in `templates/report.html.j2` (metrics context variable).
5. Add `tests/unit/test_<name>.py` using `make_sprint()`, `make_issue()`, or `make_issue_with_labels()` factories from `tests/conftest.py`.
6. Run `python tests/tools/test_coverage.py` to refresh `tests/coverage/test_coverage.md`.

**Known gap:** `ai_assistance_trend` and `ai_usage_details` are already in `metrics_dict` (steps 1–2 complete) but step 3 (Markdown rendering) is not yet done. See `docs/product/metrics/ai_assistance_trend.md` for the exact code snippet to add to `report_md.py`.

## Adding a new Jira schema field

1. Add the field entry to `_DEFAULT_SCHEMA["fields"]` in `app/core/schema.py`.
2. Add the same entry to the default schema in `config/jira_schema.json`.
3. If the field has a known `schema.custom` identifier, add it to `KNOWN_FIELD_SCHEMAS` in `schema.py`.
4. If it should be detected by name, add patterns to `KNOWN_NAME_PATTERNS` in `schema.py`.
5. Add tests in `tests/unit/test_schema.py`.

## Adding a new config environment variable

1. Add to `.env.example` with a comment.
2. Add `os.getenv()` in `app/core/config.py` as a module-level constant.
3. Add to `validate_config()` if the variable is required for the app to run.
4. Test in `tests/unit/test_config.py` using `monkeypatch` + `importlib.reload(config)`.

## Named filter presets (`config/jira_filters.json`)

Each entry: `filter_name` (display), `slug` (machine ID), `description`, `jql` (JQL string), `params` (env-var-style overrides: `JIRA_PROJECT`, `JIRA_TEAM_ID`, `schema_name`, etc.). Source-controlled like `config/jira_schema.json`, not generated output.
