# /server

Start the dev server on localhost.

## Usage

```bash
/server          # start on http://localhost:8080
/server 9000     # start on http://localhost:9000
```

## What It Does

- Starts `python server.py [PORT]` from the project root
- Serves `ui/index.html` on `/` (single-page app)
- Proxies `/api/*` routes to handler methods in `app/server/`
- Logs to stdout with timestamp + level
- Ctrl+C to stop

## Endpoints

| Route | Handler |
|-------|---------|
| `/` | Serve `ui/index.html` |
| `/api/generate` | POST to generate reports |
| `/api/config` | GET/POST config, DELETE to reset |
| `/api/schemas` | GET/POST/DELETE Jira schema files |
| `/api/filters` | GET/POST/DELETE JQL filter presets |
| `/api/test-connection` | POST to test Jira credentials |
| `/api/cert-status` | GET certificate info |
| `/api/fetch-cert` | POST to fetch and validate cert |
| `/generated/reports/...` | Serve generated report HTML/MD files |

## Live Development

- Edit `ui/index.html`, `templates/report.html.j2`, or Python code
- Refresh browser or restart server to see changes
- Server runs in foreground; watch stdout for request logs

## Related

- `docs/development/architecture.md` — Module responsibilities
- `CLAUDE.md` — Extension Patterns → Extending the dev server
- `app/server/_base.py` — Routing and handler base class
