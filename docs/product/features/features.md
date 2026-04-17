# Features — AI Adoption Metrics Report

User-visible features of the browser UI and generated reports. Update this file whenever a
tab, control, or report section is added, changed, or removed.

---

## Browser UI

The UI is a single-page application served by `app/server/` at `http://localhost:8080`.
It is the primary interface for configuring credentials, managing filters, and generating reports.

### Tabs

| Tab | ID | Default |
|-----|----|---------|
| Generate Report | `panel-generate` | yes (opens on load) |
| Filter Builder | `panel-filter` | — |
| Jira Connection | `panel-connection` | — |
| Jira Field Schema | `panel-schema` | — |

---

### Generate Report tab

The main workflow tab. Triggers report generation and displays live output.

#### Controls

| Control | Description |
|---------|-------------|
| **Saved Filter** dropdown | Selects the JQL filter used to scope sprint issues. Populated from `config/jira_filters.json`. Required — the Generate button stays disabled until a filter is selected. |
| **Report Name** field | Optional free-text name for the generated report. Auto-fills from the selected filter's `report_name` when a filter is chosen. When changed and the report is generated, the new value is saved back to the filter in `config/jira_filters.json`, used as the report `<h1>` / `# ` heading, and as the output filename stem (slugified). |
| **Generate Report** button | Runs `python main.py` on the server and streams stdout/stderr as Server-Sent Events into the output panel. |
| **Report Options** (collapsible) | Expands to reveal per-run configuration. |

#### Report Options panel

| Option | Values | Default | Persisted |
|--------|--------|---------|-----------|
| **Project Type** radio | Scrum / Kanban | Scrum | `localStorage` |
| **Estimation Type** radio | Story Points / Jira Tickets | Story Points | `localStorage` |
| **Metric Sections** checkboxes | Velocity Trend, AI Assistance Trend, AI Usage Details, DAU Survey, DAU Trend | all enabled | `localStorage` |

At least one metric section must be enabled; the Generate button is disabled when all are unchecked.

#### AI Adoption Labels card

Inline configuration for the Jira labels used by AI metrics. Changes are saved to `.env` via
`POST /api/config`.

| Field | Env var | Description |
|-------|---------|-------------|
| AI Assisted Label | `AI_ASSISTED_LABEL` | Label that marks an issue as AI-assisted (default: `AI_assistance`) |
| Exclude Labels | `AI_EXCLUDE_LABELS` | Comma-separated labels excluded from the AI % denominator |
| Tool Labels | `AI_TOOL_LABELS` | Labels identifying AI tools (e.g. `AI_Tool_Copilot,AI_Tool_ChatGPT`) |
| Action Labels | `AI_ACTION_LABELS` | Labels identifying AI use-cases (e.g. `AI_Case_CodeGen,AI_Case_Review`) |

#### Output panel

Live SSE output from the generation subprocess. Displays each stdout/stderr line as it is
produced. Shows a success or error banner on completion.

#### Last Generated Reports list

Lists all previously generated reports under `generated/reports/`, sorted newest first.
Each entry is a clickable link to the corresponding `report.html`.

---

### Filter Builder tab

Create and manage named JQL filters that scope which Jira issues are included in a report.
Filters are stored in `config/jira_filters.json` and appear in the Generate Report dropdown.
Each filter is the source of truth for which Jira field schema (`params.schema_name`) the
report pipeline uses when that filter is run.

| Feature | Description |
|---------|-------------|
| **Active Schema** dropdown | Populated from `/api/schemas`. Chosen value is saved on the filter as `params.schema_name` and is what the pipeline reads when generating a report. Independent of the Schema Setup tab. |
| **Filter Name** dropdown | Lists `— New filter —` plus every saved filter (the default is tagged `(default)`). Picking a filter loads its params into the form for in-place editing; picking `— New filter —` clears the form and reveals a text input pre-populated with `Default_Jira_Filter_<YYYY-MM-DD>`. |
| **Report Name** field | Optional text input for the report title/filename. Auto-fills from the filter name when a filter is selected or the filter name is typed. Saved alongside the filter as `report_name` in `config/jira_filters.json`. |
| Filter form | Project Key, optional Team ID, Issue Types, Closed-sprints-only, Project Type, Estimation Type, Board ID, Sprint Count, optional Jira Filter ID & page size |
| Save button | Upserts the filter by name via `POST /api/filters`; disabled while `Default_Jira_Filter` is selected (the default is read-only) |
| Filter list | All saved filters, default first; non-default entries show a Remove button |
| Default filter protection | The default filter cannot be deleted or overwritten via the UI |

