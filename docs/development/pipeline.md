# CI Pipeline — Operations Guide

## Overview

The pipeline lives in [`.github/workflows/ci.yml`](../.github/workflows/ci.yml).  
It runs on **every push and pull request** to every branch.

**Most stages are disabled by default** — integration, e2e, windows, and security
tests do not run until you explicitly enable them. However, **three jobs always
run regardless of settings:**
- `lint` (ruff check + format) — unconditional
- `unit-tests` and `component-tests` — always run on pull requests (though gated by `ENABLE_*` variables on push events)

Optional stages are enabled independently via **GitHub repository Variables** (no
YAML edits required) or toggled per-run via **workflow_dispatch** inputs.

---

## Pipeline Architecture

```
Push / PR / Manual trigger
         │
         ▼
┌──────────────────────────────────────────────────────────┐
│                    CI Workflow                          │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │         lint (ruff)  — always runs               │   │
│  │      ubuntu-latest — no gatekeeping              │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
│  ┌─────────────────┐  ┌─────────────────┐               │
│  │  unit-tests     │  │ component-tests │ ubuntu-latest│
│  │   (always on PR)│  │  (always on PR) │               │
│  │   115 tests     │  │    76 tests     │               │
│  └─────────────────┘  └─────────────────┘               │
│                                                          │
│  ┌──────────────────┐  ┌──────────────────────────┐    │
│  │integration-tests │  │      e2e-tests           │    │
│  │   6 tests        │  │  43 tests (Playwright)   │    │
│  │ (Jira secrets)   │  │  (Jira secrets)          │    │
│  └──────────────────┘  └──────────────────────────┘    │
│                                                          │
│  ┌─────────────────┐  ┌─────────────────┐              │
│  │ windows-tests   │  │ security-scan   │              │
│  │(windows-latest) │  │  (pip-audit)    │              │
│  └─────────────────┘  └─────────────────┘              │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │   allure-report (if ≥1 test didn't skip)       │    │
│  │   Generate + deploy HTML to GitHub Pages       │    │
│  └────────────────────────────────────────────────┘    │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │     ci-summary  (always runs, aggregates all)  │    │
│  └────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────┘
```

**Dependency flow:**
- `lint` runs independently (no gate).
- `unit-tests` and `component-tests` always run on PRs (regardless of `ENABLE_*` variables); on push events they are gated by `ENABLE_UNIT` and `ENABLE_COMPONENT`.
- Other test jobs and `security-scan` are independently gated by their `ENABLE_*` variables or manual `workflow_dispatch` inputs.
- `allure-report` waits for at least one of the four test jobs (unit/component/integration/e2e) and only runs if ≥1 of them was not skipped.
- `ci-summary` waits for all of them (including `lint` and `allure-report`).

---

## Enabling / Disabling Stages

### Automatic runs (push / pull request)

Navigate to **GitHub → Settings → Variables → Actions** and create or update the
corresponding repository variable.

| Variable | Stage | Runner | Note |
|---|---|---|---|
| (none) | Lint (ruff) | ubuntu-latest | Always runs — no variable to gate |
| `ENABLE_UNIT` | Unit Tests | ubuntu-latest | Always runs on PRs; gated by variable on push |
| `ENABLE_COMPONENT` | Component Tests | ubuntu-latest | Always runs on PRs; gated by variable on push |
| `ENABLE_INTEGRATION` | Integration Tests | ubuntu-latest | Requires Jira secrets |
| `ENABLE_E2E` | E2E Tests (Playwright) | ubuntu-latest | Requires Jira secrets |
| `ENABLE_WINDOWS_TESTS` | Windows-specific Tests | windows-latest | |
| `ENABLE_SECURITY_SCAN` | Security Scan (pip-audit) | ubuntu-latest | |

Set the value to the **string** `true` to enable, or remove/set to anything else
to disable.

> **Important:** On **pull requests**, `unit-tests` and `component-tests` always
> run **regardless of `ENABLE_UNIT` and `ENABLE_COMPONENT` variables**. The
> "disabled by default" statement applies to **push events only**. This ensures
> PRs are always validated before merge.

### Recommended enablement order

Enable stages incrementally rather than all at once. This surfaces problems one
layer at a time and avoids burning Windows/Playwright runner minutes on a broken
build.

