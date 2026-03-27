@echo off
cd /d "%~dp0..\.."

if not exist ".venv\" (
    echo Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 ( echo ERROR: venv creation failed. & pause & exit /b 1 )
)

echo Installing requirements-dev.txt...
.venv\Scripts\pip install -r requirements-dev.txt
if errorlevel 1 ( echo ERROR: pip install failed. & pause & exit /b 1 )

echo.
echo All dependencies installed.
pause
exit /b 0
