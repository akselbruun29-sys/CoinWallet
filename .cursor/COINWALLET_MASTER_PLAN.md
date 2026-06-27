# CoinWallet — Master Plan (AI must read this first)

> **This file is the single source of truth.** Every agent session and every 15-minute loop tick starts here.
> State tracker: `.cursor/LOOP_STATE.json` · Human log: `PROGRESS.md`

---

## 1. Loop protocol (15 minutes)

### On every loop tick OR when user says "continue" / "loop" / no specific task

1. Read this file completely.
2. Read `.cursor/LOOP_STATE.json`.
3. Read `PROGRESS.md` (last 5 entries).
4. Find the **lowest-numbered incomplete task** (e.g. `3.1` before `3.2`).
5. Implement **exactly ONE task** end-to-end in this tick.
6. Update state:
   - Set `current_task_id` to the **next** incomplete task.
   - Append task id to `completed_tasks`.
   - Set `last_loop_at` to ISO timestamp.
   - Set `last_completed_task` to the task just finished.
   - When all tasks in a phase are done, increment `current_phase` and update `phase_name`.
7. Append one row to `PROGRESS.md` loop log.
8. If blocked, write `notes` in `LOOP_STATE.json` and pick the next unblocked task in the same phase; do not skip phases.

### Loop constraints

- **One task per tick** — no bundling unless the task is trivial (<5 lines).
- **No commits** unless the user explicitly asks.
- **No tests** unless the user asks (they test manually).
- **Minimize cost** — free Esplora, no paid LLM APIs, no cloud hosting until deploy tasks.
- **Minimize scope** — match existing code style; no unrelated refactors.
- **Safety** — testnet default; never log or return mnemonics; never expose `encrypted_seed` in GET.

### Loop interval

Background timer fires every **15 minutes** (`900s`) with sentinel `AGENT_LOOP_TICK_COINWALLET`.

---

## 2. Product vision

**CoinWallet** — cross-platform non-custodial Bitcoin wallet for:

| Platform | Technology | Distribution |
|----------|------------|--------------|
| Windows | Tauri 2 | `.exe` via download site |
| Mac | Tauri 2 | `.dmg` via download site |
| iPhone | Capacitor | App Store link on download site |
| Samsung / Android | Capacitor | APK + Play Store link on download site |

**Public download website** — home, downloads (all platforms), leaderboard, privacy/terms.

**In-app tabs:** Dashboard · Wallets · Receive · Send · Coin Control · Transactions · Privacy · Advisor AI · Leaderboard · Settings

**Out of scope forever:** trading AI, buy/sell signals, exchange integration, automated trades, cloud LLM for wallet data.

---

## 3. Architecture

```
site/                    ← Download website (SvelteKit static)
admin/                   ← Wallet app UI (SvelteKit 5 + shadcn-svelte) — shared on all platforms
api/                     ← FastAPI (auth, wallet, leaderboard, admin)
src/wallet/              ← BIP84 keys, Esplora sync, wallet engine (embit)
src/database.py          ← SQLite schema
releases/                ← Build artifacts + releases.json manifest (gitignored binaries)
.cursor/
  COINWALLET_MASTER_PLAN.md   ← THIS FILE
  LOOP_STATE.json             ← Current task pointer
```

**Data flow — leaderboard (opt-in only):**
App syncs wallet → if opt-in → `POST /api/leaderboard/update` with `{ display_name, balance_sats, network }` → SQLite → `GET /api/leaderboard?network=testnet` → app tab + site page.

**Advisor AI:** on-device rule engine in `admin/src/lib/advisor/` — templates + wallet state; no network calls.

---

## 4. Existing codebase (Phases 1–2 ✓)

Already built — do not rebuild:

- FastAPI auth (sessions, bcrypt, admin users)
- Wallet CRUD, BIP84 create/import, encrypted seeds
- Esplora sync, receive, send, fee preview
- UTXO list, transactions, dashboard, settings
- SvelteKit admin shell with sidebar nav

Key paths:
- `api/main.py`, `api/wallet.py`, `api/auth.py`, `api/admin.py`
- `src/wallet/core.py`, `src/wallet/bdk_wallet.py`, `src/wallet/keys.py`
- `admin/src/routes/(app)/` — page routes
- `admin/src/lib/components/app-sidebar.svelte` — nav items

---

## 5. Phase 1 — Foundation ✓

| ID | Task | Status |
|----|------|--------|
| 1.1 | FastAPI app + CORS + health | ✓ |
| 1.2 | SQLite schema (users, wallets, audit) | ✓ |
| 1.3 | Session auth + admin role | ✓ |
| 1.4 | SvelteKit shell + login | ✓ |
| 1.5 | Sidebar layout + route structure | ✓ |