| Step | Enable | Why this order |
|---|---|---|
| 1 | `ENABLE_UNIT` | Fastest feedback (~30 s), zero secrets needed |
| 2 | `ENABLE_COMPONENT` | Still no secrets, covers HTTP + templates |
| 3 | `ENABLE_SECURITY_SCAN` | No secrets, good hygiene before adding external calls |
| 4 | `ENABLE_INTEGRATION` | Add Jira secrets first (see [Jira Secrets Setup](#jira-secrets-setup)) |
| 5 | `ENABLE_E2E` | Slowest ubuntu job (~3–5 min), needs Jira secrets + Playwright |
| 6 | `ENABLE_WINDOWS_TESTS` | Dedicated windows-latest runner — enable after Steps 1–2 are stable |

Verify the pipeline is green at each step before proceeding to the next.

### Stage cost and speed reference

GitHub-hosted runner minutes are billed at different rates. Keeping expensive
stages conditional protects runner budget.

| Stage | Typical duration | Runner | Relative cost | Secrets needed |
|---|---|---|---|---|
| Unit Tests | ~30 s | ubuntu-latest | ★☆☆☆☆ | No |
| Component Tests | ~30 s | ubuntu-latest | ★☆☆☆☆ | No |
| Security Scan | ~45 s | ubuntu-latest | ★☆☆☆☆ | No |
| Integration Tests | ~1–2 min | ubuntu-latest | ★★☆☆☆ | Yes |
| E2E Tests | ~3–5 min | ubuntu-latest | ★★★☆☆ | Yes |
| Windows Tests | ~2–4 min | windows-latest | ★★★★☆ (2× rate) | No |

> **Tip:** If runner minutes are limited, keep `ENABLE_WINDOWS_TESTS` and
> `ENABLE_E2E` disabled on feature branches and enable them only on `master`
> using the `RESTRICT_TO_MASTER` flag per stage (see below).

### Manual one-off runs

1. Go to **Actions → CI → Run workflow**
2. Select the branch
3. Toggle the boolean inputs for the stages you want to run
4. Click **Run workflow**

Manual runs ignore the `RESTRICT_TO_MASTER` flag (see below).

---

## Restricting Automatic Runs to Master Only

By default every branch triggers a run (stages will still only run if the
corresponding `ENABLE_*` variable is `true`).

To additionally skip all automatic runs on non-master branches:

**GitHub → Settings → Variables → Actions → `RESTRICT_TO_MASTER` = `true`**

| Scenario | unit-tests on a feature branch |
|---|---|
| `RESTRICT_TO_MASTER` not set | Runs if `ENABLE_UNIT == 'true'` |
| `RESTRICT_TO_MASTER = true` | Skipped (yellow dash) |
| Manual `workflow_dispatch` | Always runs regardless of this flag |

> **Warning:** Setting `RESTRICT_TO_MASTER = true` blocks **all** stages on
> **all** non-master branches, including open PRs. Use this only if you
> intentionally want CI to run exclusively on merges to master.
> For most projects, leaving this unset and relying on
> `ENABLE_*` variables gives finer control.

### Common configuration strategies

Choose the pattern that matches your workflow:

**Fast feedback on every commit (recommended starting point)**
```
ENABLE_UNIT          = true
ENABLE_COMPONENT     = true
ENABLE_SECURITY_SCAN = true
# All other stages disabled — run Integration/E2E manually or on master only
```

**Full CI on every branch (requires Jira secrets already configured)**
```
ENABLE_UNIT          = true
ENABLE_COMPONENT     = true
ENABLE_INTEGRATION   = true
ENABLE_E2E           = true
ENABLE_SECURITY_SCAN = true
ENABLE_WINDOWS_TESTS = true
# RESTRICT_TO_MASTER  — leave unset
```

**Save runner minutes: cheap stages on every branch, slow stages on master only**
```
ENABLE_UNIT          = true   # runs on every branch
ENABLE_COMPONENT     = true   # runs on every branch
ENABLE_SECURITY_SCAN = true   # runs on every branch
ENABLE_INTEGRATION   = true   # gated by RESTRICT_TO_MASTER below
ENABLE_E2E           = true   # gated by RESTRICT_TO_MASTER below
ENABLE_WINDOWS_TESTS = true   # gated by RESTRICT_TO_MASTER below
RESTRICT_TO_MASTER   = true   # Integration, E2E, Windows only run on master
```
> This pattern is not yet supported per-stage — `RESTRICT_TO_MASTER` applies
> globally. Implement per-stage branch filtering by editing the `if:` condition
> in `ci.yml` if you need finer control.

**Disable everything temporarily (e.g. during a repo migration)**
```
# Remove all ENABLE_* variables, or set each to any value other than 'true'
# Manual workflow_dispatch runs will still work
```

---

## Stage Details

### Unit Tests

- **Marker:** `unit and not windows_only`
- **Runner:** `ubuntu-latest`
- **What it covers:** Pure-function tests, no I/O — config loading, metrics
  computation, Jira client (mocked), module imports
- **Jira secrets required:** No
- **Artifacts:** `unit-results` (JUnit XML) + `allure-results-unit-<run_id>` (Allure results)

### Component Tests

- **Marker:** `component and not windows_only`
- **Runner:** `ubuntu-latest`
- **What it covers:** Filesystem and HTTP — HTML template rendering, Markdown
  generation, HTTP routes/CORS/SSE, data contracts
- **Jira secrets required:** No
- **Artifacts:** `component-results` (JUnit XML) + `allure-results-component-<run_id>` (Allure results)

### Integration Tests

- **Marker:** `integration and not windows_only`
- **Runner:** `ubuntu-latest`
- **What it covers:** Full pipeline with mocked I/O, filter flow, server
  integration
- **Jira secrets required:** Yes — see [Jira Secrets Setup](#jira-secrets-setup)
- **Artifacts:** `integration-results` (JUnit XML) + `allure-results-integration-<run_id>` (Allure results)

### E2E Tests

- **Marker:** `e2e and not windows_only`
- **Runner:** `ubuntu-latest`
- **What it covers:** CLI subprocess, server health, Playwright browser UI
  interactions (Chromium)
- **Jira secrets required:** Yes — see [Jira Secrets Setup](#jira-secrets-setup)
- **Browser caching:** Chromium binary is cached in `~/.cache/ms-playwright`,
  keyed to the hash of `requirements-dev.txt`
- **Artifacts:** `e2e-results` (JUnit XML) + `allure-results-e2e-<run_id>` (Allure results)

### Windows-specific Tests

- **Marker:** `windows_only`
- **Runner:** `windows-latest` (2× slower and 2× more expensive than ubuntu;
  only enable when validating Windows-specific OS behaviour)
- **What it covers:** Tests decorated with
  `@pytest.mark.windows_only` and `@pytest.mark.skipif(sys.platform != "win32")`
  — specifically the `Server.handle_error` suppression of
  `ConnectionAbortedError` (WinSock error `WSAECONNABORTED`)
- **Jira secrets required:** No
- **Artifact:** `windows-results` (JUnit XML only; no Allure results for this job)

### Security Scan

- **What it does:** Runs `pip-audit -r requirements.txt` against known CVE
  databases for all production dependencies
- **Runner:** `ubuntu-latest`
- **Jira secrets required:** No
- **Note:** Only production deps are scanned (`requirements.txt`). Dev-only
  packages (pytest, Playwright) are not included to reduce noise.

### Lint

- **What it does:** Runs `ruff check` and `ruff format --check` on `app/` and `tests/`
- **Runner:** `ubuntu-latest`
- **Always runs:** Yes — this job has **no `if:` condition**; it runs on every push, PR, and manual trigger unconditionally
- **Jira secrets required:** No
- **Note:** Lint is not gateable via `ENABLE_*` variables or `RESTRICT_TO_MASTER`. To enforce passing lint before merge, use the Branch Protection rules (see below).

### Allure Report

- **What it does:** Merges per-layer Allure test result artifacts, generates an HTML report with trend history, and deploys to GitHub Pages
- **When it runs:** Only when **at least one of unit/component/integration/e2e jobs was not skipped** (if all test jobs are skipped, Allure Report is also skipped)
- **Runner:** `ubuntu-latest`
- **Deployment:** Merges reports into `allure-history` and deploys to the `gh-pages` branch
- **Artifact retention:** Keeps the last 20 reports
- **Permissions required:** `contents: write` (needed to push to `gh-pages`)
- **Jira secrets required:** No
- **Note:** Allure reports are only generated if tests actually ran. If you want to download raw test results, use the JUnit XML artifacts (see Test Results Artifacts below).

---

## Jira Secrets Setup

Integration and E2E stages expose Jira credentials as environment variables.
Secrets must be added before enabling those stages.

**GitHub → Settings → Secrets → Actions → New repository secret**

| Secret name | Value |
|---|---|
| `JIRA_URL` | `https://your-org.atlassian.net` |
| `JIRA_EMAIL` | `your@email.com` |
| `JIRA_API_TOKEN` | Atlassian API token (create at id.atlassian.com) |

If the secrets are absent, the environment variables will be empty strings.
Tests that require a live Jira connection will fail or be marked as skipped
depending on each test's setup.

---

## Concurrency

The workflow uses a `concurrency` group keyed to `github.ref`:

```yaml
concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: true
```

If you push two commits to the same branch in quick succession, the in-flight
run for the first commit is cancelled automatically.

---

## Branch Protection (Recommended)

To require Lint + Unit + Component tests to pass before merging a PR to master:

1. **GitHub → Settings → Branches → Add rule → Branch name: `master`**
2. Enable **"Require status checks to pass before merging"**
3. Search for and add:
   - `Lint (ruff)` — safe to require; always runs
   - `Unit Tests` — runs on all PRs
   - `Component Tests` — runs on all PRs
4. Enable **"Require branches to be up to date before merging"**

**Note:** `Lint (ruff)` is safe to require without enabling any variables because it runs unconditionally on every push/PR. Unit and Component tests always run on PRs (regardless of `ENABLE_UNIT`/`ENABLE_COMPONENT` variables), so they are also safe to require as branch protection rules.

---

## Dependabot

[`.github/dependabot.yml`](../.github/dependabot.yml) is configured to open
weekly PRs for:

- **pip** — production and dev Python dependencies
- **github-actions** — action versions (`actions/checkout`, `actions/setup-python`, etc.)

PRs are labelled `dependencies` and capped at 5 open PRs per ecosystem.

> **Recommendation:** Keep `ENABLE_UNIT = true` and `ENABLE_COMPONENT = true`
> so that Dependabot PRs are automatically validated before you merge them.
> This catches dependency updates that break the API surface without requiring
> manual test runs.

---

## Troubleshooting

### A stage shows as a yellow dash (skipped)

The job's `if:` condition evaluated to `false`. Check in order:
1. Is the matching `ENABLE_*` variable set to the exact string `true` (not `True`, `yes`, or `1`)?
2. Is `RESTRICT_TO_MASTER = true` active and the push is on a non-master branch?
3. Did the workflow file get pushed? Go to **Actions** tab — if the workflow is not listed, the YAML was never pushed to the default branch or the current branch.

### A stage shows as expected but never starts

- Check **Actions → CI → the run** — expand the job to see the evaluated `if:` expression.
- Variables are case-sensitive: `ENABLE_UNIT` ≠ `enable_unit`.

### Integration or E2E fails with authentication errors

- Confirm all three secrets exist: `JIRA_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN`.
- Secret names are case-sensitive. Check for trailing spaces in the value.
- Re-run the job after correcting secrets; no commit is needed.

### E2E fails with `SSL: CERTIFICATE_VERIFY_FAILED`

The local `certs/jira_ca_bundle.pem` is excluded from git (`.gitignore`). If
your Jira instance uses a custom CA not trusted by ubuntu-latest:

1. Add the PEM content as a new secret: `JIRA_CA_BUNDLE`
2. Add a step before the E2E test step in `ci.yml`:
   ```yaml
   - name: Write CA bundle
     run: echo "${{ secrets.JIRA_CA_BUNDLE }}" > certs/jira_ca_bundle.pem
   ```

### Windows Tests are skipped on ubuntu-latest

This is expected. Tests decorated with `@pytest.mark.windows_only` are
excluded by the `-m "... and not windows_only"` marker filter on all ubuntu
jobs. They only run in the dedicated `windows-tests` job.

---

## Test Results Artifacts

Every test job uploads artifacts after completion, whether tests passed or failed.
Retention follows repository defaults (typically 90 days).

To download:
**Actions → select a run → Artifacts section at the bottom of the page**

### JUnit XML Reports

| Artifact name | Internal path | Format |
|---|---|---|
| `unit-results` | `results/unit.xml` | JUnit XML |
| `component-results` | `results/component.xml` | JUnit XML |
| `integration-results` | `results/integration.xml` | JUnit XML |
| `e2e-results` | `results/e2e.xml` | JUnit XML |
| `windows-results` | `results/windows.xml` | JUnit XML |

### Allure Test Reports

In addition to JUnit XML, the four main test layers (unit, component, integration, e2e) also upload raw Allure result data, which the `allure-report` job merges into an HTML report.

| Artifact name | Contents |
|---|---|
| `allure-results-unit-<run_id>` | Per-layer Allure results (unit) |
| `allure-results-component-<run_id>` | Per-layer Allure results (component) |
| `allure-results-integration-<run_id>` | Per-layer Allure results (integration) |
| `allure-results-e2e-<run_id>` | Per-layer Allure results (e2e) |

The merged HTML report is automatically deployed to the `gh-pages` branch and accessible via GitHub Pages (URL depends on your repository configuration).

---

## Windows-specific Tests — Design Notes

The application and its tests were developed for Windows. The Python source code
uses `pathlib.Path` and `sys.executable` throughout, making it fully portable.
Only one genuine OS-specific behaviour exists:

> `server.py` catches `ConnectionAbortedError` in `Server.handle_error()`.
> On Windows, abrupt client disconnects during SSE streaming raise
> `ConnectionAbortedError` (WinSock error `WSAECONNABORTED`). On Linux/macOS
> this error code is never raised — the kernel uses `BrokenPipeError` or
> `ConnectionResetError` instead.

The test `test_handle_error_swallows_connection_aborted_error` in
[`tests/component/test_server.py`](../tests/component/test_server.py) explicitly
contracts this behaviour and is automatically skipped on Linux/macOS via:

```python
@pytest.mark.windows_only
@pytest.mark.skipif(sys.platform != "win32", reason="...")
```

The ubuntu-based CI jobs pass `-m "... and not windows_only"` so the test is
excluded even if someone forgets the `skipif` decorator.
