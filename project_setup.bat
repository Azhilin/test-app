@echo off
setlocal EnableDelayedExpansion

:: ============================================================
:: CONFIGURATION
:: ============================================================
set PYTHON_MAJOR=3
set PYTHON_MIN_MINOR=10
set PYTHON_MAX_MINOR=13
set PYTHON_TARGET=3.12
set PYTHON_INSTALL_VERSION=3.12.10
set PYTHON_URL_64=https://www.python.org/ftp/python/3.12.10/python-3.12.10-amd64.exe
set PYTHON_URL_32=https://www.python.org/ftp/python/3.12.10/python-3.12.10.exe
set PYTHON_HASH_64=67b5635e80ea51072b87941312d00ec8927c4db9ba18938f7ad2d27b328b95fb
set PYTHON_HASH_32=fdfe385b94f5b8785a0226a886979527fd26eb65defdbf29992fd22cc4b0e31e
set VENV_DIR=.venv
set LOG_DIR=generated\logs
set LOG_FILE=
set ENV_FILE=.env
set ENV_TEMPLATE=.env.example
set INSTALLER_LOCAL_DIR=installers
set SKIP_COUNTDOWN=0
set SMOKE_TEST_MODE=0
set ENV_EXISTING_ACTION=prompt

:: Parse optional arguments
:PARSE_ARGS
if "%~1"=="" goto :ARGS_DONE
if /i "%~1"=="--smoke-test" (
    set SMOKE_TEST_MODE=1
    set SKIP_COUNTDOWN=1
)
if /i "%~1"=="--keep-env" (
    if /i not "%ENV_EXISTING_ACTION%"=="prompt" goto :ARGS_CONFLICT
    set ENV_EXISTING_ACTION=keep
)
if /i "%~1"=="--refresh-env" (
    if /i not "%ENV_EXISTING_ACTION%"=="prompt" goto :ARGS_CONFLICT
    set ENV_EXISTING_ACTION=refresh
)
shift
goto :PARSE_ARGS
:ARGS_DONE
goto :ARGS_OK

:ARGS_CONFLICT
echo [ERROR] Conflicting .env options. Use only one of --keep-env or --refresh-env.
exit /b 1

:ARGS_OK

:: ============================================================
:: SECTION 1 - PRE-EXECUTION & OS VALIDATION
:: ============================================================

:: OS check
if /i not "%OS%"=="Windows_NT" (
    echo [ERROR] This setup script is designed exclusively for Windows.
    echo         Please use setup.sh for macOS/Linux.
    call :COUNTDOWN
    exit /b 1
)

:: Architecture detection - handles WOW64 case (32-bit cmd on 64-bit Windows)
set ARCH=64
if "%PROCESSOR_ARCHITECTURE%"=="x86" (
    if not defined PROCESSOR_ARCHITEW6432 set ARCH=32
)

:: Change to the script's own directory so relative paths are always correct
cd /d "%~dp0"
set "PROJECT_ROOT=%CD%"
set "ENV_PATH=%PROJECT_ROOT%\%ENV_FILE%"
set "ENV_TEMPLATE_PATH=%PROJECT_ROOT%\%ENV_TEMPLATE%"

for /f "usebackq delims=" %%T in (`powershell -NoProfile -Command "Get-Date -Format yyyyMMdd-HHmmss"`) do (
    set "SESSION_STAMP=%%T"
)
if not defined SESSION_STAMP set "SESSION_STAMP=%RANDOM%"
set "LOG_FILE=%LOG_DIR%\project_setup-%SESSION_STAMP%.log"
set "LOG_FILE_PATH=%PROJECT_ROOT%\%LOG_FILE%"

:: ============================================================
:: SECTION 2 - LOGGING & USER EXPERIENCE
:: ============================================================

:: Create logs directory if it doesn't exist
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

