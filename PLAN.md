# CoinWallet — Product Plan

Cross-platform Bitcoin wallet for **Windows**, **Mac**, **iPhone**, and **Samsung / Android**.  
Non-custodial, privacy-focused, with a single **Advisor AI** tab for guidance — no trading features.

---

## Vision

CoinWallet is a native app you install on your devices — not a browser-only web dashboard. One wallet experience everywhere: desktop at home, phone on the go. Keys stay on your device; chain sync uses free public APIs (Esplora) by default.

A public **download website** hosts installers for every platform and shows a live **leaderboard** of users with the most coins in their wallet (opt-in only).

**Out of scope:** automated trading, buy/sell signals, exchange integration, or any AI that executes trades.

---

## Platforms

| Platform | Shell | Store / distribution |
|----------|-------|----------------------|
| **Windows** | Tauri 2 | `.exe` / Microsoft Store (later) |
| **Mac** | Tauri 2 | `.dmg` / Mac App Store (later) |
| **iPhone** | Capacitor + iOS | App Store |
| **Samsung / Android** | Capacitor + Android | Google Play / sideload APK |

The existing SvelteKit UI (`admin/`) becomes the shared front-end. Tauri wraps it for desktop; Capacitor wraps it for mobile. Wallet logic stays in a local backend (FastAPI embedded in Tauri sidecar today; Rust/BDK migration optional later for smaller mobile binaries).

---

## Download Website

Public marketing site (e.g. `coinwallet.app`) — separate from the wallet app itself.

**Pages:**

| Page | Content |
|------|---------|
| **Home** | What CoinWallet is, feature highlights, link to downloads |
| **Download** | One page, all platforms — Windows `.exe`, Mac `.dmg`, iPhone App Store link, Android APK / Play Store link |
| **Leaderboard** | Public ranking of opt-in users by total wallet balance |
| **Privacy / Terms** | Non-custodial disclaimer, leaderboard opt-in policy |

**Download page layout:**

- Auto-detect OS and highlight the matching download button
- Manual pickers for Windows, Mac, iPhone, Samsung / Android
- Version number + release notes per build
- Checksums (SHA-256) for desktop/APK files

**Hosting:** static site + lightweight API for leaderboard (same FastAPI backend or a small dedicated service). Free-tier friendly — e.g. Cloudflare Pages for the site, single VPS or serverless for the API.

The download site does **not** hold keys or wallet data — only public leaderboard entries users choose to share.

---

## App Tabs / Navigation

| Tab | Purpose |
|-----|---------|
| **Dashboard** | Balance, sync status, quick actions |
| **Wallets** | Create, import, backup mnemonic |
| **Receive** | BIP84 address + QR |
| **Send** | Fee preview, broadcast |
| **Coin Control** | UTXO list, freeze, labels |
| **Transactions** | History |
| **Privacy** | Privacy score, coinjoin readiness (Wasabi-style) |
| **Advisor AI** | Educational guidance only (see below) |
| **Leaderboard** | Opt-in ranking vs other users; links to full board on download site |
| **Settings** | Passphrase, network, security, leaderboard opt-in |

Consumer apps default to **single-user, local-only** for keys. Only balance + display name are sent to the server when leaderboard opt-in is enabled.

---

## Advisor AI Tab (only AI feature)

One tab. No trading AI. No market predictions. No “buy now” prompts.

**What it does (on-device, rule-based — no paid LLM API):**

- Explains your balance, recent transactions, and fees in plain language
- Suggests fee tiers based on mempool / urgency (uses existing send preview data)
- Privacy tips tied to your UTXO set and labels (e.g. “consider labeling this UTXO”)
- Security checklist (backup reminder, passphrase strength, testnet vs mainnet warnings)
- FAQ-style answers about Bitcoin basics (static content + templated responses)

**What it does not do:**

- Execute trades or connect to exchanges
- Give price targets or “signals”
- Send wallet data to a cloud LLM (unless user explicitly opts into a future optional feature)

Implementation: templated + rule engine first; optional on-device small model later if needed. Zero server cost at launch.

---

## Leaderboard

Public ranking of who holds the most coins — visible in the app and on the download website.

**How it works:**

- **Opt-in only** — off by default; user toggles on in Settings
- User picks a **display name** (username); no wallet addresses or mnemonics are ever uploaded
- App reports **total confirmed balance** (sum across wallets on current network) after each sync
- Server stores: `display_name`, `balance_sats`, `network` (testnet/mainnet), `updated_at`
- Separate boards for testnet and mainnet so test coins do not mix with real funds

**Rankings shown:**

