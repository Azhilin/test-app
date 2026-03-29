# Cycle Time

## Purpose

Cycle time measures how long it takes for an individual issue to move from active work to
completion — from the moment a developer picks it up ("In Progress") to the moment it is
marked done. Reported as statistical aggregates (mean, median, min, max) across a sample of
recently completed issues, it answers the question: *"How quickly does work flow through our
process once someone starts on it?"*

Unlike velocity (which measures output volume), cycle time measures delivery speed and process
efficiency. Together they give a complete picture of team performance.

## Use Cases

- **Process health check** — a rising median cycle time is an early warning that work is
  getting blocked, batched, or under-resourced.
- **Predictability** — the tighter the min-to-max range, the more consistently work flows.
  Wide ranges suggest unpredictable blockers or mixed issue sizes.
- **SLA and commitment** — use mean or median cycle time to set realistic delivery
  expectations with stakeholders.
- **Bottleneck identification** — when combined with status breakdown data, a long cycle time
  points to specific handoff stages that are stalling.
- **Impact of AI tooling** — compare cycle time before and after introducing AI coding
  assistants to measure whether they accelerate delivery.
- **Sprint retrospectives** — flag issues that took far longer than the median as candidates
  for discussion.

## Report Availability

| Report format | Available |
|---|---|
| HTML report | yes — statistical summary table |
| Markdown report | yes — statistical summary table |

## Required Jira Fields

| Logical key | Default Jira field ID | Type | Notes |
|---|---|---|---|
| `status` | `status` | string | Used to identify in-progress and done transitions in the changelog |
| Changelog histories | _(expand parameter)_ | event log | `expand=changelog` must be requested; contains status transition timestamps |

> **Important:** Cycle time is calculated entirely from the issue changelog, not from the
> current `status` field value. The changelog records every status transition with a
> timezone-aware ISO-8601 timestamp. Issues fetched without the changelog expansion (or with
> naive/timezone-unaware timestamps) will be excluded from the sample.

In-progress and done statuses are configurable in the schema's `status_mapping` block.
Defaults:
- `in_progress_statuses`: `In Progress`
- `done_statuses`: `Done`, `Closed`, `Resolved`, `Complete`

## Required Configuration

| Variable | Default | Effect |
|---|---|---|
| `JIRA_SPRINT_COUNT` | `10` | Controls how many sprints' worth of done issues are candidates for cycle-time sampling |

The maximum number of issues sampled for changelog fetch is hard-capped at 100 by
`get_done_issue_keys_for_changelog()`, taking the most recently completed issues first.

## Calculation

1. **Select done issues** — from all issues across the fetched sprints, identify done issues
   (up to 100, most recent first).
2. **Fetch changelogs** — retrieve each issue's changelog (Jira `expand=changelog` API call).
3. **Find the start timestamp** — scan changelog histories in order; record the timestamp of
   the *first* transition where `toString` (lowercased) is in `in_progress_statuses`.
4. **Find the end timestamp** — scan all histories; use the timestamp of the *last* transition
   where `toString` (lowercased) is in `done_statuses`.
5. **Compute days** — `cycle_days = (done_at - in_progress_at).total_seconds() / 86400`,
   rounded to 1 decimal place. If `done_at < in_progress_at`, the issue is excluded.
6. **Aggregate** — compute mean, median, min, and max across all valid `cycle_days` values.

**Formula:**

```
cycle_days(issue) = (done_at − in_progress_at) in days

mean_days   = mean(cycle_days for all valid issues)
median_days = median(cycle_days for all valid issues)
min_days    = min(cycle_days)
max_days    = max(cycle_days)
```

Issues are excluded from the sample if:
- They have no changelog, or
- No transition into an in-progress status is found, or
- No transition into a done status is found, or
- The changelog timestamps are timezone-naive (Jira always provides timezone-aware timestamps,
  but synthetic/test data must include a UTC offset).

## Recommendations

- **Configure your status names** — if your team uses custom status names such as `Active`,
  `In Review`, or `Shipped`, add them to `in_progress_statuses` or `done_statuses` in the
  schema. Mismatched statuses silently shrink the sample.
- **Monitor sample size** — a sample of fewer than 10 issues makes the statistics unreliable.
  If `sample_size` is low, increase `JIRA_SPRINT_COUNT` or broaden your in-progress/done
  status configuration.
- **Use median over mean** — a single very long-running issue (e.g. a quarterly epic) can
  skew the mean significantly. Median is more robust for everyday interpretation.
- **Exclude epics and spikes** — if your team tracks epics or time-boxed spikes as Jira
  issues, their artificially long cycle times will distort the sample. Consider filtering by
  issue type using `JIRA_ISSUE_TYPES` in `.env`.
- **Interpret the min carefully** — a very low minimum often represents a bug fix or hotfix
  that was fast-tracked; it does not mean all work could be done that quickly.
- **Pair with velocity** — high velocity + high cycle time suggests the team completes many
  items but each takes a long time to move through the pipeline, pointing to batch-processing
  or waiting time.

## Developer / AI Copilot Notes

**Module:** `app/core/metrics.py`

**Primary functions:**

```python
def compute_cycle_time(
    issues_with_changelog: list[dict],
    done_statuses: frozenset[str] | None = None,
    in_progress_statuses: frozenset[str] | None = None,
) -> dict:
    ...

def _cycle_time_from_changelog(
    issue: dict,
    done_statuses: frozenset[str] | None = None,
    in_progress_statuses: frozenset[str] | None = None,
) -> float | None:
    ...
```

**Output shape:**
```python
{
    "mean_days":   float | None,   # None when sample_size == 0
    "median_days": float | None,
    "min_days":    float | None,
    "max_days":    float | None,
    "sample_size": int,
    "values":      list[float],    # sorted ascending; individual cycle times
}
```

**Location in `metrics_dict`:** `metrics["cycle_time"]` — a single dict (not a list).

**Issue dict shape required (changelog):**
```python
{
    "key": str,
    "fields": {"status": {"name": str}},
    "changelog": {
        "histories": [
            {
                "created": str,   # ISO-8601 with timezone offset, e.g. "2026-03-01T10:00:00+00:00"
                "items": [
                    {"field": "status", "fromString": str, "toString": str}
                ]
            }
        ]
    }
}
```

**Helper function for selecting which issues to fetch changelogs for:**
```python
def get_done_issue_keys_for_changelog(
    sprints, sprint_issues, max_count=100, done_statuses=None
) -> list[str]:
    ...
```

**Extending cycle time:**
- To change the start point (e.g. use "To Do" → "In Progress" rather than first in-progress
  transition), modify `_cycle_time_from_changelog` — the logic scans histories sequentially.
- To add per-sprint cycle time (instead of aggregate), group `issues_with_changelog` by sprint
  before calling `compute_cycle_time`.
- To surface cycle time distributions in the MD report, add a section in
  `app/reporters/report_md.py` after the existing cycle time table.

**Test factory:**
```python
from tests.conftest import make_issue_with_changelog
from app.core.metrics import compute_cycle_time

issue = make_issue_with_changelog(
    "PROJ-1",
    in_progress_ts="2026-03-01T09:00:00+00:00",
    done_ts="2026-03-03T09:00:00+00:00",
)
result = compute_cycle_time([issue])
assert result["mean_days"] == 2.0
```
