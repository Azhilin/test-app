# AI Usage Details

## Purpose

AI Usage Details provides a breakdown of *how* AI tools are being used across all
AI-assisted completed issues. Where the AI Assistance Trend metric answers *"how much
AI work is happening?"*, this metric answers *"which tools are being used and for what
purposes?"*

It aggregates Jira label counts across all done AI-assisted issues to produce two
breakdowns:

- **Tool breakdown** — which AI tools (e.g. GitHub Copilot, ChatGPT, Gemini) are being
  used and in what proportion.
- **Action/use-case breakdown** — which types of AI activity (e.g. code generation, code
  review, test writing) account for the most usage.

This metric enables teams and managers to make informed decisions about tool subscriptions,
training priorities, and adoption strategies.

## Use Cases

- **Tool adoption audit** — understand which AI tools your team actually uses vs. which
  licences you pay for.
- **Use-case discovery** — identify the most common AI use-cases to focus training and
  documentation efforts.
- **ROI analysis** — if code-generation issues have shorter cycle times, quantify the
  value of that specific use-case.
- **Portfolio review** — present breakdown charts to leadership as evidence of AI programme
  breadth, not just volume.
- **Identifying gaps** — if "AI_Case_Testing" is almost never used, investigate whether
  teams lack awareness or tooling for AI-assisted testing.
- **Trend over time** — run reports periodically and compare breakdowns to see whether
  usage patterns are maturing (e.g. moving from simple generation towards code review
  and refactoring).

## Report Availability

| Report format | Available |
|---|---|
| HTML report | yes — two pie charts (tool breakdown + action breakdown) |
| Markdown report | **not yet rendered** — data is computed and present in `metrics_dict`; rendering is planned |

> The computed data is available at `metrics["ai_usage_details"]` after every report run.
> Adding it to the Markdown report requires a new section in `app/reporters/report_md.py`.
> See the *Developer / AI Copilot Notes* section below for exact steps.

## Required Jira Fields

| Logical key | Default Jira field ID | Type | Notes |
|---|---|---|---|
| `labels` | `labels` | array | Tool and action labels must be present; `AI_ASSISTED_LABEL` must also be present for an issue to be counted |
| `status` | `status` | string | Used to identify done issues |
| `sprint` | `customfield_10020` | array | Groups issues by sprint (for done-issue filtering) |

## Required Configuration

| Variable | Default | Effect |
|---|---|---|
| `AI_ASSISTED_LABEL` | `AI_assistance` | An issue must carry this label to be included in the breakdown sample |
| `AI_TOOL_LABELS` | _(empty)_ | Comma-separated labels identifying AI tools. Example: `AI_Tool_Copilot,AI_Tool_ChatGPT,AI_Tool_Gemini` |
| `AI_ACTION_LABELS` | _(empty)_ | Comma-separated labels identifying AI use-cases. Example: `AI_Case_CodeGen,AI_Case_Review,AI_Case_Testing` |

> If `AI_TOOL_LABELS` or `AI_ACTION_LABELS` are empty, the corresponding breakdown will be
> an empty list and the pie chart will not render. You must configure these variables to
> see tool/action breakdowns.

**Example `.env` configuration:**
```
AI_ASSISTED_LABEL=AI_assistance
AI_TOOL_LABELS=AI_Tool_Copilot,AI_Tool_ChatGPT,AI_Tool_Gemini,AI_Tool_Cursor
AI_ACTION_LABELS=AI_Case_CodeGen,AI_Case_Review,AI_Case_Testing,AI_Case_Docs,AI_Case_Refactor
```

## Calculation

1. **Collect all done AI-assisted issues** — across all fetched sprints, collect every unique
   done issue (by `key`) that carries the `AI_ASSISTED_LABEL` label. Duplicate issue keys
   are deduplicated; each issue is counted once regardless of how many sprints it appears in.
2. **Count total AI-assisted issues** — `ai_assisted_issue_count = len(ai_issues)`.
3. **Tool breakdown** — for each label in `AI_TOOL_LABELS`, count how many AI-assisted issues
   carry that label. Compute percentage relative to `ai_assisted_issue_count`.
4. **Action breakdown** — same process for `AI_ACTION_LABELS`.
5. **Sort** — each breakdown is sorted descending by count.
6. **Exclude zero-count labels** — labels with no matching issues are omitted from the output.

**Formula (per label):**
```
count(label) = number of AI-assisted done issues that have `label` in their labels list
pct(label)   = count(label) / ai_assisted_issue_count × 100
```