:: Write a session header to the log file
call :LOG_RAW "========================================================"
call :LOG_RAW "  Project Setup Session Started - %DATE% %TIME%"
call :LOG_RAW "========================================================"
call :LOG "[INFO]" "Writing setup log to '%LOG_FILE_PATH%'."

call :LOG "[INFO]" "OS validated: Windows_NT + Architecture: %ARCH%-bit"

:: ============================================================
:: SECTION 2a - ENVIRONMENT FILE BOOTSTRAP (early, no Python required)
:: Creates .env from .env.example before any step that may exit early.
:: ============================================================
call :ENSURE_ENV_FILE
if errorlevel 1 (
    call :COUNTDOWN
    exit /b 1
)

if "%SMOKE_TEST_MODE%"=="1" (
    call :LOG "[INFO]" "Smoke-test mode enabled. Skipping Python installation and dependency setup."
    goto :AFTER_DEPS
)

:: ============================================================
:: PRIVILEGE ASSESSMENT (Least Privilege Principle)
:: ============================================================
net session >nul 2>&1
if %errorlevel% == 0 (
    call :LOG "[INFO]" "Running with Administrator privileges. Installation will remain per-user (InstallAllUsers=0)."
) else (
    call :LOG "[INFO]" "Running as standard user - per-user installation mode (no UAC prompt required)."
)

:: ============================================================
:: SECTION 3 - PYTHON DETECTION & VERSION VALIDATION
:: ============================================================
call :LOG "[INFO]" "Detecting Python installation..."

set PYTHON_FOUND=0
set PYTHON_VERSION=
set PYTHON_MAJOR_FOUND=
set PYTHON_MINOR_FOUND=
set PYTHON_CMD=

:: Primary: Windows Python Launcher
where py >nul 2>&1
if %errorlevel% == 0 (
    for /f "tokens=2 delims= " %%V in ('py --version 2^>^&1') do (
        set PYTHON_VERSION=%%V
    )
    if defined PYTHON_VERSION (
        set PYTHON_FOUND=1
        set PYTHON_CMD=py
        call :LOG "[INFO]" "Python Launcher (py.exe) found. Reported version: !PYTHON_VERSION!"
        goto :PARSE_VERSION
    )
)

:: Fallback 1: python
where python >nul 2>&1
if %errorlevel% == 0 (
    for /f "tokens=2 delims= " %%V in ('python --version 2^>^&1') do (
        set PYTHON_VERSION=%%V
    )
    if defined PYTHON_VERSION (
        set PYTHON_FOUND=1
        set PYTHON_CMD=python
        call :LOG "[INFO]" "python found. Reported version: !PYTHON_VERSION!"
        goto :PARSE_VERSION
    )
)

:: Fallback 2: python3
where python3 >nul 2>&1
if %errorlevel% == 0 (
    for /f "tokens=2 delims= " %%V in ('python3 --version 2^>^&1') do (
        set PYTHON_VERSION=%%V
    )
    if defined PYTHON_VERSION (
        set PYTHON_FOUND=1
        set PYTHON_CMD=python3
        call :LOG "[INFO]" "python3 found. Reported version: !PYTHON_VERSION!"
        goto :PARSE_VERSION
    )
)

:: No Python detected at all
call :LOG "[WARNING]" "No Python installation detected on PATH."
goto :DO_INSTALL

:PARSE_VERSION
:: Extract Major and Minor from "3.12.10" -> MAJOR=3, MINOR=12
for /f "tokens=1,2,3 delims=." %%A in ("!PYTHON_VERSION!") do (
    set PYTHON_MAJOR_FOUND=%%A
    set PYTHON_MINOR_FOUND=%%B
)

if not defined PYTHON_MAJOR_FOUND goto :VERSION_PARSE_FAIL
if not defined PYTHON_MINOR_FOUND goto :VERSION_PARSE_FAIL

call :LOG "[INFO]" "Parsed version - Major: !PYTHON_MAJOR_FOUND!  Minor: !PYTHON_MINOR_FOUND!"