1. Rank (#1, #2, …)
2. Display name
3. Total balance (BTC / sats)
4. Last updated time

**In-app:** Leaderboard tab shows top N + the signed-in user's rank if opted in.

**Website:** Full public leaderboard page on the download site — same data, no login required to view.

**Privacy:** Users can opt out anytime; entry is removed on next sync or immediately via API. No transaction history or UTXO details on the board — balance total only.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Download website — marketing, downloads, leaderboard   │
│  (SvelteKit site/ or public routes — static + API)      │
└───────────────────────────┬─────────────────────────────┘
                            │ leaderboard API (opt-in balances)
┌───────────────────────────▼─────────────────────────────┐
│  Shared UI — SvelteKit 5 + shadcn-svelte (admin/)       │
├──────────────┬──────────────┬───────────────────────────┤
│ Tauri 2      │ Tauri 2      │ Capacitor                 │
│ Windows      │ macOS        │ iOS + Android             │
├──────────────┴──────────────┴───────────────────────────┤
│  Local wallet engine — keys, sync, PSBT (src/wallet/)   │
│  SQLite on device — encrypted seed, UTXOs, txs          │
├─────────────────────────────────────────────────────────┤
│  Chain data — Esplora (free) · Core RPC optional later  │
└─────────────────────────────────────────────────────────┘
```

---

## Development Phases

### Phase 1 — Foundation ✓
Auth, schema, UI shell, project structure.

### Phase 2 — Wallet core ✓
BIP84 wallets (testnet), Esplora sync, receive/send, UTXO and transaction views.

### Phase 3 — Download website
- Public site: home, **download page** (Windows / Mac / iPhone / Android), privacy/terms
- Host build artifacts (`.exe`, `.dmg`, APK) or link to App Store / Play Store
- OS auto-detect on download page
- Deploy to free static hosting (Cloudflare Pages, GitHub Pages, etc.)

### Phase 4 — Leaderboard
- API: `POST /api/leaderboard/opt-in`, `GET /api/leaderboard?network=testnet`
- DB table: display name, balance, network, user id, updated_at
- App tab + Settings toggle; sync pushes balance after wallet refresh
- Public leaderboard page on download website

### Phase 5 — Desktop apps (Windows + Mac)
- Package with **Tauri 2** (embed FastAPI sidecar or call wallet engine directly)
- Native window, system tray, auto-update hook (later)
- Remove “open localhost in browser” as the primary flow

### Phase 6 — Mobile apps (iPhone + Android)
- **Capacitor** shell around shared SvelteKit build
- Mobile-first layouts (bottom nav, touch targets)
- Secure storage (Keychain / Android Keystore) for encryption keys
- Camera permission for QR scan on Receive

### Phase 7 — Wasabi-style privacy
- Coin control actions (freeze, labels) — UI partially started
- Privacy score and recommendations (feeds Advisor AI context)

### Phase 8 — Advisor AI tab
- New `/advisor` route + sidebar entry
- Rule engine + templates wired to wallet state
- Static help content; no trading module

### Phase 9 — Polish & stores
- App icons, splash screens, store listings
- Mainnet gate + backup flows audited for mobile
- Optional: WebSocket live sync, Bitcoin Core RPC for power users

---

## Tech Stack (target)

| Layer | Choice |
|-------|--------|
| UI | SvelteKit 5, Tailwind 4, shadcn-svelte |
| Desktop | Tauri 2 (Rust shell) |
| Mobile | Capacitor (iOS + Android) |
| Wallet / API | Python FastAPI + embit (today); BDK Rust optional |
| Storage | SQLite, encrypted at rest |
| Chain | Esplora (Blockstream) — free tier |
| Advisor AI | On-device rules + templates — no cloud LLM at launch |
| Download site | SvelteKit static/marketing site + platform binaries |
| Leaderboard | FastAPI endpoint + SQLite; opt-in balance sync only |

---

## Cost & Privacy Defaults

- No paid APIs required for v1
- No LLM server; Advisor runs on-device
- Non-custodial — mnemonics never leave the device unencrypted
- Leaderboard shares **display name + balance only** — opt-in, revocable
- Testnet default until user explicitly enables mainnet

---

## Current Status

Web prototype (Phases 1–2) runs locally via `setup.sh` / `setup.bat`. Next step: **Phase 3 — Download website**, then **Phase 4 — Leaderboard**.

See **[.cursor/COINWALLET_MASTER_PLAN.md](./.cursor/COINWALLET_MASTER_PLAN.md)** for the full execution plan (task list, loop protocol, API specs). This file is a summary.