---

## 6. Phase 2 — Wallet core ✓

| ID | Task | Status |
|----|------|--------|
| 2.1 | BIP84 key generation + encrypted seed storage | ✓ |
| 2.2 | Esplora backend + wallet sync | ✓ |
| 2.3 | Receive page (address + QR) | ✓ |
| 2.4 | Send page (preview + broadcast) | ✓ |
| 2.5 | UTXO list page | ✓ |
| 2.6 | Transactions page | ✓ |
| 2.7 | Dashboard balance overview | ✓ |
| 2.8 | Settings (network, passphrase) | ✓ |

---

## 7. Phase 3 — Download website

**Goal:** Public `site/` SvelteKit project — marketing + downloads for all platforms.

| ID | Task | Deliverable |
|----|------|-------------|
| 3.1 | Scaffold `site/` SvelteKit project (Tailwind, match admin aesthetic) | `site/package.json`, `site/src/routes/+page.svelte` |
| 3.2 | Home page — hero, features, CTA to /download | `site/src/routes/+page.svelte` |
| 3.3 | Download page — 4 platform cards (Windows, Mac, iPhone, Android) | `site/src/routes/download/+page.svelte` |
| 3.4 | OS auto-detect — highlight current platform on /download | `site/src/lib/detect-os.ts` |
| 3.5 | `releases.json` manifest — version, URLs, SHA-256 per platform | `releases/releases.json` |
| 3.6 | Privacy page — non-custodial + leaderboard opt-in policy | `site/src/routes/privacy/+page.svelte` |
| 3.7 | Terms page (minimal) | `site/src/routes/terms/+page.svelte` |
| 3.8 | Shared nav header/footer across site pages | `site/src/lib/components/SiteNav.svelte` |
| 3.9 | Leaderboard page shell (static layout; API wired in Phase 4) | `site/src/routes/leaderboard/+page.svelte` |
| 3.10 | Static adapter config for Cloudflare Pages / GitHub Pages | `site/svelte.config.js` adapter-static |
| 3.11 | README section — how to build and deploy site | `site/README.md` |

**Download page buttons (until real builds exist):**
- Windows → `releases/coinwallet-windows-x64.exe` (placeholder `#` ok with "Coming soon" badge)
- Mac → `releases/coinwallet-macos.dmg`
- iPhone → App Store URL placeholder
- Android → `releases/coinwallet-android.apk`

---

## 8. Phase 4 — Leaderboard

**Goal:** Opt-in public ranking by total wallet balance — app tab + site page + API.

| ID | Task | Deliverable |
|----|------|-------------|
| 4.1 | DB table `leaderboard_entries` (user_id, display_name, balance_sats, network, updated_at, opted_in) | `src/database.py` migration |
| 4.2 | `GET /api/leaderboard?network=testnet&limit=100` — public, no auth | `api/leaderboard.py` |
| 4.3 | `POST /api/leaderboard/opt-in` — body: `{ display_name, opted_in }` | `api/leaderboard.py` |
| 4.4 | `POST /api/leaderboard/update` — auth required; body: `{ balance_sats, network }` | `api/leaderboard.py` |
| 4.5 | Register leaderboard router in `api/main.py` | |
| 4.6 | Settings UI — leaderboard opt-in toggle + display name field | `admin/src/routes/(app)/settings/+page.svelte` |
| 4.7 | Push balance on wallet sync when opted in | hook in sync flow / `api/wallet.py` |
| 4.8 | App `/leaderboard` route — top N + user's rank | `admin/src/routes/(app)/leaderboard/+page.svelte` |
| 4.9 | Sidebar nav entry for Leaderboard | `app-sidebar.svelte` |
| 4.10 | Wire `site/leaderboard` page to public API | fetch from API URL env |
| 4.11 | Separate testnet / mainnet tabs on leaderboard UI | both app and site |

**Privacy rules:**
- Never send addresses, mnemonics, UTXOs, or tx history to leaderboard API.
- Opt-out removes entry immediately.
- Default: opted out.

---

## 9. Phase 5 — Desktop apps (Tauri)

| ID | Task | Deliverable |
|----|------|-------------|
| 5.1 | Init Tauri 2 in repo root or `desktop/` | `src-tauri/` |
| 5.2 | Point Tauri webview at built `admin/` static output | `tauri.conf.json` |
| 5.3 | Embed or sidecar FastAPI for local wallet API | sidecar script |
| 5.4 | Windows build script | `scripts/build-windows.ps1` |
| 5.5 | Mac build script | `scripts/build-mac.sh` |
| 5.6 | Copy artifacts to `releases/` + update `releases.json` | |
| 5.7 | App icon + window title "CoinWallet" | |
| 5.8 | Update download page links to real artifacts when built | |

