# CoinWallet — Master Plan (AI must read this first)

> **This file is the single source of truth** — product plan, task list, loop state, and progress log. Every agent session and every 15-minute loop tick starts here.

## Loop status

| Field | Value |
|-------|-------|
| **Current phase** | 13 — Local-first (Wasabi-style) ✓ |
| **Next task** | **14.3** — OS/browser detection unit tests |
| **Last completed** | 14.2 iPad desktop-mode UA handling |
| **Loop mode** | Chain (5-minute ticks) |
| **Last loop tick** | 2026-06-27T16:06 |

### Loop log

| Timestamp | Task | Result |
|-----------|------|--------|
| — | Loop initialized | Phases 1–2 done in web prototype; starting Phase 3 at 3.1 |
| 2026-06-27 | 3.1 | Scaffolded `site/` SvelteKit + Tailwind; dark/green theme; `npm install` + build OK |
| 2026-06-27 | 3.2 | Home page: hero, 6 feature cards, dual CTAs to /download; build OK |
| 2026-06-27 | 3.3 | Download page: 4 platform cards with coming-soon badges and install notes |
| 2026-06-27 | 3.4 | OS auto-detect on /download; highlights user's platform card |
| 2026-06-27 | 3.5–3.11 | Chain: releases.json wired, privacy/terms, nav, leaderboard shell, static adapter, README — **Phase 3 complete** |
| 2026-06-27 | 4.1–4.11 | Chain: leaderboard DB, API, settings opt-in, sync hook, app + site UI — **Phase 4 complete** |
| 2026-06-27 | 5.1–5.8 | Chain: Tauri 2 init, static admin build, API sidecar, build scripts, releases manifest — **Phase 5 complete** |
| 2026-06-27 | 7.1–7.5 | Chain: freeze/unfreeze + labels, `privacy.py`, recommendations UI, advisor privacy templates — **Phase 7 complete** |
| 2026-06-27 | 8.1–8.8 | Chain: advisor engine, `/advisor` route, balance/fee/security/FAQ templates, verify script — **Phase 8 complete** |
| 2026-06-27 | 9.1 | CoinWallet icon master (1024), Tauri/site/admin icons, `generate_icons.py` |
| 2026-06-27 | 9.3–9.4 | Mainnet gates (v2 + user/admin ack), backup dialog hardening, verify scripts |
| 2026-06-27 | 9.5 | Cloudflare Pages: wrangler.toml, deploy workflow, sync script, _headers |
| 2026-06-27 | 9.6 | `/install` guides for Windows + macOS — **Phase 9 complete** |
| 2026-06-27 | 10.1 | Wallet `asset_type` + XMR columns migration, API filter |
| 2026-06-27 | 10.2 | XMR 25-word keys, encrypted view key, `WalletService` create/import |
| 2026-06-27 | 10.3 | monero-wallet-rpc client, XmrSyncEngine, WalletService routing |
| 2026-06-27 | 10.4 | XmrOpsEngine receive/subaddress + send; wallet API asset_type create/import |
| 2026-06-27 | 10.5 | Wallets UI asset filter/create/import; dashboard asset badges + split balances |
| 2026-06-27 | 10.6 | Unified Receive/Send pages with BTC vs XMR asset-aware UI |
| 2026-06-27 | 10.7–10.10 | Swap providers, quote/execute API, `/swap` UI + history |
| 2026-06-27 | 10.11–10.14 | Explorer links, advisor swap tips, XMR stagenet settings, verify script |
| 2026-06-27 | 11.1–11.4 | Release signing hooks, manifest fingerprints, install verify steps, CI hash check |
| 2026-06-27 | 11.11 | Block send/swap when legacy v1 wallets remain; Security UI gate |
| 2026-06-27 | 11.5–11.32 | Security hardening chain: CORS, headers, CSRF, sessions, rate limits, idle lock, swap audits, advisor checklist, release gate |
| 2026-06-27 | 11.15 | wallet.db.cwenc AES-GCM at-rest sealing via WALLET_DB_KEY |
| 2026-06-27 | 11.32 | CI + build-windows run verify_release_security.py |
| 2026-06-27 | Phase 11 ✓ | Desktop security hardening complete (11.22–11.24 deferred — mobile out of scope) |
| 2026-06-27 | 12.1–12.4 | Mac build gate, README release docs, production env template, install guides |
| 2026-06-27 | 12.6 | finalize-release, sync-site-releases artifacts, operator checklist, release-desktop.yml |
| 2026-06-27 | 12.5 (partial) | Tauri nav plugin fix; Windows 0.1.0 built (unsigned), manifest + site static synced |
| 2026-06-27 | 12.7 | deploy-site.ps1/.sh; release-desktop deploy-site job; site build verified with .exe |
| 2026-06-27 | Loop | 5-minute master plan loop armed; next: **12.5** rebuild installer |
| 2026-06-27 | 12.5 ✓ | Bundled sidecar NSIS 0.1.0 built; site redeployed; installer hosted locally only (33.8 MiB > CF limit) |
| 2026-06-27 | 12.8 ✓ | GitHub Releases URL in manifest; publish script + CI; site redeployed |
| 2026-06-27 | 14.1 ✓ | detectOS: windows nt / mac os / mobile-first; no darwin false positive |
| 2026-06-27 | 14.2 ✓ | iPad desktop UA via MacIntel + maxTouchPoints; mobile hint, no mac highlight |

