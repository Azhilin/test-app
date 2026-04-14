# AI Assistance Trend

## Purpose

AI Assistance Trend tracks the percentage of completed story points that were delivered with
AI tool assistance, sprint by sprint. It answers the question: *"Is our team actually using
AI tools, and is that usage growing over time?"*

The metric works by detecting a designated Jira label (default: `AI_assistance`) on completed
issues. When combined with velocity data, it reveals not just whether AI adoption is happening
but whether it correlates with higher throughput and shorter cycle times — making it the core
measure for an AI adoption programme.

## Use Cases

- **Adoption tracking** — confirm that AI tools are being used and measure the rate of uptake
  across sprints.
- **Trend reporting** — present leadership with a clear sprint-over-sprint trend line showing
  AI adoption momentum.
- **Team comparison** — run the report per board/team to identify leaders and laggards in AI
  adoption (requires a separate report run per team).
- **ROI hypothesis** — pair with velocity: if AI-assisted sprints show higher velocity, there
  is a correlation worth investigating as a productivity signal.
- **Goal-setting** — set a target percentage (e.g. "50% of story points AI-assisted by Q3")
  and track progress each sprint.
- **Incentive accountability** — when teams are asked to label AI-assisted work, this metric
  makes that commitment measurable.

## Report Availability

| Report format | Available |
|---|---|
| HTML report | yes — line chart + per-sprint data table |
| Markdown report | **not yet rendered** — data is computed and present in `metrics_dict`; rendering is planned |

> The computed data is available at `metrics["ai_assistance_trend"]` after every report run.
> Adding it to the Markdown report requires a new section in `app/reporters/report_md.py`.
> See the *Developer / AI Copilot Notes* section below for the exact steps.

## Required Jira Fields

| Logical key | Default Jira field ID | Type | Notes |
|---|---|---|---|
| `story_points` | `customfield_10016` | number | Issues with no points contribute 0 to both totals |
| `status` | `status` | string | Used to identify done issues |
| `labels` | `labels` | array | Must contain `AI_ASSISTED_LABEL` value to be counted as AI-assisted |
| `sprint` | `customfield_10020` | array | Groups issues by sprint |

## Required Configuration

| Variable | Default | Effect |
|---|---|---|
| `AI_ASSISTED_LABEL` | `AI_assistance` | The exact Jira label that marks an issue as AI-assisted |
| `AI_EXCLUDE_LABELS` | _(empty)_ | Comma-separated labels; issues carrying any of these are excluded from **both** numerator and denominator. Use for overhead, non-delivery work (e.g. `admin`, `spike`). |
| `JIRA_SCHEMA_NAME` | _(unset)_ | Optional CLI: schema entry in `config/jira_schema.json` (field IDs including story points) |

**Example `.env` configuration:**
```
AI_ASSISTED_LABEL=AI_assistance
AI_EXCLUDE_LABELS=spike,admin,tech-debt
```

## Calculation

Before per-sprint computation, `sprint_issues` is pre-processed so that each ticket key
appears only in its **last (most recent) sprint**. A ticket carried forward across sprints
is therefore counted once — in the sprint where it was completed — preventing inflation of
both `total_sp` and `ai_sp` in earlier sprints.

For each sprint:

1. **Filter to done issues** — keep issues whose `status.name` (lowercased) is in `done_statuses`.
2. **Apply exclusions** — remove issues that carry any label in `AI_EXCLUDE_LABELS`.
3. **Sum total story points** (`total_sp`) — sum `story_points` for all remaining done issues.
4. **Sum AI story points** (`ai_sp`) — sum `story_points` for done issues that also carry the
   `AI_ASSISTED_LABEL` label.
5. **Compute percentage:**

```
ai_pct(sprint) = (ai_sp / total_sp) × 100   if total_sp > 0, else 0.0
```

Result is rounded to 1 decimal place.

> Note: exclusions apply to the denominator too. This is intentional — it ensures that
> non-delivery work (e.g. administrative tickets) does not dilute the AI adoption percentage.

## Recommendations

- **Agree on the label name before the first sprint** — the label value must be consistent
  across all issues. Even a typo (`AI_Assistance` vs `AI_assistance`) will cause misses.
  The label is case-sensitive in the Jira UI.
- **Add labelling to your Definition of Done** — teams forget to label issues after the fact.
  Make "add `AI_assistance` label if AI tools were used" part of the ticket-closure checklist.
- **Use `AI_EXCLUDE_LABELS` for non-delivery work** — spikes, admin, and ceremony tickets
  typically have no AI involvement. Excluding them prevents the denominator from being inflated
  by work that was never a candidate for AI assistance.
- **Interpret 0% sprints carefully** — a sprint showing 0% AI assistance can mean the team
  didn't use AI tools, or that they simply forgot to label. Check with the team before drawing
  conclusions.
- **Don't target 100%** — not every issue type benefits equally from AI tools. A realistic
  ceiling for most teams is 40–70%; forcing higher numbers leads to label inflation rather
  than genuine usage.
- **Pair with cycle time** — if AI-assisted issues consistently have shorter cycle times, that
  is evidence of productivity impact beyond just adoption rate.

## Developer / AI Copilot Notes

**Module:** `app/core/metrics.py`

**Primary function:**
```python
def compute_ai_assistance_trend(
    sprints: list[dict],
    sprint_issues: dict[int, list[dict]],
    ai_assisted_label: str | None = None,       # defaults to config.AI_ASSISTED_LABEL
    ai_exclude_labels: list[str] | None = None, # defaults to config.AI_EXCLUDE_LABELS
    story_points_field: str | None = None,
    done_statuses: frozenset[str] | None = None,
) -> list[dict]:
    ...
```

**Output shape (one item per sprint):**
```python
{
    "sprint_id":   int,
    "sprint_name": str,
    "start_date":  str | None,  # ISO-8601 or None
    "end_date":    str | None,  # ISO-8601 or None
    "total_sp":    float,       # done SP after exclusions, rounded to 1 dp
    "ai_sp":       float,       # AI-assisted done SP, rounded to 1 dp
    "ai_pct":      float,       # percentage, rounded to 1 dp
}
```

**Location in `metrics_dict`:** `metrics["ai_assistance_trend"]` — a list ordered by the input
`sprints` list.

**Adding to the Markdown report** (`app/reporters/report_md.py`):

Add a new section after the cycle time block in `generate_md()`:

```python
ai_trend = metrics.get("ai_assistance_trend") or []
if ai_trend:
    parts.append("## AI Assistance Trend")
    parts.append("")
    headers = ["Sprint", "Total SP", "AI-assisted SP", "AI %"]
    rows = [
        [row["sprint_name"], row["total_sp"], row["ai_sp"], f"{row['ai_pct']}%"]
        for row in ai_trend
    ]
    parts.append(_md_table(headers, rows))
    parts.append("")
```

**Test factory:**
```python
from tests.conftest import make_sprint, make_issue
from app.core.metrics import compute_ai_assistance_trend

sprint = make_sprint(1, name="Sprint 1")
issues = {1: [
    make_issue("PROJ-1", status="Done", points=5),   # no AI label
    make_issue("PROJ-2", status="Done", points=3),   # AI-assisted
]}
# Add AI label to second issue
issues[1][1]["fields"]["labels"] = ["AI_assistance"]

result = compute_ai_assistance_trend([sprint], issues, ai_assisted_label="AI_assistance")
assert result[0]["ai_pct"] == 37.5   # 3 / 8 * 100
```
