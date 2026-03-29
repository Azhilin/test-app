# Velocity

## Purpose

Velocity measures how much work a team completes in each sprint, expressed in story points.
It is the most widely used leading indicator of team throughput: a stable or rising velocity
means the team is delivering predictably, while sudden drops or spikes signal disruption,
scope changes, or estimation drift.

This metric answers the core planning question: *"How many story points can we expect this
team to deliver in the next sprint?"*

## Use Cases

- **Sprint planning** — use the average of the last 3–5 sprints as the team's capacity target.
- **Trend analysis** — spot sustained improvement (e.g. after adopting new practices) or
  decline (e.g. after team restructuring or technical-debt accumulation).
- **Predictability assessment** — high variance sprint-to-sprint suggests unreliable estimation
  or frequent scope changes.
- **Capacity comparison** — compare velocity across teams or time periods (normalised to team
  size) to inform staffing decisions.
- **AI adoption impact** — use alongside the AI Assistance Trend metric to assess whether
  AI tooling correlates with higher throughput.

## Report Availability

| Report format | Available |
|---|---|
| HTML report | yes — bar chart with running average line |
| Markdown report | yes — ASCII bar chart + data table |

## Required Jira Fields

| Logical key | Default Jira field ID | Type | Notes |
|---|---|---|---|
| `story_points` | `customfield_10016` | number | Must be set on each issue; issues with no value count as 0 points |
| `status` | `status` | string | Used to identify completed issues |
| `sprint` | `customfield_10020` | array | Groups issues by sprint |

The `story_points` field ID varies by Jira instance. Set it on the active schema in
`config/jira_schema.json` (via the UI's *Jira Field Schema* card or by editing that file).
If the file is missing, the app uses a built-in default schema (same default ID as Jira Cloud).

Done statuses are configurable in the schema's `status_mapping.done_statuses` list (defaults:
`Done`, `Closed`, `Resolved`, `Complete`).

## Required Configuration

| Variable | Default | Effect |
|---|---|---|
| `JIRA_SCHEMA_NAME` | _(unset)_ | Optional: which `schema_name` in `config/jira_schema.json` the CLI uses (`python main.py`) |
| `JIRA_SPRINT_COUNT` | `10` | Number of past sprints fetched and displayed |
| `JIRA_BOARD_ID` | _(first board)_ | Scopes sprint and issue fetch to a specific board |

Story points and other field IDs always come from the active schema (file or built-in default).

## Calculation

1. **Fetch sprints** — retrieve the last `JIRA_SPRINT_COUNT` sprints for the board.
2. **Fetch issues** — for each sprint, retrieve all issues assigned to it.
3. **Filter to done issues** — keep only issues whose `status.name` (lowercased) is in the
   configured `done_statuses` set.
4. **Sum story points** — add up the `story_points` field value for each done issue.
   Issues with a missing or non-numeric value contribute 0.
5. **Record per sprint** — store `velocity` (rounded to 1 decimal place) and `issue_count`
   (number of done issues) for each sprint.

**Formula:**

```
velocity(sprint) = Σ story_points(issue)  for all issues where status ∈ done_statuses
```

No weighting, averaging, or normalisation is applied within a single sprint. The HTML report
overlays a running average line for visual trend interpretation.

## Recommendations

- **Estimate all issues** — velocity is meaningless if a large share of issues have no story
  points. Enforce estimation as a team norm during sprint planning.
- **Use a rolling average** — a single sprint's velocity is noisy. For planning, average the
  last 3–5 sprints.
- **Don't compare across teams directly** — story-point scales differ per team. Use velocity
  as a self-comparison tool within one team over time.
- **Investigate outlier sprints** — a sprint with unusually high or low velocity warrants
  a quick check: were there holidays, carry-over issues, or an estimation re-calibration?
- **Watch issue count alongside points** — a sprint can show high velocity by completing many
  small issues. If `issue_count` is unusually high, check whether large stories are being
  split artificially to inflate the number.
- **Align done statuses with your workflow** — if your board uses custom status names (e.g.
  `Shipped`, `Accepted`), add them to `status_mapping.done_statuses` in the schema; otherwise
  those issues will be excluded from velocity.

## Developer / AI Copilot Notes

**Module:** `app/core/metrics.py`

**Primary function:**
```python
def compute_velocity(
    sprints: list[dict],
    sprint_issues: dict[int, list[dict]],
    story_points_field: str | None = None,
    done_statuses: frozenset[str] | None = None,
) -> list[dict]:
    ...
```

**Output shape (one item per sprint):**
```python
{
    "sprint_id": int,
    "sprint_name": str,
    "start_date": str | None,   # ISO-8601 or None
    "end_date":   str | None,   # ISO-8601 or None
    "velocity":   float,        # story points, rounded to 1 dp
    "issue_count": int,         # number of done issues
}
```

**Location in `metrics_dict`:** `metrics["velocity"]` — a list ordered by the input `sprints` list.

**Helper functions used:**
- `_get_story_points(issue, story_points_field)` — extracts the numeric field value, returns `0.0` on missing/invalid.
- `_is_done(issue, done_statuses)` — checks `fields.status.name` (lowercased) against `done_statuses`.
- `_resolve_schema_params(schema)` — pulls `story_points_field` and `done_statuses` from the active schema dict.

**Extending velocity:**
- To change the aggregation (e.g. count issues instead of points), modify `_get_story_points` or
  add a parallel `compute_velocity_by_count` function following the same signature.
- To add a new "done" status, update `status_mapping.done_statuses` in the schema JSON — no code
  change required.
- To add velocity to a new report format, consume `metrics["velocity"]` from the dict returned by
  `build_metrics_dict()`.

**Test factory:** use `make_sprint()` and `make_issue()` from `tests/conftest.py`.

```python
from tests.conftest import make_sprint, make_issue
from app.core.metrics import compute_velocity

sprint = make_sprint(1, name="Sprint 1")
issues = {1: [make_issue("PROJ-1", status="Done", points=5)]}
result = compute_velocity([sprint], issues)
assert result[0]["velocity"] == 5.0
```
