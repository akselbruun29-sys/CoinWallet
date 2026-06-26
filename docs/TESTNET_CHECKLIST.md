# Testnet validation checklist

## Automated (API running)

```powershell
.\venv\Scripts\python.exe scripts\validate_isolation.py
```

Optional second user:

```powershell
$env:VALIDATE_TEST_USER="alice"
$env:VALIDATE_TEST_PASS="yourpassword"
.\venv\Scripts\python.exe scripts\validate_isolation.py
```

## Manual flow

1. **Security** — set wallet passphrase and unlock.
2. **Wallets** — create a testnet wallet; save the mnemonic backup.
3. **Receive** — copy address; fund from a testnet faucet (e.g. [testnet-faucet.com](https://testnet-faucet.com) or [coinfaucet.eu](https://coinfaucet.eu/en/btc-testnet/)).
4. **Wallets** or header — **Sync**; confirm balance on Dashboard.
5. **Send** — preview and send a small amount to another testnet address.
6. **Transactions** — confirm tx appears with explorer link.

## Multi-user isolation

1. **Admin** → create user `alice` / password.
2. Sign in as `alice` → set her wallet passphrase → create wallet.
3. Sign in as `admin` → confirm alice's wallet is not visible.
4. Run `validate_isolation.py` with `VALIDATE_TEST_USER=alice`.

## Legacy encryption migration

1. **Security** — if `legacy_wallet_count > 0`, set or enter wallet passphrase.
2. Confirm `legacy_wallet_count` becomes `0`.
