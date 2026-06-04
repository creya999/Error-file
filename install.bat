@echo off
title ADBN Instant Card System - Setup
color 0A

echo ============================================================
echo   Agricultural Development Bank Nepal
echo   Instant Card System - Windows Setup
echo ============================================================
echo.

:: ── Check Python ─────────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH.
    echo.
    echo   Please install Python 3.10 or later from:
    echo   https://www.python.org/downloads/
    echo.
    echo   IMPORTANT: During installation check the box:
    echo   "Add Python to PATH"
    echo.
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('python --version') do echo [OK] %%i found.

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
    python -m venv venv
    echo [OK] Virtual environment created.
)

:: ── Activate venv ────────────────────────────────────────────
call venv\Scripts\activate.bat

:: ── Upgrade pip ──────────────────────────────────────────────
echo [INFO] Upgrading pip...
python -m pip install --upgrade pip --quiet

:: ── Install packages ─────────────────────────────────────────
echo [INFO] Installing required packages (this may take a minute)...
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Package installation failed. Check your internet connection.
    pause
    exit /b 1
)
echo [OK] All packages installed.

:: ── Create .env if missing ───────────────────────────────────
if not exist ".env" (
    echo.
    echo [INFO] Creating .env configuration file...
    copy .env.example .env >nul
    echo [ACTION REQUIRED] Please fill in your SQL Server details in the .env file.
    echo.
    echo Opening .env file for editing...
    notepad .env
)

:: ── Run database migrations ──────────────────────────────────
echo [INFO] Running database migrations...
python migrate.py
if errorlevel 1 (
    echo [WARNING] Migration failed. You can run migrate.py manually later.
) else (
    echo [OK] Database migrations complete.
)

:: ── Import branches ──────────────────────────────────────────
echo [INFO] Importing branch list...
python import_branches.py
if errorlevel 1 (
    echo [WARNING] Branch import failed. You can run import_branches.py manually later.
) else (
    echo [OK] Branches imported successfully.
)

echo.
echo ============================================================
echo   Setup Complete!
echo.
echo   Next steps:
echo   1. Make sure SQL Server is running
echo   2. Create the database in SSMS:
echo      CREATE DATABASE adbn_instant_card;
echo   3. Edit .env with your SQL Server credentials
echo   4. Double-click start.bat to launch the application
echo   5. Open browser: http://localhost:5000
echo   6. Login with  Staff ID: ADMIN001  Password: Admin@1234
echo ============================================================
echo.
pause