:: Validate major version is 3
if not "!PYTHON_MAJOR_FOUND!"=="3" (
    call :LOG "[WARNING]" "Detected Python !PYTHON_VERSION! - major version is not 3. Proceeding to install Python %PYTHON_INSTALL_VERSION%."
    goto :PROMPT_INSTALL
)

:: Check minor >= MIN_MINOR and < MAX_MINOR
if !PYTHON_MINOR_FOUND! GEQ %PYTHON_MIN_MINOR% (
    if !PYTHON_MINOR_FOUND! LSS %PYTHON_MAX_MINOR% (
        call :LOG "[SUCCESS]" "Python !PYTHON_VERSION! satisfies the required range (>=%PYTHON_MAJOR%.%PYTHON_MIN_MINOR%, <%PYTHON_MAJOR%.%PYTHON_MAX_MINOR%). Skipping installation."
        goto :SETUP_VENV
    )
)

:: Version is out of range
call :LOG "[WARNING]" "Python !PYTHON_VERSION! is outside the required range (>=%PYTHON_MAJOR%.%PYTHON_MIN_MINOR%, <%PYTHON_MAJOR%.%PYTHON_MAX_MINOR%)."
goto :PROMPT_INSTALL

:VERSION_PARSE_FAIL
call :LOG "[WARNING]" "Could not parse the Python version string: !PYTHON_VERSION!. Proceeding to install."
goto :DO_INSTALL

:PROMPT_INSTALL
echo.
echo  The detected Python version (!PYTHON_VERSION!) is not compatible with this project.
echo  Python %PYTHON_INSTALL_VERSION% will be installed alongside your current version.
echo  The Windows Launcher (py.exe) will manage both versions.
echo.
set /p USER_CHOICE="  Proceed with installing Python %PYTHON_INSTALL_VERSION%? [Y/N]: "
if /i "!USER_CHOICE!"=="Y" goto :DO_INSTALL
if /i "!USER_CHOICE!"=="YES" goto :DO_INSTALL
call :LOG "[INFO]" "User declined installation. Exiting."
call :COUNTDOWN
exit /b 0

:: ============================================================
:: SECTION 4 - PYTHON INSTALLATION (SECURE & SILENT)
:: ============================================================
:DO_INSTALL
call :LOG "[INFO]" "Preparing to download Python %PYTHON_INSTALL_VERSION% (%ARCH%-bit)..."

:: Select the correct installer URL and hash based on architecture
if "%ARCH%"=="64" (
    set INSTALLER_URL=%PYTHON_URL_64%
    set EXPECTED_HASH=%PYTHON_HASH_64%
    set INSTALLER_FILE=%TEMP%\python-%PYTHON_INSTALL_VERSION%-amd64.exe
) else (
    set INSTALLER_URL=%PYTHON_URL_32%
    set EXPECTED_HASH=%PYTHON_HASH_32%
    set INSTALLER_FILE=%TEMP%\python-%PYTHON_INSTALL_VERSION%-win32.exe
)

:: Check for a bundled installer first (offline / avoids SSL issues)
if "%ARCH%"=="64" (
    if exist "%INSTALLER_LOCAL_DIR%\python-%PYTHON_INSTALL_VERSION%-amd64.exe" (
        set INSTALLER_FILE=%INSTALLER_LOCAL_DIR%\python-%PYTHON_INSTALL_VERSION%-amd64.exe
        call :LOG "[INFO]" "Bundled installer found: '!INSTALLER_FILE!'. Skipping download."
        goto :VERIFY_INSTALLER
    )
) else (
    if exist "%INSTALLER_LOCAL_DIR%\python-%PYTHON_INSTALL_VERSION%.exe" (
        set INSTALLER_FILE=%INSTALLER_LOCAL_DIR%\python-%PYTHON_INSTALL_VERSION%.exe
        call :LOG "[INFO]" "Bundled installer found: '!INSTALLER_FILE!'. Skipping download."
        goto :VERIFY_INSTALLER
    )
)

