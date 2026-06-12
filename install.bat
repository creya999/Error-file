@echo off
title ADBL Instant Card System - Setup
color 0A

echo ============================================================
echo   Agricultural Development Bank Nepal
echo   Instant Card System - Windows Setup
echo ============================================================
echo.

:: ── Check Python ─────────────────────────────────────────────
:: Try 'python' first, then fall back to 'py' (Python Launcher for Windows)
set PYTHON_CMD=python
python --version >nul 2>&1
if errorlevel 1 (
    py --version >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] Python is not installed or not in PATH.
        echo.
        echo   Please install Python 3.10 - 3.12 from:
        echo   https://www.python.org/downloads/
        echo.
        echo   IMPORTANT: During installation, check the box:
        echo   "Add Python to PATH"
        echo.
        echo   After installing, close this window and run install.bat again.
        echo.
        pause
        exit /b 1
    )
    set PYTHON_CMD=py
)
for /f "tokens=*" %%i in ('%PYTHON_CMD% --version') do echo [OK] %%i found.

:: ── Check ODBC Driver ────────────────────────────────────────
reg query "HKLM\SOFTWARE\ODBC\ODBCINST.INI\ODBC Driver 17 for SQL Server" >nul 2>&1
if errorlevel 1 (
    echo.
    echo [WARNING] ODBC Driver 17 for SQL Server not found.
    echo   Please download and install it from:
    echo   https://aka.ms/odbc17
    echo.
    echo   Setup will continue but the app will not connect to SQL Server
    echo   until the ODBC driver is installed.
    echo.
    pause
)

:: ── Create virtual environment ───────────────────────────────
if not exist "venv" (
    echo [INFO] Creating Python virtual environment...
    %PYTHON_CMD% -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created.
) else (
    echo [OK] Virtual environment already exists.
)

:: ── Use full venv paths — no reliance on activate ─────────────
set VENV_PYTHON=%~dp0venv\Scripts\python.exe

if not exist "%VENV_PYTHON%" (
    echo [ERROR] venv\Scripts\python.exe not found.
    echo         Delete the venv folder and run install.bat again.
    pause
    exit /b 1
)

:: ── Upgrade pip ──────────────────────────────────────────────
echo [INFO] Upgrading pip...
"%VENV_PYTHON%" -m pip install --upgrade pip --quiet

:: ── Install packages ─────────────────────────────────────────
echo [INFO] Installing required packages (this may take a minute)...
"%VENV_PYTHON%" -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo [ERROR] Package installation failed.
    echo   - Check your internet connection
    echo   - Make sure Microsoft C++ Build Tools are installed (required for pyodbc):
    echo     https://visualstudio.microsoft.com/visual-cpp-build-tools/
    echo     Select "Desktop development with C++" during install.
    echo.
    pause
    exit /b 1
)
echo [OK] All packages installed.

:: ── Create .env if missing ───────────────────────────────────
if not exist ".env" (
    echo.
    echo [INFO] Creating .env configuration file from template...
    copy .env.example .env >nul
    echo [ACTION REQUIRED] Fill in your SQL Server details in the .env file.
    echo.
    echo   Opening .env in Notepad — save and close when done...
    notepad .env
    echo.
    echo [INFO] Waiting for you to save .env before continuing...
    pause
)

:: ── Run database migrations ──────────────────────────────────
echo [INFO] Running database migrations...
"%VENV_PYTHON%" migrate.py
if errorlevel 1 (
    echo [WARNING] Migration failed. Ensure .env credentials are correct,
    echo           then run:  venv\Scripts\python.exe migrate.py
) else (
    echo [OK] Database migrations complete.
)

:: ── Fix legacy roles (safe to run on fresh installs too) ─────
echo [INFO] Checking for legacy data (role fixes)...
"%VENV_PYTHON%" fix_roles.py
if errorlevel 1 (
    echo [WARNING] fix_roles.py failed. Run manually if upgrading from an older version.
) else (
    echo [OK] Role check complete.
)

:: ── Import branches ──────────────────────────────────────────
echo [INFO] Importing branch list...
"%VENV_PYTHON%" import_branches.py
if errorlevel 1 (
    echo [WARNING] Branch import failed. Run manually:
    echo           venv\Scripts\python.exe import_branches.py
) else (
    echo [OK] Branches imported successfully.
)

echo.
echo ============================================================
echo   Setup Complete!
echo.
echo   Before starting, make sure:
echo   1. SQL Server is running
echo   2. Database exists in SSMS:
echo        CREATE DATABASE adbl_instant_card;
echo   3. .env has correct DB credentials
echo.
echo   Then double-click start.bat to launch the app.
echo.
echo   Open browser : http://localhost:5000
echo   Login        : Staff ID  ADMIN001
echo                  Password  Admin@1234
echo.
echo   Change the admin password immediately after first login!
echo ============================================================
echo.
pause
