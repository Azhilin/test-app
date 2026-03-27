# Technical Requirements — AI Adoption Metrics Report

This document describes the technical prerequisites for installing, running, and developing the AI Adoption Metrics Report tool. For a quickstart, see [`README.md`](../../../README.md).

---

## Table of Contents

1. [Operating System](#1-operating-system)
2. [Runtime Prerequisites](#2-runtime-prerequisites)
3. [Installation](#3-installation)
4. [Browser Requirements](#4-browser-requirements)
5. [Network Requirements](#5-network-requirements)
6. [Credentials & API Tokens](#6-credentials--api-tokens)
7. [SSL / TLS Certificate Support](#7-ssl--tls-certificate-support)

---

## 1. Operating System

| Platform | Status | Notes |
|----------|--------|-------|
| Windows 10 / 11 | **Primary — fully supported** | `project_setup.bat` and `start_app.bat` launchers included; Python auto-install supported |
| macOS | Supported | Manual virtual environment setup required; no launcher scripts |
| Linux | Supported | Manual virtual environment setup required; no launcher scripts |

---

## 2. Runtime Prerequisites

### End-user

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | 3.12 or later | `project_setup.bat` installs Python 3.12 per-user on Windows (no admin rights needed); on macOS/Linux, install via system package manager or [python.org](https://www.python.org/downloads/) |
| pip | Bundled with Python 3.12+ | No separate install required |

Runtime packages (installed from `requirements.txt`):

| Package | Minimum Version | Role |
|---------|----------------|------|
| `atlassian-python-api` | 3.41.0 | Jira Cloud REST client (boards, sprints, issues, changelogs) |
| `python-dotenv` | 1.0.0 | `.env` configuration file loading |
| `jinja2` | 3.1.0 | HTML report templating |
| `requests` | 2.28.0 | HTTP library (transitive dependency) |
| `pandas` | 2.0.0 | Available for future metric computation (not used in core pipeline) |
| `cryptography` | 42.0.0 | PEM certificate validation |

### Developer (additional)

Dev packages (installed from `requirements-dev.txt`, which includes all runtime packages):

| Package | Minimum Version | Role |
|---------|----------------|------|
| `pytest` | 8.0.0 | Test runner |
| `pytest-mock` | 3.12.0 | `mocker` fixture for mocking |
| `pytest-playwright` | 0.6.2 | Browser-based E2E tests |
| `pytest-cov` | 5.0.0 | Test coverage reporting |
| `ruff` | 0.9.0 | Linting and formatting |

E2E tests also require a Chromium browser installed via Playwright:

```bash
.venv/Scripts/playwright install chromium   # Windows
.venv/bin/playwright install chromium       # macOS / Linux
```

---

## 3. Installation

### End-user — Windows

Double-click **`project_setup.bat`**. This script:
- Detects or installs Python 3.12 (per-user, no admin rights required)
- Creates a `.venv` virtual environment in the project root
- Installs all packages from `requirements.txt`
- Creates `.env` from `.env.example` if `.env` does not yet exist

### End-user — macOS / Linux

```bash
python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env          # then edit .env with your Jira credentials
```

### Developer

```bash
python3.12 -m venv .venv

# Windows
.venv\Scripts\pip install -r requirements-dev.txt
.venv\Scripts\playwright install chromium

# macOS / Linux
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/playwright install chromium
```

### Starting the application

| Method | Command |
|--------|---------|
| Windows launcher | Double-click `start_app.bat` — starts the server and opens `http://localhost:8080` |
| Cross-platform | `python server.py` — port from `PORT` in `.env` or default `8080`; pass a number (e.g. `python server.py 9000`) to override for a single run |
| CLI only (no UI) | `python main.py` — generates reports directly to `generated/reports/` |

---

## 4. Browser Requirements

The browser UI is served at `http://localhost:8080` by a local HTTP server. No internet connection is required to load the UI itself.

### Supported browsers

| Browser | Minimum Version |
|---------|----------------|
| Google Chrome / Chromium | 90+ |
| Microsoft Edge | 90+ |
| Mozilla Firefox | 88+ |
| Safari | 14+ |

### Browser configuration requirements

- **JavaScript must be enabled.** The UI relies on vanilla JavaScript and the Chart.js library (loaded inline from the report HTML).
- **`localhost` must not be blocked.** Some browser extensions (ad-blockers, privacy tools) may intercept requests to `http://localhost`. Disable such extensions for `localhost` if the UI fails to load or API calls do not reach the server.
- **The configured port must be free.** The default port is `8080`. To use a different port persistently, set `PORT=<number>` in `.env` — this applies to all launch methods including `start_app.bat`. To override for a single run only, pass the port as a CLI argument (`python server.py 9000`). Open the browser at the matching URL in both cases.

---

## 5. Network Requirements

| Requirement | Detail |
|-------------|--------|
| Outbound HTTPS to Jira Cloud (port 443) | **Required.** The tool connects directly from the local machine to the Jira Cloud instance specified in `JIRA_URL` (e.g. `https://yourcompany.atlassian.net`). This connection must not be blocked by a firewall or corporate proxy. |
| `localhost` port availability | Default port `8080` must be free on `127.0.0.1`. Configurable via `PORT=<number>` in `.env` (persistent — applies to all launch methods) or as a CLI argument to `server.py` (single run only). |
| No inbound rules required | The HTTP server binds to `127.0.0.1` (loopback) by default and is not reachable from other machines. |
| Proxy support | Not natively configured. OS-level proxy environment variables (`HTTP_PROXY`, `HTTPS_PROXY`) may be honoured by the underlying HTTP client depending on the system configuration. |

---

## 6. Credentials & API Tokens

Three values are required to connect to Jira Cloud. All three must be present in the `.env` file before generating a report.

| Credential | Variable | How to obtain |
|------------|----------|---------------|
| Jira site URL | `JIRA_URL` | Base URL of your Jira Cloud site — e.g. `https://yourcompany.atlassian.net`. No trailing slash. |
| Atlassian account email | `JIRA_EMAIL` | The email address of the Atlassian account that has at minimum **read access** to the boards and projects you want to report on. |
| API token | `JIRA_API_TOKEN` | A personal API token generated at [Atlassian account security settings](https://id.atlassian.com/manage-profile/security/api-tokens). This is not your Atlassian password. |

### Storage and security

- Credentials are stored in `.env` in the project root (local machine only).
- `.env` is listed in `.gitignore` — credentials are never committed to version control.
- The API token is masked as `***` in all server API responses (e.g. `GET /api/config`).
- Credentials are transmitted only to the Jira URL specified in `JIRA_URL` — never to any third party.

### Entering credentials

Credentials can be set in two ways:
1. **Browser UI** — Jira Connection tab → fill in the fields → click **Save**.
2. **Direct file edit** — copy `.env.example` to `.env` and fill in the three values manually.

---

## 7. SSL / TLS Certificate Support

Relevant only when connecting to a Jira instance that uses a self-signed or privately issued CA certificate not trusted by the operating system's certificate store (common in on-premise or air-gapped environments).

### How to provide the certificate

| Method | Steps |
|--------|-------|
| **Auto-fetch via UI** | Open the Jira Connection tab → scroll to the **SSL / TLS Certificate** section → click **Fetch Certificate**. The server downloads the certificate from the host in `JIRA_URL` and saves it automatically. |
| **Auto-fetch via CLI** | Run `python tools/fetch_ssl_cert.py` from the project root. |
| **Manual placement** | Obtain the PEM bundle from your network or security team and place it at `certs/jira_ca_bundle.pem` in the project root. |

### Behaviour when the bundle is present

- The config module (`app/core/config.py`) detects `certs/jira_ca_bundle.pem` at startup and passes its path as the `verify_ssl` argument to the Jira client.
- Certificate validity (expiry date, days remaining, subject) is visible in the Jira Connection tab under the SSL / TLS Certificate section.
- If the certificate has expired or is invalid, a warning is shown; the Jira connection may still succeed if the OS trusts the CA by other means.
