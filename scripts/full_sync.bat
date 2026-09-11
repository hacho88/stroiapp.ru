@echo off
chcp 65001 >nul
echo ==========================================
echo   AI StroiApp — FULL SYNC (one-shot)
echo   Upload ALL files to production
echo ==========================================
echo.

cd /d "%~dp0"

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found.
    pause
    exit /b 1
)

python -c "import watchdog, requests, dotenv" >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing dependencies...
    pip install -r requirements.txt
)

python live_sync.py --full
pause
