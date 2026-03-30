"""Jira filter CRUD handler mixin — /api/filters."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime

from ._base import _root

logger = logging.getLogger(__name__)


class FilterHandlerMixin:
    _DEFAULT_FILTER: dict = {
        "filter_name": "Default_Jira_Filter",
        "slug": "default_jira_filter",
        "description": "Default JQL filter template. Set JIRA_PROJECT before saving.",
        "is_default": True,
        "created_at": None,
        "jql": "",
        "params": {
            "JIRA_PROJECT": "",
            "JIRA_TEAM_ID": "",
            "JIRA_ISSUE_TYPES": "",
            "JIRA_FILTER_STATUS": "Done",
            "JIRA_CLOSED_SPRINTS_ONLY": "true",
            "schema_name": "Default_Jira_Cloud",
        },
    }

    @staticmethod
    def _filters_config_path():
        return _root() / "config" / "jira_filters.json"

    def _load_filters(self) -> list[dict]:
        """Read config/jira_filters.json, creating it with the default entry if missing."""
        path = self._filters_config_path()
        if not path.is_file():
            filters = [self._DEFAULT_FILTER.copy()]
            path.write_text(json.dumps(filters, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            return filters
        try:
            filters = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(filters, list):
                filters = []
        except (OSError, json.JSONDecodeError):
            filters = []
        if not any(f.get("is_default") for f in filters):
            filters.insert(0, self._DEFAULT_FILTER.copy())
        return filters

    def _save_filters(self, filters: list[dict]) -> None:
        path = self._filters_config_path()
        path.write_text(json.dumps(filters, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    @staticmethod
    def _build_jql_from_params(params: dict, team_jql_field: str = "Team[Team]") -> str:
        """Build a JQL query from filter params. Mirrors buildJqlLocally() in ui/index.html."""

        def jql_quote(v: str) -> str:
            if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
                return v
            if any(c in v for c in " (),=<>"):
                return f'"{v}"'
            return v

        raw_project = (params.get("JIRA_PROJECT") or "").strip()
        projects = [p.strip() for p in raw_project.split(",") if p.strip()]
        if not projects:
            return ""

        clauses: list[str] = []
        if len(projects) == 1:
            clauses.append(f"project = {projects[0]}")
        else:
            clauses.append(f"project IN ({', '.join(projects)})")

        raw_team = (params.get("JIRA_TEAM_ID") or "").strip()
        team_ids = [t.strip() for t in raw_team.split(",") if t.strip()]
        if team_ids:
            quoted = [jql_quote(t) for t in team_ids]
            tf = f'"{team_jql_field}"'
            if len(quoted) == 1:
                clauses.append(f"{tf} = {quoted[0]}")
            else:
                clauses.append(f"{tf} IN ({', '.join(quoted)})")

        raw_status = (params.get("JIRA_FILTER_STATUS") or "Done").strip()
        statuses = [s.strip() for s in raw_status.split(",") if s.strip()] or ["Done"]
        quoted_st = [jql_quote(s) for s in statuses]
        if len(quoted_st) == 1:
            clauses.append(f"status = {quoted_st[0]}")
        else:
            clauses.append(f"status IN ({', '.join(quoted_st)})")

        raw_types = (params.get("JIRA_ISSUE_TYPES") or "").strip()
        types = [t.strip() for t in raw_types.split(",") if t.strip()]
        if types:
            clauses.append(f"type IN ({', '.join(jql_quote(t) for t in types)})")

        closed_only = (params.get("JIRA_CLOSED_SPRINTS_ONLY") or "true").strip().lower()
        if closed_only in ("1", "true", "yes", "on"):
            clauses.append("sprint in closedSprints()")

        return " AND ".join(clauses)

    def _handle_get_filters(self) -> None:
        """Return all saved filters from config/jira_filters.json."""
        filters = self._load_filters()
        defaults = [f for f in filters if f.get("is_default")]
        user = [f for f in filters if not f.get("is_default")]
        user.sort(key=lambda f: f.get("created_at") or "", reverse=True)
        self._send_json(200, {"ok": True, "filters": defaults + user})

    def _handle_post_filter(self) -> None:
        """Create or update a named filter in config/jira_filters.json."""
        body = self._read_json_body()
        if body is None:
            self._send_json(400, {"ok": False, "error": "Invalid JSON body"})
            return

        name = (body.get("name") or "").strip()
        params = body.get("params") or {}

        if not name:
            self._send_json(400, {"ok": False, "error": "Filter name is required"})
            return
        if not (params.get("JIRA_PROJECT") or "").strip():
            self._send_json(200, {"ok": False, "error": "JIRA_PROJECT is required to build a JQL filter"})
            return

        team_jql_field = "Team[Team]"
        schema_name = (params.get("schema_name") or "").strip()
        if schema_name:
            try:
                from app.core import schema as schema_mod

                schema = schema_mod.get_schema(schema_name)
                if schema:
                    team_field = (schema.get("fields") or {}).get("team") or {}
                    team_jql_field = team_field.get("jql_name") or team_field.get("id") or team_jql_field
            except Exception:  # noqa: BLE001  # nosec B110
                pass

        jql = self._build_jql_from_params(params, team_jql_field)

        slug = self._slugify(name) or "filter"
        created_at = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S")

        filters = self._load_filters()
        idx = next((i for i, f in enumerate(filters) if f.get("filter_name", "").lower() == name.lower()), None)
        updated = idx is not None and not filters[idx].get("is_default")

        entry: dict = {
            "filter_name": name,
            "slug": slug,
            "description": "",
            "is_default": False,
            "created_at": created_at,
            "jql": jql,
            "params": params,
        }

        if updated and idx is not None:
            entry["created_at"] = filters[idx].get("created_at") or created_at
            filters[idx] = entry
        else:
            filters.append(entry)

        self._save_filters(filters)
        self._send_json(
            200,
            {"ok": True, "updated": updated, "jql": jql, "slug": slug, "created_at": entry["created_at"]},
        )

    def _handle_delete_filter(self, slug: str) -> None:
        """Remove a filter entry by slug. The default filter cannot be deleted."""
        if not slug:
            self._send_json(400, {"ok": False, "error": "Filter slug is required"})
            return

        filters = self._load_filters()
        target = next((f for f in filters if f.get("slug") == slug), None)

        if target is None:
            self._send_json(200, {"ok": False, "error": "Filter not found"})
            return
        if target.get("is_default"):
            self._send_json(200, {"ok": False, "error": "Cannot delete the default filter"})
            return

        self._save_filters([f for f in filters if f.get("slug") != slug])
        self._send_json(200, {"ok": True})
