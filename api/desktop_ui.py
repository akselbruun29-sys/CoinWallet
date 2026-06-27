"""Serve the built admin UI from the desktop API sidecar (avoids Tauri asset protocol issues)."""
from __future__ import annotations

import os
import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles


def resolve_ui_root() -> Path | None:
    override = os.getenv("COINWALLET_UI_ROOT", "").strip()
    if override:
        path = Path(override)
        return path if path.is_dir() else None

    if getattr(sys, "frozen", False):
        bundled = Path(getattr(sys, "_MEIPASS", "")) / "admin_ui"
        if bundled.is_dir():
            return bundled

    repo = Path(__file__).resolve().parents[1]
    dev_build = repo / "admin" / "build"
    if dev_build.is_dir():
        return dev_build

    return None


def mount_desktop_ui(app: FastAPI) -> bool:
    root = resolve_ui_root()
    if root is None or not (root / "index.html").is_file():
        return False

    app.mount("/", StaticFiles(directory=str(root), html=True), name="desktop_ui")
    return True
