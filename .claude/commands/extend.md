# /extend

Reference for extending the application: data contracts and step-by-step recipes.

## metrics_dict shape

Built by `build_metrics_dict` in `app/core/metrics.py`; consumed by both reporters.

```python
{
    "generated_at": str,          # ISO-8601 UTC
    "schema_name": str|None,      # active schema name, or None if default
    "velocity": [
        {sprint_id, sprint_name, start_date, end_date, velocity: float, issue_count: int}
    ],
    "ai_assistance_trend": [
        {sprint_id, sprint_name, start_date, end_date, total_sp, ai_sp, ai_pct: float}
    ],                             # per-sprint AI-assisted story-point percentage
    "ai_usage_details": {
        ai_assisted_issue_count: int,
        tool_breakdown: [{label, count, pct}],
        action_breakdown: [{label, count, pct}]
    },
    "dau": {
        team_avg: float|None, response_count: int,
        by_role: [{role, avg, count}], breakdown: [{answer, count}]
    },
    # enriched in app/cli.py after fetch:
    "filter_name": str|None,
    "filter_id": int|None,
    "filter_jql": str|None,
    "project_key": str|None,
}
```

Full Sprint and Issue dict shapes: `docs/development/architecture.md`.

## Adding a new metric

1. Add `compute_<name>(sprints, sprint_issues) -> list[dict]` to `app/core/metrics.py`; each dict must include `sprint_id` and `sprint_name`. Accept optional schema-driven parameters if the metric depends on configurable field IDs or status names.
2. Call it in `build_metrics_dict()` and add result to the returned dict.
3. Add rendering in `app/reporters/report_md.py` (new section after `cycle_time`).
4. Add rendering in `templates/report.html.j2`.
5. Add `tests/unit/test_<name>.py` using `make_sprint()` and `make_issue()` or `make_issue_with_labels()` factories.

**Note:** `ai_assistance_trend` and `ai_usage_details` are already in `metrics_dict` but **not yet rendered** in the Markdown report. See `docs/product/metrics/ai_assistance_trend.md` for the exact code snippet.

## Adding a new Jira field to the schema

1. Add the field entry to `_DEFAULT_SCHEMA["fields"]` in `app/core/schema.py`.
2. Add the same entry to the default schema in `config/jira_schema.json`.
3. If the field has a known `schema.custom` identifier, add it to `KNOWN_FIELD_SCHEMAS` in `schema.py`.
4. If it should be detected by name, add patterns to `KNOWN_NAME_PATTERNS` in `schema.py`.
5. Add tests in `tests/unit/test_schema.py`.

## Adding a new config var

1. Add to `.env.example` with a comment.
2. Add `os.getenv()` in `app/core/config.py` as module-level constant.
3. Add to `validate_config()` if required.
4. Test in `tests/unit/test_config.py` using `monkeypatch` + `importlib.reload(config)` pattern.

## Extending the dev server

Add a method `_handle_<name>(self)` to the `Handler` class in `app/server/_base.py`, then route it from `do_GET` or `do_POST`. Cover it in `tests/component/test_server.py` using the `server_url` fixture.

## Related

- `/test` — run tests and see factory/fixture reference
- `docs/development/architecture.md` — full data-flow diagrams
