@echo off
cd /d "%~dp0..\.."

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

echo  Running INTEGRATION tests...
echo.
%PYTHON% -m pytest tests\integration\ -v -m integration
