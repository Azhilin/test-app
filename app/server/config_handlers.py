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
    "JIRA_CLOSED_SPRINTS_ONLY",
    "JIRA_FILTER_PAGE_SIZE",
    "AI_ASSISTED_LABEL",
    "AI_EXCLUDE_LABELS",
    "AI_TOOL_LABELS",
    "AI_ACTION_LABELS",
]

# Keys that contain credentials — written to .env (gitignored).
# All other keys are written to config/defaults.env (committed).
_SECRET_KEYS = {"JIRA_URL", "JIRA_EMAIL", "JIRA_API_TOKEN"}


def _read_env_file(path) -> dict[str, str]:
    """Parse a key=value env file; skip blank lines and comments."""
    result: dict[str, str] = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith("#") or "=" not in stripped:
                continue
            key, _, val = stripped.partition("=")
            result[key.strip()] = val.strip()
    return result


class ConfigHandlerMixin:
    def _handle_get_config(self) -> None:
        """Return current config values; JIRA_API_TOKEN is masked as '***'."""
        defaults_path = _root() / "config" / "defaults.env"
        env_path = _root() / ".env"

        # Merge: defaults first, then .env wins on collision
        raw_config = _read_env_file(defaults_path)
        raw_config.update(_read_env_file(env_path))

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
        """Write whitelisted config keys to the appropriate env file on disk."""
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
            secret_updates = {k: v for k, v in updates.items() if k in _SECRET_KEYS}
            defaults_updates = {k: v for k, v in updates.items() if k not in _SECRET_KEYS}
            if secret_updates:
                self._write_env_fields(secret_updates, _root() / ".env", _root() / ".env.example")
            if defaults_updates:
                self._write_env_fields(defaults_updates, _root() / "config" / "defaults.env", None)
            self._send_json(200, {"ok": True})
        except Exception as exc:  # noqa: BLE001
            self._send_json(500, {"ok": False, "error": str(exc)})

    def _write_env_fields(self, updates: dict[str, str], env_path, fallback_path) -> None:
        """Update or add key=value pairs in the given env file.

        Falls back to fallback_path as a template when env_path is absent.
        """
        if env_path.exists():
            lines = env_path.read_text(encoding="utf-8").splitlines()
        elif fallback_path is not None and fallback_path.exists():
            lines = fallback_path.read_text(encoding="utf-8").splitlines()
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
