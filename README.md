# AI Adoption Metrics Report

Fetches data from Jira Cloud and generates AI adoption and velocity trend reports in HTML and Markdown (in parallel).

## Setup

### Step 1 - Install Python, dependencies, and bootstrap config (run once)

Double-click **`project_setup.bat`**.

This will:

- Detect or install Python 3.12 (per-user, no admin rights needed)
- Create a `.venv` virtual environment
- Install all required packages from `requirements.txt`
- Create `.env` from `.env.example` when `.env` is missing
- Prompt to keep or back up and recreate `.env` when it already exists

### Step 2 - Configure Jira credentials

Open `.env` and fill in:

- `JIRA_URL` – e.g. `https://your-domain.atlassian.net`
- `JIRA_EMAIL` – your Atlassian account email
- `JIRA_API_TOKEN` – create at [Atlassian API tokens](https://id.atlassian.com/manage-profile/security/api-tokens)

Optional settings (see `.env.example` for details):
`JIRA_BOARD_ID`, `JIRA_SPRINT_COUNT`, `JIRA_SCHEMA_NAME`, `JIRA_FILTER_ID`,
`AI_ASSISTED_LABEL`, `AI_EXCLUDE_LABELS`, `AI_TOOL_LABELS`, `AI_ACTION_LABELS`

## Run

### Using the browser UI (recommended)

Double-click **`start_app.bat`** — this starts a local server bound to `127.0.0.1` and opens the app in your browser at `http://localhost:8080`.

Use the UI to configure your Jira connection, select a filter, and generate reports.

If your Jira instance uses a custom CA certificate, use the Jira Connection tab to fetch it or place the PEM bundle at `certs/jira_ca_bundle.pem`.