---

## 10. Phase 6 — Mobile apps (Capacitor)

| ID | Task | Deliverable |
|----|------|-------------|
| 6.1 | Init Capacitor in `admin/` | `capacitor.config.ts` |
| 6.2 | iOS project scaffold | `ios/` |
| 6.3 | Android project scaffold | `android/` |
| 6.4 | Mobile bottom nav layout (replace sidebar on small screens) | layout component |
| 6.5 | Touch-friendly send/receive flows | |
| 6.6 | Secure storage for encryption keys (Keychain / Keystore) | native plugin |
| 6.7 | QR scanner on Receive (camera permission) | |
| 6.8 | Update download page with store links / APK path | |

---

## 11. Phase 7 — Wasabi-style privacy

| ID | Task | Deliverable |
|----|------|-------------|
| 7.1 | UTXO freeze/unfreeze API + UI actions | |
| 7.2 | UTXO label edit (partially started) — finish | |
| 7.3 | Privacy score calculation from UTXO graph | `src/wallet/privacy.py` |
| 7.4 | Privacy page — score + recommendations | `admin/.../privacy/+page.svelte` |
| 7.5 | Feed privacy context to Advisor AI templates | |

---

## 12. Phase 8 — Advisor AI tab

| ID | Task | Deliverable |
|----|------|-------------|
| 8.1 | Create `admin/src/lib/advisor/` — rule engine + templates | |
| 8.2 | `/advisor` route + sidebar entry | |
| 8.3 | Balance & recent tx explainer (template strings) | |
| 8.4 | Fee suggestion from send preview data | |
| 8.5 | Privacy tips from UTXO state | |
| 8.6 | Security checklist (backup, passphrase, network) | |
| 8.7 | Static Bitcoin FAQ content | |
| 8.8 | **Verify:** no trading/signals/exchange code anywhere | |

---

## 13. Phase 9 — Polish & stores

| ID | Task | Deliverable |
|----|------|-------------|
| 9.1 | App icons all platforms (1024 master) | |
| 9.2 | Splash screens mobile | |
| 9.3 | Mainnet gate audit (mobile + desktop) | |
| 9.4 | Backup flow audit — mnemonic shown once | |
| 9.5 | Deploy download site to Cloudflare Pages | |
| 9.6 | App Store / Play Store listing copy | |
| 9.7 | Optional: WebSocket live sync | |
| 9.8 | Optional: Bitcoin Core RPC backend | |

---

## 14. API spec reference (leaderboard)

```
GET  /api/leaderboard?network=testnet&limit=100
→ { entries: [{ rank, display_name, balance_sats, updated_at }], network }

POST /api/leaderboard/opt-in          (auth)
→ { display_name: string, opted_in: boolean }

POST /api/leaderboard/update          (auth)
→ { balance_sats: number, network: "testnet"|"mainnet" }

DELETE /api/leaderboard/opt-out       (auth)
→ removes user's entry
```

---

## 15. UI nav (final app sidebar)

Order in `app-sidebar.svelte`:

1. Dashboard `/`
2. Wallets `/wallets`
3. Receive `/receive`
4. Send `/send`
5. Coin Control `/utxos`
6. Transactions `/transactions`
7. Privacy `/privacy`
8. Advisor AI `/advisor`
9. Leaderboard `/leaderboard`
10. Settings `/settings`
11. Admin `/admin` (admin role only)

---

## 16. Site nav (download website)

1. Home `/`
2. Download `/download`
3. Leaderboard `/leaderboard`
4. Privacy `/privacy`
5. Terms `/terms`

---

## 17. Cost & privacy defaults

- Esplora (Blockstream) — free chain data
- No cloud LLM at launch
- Leaderboard: display name + balance only, opt-in
- Testnet default until user enables mainnet
- Non-custodial — keys never leave device unencrypted

---

## 18. Current pointer

**Next task:** read `.cursor/LOOP_STATE.json` → field `current_task_id`

When Phase 3 starts: **3.1** — scaffold `site/` SvelteKit project.

---

## 19. Quick decision tree

```
User message vague or loop tick?
  → Read this file + LOOP_STATE.json
  → Do current_task_id
  → Update state + PROGRESS.md

User gives specific task?
  → Still read this file for context
  → Do user's task (may override loop pointer temporarily)
  → Update LOOP_STATE.json if task matches a numbered item

User says stop loop?
  → Kill loop shell PID, do not arm next tick
```

---

*Last plan revision: 2026-06-27 — includes download site, leaderboard, 15-min loop, cross-platform apps, Advisor AI (no trading).*
