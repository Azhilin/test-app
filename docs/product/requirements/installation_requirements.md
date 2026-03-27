# Installation Requirements — AI Adoption Metrics Report

This document describes how to obtain, install, and launch the AI Adoption Metrics Report tool from a release zip package. For a quickstart, see [`README.md`](../../../README.md). For software and hardware prerequisites, see [`technical_requirements.md`](technical_requirements.md).

---

## Table of Contents

1. [Zip Contents](#1-zip-contents)
2. [Installation — Windows](#2-installation--windows-recommended)
3. [Installation — macOS / Linux](#3-installation--macos--linux)
4. [Update / Reinstall](#4-update--reinstall)
5. [Troubleshooting](#5-troubleshooting)

---

## 1. Zip Contents

The release package is named `ai_adoption_manager_<YYYY-MM-DD_HH-mm-ss>.zip`. Below is what the archive contains and what is intentionally excluded.

### Included

| Path | Description |
|------|-------------|
| `app/` | Application source code |
| `templates/` | Jinja2 HTML report template |
| `ui/` | Browser UI files |
| `docs/product/schemas/` | Schema storage folder (may be empty) |
| `certs/` | Placeholder folder for optional SSL certificate; contains `README.txt` |
| `main.py` | CLI entry point |
| `server.py` | Browser UI server entry point |
| `requirements.txt` | Runtime Python dependencies |
| `.env.example` | Configuration template — copy to `.env` and fill in credentials |
| `project_setup.bat` | One-time Windows setup script |
| `start_app.bat` | Windows launcher |
| `README.md` | Quickstart guide |

### Not included

| Item | Reason |
|------|--------|
| `.venv/` | Created locally by `project_setup.bat` or manually |
| `generated/` | Created at runtime (reports, filters, logs) |
| `requirements-dev.txt` | Developer-only; not needed to run the app |
| Test files | Developer-only |
| `.env` | Never distributed; created from `.env.example` during setup |

---

## 2. Installation — Windows (Recommended)

### Step 1 — Extract the zip

1. Download the release zip (e.g. `ai_adoption_manager_2026-03-27_10-00-00.zip`).
2. Right-click the file → **Extract All…**
3. Choose a destination folder, for example `C:\Tools\ai_adoption_manager`.

> **Note:** Avoid paths that contain spaces or non-ASCII characters, as these can cause issues with Windows batch scripts.

### Step 2 — Run `project_setup.bat` (once)

Double-click **`project_setup.bat`** in the extracted folder.

The script performs the following steps automatically:

- **Python detection** — checks for Python 3.10–3.12 on the system PATH.
  - If a compatible version is found, it is used as-is.
  - If no Python is found or the version is outside the supported range, the script downloads and installs **Python 3.12.10** from python.org (per-user, no administrator rights required, SHA-256 checksum verified, TLS 1.2 enforced).
- **Virtual environment** — creates a `.venv/` folder inside the project directory.
- **Dependencies** — installs all packages from `requirements.txt` into the virtual environment.
- **Dev dependencies** *(optional)* — prompts whether to also install `requirements-dev.txt` (pytest and related tools). Answer **N** unless you plan to run the test suite.
- **`.env` bootstrap** — if no `.env` file exists, creates one from `.env.example`. If `.env` already exists, prompts you to keep it or back it up and recreate it.
- **Setup log** — writes a full timestamped log to `generated\logs\project_setup-<timestamp>.log`.

The script closes automatically after 10 seconds (or immediately on any keypress).

### Step 3 — Configure Jira credentials

Open **`.env`** in any text editor and fill in the three required values:

| Variable | Example | Description |
|----------|---------|-------------|
| `JIRA_URL` | `https://yourcompany.atlassian.net` | Base URL of your Jira Cloud site. No trailing slash. |
| `JIRA_EMAIL` | `you@example.com` | Email address of your Atlassian account. |
| `JIRA_API_TOKEN` | `ATATTxxxx…` | Personal API token. Create one at [Atlassian account security settings](https://id.atlassian.com/manage-profile/security/api-tokens). |

Alternatively, you can skip this step and enter credentials through the browser UI after launching (Jira Connection tab → Save).

**Optional — custom port:** Add `PORT=<number>` to `.env` to run the server on a port other than `8080`. This setting is persistent — `start_app.bat` will use it automatically on every launch.

### Step 4 — Launch the application

Double-click **`start_app.bat`**.

The local server starts and your default browser opens automatically at `http://localhost:8080`.

---

## 3. Installation — macOS / Linux

The release zip does not include launcher scripts for macOS or Linux. Follow these manual steps.

### Step 1 — Extract the zip

```bash
unzip ai_adoption_manager_<timestamp>.zip -d ~/ai_adoption_manager
cd ~/ai_adoption_manager
```

### Step 2 — Create a virtual environment

Python 3.10, 3.11, or 3.12 is required. Python 3.12 is recommended.

```bash
python3.12 -m venv .venv
```

If `python3.12` is not available, install it via your system package manager (e.g. `brew install python@3.12` on macOS, or `apt install python3.12` on Ubuntu/Debian) or from [python.org](https://www.python.org/downloads/).

### Step 3 — Install dependencies

```bash
.venv/bin/pip install -r requirements.txt
```

### Step 4 — Configure credentials

```bash
cp .env.example .env
```

Open `.env` in a text editor and fill in `JIRA_URL`, `JIRA_EMAIL`, and `JIRA_API_TOKEN` (see [Step 3 of the Windows instructions](#step-3--configure-jira-credentials) for details).

### Step 5 — Launch the application

```bash
.venv/bin/python server.py
```

Then open `http://localhost:8080` in a browser.

To use a different port **persistently** (survives restarts), set `PORT` in `.env` before launching:

```bash
echo "PORT=9000" >> .env
.venv/bin/python server.py
# Open http://localhost:9000
```

To override the port for a **single run** without editing `.env`:

```bash
.venv/bin/python server.py 9000
# Open http://localhost:9000
```

---

## 4. Update / Reinstall

When a new release zip is available, follow these steps to update.

### Windows

1. Extract the new zip to a folder (either a new location or the same folder as before).
2. Double-click **`project_setup.bat`** again.
   - The script detects the existing `.env` and prompts:
     - **`[K]` Keep** — your current credentials and settings are preserved unchanged.
     - **`[B]` Backup and recreate** — your existing `.env` is backed up to `.env.backup-<timestamp>` and a fresh `.env` is created from `.env.example`.
   - The virtual environment and dependencies are recreated to pick up any new packages.
3. Double-click **`start_app.bat`** to launch.

### macOS / Linux

1. Extract the new zip over the existing folder (or to a new location).
2. Re-run the dependency install to pick up any new or updated packages:
   ```bash
   .venv/bin/pip install -r requirements.txt
   ```
3. Your existing `.env` is preserved. If new configuration variables were added, compare `.env.example` with your `.env` and add any missing entries.
4. Launch with `.venv/bin/python server.py`.

---

## 5. Troubleshooting

| Problem | Likely cause | Resolution |
|---------|-------------|------------|
| `project_setup.bat` reports a Python version error | Python found on PATH is outside the supported range (3.10–3.12) | Allow the script to install Python 3.12.10, or install it manually from [python.org](https://www.python.org/downloads/) |
| Download fails during Python install | No internet access or firewall blocks `python.org` | Install Python 3.12 manually, then re-run `project_setup.bat` |
| `pip install` fails with an SSL error | Corporate proxy intercepts HTTPS traffic | Set `HTTP_PROXY` and `HTTPS_PROXY` environment variables before running the script, or ask IT for the trusted CA bundle |
| Port 8080 is already in use | Another process is listening on port 8080 | Set `PORT=9000` in `.env` for a persistent change (works with `start_app.bat`), or pass the port as a one-time CLI argument: `python server.py 9000`. Open the browser at the matching URL. |
| Browser shows "This site can't be reached" | Server is not running, or the URL/port does not match | Check that the `start_app.bat` console window is still open; verify the URL and port match |
| Jira connection test fails (red status) | Wrong credentials, missing `JIRA_URL`, or outbound HTTPS blocked | Verify `JIRA_URL` has no trailing slash; confirm the API token is valid; ensure outbound HTTPS to Jira Cloud (port 443) is not blocked by a firewall or proxy |
| SSL / TLS error when connecting to Jira | Jira uses a self-signed or private CA certificate not trusted by the OS | Open the Jira Connection tab → click **Fetch Certificate**, or place the PEM bundle manually at `certs/jira_ca_bundle.pem` |
| Setup log shows an unexpected error | Any failure during `project_setup.bat` | Open `generated\logs\project_setup-<timestamp>.log` for a full timestamped trace of what went wrong |
