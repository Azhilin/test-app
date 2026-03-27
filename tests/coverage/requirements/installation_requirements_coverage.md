# Installation Requirements — Coverage Detail

> Source document: [docs/product/requirements/installation_requirements.md](../../../docs/product/requirements/installation_requirements.md)  
> Back to summary: [tests/coverage/test_coverage.md](../test_coverage.md)

**Total:** 38 | **✅ Covered:** 5 | **🔶 Partial:** 0 | **❌ Gap:** 0 | **⬜ N/T:** 33 | **Functional:** 100%


#### Zip Contents

| ID | Requirement | Status | Tests |
|----|-------------|--------|-------|
| IR-01 | app/ source code included in release zip | ⬜ | — |
| IR-02 | templates/ Jinja2 HTML report template included | ⬜ | — |
| IR-03 | ui/ browser UI files included | ⬜ | — |
| IR-04 | docs/product/schemas/ folder included (may be empty) | ⬜ | — |
| IR-05 | certs/ placeholder folder with README.txt included | ⬜ | — |
| IR-06 | main.py CLI entry point included | ⬜ | — |
| IR-07 | server.py browser UI server entry point included | ⬜ | — |
| IR-08 | requirements.txt included | ⬜ | — |
| IR-09 | .env.example configuration template included | ⬜ | — |
| IR-10 | project_setup.bat one-time setup script included | ⬜ | — |
| IR-11 | start_app.bat Windows launcher included | ⬜ | — |
| IR-12 | README.md quickstart guide included | ⬜ | — |
| IR-13 | .venv/ NOT included in release zip | ⬜ | — |
| IR-14 | generated/ NOT included in release zip | ⬜ | — |
| IR-15 | requirements-dev.txt NOT included in release zip | ⬜ | — |
| IR-16 | Test files NOT included in release zip | ⬜ | — |
| IR-17 | .env NOT distributed in release zip | ⬜ | — |

#### Windows Installation

| ID | Requirement | Status | Tests |
|----|-------------|--------|-------|
| IR-18 | Zip extractable without errors to any destination folder | ⬜ | — |
| IR-19 | Paths with spaces or non-ASCII should be avoided (batch scripts) | ⬜ | — |
| IR-20 | project_setup.bat detects Python 3.10-3.12 on PATH | ⬜ | — |
| IR-21 | project_setup.bat downloads Python 3.12.10 if no compatible version | ⬜ | — |
| IR-22 | Python install via project_setup.bat is per-user (no admin) | ⬜ | — |
| IR-23 | Python installer SHA-256 checksum verified | ⬜ | — |
| IR-24 | Python download enforces TLS 1.2 | ⬜ | — |
| IR-25 | project_setup.bat creates .venv/ virtual environment | ⬜ | — |
| IR-26 | project_setup.bat installs packages from requirements.txt | ⬜ | — |
| IR-27 | project_setup.bat optionally installs requirements-dev.txt | ⬜ | — |
| IR-28 | project_setup.bat creates .env from .env.example if absent | ✅ | `test_server_config.py::TestWriteEnvFields::test_creates_env_from_example_when_env_missing` |
| IR-29 | project_setup.bat prompts to keep or backup+recreate .env on update | ⬜ | — |
| IR-30 | project_setup.bat writes setup log to generated/logs/ | ⬜ | — |
| IR-31 | project_setup.bat closes after 10s or on keypress | ⬜ | — |
| IR-32 | Credentials required in .env before generating reports | ✅ | `integration/test_integration.py::test_main_pipeline_config_fail`, `e2e/test_e2e.py::test_cli_no_credentials_via_subprocess` |
| IR-33 | start_app.bat launches server and opens http://localhost:8080 | ⬜ | — |

#### macOS / Linux Installation

| ID | Requirement | Status | Tests |
|----|-------------|--------|-------|
| IR-34 | venv created with python3.12 -m venv .venv | ⬜ | — |
| IR-35 | Dependencies installable via .venv/bin/pip install -r requirements.txt | ⬜ | — |
| IR-36 | Server startable with .venv/bin/python server.py | ✅ | `e2e/test_e2e.py::test_server_health_check` |
| IR-37 | Server startable on custom port (server.py 9000) | ✅ | `e2e/test_e2e.py::test_server_health_check` |

#### Update / Reinstall

| ID | Requirement | Status | Tests |
|----|-------------|--------|-------|
| IR-38 | Update process preserves existing .env credentials | ✅ | `test_server_config.py::TestWriteEnvFields::test_replaces_existing_key`, `test_server_config.py::TestWriteEnvFields::test_example_file_is_not_modified`, `test_server_config.py::TestWriteEnvFields::test_preserves_other_credential_keys_when_updating_url`, `test_server_config.py::TestWriteEnvFields::test_partial_update_preserves_untouched_key`, `test_server_config.py::TestWriteEnvFields::test_preserves_unrelated_optional_env_vars`, `test_server_config.py::TestWriteEnvFields::test_preserves_comment_lines_and_blanks` |