call :LOG "[INFO]" "Download URL: !INSTALLER_URL!"
call :LOG "[INFO]" "Installer will be saved to: !INSTALLER_FILE!"

:: Strategy 1: Secure download via PowerShell with forced TLS 1.2
call :LOG "[INFO]" "Downloading installer (forcing TLS 1.2)..."
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; " ^
    "try { " ^
    "  $wc = New-Object System.Net.WebClient; " ^
    "  $wc.DownloadFile('!INSTALLER_URL!', '!INSTALLER_FILE!'); " ^
    "  Write-Host 'Download complete.' " ^
    "} catch { " ^
    "  Write-Host ('DOWNLOAD_FAILED: ' + $_.Exception.Message); " ^
    "  exit 1 " ^
    "}"

if %errorlevel% equ 0 goto :DOWNLOAD_DONE

:: Strategy 2: Fallback via bitsadmin (built-in, handles SSL differently on restricted systems)
call :LOG "[WARNING]" "Primary download failed. Retrying via bitsadmin..."
bitsadmin /transfer "PythonInstaller" /download /priority NORMAL "!INSTALLER_URL!" "!INSTALLER_FILE!" >nul 2>&1

if %errorlevel% neq 0 (
    call :LOG "[ERROR]" "Both download methods failed."
    echo.
    echo  ================================================================
    echo   Could not download the Python installer automatically.
    echo   This is usually caused by SSL certificate restrictions on
    echo   your network.
    echo.
    echo   SOLUTION: Ask your IT team (or a technical colleague) to
    echo   download the file manually and place it here:
    echo.
    if "%ARCH%"=="64" (
        echo     %INSTALLER_LOCAL_DIR%\python-%PYTHON_INSTALL_VERSION%-amd64.exe
    ) else (
        echo     %INSTALLER_LOCAL_DIR%\python-%PYTHON_INSTALL_VERSION%.exe
    )
    echo.
    echo   Then run project_setup.bat again.
    echo  ================================================================
    echo.
    call :COUNTDOWN
    exit /b 1
)

:DOWNLOAD_DONE
if not exist "!INSTALLER_FILE!" (
    call :LOG "[ERROR]" "Installer file not found after download: !INSTALLER_FILE!"
    call :COUNTDOWN
    exit /b 1
)

:VERIFY_INSTALLER
call :LOG "[INFO]" "Verifying SHA-256 checksum..."

:: SHA-256 checksum validation
for /f "usebackq delims=" %%H in (`powershell -NoProfile -Command "(Get-FileHash '!INSTALLER_FILE!' -Algorithm SHA256).Hash.ToLower()"`) do (
    set ACTUAL_HASH=%%H
)

call :LOG "[INFO]" "Expected: !EXPECTED_HASH!"
call :LOG "[INFO]" "Actual:   !ACTUAL_HASH!"

if /i not "!ACTUAL_HASH!"=="!EXPECTED_HASH!" (
    call :LOG "[ERROR]" "SHA-256 checksum MISMATCH. The installer may have been tampered with (MITM risk)."
    call :LOG "[ERROR]" "Deleting the unsafe file and aborting installation."
    del /f /q "!INSTALLER_FILE!" >nul 2>&1
    call :COUNTDOWN
    exit /b 1
)

call :LOG "[SUCCESS]" "Checksum verified successfully. Installer is authentic."

:: Silent per-user installation
call :LOG "[INFO]" "Running silent Python %PYTHON_INSTALL_VERSION% installer (per-user, no UAC)..."
"!INSTALLER_FILE!" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0 Include_launcher=1

if %errorlevel% neq 0 (
    call :LOG "[ERROR]" "Python installer exited with a non-zero code (%errorlevel%). Installation may have failed."
    del /f /q "!INSTALLER_FILE!" >nul 2>&1
    call :COUNTDOWN
    exit /b 1
)

call :LOG "[SUCCESS]" "Python %PYTHON_INSTALL_VERSION% installed successfully."

