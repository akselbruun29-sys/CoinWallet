# CoinWallet download site

Public marketing and download pages for CoinWallet (`site/`). Built with SvelteKit 5 and Tailwind CSS 4.

## Development

```bash
cd site
npm install
npm run dev
```

Open http://localhost:5174

## Production build

```bash
cd site
npm run build
```

The `prebuild` script syncs `releases/releases.json` into `site/static/releases/`. Static output is written to `site/build/`.

Preview locally:

```bash
npm run preview
```

## Deploy to Cloudflare Pages (free tier)

### One-time Cloudflare setup

1. Create a [Cloudflare](https://dash.cloudflare.com) account.
2. **Workers & Pages → Create → Pages → Connect to Git** (optional) or use Wrangler CLI below.
3. Create project name **`coinwallet`** (must match `site/wrangler.toml`).
4. Under **Settings → Environment variables**, add:
   - `VITE_PUBLIC_API_URL` — public URL of your wallet API (for the leaderboard page), e.g. `https://api.yourdomain.com`
5. Under **Settings → Builds** (if using Git connect):
   - **Root directory:** `site`
   - **Build command:** `npm ci && npm run build`
   - **Build output directory:** `site/build` (or `build` if root is `site`)

### GitHub Actions (recommended)

Add repository secrets:

| Secret | Description |
|--------|-------------|
| `CLOUDFLARE_API_TOKEN` | API token with **Cloudflare Pages — Edit** permission |
| `CLOUDFLARE_ACCOUNT_ID` | Account ID from Cloudflare dashboard |

Optional repository variable:

| Variable | Description |
|----------|-------------|
| `VITE_PUBLIC_API_URL` | Baked into the site at build time for leaderboard fetch |

Push to `main`/`master` (when `site/` or `releases/` changes) runs `.github/workflows/deploy-site.yml`.

Manual deploy: **Actions → Deploy site → Run workflow**.

### Local deploy (Wrangler CLI)

```bash
npx wrangler login
# Windows
./scripts/deploy-site.ps1
# macOS / Linux
./scripts/deploy-site.sh
```

Or from `site/`:

```bash
npm run deploy:cf
```

### Custom domain

In Cloudflare Pages → **coinwallet** → **Custom domains**, add e.g. `coinwallet.example.com`.

## Release manifest

Platform downloads are driven by `releases/releases.json` (Windows and macOS only). After desktop builds, run `scripts/finalize-release.ps1` (or `finalize-release.sh`) to verify checksums and sync manifest.bootstrap` artifacts into `site/static/releases/`, then redeploy the site.

## Pages

| Route | Purpose |
|-------|---------|
| `/` | Home |
| `/download` | Platform downloads |
| `/install` | Windows & macOS install guides |
| `/leaderboard` | Public rankings |
| `/privacy` | Privacy policy |
| `/terms` | Terms of use |
