@echo off
setlocal enabledelayedexpansion

echo === Wallet Vault Setup ===
echo Step 1: Checking Python...
python --version >nul 2>&1 || (
    echo ERROR: Python 3.10+ required
    exit /b 1
)

echo Step 2: Creating virtual environment...
python -m venv venv
call venv\Scripts\activate.bat

echo Step 3: Installing dependencies...
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

echo Step 4: Creating .env file...
if not exist .env (
    copy .env.example .env
    echo CREATED .env - configure admin credentials and WALLET_ENCRYPTION_KEY
) else (
    echo .env already exists (skipped)
)

echo Step 5: Creating logs and data directories...
if not exist logs mkdir logs
if not exist data\bdk mkdir data\bdk

echo Step 6: Testing imports...
python -c "from src.database import WalletDatabase; from src.wallet.core import WalletService; print('All imports successful')" || (
    echo ERROR: Import failed
    exit /b 1
)

echo.
echo === Setup Complete ===
echo Next steps:
echo 1. Set ADMIN_PASSWORD_HASH and SESSION_SECRET in .env
echo 2. Set WALLET_ENCRYPTION_KEY (32+ char secret) in .env
echo 3. Run: .\start_admin.ps1
