# CoinWallet

Cross-platform Bitcoin wallet for **Windows**, **Mac**, **iPhone**, and **Samsung / Android** — non-custodial, privacy-focused, with an on-device **Advisor AI** tab for guidance (no trading features).

Public **download website** for all platforms plus an opt-in **leaderboard** showing who holds the most coins.

**Status:** Web prototype complete (Phases 1–4). Download site, leaderboard, and native apps are next.

See **[.cursor/COINWALLET_MASTER_PLAN.md](./.cursor/COINWALLET_MASTER_PLAN.md)** for the full execution plan with granular tasks and 15-minute loop protocol.

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

Copy [`.env.example`](.env.example) to `.env` and set required values. See [Security](#security) below.

### Run

```powershell
.\start_admin.ps1
```

Open http://localhost:5173 — API http://127.0.0.1:8001

### Validate

```powershell
.\venv\Scripts\python.exe scripts\validate_isolation.py
```

Manual testnet steps: [`docs/TESTNET_CHECKLIST.md`](docs/TESTNET_CHECKLIST.md)

## Pages

| Page | Description |
|------|-------------|
| Dashboard | Balances, sync, wallet security status |
| Wallets | Create/import, export xpub, delete |
| Receive / Send | BIP84 addresses, fee preview (unlock required) |
| Coin Control | UTXO freeze, labels, manual coin select |
| Transactions | History with tx labels & explorer links |
| Privacy | Privacy score, entities, exchange exposure |
| Security | Wallet passphrase, lock/unlock, legacy migration |
| Admin | Users, approval, audit log |
| Settings | Account & network (admin: full instance config) |
| Logs | Admin-only server logs |
| **Advisor AI** | Phase 8 — guidance only, no trading |
| **Leaderboard** | Phase 4 — opt-in ranking by wallet balance |

## Docker

```bash
cp .env.example .env
# edit .env
docker compose up --build
```

Caddy reverse proxy on port 80. Set `SECURE_COOKIES=true` and `STRICT_SECRETS=true` for production.

### Database backup

```powershell
.\scripts\backup_db.ps1
```

```bash
./scripts/backup_db.sh
```

## Project Structure

```
CoinWallet/
├── api/              # FastAPI auth, wallet, admin, security
├── admin/            # SvelteKit 5 UI (shared across platforms)
├── site/             # Download website (planned)
├── src/              # database, wallet engine, config
├── scripts/          # validate, backup, seed_admin
├── deploy/           # Caddyfile
└── docs/             # TESTNET_CHECKLIST.md
```

## Tech Stack

- **UI:** SvelteKit 5, Tailwind 4, shadcn-svelte
- **Desktop (planned):** Tauri 2 — Windows + Mac
- **Mobile (planned):** Capacitor — iOS + Android
- **Download site (planned):** SvelteKit marketing site
- **Backend:** Python, FastAPI, SQLite, bcrypt
- **Bitcoin:** embit (BIP39/BIP84/PSBT) + Esplora / optional Core RPC
- **Advisor AI (planned):** On-device rule engine — no trading, no cloud LLM at launch

## Security

### User isolation (Open WebUI-style)

- Per-user wallet encryption — mnemonics encrypted with each user's wallet passphrase
- Wallet unlock sessions (15 min TTL); lock on logout
- API scoped by `user_id`; admins cannot access other users' wallets
- Registration off by default; pending users need admin approval
- Server logs and full settings are admin-only
- Login and wallet-unlock rate limiting

### First use

1. Sign in → **Security** → set wallet passphrase → unlock
2. Create wallet, sync, send on testnet

### Production

- `STRICT_SECRETS=true` — fail startup on weak secrets
- `SECURE_COOKIES=true` — behind HTTPS
- Use Docker + Caddy TLS for remote access
- Run `backup_db` on a schedule

### Trust model

While unlocked, the server signs in-process. User passphrase encryption prevents passive DB theft by the admin. Malicious operators could still patch code.

Never commit `.env`, `wallet.db`, or key material.

## Development Phases

1. **Phase 1** — Foundation ✓
2. **Phase 2** — Wallet core ✓
3. **Phase 3** — Download website (all platforms)
4. **Phase 4** — Leaderboard (opt-in, app + website)
5. **Phase 5** — Desktop apps (Tauri — Windows + Mac)
6. **Phase 6** — Mobile apps (Capacitor — iPhone + Android)
7. **Phase 7** — Wasabi features (coin control, privacy score, labels) ✓
8. **Phase 8** — Advisor AI tab (on-device guidance, no trading)
9. **Phase 9** — Store polish, live sync, optional Core RPC ✓

Full details in [PLAN.md](./PLAN.md).

## Repository name

The git folder may still be named `trading-bot`; the product is **CoinWallet**. Rename locally with:

```bash
git remote -v   # update remote URL after GitHub rename if desired
```
