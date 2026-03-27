# Dau Survey Requirements — Coverage Detail

> Source document: [docs/product/requirements/dau_survey_requirements.md](../../../docs/product/requirements/dau_survey_requirements.md)  
> Back to summary: [tests/coverage/test_coverage.md](../test_coverage.md)

**Total:** 31 | **✅ Covered:** 26 | **🔶 Partial:** 0 | **❌ Gap:** 3 | **⬜ N/T:** 2 | **Functional:** 90%


#### Survey UI

| ID | Requirement | Status | Tests |
|----|-------------|--------|-------|
| DAU-F-001 | Username is a required text field | ✅ | `e2e/test_dau_survey_ui.py::test_submit_button_initially_disabled`, `e2e/test_dau_survey_ui.py::test_submit_enabled_only_when_all_fields_are_valid` |
| DAU-F-002 | Username accepts only alphanumeric characters, minimum 2 characters | ✅ | `e2e/test_dau_survey_ui.py::test_username_rejects_underscore`, `e2e/test_dau_survey_ui.py::test_username_rejects_space`, `e2e/test_dau_survey_ui.py::test_username_too_short_shows_error`, `e2e/test_dau_survey_ui.py::test_username_valid_input_applies_valid_class` |
| DAU-F-003 | Username is persisted across sessions via localStorage | ✅ | `e2e/test_dau_survey_ui.py::test_username_saved_to_localstorage_after_submit`, `e2e/test_dau_survey_ui.py::test_username_restored_from_localstorage_on_page_load` |
| DAU-F-004 | Role is a required dropdown with exactly 5 options | ✅ | `e2e/test_dau_survey_ui.py::test_submit_enabled_only_when_all_fields_are_valid`, `e2e/test_dau_survey_ui.py::test_confirmation_displays_submitted_data` |
| DAU-F-005 | Usage frequency is a required radio selection with exactly 4 options | ✅ | `e2e/test_dau_survey_ui.py::test_radio_card_click_marks_it_selected`, `e2e/test_dau_survey_ui.py::test_submit_enabled_only_when_all_fields_are_valid` |
| DAU-F-006 | Progress bar reflects number of completed fields out of 3 | ✅ | `e2e/test_dau_survey_ui.py::test_progress_starts_at_zero`, `e2e/test_dau_survey_ui.py::test_progress_increments_with_each_field` |
| DAU-F-007 | Submit button is disabled until all 3 fields are valid | ✅ | `e2e/test_dau_survey_ui.py::test_submit_button_initially_disabled`, `e2e/test_dau_survey_ui.py::test_submit_enabled_only_when_all_fields_are_valid` |
| DAU-F-008 | Confirmation screen is shown after a successful save | ✅ | `e2e/test_dau_survey_ui.py::test_submit_hides_form_and_shows_confirmation`, `e2e/test_dau_survey_ui.py::test_confirmation_displays_submitted_data` |
| DAU-F-009 | Keyboard navigation works within the radio group | ✅ | `e2e/test_dau_survey_ui.py::test_radio_card_keyboard_navigation` |

#### Submission and Storage

| ID | Requirement | Status | Tests |
|----|-------------|--------|-------|
| DAU-F-010 | Survey data is saved via the File System Access API when supported | ✅ | `e2e/test_dau_survey_ui.py::test_submit_writes_valid_json_to_mocked_fs` |
| DAU-F-011 | Survey data falls back to a browser download when the FS API is unavailable | ✅ | `e2e/test_dau_survey_ui.py::test_fs_api_unavailable_falls_back_to_download` |
| DAU-F-012 | If the FS API directory picker is cancelled, the form remains intact | ✅ | `e2e/test_dau_survey_ui.py::test_fs_api_abort_keeps_form_intact` |
| DAU-F-013 | If the FS API call fails for a non-cancel reason, the app falls back to download | ✅ | `e2e/test_dau_survey_ui.py::test_fs_api_non_abort_error_falls_back_to_download` |
| DAU-F-014 | Output filename encodes the respondent and submission time | ✅ | `e2e/test_dau_survey_ui.py::test_filename_matches_dau_username_timestamp_pattern` |
| DAU-F-015 | Submission payload matches the defined schema | ✅ | `e2e/test_dau_survey_ui.py::test_submit_writes_valid_json_to_mocked_fs`, `e2e/test_dau_survey_ui.py::test_submit_timestamp_format`, `e2e/test_dau_survey_ui.py::test_submit_week_field_format` |
| DAU-F-016 | Response files are saved to generated/ by default | ❌ | — |

