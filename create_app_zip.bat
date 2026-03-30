@echo off
setlocal EnableDelayedExpansion

cd /d "%~dp0"

:: ============================================================
:: CONFIGURATION
:: ============================================================
set APP_NAME=ai_adoption_manager
set RELEASES_DIR=generated\releases
set ROBOCOPY_DIR_EXCLUDES=__pycache__ .pytest_cache .mypy_cache .ruff_cache
set ROBOCOPY_FILE_EXCLUDES=*.pyc *.pyo .DS_Store Thumbs.db *.log dau_report.json

:: ============================================================
:: GENERATE TIMESTAMP
:: ============================================================
for /f "usebackq delims=" %%T in (`powershell -NoProfile -Command "Get-Date -Format 'yyyy-MM-dd_HH-mm-ss'"`) do set TIMESTAMP=%%T

set ZIP_NAME=%APP_NAME%_%TIMESTAMP%
set STAGING_DIR=%RELEASES_DIR%\%ZIP_NAME%
set ZIP_PATH=%RELEASES_DIR%\%ZIP_NAME%.zip

echo.
echo  AI Adoption Manager — creating release package...
echo  Output: %ZIP_PATH%
echo.

:: ============================================================
:: PREPARE OUTPUT DIRECTORIES
:: ============================================================
if not exist "%RELEASES_DIR%" (
    mkdir "%RELEASES_DIR%"
    if errorlevel 1 (
        echo [ERROR] Failed to create output directory: %RELEASES_DIR%
        pause
        exit /b 1
    )
)

if exist "%STAGING_DIR%" rmdir /s /q "%STAGING_DIR%"
mkdir "%STAGING_DIR%"
if errorlevel 1 (
    echo [ERROR] Failed to create staging directory: %STAGING_DIR%
    pause
    exit /b 1
)

:: ============================================================
:: COPY FOLDERS
:: robocopy exit codes 0-7 are success; 8+ indicate errors.
:: /E = include subdirs (even empty), /XD = exclude dirs, /XF = exclude files
:: ============================================================
echo  Copying app sources...

robocopy "app"       "%STAGING_DIR%\app"       /E /XD %ROBOCOPY_DIR_EXCLUDES% /XF %ROBOCOPY_FILE_EXCLUDES% /NFL /NDL /NJH /NJS >nul
if errorlevel 8 ( echo [ERROR] Failed to copy app\      & goto :ABORT )

robocopy "templates" "%STAGING_DIR%\templates" /E /XD %ROBOCOPY_DIR_EXCLUDES% /XF %ROBOCOPY_FILE_EXCLUDES% /NFL /NDL /NJH /NJS >nul
if errorlevel 8 ( echo [ERROR] Failed to copy templates\ & goto :ABORT )

robocopy "ui"        "%STAGING_DIR%\ui"        /E /XD %ROBOCOPY_DIR_EXCLUDES% /XF %ROBOCOPY_FILE_EXCLUDES% /NFL /NDL /NJH /NJS >nul
if errorlevel 8 ( echo [ERROR] Failed to copy ui\        & goto :ABORT )

echo  Copying config (schemas and filters)...
robocopy "config"    "%STAGING_DIR%\config"    /E /XD %ROBOCOPY_DIR_EXCLUDES% /XF %ROBOCOPY_FILE_EXCLUDES% /NFL /NDL /NJH /NJS >nul
if errorlevel 8 ( echo [ERROR] Failed to copy config\ & goto :ABORT )

echo  Copying tools...
mkdir "%STAGING_DIR%\tools"
if errorlevel 1 ( echo [ERROR] Failed to create tools\ & goto :ABORT )
copy /Y "tools\fetch_ssl_cert.py" "%STAGING_DIR%\tools\" >nul
if errorlevel 1 ( echo [ERROR] Failed to copy tools\fetch_ssl_cert.py & goto :ABORT )

echo  Copying schema storage...
if exist "docs\product\schemas" (
    robocopy "docs\product\schemas" "%STAGING_DIR%\docs\product\schemas" /E /XD %ROBOCOPY_DIR_EXCLUDES% /XF %ROBOCOPY_FILE_EXCLUDES% /NFL /NDL /NJH /NJS >nul
    if errorlevel 8 ( echo [ERROR] Failed to copy docs\product\schemas\ & goto :ABORT )
) else (
    mkdir "%STAGING_DIR%\docs\product\schemas"
    if errorlevel 1 ( echo [ERROR] Failed to create docs\product\schemas\ & goto :ABORT )
)

echo  Preparing certs folder...
mkdir "%STAGING_DIR%\certs"
if errorlevel 1 ( echo [ERROR] Failed to create certs\ & goto :ABORT )
> "%STAGING_DIR%\certs\README.txt" echo Place jira_ca_bundle.pem here if your Jira instance uses a custom CA.
if errorlevel 1 ( echo [ERROR] Failed to create certs\README.txt & goto :ABORT )

:: ============================================================
:: COPY ROOT FILES
:: ============================================================
echo  Copying configuration and scripts...

for %%F in (main.py server.py requirements.txt .env.example start_app.bat project_setup.bat README.md) do (
    copy /Y "%%F" "%STAGING_DIR%\" >nul
    if errorlevel 1 (
        echo [ERROR] Failed to copy %%F
        goto :ABORT
    )
)

:: ============================================================
:: CREATE ZIP ARCHIVE
:: ============================================================
echo  Creating zip archive...

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "Compress-Archive -Path '%STAGING_DIR%' -DestinationPath '%ZIP_PATH%' -Force"

if errorlevel 1 (
    echo [ERROR] Failed to create zip archive.
    goto :ABORT
)

:: ============================================================
:: CLEANUP STAGING DIR
:: ============================================================
rmdir /s /q "%STAGING_DIR%"

:: ============================================================
:: DONE
:: ============================================================
echo.
echo  Done! Release package created:
echo.
echo    %ZIP_PATH%
echo.
echo  Share this zip with end users. They should:
echo    1. Unzip to any folder
echo    2. Run project_setup.bat (installs Python ^& dependencies, once)
echo    3. Review .env and fill in Jira credentials
echo    4. Run start_app.bat     (opens the app in the browser)
echo.
pause
exit /b 0

:ABORT
rmdir /s /q "%STAGING_DIR%" >nul 2>&1
echo.
echo  Packaging aborted. No zip file was created.
echo.
pause
exit /b 1
