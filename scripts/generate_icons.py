#!/usr/bin/env python3
"""Generate CoinWallet icons from the 1024 master (Phase 9.1).

Usage:
  pip install pillow
  python scripts/generate_icons.py
  cargo tauri icon assets/branding/icon-1024.png   # optional: refresh .icns / Windows tiles
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT / "assets" / "branding" / "icon-1024.png"
SVG = ROOT / "assets" / "branding" / "icon-master.svg"
TAURI_ICONS = ROOT / "src-tauri" / "icons"
WEB_DIRS = (
    ROOT / "site" / "static",
    ROOT / "admin" / "static",
)

BG = (35, 35, 41, 255)
GREEN = (82, 208, 132, 255)
GREEN_SHADOW = (35, 35, 41, 90)
FG = (244, 244, 245, 255)


def _require_pillow():
    try:
        from PIL import Image, ImageDraw  # noqa: PLC0415

        return Image, ImageDraw
    except ImportError:
        print("Install Pillow: pip install pillow", file=sys.stderr)
        sys.exit(1)


def _shield_points(cx: float, cy: float, w: float, h: float) -> list[tuple[float, float]]:
    hw = w / 2
    return [
        (cx, cy - h / 2),
        (cx + hw, cy - h / 2 + h * 0.12),
        (cx + hw, cy + h * 0.08),
        (cx, cy + h / 2),
        (cx - hw, cy + h * 0.08),
        (cx - hw, cy - h / 2 + h * 0.12),
    ]


def render_icon(size: int):
    Image, ImageDraw = _require_pillow()
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    margin = int(size * 0.0625)
    radius = int(size * 0.1875)
    draw.rounded_rectangle(
        [margin, margin, size - margin, size - margin],
        radius=radius,
        fill=BG,
    )

    cx, cy = size / 2, size / 2
    shield_h = size * 0.52
    shield_w = size * 0.44
    outer = _shield_points(cx, cy - size * 0.02, shield_w, shield_h)
    draw.polygon(outer, fill=GREEN)
    inner = _shield_points(cx, cy - size * 0.02, shield_w * 0.72, shield_h * 0.72)
    draw.polygon(inner, fill=GREEN_SHADOW)

    # Stylized B mark
    bar_w = max(2, int(size * 0.043))
    x0 = int(cx - size * 0.06)
    y0 = int(cy - size * 0.12)
    y1 = int(cy + size * 0.12)
    draw.rounded_rectangle([x0, y0, x0 + bar_w, y1], radius=bar_w // 2, fill=FG)
    top = [x0 + bar_w, y0, int(cx + size * 0.08), y0, int(cx + size * 0.08), cy - 2, x0 + bar_w, cy - 2]
    bot = [x0 + bar_w, cy + 2, int(cx + size * 0.1), cy + 2, int(cx + size * 0.1), y1, x0 + bar_w, y1]
    draw.polygon(top, fill=FG)
    draw.polygon(bot, fill=FG)
    return img


def write_png(path: Path, size: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    render_icon(size).save(path, format="PNG")


def write_ico(path: Path) -> None:
    Image, _ = _require_pillow()
    sizes = [16, 24, 32, 48, 64, 128, 256]
    images = [render_icon(s) for s in sizes]
    path.parent.mkdir(parents=True, exist_ok=True)
    images[0].save(
        path,
        format="ICO",
        sizes=[(s, s) for s in sizes],
        append_images=images[1:],
    )


def write_web_assets() -> None:
    for directory in WEB_DIRS:
        directory.mkdir(parents=True, exist_ok=True)
        render_icon(512).save(directory / "apple-touch-icon.png", format="PNG")
        render_icon(192).save(directory / "icon-192.png", format="PNG")
        render_icon(32).save(directory / "favicon.png", format="PNG")
        write_ico(directory / "favicon.ico")


def write_tauri_pngs() -> None:
    TAURI_ICONS.mkdir(parents=True, exist_ok=True)
    mapping = {
        "32x32.png": 32,
        "128x128.png": 128,
        "128x128@2x.png": 256,
        "icon.png": 512,
        "Square30x30Logo.png": 30,
        "Square44x44Logo.png": 44,
        "Square71x71Logo.png": 71,
        "Square89x89Logo.png": 89,
        "Square107x107Logo.png": 107,
        "Square142x142Logo.png": 142,
        "Square150x150Logo.png": 150,
        "Square284x284Logo.png": 284,
        "Square310x310Logo.png": 310,
        "StoreLogo.png": 50,
    }
    for name, size in mapping.items():
        write_png(TAURI_ICONS / name, size)
    write_ico(TAURI_ICONS / "icon.ico")


def maybe_tauri_icon() -> None:
    try:
        subprocess.run(
            ["cargo", "tauri", "icon", str(MASTER)],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        print("Refreshed src-tauri/icons via cargo tauri icon")
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        print(f"Note: cargo tauri icon skipped ({exc}). PNG/ICO assets still written.")


def main() -> int:
    MASTER.parent.mkdir(parents=True, exist_ok=True)
    write_png(MASTER, 1024)
    write_tauri_pngs()
    write_web_assets()
    maybe_tauri_icon()
    print(f"Wrote {MASTER}")
    print(f"Wrote Tauri icons in {TAURI_ICONS}")
    for directory in WEB_DIRS:
        print(f"Wrote web icons in {directory}")
    if SVG.exists():
        print(f"Vector source: {SVG}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
