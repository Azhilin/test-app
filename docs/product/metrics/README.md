# Metrics Reference

This folder contains documentation for every metric produced by the AI Adoption Metrics Report tool.
Each file describes the metric's purpose, the Jira data it needs, how it is calculated, and how to
interpret the results — written for both product users and developers/AI Copilots.

## Available Metrics

| Metric | Short description | HTML report | MD report |
|---|---|:---:|:---:|
| [Velocity](velocity.md) | Completed story points per sprint | yes | yes |
| [Cycle Time](cycle_time.md) | Average days from start to done per issue | yes | yes |
| [AI Assistance Trend](ai_assistance_trend.md) | % of completed work that was AI-assisted, per sprint | yes | planned |
| [AI Usage Details](ai_usage_details.md) | Breakdown of AI tools and use-cases across all AI-assisted issues | yes | planned |
| [Custom Trends](custom_trends.md) | Extension point for team-specific metrics | yes | yes |

> **MD report gap:** AI Assistance Trend and AI Usage Details are currently rendered only in the HTML
> report. They are computed and available in the `metrics_dict`; adding them to the Markdown report
> is a straightforward extension — see each metric's *Developer / AI Copilot Notes* section.

## Jira Fields Reference

The table below lists every Jira field defined in the schema. Field IDs can be customised
per Jira instance via `config/jira_schema.json` (see the *Jira Field Schema* card in the UI).
Custom fields are auto-detected when you use the UI's *Fetch Schema* feature.

Fields marked **active** are currently read by the metrics engine. Fields marked **available**
are in the schema and returned by Jira's default API response, ready for use in custom metrics
or future built-in metrics.

### Currently active fields

| Logical key | Default Jira field ID | Type | Used by |
|---|---|---|---|
| `story_points` | `customfield_10016` | number | Velocity, AI Assistance Trend |
| `status` | `status` | string | Velocity, Cycle Time (changelog), AI metrics (done filter) |
| `labels` | `labels` | array | AI Assistance Trend, AI Usage Details |
| `sprint` | `customfield_10020` | array | All metrics (sprint grouping) |
| Changelog histories | _(expand parameter)_ | event log | Cycle Time |

### Available for custom metrics and future built-in metrics

| Logical key | Default Jira field ID | Type | Auto-detected | Recommended use |
|---|---|---|:---:|---|
| `epic_link` | `customfield_10014` | string | yes | Group velocity/cycle time by epic |
| `epic_name` | `customfield_10011` | string | yes | Epic label in reports |
| `team` | `customfield_10001` | string | yes | Per-team velocity breakdown; also used by the UI filter |
| `priority` | `priority` | string | n/a (standard) | Priority distribution across sprints |
| `labels` | `labels` | array | n/a (standard) | Already used by AI metrics; also available for custom categorisation |
| `issue_type` | `issuetype` | string | n/a (standard) | Bug rate, story vs task split |
| `resolution` | `resolution` | object | n/a (standard) | Resolution category breakdown; use `resolution_date` for timing |
| `assignee` | `assignee` | object | n/a (standard) | Per-assignee velocity or cycle-time breakdown |
| `components` | `components` | array | n/a (standard) | Component-level delivery trends |
| `fix_version` | `fixVersions` | array | n/a (standard) | Release-based delivery metrics |
| `parent` | `parent` | object | n/a (standard) | Epic rollup for Next-gen (team-managed) projects |
| `due_date` | `duedate` | string | n/a (standard) | Deadline adherence tracking |
| `resolution_date` | `resolutiondate` | string | n/a (standard) | Reliable done-timestamp for cycle time (alternative to changelog) |
| `start_date` | `customfield_10015` | string | yes | Issue-level start date for time-in-progress calculation |

> **Note on `start_date`:** The default ID `customfield_10015` is the most common Jira Cloud
> value but varies by instance. Always verify with the UI's *Fetch Schema* auto-detect or check
> your Jira field list at `https://<your-domain>.atlassian.net/rest/api/2/field`.
>
> **Note on `resolution_date`:** This standard field is populated by Jira automatically when
> an issue transitions to a resolved status. It can serve as a more reliable "done at" timestamp
> than parsing status-change events in the changelog.

## Configuration Quick Reference

| Environment variable | Default | Purpose |
|---|---|---|
| `JIRA_SCHEMA_NAME` | _(unset)_ | CLI-only fallback (`python main.py`); which schema entry in `config/jira_schema.json` to use. UI runs use the active filter's `params.schema_name` from `config/jira_filters.json`, which overrides this env var via `/api/generate`. |
| `JIRA_SPRINT_COUNT` | `10` | Number of past sprints to include |
| `AI_ASSISTED_LABEL` | `AI_assistance` | Label that marks an issue as AI-assisted |
| `AI_EXCLUDE_LABELS` | _(empty)_ | Issues with these labels are excluded from the AI % denominator |
| `AI_TOOL_LABELS` | _(empty)_ | Labels identifying AI tools (e.g. `AI_Tool_Copilot`) |
| `AI_ACTION_LABELS` | _(empty)_ | Labels identifying AI use-cases (e.g. `AI_Case_CodeGen`) |

Full configuration reference: [`.env.example`](../../../.env.example)
