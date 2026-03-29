# Jira Authentication

**Official reference:** <https://developer.atlassian.com/cloud/jira/platform/basic-auth-for-rest-apis/>

This project uses **HTTP Basic Authentication** with an Atlassian account email address and an API token. Password-based authentication is deprecated by Atlassian.

---

## 1. Create an API Token

1. Log in to your Atlassian account at <https://id.atlassian.com/manage/api-tokens>.
2. Click **Create API token**.
3. Give the token a descriptive label (e.g. `metrics-report-script`).
4. Copy the token immediately — it is shown only once.

> **Security note:** Basic auth is suitable for personal scripts and bots. For production integrations consider [OAuth 2.0 (3LO)](https://developer.atlassian.com/cloud/jira/platform/oauth-2-3lo-apps/), which is more secure and supports scoped access.

---

## 2. Basic Auth Header Construction

The `Authorization` header value is `Basic <base64(email:token)>`.

**Linux / macOS:**

```bash
echo -n "user@example.com:your_api_token" | base64
# → dXNlckBleGFtcGxlLmNvbTp5b3VyX2FwaV90b2tlbg==
```

**Windows PowerShell:**

```powershell
$Text  = "user@example.com:your_api_token"
$Bytes = [System.Text.Encoding]::UTF8.GetBytes($Text)
[Convert]::ToBase64String($Bytes)
```

**curl example:**

```bash
curl -u user@example.com:your_api_token \
     -H "Accept: application/json" \
     "https://your-domain.atlassian.net/rest/api/3/myself"
```

---

## 3. How Credentials Flow Through This Codebase

### 3.1 `.env` Configuration

All credentials are stored in `.env` (never committed to source control):

```ini
JIRA_URL=https://your-domain.atlassian.net
JIRA_EMAIL=user@example.com
JIRA_API_TOKEN=your_api_token_here
```

`app/config.py` loads these at module import time via `python-dotenv`:

```python
JIRA_URL        = os.getenv("JIRA_URL", "").rstrip("/")
JIRA_EMAIL      = os.getenv("JIRA_EMAIL", "")
JIRA_API_TOKEN  = os.getenv("JIRA_API_TOKEN", "")
```

### 3.2 `atlassian-python-api` Client (`app/jira_client.py`)

```python
from atlassian import Jira
from app import config

def create_client() -> Jira:
    return Jira(
        url=config.JIRA_URL,
        username=config.JIRA_EMAIL,
        password=config.JIRA_API_TOKEN,   # API token used as password
    )
```

The library constructs `Authorization: Basic <base64(email:token)>` internally and attaches it to every request via a `requests.Session`.

### 3.3 Raw HTTP Request (`main.py`)

When `JIRA_FILTER_ID` is set, `main.py` reuses the authenticated session from the library client:

```python
f = jira._session.get(
    f"{config.JIRA_URL}/rest/api/2/filter/{config.JIRA_FILTER_ID}"
).json()
```

The `_session` object already has the `Authorization` header set by the library.

### 3.4 Connection Test (`server.py`)

The dev server's `/api/test-connection` endpoint constructs Basic auth manually:

```python
import base64, urllib.request

creds = base64.b64encode(f"{email}:{token}".encode()).decode()
req = urllib.request.Request(
    f"{url}/rest/api/3/myself",
    headers={"Authorization": f"Basic {creds}", "Accept": "application/json"},
)
```

---

## 4. Required Permissions

The authenticated user must have at minimum:

| Permission | Required For |
|-----------|-------------|
| **Browse Projects** | Reading issues, sprints, boards |
| **View (Read) Filters** | Fetching saved filter JQL (`JIRA_FILTER_ID`) |
| **Jira Software access** | Accessing Agile boards and sprints |

---

## 5. Security Considerations

| Topic | Guidance |
|-------|----------|
| Token storage | Store in `.env`; never commit to git (`.env` is in `.gitignore`) |
| Token scope | API tokens have the same permissions as the user account — use a dedicated service account with minimal permissions for production |
| CAPTCHA lockout | After several failed login attempts Jira triggers CAPTCHA; the REST API returns `X-Seraph-LoginReason: AUTHENTICATION_DENIED` — revoke and regenerate the token |
| Token rotation | Revoke and regenerate tokens regularly at <https://id.atlassian.com/manage/api-tokens> |
| Upgrade path | Migrate to [OAuth 2.0 (3LO)](https://developer.atlassian.com/cloud/jira/platform/oauth-2-3lo-apps/) for multi-user or production deployments |

---

## 6. Validate Configuration

Run the built-in validator before executing the pipeline:

```python
from app import config

errors = config.validate_config()
if errors:
    for e in errors:
        print(f"Config error: {e}")
```

`validate_config()` checks that `JIRA_URL`, `JIRA_EMAIL`, and `JIRA_API_TOKEN` are all non-empty.
