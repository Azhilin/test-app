"""Config read/write handler mixin — /api/config."""

from __future__ import annotations

from ._base import _root

_CONFIG_KEYS = [
    "JIRA_URL",
    "JIRA_EMAIL",
    "JIRA_API_TOKEN",
    "JIRA_BOARD_ID",
    "JIRA_SPRINT_COUNT",
    "JIRA_SCHEMA_NAME",
    "JIRA_FILTER_ID",
    "JIRA_PROJECT",
    "JIRA_TEAM_ID",
    "JIRA_ISSUE_TYPES",
    "JIRA_FILTER_STATUS",
    "JIRA_CLOSED_SPRINTS_ONLY",
    "JIRA_FILTER_PAGE_SIZE",
    "AI_ASSISTED_LABEL",
    "AI_EXCLUDE_LABELS",
    "AI_TOOL_LABELS",
    "AI_ACTION_LABELS",
]


class ConfigHandlerMixin:
    def _handle_get_config(self) -> None:
        """Return current .env values; JIRA_API_TOKEN is masked as '***'."""
        env_path = _root() / ".env"
        raw_config: dict[str, str] = {}
        if env_path.exists():
            for line in env_path.read_text(encoding="utf-8").splitlines():
                stripped = line.strip()
                if stripped.startswith("#") or "=" not in stripped:
                    continue
                key, _, val = stripped.partition("=")
                raw_config[key.strip()] = val.strip()

        out: dict[str, str] = {}
        for k in _CONFIG_KEYS:
            v = raw_config.get(k, "")
            if k == "JIRA_API_TOKEN" and v:
                out[k] = "***"
            elif v:
                out[k] = v

        configured = bool(out.get("JIRA_URL") and out.get("JIRA_EMAIL") and out.get("JIRA_API_TOKEN"))
        self._send_json(200, {"config": out, "configured": configured})

    def _handle_post_config(self) -> None:
        """Write whitelisted config keys to .env on disk."""
        body = self._read_json_body()
        if body is None:
            self._send_json(400, {"ok": False, "error": "Invalid JSON body"})
            return

        updates: dict[str, str] = {}
        for key in _CONFIG_KEYS:
            val = (body.get(key) or "").strip()
            if key == "JIRA_API_TOKEN" and val == "***":
                continue
            if val:
                updates[key] = val

        try:
            self._write_env_fields(updates)
            self._send_json(200, {"ok": True})
        except Exception as exc:  # noqa: BLE001
            self._send_json(500, {"ok": False, "error": str(exc)})

    def _write_env_fields(self, updates: dict[str, str]) -> None:
        """Update or add key=value pairs in .env, creating from .env.example if absent."""
        env_path = _root() / ".env"
        example_path = _root() / ".env.example"

        if env_path.exists():
            lines = env_path.read_text(encoding="utf-8").splitlines()
        elif example_path.exists():
            lines = example_path.read_text(encoding="utf-8").splitlines()
        else:
            lines = []

        written = set()
        new_lines: list[str] = []
        for line in lines:
            stripped = line.strip()
            check = stripped.lstrip("# ")
            matched_key = None
            for key in updates:
                if check.startswith(key + "=") or check == key:
                    matched_key = key
                    break
            if matched_key and matched_key not in written:
                new_lines.append(f"{matched_key}={updates[matched_key]}")
                written.add(matched_key)
            else:
                new_lines.append(line)

        for key, val in updates.items():
            if key not in written:
                new_lines.append(f"{key}={val}")

        env_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
