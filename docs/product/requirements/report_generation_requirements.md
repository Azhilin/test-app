# Report Generation Requirements — AI Adoption Metrics Report

This document defines the functional and non-functional requirements for the
Generate Report tab, including filter selection, project type, estimation type,
metric toggles, and report output.

---

## Table of Contents

1. [Filter Selection](#1-filter-selection)
2. [Project Type](#2-project-type)
3. [Estimation Type](#3-estimation-type)
4. [Metric Toggles](#4-metric-toggles)
5. [Report Output](#5-report-output)
6. [Configuration](#6-configuration)
7. [Non-Functional Requirements](#7-non-functional-requirements)

---

## 1. Filter Selection

| ID | Requirement | Acceptance Criterion | Status |
|----|-------------|----------------------|--------|
| RG-FS-001 | Generate tab shows a filter dropdown populated from saved filters | Dropdown lists all entries from `jira_filters.json`; the default filter is pre-selected on load | ✓ Met |
| RG-FS-002 | "Project Default Filter" is the pre-selected option when a default filter exists | On page load, the filter marked `is_default: true` is selected in the dropdown | ✓ Met |
| RG-FS-003 | Selected filter slug is passed to the `/api/generate` SSE endpoint | The generate request includes `?filter=<slug>` matching the selected dropdown value | ✓ Met |

## 2. Project Type

| ID | Requirement | Acceptance Criterion | Status |
|----|-------------|----------------------|--------|
| RG-PT-001 | Generate tab shows SCRUM / KANBAN radio buttons | Two radio buttons labeled "Scrum" and "Kanban" are visible in the Generate tab | ✓ Met |
| RG-PT-002 | SCRUM is the default project type | On page load (no localStorage override), the Scrum radio is selected | ✓ Met |
| RG-PT-003 | Selected project type is sent to the generate endpoint | The generate request includes `project_type=SCRUM` or `project_type=KANBAN` as a query parameter | ✓ Met |
| RG-PT-004 | Project type selection persists across page reloads via localStorage | After selecting Kanban and reloading, the Kanban radio is still selected | ✓ Met |
| RG-PT-005 | Project type is included in the report header | Both HTML and MD reports display the project type (e.g. "Project Type: Scrum") | ✓ Met |

## 3. Estimation Type

| ID | Requirement | Acceptance Criterion | Status |
|----|-------------|----------------------|--------|
| RG-ET-001 | Generate tab shows StoryPoints / JiraTickets radio buttons | Two radio buttons labeled "Story Points" and "Jira Tickets" are visible | ✓ Met |
| RG-ET-002 | StoryPoints is the default estimation type | On page load (no localStorage override), Story Points radio is selected | ✓ Met |
| RG-ET-003 | Selected estimation type is sent to the generate endpoint | The generate request includes `estimation_type=StoryPoints` or `estimation_type=JiraTickets` | ✓ Met |
| RG-ET-004 | Estimation type selection persists across page reloads via localStorage | After selecting Jira Tickets and reloading, it remains selected | ✓ Met |
| RG-ET-005 | Estimation type is included in the report header | Both HTML and MD reports display the estimation type | ✓ Met |
| RG-ET-006 | When JiraTickets is selected, velocity uses issue count instead of story points | Velocity rows show count of done issues instead of summed story points | ✓ Met |
| RG-ET-007 | Report labels reflect estimation type | Column headers read "Velocity (points)" or "Velocity (issues)" depending on estimation type | ✓ Met |

## 4. Metric Toggles

| ID | Requirement | Acceptance Criterion | Status |
|----|-------------|----------------------|--------|
| RG-MT-001 | Generate tab shows 4 metric toggle checkboxes | Checkboxes for: Velocity Trend, AI Assistance Trend, AI Usage Details, DAU | ✓ Met |
| RG-MT-002 | All metric toggles default to enabled | On first load (no localStorage), all 4 checkboxes are checked | ✓ Met |
| RG-MT-003 | Disabled metrics are excluded from the generated report | Unchecking "Velocity Trend" removes the velocity section from HTML and MD output | ✓ Met |
| RG-MT-004 | Metric toggle state is sent to the generate endpoint | The generate request includes boolean parameters for each metric (e.g. `metric_velocity=true`) | ✓ Met |
| RG-MT-005 | Metric toggle state persists across page reloads via localStorage | After unchecking DAU and reloading, DAU remains unchecked | ✓ Met |
| RG-MT-006 | At least one metric must be enabled to generate a report | The Generate button is disabled when all 4 checkboxes are unchecked | ✓ Met |

## 5. Report Output

| ID | Requirement | Acceptance Criterion | Status |
|----|-------------|----------------------|--------|
| RG-RO-001 | HTML report is generated and linked in the UI report list | After generation, the reports list shows a clickable link to the HTML report | ✓ Met |
| RG-RO-002 | MD report is generated alongside the HTML report | Both `report.html` and `report.md` are created in the timestamped output folder | ✓ Met |
| RG-RO-003 | Only HTML reports are linked in the UI | The reports list shows HTML links only; MD files are not displayed to the user | ✓ Met |
| RG-RO-004 | Section visibility in HTML matches metric toggle state | Disabled metrics produce no section in the HTML report | ✓ Met |
| RG-RO-005 | Section visibility in MD matches metric toggle state | Disabled metrics produce no section in the MD report | ✓ Met |

## 6. Configuration

| ID | Requirement | Acceptance Criterion | Status |
|----|-------------|----------------------|--------|
| RG-CF-001 | `PROJECT_TYPE` env var controls default project type | Setting `PROJECT_TYPE=KANBAN` in `.env` causes Kanban to be pre-selected in UI and used by CLI | ✓ Met |
| RG-CF-002 | `ESTIMATION_TYPE` env var controls default estimation type | Setting `ESTIMATION_TYPE=JiraTickets` in `.env` causes Jira Tickets to be pre-selected and used by CLI | ✓ Met |
| RG-CF-003 | Individual `METRIC_*` env vars control metric inclusion | Setting `METRIC_VELOCITY=false` excludes velocity from CLI-generated reports | ✓ Met |
| RG-CF-004 | All new env vars have sensible defaults | Without any `.env` changes, behavior matches current defaults: SCRUM, StoryPoints, all metrics on | ✓ Met |

## 7. Non-Functional Requirements

| ID | Requirement | Acceptance Criterion | Status |
|----|-------------|----------------------|--------|
| RG-NFR-001 | UI state persistence uses localStorage only | No server-side session storage; all UI selections are persisted client-side | ✓ Met |
| RG-NFR-002 | New parameters do not break existing filter overlay mechanism | Existing filter slug handling continues to work alongside new parameters | ✓ Met |
| RG-NFR-003 | Report generation time is not significantly impacted by new controls | Adding project type / estimation type / metric toggles does not add perceptible latency | ✓ Met |
