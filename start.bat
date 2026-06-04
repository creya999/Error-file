@echo off
title ADBN Instant Card System
color 0A

echo ============================================================
echo   Agricultural Development Bank Nepal
echo   Instant Card System — Production Server
echo ============================================================
echo.

:: Activate virtual environment
if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found.
    echo         Please run install.bat first.
    pause
    exit /b 1
)

call venv\Scripts\activate.bat

:: Check .env exists
if not exist ".env" (
    echo [ERROR] .env file not found.
    echo         Please run install.bat first and fill in your database credentials.
    pause
    exit /b 1
)

echo [INFO] Starting ADBN Instant Card System (Production / Waitress)...
echo [INFO] Listening on 127.0.0.1:5000
echo [INFO] Access via your configured domain over VPN
echo [INFO] Press CTRL+C to stop the server.
echo.

python serve.py

pause
