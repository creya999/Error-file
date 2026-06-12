@echo off
title ADBL Instant Card System
color 0A

echo ============================================================
echo   Agricultural Development Bank Nepal
echo   Instant Card System — Production Server
echo ============================================================
echo.

:: ── Check virtual environment ─────────────────────────────────
if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found.
    echo         Please run install.bat first.
    pause
    exit /b 1
)

call venv\Scripts\activate.bat
set VENV_PYTHON=%~dp0venv\Scripts\python.exe

:: ── Check .env ───────────────────────────────────────────────
if not exist ".env" (
    echo [ERROR] .env file not found.
    echo         Please run install.bat first and fill in your database credentials.
    pause
    exit /b 1
)

:: ── Run any pending migrations ────────────────────────────────
echo [INFO] Checking for pending database migrations...
"%VENV_PYTHON%" migrate.py
if errorlevel 1 (
    echo [WARNING] Migration check failed — continuing anyway.
) else (
    echo [OK] Database is up to date.
)

echo.
echo [INFO] Starting ADBL Instant Card System (Production / Waitress)...
echo [INFO] Listening on 127.0.0.1:5000
echo [INFO] Access via your configured domain over VPN
echo [INFO] Press CTRL+C to stop the server.
echo.

"%VENV_PYTHON%" serve.py

pause
