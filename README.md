# AI Adoption Metrics Report

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

Reports are written to `reports/<timestamp>/` (e.g. `reports/2026-03-18T17-27-30/report.html` and `report.md`). Each run creates a new timestamped folder.

To remove all generated reports:

```bash
python remove_reports.py
```

Optional env vars: `JIRA_BOARD_ID`, `JIRA_SPRINT_COUNT`, `JIRA_STORY_POINTS_FIELD`, `JIRA_FILTER_ID` (see `.env.example`).
