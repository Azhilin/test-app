@echo off
cd /d "%~dp0"

echo  AI Adoption Metrics — starting server...
echo.

where python >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not on PATH.
    echo Please install Python from https://www.python.org/downloads/
    pause
    exit /b 1
)

python server.py
pause
