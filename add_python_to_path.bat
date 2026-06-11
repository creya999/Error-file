@echo off
title Add Python to PATH
color 0A

echo ============================================================
echo   Add Python to Windows PATH
echo ============================================================
echo.
echo   Run this script as Administrator if it fails.
echo.

:: ── Try to find Python location ───────────────────────────────
set PYTHON_DIR=
set PYTHON_SCRIPTS=

:: Check common install locations
for %%P in (
    "%LOCALAPPDATA%\Programs\Python\Python313"
    "%LOCALAPPDATA%\Programs\Python\Python312"
    "%LOCALAPPDATA%\Programs\Python\Python311"
    "%LOCALAPPDATA%\Programs\Python\Python310"
    "%LOCALAPPDATA%\Programs\Python\Python39"
    "C:\Python313"
    "C:\Python312"
    "C:\Python311"
    "C:\Python310"
    "C:\Python39"
    "C:\Program Files\Python313"
    "C:\Program Files\Python312"
    "C:\Program Files\Python311"
    "C:\Program Files\Python310"
) do (
    if exist %%P\python.exe (
        set PYTHON_DIR=%%~P
        set PYTHON_SCRIPTS=%%~P\Scripts
        goto :found
    )
)

:: If not found in common paths, try where command
for /f "tokens=*" %%i in ('where python 2^>nul') do (
    if exist "%%i" (
        for %%F in ("%%i") do set PYTHON_DIR=%%~dpF
        set PYTHON_DIR=%PYTHON_DIR:~0,-1%
        set PYTHON_SCRIPTS=%PYTHON_DIR%\Scripts
        goto :found
    )
)

echo [ERROR] Could not find Python installation automatically.
echo.
echo   Please find your Python folder manually:
echo   1. Search for python.exe in File Explorer
echo   2. Copy the folder path (e.g. C:\Users\YourName\AppData\Local\Programs\Python\Python312)
echo   3. Add that path and the \Scripts subfolder to PATH manually:
echo      - Open Start menu, search "Edit system environment variables"
echo      - Click Environment Variables
echo      - Under User variables, select Path and click Edit
echo      - Click New and add both paths
echo.
pause
exit /b 1

:found
echo [OK] Found Python at: %PYTHON_DIR%
echo [OK] Scripts folder:  %PYTHON_SCRIPTS%
echo.

:: ── Add to user PATH via registry (no admin needed) ───────────
setx PATH "%PATH%;%PYTHON_DIR%;%PYTHON_SCRIPTS%"

if errorlevel 1 (
    echo.
    echo [ERROR] Failed to update PATH.
    echo         Try running this script as Administrator:
    echo         Right-click add_python_to_path.bat -> Run as administrator
    echo.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   Done! Python has been added to your PATH.
echo.
echo   IMPORTANT: Close this window and open a NEW Command Prompt
echo   for the change to take effect.
echo.
echo   Then verify by running:
echo     python --version
echo ============================================================
echo.
pause
