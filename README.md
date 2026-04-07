# AI Adoption Metrics Report

Fetches data from Jira Cloud and generates AI adoption and velocity trend reports in HTML and Markdown (in parallel).

## Setup

### Step 1 - Install Python, dependencies, and bootstrap config (run once)

Double-click **`project_setup.bat`**.

This will:

- Detect or install Python 3.12 (per-user, no admin rights needed)
- Create a `.venv` virtual environment
- Install all required packages from `requirements.txt`
- Optionally install dev dependencies (`pytest`, linters, etc.) and the Playwright Chromium browser (required for e2e tests)
- Create `.env` from `.env.example` when `.env` is missing
- Prompt to keep or back up and recreate `.env` when it already exists

### Step 2 - Configure Jira credentials

Open `.env` and fill in:

- `JIRA_URL` – e.g. `https://your-domain.atlassian.net`
- `JIRA_EMAIL` – your Atlassian account email
- `JIRA_API_TOKEN` – create at [Atlassian API tokens](https://id.atlassian.com/manage-profile/security/api-tokens)

That is all that `.env` needs. Non-sensitive settings (`JIRA_BOARD_ID`, `JIRA_SPRINT_COUNT`, `JIRA_SCHEMA_NAME`, AI labels, metric toggles, etc.) live in `config/defaults.env` — edit that file to change project-wide defaults.

## Run

### Using the browser UI (recommended)

Double-click **`start_app.bat`** — this starts a local server bound to `127.0.0.1` and opens the app in your browser at `http://localhost:8080`.

Use the UI to configure your Jira connection, select a filter, and generate reports.

If your Jira instance uses a custom CA certificate, use the Jira Connection tab to fetch it or place the PEM bundle at `certs/jira_ca_bundle.pem`.

## Troubleshooting

### Port 8080 already in use

If the server fails to start because port 8080 is occupied by a stale previous instance:

**Quick fix — use a different port:**

Open `config/defaults.env` (or add to `.env` to override) and change the `PORT` line:

```
PORT=9000
```

Then restart the server and open `http://localhost:9000` in your browser.

Alternatively, pass the port directly on the command line (overrides `.env`):

```bash
python server.py 9000
```

**Kill the stale process (Windows):**

1. Find the PID holding port 8080:
   ```
   netstat -ano | findstr :8080
   ```
   The last column is the PID.

2. Kill it:
   ```powershell
   # PowerShell - kill by PID
   Stop-Process -Id <PID> -Force
   
   # Kill all Python processes
   taskkill /IM python.exe /F
   
   # Kill by window title
   taskkill /FI "WINDOWTITLE eq *server.py*" /F
   
   # Or in PowerShell:
   Stop-Process -Name python -Force
   ```
   ```cmd
   :: Command Prompt
   taskkill /PID <PID> /F
   ```

3. Restart the server normally.
