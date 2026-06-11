@echo off
title ADBN - Install as Windows Service
color 0A

echo ============================================================
echo   ADBN Instant Card System - Install as Windows Service
echo   Run this as Administrator!
echo ============================================================
echo.

:: Check admin rights
net session >nul 2>&1
if errorlevel 1 (
    echo [ERROR] This script must be run as Administrator.
    echo   Right-click install_service.bat and choose "Run as administrator"
    echo.
    pause
    exit /b 1
)

:: Check NSSM exists
if not exist "%~dp0nssm.exe" (
    echo [ERROR] nssm.exe not found in project folder.
    echo.
    echo   1. Download NSSM from: https://nssm.cc/download
    echo   2. Extract nssm.exe into this project folder
    echo   3. Run this script again
    echo.
    pause
    exit /b 1
)

set PROJECT_DIR=%~dp0
set PROJECT_DIR=%PROJECT_DIR:~0,-1%
set PYTHON_EXE=%PROJECT_DIR%\venv\Scripts\python.exe
set SERVE_PY=%PROJECT_DIR%\serve.py
set SERVICE_NAME=ADBN-InstantCard

if not exist "%PYTHON_EXE%" (
    echo [ERROR] venv not found. Please run install.bat first.
    pause
    exit /b 1
)

:: Remove existing service if present
sc query "%SERVICE_NAME%" >nul 2>&1
if not errorlevel 1 (
    echo [INFO] Removing existing service...
    "%~dp0nssm.exe" stop "%SERVICE_NAME%" >nul 2>&1
    "%~dp0nssm.exe" remove "%SERVICE_NAME%" confirm
)

:: Create logs folder
if not exist "%PROJECT_DIR%\logs" mkdir "%PROJECT_DIR%\logs"

:: Install service
echo [INFO] Installing Windows service...
"%~dp0nssm.exe" install "%SERVICE_NAME%" "%PYTHON_EXE%" "%SERVE_PY%"
"%~dp0nssm.exe" set "%SERVICE_NAME%" AppDirectory "%PROJECT_DIR%"
"%~dp0nssm.exe" set "%SERVICE_NAME%" DisplayName "ADBN Instant Card System"
"%~dp0nssm.exe" set "%SERVICE_NAME%" Description "Agricultural Development Bank Nepal - Instant Card Request System"
"%~dp0nssm.exe" set "%SERVICE_NAME%" Start SERVICE_AUTO_START
"%~dp0nssm.exe" set "%SERVICE_NAME%" AppStdout "%PROJECT_DIR%\logs\app.log"
"%~dp0nssm.exe" set "%SERVICE_NAME%" AppStderr "%PROJECT_DIR%\logs\error.log"
"%~dp0nssm.exe" set "%SERVICE_NAME%" AppRotateFiles 1
"%~dp0nssm.exe" set "%SERVICE_NAME%" AppRotateBytes 10485760

:: Start service
echo [INFO] Starting service...
"%~dp0nssm.exe" start "%SERVICE_NAME%"

echo.
echo ============================================================
echo   Done! Service is running in the background.
echo.
echo   App URL  : http://localhost:5000
echo   Logs     : %PROJECT_DIR%\logs\
echo.
echo   To manage the service (run as Administrator):
echo     Stop    : nssm stop %SERVICE_NAME%
echo     Start   : nssm start %SERVICE_NAME%
echo     Restart : nssm restart %SERVICE_NAME%
echo     Remove  : nssm remove %SERVICE_NAME% confirm
echo.
echo   Or open services.msc and look for "ADBN Instant Card System"
echo ============================================================
echo.
pause
