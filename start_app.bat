@echo off
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    set PYTHON=.venv\Scripts\python.exe
) else (
    where python >nul 2>&1
    if errorlevel 1 (
        echo ERROR: Python is not installed or not on PATH.
        echo Please install Python from https://www.python.org/downloads/
        pause
        exit /b 1
    )
    set PYTHON=python
)

powershell -NoProfile -NoExit -Command ^
  "$host.UI.RawUI.WindowTitle = 'AI Adoption Metrics';" ^
  "Write-Host ' AI Adoption Metrics — starting server...' -ForegroundColor Cyan;" ^
  "Write-Host '';" ^
  "& '%~dp0%PYTHON%' server.py;" ^
  "Write-Host '';" ^
  "Write-Host 'Server stopped. Press any key to close...' -ForegroundColor Yellow;" ^
  "$null = $host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')"
