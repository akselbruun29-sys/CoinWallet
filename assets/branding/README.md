# CoinWallet branding assets

| File | Purpose |
|------|---------|
| `icon-master.svg` | Vector source (1024 viewBox) |
| `icon-1024.png` | Master raster for Tauri + stores |

## Regenerate platform icons

```bash
pip install pillow
python scripts/generate_icons.py
```

This writes:

- `assets/branding/icon-1024.png`
- `src-tauri/icons/*` (PNG, ICO; runs `cargo tauri icon` when available)
- `site/static/favicon.*` and `admin/static/favicon.*`

Run after changing the logo design.
