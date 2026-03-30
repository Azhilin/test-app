"""Connection handler mixin — /api/test-connection."""

from __future__ import annotations

import base64
import json
import urllib.error
import urllib.request


class ConnectionHandlerMixin:
    def _handle_test_connection(self) -> None:
        body = self._read_json_body()
        if body is None:
            self._send_json(400, {"ok": False, "error": "Invalid JSON body"})
            return

        url = (body.get("url") or "").strip().rstrip("/")
        email = (body.get("email") or "").strip()
        token = (body.get("token") or "").strip()

        if not url or not email or not token:
            self._send_json(400, {"ok": False, "error": "url, email, and token are required"})
            return

        if token == "***":  # nosec B105
            _, _, env_token = self._read_env_credentials()
            if not env_token:
                self._send_json(400, {"ok": False, "error": "No saved token on server"})
                return
            token = env_token

        endpoint = f"{url}/rest/api/3/myself"
        creds = base64.b64encode(f"{email}:{token}".encode()).decode()

        req = urllib.request.Request(
            endpoint,
            headers={"Authorization": f"Basic {creds}", "Accept": "application/json"},
        )

        try:
            with urllib.request.urlopen(req, timeout=12, context=self._jira_ssl_context()) as resp:  # nosec B310
                data = json.loads(resp.read())
                self._send_json(
                    200,
                    {
                        "ok": True,
                        "displayName": data.get("displayName", ""),
                        "emailAddress": data.get("emailAddress", ""),
                    },
                )
        except urllib.error.HTTPError as exc:
            self._send_json(
                200,
                {
                    "ok": False,
                    "httpStatus": exc.code,
                    "error": str(exc.reason),
                },
            )
        except urllib.error.URLError as exc:
            self._send_json(
                200,
                {
                    "ok": False,
                    "error": f"Could not reach Jira: {exc.reason}",
                },
            )
        except Exception as exc:  # noqa: BLE001
            self._send_json(500, {"ok": False, "error": str(exc)})