---

## 1. Loop protocol (15 minutes)

### On every loop tick OR when user says "continue" / "loop" / no specific task

1. Read this file completely.
2. Find the **lowest-numbered incomplete task** (check ✓ in phase tables below; e.g. `3.1` before `3.2`).
3. Implement **exactly ONE task** end-to-end in this tick.
4. Update this file:
   - Mark the task ✓ in its phase table.
   - Update **Loop status** (next task, last completed, last loop tick timestamp).
   - Append one row to **Loop log**.
   - When all tasks in a phase are done, mark the phase header ✓.
5. If blocked, add a note under **Loop status** and pick the next unblocked task in the same phase; do not skip phases.

### Loop constraints

- **One task per tick** — no bundling unless the task is trivial (<5 lines).
- **No commits** unless the user explicitly asks.
- **No tests** unless the user asks (they test manually).
- **Minimize cost** — free Esplora, no paid LLM APIs, no cloud hosting until deploy tasks.
- **Minimize scope** — match existing code style; no unrelated refactors.
- **Safety** — testnet default; never log or return mnemonics or passphrases; never expose `encrypted_seed` in GET; reject weak secrets in production builds (`STRICT_SECRETS=true`).

### Loop interval

Background timer fires every **5 minutes** (`300s`) with sentinel `AGENT_LOOP_TICK_COINWALLET`.

---

## 2. Product vision

**CoinWallet** — cross-platform non-custodial wallet, **Bitcoin-first** with optional **Monero (XMR)** support:

| Platform | Technology | Distribution |
|----------|------------|--------------|
| Windows | Tauri 2 | `.exe` from download site (no Microsoft Store) |
| Mac | Tauri 2 | `.dmg` from download site (no Mac App Store) |

**Platforms:** desktop only — **Windows and macOS**. Mobile (iOS/Android) is out of scope.

**Distribution policy:** direct downloads only — no App Store, Play Store, or other store listings. Saves store fees and review overhead; users install from the public website.

**Assets (phased):**
| Asset | Phase | Notes |
|-------|-------|-------|
| **BTC** | 1–2 ✓ | BIP84 native segwit, Esplora sync |
| **XMR** | 10 | Separate Monero wallet; stagenet/testnet first |
| **BTC ↔ XMR swap** | 10 | User-initiated only — quote, review, confirm (privacy exit) |

**Public download website** — home, downloads (all platforms), leaderboard, privacy/terms.

**In-app tabs:** Dashboard · Wallets · Receive · Send · **Swap** · Coin Control · Transactions · Privacy · Advisor AI · Leaderboard · Settings

**Out of scope forever:** trading AI, buy/sell signals, automated market trading, portfolio rebalancing bots.

**Optional cloud (Phase 13):** public leaderboard + cloud AI hints — display name and balance band only; keys and seeds never leave the device. Rule-based advisor works fully offline.

---

## 3. Architecture

```
site/                    ← Download website (SvelteKit static) — leaderboard reads remote URL
admin/                   ← Wallet app UI (SvelteKit 5 + shadcn-svelte) — shared on all platforms
api/                     ← FastAPI local sidecar (auth, wallet, swap) — 127.0.0.1 only
api/cloud_app.py         ← Optional cloud deploy — leaderboard + future AI only
src/wallet/              ← BIP84 BTC engine + Monero engine (Phase 10)
src/wallet/xmr/          ← XMR keys, sync, send (Phase 10)
src/database.py          ← SQLite schema (local wallet.db + global_leaderboard_entries on cloud)
releases/                ← Build artifacts + releases.json manifest (gitignored binaries)
.cursor/
  COINWALLET_MASTER_PLAN.md   ← THIS FILE (plan + loop state + log)
```

**Wasabi-style local-first (Phase 13):**

| Layer | Runs where | Needs internet |
|-------|------------|----------------|
| Keys, signing, wallet.db | This device | No |
| FastAPI sidecar | `127.0.0.1` | No |
| Rule-based Advisor | In-app | No |
| Blockchain sync (Esplora / XMR RPC) | Outbound to chain APIs | Yes (like any Bitcoin wallet) |
| Swap quotes | Outbound to allowlisted providers | Yes (user-initiated only) |
| Public leaderboard | `api/cloud_app.py` | Yes (opt-in display name + balance) |
| Cloud AI hints (optional) | Future `VITE_ADVISOR_AI_URL` | Yes (non-sensitive summary only) |

