"""Jira schema CRUD handler mixin — /api/schemas, /api/schema-detail/."""

from __future__ import annotations

import json
import logging
import re
import urllib.error
from datetime import UTC, datetime
from urllib.parse import quote as urlquote
from urllib.parse import unquote as urlunquote

from ._base import _root

logger = logging.getLogger(__name__)


class SchemaHandlerMixin:
    @staticmethod
    def _schemas_dir():
        return _root() / "docs" / "product" / "schemas"

    @staticmethod
    def _slugify(name: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "_", name.lower().strip())
        slug = slug.strip("_")[:80]
        return slug or "schema"

    def _handle_get_schema_detail(self, filename: str) -> None:
        filename = urlunquote(filename)
        if not filename.endswith(".json") or "/" in filename or "\\" in filename:
            self._send_json(400, {"ok": False, "error": "Invalid filename"})
            return
        target = self._schemas_dir() / filename
        if not target.is_file():
            self._send_json(404, {"ok": False, "error": "Schema not found"})
            return
        try:
            self._send_json(200, json.loads(target.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError) as exc:
            self._send_json(500, {"ok": False, "error": str(exc)})

    def _handle_get_schemas(self) -> None:
        """List schema names, or return a single schema when ?name= is provided."""
        from app.core import schema as schema_mod

        params = self._query_params()
        name_list = params.get("name")

        if name_list:
            name = name_list[0]
            schema = schema_mod.get_schema(name)
            if schema is None:
                self._send_json(404, {"ok": False, "error": f"Schema '{name}' not found"})
            else:
                self._send_json(200, {"ok": True, "schema": schema})
        else:
            schemas = schema_mod.load_schemas()
            names = [s.get("schema_name", "") for s in schemas]
            self._send_json(200, {"ok": True, "schemas": names})

    def _handle_post_schema(self) -> None:
        """Auto-fetch Jira fields and create a new schema entry."""
        from app.core import schema as schema_mod

        body = self._read_json_body()
        if body is None:
            self._send_json(400, {"ok": False, "error": "Invalid JSON body"})
            return

        legacy_name = (body.get("name") or "").strip()
        if legacy_name or body.get("projects") is not None or body.get("filter_id") is not None:
            projects = [p.strip() for p in str(body.get("projects") or "").split(",") if p.strip()]
            filter_id = (body.get("filter_id") or "").strip() or None

            if not legacy_name:
                self._send_json(400, {"ok": False, "error": "Schema name is required"})
                return
            if not projects:
                self._send_json(400, {"ok": False, "error": "At least one Project Key is required"})
                return

            url, email, token = self._read_env_credentials()
            if not url or not email or not token:
                self._send_json(
                    400,
                    {
                        "ok": False,
                        "error": (
                            "Jira credentials not found in .env. Save credentials in the Jira Connection tab first."
                        ),
                    },
                )
                return

            try:
                fields_raw = self._jira_api_get("/rest/api/2/field", url, email, token)
            except urllib.error.HTTPError as exc:
                self._send_json(
                    200,
                    {"ok": False, "error": f"Jira API error fetching fields: HTTP {exc.code} {exc.reason}"},
                )
                return
            except (urllib.error.URLError, OSError) as exc:
                self._send_json(200, {"ok": False, "error": f"Could not reach Jira: {exc}"})
                return

            fields: list[dict] = []
            for field in fields_raw if isinstance(fields_raw, list) else []:
                entry = {
                    "id": field.get("id", ""),
                    "name": field.get("name", ""),
                    "custom": field.get("custom", False),
                }
                if field.get("schema"):
                    entry["schema"] = {
                        "type": field["schema"].get("type", ""),
                        "custom": field["schema"].get("custom", ""),
                        "system": field["schema"].get("system", ""),
                    }
                fields.append(entry)

            sample_issue_key = None
            populated_fields: list[str] = []
            proj_clause = projects[0] if len(projects) == 1 else f"({', '.join(projects)})"
            jql = f"project {'= ' + proj_clause if len(projects) == 1 else 'IN ' + proj_clause} ORDER BY created DESC"
            try:
                search_result = self._jira_api_get(
                    f"/rest/api/2/search?jql={urlquote(jql)}&maxResults=1&fields=*all",
                    url,
                    email,
                    token,
                )
                issues = search_result.get("issues") or []
                if issues:
                    issue = issues[0]
                    sample_issue_key = issue.get("key")
                    issue_fields = issue.get("fields") or {}
                    populated_fields = [k for k, v in issue_fields.items() if v is not None]
            except (urllib.error.HTTPError, urllib.error.URLError, OSError) as exc:
                logger.warning(
                    "Failed to fetch sample Jira issue for schema inference: %s",
                    self._sanitise_exc(exc, url, email, token),
                )

            filter_jql = None
            if filter_id:
                try:
                    filter_data = self._jira_api_get(f"/rest/api/2/filter/{filter_id}", url, email, token)
                    filter_jql = filter_data.get("jql")
                except (urllib.error.HTTPError, urllib.error.URLError, OSError) as exc:
                    logger.warning(
                        "Could not fetch Jira filter %s: %s",
                        filter_id,
                        self._sanitise_exc(exc, url, email, token),
                    )

            created_at = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S")
            filename = f"{self._slugify(legacy_name)}.json"
            schemas_dir = self._schemas_dir()
            schemas_dir.mkdir(parents=True, exist_ok=True)
            out_path = schemas_dir / filename
            updated = out_path.exists()
            out_path.write_text(
                json.dumps(
                    {
                        "name": legacy_name,
                        "created_at": created_at,
                        "projects": projects,
                        "filter_id": filter_id,
                        "filter_jql": filter_jql,
                        "fields": fields,
                        "sample_issue_key": sample_issue_key,
                        "populated_fields": populated_fields,
                    },
                    indent=2,
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )
            self._send_json(
                200,
                {
                    "ok": True,
                    "updated": updated,
                    "name": legacy_name,
                    "filename": filename,
                    "created_at": created_at,
                    "field_count": len(fields),
                    "custom_count": sum(1 for field in fields if field.get("custom")),
                },
            )
            return

        schema_name = (body.get("schema_name") or "").strip()
        url = (body.get("jira_url") or "").strip().rstrip("/")
        email = (body.get("jira_email") or "").strip()
        token = (body.get("jira_token") or "").strip()

        if not schema_name:
            self._send_json(400, {"ok": False, "error": "schema_name is required"})
            return
        if not url or not email or not token:
            self._send_json(400, {"ok": False, "error": "jira_url, jira_email, and jira_token are required"})
            return

        # Optional resolution hints from the caller
        project_keys_raw = (body.get("project_keys") or "").strip()
        project_keys = [k.strip() for k in project_keys_raw.split(",") if k.strip()]
        board_id_raw = body.get("board_id")
        board_id: int | None = int(board_id_raw) if board_id_raw else None
        filter_id_hint = (body.get("filter_id") or "").strip() or None

        try:
            jira_fields = self._jira_api_get("/rest/api/2/field", url, email, token)
        except urllib.error.HTTPError as exc:
            self._send_json(200, {"ok": False, "error": f"Jira returned HTTP {exc.code}: {exc.reason}"})
            return
        except urllib.error.URLError as exc:
            self._send_json(200, {"ok": False, "error": f"Could not reach Jira: {exc.reason}"})
            return
        except Exception as exc:  # noqa: BLE001
            self._send_json(500, {"ok": False, "error": str(exc)})
            return

        if not isinstance(jira_fields, list):
            self._send_json(200, {"ok": False, "error": "Unexpected response from Jira /rest/api/2/field"})
            return

        # Derive project key from board when not provided directly
        if not project_keys and board_id is not None:
            try:
                board_info = self._jira_api_get(f"/rest/agile/1.0/board/{board_id}", url, email, token)
                pk = (board_info.get("location") or {}).get("projectKey", "").strip()
                if pk:
                    project_keys = [pk]
            except (urllib.error.HTTPError, urllib.error.URLError, OSError) as exc:
                logger.warning(
                    "Could not fetch board info for board %s: %s",
                    board_id,
                    self._sanitise_exc(exc, url, email, token),
                )

        # Probe a sample issue to collect populated field IDs
        populated_fields: list[str] = []
        if project_keys:
            proj_clause = project_keys[0] if len(project_keys) == 1 else f"({', '.join(project_keys)})"
            jql = (
                f"project {'= ' + proj_clause if len(project_keys) == 1 else 'IN ' + proj_clause}"
                " ORDER BY created DESC"
            )
            try:
                search_result = self._jira_api_get(
                    f"/rest/api/2/search?jql={urlquote(jql)}&maxResults=1&fields=*all",
                    url,
                    email,
                    token,
                )
                issues = search_result.get("issues") or []
                if issues:
                    issue_fields = issues[0].get("fields") or {}
                    populated_fields = [k for k, v in issue_fields.items() if v is not None]
            except (urllib.error.HTTPError, urllib.error.URLError, OSError) as exc:
                logger.warning(
                    "Could not fetch sample issue for schema inference: %s",
                    self._sanitise_exc(exc, url, email, token),
                )
        elif filter_id_hint:
            try:
                filter_data = self._jira_api_get(f"/rest/api/2/filter/{filter_id_hint}", url, email, token)
                filter_jql = filter_data.get("jql", "")
                if filter_jql:
                    search_result = self._jira_api_get(
                        f"/rest/api/2/search?jql={urlquote(filter_jql)}&maxResults=1&fields=*all",
                        url,
                        email,
                        token,
                    )
                    issues = search_result.get("issues") or []
                    if issues:
                        issue_fields = issues[0].get("fields") or {}
                        populated_fields = [k for k, v in issue_fields.items() if v is not None]
            except (urllib.error.HTTPError, urllib.error.URLError, OSError) as exc:
                logger.warning(
                    "Could not fetch sample issue via filter %s: %s",
                    filter_id_hint,
                    self._sanitise_exc(exc, url, email, token),
                )

        # Detect status categories from the Jira instance
        board_statuses: dict[str, list[str]] | None = None
        try:
            all_statuses = self._jira_api_get("/rest/api/2/status", url, email, token)
            if isinstance(all_statuses, list):
                # Optionally narrow to statuses used by a specific project
                project_status_names: set[str] | None = None
                if project_keys:
                    try:
                        proj_statuses_raw = self._jira_api_get(
                            f"/rest/api/2/project/{project_keys[0]}/statuses",
                            url,
                            email,
                            token,
                        )
                        if isinstance(proj_statuses_raw, list):
                            project_status_names = set()
                            for issue_type_entry in proj_statuses_raw:
                                for s in issue_type_entry.get("statuses") or []:
                                    project_status_names.add(s.get("name", ""))
                    except (urllib.error.HTTPError, urllib.error.URLError, OSError) as exc:
                        logger.warning(
                            "Could not fetch project statuses for %s: %s",
                            project_keys[0],
                            self._sanitise_exc(exc, url, email, token),
                        )

                done_statuses: list[str] = []
                in_progress_statuses: list[str] = []
                for status_obj in all_statuses:
                    sname = status_obj.get("name", "")
                    if not sname:
                        continue
                    if project_status_names is not None and sname not in project_status_names:
                        continue
                    category = (status_obj.get("statusCategory") or {}).get("key", "")
                    if category == "done":
                        done_statuses.append(sname)
                    elif category == "indeterminate":
                        in_progress_statuses.append(sname)
                if done_statuses or in_progress_statuses:
                    board_statuses = {
                        "done_statuses": done_statuses,
                        "in_progress_statuses": in_progress_statuses,
                    }
        except (urllib.error.HTTPError, urllib.error.URLError, OSError) as exc:
            logger.warning(
                "Could not fetch Jira statuses for schema inference: %s",
                self._sanitise_exc(exc, url, email, token),
            )

        new_schema = schema_mod.build_schema_from_fields(
            jira_fields,
            schema_name=schema_name,
            jira_url=url,
            populated_fields=populated_fields or None,
            board_statuses=board_statuses,
        )
        schema_mod.save_schema(new_schema)
        self._send_json(200, {"ok": True, "schema": new_schema})

    def _handle_delete_schema(self, filename: str | None = None) -> None:
        """Delete a schema entry by filename or by ?name=."""
        from app.core import schema as schema_mod

        if filename is not None:
            filename = urlunquote(filename)
            if not filename.endswith(".json") or "/" in filename or "\\" in filename:
                self._send_json(400, {"ok": False, "error": "Invalid filename"})
                return
            target = self._schemas_dir() / filename
            if target.is_file():
                target.unlink()
                self._send_json(200, {"ok": True})
            else:
                self._send_json(404, {"ok": False, "error": "Schema not found"})
            return

        params = self._query_params()
        name_list = params.get("name")
        if not name_list:
            self._send_json(400, {"ok": False, "error": "Query parameter 'name' is required"})
            return

        name = name_list[0]
        if name == schema_mod.DEFAULT_SCHEMA_NAME:
            self._send_json(400, {"ok": False, "error": "Cannot delete the default schema"})
            return

        deleted = schema_mod.delete_schema(name)
        if deleted:
            self._send_json(200, {"ok": True})
        else:
            self._send_json(404, {"ok": False, "error": f"Schema '{name}' not found"})
