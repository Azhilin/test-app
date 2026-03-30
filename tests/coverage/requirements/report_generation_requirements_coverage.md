# Report Generation Requirements — Coverage Detail

> Source document: [docs/product/requirements/report_generation_requirements.md](../../../docs/product/requirements/report_generation_requirements.md)  
> Back to summary: [tests/coverage/test_coverage.md](../test_coverage.md)

**Total:** 33 | **✅ Covered:** 30 | **🔶 Partial:** 0 | **❌ Gap:** 0 | **⬜ N/T:** 3 | **Functional:** 100%


#### Filter Selection

| ID | Requirement | Status | Tests |
|----|-------------|--------|-------|
| RG-FS-001 | Generate tab shows a filter dropdown populated from saved filters | ✅ | `unit/test_filter_handlers.py::test_default_filter_entry_is_present_and_correct`, `component/test_server_filters.py::test_get_filters_default_is_first`, `e2e/test_e2e_filters.py::test_filter_list_displayed_on_load` |
| RG-FS-002 | Project Default Filter is the pre-selected option when a default filter exists | ✅ | `component/test_server_filters.py::test_get_filters_default_is_first`, `e2e/test_e2e_filters.py::test_filter_name_prepopulated_on_empty_load` |
| RG-FS-003 | Selected filter slug is passed to the /api/generate SSE endpoint | ✅ | `unit/test_filter_handlers.py::test_generate_applies_filter_params_to_subprocess_env`, `e2e/test_e2e_ui.py::test_generate_with_filter_sse_streaming` |

#### Project Type

| ID | Requirement | Status | Tests |
|----|-------------|--------|-------|
| RG-PT-001 | Generate tab shows SCRUM / KANBAN radio buttons | ✅ | `e2e/test_e2e_ui.py::test_project_type_radios_visible` |
| RG-PT-002 | SCRUM is the default project type | ✅ | `unit/test_config.py::test_project_type_default_scrum` |
| RG-PT-003 | Selected project type is sent to the generate endpoint | ✅ | `unit/test_filter_handlers.py::test_generate_applies_filter_params_to_subprocess_env` |
| RG-PT-004 | Project type selection persists across page reloads via localStorage | ✅ | `e2e/test_e2e_ui.py::test_project_type_persists_in_localstorage` |
| RG-PT-005 | Project type is included in the report header | ✅ | `component/test_report_html.py::test_project_type_shown_in_header`, `component/test_report_md.py::test_project_type_shown_in_md_header` |

#### Estimation Type

| ID | Requirement | Status | Tests |
|----|-------------|--------|-------|
| RG-ET-001 | Generate tab shows StoryPoints / JiraTickets radio buttons | ✅ | `e2e/test_e2e_ui.py::test_estimation_type_radios_visible` |
| RG-ET-002 | StoryPoints is the default estimation type | ✅ | `unit/test_config.py::test_estimation_type_default_story_points` |
| RG-ET-003 | Selected estimation type is sent to the generate endpoint | ✅ | `unit/test_filter_handlers.py::test_generate_applies_filter_params_to_subprocess_env` |
| RG-ET-004 | Estimation type selection persists across page reloads via localStorage | ✅ | `e2e/test_e2e_ui.py::test_estimation_type_persists_in_localstorage` |
| RG-ET-005 | Estimation type is included in the report header | ✅ | `component/test_report_html.py::test_estimation_type_shown_in_header`, `component/test_report_md.py::test_estimation_type_shown_in_md_header` |
| RG-ET-006 | When JiraTickets is selected, velocity uses issue count instead of story points | ✅ | `unit/test_metrics.py::test_build_metrics_dict_jira_tickets_velocity_uses_issue_count`, `unit/test_metrics.py::test_build_metrics_dict_story_points_velocity_unchanged` |
| RG-ET-007 | Report labels reflect estimation type | ✅ | `component/test_report_html.py::test_velocity_header_reflects_estimation_type_tickets`, `component/test_report_md.py::test_velocity_header_label_story_points`, `component/test_report_md.py::test_velocity_header_label_jira_tickets` |

#### Metric Toggles