**Multi-asset model (Phase 10):** `wallets.asset_type` = `btc` | `xmr`. Each asset has its own encrypted seed, sync backend, and receive/send flows. Dashboard aggregates balances by asset.

**Data flow — leaderboard (opt-in only):**
App syncs wallet locally → if opt-in → local sidecar pushes `{ display_name, balance_sats, network }` to cloud via device token → `GET /api/leaderboard` on cloud → app tab + site page. No wallet keys on cloud.

**Advisor AI:** on-device rule engine in `admin/src/lib/advisor/` — works offline. Optional `VITE_ADVISOR_AI_URL` adds cloud hints from a non-sensitive summary only.

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

## 7. Phase 3 — Download website ✓

**Goal:** Public `site/` SvelteKit project — marketing + downloads for all platforms.

| ID | Task | Deliverable | Status |
|----|------|-------------|--------|
| 3.1 | Scaffold `site/` SvelteKit project (Tailwind, match admin aesthetic) | `site/package.json`, `site/src/routes/+page.svelte` | ✓ |
| 3.2 | Home page — hero, features, CTA to /download | `site/src/routes/+page.svelte` | ✓ |
| 3.3 | Download page — 4 platform cards (Windows, Mac, iPhone, Android) | `site/src/routes/download/+page.svelte` | ✓ |
| 3.4 | OS auto-detect — highlight current platform on /download | `site/src/lib/detect-os.ts` | ✓ |
| 3.5 | `releases.json` manifest — version, URLs, SHA-256, signature + signer fingerprint per platform (feeds Phase 11.1–11.2) | `releases/releases.json` | ✓ |
| 3.6 | Privacy page — non-custodial, leaderboard opt-in, swap provider disclosure, sideload trust model | `site/src/routes/privacy/+page.svelte` | ✓ |
| 3.7 | Terms page (minimal) | `site/src/routes/terms/+page.svelte` | ✓ |
| 3.8 | Shared nav header/footer across site pages | `site/src/lib/components/SiteHeader.svelte`, `SiteFooter.svelte` | ✓ |
| 3.9 | Leaderboard page shell (static layout; API wired in Phase 4) | `site/src/routes/leaderboard/+page.svelte` | ✓ |
| 3.10 | Static adapter config for Cloudflare Pages / GitHub Pages | `site/svelte.config.js` adapter-static | ✓ |
| 3.11 | README section — how to build and deploy site | `site/README.md` | ✓ |

**Download page buttons (until real builds exist):**
- Windows → `releases/coinwallet-windows-x64-setup.exe` (NSIS installer from `cargo tauri build`)
- Mac → `releases/coinwallet-macos.dmg` (+ Gatekeeper / “Open anyway” note)

Each file lists version, SHA-256, code signature metadata, and short install steps — no store badges or store URLs.

**`releases.json` schema (task 3.5):**
```json
{
  "version": "0.0.0",
  "released_at": "ISO-8601",
  "min_supported_version": "0.0.0",
  "signer_fingerprint": "hex or cert thumbprint",
  "platforms": {
    "windows": { "url": "...", "sha256": "...", "signature": "...", "signer_fingerprint": "...", "available": false },
    "macos": { "..." }
  }
}
```

---

## 8. Phase 4 — Leaderboard ✓

**Goal:** Opt-in public ranking by total wallet balance — app tab + site page + API.

| ID | Task | Deliverable | Status |
|----|------|-------------|--------|
| 4.1 | DB table `leaderboard_entries` (user_id, display_name, balance_sats, network, updated_at, opted_in) | `src/database.py` migration | ✓ |
| 4.2 | `GET /api/leaderboard?network=testnet&limit=100` — public, no auth; rate limit + short TTL cache (see 11.17) | `api/leaderboard.py` | ✓ |
| 4.3 | `POST /api/leaderboard/opt-in` — body: `{ display_name, opted_in }` | `api/leaderboard.py` | ✓ |
| 4.4 | `POST /api/leaderboard/update` — auth required; body: `{ balance_sats, network }` | `api/leaderboard.py` | ✓ |
| 4.5 | Register leaderboard router in `api/main.py` | | ✓ |
| 4.6 | Settings UI — leaderboard opt-in toggle + display name field | `admin/src/routes/(app)/settings/+page.svelte` | ✓ |
| 4.7 | Push balance on wallet sync when opted in | hook in sync flow / `api/wallet.py` | ✓ |
| 4.8 | App `/leaderboard` route — top N + user's rank | `admin/src/routes/(app)/leaderboard/+page.svelte` | ✓ |
| 4.9 | Sidebar nav entry for Leaderboard | `app-sidebar.svelte` | ✓ |
| 4.10 | Wire `site/leaderboard` page to public API | fetch from API URL env | ✓ |
| 4.11 | Separate testnet / mainnet tabs on leaderboard UI | both app and site | ✓ |

