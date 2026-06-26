@echo off
setlocal

echo Starting Wallet Vault Admin...
echo.

cd /d "%~dp0"

if not exist venv\Scripts\python.exe (
    echo ERROR: Run setup.bat first
    exit /b 1
)

start "Wallet Vault API" cmd /k "cd /d %~dp0 && venv\Scripts\uvicorn api.main:app --reload --port 8001"

if not exist admin\node_modules (
    echo Installing admin UI dependencies...
    cd admin
    call npm install
    cd ..
)

start "Wallet Vault Admin UI" cmd /k "cd /d %~dp0admin && npm run dev"

echo.
echo API:      http://127.0.0.1:8001
echo Admin UI: http://localhost:5173
echo.
echo Close the terminal windows to stop the services.
