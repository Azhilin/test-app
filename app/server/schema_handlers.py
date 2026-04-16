"""Jira schema CRUD handler mixin — /api/schemas, /api/schema-detail/."""

from __future__ import annotations

import json
import logging
import re
from urllib.parse import unquote as urlunquote

from ._base import _root

logger = logging.getLogger(__name__)


class SchemaHandlerMixin:
    @staticmethod
    def _schemas_dir():
        return _root() / "generated" / "schemas"

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
        """Upsert a schema entry from a raw-JSON body: {schema: {...}}."""
        from app.core import schema as schema_mod

        body = self._read_json_body()
        if not isinstance(body, dict):
            self._send_json(400, {"ok": False, "error": "Invalid JSON body"})
            return

        schema = body.get("schema")
        if not isinstance(schema, dict):
            self._send_json(400, {"ok": False, "error": "Request must contain a 'schema' object"})
            return

        raw_name = schema.get("schema_name")
        if not isinstance(raw_name, str) or not raw_name.strip():
            self._send_json(400, {"ok": False, "error": "schema_name must be a non-empty string"})
            return
        name = raw_name.strip()

        if not isinstance(schema.get("fields"), dict):
            self._send_json(400, {"ok": False, "error": "fields must be an object"})
            return

        status_mapping = schema.get("status_mapping")
        if (
            not isinstance(status_mapping, dict)
            or not isinstance(status_mapping.get("done_statuses"), list)
            or not isinstance(status_mapping.get("in_progress_statuses"), list)
        ):
            self._send_json(
                400,
                {
                    "ok": False,
                    "error": ("status_mapping.done_statuses and status_mapping.in_progress_statuses must be lists"),
                },
            )
            return

        schema["schema_name"] = name
        updated = schema_mod.get_schema(name) is not None
        schema_mod.save_schema(schema)
        self._send_json(200, {"ok": True, "updated": updated, "schema": schema})

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