:: Clean up installer
del /f /q "!INSTALLER_FILE!" >nul 2>&1

:: PATH Refresh - the current cmd session won't see the new PATH without a restart.
:: Read the updated User PATH from the registry via PowerShell and apply it to this session.
call :LOG "[INFO]" "Refreshing PATH environment variable for this session..."
for /f "usebackq delims=" %%P in (`powershell -NoProfile -Command "[Environment]::GetEnvironmentVariable('PATH','User')"`) do (
    set USER_PATH=%%P
)
for /f "usebackq delims=" %%P in (`powershell -NoProfile -Command "[Environment]::GetEnvironmentVariable('PATH','Machine')"`) do (
    set MACHINE_PATH=%%P
)
set PATH=!MACHINE_PATH!;!USER_PATH!

call :LOG "[INFO]" "PATH refreshed. New user segment: !USER_PATH!"

:: Update PYTHON_CMD to use py launcher now that it's installed
set PYTHON_CMD=py

:: ============================================================
:: SECTION 5 - VIRTUAL ENVIRONMENT SETUP
:: ============================================================
:SETUP_VENV
call :LOG "[INFO]" "Setting up Python virtual environment in '%VENV_DIR%'..."

:: Check if venv already exists and is complete
if exist "%VENV_DIR%\Scripts\activate.bat" (
    call :LOG "[INFO]" "Virtual environment already exists at '%VENV_DIR%'. Skipping creation."
    goto :AFTER_VENV_CREATE
)

:: If venv directory exists but is incomplete/corrupted, remove it and recreate
if exist "%VENV_DIR%" (
    call :LOG "[WARNING]" "Directory '%VENV_DIR%' exists but appears incomplete. Removing and recreating..."
    rmdir /s /q "%VENV_DIR%" >nul 2>&1
    if !errorlevel! neq 0 (
        call :LOG "[ERROR]" "Failed to remove incomplete virtual environment at '%VENV_DIR%'."
        call :COUNTDOWN
        exit /b 1
    )
)

:: Create venv using the detected Python command, preferring the launcher when available
if /i "%PYTHON_CMD%"=="py" (
    py -%PYTHON_TARGET% -m venv "%VENV_DIR%"
) else (
    %PYTHON_CMD% -m venv "%VENV_DIR%"
)

if %errorlevel% neq 0 (
    call :LOG "[ERROR]" "Failed to create virtual environment. Check that a compatible Python interpreter is available."
    call :COUNTDOWN
    exit /b 1
)

:AFTER_VENV_CREATE
:: Verify activation script exists as confirmation the venv was built correctly
if not exist "%VENV_DIR%\Scripts\activate.bat" (
    call :LOG "[ERROR]" "Virtual environment activation script not found at '%VENV_DIR%\Scripts\activate.bat'. Creation may have failed."
    call :COUNTDOWN
    exit /b 1
)

call :LOG "[SUCCESS]" "Virtual environment ready at '%VENV_DIR%'."

:: ============================================================
:: SECTION 5a - SSL CERTIFICATE BOOTSTRAP
:: Exports Windows trusted root and intermediate CA certificates
:: to a PEM file, then points pip at it via PIP_CERT.
:: Resolves SSL failures on corporate laptops where pip.ini
:: references a missing cert file, or where a corporate proxy
:: performs SSL inspection with a CA not in pip's certifi bundle.
:: ============================================================
call :LOG "[INFO]" "Exporting Windows trusted certificates for pip SSL validation..."

set "WIN_CERT_PEM=%PROJECT_ROOT%\certs\windows-trusted-roots.pem"