> An issue can match multiple tool or action labels simultaneously. Percentages can therefore
> sum to more than 100% — this is intentional and expected when a developer uses more than
> one tool on a single issue.

## Recommendations

- **Define a labelling convention before rollout** — agree on exact label names (case matters
  in Jira) and communicate them to all team members. A label taxonomy document or Jira label
  picklist reduces noise.
- **Use consistent prefixes** — prefixing tool labels with `AI_Tool_` and action labels with
  `AI_Case_` makes them visually distinct in Jira and easy to configure via `AI_TOOL_LABELS`
  and `AI_ACTION_LABELS`.
- **Limit the number of labels** — 3–6 tool labels and 4–8 action labels is a good range.
  Too many labels creates overhead and fragmented pie charts.
- **Interpret "no data" correctly** — if `ai_assisted_issue_count` is 0 but AI Assistance
  Trend shows a non-zero percentage, check that the `AI_ASSISTED_LABEL` value in `.env`
  exactly matches the Jira label (including capitalisation and underscores).
- **Review unknown tool usage** — if the "Other" slice in your mental model is large (many
  AI-assisted issues don't match any tool label), survey the team to discover unconfigured
  tools.
- **Use the action breakdown for training ROI** — if `AI_Case_Testing` is low despite
  available tooling, invest in a short hands-on session. The metric gives you a baseline
  to measure the impact.

## Developer / AI Copilot Notes

**Module:** `app/core/metrics.py`

**Primary function:**
```python
def compute_ai_usage_details(
    sprints: list[dict],
    sprint_issues: dict[int, list[dict]],
    ai_assisted_label: str | None = None,      # defaults to config.AI_ASSISTED_LABEL
    ai_tool_labels: list[str] | None = None,   # defaults to config.AI_TOOL_LABELS
    ai_action_labels: list[str] | None = None, # defaults to config.AI_ACTION_LABELS
    done_statuses: frozenset[str] | None = None,
) -> dict:
    ...
```

**Output shape:**
```python
{
    "ai_assisted_issue_count": int,
    "tool_breakdown": [
        {"label": str, "count": int, "pct": float},  # sorted desc by count
        # ... one entry per matched AI_TOOL_LABELS label
    ],
    "action_breakdown": [
        {"label": str, "count": int, "pct": float},  # sorted desc by count
        # ... one entry per matched AI_ACTION_LABELS label
    ],
}
```

**Location in `metrics_dict`:** `metrics["ai_usage_details"]` — a single dict.

**Adding to the Markdown report** (`app/reporters/report_md.py`):

Add a new section after the AI Assistance Trend block (or cycle time if trend is not yet added):

```python
ai_usage = metrics.get("ai_usage_details") or {}
total = ai_usage.get("ai_assisted_issue_count", 0)
if total > 0:
    parts.append("## AI Usage Details")
    parts.append("")
    parts.append(f"Total AI-assisted issues: **{total}**")
    parts.append("")
    tool_bd = ai_usage.get("tool_breakdown") or []
    if tool_bd:
        parts.append("### By Tool")
        parts.append("")
        parts.append(_md_table(
            ["Tool label", "Issues", "%"],
            [[r["label"], r["count"], f"{r['pct']}%"] for r in tool_bd],
        ))
        parts.append("")
    action_bd = ai_usage.get("action_breakdown") or []
    if action_bd:
        parts.append("### By Use Case")
        parts.append("")
        parts.append(_md_table(
            ["Use-case label", "Issues", "%"],
            [[r["label"], r["count"], f"{r['pct']}%"] for r in action_bd],
        ))
        parts.append("")
```

**Test factory:**
```python
from tests.conftest import make_sprint, make_issue
from app.core.metrics import compute_ai_usage_details

sprint = make_sprint(1, name="Sprint 1")
issue1 = make_issue("PROJ-1", status="Done", points=5)
issue1["fields"]["labels"] = ["AI_assistance", "AI_Tool_Copilot", "AI_Case_CodeGen"]
issue2 = make_issue("PROJ-2", status="Done", points=3)
issue2["fields"]["labels"] = ["AI_assistance", "AI_Tool_ChatGPT", "AI_Case_Review"]

result = compute_ai_usage_details(
    [sprint],
    {1: [issue1, issue2]},
    ai_tool_labels=["AI_Tool_Copilot", "AI_Tool_ChatGPT"],
    ai_action_labels=["AI_Case_CodeGen", "AI_Case_Review"],
)
assert result["ai_assisted_issue_count"] == 2
assert result["tool_breakdown"][0]["label"] in ("AI_Tool_Copilot", "AI_Tool_ChatGPT")
```
