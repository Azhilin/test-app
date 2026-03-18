# Jira Metrics Report

Fetches data from Jira Cloud and generates metrics trend reports in HTML and Markdown (in parallel).

## Setup

1. Copy `.env.example` to `.env` and set:
   - `JIRA_URL` – e.g. `https://your-domain.atlassian.net`
   - `JIRA_EMAIL` – your Atlassian account email
   - `JIRA_API_TOKEN` – create at [Atlassian API tokens](https://id.atlassian.com/manage-profile/security/api-tokens)

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## Run

```bash
python main.py
```

Outputs: `report.html` and `report.md`.

Optional env vars: `JIRA_BOARD_ID`, `JIRA_SPRINT_COUNT`, `JIRA_STORY_POINTS_FIELD` (see `.env.example`).