if not exist "%PROJECT_ROOT%\certs" mkdir "%PROJECT_ROOT%\certs"

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$stores = 'Root','CA'; " ^
    "$pems = @(); " ^
    "foreach ($store in $stores) { " ^
    "  try { " ^
    "    $s = New-Object System.Security.Cryptography.X509Certificates.X509Store($store, 'LocalMachine'); " ^
    "    $s.Open(0); " ^
    "    foreach ($cert in $s.Certificates) { " ^
    "      $b64 = [Convert]::ToBase64String($cert.RawData, 1); " ^
    "      $pems += '-----BEGIN CERTIFICATE-----' + [char]10 + $b64 + [char]10 + '-----END CERTIFICATE-----' " ^
    "    }; " ^
    "    $s.Close() " ^
    "  } catch {} " ^
    "}; " ^
    "[IO.File]::WriteAllText('!WIN_CERT_PEM!', ($pems -join [char]10), [Text.Encoding]::ASCII); " ^
    "Write-Host ('Exported ' + $pems.Count + ' certificates')"

if %errorlevel% neq 0 (
    call :LOG "[WARNING]" "Could not export Windows certificates. Pip may fail if SSL inspection is active."
    call :LOG "[WARNING]" "If pip fails, ask IT to provide a CA bundle and set PIP_CERT to its path manually."
) else (
    set "PIP_CERT=!WIN_CERT_PEM!"
    call :LOG "[SUCCESS]" "Certificates exported to 'certs\windows-trusted-roots.pem'. PIP_CERT set for this session."
)

:: Upgrade pip inside the isolated environment first
call :LOG "[INFO]" "Upgrading pip inside the virtual environment..."
"%VENV_DIR%\Scripts\python.exe" -m pip install --upgrade pip --quiet

if %errorlevel% neq 0 (
    call :LOG "[WARNING]" "pip upgrade returned a non-zero exit code. Proceeding anyway."
) else (
    call :LOG "[SUCCESS]" "pip upgraded successfully."
)

:: Install project dependencies
if exist "requirements.txt" (
    call :LOG "[INFO]" "Installing project dependencies from requirements.txt..."
    "%VENV_DIR%\Scripts\pip.exe" install -r requirements.txt

    if !errorlevel! neq 0 (
        call :LOG "[ERROR]" "Dependency installation failed. Review the output above."
        call :COUNTDOWN
        exit /b 1
    )
    call :LOG "[SUCCESS]" "All dependencies installed successfully."
) else (
    call :LOG "[WARNING]" "requirements.txt not found in project root. Skipping dependency installation."
)

:: Optionally install dev dependencies
if exist "requirements-dev.txt" (
    echo.
    set /p DEV_CHOICE="  Install dev dependencies (pytest, pytest-mock)? [Y/N]: "
    if /i "!DEV_CHOICE!"=="Y" goto :INSTALL_DEV
    if /i "!DEV_CHOICE!"=="YES" goto :INSTALL_DEV
    call :LOG "[INFO]" "Skipping dev dependency installation."
    goto :AFTER_DEV
    :INSTALL_DEV
    call :LOG "[INFO]" "Installing dev dependencies from requirements-dev.txt..."
    "%VENV_DIR%\Scripts\pip.exe" install -r requirements-dev.txt
    if !errorlevel! neq 0 (
        call :LOG "[ERROR]" "Dev dependency installation failed. Review the output above."
        call :COUNTDOWN
        exit /b 1
    )
    call :LOG "[SUCCESS]" "Dev dependencies installed successfully."
    call :LOG "[INFO]" "Installing Playwright Chromium browser (required for e2e tests)..."
    "%VENV_DIR%\Scripts\python.exe" -m playwright install chromium
    if !errorlevel! neq 0 (
        call :LOG "[WARNING]" "Playwright Chromium install failed. E2e tests will not run. Re-run: .venv\Scripts\python -m playwright install chromium"
    ) else (
        call :LOG "[SUCCESS]" "Playwright Chromium installed successfully."
    )
    :AFTER_DEV
)