**Privacy rules:**
- Never send addresses, mnemonics, UTXOs, or tx history to leaderboard API.
- Opt-out removes entry immediately.
- Default: opted out.

---

## 9. Phase 5 — Desktop apps (Tauri) ✓

| ID | Task | Deliverable | Status |
|----|------|-------------|--------|
| 5.1 | Init Tauri 2 in repo root or `desktop/` | `src-tauri/` | ✓ |
| 5.2 | Point Tauri webview at built `admin/` static output | `tauri.conf.json` | ✓ |
| 5.3 | Embed or sidecar FastAPI for local wallet API — bind `127.0.0.1` only, `STRICT_SECRETS=true` (see 11.10, 11.20) | `src-tauri/src/lib.rs`, `scripts/start-desktop-api.*` | ✓ |
| 5.4 | Windows build script | `scripts/build-windows.ps1` | ✓ |
| 5.5 | Mac build script | `scripts/build-mac.sh` | ✓ |
| 5.6 | Copy artifacts to `releases/` + update `releases.json` | `scripts/update-releases-manifest.ps1` | ✓ |
| 5.7 | App icon + window title "CoinWallet" | `src-tauri/tauri.conf.json`, `icons/` | ✓ |
| 5.8 | Update download page links to real artifacts when built | driven by `releases.json` `available` flag | ✓ |

---

## 10. Phase 6 — Mobile apps ~~(Capacitor)~~ **OUT OF SCOPE**

> Desktop only: Windows + macOS. Mobile (iOS/Android) removed from product scope.

<!-- Retained for historical reference only:

| ID | Task | Deliverable |
|----|------|-------------|
| 6.1 | Init Capacitor in `admin/` | `capacitor.config.ts` |
| 6.2 | iOS project scaffold | `ios/` |
| 6.3 | Android project scaffold | `android/` |
| 6.4 | Mobile bottom nav layout (replace sidebar on small screens) | layout component |
| 6.5 | Touch-friendly send/receive flows | |
| 6.6 | Secure storage for encryption keys — iOS Keychain `WHEN_UNLOCKED_THIS_DEVICE_ONLY`; Android Keystore non-exportable | native plugin |
| 6.7 | QR scanner on Receive (camera permission) | |
| 6.8 | Update download page with APK / IPA paths + sideload install guides | |

-->

---

## 11. Phase 7 — Wasabi-style privacy ✓

| ID | Task | Deliverable |
|----|------|-------------|
| 7.1 ✓ | UTXO freeze/unfreeze API + UI actions | `api/wallet.py`, `admin/.../utxos` |
| 7.2 ✓ | UTXO label edit (partially started) — finish | Coin Control labels + tx labels |
| 7.3 ✓ | Privacy score calculation from UTXO graph | `src/wallet/privacy.py` |
| 7.4 ✓ | Privacy page — score + recommendations | `admin/.../privacy/+page.svelte` |
| 7.5 ✓ | Feed privacy context to Advisor AI templates | `admin/src/lib/advisor/privacy.ts` |

---

## 12. Phase 8 — Advisor AI tab ✓

| ID | Task | Deliverable |
|----|------|-------------|
| 8.1 ✓ | Create `admin/src/lib/advisor/` — rule engine + templates | `engine.ts`, `balance.ts`, `fees.ts`, `security.ts`, `faq.ts` |
| 8.2 ✓ | `/advisor` route + sidebar entry | `admin/.../advisor/+page.svelte`, sidebar |
| 8.3 ✓ | Balance & recent tx explainer (template strings) | `advisor/balance.ts` |
| 8.4 ✓ | Fee suggestion from send preview data | `advisor/fees.ts`, Send preview tips |
| 8.5 ✓ | Privacy tips from UTXO state | `advisor/privacy.ts` |
| 8.6 ✓ | Security checklist (backup, passphrase, network) | `advisor/security.ts` |
| 8.7 ✓ | Static Bitcoin FAQ content | `advisor/faq.ts` |
| 8.8 ✓ | **Verify:** no automated trading bot, signals, or background swap jobs | `scripts/verify_no_trading_features.py` |

---

## 13. Phase 9 — Polish & web release ✓

| ID | Task | Deliverable |
|----|------|-------------|
| 9.1 ✓ | App icons all platforms (1024 master) | `assets/branding/`, `scripts/generate_icons.py`, `src-tauri/icons/` |
| 9.2 — | Splash screens mobile | **Out of scope** (desktop-only) |
| 9.3 ✓ | Mainnet gate audit (desktop) — v2 passphrase + acknowledgment | `mainnet_gate.py`, Security/Settings UI, verify script |
| 9.4 ✓ | Backup flow audit — mnemonic shown once | Wallets dialog + `verify_backup_flow.py` |
| 9.5 ✓ | Deploy download site to Cloudflare Pages (free tier) | `deploy-site.yml`, `wrangler.toml`, deploy scripts |
| 9.6 ✓ | Per-platform install docs on site (Windows, Mac) | `/install`, `install-guides.ts` |
| 9.7 — | Optional: WebSocket live sync | skipped |
| 9.8 — | Optional: Bitcoin Core RPC backend | skipped |

