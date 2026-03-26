# Confluence Authentication

This document describes how to authenticate against the Confluence Cloud REST API using the credentials already configured in this project.

---

## 1. Credential Reuse

The Confluence Cloud REST API uses the **same Atlassian account** as Jira Cloud. No additional credentials are required. The three env vars already in `.env` are sufficient:

| Env Var | Role |
|---------|------|
| `JIRA_URL` | Atlassian Cloud base URL, e.g. `https://your-domain.atlassian.net` — also the Confluence base URL |
| `JIRA_EMAIL` | Atlassian account email — used as the Basic auth username |
| `JIRA_API_TOKEN` | API token from Atlassian account — used as the Basic auth password |

> **Why the same URL?**  
> On Atlassian Cloud, Jira and Confluence share the same domain. Confluence REST API endpoints are served at `https://your-domain.atlassian.net/wiki/rest/api/` (v1) and `https://your-domain.atlassian.net/wiki/api/v2/` (v2).

---

## 2. Authentication Method: HTTP Basic Auth

Confluence Cloud REST APIs support **HTTP Basic Authentication** for direct API calls (scripts, integrations, and tools like this project). The `Authorization` header is constructed as:

```
Authorization: Basic base64(email:api_token)
```

### Example — raw header

```python
import base64

email = "user@example.com"
api_token = "your-api-token"
credentials = base64.b64encode(f"{email}:{api_token}".encode()).decode()
headers = {
    "Authorization": f"Basic {credentials}",
    "Content-Type": "application/json",
    "Accept": "application/json",
}
```

### Example — using atlassian-python-api (recommended)

The `Confluence` class handles Basic auth automatically when constructed with `username` and `password`:

```python
from atlassian import Confluence
from app import config

confluence = Confluence(
    url=config.JIRA_URL,
    username=config.JIRA_EMAIL,
    password=config.JIRA_API_TOKEN,
)
```

The library sets the `Authorization: Basic ...` header on every request. No manual header construction is needed.

---

## 3. Optional: Separate Confluence URL

In most Atlassian Cloud setups, Jira and Confluence share the same base URL. However, if your organisation uses a separate Confluence URL (rare), add an optional env var:

```ini
# .env.example addition
# Optional: Confluence base URL if different from JIRA_URL
# Defaults to JIRA_URL when not set.
# CONFLUENCE_URL=
```

```python
# app/config.py addition
CONFLUENCE_URL = os.getenv("CONFLUENCE_URL", "").rstrip("/") or JIRA_URL
```

The `Confluence` client is then initialised with `CONFLUENCE_URL` instead of `JIRA_URL`.

---

## 4. Optional: Default Space Key

Many Confluence operations require a space key. Add an optional env var to avoid hard-coding it:

```ini
# .env.example addition
# Optional: Default Confluence space key for read/write operations (e.g. TEAM)
# CONFLUENCE_SPACE_KEY=
```

```python
# app/config.py addition
CONFLUENCE_SPACE_KEY = os.getenv("CONFLUENCE_SPACE_KEY", "").strip() or None
```

---

## 5. Verifying Credentials

Use the `/wiki/rest/api/user/current` endpoint (v1) to confirm that credentials are valid and the account has Confluence access:

```python
from atlassian import Confluence
from app import config

confluence = Confluence(
    url=config.JIRA_URL,
    username=config.JIRA_EMAIL,
    password=config.JIRA_API_TOKEN,
)
me = confluence.get_user_details_by_username(config.JIRA_EMAIL)
print(me)
```

Or via a raw request:

```python
import requests, base64
from app import config

credentials = base64.b64encode(
    f"{config.JIRA_EMAIL}:{config.JIRA_API_TOKEN}".encode()
).decode()
response = requests.get(
    f"{config.JIRA_URL}/wiki/rest/api/user/current",
    headers={"Authorization": f"Basic {credentials}"},
)
response.raise_for_status()
print(response.json())
```

Expected response shape:

```json
{
  "type": "known",
  "accountId": "5b10a2844c20165700ede21g",
  "email": "user@example.com",
  "displayName": "Jane Smith",
  "profilePicture": { "path": "...", "width": 48, "height": 48, "isDefault": false },
  "isExternalCollaborator": false
}
```

---

## 6. Authentication for v2 Endpoints

The v2 REST API (`/wiki/api/v2/`) uses the same Basic auth mechanism. When making raw `_session` calls against v2 endpoints, the `atlassian-python-api` session already carries the correct `Authorization` header:

```python
# Raw v2 call using the session from an existing Confluence client
response = confluence._session.get(
    f"{config.JIRA_URL}/wiki/api/v2/spaces",
    params={"limit": 10},
)
response.raise_for_status()
data = response.json()
```

---

## 7. API Token Management

- Create or revoke tokens at: <https://id.atlassian.com/manage-profile/security/api-tokens>
- Tokens do not expire by default but can be revoked at any time.
- Store tokens in `.env` only — never commit them to version control.
- Official docs: <https://developer.atlassian.com/cloud/confluence/basic-auth-for-rest-apis/>

---

## 8. XSRF Protection

Some Confluence v1 endpoints (particularly `POST`/`PUT`/`DELETE`) require the `X-Atlassian-Token: no-check` header to bypass CSRF protection. The `atlassian-python-api` library adds this header automatically for mutating requests. For raw `_session` calls, add it manually:

```python
response = confluence._session.post(
    f"{config.JIRA_URL}/wiki/rest/api/content",
    json={...},
    headers={"X-Atlassian-Token": "no-check"},
)
```
