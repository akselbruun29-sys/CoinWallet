# Wallet Vault

A self-hosted, multi-user Bitcoin wallet web platform — Open WebUI-style admin shell with Wasabi-inspired privacy UX.

---

## For users

Everything below is for running and using Wallet Vault day to day.

### What you get

- BIP84 Bitcoin wallets (testnet by default)
- Receive addresses with QR codes
- Send with fee preview
- Coin control (freeze UTXOs, labels)
- Privacy score and entity tagging
- Per-user wallet encryption — admins cannot spend your coins without your wallet passphrase
- Mobile-friendly UI (bottom nav on phones)

### Quick start

**Windows**

```batch
setup.bat
```

**Mac / Linux**

```bash
chmod +x setup.sh
./setup.sh
```

**Configure**

1. Copy `.env.example` to `.env`
2. Set required values:

```env
WALLET_ENCRYPTION_KEY=<32+ char random secret>
ADMIN_USERNAME=admin
ADMIN_PASSWORD_HASH="<bcrypt hash>"
SESSION_SECRET=<random string>
BITCOIN_NETWORK=testnet
BITCOIN_BACKEND_URI=https://blockstream.info/testnet/api/
WALLET_DB=wallet.db
```

Generate a password hash:

```powershell
python scripts/hash_password.py yourpassword
```

Or seed the admin user (dev only):

```powershell
python scripts/seed_admin.py
```

**Run**

```powershell
.\start_admin.ps1
```

| Service | URL |
|---------|-----|
| UI | http://localhost:5173 |
| API | http://127.0.0.1:8001 |

Sign in with `admin` and the password matching your `ADMIN_PASSWORD_HASH`.

Stop with `.\stop_admin.ps1` or close the service windows.

### First use

1. Sign in
2. Open **Security** and set your **wallet passphrase** (separate from your login password)
3. Unlock, then create a wallet under **Wallets**
4. **Sync**, then use **Receive** / **Send**

Your wallet passphrase encrypts your recovery phrases. The server admin cannot decrypt them without it.

### Using on your phone

On the same Wi‑Fi, open `http://<your-pc-ip>:5173` in the browser.

- Bottom nav: Home, Wallets, Receive, Send, More (sidebar)
- Tables scroll horizontally on small screens
- Forms and buttons stack for touch use

### App pages

| Page | What it does |
|------|----------------|
| Dashboard | Balance, sync status, quick actions |
| Wallets | Create, import, select wallets |
| Receive | Fresh BIP84 address + QR |
| Send | Preview fees, broadcast |
| Coin Control | Freeze UTXOs, add labels |
| Transactions | History after sync |
| Privacy | Privacy score, UTXO breakdown |
| Stats | Wallet aggregates |
| Security | Passphrase, lock/unlock, legacy migration |
| Settings | Account, password, network (admin) |
| Admin | Users, approval, audit (admin only) |
| Logs | Server logs (admin only) |

### Security (what you should know)

- **Login password** — gets you into the app
- **Wallet passphrase** — unlocks your keys for sync, receive, and send
- **Unlock session** — expires after ~15 minutes; lock when done
- **Registration** — off by default; new users may need admin approval
- **Testnet first** — use testnet coins until you deliberately enable mainnet

Never share your recovery phrase or wallet passphrase. The operator still hosts the server and could change code — only use instances you trust.

### Troubleshooting

**Can't log in**

- Verify hash: `python scripts/hash_password.py yourpassword` matches `ADMIN_PASSWORD_HASH` in `.env`
- Health check: `GET http://127.0.0.1:8001/api/health` → `{"status":"ok"}`
- Hard-refresh or clear session storage if an old token is stuck

**Port already in use**

```powershell
.\stop_admin.ps1
```

Then start again.

---

## AI context

Everything below is for AI assistants and developers working on this repo. Prefer minimal, focused diffs. Do not commit unless asked. Do not run tests unless asked.

### Project identity

Self-hosted **multi-user Bitcoin wallet** (testnet first). Not a trading bot — repo folder name is legacy.

### Architecture

```
trading-bot/
├── api/
│   ├── main.py       # FastAPI app, auth, status, CORS
│   ├── wallet.py     # Wallet CRUD, sync, send, UTXOs, privacy
│   ├── security.py   # Per-user wallet passphrase, lock/unlock, v1→v2 migration
│   ├── admin.py      # Users, settings, audit
│   └── events.py     # WebSocket hub (/api/ws)
├── admin/            # SvelteKit 5 + Tailwind 4 + shadcn-svelte
├── src/
│   ├── database.py   # SQLite: users, wallets, UTXOs, txs, audit
│   └── wallet/       # BIP84 keys, Esplora backend, embit PSBT engine
└── scripts/          # hash_password, seed_admin, test_login
```

**Ports:** API `8001`, UI dev server `5173`. Start stack: `.\start_admin.ps1`

**Stack:** Python/FastAPI/SQLite · SvelteKit 5 · embit + Esplora (Blockstream testnet API)

### Safety rules (non-negotiable)

- Default to **testnet** (`BITCOIN_NETWORK=testnet`)
- Never expose `encrypted_seed`, mnemonics, or passphrases in GET responses or audit logs
- Gate mainnet behind explicit config (`ALLOW_MAINNET`, admin settings)
- Never commit `.env`, `wallet.db`, `trading_bot.db`, or key material
- Wallet routes scoped by `user_id` — admins must not access other users' wallets via API
- Audit sensitive actions (`WALLET_CREATED`, `TX_SENT`) without secrets

### Development guidelines

- Use **Esplora** for chain data; Bitcoin Core RPC is Phase 4
- Encrypt seeds at rest with `WALLET_ENCRYPTION_KEY` (server pepper) + per-user passphrase (v2)
- Signing requires unlocked wallet session (`WALLET_UNLOCK_TTL`, default 900s)
- UI: match existing shadcn-svelte patterns; mobile layout uses `MobileNav`, `ScrollTable`, responsive header
- Keep changes minimal — no drive-by refactors or extra abstractions
- Comments only for non-obvious business logic
- Match repo conventions for naming, imports, and file layout

### Key env vars

| Variable | Purpose |
|----------|---------|
| `WALLET_ENCRYPTION_KEY` | Server pepper for vault crypto |
| `ADMIN_PASSWORD_HASH` | Bcrypt login hash (quote in `.env`) |
| `SESSION_SECRET` | Session cookie signing |
| `WALLET_DB` | SQLite path (default `wallet.db`) |
| `OPEN_REGISTRATION` | Public signup (default `false`) |
| `AUTO_APPROVE_USERS` | Skip pending role (default `true`) |
| `BITCOIN_BACKEND_URI` | Esplora base URL |
| `WALLET_UNLOCK_TTL` | Unlock session seconds |

### Phase status

1. **Phase 1** — Auth, schema, UI shell ✓
2. **Phase 2** — Keys, Esplora sync, send/receive ✓
3. **Phase 3** — Coin control, privacy score, labels — in progress
4. **Phase 4** — WebSocket live sync ✓ · Core RPC · node integration — planned

### Cursor rule

Project rule file: `.cursor/rules/wallet-vault.mdc` — keep in sync when architecture or safety rules change.
