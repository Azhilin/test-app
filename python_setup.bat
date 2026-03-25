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
set LOG_DIR=logs
set LOG_FILE=logs\install_python.log

:: ============================================================
:: SECTION 1 — PRE-EXECUTION & OS VALIDATION
:: ============================================================

:: OS check
if /i not "%OS%"=="Windows_NT" (
    echo [ERROR] This setup script is designed exclusively for Windows.
    echo         Please use setup.sh for macOS/Linux.
    call :COUNTDOWN
    exit /b 1
)

:: Architecture detection — handles WOW64 case (32-bit cmd on 64-bit Windows)
set ARCH=64
if "%PROCESSOR_ARCHITECTURE%"=="x86" (
    if not defined PROCESSOR_ARCHITEW6432 set ARCH=32
)

:: Change to the script's own directory so relative paths are always correct
cd /d "%~dp0"

:: ============================================================
:: SECTION 2 — LOGGING & USER EXPERIENCE
:: ============================================================

:: Create logs directory if it doesn't exist
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

:: Write a session header to the log file
call :LOG_RAW "========================================================"
call :LOG_RAW "  Python Setup Session Started — %DATE% %TIME%"
call :LOG_RAW "========================================================"

call :LOG "[INFO]" "OS validated: Windows_NT + Architecture: %ARCH%-bit"

:: ============================================================
:: PRIVILEGE ASSESSMENT (Least Privilege Principle)
:: ============================================================
net session >nul 2>&1
if %errorlevel% == 0 (
    call :LOG "[INFO]" "Running with Administrator privileges. Installation will remain per-user (InstallAllUsers=0)."
) else (
    call :LOG "[INFO]" "Running as standard user — per-user installation mode (no UAC prompt required)."
)

:: ============================================================
:: SECTION 3 — PYTHON DETECTION & VERSION VALIDATION
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
:: Extract Major and Minor from "3.12.10" → MAJOR=3, MINOR=12
for /f "tokens=1,2,3 delims=." %%A in ("!PYTHON_VERSION!") do (
    set PYTHON_MAJOR_FOUND=%%A
    set PYTHON_MINOR_FOUND=%%B
)

if not defined PYTHON_MAJOR_FOUND goto :VERSION_PARSE_FAIL
if not defined PYTHON_MINOR_FOUND goto :VERSION_PARSE_FAIL

call :LOG "[INFO]" "Parsed version — Major: !PYTHON_MAJOR_FOUND!  Minor: !PYTHON_MINOR_FOUND!"

:: Validate major version is 3
if not "!PYTHON_MAJOR_FOUND!"=="3" (
    call :LOG "[WARNING]" "Detected Python !PYTHON_VERSION! — major version is not 3. Proceeding to install Python %PYTHON_INSTALL_VERSION%."
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
:: SECTION 4 — PYTHON INSTALLATION (SECURE & SILENT)
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

call :LOG "[INFO]" "Download URL: !INSTALLER_URL!"
call :LOG "[INFO]" "Installer will be saved to: !INSTALLER_FILE!"

:: Secure download via PowerShell with forced TLS 1.2
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

if %errorlevel% neq 0 (
    call :LOG "[ERROR]" "Download failed. Check your internet connection and try again."
    call :COUNTDOWN
    exit /b 1
)

if not exist "!INSTALLER_FILE!" (
    call :LOG "[ERROR]" "Installer file not found after download: !INSTALLER_FILE!"
    call :COUNTDOWN
    exit /b 1
)

call :LOG "[INFO]" "Download complete. Verifying SHA-256 checksum..."

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

:: PATH Refresh — the current cmd session won't see the new PATH without a restart.
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
:: SECTION 5 — VIRTUAL ENVIRONMENT SETUP
:: ============================================================
:SETUP_VENV
call :LOG "[INFO]" "Setting up Python virtual environment in '%VENV_DIR%'..."

:: Create venv using the specific required Python version via the launcher
py -%PYTHON_TARGET% -m venv %VENV_DIR%

if %errorlevel% neq 0 (
    call :LOG "[ERROR]" "Failed to create virtual environment. Check that py -%PYTHON_TARGET% is available."
    call :COUNTDOWN
    exit /b 1
)

:: Verify activation script exists as confirmation the venv was built correctly
if not exist "%VENV_DIR%\Scripts\activate.bat" (
    call :LOG "[ERROR]" "Virtual environment activation script not found at '%VENV_DIR%\Scripts\activate.bat'. Creation may have failed."
    call :COUNTDOWN
    exit /b 1
)

call :LOG "[SUCCESS]" "Virtual environment created at '%VENV_DIR%'."

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
    :AFTER_DEV
)

:: .gitignore check — ensure .venv/ is excluded from version control
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
call :LOG "[SUCCESS]" "================================================================"
call :LOG_RAW "  Session ended — %DATE% %TIME%"
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

:: :COUNTDOWN
::   Prints a message and waits 10 seconds, closing immediately on any keypress.
:COUNTDOWN
echo.
echo  Closing in 10 seconds — press any key to close now.
timeout /t 10 >nul
goto :eof