| ID | Requirement | Status | Tests |
|----|-------------|--------|-------|
| RG-MT-001 | Generate tab shows 6 metric toggle checkboxes | ✅ | `e2e/test_e2e_ui.py::test_metric_toggle_checkboxes_visible` |
| RG-MT-002 | All metric toggles default to enabled | ✅ | `unit/test_config.py::test_metric_toggles_default_true` |
| RG-MT-003 | Disabled metrics are excluded from the generated report | ✅ | `component/test_report_html.py::test_velocity_section_hidden_when_section_visibility_false`, `component/test_report_html.py::test_ai_assistance_section_hidden_when_section_visibility_false`, `component/test_report_html.py::test_ai_usage_section_hidden_when_section_visibility_false`, `component/test_dau_report.py::test_html_dau_section_hidden_when_visibility_false` |
| RG-MT-004 | Metric toggle state is sent to the generate endpoint | ✅ | `unit/test_filter_handlers.py::test_generate_applies_filter_params_to_subprocess_env` |
| RG-MT-005 | Metric toggle state persists across page reloads via localStorage | ✅ | `e2e/test_e2e_ui.py::test_metric_toggles_persist_in_localstorage` |
| RG-MT-006 | At least one metric must be enabled to generate a report | ✅ | `e2e/test_e2e_ui.py::test_generate_button_disabled_when_all_metrics_unchecked` |

#### Report Output

| ID | Requirement | Status | Tests |
|----|-------------|--------|-------|
| RG-RO-001 | HTML report is generated and linked in the UI report list | ✅ | `component/test_report_html.py::test_file_created`, `component/test_server.py::test_generate_returns_sse_content_type`, `component/test_server.py::test_generate_ends_with_close_event` |
| RG-RO-002 | MD report is generated alongside the HTML report | ✅ | `component/test_report_md.py::test_file_created` |
| RG-RO-003 | Only HTML reports are linked in the UI | ✅ | `e2e/test_e2e_ui.py::test_reports_list_links_only_html` |
| RG-RO-004 | Section visibility in HTML matches metric toggle state | ✅ | `component/test_report_html.py::test_velocity_section_hidden_when_section_visibility_false`, `component/test_report_html.py::test_ai_assistance_section_hidden_when_section_visibility_false`, `component/test_report_html.py::test_ai_usage_section_hidden_when_section_visibility_false`, `component/test_dau_report.py::test_html_dau_section_hidden_when_visibility_false` |
| RG-RO-005 | Section visibility in MD matches metric toggle state | ✅ | `component/test_report_md.py::test_velocity_section_hidden_when_section_visibility_false`, `component/test_report_md.py::test_dau_section_hidden_when_section_visibility_false` |

#### Configuration

| ID | Requirement | Status | Tests |
|----|-------------|--------|-------|
| RG-CF-001 | PROJECT_TYPE env var controls default project type | ✅ | `unit/test_config.py::test_project_type_default_scrum`, `unit/test_config.py::test_project_type_kanban`, `unit/test_config.py::test_project_type_invalid_falls_back` |
| RG-CF-002 | ESTIMATION_TYPE env var controls default estimation type | ✅ | `unit/test_config.py::test_estimation_type_default_story_points`, `unit/test_config.py::test_estimation_type_jira_tickets`, `unit/test_config.py::test_estimation_type_invalid_falls_back` |
| RG-CF-003 | Individual METRIC_* env vars control metric inclusion | ✅ | `unit/test_config.py::test_metric_toggles_default_true`, `unit/test_config.py::test_metric_toggles_explicit_false` |
| RG-CF-004 | All new env vars have sensible defaults | ✅ | `unit/test_config.py::test_project_type_default_scrum`, `unit/test_config.py::test_estimation_type_default_story_points`, `unit/test_config.py::test_metric_toggles_default_true` |

#### Non-Functional Requirements

| ID | Requirement | Status | Tests |
|----|-------------|--------|-------|
| RG-NFR-001 | UI state persistence uses localStorage only | ⬜ | — |
| RG-NFR-002 | New parameters do not break existing filter overlay mechanism | ⬜ | `integration/test_integration.py::test_filter_metadata_in_html` |
| RG-NFR-003 | Report generation time is not significantly impacted by new controls | ⬜ | `component/test_report_performance.py::test_report_generation_completes_within_time_limit` |
