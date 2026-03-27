"""Tests for app.core.schema: load, save, delete, query field schemas."""
from __future__ import annotations

import json

import pytest

from app.core import schema as schema_mod

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# load_schemas
# ---------------------------------------------------------------------------

def test_load_schemas_returns_list_from_file(tmp_path):
    p = tmp_path / "schemas.json"
    p.write_text(json.dumps({"schemas": [{"schema_name": "A"}]}), encoding="utf-8")
    result = schema_mod.load_schemas(p)
    assert len(result) == 1
    assert result[0]["schema_name"] == "A"


def test_load_schemas_missing_file(tmp_path):
    result = schema_mod.load_schemas(tmp_path / "nope.json")
    assert result == []


def test_load_schemas_invalid_json(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text("not json", encoding="utf-8")
    result = schema_mod.load_schemas(p)
    assert result == []


# ---------------------------------------------------------------------------
# get_schema
# ---------------------------------------------------------------------------

def test_get_schema_found(tmp_path):
    p = tmp_path / "schemas.json"
    p.write_text(json.dumps({"schemas": [{"schema_name": "X", "fields": {}}]}), encoding="utf-8")
    assert schema_mod.get_schema("X", p) is not None
    assert schema_mod.get_schema("X", p)["schema_name"] == "X"


def test_get_schema_not_found(tmp_path):
    p = tmp_path / "schemas.json"
    p.write_text(json.dumps({"schemas": [{"schema_name": "X"}]}), encoding="utf-8")
    assert schema_mod.get_schema("Y", p) is None


# ---------------------------------------------------------------------------
# get_active_schema
# ---------------------------------------------------------------------------

def test_get_active_schema_by_name(tmp_path):
    dn = schema_mod.DEFAULT_SCHEMA_NAME
    data = {"schemas": [
        {"schema_name": dn, "fields": {}},
        {"schema_name": "Custom", "fields": {"story_points": {"id": "cf_99"}}},
    ]}
    p = tmp_path / "schemas.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    result = schema_mod.get_active_schema("Custom", p)
    assert result["schema_name"] == "Custom"


def test_get_active_schema_falls_back_to_default(tmp_path):
    dn = schema_mod.DEFAULT_SCHEMA_NAME
    data = {"schemas": [{"schema_name": dn, "fields": {}}]}
    p = tmp_path / "schemas.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    result = schema_mod.get_active_schema(None, p)
    assert result["schema_name"] == dn


def test_get_active_schema_no_file_returns_hardcoded_default(tmp_path):
    result = schema_mod.get_active_schema(None, tmp_path / "missing.json")
    assert result["schema_name"] == schema_mod.DEFAULT_SCHEMA_NAME
    assert "fields" in result
    assert "status_mapping" in result


def test_get_active_schema_hardcoded_uses_builtin_story_points(tmp_path):
    result = schema_mod.get_active_schema(None, tmp_path / "missing.json")
    assert result["fields"]["story_points"]["id"] == schema_mod.DEFAULT_STORY_POINTS_FIELD_ID


# ---------------------------------------------------------------------------
# save_schema
# ---------------------------------------------------------------------------

def test_save_schema_creates_file(tmp_path):
    p = tmp_path / "sub" / "schemas.json"
    schema_mod.save_schema({"schema_name": "New", "fields": {}}, p)
    data = json.loads(p.read_text(encoding="utf-8"))
    assert len(data["schemas"]) == 1
    assert data["schemas"][0]["schema_name"] == "New"


def test_save_schema_updates_existing(tmp_path):
    p = tmp_path / "schemas.json"
    p.write_text(json.dumps({"schemas": [{"schema_name": "A", "v": 1}]}), encoding="utf-8")
    schema_mod.save_schema({"schema_name": "A", "v": 2}, p)
    data = json.loads(p.read_text(encoding="utf-8"))
    assert len(data["schemas"]) == 1
    assert data["schemas"][0]["v"] == 2


def test_save_schema_appends_new(tmp_path):
    p = tmp_path / "schemas.json"
    p.write_text(json.dumps({"schemas": [{"schema_name": "A"}]}), encoding="utf-8")
    schema_mod.save_schema({"schema_name": "B"}, p)
    data = json.loads(p.read_text(encoding="utf-8"))
    assert len(data["schemas"]) == 2


# ---------------------------------------------------------------------------
# delete_schema
# ---------------------------------------------------------------------------

def test_delete_schema_removes_entry(tmp_path):
    p = tmp_path / "schemas.json"
    dn = schema_mod.DEFAULT_SCHEMA_NAME
    p.write_text(json.dumps({"schemas": [
        {"schema_name": dn},
        {"schema_name": "Custom"},
    ]}), encoding="utf-8")
    assert schema_mod.delete_schema("Custom", p) is True
    data = json.loads(p.read_text(encoding="utf-8"))
    assert len(data["schemas"]) == 1


def test_delete_schema_refuses_default(tmp_path):
    dn = schema_mod.DEFAULT_SCHEMA_NAME
    p = tmp_path / "schemas.json"
    p.write_text(json.dumps({"schemas": [{"schema_name": dn}]}), encoding="utf-8")
    assert schema_mod.delete_schema(dn, p) is False


def test_delete_schema_not_found(tmp_path):
    p = tmp_path / "schemas.json"
    p.write_text(json.dumps({"schemas": []}), encoding="utf-8")
    assert schema_mod.delete_schema("Ghost", p) is False


# ---------------------------------------------------------------------------
# get_field_id / get_field_jql_name
# ---------------------------------------------------------------------------

def test_get_field_id():
    schema = {"fields": {"story_points": {"id": "cf_100", "type": "number"}}}
    assert schema_mod.get_field_id(schema, "story_points") == "cf_100"
    assert schema_mod.get_field_id(schema, "missing") is None


def test_get_field_jql_name_with_explicit_jql_name():
    schema = {"fields": {"team": {"id": "cf_1", "jql_name": "Team[Team]"}}}
    assert schema_mod.get_field_jql_name(schema, "team") == "Team[Team]"


def test_get_field_jql_name_falls_back_to_id():
    schema = {"fields": {"priority": {"id": "priority"}}}
    assert schema_mod.get_field_jql_name(schema, "priority") == "priority"


# ---------------------------------------------------------------------------
# get_done_statuses / get_in_progress_statuses
# ---------------------------------------------------------------------------

def test_get_done_statuses():
    schema = {"status_mapping": {"done_statuses": ["Done", "Finished"]}}
    assert schema_mod.get_done_statuses(schema) == ["Done", "Finished"]


def test_get_done_statuses_defaults():
    assert "Done" in schema_mod.get_done_statuses({})


def test_get_in_progress_statuses():
    schema = {"status_mapping": {"in_progress_statuses": ["Working"]}}
    assert schema_mod.get_in_progress_statuses(schema) == ["Working"]


def test_get_in_progress_statuses_defaults():
    assert "In Progress" in schema_mod.get_in_progress_statuses({})


# ---------------------------------------------------------------------------
# build_schema_from_fields
# ---------------------------------------------------------------------------

def test_build_schema_from_fields_detects_sprint():
    jira_fields = [
        {
            "id": "customfield_10020",
            "name": "Sprint",
            "custom": True,
            "schema": {"type": "array", "custom": "com.pyxis.greenhopper.jira:gh-sprint"},
        },
    ]
    result = schema_mod.build_schema_from_fields(jira_fields, "Test Schema")
    assert result["schema_name"] == "Test Schema"
    assert result["fields"]["sprint"]["id"] == "customfield_10020"


def test_build_schema_from_fields_detects_story_points_by_name():
    jira_fields = [
        {
            "id": "customfield_99999",
            "name": "Story Points",
            "custom": True,
            "schema": {"type": "number"},
        },
    ]
    result = schema_mod.build_schema_from_fields(jira_fields, "SP Test")
    assert result["fields"]["story_points"]["id"] == "customfield_99999"


def test_build_schema_from_fields_preserves_defaults_for_missing():
    result = schema_mod.build_schema_from_fields([], "Empty")
    assert result["fields"]["priority"]["id"] == "priority"
    assert result["fields"]["labels"]["id"] == "labels"
    assert "status_mapping" in result


def test_build_schema_from_fields_preserves_team_jql_name():
    jira_fields = [
        {
            "id": "customfield_50000",
            "name": "Team",
            "custom": True,
            "schema": {"type": "string", "custom": "com.atlassian.teams:rm-teams-custom-field-team"},
        },
    ]
    result = schema_mod.build_schema_from_fields(jira_fields, "Team Test")
    assert result["fields"]["team"]["id"] == "customfield_50000"
    assert result["fields"]["team"]["jql_name"] == "Team[Team]"