**Phase 9 complete** (required tasks; optional 9.7–9.8 deferred).

---

## 14. Phase 10 — Multi-asset & BTC↔XMR swap

**Goal:** Hold Monero (XMR) in the same app as Bitcoin; let the user manually swap BTC→XMR (or back) for privacy — **not** a trading bot.

**Swap UX (same trust model as Send):**
1. User picks direction (BTC→XMR or XMR→BTC), amount, destination wallet
2. App fetches quote (rate, network fee, swap provider fee, min/max)
3. User reviews and confirms (wallet unlock required)
4. App executes or returns deposit instructions; status tracked until settled

**Provider strategy (pick one per task 10.8; prefer non-custodial):**
- **Preferred:** Atomic swap / Haveno-style P2P (self-hosted or public Haveno node)
- **Fallback:** User-selected swap API with full disclosure (SideShift, FixedFloat, etc.) — clearly label custodial risk
- **Never:** Embedded exchange account, API keys stored server-side, or auto-rebalancing

| ID | Task | Deliverable | Status |
|----|------|-------------|--------|
| 10.1 ✓ | DB migration — `wallets.asset_type` (`btc`\|`xmr`), XMR-specific columns | `src/database.py` |
| 10.2 ✓ | XMR key generation + encrypted seed storage (25-word Monero mnemonic) | `src/wallet/xmr/keys.py` |
| 10.3 ✓ | XMR sync backend — wallet-rpc sidecar | `src/wallet/xmr/sync.py`, `rpc.py` |
| 10.4 ✓ | XMR receive (primary + subaddress) + send | `src/wallet/xmr/ops.py`, `session.py`, `api/wallet.py` |
| 10.5 ✓ | Wallets UI — filter/create by asset; asset badge on dashboard | `admin/.../wallets`, dashboard |
| 10.6 ✓ | XMR receive/send pages (unified Receive/Send with asset picker) | `admin/src/routes/(app)/receive`, `send` |
| 10.7 ✓ | `GET /api/swap/quote` — rate + fees | `api/swap.py`, `src/wallet/swap/` |
| 10.8 ✓ | Swap provider adapter + rate_table + Haveno stub | `src/wallet/swap/providers/` |
| 10.9 ✓ | `POST /api/swap/execute` — swap record + deposit steps | `api/swap.py`, `swaps` table |
| 10.10 ✓ | `/swap` route — quote form, review, history | `admin/.../swap/+page.svelte` |
| 10.11 ✓ | Swap history table + explorer links per asset | `swaps` txid columns, `/swap` UI |
| 10.12 ✓ | Advisor AI — swap privacy tips | `admin/src/lib/advisor/swap.ts` |
| 10.13 ✓ | Stagenet/testnet defaults for XMR; mainnet gate on swap | settings, `SwapService` |
| 10.14 ✓ | **Verify:** no automated trading/signals/background swap | `scripts/verify_no_trading_features.py` |

**Privacy rules:**
- Swap is opt-in per transaction — never auto-convert received BTC
- Show full quote breakdown before confirm
- Log swap events in audit (amounts + provider; no mnemonics or private keys)
- XMR view keys / spend keys never exposed in GET or logs

---

## 15. API spec reference (leaderboard)

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

### Swap (Phase 10)

```
GET  /api/swap/providers
→ { providers: [{ id, name, type: "atomic"|"api", custodial: bool }] }

GET  /api/swap/quote?from=btc&to=xmr&amount_sats=100000&provider=haveno
→ { rate, receive_amount_atomic, fees: { network, provider }, min, max, expires_at }

POST /api/swap/execute                (auth, wallet unlocked)
→ { from_asset, to_asset, amount, provider, destination_wallet_id }
← { swap_id, status: "awaiting_deposit"|"processing", deposit_address?, deposit_amount? }

GET  /api/swap/{swap_id}              (auth)
→ { status, from_amount, to_amount, txids, created_at, settled_at }
```

---

## 16. UI nav (final app sidebar)

Order in `app-sidebar.svelte`:

1. Dashboard `/`
2. Wallets `/wallets`
3. Receive `/receive`
4. Send `/send`
5. Swap `/swap` *(Phase 10 — BTC↔XMR)*
6. Coin Control `/utxos`
7. Transactions `/transactions`
8. Privacy `/privacy`
9. Advisor AI `/advisor`
10. Leaderboard `/leaderboard`
11. Settings `/settings`
12. Admin `/admin` (admin role only)

---

## 17. Site nav (download website)

1. Home `/`
2. Download `/download`
3. Leaderboard `/leaderboard`
4. Privacy `/privacy`
5. Terms `/terms`

