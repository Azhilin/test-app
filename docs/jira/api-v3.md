# Jira Platform REST API v3

**Official reference:** <https://developer.atlassian.com/cloud/jira/platform/rest/v3/intro/>  
**OpenAPI spec:** <https://dac-static.atlassian.com/cloud/jira/platform/swagger.v3.json>

---

## 1. About v3

Jira Platform REST API v3 is the **current recommended version** for new integrations. It exposes the same operations as v2 with one key difference: rich text fields (descriptions, comments, etc.) are returned and accepted in [Atlassian Document Format (ADF)](https://developer.atlassian.com/cloud/jira/platform/apis/document/structure/) rather than plain strings.

**Base URL:**

```
https://<your-domain>.atlassian.net/rest/api/3/
```

---

## 2. v2 vs v3 Differences

| Aspect | v2 | v3 |
|--------|----|----|
| Rich text fields | Plain string | ADF JSON object |
| Operation coverage | Full | Full (same as v2) |
| Recommendation | Stable, widely supported | Recommended for new integrations |
| `description` field | `"string value"` | `{"type":"doc","version":1,"content":[...]}` |
| `comment.body` field | `"string value"` | ADF object |

**When to prefer v2:** When you only need to read/write plain text and want simpler response handling (as this project does).  
**When to prefer v3:** When building a UI that renders rich text, or when creating/updating issue descriptions and comments programmatically.

---

## 3. Authentication

See [authentication.md](authentication.md). v3 uses the same Basic auth scheme as v2.

---

## 4. Endpoints Used by This Project

### 4.1 GET /rest/api/3/myself — Get Current User

**Used in:** `server.py` `_handle_test_connection()` — validates that credentials are correct before saving them.

**Official docs:** <https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-myself/#api-rest-api-3-myself-get>

**Request:**

```
GET https://<your-domain>.atlassian.net/rest/api/3/myself
Authorization: Basic <base64(email:token)>
Accept: application/json
```

No path or query parameters.

**Response (200 OK):**

```json
{
  "accountId": "5b10a2844c20165700ede21g",
  "accountType": "atlassian",
  "emailAddress": "user@example.com",
  "displayName": "Mia Kramer",
  "active": true,
  "timeZone": "Australia/Sydney",
  "locale": "en_AU",
  "groups": {
    "size": 3,
    "items": []
  },
  "applicationRoles": {
    "size": 1,
    "items": []
  },
  "self": "https://your-domain.atlassian.net/rest/api/3/user?accountId=5b10a2844c20165700ede21g"
}
```

**How it is called in this project (`server.py`):**

```python
import base64, urllib.request, json

endpoint = f"{url}/rest/api/3/myself"
creds    = base64.b64encode(f"{email}:{token}".encode()).decode()

req = urllib.request.Request(
    endpoint,
    headers={"Authorization": f"Basic {creds}", "Accept": "application/json"},
)
with urllib.request.urlopen(req, timeout=12) as resp:
    data = json.loads(resp.read())
    # data["displayName"], data["emailAddress"]
```

**Error responses:**

| Code | Meaning |
|------|---------|
| `200` | Credentials valid; body contains user info |
| `401` | Invalid credentials |
| `403` | User exists but does not have Jira access |

---

## 5. ADF (Atlassian Document Format) Overview

When using v3 to create or update issues with rich text, the `description` and `comment.body` fields must be ADF objects:

```json
{
  "description": {
    "type": "doc",
    "version": 1,
    "content": [
      {
        "type": "paragraph",
        "content": [
          {
            "type": "text",
            "text": "This is the issue description."
          }
        ]
      }
    ]
  }
}
```

**ADF reference:** <https://developer.atlassian.com/cloud/jira/platform/apis/document/structure/>

This project does not currently create or update issue descriptions, so ADF is not relevant to the current implementation. If you add write operations, use v3 with ADF for rich text fields.

---

## 6. Pagination, Status Codes, and Headers

Identical to v2. See [api-v2.md — Pagination](api-v2.md#4-pagination), [Status Codes](api-v2.md#6-status-codes), and [Special Headers](api-v2.md#7-special-request-headers).

---

## 7. Key v3 Endpoints for Future Use

| Endpoint | Description |
|----------|-------------|
| `GET /rest/api/3/myself` | Get authenticated user (used by this project) |
| `GET /rest/api/3/issue/{issueIdOrKey}` | Get issue (ADF rich text) |
| `POST /rest/api/3/issue` | Create issue with ADF description |
| `PUT /rest/api/3/issue/{issueIdOrKey}` | Update issue fields |
| `GET /rest/api/3/search` | JQL search |
| `GET /rest/api/3/project` | List projects |
| `GET /rest/api/3/user` | Get user by account ID |
| `GET /rest/api/3/filter/{id}` | Get saved filter (v3 equivalent of the v2 call in `main.py`) |

For full CRUD details on all entities, see [crud-operations.md](crud-operations.md).
