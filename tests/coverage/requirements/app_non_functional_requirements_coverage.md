# App Non Functional Requirements — Coverage Detail

> Source document: [docs/product/requirements/app_non_functional_requirements.md](../../../docs/product/requirements/app_non_functional_requirements.md)  
> Back to summary: [tests/coverage/test_coverage.md](../test_coverage.md)

**Total:** 33 | **✅ Covered:** 23 | **🔶 Partial:** 0 | **❌ Gap:** 0 | **⬜ N/T:** 10 | **Functional:** 100%


#### Performance

| ID | Requirement | Status | Tests |
|----|-------------|--------|-------|
| NFR-P-001 | Report generation completes within 60s for 10 sprints / 500 issues | ✅ | `component/test_report_performance.py::test_report_generation_completes_within_time_limit` |
| NFR-P-002 | HTML and Markdown reports generated in parallel via ThreadPoolExecutor | ✅ | `unit/test_cli.py::test_main_generates_reports_in_parallel` |
| NFR-P-003 | Jira connection test times out after no more than 12 seconds | ✅ | `unit/test_jira_client.py::test_create_client_passes_timeout` |
| NFR-P-004 | SSE events forwarded to browser within 1 second of stdout write | ⬜ | — |
| NFR-P-005 | Data fetch bounded: sprint count capped, issues paged, changelog limited | ✅ | `unit/test_jira_client.py::test_get_sprints_capped_at_sprint_count` |

#### Security

| ID | Requirement | Status | Tests |
|----|-------------|--------|-------|
| NFR-S-001 | API token always returned as *** in GET /api/config responses | ✅ | `test_server_config.py::TestGetConfig::test_token_always_masked_as_stars` |
| NFR-S-002 | Path traversal on /generated/reports/ rejected with HTTP 404 | ✅ | `unit/test_server_handlers.py::test_resolve_report_path_rejects_path_traversal` |
| NFR-S-003 | HTTP server binds exclusively to 127.0.0.1 by default | ✅ | `unit/test_server_handlers.py::test_run_defaults_host_to_loopback` |
| NFR-S-004 | Schema file requests restricted to safe filenames and .json extension | ✅ | `unit/test_server_handlers.py::test_get_schema_detail_rejects_path_traversal`, `unit/test_server_handlers.py::test_delete_schema_rejects_invalid_filename` |
| NFR-S-005 | .env and .env.backup-* listed in .gitignore, never committed | ⬜ | — |
| NFR-S-006 | Credentials not included in exception messages, CLI stderr, or SSE events | ✅ | `unit/test_jira_client.py::test_sanitise_error_replaces_url`, `unit/test_jira_client.py::test_sanitise_error_replaces_email_and_token`, `unit/test_jira_client.py::test_sanitise_error_handles_none_config_values` |

#### Usability

| ID | Requirement | Status | Tests |
|----|-------------|--------|-------|
| NFR-U-001 | Report generation progress displayed in real time without buffering | ⬜ | — |
| NFR-U-002 | Jira credentials pre-fill on next browser session after Save | ✅ | `e2e/test_e2e_connection.py::test_save_posts_correct_payload`, `e2e/test_e2e_connection.py::test_saved_credentials_prefill_on_reload` |
| NFR-U-003 | Generated HTML report is fully self-contained (inline CSS and data) | ✅ | `component/test_report_html.py` |
| NFR-U-004 | Past reports listed on Generate tab, sorted newest first with links | ✅ | `component/test_server.py::test_get_reports_returns_empty_list_when_no_reports`, `component/test_server.py::test_get_reports_returns_sorted_list` |
| NFR-U-005 | Connection failures and errors display human-readable messages in UI | ✅ | `unit/test_server_handlers.py::test_handle_generate_emits_error_event_for_nonzero_exit`, `unit/test_server_handlers.py::test_handle_generate_emits_error_when_main_file_missing` |

#### Reliability & Error Handling

| ID | Requirement | Status | Tests |
|----|-------------|--------|-------|
| NFR-R-001 | Missing required config detected before any Jira API call is made | ✅ | `unit/test_config.py::test_validate_config_all_set`, `unit/test_config.py::test_validate_config_missing_url`, `unit/test_config.py::test_validate_config_missing_email`, `unit/test_config.py::test_validate_config_missing_token`, `integration/test_integration.py::test_main_pipeline_config_fail` |
| NFR-R-002 | Jira connectivity failure reported as SSE error; server continues | ✅ | `component/test_server.py::test_test_connection_http_error`, `unit/test_server_handlers.py::test_handle_generate_emits_error_event_for_nonzero_exit` |
| NFR-R-003 | Client disconnect mid-stream caught and suppressed; no unhandled exception | ✅ | `unit/test_server_handlers.py::test_client_disconnect_tuple_includes_all_error_types`, `unit/test_server_handlers.py::test_serve_file_catches_client_disconnect`, `component/test_server.py::test_handle_error_swallows_connection_aborted_error` |
| NFR-R-004 | Changelog fetch failure for one issue skipped; full report still generated | ✅ | `unit/test_jira_client.py::test_get_issues_with_changelog_skips_failures` |
| NFR-R-005 | SSE stream always sends final event: close before connection ends | ✅ | `component/test_server.py::test_generate_ends_with_close_event` |

#### Data Privacy

| ID | Requirement | Status | Tests |
|----|-------------|--------|-------|
| NFR-D-001 | All credentials stored on local machine only; not sent to third parties | ⬜ | — |
| NFR-D-002 | DAU survey responses stored locally only; not sent externally | ⬜ | — |
| NFR-D-003 | No usage telemetry, analytics, or crash reporting sent anywhere | ⬜ | — |
| NFR-D-004 | Credential backup files (.env.backup-*) excluded from version control | ⬜ | — |

#### Compatibility

| ID | Requirement | Status | Tests |
|----|-------------|--------|-------|
| NFR-C-001 | All unit and component tests pass on Python 3.10, 3.11, and 3.12 | ⬜ | — |
| NFR-C-002 | Windows installation requires no administrator rights | ⬜ | — |
| NFR-C-003 | Browser UI functions correctly in Chrome/Edge/Firefox/Safari 90+/88+/14+ | ⬜ | — |
| NFR-C-004 | CLI and browser UI produce identical metric values from same data | ✅ | `unit/test_metrics.py::test_build_metrics_dict_is_deterministic` |

#### Accessibility

| ID | Requirement | Status | Tests |
|----|-------------|--------|-------|
| NFR-A-001 | All interactive UI regions carry correct ARIA role attributes | ✅ | `e2e/test_e2e_ui.py::test_keyboard_arrow_right_navigation` |
| NFR-A-002 | Dynamic content updates use aria-live='polite' for screen readers | ✅ | `e2e/test_e2e_ui.py::test_dynamic_regions_have_aria_live` |
| NFR-A-003 | Required form fields carry aria-required='true' | ✅ | `e2e/test_e2e_ui.py::test_required_fields_have_aria_required` |
| NFR-A-004 | Decorative UI elements carry aria-hidden='true' | ✅ | `e2e/test_e2e_ui.py::test_decorative_icons_have_aria_hidden` |
