#!/bin/bash
set -e

echo "=== Wallet Vault Setup ==="
echo "Step 1: Checking Python..."
python3 --version || { echo "Python 3.10+ required"; exit 1; }

echo "Step 2: Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

echo "Step 3: Installing dependencies..."
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

echo "Step 4: Creating .env file..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo ".env created. Configure admin credentials and WALLET_ENCRYPTION_KEY"
else
    echo ".env already exists (skipped)"
fi

echo "Step 5: Creating logs and data directories..."
mkdir -p logs data/bdk

echo "Step 6: Testing imports..."
python -c "from src.database import WalletDatabase; from src.wallet.core import WalletService; print('All imports successful')" || {
    echo "Import failed. Check requirements.txt"
    exit 1
}

echo ""
echo "=== Setup Complete ==="
echo "Next steps:"
echo "1. Set ADMIN_PASSWORD_HASH and SESSION_SECRET in .env"
echo "2. Set WALLET_ENCRYPTION_KEY in .env"
echo "3. Run: ./start_admin.ps1 or uvicorn + npm run dev"