#### Metrics Computation

| ID | Requirement | Status | Tests |
|----|-------------|--------|-------|
| DAU-F-017 | compute_dau_metrics() reads all dau_*.json files from the given directory | ✅ | `unit/test_dau_metrics.py::test_empty_dir_returns_zero_count`, `unit/test_dau_metrics.py::test_missing_dir_returns_zero_count`, `unit/test_dau_metrics.py::test_three_response_files_counted`, `unit/test_dau_metrics.py::test_non_dau_files_are_ignored`, `unit/test_dau_metrics.py::test_malformed_json_file_is_skipped` |
| DAU-F-018 | compute_dau_metrics maps each usage answer to its score and computes the team... | ✅ | `unit/test_dau_metrics.py::test_mixed_scores_correct_avg`, `unit/test_dau_metrics.py::test_all_not_used_avg_is_zero`, `unit/test_dau_metrics.py::test_unknown_usage_falls_back_to_zero` |
| DAU-F-019 | compute_dau_metrics returns a by_role list with per-role averages and counts | ✅ | `unit/test_dau_metrics.py::test_by_role_sorted_alphabetically`, `unit/test_dau_metrics.py::test_by_role_correct_avg_and_count` |
| DAU-F-020 | compute_dau_metrics returns a breakdown list with per-answer counts | ✅ | `unit/test_dau_metrics.py::test_breakdown_sorted_descending_by_count` |
| DAU-F-021 | build_metrics_dict() includes a dau key | ✅ | `unit/test_dau_metrics.py::test_build_metrics_dict_includes_dau_key` |
| DAU-F-022 | The responses directory is configurable via DAU_RESPONSES_DIR environment var... | ✅ | `unit/test_dau_metrics.py::test_dau_responses_dir_env_var_overrides_default` |

#### Report Rendering

| ID | Requirement | Status | Tests |
|----|-------------|--------|-------|
| DAU-F-023 | The HTML report includes a DAU section | ✅ | `component/test_dau_report.py::test_html_has_dau_section_when_data_present`, `component/test_dau_report.py::test_html_dau_shows_team_avg` |
| DAU-F-024 | The HTML report DAU section is omitted when there are no responses | ✅ | `component/test_dau_report.py::test_html_dau_section_absent_when_no_responses`, `component/test_dau_report.py::test_html_dau_section_hidden_when_visibility_false` |
| DAU-F-025 | The Markdown report includes a ## Daily Active Usage (DAU) section | ✅ | `component/test_dau_report.py::test_md_has_dau_heading_when_data_present`, `component/test_dau_report.py::test_md_dau_shows_team_avg`, `component/test_dau_report.py::test_md_dau_shows_role_in_table` |
| DAU-F-026 | The Markdown DAU section is omitted when there are no responses | ✅ | `component/test_dau_report.py::test_md_dau_section_absent_when_no_responses` |

#### Non-Functional Requirements

| ID | Requirement | Status | Tests |
|----|-------------|--------|-------|
| DAU-NFR-001 | All survey data is stored locally; no data is sent to any external service | ❌ | — |
| DAU-NFR-002 | Response files are excluded from version control | ⬜ | — |
| DAU-NFR-003 | No server process is required to submit the survey | ✅ | `e2e/test_dau_survey_ui.py::test_survey_page_loads_with_title` |
| DAU-NFR-004 | Survey page styling is consistent with the existing report aesthetic | ⬜ | — |
| DAU-NFR-005 | Form fields carry ARIA labels and the confirmation screen uses a live region | ❌ | — |