:: ============================================================
:: SECTION 7 - .GITIGNORE SAFETY CHECK
:AFTER_DEPS
:: ============================================================
if exist ".gitignore" (
    findstr /i /c:".venv" .gitignore >nul 2>&1
    if !errorlevel! neq 0 (
        call :LOG "[WARNING]" ".venv not found in .gitignore. Appending '.venv/' to prevent accidental commits..."
        echo.>> .gitignore
        echo .venv/>> .gitignore
        call :LOG "[INFO]" "'.venv/' appended to .gitignore."
    ) else (
        call :LOG "[INFO]" ".venv is already listed in .gitignore. No changes needed."
    )
) else (
    call :LOG "[WARNING]" ".gitignore not found. Consider creating one and adding '.venv/' to it."
)

:: ============================================================
:: DONE
:: ============================================================
echo.
call :LOG "[SUCCESS]" "================================================================"
call :LOG "[SUCCESS]" "  Setup complete! Your Python environment is ready."
call :LOG "[SUCCESS]" "  To activate the virtual environment, run:"
call :LOG "[SUCCESS]" "    %VENV_DIR%\Scripts\activate.bat"
call :LOG "[SUCCESS]" "  Review '%ENV_FILE%' and fill in Jira credentials before running start_app.bat."
call :LOG "[SUCCESS]" "  Setup log saved to: %LOG_FILE_PATH%"
call :LOG "[SUCCESS]" "================================================================"
call :LOG_RAW "  Session ended - %DATE% %TIME%"
call :LOG_RAW "========================================================"
echo.
call :COUNTDOWN
exit /b 0

:: ============================================================
:: SUBROUTINES
:: ============================================================

:: :LOG prefix message
::   Writes a timestamped, prefixed message to both the console and the log file.
:LOG
set "_PREFIX=%~1"
set "_MSG=%~2"
for /f "tokens=1-3 delims=:., " %%A in ("%TIME%") do (
    set _HH=%%A
    set _MM=%%B
    set _SS=%%C
)
echo !_PREFIX! !_MSG!
echo [!_HH!:!_MM!:!_SS!] !_PREFIX! !_MSG!>> "%LOG_FILE%"
goto :eof

:: :LOG_RAW message
::   Writes a raw (no prefix) line to the log file only (used for headers/separators).
:LOG_RAW
echo %~1 >> "%LOG_FILE%"
goto :eof

:: :ENSURE_ENV_FILE
::   Creates .env from .env.example or offers a backup-and-refresh path when .env exists.
:ENSURE_ENV_FILE
call :LOG "[INFO]" "Ensuring '%ENV_FILE%' is available at '%ENV_PATH%'."

if exist "%ENV_FILE%" goto :HANDLE_EXISTING_ENV

if exist "%ENV_TEMPLATE%" (
    call :COPY_TEMPLATE_TO_ENV
    if errorlevel 1 exit /b 1
    call :LOG "[SUCCESS]" "Created '%ENV_FILE%' at '%ENV_PATH%' from '%ENV_TEMPLATE_PATH%' with default values."
) else (
    call :LOG "[WARNING]" "'%ENV_TEMPLATE%' not found at '%ENV_TEMPLATE_PATH%'. Skipping '%ENV_FILE%' creation at '%ENV_PATH%'."
)
exit /b 0

:HANDLE_EXISTING_ENV
if not exist "%ENV_TEMPLATE%" (
    call :LOG "[INFO]" "Existing '%ENV_FILE%' found at '%ENV_PATH%'. Leaving it unchanged."
    call :LOG "[WARNING]" "'%ENV_TEMPLATE%' not found at '%ENV_TEMPLATE_PATH%', so refresh options for '%ENV_PATH%' are unavailable."
    exit /b 0
)

if /i "%ENV_EXISTING_ACTION%"=="keep" (
    call :LOG "[INFO]" "Existing '%ENV_FILE%' found at '%ENV_PATH%'. Keeping it unchanged because --keep-env was provided."
    exit /b 0
)

