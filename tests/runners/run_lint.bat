@echo off
setlocal enabledelayedexpansion

:: Move to project root (two levels up from tests\runners\)
cd /d "%~dp0..\.."

set ERRORS=0

echo [1/4] ruff check (lint)...
call .venv\Scripts\ruff check app/ tests/
if %ERRORLEVEL% neq 0 set /a ERRORS+=1

echo.
echo [2/4] ruff format --check (formatting)...
call .venv\Scripts\ruff format --check app/ tests/
if %ERRORLEVEL% neq 0 set /a ERRORS+=1

echo.
echo [3/4] mypy (type checking)...
call .venv\Scripts\mypy app/ --ignore-missing-imports --python-version 3.12
if %ERRORLEVEL% neq 0 set /a ERRORS+=1

echo.
echo [4/4] bandit (security lint)...
call .venv\Scripts\bandit -r app/ -q
if %ERRORLEVEL% neq 0 set /a ERRORS+=1

echo.
if %ERRORS% equ 0 (
    echo All checks passed.
    exit /b 0
) else (
    echo %ERRORS% check^(s^) failed.
    exit /b 1
)
