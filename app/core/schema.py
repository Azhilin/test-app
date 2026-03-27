"""Load, save, and query Jira field schemas from config/jira_schema.json."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SCHEMA_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "jira_schema.json"

DEFAULT_SCHEMA_NAME = "Default_Jira_Cloud"

_DEFAULT_SCHEMA: dict[str, Any] = {
    "schema_name": DEFAULT_SCHEMA_NAME,
    "description": "Standard Jira Cloud field mapping",
    "jira_url_pattern": "",
    "fields": {
        "story_points": {"id": "customfield_10016", "type": "number", "description": "Story point estimate"},
        "sprint": {"id": "customfield_10020", "type": "array", "description": "Sprint(s) the issue belongs to"},
        "epic_link": {"id": "customfield_10014", "type": "string", "description": "Parent epic key"},
        "epic_name": {"id": "customfield_10011", "type": "string", "description": "Epic name"},
        "team": {"id": "customfield_10001", "type": "string", "jql_name": "Team[Team]", "description": "Team field"},
        "priority": {"id": "priority", "type": "string", "description": "Issue priority"},
        "labels": {"id": "labels", "type": "array", "description": "Issue labels"},
        "issue_type": {"id": "issuetype", "type": "string", "description": "Issue type"},
        "status": {"id": "status", "type": "string", "description": "Issue status"},
        "resolution": {"id": "resolution", "type": "object", "description": "Resolution object (name: Done/Fixed/etc.); use resolution_date for time-based metrics"},
        "assignee": {"id": "assignee", "type": "object", "description": "Issue assignee (user object with displayName, accountId); use for per-assignee breakdowns"},
        "components": {"id": "components", "type": "array", "description": "Jira components assigned to the issue; use for component-level delivery trends"},
        "fix_version": {"id": "fixVersions", "type": "array", "description": "Fix version(s) / release tags; use for release-based delivery metrics"},
        "parent": {"id": "parent", "type": "object", "description": "Parent issue (epic or task); alternative to epic_link for Next-gen projects"},
        "due_date": {"id": "duedate", "type": "string", "description": "Issue due date (ISO-8601 date string)"},
        "resolution_date": {"id": "resolutiondate", "type": "string", "description": "Timestamp when the issue was resolved (ISO-8601); reliable cycle-time endpoint"},
        # start_date is a custom field whose ID varies by instance; customfield_10015 is the Jira Cloud default
        "start_date": {"id": "customfield_10015", "type": "string", "description": "Issue start date (custom field; ID varies by instance — verify via auto-detect)"},
    },
    "status_mapping": {
        "done_statuses": ["Done", "Closed", "Resolved", "Complete"],
        "in_progress_statuses": ["In Progress"],
    },
}

# Built-in story points field when no schema dict supplies one (matches _DEFAULT_SCHEMA)
DEFAULT_STORY_POINTS_FIELD_ID: str = _DEFAULT_SCHEMA["fields"]["story_points"]["id"]


def _read_file(path: Path | None = None) -> dict[str, Any]:
    """Read and parse the schema JSON file. Returns {"schemas": []} on failure."""
    p = path or SCHEMA_PATH
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {"schemas": []}


def _write_file(data: dict[str, Any], path: Path | None = None) -> None:
    p = path or SCHEMA_PATH
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_schemas(path: Path | None = None) -> list[dict[str, Any]]:
    """Return all schema entries from the JSON file."""
    return _read_file(path).get("schemas") or []


def get_schema(name: str, path: Path | None = None) -> dict[str, Any] | None:
    """Find a schema by name. Returns None if not found."""
    for s in load_schemas(path):
        if s.get("schema_name") == name:
            return s
    return None


def get_active_schema(schema_name: str | None = None, path: Path | None = None) -> dict[str, Any]:
    """Resolve the active schema with a fallback chain.

    1. If schema_name is given, look it up.
    2. Otherwise try the default schema from file.
    3. If nothing found, return the built-in default (same shape as shipped jira_schema.json).
    """
    if schema_name:
        found = get_schema(schema_name, path)
        if found:
            return found

    default = get_schema(DEFAULT_SCHEMA_NAME, path)
    if default:
        return default

    return json.loads(json.dumps(_DEFAULT_SCHEMA))


def save_schema(schema: dict[str, Any], path: Path | None = None) -> None:
    """Add or update a schema entry (matched by schema_name)."""
    data = _read_file(path)
    schemas = data.get("schemas") or []
    name = schema.get("schema_name", "")

    for i, s in enumerate(schemas):
        if s.get("schema_name") == name:
            schemas[i] = schema
            data["schemas"] = schemas
            _write_file(data, path)
            return

    schemas.append(schema)
    data["schemas"] = schemas
    _write_file(data, path)


def delete_schema(name: str, path: Path | None = None) -> bool:
    """Remove a schema entry by name. Refuses to delete the default. Returns True if deleted."""
    if name == DEFAULT_SCHEMA_NAME:
        return False
    data = _read_file(path)
    schemas = data.get("schemas") or []
    before = len(schemas)
    schemas = [s for s in schemas if s.get("schema_name") != name]
    if len(schemas) == before:
        return False
    data["schemas"] = schemas
    _write_file(data, path)
    return True


def get_field_id(schema: dict[str, Any], field_key: str) -> str | None:
    """Extract a field's Jira ID from the schema (e.g. get_field_id(s, 'story_points'))."""
    field = (schema.get("fields") or {}).get(field_key)
    return field.get("id") if field else None


