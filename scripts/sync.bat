@echo off
chcp 65001 >nul
echo ==========================================
echo   AI StroiApp — LIVE SYNC
echo   Auto-upload files to production
echo ==========================================
echo.

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

REM Проверяем Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Install Python 3.10+ and add to PATH.
    pause
    exit /b 1
)

REM Проверяем зависимости
python -c "import watchdog, requests, dotenv" >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing dependencies...
    pip install -r requirements.txt
)

REM Запускаем live sync в watch-режиме
echo [INFO] Starting live sync... Press Ctrl+C to stop.
echo.
python live_sync.py --watch

pause