---

## 18. Cost & privacy defaults

- Esplora (Blockstream) — free chain data
- **No app stores** — distribute via download site only (no Apple/Google/Microsoft store fees or listings)
- Static site on Cloudflare Pages / GitHub Pages — free tier
- No cloud LLM at launch
- Leaderboard: display name + balance only, opt-in
- Testnet/stagenet default until user enables mainnet
- Non-custodial — keys never leave device unencrypted
- XMR swap: user confirms every conversion; no background trading

---

## 19. Current pointer

**Next task:** **12.5** — First signed release (operator: run checklist, build, sign, `finalize-release`, deploy site).

Update **Loop status** at the top of this file after every tick.

---

## 20. Quick decision tree

```
User message vague or loop tick?
  → Read this file
  → Do next incomplete task (Loop status → phase tables)
  → Update Loop status + Loop log + task ✓ in this file

User gives specific task?
  → Still read this file for context
  → Do user's task (may override loop pointer temporarily)
  → Mark matching task ✓ if applicable

User says stop loop?
  → Kill loop shell PID, do not arm next tick
```

---

## 21. Phase 11 — Security hardening ✓

**Goal:** Close supply-chain, API, key-lifecycle, and public-surface gaps before mainnet and real-money swap. Builds on existing bcrypt sessions, AES-GCM seeds, rate limiting, and passphrase unlock (v2 DEK).

**Priority (highest ROI before real money):** 11.1 → 11.11 → 11.20 → 11.12–11.13 → 11.25–11.26, then remainder.

### 11.1 Supply chain & release integrity

| ID | Task | Deliverable |
|----|------|-------------|
| 11.1 ✓ | Sign release artifacts (optional Authenticode / codesign hooks) | `scripts/sign-release-*`, `build-*.ps1` |
| 11.2 ✓ | Publish signing fingerprints on site + manifest | `releases.json`, download page |
| 11.3 ✓ | Document verify steps per platform | `install-guides.ts` |
| 11.4 ✓ | CI artifact hash verification | `verify-release-manifest.py`, CI |

### 11.2 API & session hardening

