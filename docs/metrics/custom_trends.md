# Custom Trends

## Purpose

Custom Trends is a built-in extension point that lets teams add their own per-sprint metrics
to both the HTML and Markdown reports without modifying the core reporting pipeline.

Out of the box, `compute_custom_trends()` is a placeholder that returns an empty list.
No data is displayed in either report when no custom trends are implemented. Once you add
a calculation, both report formats will automatically pick it up via the `metrics_dict`.

This answers the question: *"How do I add a team-specific metric that appears in our
standard reports alongside velocity and cycle time?"*

## Use Cases

Custom trends are appropriate for any per-sprint measurement that:

- Can be computed from Jira issue data (fields, labels, story points, status, etc.)
- Needs to be tracked sprint-over-sprint as a trend
- Is specific to your team, organisation, or process

**Example metrics you could implement:**

- **Bug rate** — percentage of done issues that are bugs (by issue type).
- **Carry-over rate** — percentage of sprint issues that were not in the original sprint scope
  (requires custom field or label).
- **Defect escape rate** — number of bugs reported in a sprint vs. stories completed.
- **Unestimated issue ratio** — fraction of done issues with no story points.
- **Review cycle count** — average number of times an issue was moved back to "In Progress"
  from "In Review" (requires changelog).
- **AI-assisted cycle time delta** — average cycle time for AI-assisted issues vs. non-assisted
  (requires changelog + AI label).

## Report Availability

| Report format | Available |
|---|---|
| HTML report | yes — table rendered when list is non-empty |
| Markdown report | yes — table rendered when list is non-empty |

Both renderers display whatever key/value pairs are in the returned dicts, using `sprint_name`
as the first column and all other keys as additional columns.

## Required Jira Fields

Custom trends have no fixed field requirements — they depend entirely on what you implement.
The function receives the same `sprints` and `sprint_issues` data that velocity uses, so any
field present on issues is available.

Common fields you may access:

| Logical key | Default Jira field ID | Type | Example use |
|---|---|---|---|
| `issuetype` | `issuetype` | string | Filter to bugs, stories, tasks |
| `story_points` | `customfield_10016` | number | Estimate-related trends |
| `labels` | `labels` | array | Label-based categorisation |
| `status` | `status` | string | Done/in-progress filtering |
| `priority` | `priority` | string | Priority distribution |

## Required Configuration

No dedicated configuration variables exist for custom trends. If your metric needs
configurable parameters, add them to `.env` and `app/core/config.py` following the
[extension pattern for config variables](../../.cursor/rules/extension-patterns.mdc).

## Calculation

The placeholder implementation:

```python
def compute_custom_trends(
    _sprints: list[dict],
    _sprint_issues: dict[int, list[dict]],
) -> list[dict]:
    return []
```

Replace the body with your own logic. Each item in the returned list must follow this shape:

```python
{
    "sprint_id":   int,    # required — used internally for joins
    "sprint_name": str,    # required — rendered as the first column
    "<your_key>":  ...,    # one or more metric values
}
```

**Example — bug rate per sprint:**

```python
def compute_custom_trends(
    sprints: list[dict],
    sprint_issues: dict[int, list[dict]],
) -> list[dict]:
    rows = []
    for sprint in sprints:
        sid = sprint.get("id")
        if sid is None:
            continue
        issues = sprint_issues.get(sid) or []
        done = [i for i in issues if _is_done(i)]
        bug_count = sum(
            1 for i in done
            if (i.get("fields") or {}).get("issuetype", {}).get("name", "").lower() == "bug"
        )
        total = len(done)
        bug_pct = round(bug_count / total * 100, 1) if total else 0.0
        rows.append({
            "sprint_id":   sid,
            "sprint_name": sprint.get("name") or f"Sprint {sid}",
            "bugs_done":   bug_count,
            "bug_pct":     bug_pct,
        })
    return rows
```

This will automatically appear as a table with columns `Sprint`, `bugs_done`, and `bug_pct`
in both the HTML and Markdown reports.

## Recommendations

- **Start with one metric** — add one custom trend, validate it over a few sprints, then add
  more. Multiple unvalidated metrics create noise.
- **Name keys clearly** — the key names become column headers in the report. Use
  human-readable names like `bug_pct` or `carry_over_count` rather than `x` or `val`.
- **Document your metric** — copy this file as a template, replace the placeholder content,
  and commit it to `docs/metrics/` alongside the implementation.
- **Add a unit test** — follow the pattern in `tests/unit/` using `make_sprint()` and
  `make_issue()` from `tests/conftest.py`. Run `python tests/tools/test_coverage.py` after
  adding tests to update the coverage stats.
- **Accept schema-driven parameters** — if your metric depends on configurable statuses or
  field IDs, add optional `done_statuses` or `story_points_field` parameters and wire them
  through `build_metrics_dict()` using `_resolve_schema_params()`.

## Developer / AI Copilot Notes

**Module:** `app/core/metrics.py`

**Function signature (placeholder):**
```python
def compute_custom_trends(
    _sprints: list[dict[str, Any]],
    _sprint_issues: dict[int, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    return []
```

**Location in `metrics_dict`:** `metrics["custom_trends"]` — a list (empty by default).

**Full extension checklist** (from the project's [Extension Patterns](../../.cursor/rules/extension-patterns.mdc)):

1. Replace the body of `compute_custom_trends()` in `app/core/metrics.py`. Each returned
   dict must include `sprint_id` and `sprint_name` plus at least one metric value key.
2. The function is already called in `build_metrics_dict()` and its result is already
   included in `metrics["custom_trends"]` — no pipeline change needed.
3. Both reporters already handle non-empty `custom_trends` automatically:
   - `app/reporters/report_md.py` renders a Markdown table.
   - `templates/report.html.j2` renders an HTML table.
4. Add a test file at `tests/unit/test_custom_trends.py`.
5. Run `python tests/tools/test_coverage.py` to update `tests/test_coverage.md`.

**If you need a completely new metric** (not a replacement for custom_trends), follow the
full *Adding a New Metric* pattern in `extension-patterns.mdc`, which adds a new key to
`metrics_dict` alongside `velocity`, `cycle_time`, and `custom_trends`.

**Test factory:**
```python
from tests.conftest import make_sprint, make_issue
from app.core.metrics import compute_custom_trends

sprint = make_sprint(1, name="Sprint 1")
issues = {1: [make_issue("PROJ-1", status="Done", points=5)]}
result = compute_custom_trends([sprint], issues)
assert result == []  # placeholder always returns empty
```
