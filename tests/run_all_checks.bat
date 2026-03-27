@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0.."

:: ─────────────────────────────────────────────────────────────────────────────
::  run_all_checks.bat  —  local mirror of the full CI pipeline
::
::  Usage:
::    run_all_checks.bat               run all auto stages (lint, unit,
::                                     component, windows, security)
::    run_all_checks.bat --integration also run integration tests (needs Jira)
::    run_all_checks.bat --e2e         also run E2E tests (needs Jira + browser)
::    run_all_checks.bat --all         run every stage including integration + e2e
::
::  Jira credentials are read from the .env file or environment variables.
:: ─────────────────────────────────────────────────────────────────────────────

:: ── Parse flags ──────────────────────────────────────────────────────────────
set RUN_INTEGRATION=0
set RUN_E2E=0
:parse_args
if "%~1"=="--integration" ( set RUN_INTEGRATION=1 & shift & goto parse_args )
if "%~1"=="--e2e"         ( set RUN_E2E=1         & shift & goto parse_args )
if "%~1"=="--all"         ( set RUN_INTEGRATION=1 & set RUN_E2E=1 & shift & goto parse_args )

:: ── Detect Python ────────────────────────────────────────────────────────────
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

:: ── Stage result tracking ─────────────────────────────────────────────────────
set R_LINT=SKIP
set R_UNIT=SKIP
set R_COMPONENT=SKIP
set R_WINDOWS=SKIP
set R_INTEGRATION=SKIP
set R_E2E=SKIP
set R_SECURITY=SKIP
set ANY_FAILED=0

:: ─────────────────────────────────────────────────────────────────────────────
echo.
echo =========================================================================
echo   LOCAL CI CHECKS
echo =========================================================================
echo.

:: ── 1. Lint ──────────────────────────────────────────────────────────────────
echo ── [1/7] Lint (ruff) ────────────────────────────────────────────────────
echo.
%PYTHON% -m ruff check app/ tests/
set EC1=!ERRORLEVEL!
%PYTHON% -m ruff format --check app/ tests/
set EC2=!ERRORLEVEL!
if !EC1! neq 0 ( set R_LINT=FAIL & set ANY_FAILED=1 ) else if !EC2! neq 0 ( set R_LINT=FAIL & set ANY_FAILED=1 ) else ( set R_LINT=PASS )
echo.

:: ── 2. Unit Tests ─────────────────────────────────────────────────────────────
echo ── [2/7] Unit Tests ─────────────────────────────────────────────────────
echo.
%PYTHON% -m pytest tests\unit\ -m "unit and not windows_only" --tb=short
if !ERRORLEVEL! neq 0 ( set R_UNIT=FAIL & set ANY_FAILED=1 ) else ( set R_UNIT=PASS )
echo.

:: ── 3. Component Tests ───────────────────────────────────────────────────────
echo ── [3/7] Component Tests ────────────────────────────────────────────────
echo.
%PYTHON% -m pytest tests\component\ -m "component and not windows_only" --tb=short
if !ERRORLEVEL! neq 0 ( set R_COMPONENT=FAIL & set ANY_FAILED=1 ) else ( set R_COMPONENT=PASS )
echo.

:: ── 4. Windows-specific Tests ────────────────────────────────────────────────
echo ── [4/7] Windows-specific Tests ─────────────────────────────────────────
echo.
%PYTHON% -m pytest tests\ -m windows_only --tb=short
if !ERRORLEVEL! neq 0 ( set R_WINDOWS=FAIL & set ANY_FAILED=1 ) else ( set R_WINDOWS=PASS )
echo.

:: ── 5. Integration Tests (optional) ──────────────────────────────────────────
echo ── [5/7] Integration Tests ──────────────────────────────────────────────
if !RUN_INTEGRATION! equ 0 (
    echo   SKIPPED — pass --integration or --all to enable.
    echo   Requires JIRA_URL / JIRA_EMAIL / JIRA_API_TOKEN in .env
) else (
    echo.
    %PYTHON% -m pytest tests\integration\ -m "integration and not windows_only" --tb=short
    if !ERRORLEVEL! neq 0 ( set R_INTEGRATION=FAIL & set ANY_FAILED=1 ) else ( set R_INTEGRATION=PASS )
)
echo.

:: ── 6. E2E Tests (optional) ──────────────────────────────────────────────────
echo ── [6/7] E2E Tests ──────────────────────────────────────────────────────
if !RUN_E2E! equ 0 (
    echo   SKIPPED — pass --e2e or --all to enable.
    echo   Requires JIRA_URL / JIRA_EMAIL / JIRA_API_TOKEN in .env + Playwright
) else (
    echo.
    %PYTHON% -m playwright install chromium >nul 2>&1
    %PYTHON% -m pytest tests\e2e\ -m "e2e and not windows_only" --tb=short
    if !ERRORLEVEL! neq 0 ( set R_E2E=FAIL & set ANY_FAILED=1 ) else ( set R_E2E=PASS )
)
echo.

:: ── 7. Security Scan ─────────────────────────────────────────────────────────
echo ── [7/7] Security Scan (pip-audit) ──────────────────────────────────────
echo.
%PYTHON% -m pip_audit --version >nul 2>&1
if !ERRORLEVEL! neq 0 (
    where pip-audit >nul 2>&1
    if !ERRORLEVEL! neq 0 (
        echo   WARNING: pip-audit not found. Install with: pip install pip-audit
        set R_SECURITY=SKIP
    ) else (
        pip-audit -r requirements.txt
        if !ERRORLEVEL! neq 0 ( set R_SECURITY=FAIL & set ANY_FAILED=1 ) else ( set R_SECURITY=PASS )
    )
) else (
    %PYTHON% -m pip_audit -r requirements.txt
    if !ERRORLEVEL! neq 0 ( set R_SECURITY=FAIL & set ANY_FAILED=1 ) else ( set R_SECURITY=PASS )
)
echo.

:: ── Summary ───────────────────────────────────────────────────────────────────
echo =========================================================================
echo   SUMMARY
echo =========================================================================
echo.
echo   Stage                   Result
echo   ─────────────────────── ──────
echo   Lint (ruff)             !R_LINT!
echo   Unit Tests              !R_UNIT!
echo   Component Tests         !R_COMPONENT!
echo   Windows Tests           !R_WINDOWS!
echo   Integration Tests       !R_INTEGRATION!
echo   E2E Tests               !R_E2E!
echo   Security Scan           !R_SECURITY!
echo.

if !ANY_FAILED! equ 1 (
    echo   RESULT: One or more stages FAILED.
) else (
    echo   RESULT: All stages passed or were skipped.
)
echo.
echo =========================================================================
echo.
pause
exit /b !ANY_FAILED!
