@echo off
cd /d "%~dp0..\.."

::  run_all_checks.bat  —  local mirror of the full CI pipeline
::
::  Usage:
::    run_all_checks.bat               run all auto stages (lint, unit,
::                                     component, windows, security) in parallel
::    run_all_checks.bat --integration also run integration tests (needs Jira)
::    run_all_checks.bat --e2e         also run E2E tests (needs Jira + browser)
::    run_all_checks.bat --all         run every stage including integration + e2e
::
::  Jira credentials are read from the .env file or environment variables.

if exist ".venv\Scripts\python.exe" (
    set PYTHON=.venv\Scripts\python.exe
) else (
    where python >nul 2>&1
    if errorlevel 1 (
        echo ERROR: Python is not installed or not on PATH.
        pause
        exit /b 1
    )
    set PYTHON=python
)

%PYTHON% tests\runners\run_all_checks.py %*
set EXIT_CODE=%ERRORLEVEL%
pause
exit /b %EXIT_CODE%
