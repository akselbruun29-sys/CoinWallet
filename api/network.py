"""Network privacy status — Tor bootstrap and first-run wizard."""
from __future__ import annotations

import os

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api.auth import get_db
from src.database import WalletDatabase
from src.wallet.tor import tor_bootstrap_complete, tor_enabled_for_db, tor_socks_url

router = APIRouter(prefix="/api/network", tags=["network"])


def _tor_managed() -> bool:
    return os.getenv("COINWALLET_TOR_MANAGED", "").lower() in ("true", "1", "yes")


def _wizard_complete(db: WalletDatabase) -> bool:
    if os.getenv("COINWALLET_PRODUCTION", "").lower() not in ("true", "1", "yes"):
        return True
    if not _tor_managed():
        return db.get_setting("network_wizard_complete", "false").lower() in (
            "true",
            "1",
            "yes",
        )
    return db.get_setting("network_wizard_complete", "false").lower() in (
        "true",
        "1",
        "yes",
    )


@router.get("/status")
def network_status(db: WalletDatabase = Depends(get_db)):
    tor_on = tor_enabled_for_db(db)
    managed = _tor_managed()
    bootstrap = tor_bootstrap_complete(db) if tor_on else False
    return {
        "tor_enabled": tor_on,
        "tor_managed": managed,
        "tor_proxy": tor_socks_url() if tor_on else None,
        "tor_bootstrap_complete": bootstrap,
        "network_wizard_complete": _wizard_complete(db),
        "backend": "esplora",
        "light_client": True,
    }


class CompleteSetupRequest(BaseModel):
    skip_tor: bool = False


@router.post("/complete-setup")
def complete_network_setup(
    body: CompleteSetupRequest,
    db: WalletDatabase = Depends(get_db),
):
    if body.skip_tor and _tor_managed():
        raise HTTPException(status_code=400, detail="Tor setup is required in desktop builds")
    if _tor_managed() and not body.skip_tor:
        if tor_enabled_for_db(db) and not tor_bootstrap_complete(db):
            raise HTTPException(
                status_code=409,
                detail="Tor is still connecting — wait for bootstrap to finish",
            )
    db.set_setting("network_wizard_complete", "true")
    if not body.skip_tor and _tor_managed():
        db.set_setting("tor_enabled", "true")
    return {"network_wizard_complete": True, "tor_enabled": tor_enabled_for_db(db)}
