# CoinWallet

Cross-platform Bitcoin wallet for **Windows**, **Mac**, **iPhone**, and **Samsung / Android** — non-custodial, privacy-focused, with an on-device **Advisor AI** tab for guidance (no trading features).

Public **download website** for all platforms plus an opt-in **leaderboard** showing who holds the most coins.

**Current milestone:** Web prototype complete (Phases 1–2). Download site and leaderboard are next.

See **[.cursor/COINWALLET_MASTER_PLAN.md](./.cursor/COINWALLET_MASTER_PLAN.md)** for the full execution plan with granular tasks and 15-minute loop protocol.

## Quick Start (dev — web prototype)

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

## App Tabs

| Tab | Status |
|-----|--------|
| Dashboard | Balance overview, sync status |
| Wallets | Create wallets, mnemonic backup |
| Receive | BIP84 receive address + QR |
| Send | Fee preview + broadcast |
| Coin Control | UTXO list (freeze/labels → Phase 5) |
| Transactions | Synced transaction history |
| Privacy | Phase 5 (stub UI) |
| **Advisor AI** | Phase 8 — guidance only, no trading |
| **Leaderboard** | Phase 4 — opt-in ranking by wallet balance |
| Stats | Wallet aggregates |
| Admin | User management, audit log (self-host mode) |
| Settings | Account & network info |

## Project Structure

```
CoinWallet/
├── api/              # FastAPI auth + wallet + admin + leaderboard API
├── admin/            # SvelteKit 5 + shadcn-svelte UI (shared across platforms)
├── site/             # Download website (planned) — downloads + public leaderboard
├── src/
│   ├── database.py   # Users, wallets, UTXOs, transactions, audit
│   └── wallet/       # keys, Esplora backend, wallet engine
├── scripts/          # seed_admin, hash_password
└── data/             # Local wallet engine data (gitignored)
```

## Tech Stack

- **UI:** SvelteKit 5, Tailwind 4, shadcn-svelte
- **Desktop (planned):** Tauri 2 — Windows + Mac
- **Mobile (planned):** Capacitor — iOS + Android
- **Download site (planned):** SvelteKit marketing site — all platform downloads + public leaderboard
- **Backend:** Python, FastAPI, SQLite, bcrypt sessions
- **Bitcoin:** embit (BIP39/BIP84/PSBT) + Esplora (Blockstream testnet API)
- **Advisor AI (planned):** On-device rule engine — no trading, no cloud LLM at launch

## Security

- Non-custodial design — mnemonics encrypted at rest with `WALLET_ENCRYPTION_KEY`
- Mnemonic shown **once** on wallet create; never logged or returned on GET
- Never commit `.env`, `wallet.db`, or key material
- Default to **testnet** until explicitly configured for mainnet
- Admin creates users by default (`OPEN_REGISTRATION=false`) in self-host mode

## Development Phases

1. **Phase 1** — Foundation (auth, schema, UI shell) ✓
2. **Phase 2** — Wallet core (keys, Esplora sync, send/receive) ✓
3. **Phase 3** — Download website (all platforms)
4. **Phase 4** — Leaderboard (opt-in, app + website)
5. **Phase 5** — Desktop apps (Tauri — Windows + Mac)
6. **Phase 6** — Mobile apps (Capacitor — iPhone + Android)
7. **Phase 7** — Wasabi features (coin control, privacy score, labels)
8. **Phase 8** — Advisor AI tab (on-device guidance, no trading)
9. **Phase 9** — Store polish, live sync, optional Core RPC

Full details in [PLAN.md](./PLAN.md).
