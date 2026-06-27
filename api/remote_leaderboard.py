"""Token-authenticated leaderboard endpoints for the cloud services deployment."""
from __future__ import annotations

import time
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from api.auth import get_db
from api.leaderboard import validate_display_name
from api.rate_limit import check_rate_limit
from api.remote_services import hash_leaderboard_token, leaderboard_cloud_mode
from src.database import WalletDatabase

router = APIRouter(prefix="/api/leaderboard/remote", tags=["leaderboard-remote"])

_last_balance_update: dict[str, float] = {}
_MAX_BALANCE_JUMP_RATIO = 2.0
_MIN_UPDATE_INTERVAL = 60


class TokenRegisterRequest(BaseModel):
    token: str = Field(..., min_length=16, max_length=128)
    display_name: str = Field(..., min_length=2, max_length=32)
    network: str = Field(..., pattern="^(testnet|signet|regtest|mainnet)$")
    balance_sats: int = Field(..., ge=0)


class TokenUpdateRequest(BaseModel):
    token: str = Field(..., min_length=16, max_length=128)
    network: str = Field(..., pattern="^(testnet|signet|regtest|mainnet)$")
    balance_sats: int = Field(..., ge=0)


class TokenOptOutRequest(BaseModel):
    token: str = Field(..., min_length=16, max_length=128)
    network: str = Field(..., pattern="^(testnet|signet|regtest|mainnet)$")


def _token_hash(token: str) -> str:
    return hash_leaderboard_token(token.strip())


def _entry_by_hash(db: WalletDatabase, token_hash: str, network: str) -> Optional[dict]:
    return db.get_global_leaderboard_entry(token_hash, network)


def _require_cloud_db() -> WalletDatabase:
    if not leaderboard_cloud_mode():
        raise HTTPException(
            status_code=503,
            detail="Leaderboard cloud endpoints are disabled (set LEADERBOARD_CLOUD_MODE=true)",
        )
    return get_db()


@router.post("/register")
def remote_register(
    body: TokenRegisterRequest,
    request: Request,
    db: WalletDatabase = Depends(get_db),
):
    if not leaderboard_cloud_mode():
        raise HTTPException(
            status_code=503,
            detail="Leaderboard cloud endpoints are disabled (set LEADERBOARD_CLOUD_MODE=true)",
        )
    check_rate_limit(request, "leaderboard_remote_register", limit=20, window_seconds=60)
    try:
        display_name = validate_display_name(body.display_name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    token_hash = _token_hash(body.token)
    db.upsert_global_leaderboard(
        token_hash, display_name, body.network, body.balance_sats, opted_in=True
    )
    rank = db.get_global_leaderboard_rank(token_hash, body.network)
    return {
        "network": body.network,
        "display_name": display_name,
        "balance_sats": body.balance_sats,
        "rank": rank,
    }


@router.post("/update")
def remote_update(
    body: TokenUpdateRequest,
    request: Request,
    db: WalletDatabase = Depends(get_db),
):
    if not leaderboard_cloud_mode():
        raise HTTPException(
            status_code=503,
            detail="Leaderboard cloud endpoints are disabled (set LEADERBOARD_CLOUD_MODE=true)",
        )
    check_rate_limit(request, "leaderboard_remote_update")
    token_hash = _token_hash(body.token)
    entry = _entry_by_hash(db, token_hash, body.network)
    if not entry or not entry["opted_in"]:
        raise HTTPException(status_code=404, detail="Leaderboard entry not found")

    update_key = f"{token_hash}:{body.network}"
    now = time.time()
    last = _last_balance_update.get(update_key, 0)
    if now - last < _MIN_UPDATE_INTERVAL:
        raise HTTPException(status_code=429, detail="Updates limited to once per minute")

    previous = int(entry.get("balance_sats") or 0)
    tolerance = max(10_000, int(previous * 0.05))
    if previous > 0 and body.balance_sats > previous * _MAX_BALANCE_JUMP_RATIO + tolerance:
        raise HTTPException(status_code=400, detail="Impossible balance increase rejected")

    if previous > 0 and abs(body.balance_sats - previous) > tolerance:
        raise HTTPException(status_code=400, detail="Balance change exceeds tolerance")

    db.update_global_leaderboard_balance(token_hash, body.network, body.balance_sats)
    _last_balance_update[update_key] = now
    return {
        "network": body.network,
        "balance_sats": body.balance_sats,
        "rank": db.get_global_leaderboard_rank(token_hash, body.network),
    }


@router.post("/opt-out")
def remote_opt_out(
    body: TokenOptOutRequest,
    request: Request,
    db: WalletDatabase = Depends(get_db),
):
    if not leaderboard_cloud_mode():
        raise HTTPException(
            status_code=503,
            detail="Leaderboard cloud endpoints are disabled (set LEADERBOARD_CLOUD_MODE=true)",
        )
    check_rate_limit(request, "leaderboard_remote_opt_out", limit=10, window_seconds=60)
    token_hash = _token_hash(body.token)
    db.delete_global_leaderboard(token_hash, body.network)
    return {"network": body.network, "opted_in": False}
