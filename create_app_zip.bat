@echo off
setlocal EnableDelayedExpansion

cd /d "%~dp0"

:: ============================================================
:: CONFIGURATION
:: ============================================================
set APP_NAME=ai_adoption_manager
set RELEASES_DIR=generated\releases

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

robocopy "app"       "%STAGING_DIR%\app"       /E /XD __pycache__ /XF *.pyc /NFL /NDL /NJH /NJS >nul
if errorlevel 8 ( echo [ERROR] Failed to copy app\      & goto :ABORT )

robocopy "templates" "%STAGING_DIR%\templates" /E /XD __pycache__ /XF *.pyc /NFL /NDL /NJH /NJS >nul
if errorlevel 8 ( echo [ERROR] Failed to copy templates\ & goto :ABORT )

robocopy "ui"        "%STAGING_DIR%\ui"        /E /XD __pycache__ /XF *.pyc /NFL /NDL /NJH /NJS >nul
if errorlevel 8 ( echo [ERROR] Failed to copy ui\        & goto :ABORT )

robocopy "docs"      "%STAGING_DIR%\docs"      /E /XD __pycache__ /XF *.pyc /NFL /NDL /NJH /NJS >nul
if errorlevel 8 ( echo [ERROR] Failed to copy docs\      & goto :ABORT )

:: ============================================================
:: COPY ROOT FILES
:: ============================================================
echo  Copying configuration and scripts...

for %%F in (main.py server.py requirements.txt .env.example start_app.bat python_setup.bat README.md) do (
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
echo    2. Run python_setup.bat  (installs Python ^& dependencies, once)
echo    3. Copy .env.example to .env and fill in Jira credentials
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
