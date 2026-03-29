"""Report generation and listing handler mixin — /api/generate (SSE), /api/reports."""

from __future__ import annotations

import os
import subprocess
import sys
from urllib.parse import parse_qs, urlparse
from urllib.parse import unquote as urlunquote

from ._base import _dotenv_values, _root


class GenerateHandlerMixin:
    def _handle_generate(self) -> None:
        """Run main.py and stream stdout/stderr as Server-Sent Events."""
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("X-Accel-Buffering", "no")  # disable nginx buffering
        self._cors_headers()
        self.end_headers()

        def emit(data: str, event: str = "message") -> None:
            try:
                if event != "message":
                    self.wfile.write(f"event: {event}\n".encode())
                for part in data.splitlines():
                    self.wfile.write(f"data: {part}\n".encode())
                self.wfile.write(b"\n")
                self.wfile.flush()
            except BrokenPipeError:
                # Client disconnected; ignore broken pipe during SSE write.
                pass

        try:
            root = _root()
            fresh_env = {**os.environ, **_dotenv_values(root / ".env")}

            qs = parse_qs(urlparse(self.path).query)
            filter_slug = urlunquote((qs.get("filter") or [""])[0]).strip()
            if filter_slug:
                _FILTER_PARAM_KEYS = [
                    "JIRA_PROJECT",
                    "JIRA_TEAM_ID",
                    "JIRA_ISSUE_TYPES",
                    "JIRA_FILTER_STATUS",
                    "JIRA_CLOSED_SPRINTS_ONLY",
                    "JIRA_FILTER_PAGE_SIZE",
                ]
                for _entry in self._load_filters():
                    if _entry.get("slug") == filter_slug:
                        _params = _entry.get("params") or {}
                        for _key in _FILTER_PARAM_KEYS:
                            _val = (_params.get(_key) or "").strip()
                            if _val:
                                fresh_env[_key] = _val
                        break

            proc = subprocess.Popen(
                [sys.executable, str(root / "main.py")],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=str(root),
                env=fresh_env,
            )
            for line in proc.stdout:
                emit(line.rstrip())
            proc.wait()

            if proc.returncode == 0:
                emit("__done__", "done")
            else:
                emit(f"__error__:Process exited with code {proc.returncode}", "error")
        except FileNotFoundError:
            emit("__error__:main.py not found — run from the project root", "error")
        except Exception as exc:  # noqa: BLE001
            emit(f"__error__:{exc}", "error")
        finally:
            try:
                self.wfile.write(b"event: close\ndata:\n\n")
                self.wfile.flush()
            except BrokenPipeError:
                pass

    def _handle_get_reports(self) -> None:
        """Return generated report folders, newest-first."""
        reports_dir = self._reports_dir()
        entries: list[dict[str, str]] = []
        if reports_dir.is_dir():
            for folder in sorted(reports_dir.iterdir(), reverse=True):
                if not folder.is_dir():
                    continue
                entries.append({"ts": folder.name, "html": "report.html", "md": "report.md"})
        self._send_json(200, {"reports": entries})