---

### Jira Connection tab

Configures and verifies the Jira Cloud connection. Settings are saved to `.env` via
`POST /api/config`.

| Section | Controls |
|---------|----------|
| **Credentials** | Jira URL, Jira Email, API Token (masked); Save and Test Connection buttons |
| **Sprint Settings** | Board ID (optional), Sprint Count; saved to `config/defaults.env` |
| **SSL Certificate** | Certificate status badge (Valid / Expired / No certificate); Fetch Certificate and Remove Certificate buttons |

The **Test Connection** button proxies a credential check to `JIRA_URL/rest/api/3/myself`
with a 12-second timeout and reports success or HTTP error status.

---

### Schema Setup tab

Manages the Jira field schema used to locate story-points, sprint, team, and status fields
on each Jira instance. Schemas are stored in `config/jira_schema.json`; the tab sits between
**Jira Connection** and **Filter Builder**.

| Feature | Description |
|---------|-------------|
| Schema dropdown | Lists every schema from `config/jira_schema.json`; `Default_Jira_Cloud` is always present and selected by default |
| JSON editor | Full schema body is shown as pretty-printed JSON in a textarea; all fields (`schema_name`, `description`, `fields`, `status_mapping`, ...) are editable in one place |
| New Schema | Loads a blank template into the editor; user sets `schema_name` directly in the JSON body before saving |
| Save | Upserts the schema by `schema_name` via `POST /api/schemas`; client-side JSON validation blocks malformed bodies before the request is sent |
| Delete | Removes any non-default schema entry; disabled while `Default_Jira_Cloud` is selected |
| Active schema selection | The Schema Setup tab is an editor and does not select the schema used for metrics. The active schema for a report run is determined by the selected filter's `params.schema_name` in `config/jira_filters.json`; for CLI-only runs, `JIRA_SCHEMA_NAME` in `.env` / `config/defaults.env` is used as a fallback. |

---

## Generated Reports

Each `python main.py` run writes to `generated/reports/<YYYY-MM-DDTHH-MM-SS>/`:

| File | Format | Description |
|------|--------|-------------|
| `report.html` | HTML | Self-contained, fully inline (CSS + Chart.js + data). Opens in any browser without a server. |
| `report.md` | Markdown | Plain-text summary with ASCII bar charts and tables. |

### Report sections

Each section can be independently toggled via the **Metric Sections** checkboxes in the UI
(or via `METRIC_*` env vars for CLI runs).

| Section | Toggle | HTML | Markdown | Description |
|---------|--------|------|----------|-------------|
| **Velocity Trend** (or **Throughput Trend** for Kanban) | `METRIC_VELOCITY` | bar chart + running-average line | ASCII bar chart + table | Story points (or issue count) of done issues per sprint |
| **AI Assistance Trend** | `METRIC_AI_TREND` | line chart + per-sprint table | table | Per-sprint % of done story points carrying the AI-assisted label |
| **AI Usage Details** | `METRIC_AI_USAGE` | two donut/bar charts (tools + use-cases) | tables | Breakdown of AI tool labels and AI use-case labels across AI-assisted issues |
| **DAU Survey** | `METRIC_DAU` | team-average card + by-role table + usage-frequency bar chart | summary + by-role table | Team Daily Active Usage average from self-reported survey data |
| **DAU Trend** | `METRIC_DAU_TREND` | combo bar+line chart (avg days + adoption %) | ASCII bar chart + table | Week-over-week DAU average and adoption percentage |

### Label adaptation

Report column headers and chart labels adapt to the selected **Project Type** and
**Estimation Type**:

| Project Type | Velocity section title | Period column |
|---|---|---|
| Scrum | Velocity trend | Sprint |
| Kanban | Throughput trend | Period |

| Estimation Type | Velocity unit label |
|---|---|
| Story Points | points |
| Jira Tickets | issues (count of done issues) |