| ID | Task | Deliverable |
|----|------|-------------|
| 11.5 ✓ | Production CORS allowlist via env (`CORS_ORIGINS`); deny `*` with credentials | `api/main.py` |
| 11.6 ✓ | Security headers middleware (CSP, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy`) | `api/middleware.py` |
| 11.7 ✓ | CSRF protection for cookie-authenticated mutating routes OR document SameSite-only model for native shells | `api/auth.py` + admin fetch wrapper |
| 11.8 ✓ | Extend rate limits: login, unlock, send, swap execute; optional Redis/file backend for multi-process | `api/rate_limit.py` |
| 11.9 ✓ | Session rotation on login + idle timeout (separate from 7-day max age) | `api/auth.py` |
| 11.10 ✓ | `STRICT_SECRETS=true` required in production builds (Tauri/Capacitor sidecar env) | Phase 5.3 sidecar config |

### 11.3 Wallet & key lifecycle

| ID | Task | Deliverable |
|----|------|-------------|
| 11.11 ✓ | Force v2 migration before send/swap; block if legacy wallets remain | `mainnet_gate.py`, Send UI |
| 11.12 ✓ | Auto-lock wallet after idle timeout (configurable in Settings) | `src/wallet/vault.py` + Settings UI |
| 11.13 ✓ | Clear in-memory DEK on lock, app background, and logout | vault + Tauri/Capacitor lifecycle hooks |
| 11.14 ✓ | Mnemonic display: single-use modal, no clipboard auto-copy, explicit "I wrote it down" | Phase 9.4 backup audit |
| 11.15 ✓ | SQLite encryption at rest (SQLCipher or OS-level file encryption on desktop/mobile) | `src/db_at_rest.py`, `WALLET_DB_KEY` |

### 11.4 Leaderboard & public surface

| ID | Task | Deliverable |
|----|------|-------------|
| 11.16 ✓ | Display name validation (length, charset, block impersonation of "admin"/"CoinWallet") | `api/leaderboard.py` |
| 11.17 ✓ | Rate limit public GET; cache responses (CDN or short TTL) | leaderboard router |
| 11.18 ✓ | Balance update: reject impossible jumps, cap update frequency per user | `POST /api/leaderboard/update` |
| 11.19 ✓ | Privacy page documents exactly what is sent — leaderboard data flow diagram | `site/.../privacy/` |

### 11.5 Desktop & mobile shell

| ID | Task | Deliverable |
|----|------|-------------|
| 11.20 ✓ | Bind FastAPI sidecar to `127.0.0.1` only; reject non-local Host headers | Tauri sidecar |
| 11.21 ✓ | Tauri allowlist: disable arbitrary IPC, file system, and remote URL loading except Esplora | `tauri.conf.json` |
| 11.22 — | Capacitor: certificate pinning for Esplora (optional toggle) + no cleartext HTTP | **out of scope** (desktop only) |
| 11.23 — | Android backup disabled; iOS Data Protection for Keychain items | **out of scope** |
| 11.24 — | Screenshot/recents blur on mnemonic and unlock screens (mobile) | **out of scope** |

### 11.6 Swap & XMR

| ID | Task | Deliverable |
|----|------|-------------|
| 11.25 ✓ | Provider allowlist in config; no arbitrary URL from client | `src/wallet/swap/` |
| 11.26 ✓ | Quote expiry enforced server-side; reject stale execute | `api/swap.py` |
| 11.27 ✓ | Swap deposit addresses shown once with checksum verification | swap UI |
| 11.28 ✓ | XMR view/spend keys never in API responses — automated grep/audit in Phase 10.14 verify | audit script |

### 11.7 Operational security & audit

| ID | Task | Deliverable |
|----|------|-------------|
| 11.29 ✓ | Expand audit log: login failures, unlock failures, mainnet enable, swap execute (no secrets) | `src/database.py` |
| 11.30 ✓ | Structured security checklist in Advisor AI tab (Phase 8.6) wired to real wallet state | `admin/src/lib/advisor/` |
| 11.31 ✓ | `.env.example` with all security env vars documented | repo root |
| 11.32 ✓ | Pre-release security review gate: run through checklist before mainnet / real releases | `scripts/verify_release_security.py` |

**Out of scope for Phase 11 (defer post-launch):** bug bounty, paid pentest, HSM, cloud WAF, Rust BDK migration for security alone.

---

*Last plan revision: 2026-06-27 — Phase 11 complete; Phase 12 release readiness started.*

---

## 22. Phase 12 — Release readiness

**Goal:** Ship signed desktop builds with documented production env, build-script parity, and operator docs.

| ID | Task | Deliverable |
|----|------|-------------|
| 12.1 ✓ | Mac build runs pre-release security gate (parity with Windows) | `scripts/build-mac.sh` |
| 12.2 ✓ | README production release section + corrected ports/phase status | `README.md` |
| 12.3 ✓ | Production desktop env template | `.env.production.desktop.example` |
| 12.4 ✓ | Install guides mention production hardening (STRICT_SECRETS, WALLET_DB_KEY) | `install-guides.ts` |
| 12.5 ✓ | First release — build, deploy site with binaries, optional signing | operator |
| 12.6 ✓ | Finalize/sync scripts, operator checklist, GitHub Release desktop workflow | `finalize-release.*`, `sync-site-releases.mjs`, `release-desktop.yml` |
| 12.7 ✓ | Deploy scripts + CI deploy job (binaries not in git) | `deploy-site.ps1`, `release-desktop.yml` deploy-site job |
| 12.8 ✓ | Host oversized installer on GitHub Releases | `publish-github-release.ps1`, `release_urls.py`, CI `gh release upload` |

**Operator:** Run `gh auth login` then `.\scripts\publish-github-release.ps1 -Version 0.1.0` to upload the binary once.

**Deferred:** mobile Capacitor (Phase 6), Haveno live quotes, optional Core RPC (9.8).

---

## 23. Phase 13 — Local-first (Wasabi-style) ✓ (foundation)

**Goal:** Wallet core stays on-device; only leaderboard + optional cloud AI need CoinWallet servers.

| ID | Task | Deliverable | Status |
|----|------|-------------|--------|
| 13.1 | Document local vs remote split | Master plan architecture table | ✓ |
| 13.2 | Token-based remote leaderboard API | `api/remote_leaderboard.py`, `global_leaderboard_entries` | ✓ |
| 13.3 | Local sidecar syncs opt-in to remote URL | `COINWALLET_REMOTE_SERVICES_URL`, `api/remote_services.py` | ✓ |
| 13.4 | Minimal cloud deploy app | `api/cloud_app.py`, `scripts/run-cloud-services.ps1` | ✓ |
| 13.5 | Admin/site fetch leaderboard from remote URL | `VITE_REMOTE_SERVICES_URL`, `remote-services.ts` | ✓ |
| 13.6 | Optional cloud AI hook (offline fallback) | `admin/src/lib/advisor/remote-ai.ts` | ✓ |
| 13.7 | Bundle Python sidecar in NSIS installer | `build-api-sidecar.ps1`, PyInstaller, `externalBin` | ✓ |
| 13.8 | Host cloud services + wire production URLs | Pages Functions + D1 on coinwallet.pages.dev | ✓ |

---

## 24. Phase 14 — Code review remediation

**Goal:** Close bugs and security gaps from the 2026-06-27 code review — download OS detection, WebSocket auth, wallet delete policy, leaderboard network UX, and targeted tests.

**Priority:** 14.1 → 14.2 → 14.3 → 14.4, then remainder.

### 14.1 Download site — OS / browser detection

| ID | Task | Deliverable |
|----|------|-------------|
| 14.1 ✓ | Fix `detectOS()` false positives — use `windows nt` / `\bmac os\b` / `iphone|ipad`; check mobile before OS; avoid `/win/` matching `darwin` | `site/src/lib/detect-os.ts` |
| 14.2 ✓ | iPad desktop-mode UA — treat as mobile or unknown; do not highlight macOS card | `detect-os.ts` + `download/+page.svelte` |
| 14.3 | Unit tests for OS/browser detection against real UA samples (Windows, Mac Safari, iPhone, iPad desktop, Darwin WebView) | `site/src/lib/detect-os.test.ts` or `scripts/verify-detect-os.mjs` |

### 14.2 API auth & session

| ID | Task | Deliverable |
|----|------|-------------|
| 14.4 | WebSocket auth — move session token off query string (post-connect auth message or `Sec-WebSocket-Protocol`; cookie on localhost) | `api/events.py`, admin WS client |
| 14.5 | Reject empty/missing `Host` when `LOCALHOST_ONLY` / `STRICT_SECRETS` enabled | `api/middleware.py` |
| 14.6 | Document dual auth model (HttpOnly cookie + Bearer in `sessionStorage`); tighten admin CSP in production build | `README.md`, admin `vite.config` or headers |

### 14.3 Wallet & leaderboard behavior

| ID | Task | Deliverable |
|----|------|-------------|
| 14.7 | Require `require_wallet_unlocked` (or re-enter passphrase) for `DELETE /api/wallets/{id}` | `api/wallet.py` |
| 14.8 | Leaderboard opt-in — accept explicit `network` in request body; align Settings UI with testnet/mainnet boards | `api/leaderboard.py`, settings + leaderboard pages |
| 14.9 | Optional: do not `touch_unlock` on read-only GET routes (configurable `WALLET_TOUCH_ON_READ=false`) | `api/middleware.py`, Settings |

### 14.4 Test coverage

| ID | Task | Deliverable |
|----|------|-------------|
| 14.10 | pytest: `list_wallets` / `get_wallet` never return `encrypted_seed` | `tests/test_wallet_secrets.py` |
| 14.11 | pytest: leaderboard display-name validation + balance update rejection | `tests/test_leaderboard.py` |
| 14.12 | pytest: mainnet gate blocks send/swap without v2 + ack | `tests/test_mainnet_gate.py` |
| 14.13 | pytest: swap quote expiry rejected on stale execute | `tests/test_swap.py` |

**Out of scope:** full mobile Capacitor hardening (11.22–11.24), paid pentest, forcing removal of Bearer tokens (desktop SPA depends on them today).

---

## 25. Phase 15 — Download website visual upgrade

**Goal:** Make `site/` feel premium and product-ready — same neutral shadcn zinc + green money accent as admin, but with stronger layout, motion, and polish. No new paid assets or heavy animation libraries.

**Design direction:** Dark zinc base, subtle green glow accents, crisp typography, glass-style cards, clear hierarchy. Match admin brand; site can be more marketing-forward.

| ID | Task | Deliverable |
|----|------|-------------|
| 15.1 | Design tokens pass — typography scale, section spacing, shared `--glow-success`, card shadow utilities | `site/src/app.css` |
| 15.2 | Logo mark + wordmark component (icon + CoinWallet split color) | `site/src/lib/components/BrandLogo.svelte` |
| 15.3 | Header/footer upgrade — sticky blur nav, mobile hamburger menu, footer columns (Download, Legal, Links) | `SiteHeader.svelte`, `SiteFooter.svelte` |
| 15.4 | Home hero — mesh/grid background, optional product mockup or wallet screenshot frame, stronger CTA pair | `site/src/routes/+page.svelte` |
| 15.5 | Feature cards — Lucide-style inline SVG icons, hover lift + border glow | `+page.svelte` or `FeatureCard.svelte` |
| 15.6 | Download page — polished platform cards, version badge, checksum copy button, detected-env tip styling | `download/+page.svelte` |
| 15.7 | Leaderboard — rank medals for top 3, zebra rows, loading skeleton | `leaderboard/+page.svelte` |
| 15.8 | Privacy / terms / install — consistent prose layout, table of contents on install guide | `privacy/`, `terms/`, `install/` |
| 15.9 | Page transitions + reduced-motion respect (`prefers-reduced-motion`) | `+layout.svelte`, shared CSS |
| 15.10 | SEO & social — OG/Twitter meta, theme-color, favicon set from app icon | `site/src/app.html`, `+page.svelte` head |
| 15.11 | Lighthouse pass — fix contrast, tap targets, meta; document scores in `site/README.md` | manual audit + README note |

**Constraints:** static adapter only; no client-side wallet logic on site; keep bundle lean (CSS + Svelte transitions, no Framer/Lottie unless user approves).

*Last plan revision: 2026-06-27 — Phase 15 download website visual upgrade added.*
