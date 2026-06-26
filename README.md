# Wallet Vault

A self-hosted, multi-user Bitcoin wallet web platform — Open WebUI-style admin shell with Wasabi-inspired privacy UX.

**Phase 2 complete:** BIP84 wallets (testnet), Esplora sync, receive/send, UTXO and transaction views.

## Quick Start

### Windows

```batch
setup.bat
```

### Mac / Linux

```bash
chmod +x setup.sh
./setup.sh
```

### Configure

1. Copy `.env.example` to `.env`
2. Set **required** wallet and auth values:

```env
WALLET_ENCRYPTION_KEY=<32+ char random secret>
ADMIN_USERNAME=admin
ADMIN_PASSWORD_HASH="<bcrypt hash>"
SESSION_SECRET=<random string>
BITCOIN_NETWORK=testnet
BITCOIN_BACKEND_URI=https://blockstream.info/testnet/api/
```

Generate a password hash:

```powershell
python scripts/hash_password.py yourpassword
```

Or seed the admin user (dev only):

```powershell
python scripts/seed_admin.py
```

### Run

```powershell
.\start_admin.ps1
```

Open http://localhost:5173 and sign in.

API: http://127.0.0.1:8001

## Pages

| Page | Status |
|------|--------|
| Dashboard | Balance overview, sync status |
| Wallets | Create wallets, mnemonic backup |
| Receive | BIP84 receive address + QR |
| Send | Fee preview + broadcast |
| Coin Control | UTXO list (freeze/labels → Phase 3) |
| Transactions | Synced transaction history |
| Privacy | Phase 3 (stub UI) |
| Stats | Wallet aggregates |
| Admin | User management, audit log |
| Settings | Account & network info |

## Project Structure

```
wallet-vault/
├── api/              # FastAPI auth + wallet + admin API
├── admin/            # SvelteKit 5 + shadcn-svelte UI
├── src/
│   ├── database.py   # Users, wallets, UTXOs, transactions, audit
│   └── wallet/       # keys, Esplora backend, wallet engine
├── scripts/          # seed_admin, hash_password
└── data/             # Local wallet engine data (gitignored)
```

## Tech Stack

- **Backend:** Python, FastAPI, SQLite, bcrypt sessions
- **Frontend:** SvelteKit 5, Tailwind 4, shadcn-svelte
- **Bitcoin:** embit (BIP39/BIP84/PSBT) + Esplora (Blockstream testnet API)

## Security

- Non-custodial design — mnemonics encrypted at rest with `WALLET_ENCRYPTION_KEY`
- Mnemonic shown **once** on wallet create; never logged or returned on GET
- Never commit `.env`, `wallet.db`, or key material
- Default to **testnet** until explicitly configured for mainnet
- Admin creates users by default (`OPEN_REGISTRATION=false`)

## Development Phases

1. **Phase 1** — Foundation (auth, schema, UI shell) ✓
2. **Phase 2** — Wallet core (keys, Esplora sync, send/receive) ✓
3. **Phase 3** — Wasabi features (coin control, privacy score, labels)
4. **Phase 4** — WebSocket live sync, Bitcoin Core RPC, node integration