def get_field_jql_name(schema: dict[str, Any], field_key: str) -> str | None:
    """Extract a field's JQL name (falls back to id if jql_name absent)."""
    field = (schema.get("fields") or {}).get(field_key)
    if not field:
        return None
    return field.get("jql_name") or field.get("id")


def get_done_statuses(schema: dict[str, Any]) -> list[str]:
    """Return done status names from the schema's status_mapping."""
    mapping = schema.get("status_mapping") or {}
    return list(mapping.get("done_statuses") or ["Done", "Closed", "Resolved", "Complete"])


def get_in_progress_statuses(schema: dict[str, Any]) -> list[str]:
    """Return in-progress status names from the schema's status_mapping."""
    mapping = schema.get("status_mapping") or {}
    return list(mapping.get("in_progress_statuses") or ["In Progress"])


# Well-known Jira custom field schema identifiers used for auto-detection
KNOWN_FIELD_SCHEMAS: dict[str, str] = {
    "com.pyxis.greenhopper.jira:gh-sprint": "sprint",
    "com.pyxis.greenhopper.jira:gh-epic-link": "epic_link",
    "com.pyxis.greenhopper.jira:gh-epic-label": "epic_name",
    "com.atlassian.jira.plugin.system.customfieldtypes:float": "story_points",
    "com.atlassian.teams:rm-teams-custom-field-team": "team",
    # datepicker is used for "Start date" on Jira Cloud; other date custom fields may match too
    "com.atlassian.jira.plugin.system.customfieldtypes:datepicker": "start_date",
}

# Name patterns used as secondary heuristic when schema.custom is absent
KNOWN_NAME_PATTERNS: dict[str, list[str]] = {
    "story_points": ["story point", "story_point"],
    "sprint": ["sprint"],
    "epic_link": ["epic link"],
    "epic_name": ["epic name"],
    "team": ["team"],
    "start_date": ["start date", "start_date"],
}


def build_schema_from_fields(
    jira_fields: list[dict[str, Any]],
    schema_name: str,
    jira_url: str = "",
    description: str = "",
) -> dict[str, Any]:
    """Build a schema dict from Jira's GET /rest/api/2/field response.

    Matches custom fields by their schema.custom identifier first, then falls back
    to name-based heuristics. Standard fields (priority, labels, etc.) are always
    included with their canonical IDs.
    """
    detected: dict[str, dict[str, Any]] = {}

    for field in jira_fields:
        fid = field.get("id", "")
        fname = field.get("name", "")
        is_custom = field.get("custom", False)
        schema_info = field.get("schema") or {}
        custom_type = schema_info.get("custom", "")

        if is_custom and custom_type in KNOWN_FIELD_SCHEMAS:
            key = KNOWN_FIELD_SCHEMAS[custom_type]
            detected[key] = {
                "id": fid,
                "type": schema_info.get("type", "string"),
                "description": fname,
            }
            continue

        if is_custom:
            name_lower = fname.lower()
            for key, patterns in KNOWN_NAME_PATTERNS.items():
                if key not in detected and any(p in name_lower for p in patterns):
                    detected[key] = {
                        "id": fid,
                        "type": schema_info.get("type", "string"),
                        "description": fname,
                    }
                    break

    # Start from default and overlay detected fields
    fields = json.loads(json.dumps(_DEFAULT_SCHEMA["fields"]))
    for key, info in detected.items():
        if key in fields:
            fields[key]["id"] = info["id"]
            fields[key]["type"] = info.get("type", fields[key].get("type", "string"))
            fields[key]["description"] = info.get("description", fields[key].get("description", ""))
        else:
            fields[key] = info

    # Carry over jql_name from default for team if not overridden
    if "team" in detected and "jql_name" not in detected["team"]:
        fields["team"]["jql_name"] = _DEFAULT_SCHEMA["fields"]["team"]["jql_name"]

    return {
        "schema_name": schema_name,
        "description": description or f"Auto-detected from {jira_url}",
        "jira_url_pattern": jira_url,
        "fields": fields,
        "status_mapping": json.loads(json.dumps(_DEFAULT_SCHEMA["status_mapping"])),
    }