if /i "%ENV_EXISTING_ACTION%"=="refresh" (
    call :LOG "[INFO]" "Existing '%ENV_FILE%' found at '%ENV_PATH%'. Refreshing it from '%ENV_TEMPLATE_PATH%' because --refresh-env was provided."
    goto :BACKUP_AND_RECREATE_ENV
)

echo.
echo  Existing %ENV_FILE% found.
echo    [K] Keep the current %ENV_FILE% unchanged
echo    [B] Back up the current %ENV_FILE% and recreate it from %ENV_TEMPLATE%
set /p ENV_CHOICE="  Choose [K/B] (default: K): "

if not defined ENV_CHOICE (
    call :LOG "[INFO]" "Existing '%ENV_FILE%' found at '%ENV_PATH%'. Leaving it unchanged."
    exit /b 0
)

if /i "%ENV_CHOICE%"=="K" (
    call :LOG "[INFO]" "Existing '%ENV_FILE%' found at '%ENV_PATH%'. Leaving it unchanged."
    exit /b 0
)

if /i "%ENV_CHOICE%"=="B" goto :BACKUP_AND_RECREATE_ENV

call :LOG "[WARNING]" "Unrecognized choice '%ENV_CHOICE%'. Leaving '%ENV_FILE%' unchanged at '%ENV_PATH%'."
exit /b 0

:BACKUP_AND_RECREATE_ENV
call :BUILD_ENV_BACKUP_PATH
copy /Y "%ENV_PATH%" "%ENV_BACKUP_FILE%" >nul
if errorlevel 1 (
    call :LOG "[ERROR]" "Failed to back up '%ENV_PATH%' to '%ENV_BACKUP_FILE%'."
    exit /b 1
)

call :LOG "[SUCCESS]" "Backed up '%ENV_PATH%' to '%ENV_BACKUP_FILE%'."
call :COPY_TEMPLATE_TO_ENV
if errorlevel 1 (
    copy /Y "%ENV_BACKUP_FILE%" "%ENV_PATH%" >nul
    if errorlevel 1 (
        call :LOG "[ERROR]" "Failed to recreate '%ENV_PATH%' and failed to restore the backup from '%ENV_BACKUP_FILE%'."
    ) else (
        call :LOG "[WARNING]" "Failed to recreate '%ENV_PATH%'. Restored the original file from backup '%ENV_BACKUP_FILE%'."
    )
    exit /b 1
)

call :LOG "[SUCCESS]" "Recreated '%ENV_FILE%' at '%ENV_PATH%' from '%ENV_TEMPLATE_PATH%' with default values."
exit /b 0

:: :COPY_TEMPLATE_TO_ENV
::   Copies .env.example to .env and returns non-zero on failure.
:COPY_TEMPLATE_TO_ENV
copy /Y "%ENV_TEMPLATE_PATH%" "%ENV_PATH%" >nul
if errorlevel 1 (
    call :LOG "[ERROR]" "Failed to create '%ENV_FILE%' at '%ENV_PATH%' from '%ENV_TEMPLATE_PATH%'."
    exit /b 1
)
exit /b 0

:: :BUILD_ENV_BACKUP_PATH
::   Builds a timestamped backup filename for the current .env file.
:BUILD_ENV_BACKUP_PATH
set "ENV_BACKUP_STAMP="
for /f "usebackq delims=" %%T in (`powershell -NoProfile -Command "Get-Date -Format yyyyMMdd-HHmmss"`) do (
    set "ENV_BACKUP_STAMP=%%T"
)
if not defined ENV_BACKUP_STAMP set "ENV_BACKUP_STAMP=%RANDOM%"
set "ENV_BACKUP_FILE=%ENV_PATH%.backup-%ENV_BACKUP_STAMP%"
goto :eof

:: :COUNTDOWN
::   Prints a message and waits 10 seconds, closing immediately on any keypress.
:COUNTDOWN
if "%SKIP_COUNTDOWN%"=="1" goto :eof
echo.
echo  Closing in 10 seconds - press any key to close now.
timeout /t 10 >nul
goto :eof
