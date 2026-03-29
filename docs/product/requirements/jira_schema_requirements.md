# Jira Schema Requirements — AI Adoption Metrics Report

This document defines requirements for the field schema system that maps Jira custom field IDs and status names to application concepts (story points, done statuses, etc.). The schema is stored in `config/jira_schema.json` and managed by `app/core/schema.py`.

---

## Table of Contents

1. [Schema Loading](#1-schema-loading)
2. [Active Schema Resolution](#2-active-schema-resolution)
3. [Schema Save & Delete](#3-schema-save--delete)
4. [Field ID & JQL Name Lookups](#4-field-id--jql-name-lookups)
5. [Status Mappings](#5-status-mappings)
6. [Auto-Detection from Jira Fields](#6-auto-detection-from-jira-fields)
7. [Future Enhancements](#7-future-enhancements)

---

## 1. Schema Loading

| ID | Requirement | Acceptance Criterion | Status | Tests |
|----|-------------|----------------------|--------|-------|
| JSR-L-001 | All schema entries are loaded from `config/jira_schema.json` | `load_schemas()` reads the file, parses the `"schemas"` array, and returns it as a Python list; each entry is a dict with at least `schema_name` and `fields` keys | ✓ Met | `test_load_schemas_returns_list_from_file` |
| JSR-L-002 | A missing schema file returns an empty list | When `config/jira_schema.json` does not exist, `load_schemas()` returns `[]` without raising an exception | ✓ Met | `test_load_schemas_missing_file` |
| JSR-L-003 | Malformed JSON in the schema file returns an empty list | When the file contains invalid JSON, `load_schemas()` returns `[]` without raising an exception | ✓ Met | `test_load_schemas_invalid_json` |
| JSR-L-004 | A schema can be retrieved by name | `get_schema(name)` returns the matching dict when the name exists, and `None` when it does not | ✓ Met | `test_get_schema_found`, `test_get_schema_not_found` |

---

## 2. Active Schema Resolution

| ID | Requirement | Acceptance Criterion | Status | Tests |
|----|-------------|----------------------|--------|-------|
| JSR-R-001 | A named schema is returned when an explicit name is given | `get_active_schema(schema_name="MySchema")` returns the entry whose `schema_name` equals `"MySchema"` | ✓ Met | `test_get_active_schema_by_name` |
| JSR-R-002 | `Default_Jira_Cloud` is used as a fallback when no name is given | When `schema_name` is `None` and `config/jira_schema.json` exists, `get_active_schema()` returns the entry named `"Default_Jira_Cloud"` | ✓ Met | `test_get_active_schema_falls_back_to_default` |
| JSR-R-003 | The hardcoded `_DEFAULT_SCHEMA` is returned when the file is absent | When `config/jira_schema.json` does not exist, `get_active_schema()` returns the built-in default schema including the correct `customfield_10016` story-points field ID | ✓ Met | `test_get_active_schema_no_file_returns_hardcoded_default`, `test_get_active_schema_hardcoded_uses_builtin_story_points` |
| JSR-R-004 | A non-existent named schema falls back to the default silently | When `schema_name` is provided but no entry with that name exists in the file, `get_active_schema()` returns the default schema without raising an exception | ⚠ Undocumented fallback — no warning logged | — |

---

## 3. Schema Save & Delete

| ID | Requirement | Acceptance Criterion | Status | Tests |
|----|-------------|----------------------|--------|-------|
| JSR-SD-001 | A new schema is appended to the file | `save_schema(schema)` adds the entry to `config/jira_schema.json` when no entry with the same `schema_name` already exists | ✓ Met | `test_save_schema_appends_new` |
| JSR-SD-002 | An existing schema is updated in-place | `save_schema(schema)` overwrites the first entry whose `schema_name` matches, preserving all other entries unchanged | ✓ Met | `test_save_schema_updates_existing` |
| JSR-SD-003 | The parent directory is created if absent | When the target file's parent directory does not exist, `save_schema()` creates it before writing the file | ✓ Met | `test_save_schema_creates_file` |
| JSR-SD-004 | `Default_Jira_Cloud` cannot be deleted | `delete_schema("Default_Jira_Cloud")` returns `False` and leaves the file unchanged | ✓ Met | `test_delete_schema_refuses_default` |
| JSR-SD-005 | Deleting a non-existent schema name returns `False` | `delete_schema("Unknown")` returns `False` without modifying the file or raising an exception | ✓ Met | `test_delete_schema_not_found` |

---

## 4. Field ID & JQL Name Lookups

| ID | Requirement | Acceptance Criterion | Status | Tests |
|----|-------------|----------------------|--------|-------|
| JSR-F-001 | `get_field_id()` returns the Jira field ID for a known field key | `get_field_id(schema, "story_points")` returns the string stored in `schema["fields"]["story_points"]["id"]` | ✓ Met | `test_get_field_id` |
| JSR-F-002 | `get_field_id()` returns `None` for an unknown field key | `get_field_id(schema, "nonexistent_key")` returns `None` without raising a `KeyError` | ✓ Met | `test_get_field_id` |
| JSR-F-003 | `get_field_jql_name()` falls back to `id` when `jql_name` is absent | When a field entry has no `jql_name` key, `get_field_jql_name()` returns the value of `id` instead | ✓ Met | `test_get_field_jql_name_falls_back_to_id`, `test_get_field_jql_name_with_explicit_jql_name` |

---

## 5. Status Mappings

| ID | Requirement | Acceptance Criterion | Status | Tests |
|----|-------------|----------------------|--------|-------|
| JSR-SM-001 | `get_done_statuses()` returns the configured done status list | When the schema has a `status_mapping.done_statuses` list, `get_done_statuses()` returns it unchanged | ✓ Met | `test_get_done_statuses` |
| JSR-SM-002 | `get_in_progress_statuses()` returns the configured in-progress list | When the schema has a `status_mapping.in_progress_statuses` list, `get_in_progress_statuses()` returns it unchanged | ✓ Met | `test_get_in_progress_statuses` |
| JSR-SM-003 | Default done statuses are returned when `status_mapping` is absent | When the schema dict has no `status_mapping` key, `get_done_statuses()` returns `["Done", "Closed", "Resolved", "Complete"]` | ✓ Met | `test_get_done_statuses_defaults` |
| JSR-SM-004 | Default in-progress statuses are returned when `status_mapping` is absent | When the schema dict has no `status_mapping` key, `get_in_progress_statuses()` returns `["In Progress"]` | ✓ Met | `test_get_in_progress_statuses_defaults` |

---

## 6. Auto-Detection from Jira Fields

| ID | Requirement | Acceptance Criterion | Status | Tests |
|----|-------------|----------------------|--------|-------|
| JSR-AD-001 | Sprint field is detected by `schema.custom` identifier | When a Jira field's `schema.custom` value matches a `KNOWN_FIELD_SCHEMAS` entry (e.g. `com.pyxis.greenhopper.jira:gh-sprint`), `build_schema_from_fields()` maps it to the `sprint` field | ✓ Met | `test_build_schema_from_fields_detects_sprint` |
| JSR-AD-002 | Story-points field is detected by name pattern when `schema.custom` is absent | When a custom field has no matching `schema.custom` identifier but its name contains a substring from `KNOWN_NAME_PATTERNS` (e.g. `"story point"`), `build_schema_from_fields()` maps it to `story_points` | ✓ Met | `test_build_schema_from_fields_detects_story_points_by_name` |
| JSR-AD-003 | Undetected fields retain their `_DEFAULT_SCHEMA` values | For any field key not matched during auto-detection, `build_schema_from_fields()` preserves the default field ID and type from `_DEFAULT_SCHEMA` | ✓ Met | `test_build_schema_from_fields_preserves_defaults_for_missing` |
| JSR-AD-004 | The `team` field's `jql_name` is preserved through auto-detection | Even when the team field is re-detected and its `id` overridden, its `jql_name` (e.g. `"Team[Team]"`) is carried into the resulting schema | ✓ Met | `test_build_schema_from_fields_preserves_team_jql_name` |
| JSR-AD-005 | Null or structurally incomplete entries in the Jira fields response are tolerated | When the `jira_fields` list passed to `build_schema_from_fields()` contains `None` values or dicts missing `schema` or `name` keys, the function completes without raising an exception and falls back to default values for unmatched fields | ⚠ Not tested | — |

---

## 7. Future Enhancements

| ID | Requirement | Rationale | Status |
|----|-------------|-----------|--------|
| JSR-FUT-001 | Validate schema entries on load and surface missing required keys as warnings | Malformed schema entries (e.g. missing `schema_name` or `fields`) are loaded silently; a validation pass would make configuration errors diagnosable without crashing | Proposed |
| JSR-FUT-002 | Block duplicate `schema_name` values on save | `save_schema()` updates only the first matching entry; a file with duplicate names causes subsequent entries to be silently ignored | Proposed |
| JSR-FUT-003 | Add a `get_schema_names()` convenience function | All callers that need a list of schema names must call `load_schemas()` and map manually; a helper would reduce boilerplate across the codebase | Proposed |
| JSR-FUT-004 | Emit a warning when a non-existent named schema falls back to the default | `get_active_schema()` silently uses the default if the requested name is not found; a `logger.warning()` would make a misconfigured `JIRA_SCHEMA_NAME` env var visible without breaking the pipeline | Proposed |
