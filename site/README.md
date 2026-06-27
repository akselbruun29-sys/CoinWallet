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

Static output is written to `site/build/` — ready for any static host.

Preview locally:

```bash
npm run preview
```

## Deploy

### Cloudflare Pages

1. Connect the repository in Cloudflare Pages.
2. **Build command:** `cd site && npm install && npm run build`
3. **Build output directory:** `site/build`
4. **Node version:** 20 or later

### GitHub Pages

1. Run `npm run build` in `site/`.
2. Publish the contents of `site/build/` to your `gh-pages` branch or use GitHub Actions with `peaceiris/actions-gh-pages`, setting `publish_dir` to `site/build`.

## Release manifest

Platform downloads are driven by `releases/releases.json` at the repo root (Windows and macOS only).

## Pages

| Route | Purpose |
|-------|---------|
| `/` | Home |
| `/download` | Platform downloads |
| `/leaderboard` | Public rankings (API wired in Phase 4) |
| `/privacy` | Privacy policy |
| `/terms` | Terms of use |
