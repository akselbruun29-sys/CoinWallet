# What you must do

Do these in order. Everything else (tests, builds, Tor download) is already done.

---

## Required

### 1 — Log into GitHub CLI (one-time)

```powershell
cd C:\Users\aksel\Documents\GitHub\trading-bot
& "$env:ProgramFiles\GitHub CLI\gh.exe" auth login
```

(`gh` may not be on PATH — use the full path above, or add `C:\Program Files\GitHub CLI` to PATH.)

Check it worked:

```powershell
& "$env:ProgramFiles\GitHub CLI\gh.exe" auth status
```

---

### 2 — Upload the Windows installer

Fixes the **404** on the download page.

```powershell
.\scripts\publish-github-release.ps1 -Version 0.1.0
```

Open this in a browser — it must download, not 404:

https://github.com/akselbruun29-sys/CoinWallet/releases/download/v0.1.0/coinwallet-windows-x64-setup.exe

**If you get 404:** the GitHub repo is probably **private**. Public download links only work when the repo is **public**:

```powershell
& "$env:ProgramFiles\GitHub CLI\gh.exe" repo edit akselbruun29-sys/CoinWallet --visibility public --accept-visibility-change-consequences
```

(`gh` requires the second flag to confirm you understand the repo becomes public.)

---

### 3 — Rebuild the installer with Tor inside

Tor is already downloaded into the repo. The current `.exe` was built **before** that — rebuild so users get Tor bundled.

```powershell
.\scripts\build-windows.ps1
.\scripts\publish-github-release.ps1 -Version 0.1.0
```

---

### 4 — Test the app in the browser (testnet)

```powershell
.\start_admin.ps1
```

Open http://localhost:5173

| Step | Where | What |
|------|-------|------|
| 4a | Login | Sign in as `admin` (password in your `.env`) |
| 4b | Settings | Change admin password if still default |
| 4c | Security | Set **wallet passphrase** (encrypts recovery words — not the same as login) |
| 4d | Wallets | Create a **testnet** wallet → write down words → confirm backup |
| 4e | Sync | Click Sync until it succeeds |
| 4f | Receive | Copy address → get free coins from a testnet faucet → Sync again |
| 4g | Send | Optional: send a small amount to another testnet address |

Unsure of login password:

```powershell
.\venv\Scripts\python.exe scripts\debug_login.py
```

More detail: [TESTNET_CHECKLIST.md](./TESTNET_CHECKLIST.md)

---

### 5 — Test the installed desktop app

```powershell
# run the installer you built
.\releases\coinwallet-windows-x64-setup.exe
```

After install: launch CoinWallet → complete setup wizard if shown → repeat step 4 (login, passphrase, wallet, sync).

Windows may show **“Unknown publisher”** — normal until you code-sign.

---

## Optional (skip for now if you want)

| Task | How |
|------|-----|
| Code signing (SmartScreen) | Set `WIN_SIGN_CERT_PATH` + password, then `build-windows.ps1` |
| Redeploy marketing site | `.\scripts\deploy-site.ps1` (only if you changed releases/manifest) |
| Lighthouse scores | Build `site/`, run Lighthouse, fill table in `site/README.md` |
| macOS build | Needs a Mac: `./scripts/build-mac.sh` + publish script |

---

## Quick copy-paste (minimum path)

```powershell
cd C:\Users\aksel\Documents\GitHub\trading-bot
& "$env:ProgramFiles\GitHub CLI\gh.exe" auth login
.\scripts\publish-github-release.ps1 -Version 0.1.0
.\scripts\build-windows.ps1
.\scripts\publish-github-release.ps1 -Version 0.1.0
.\start_admin.ps1
# then: browser → login → passphrase → testnet wallet → sync
```
