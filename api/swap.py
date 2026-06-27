"""BTC ↔ XMR swap API — user-initiated quotes only."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field

from api.auth import AuthUser, get_current_user, get_db
from api.rate_limit import check_rate_limit
from api.security import require_wallet_unlocked
from src.database import WalletDatabase
from src.wallet.swap.registry import list_providers
from src.wallet.swap.service import SwapService

router = APIRouter(prefix="/api/swap", tags=["swap"])


def _swap_service(db: WalletDatabase = Depends(get_db)) -> SwapService:
    return SwapService(db)


def _client_ip(request: Request) -> str:
    if request.client:
        return request.client.host
    return ""


class AttachSwapTxidsRequest(BaseModel):
    from_txid: Optional[str] = Field(default=None, max_length=64)
    to_txid: Optional[str] = Field(default=None, max_length=64)


class ExecuteSwapRequest(BaseModel):
    quote_id: str = Field(..., min_length=8)
    destination_wallet_id: int = Field(..., gt=0)


@router.get("/providers")
def swap_providers(
    user: AuthUser = Depends(get_current_user),
    db: WalletDatabase = Depends(get_db),
):
    return {"providers": list_providers(db)}


@router.get("/quote")
def swap_quote(
    request: Request,
    from_asset: str = Query(..., alias="from", pattern="^(btc|xmr)$"),
    to_asset: str = Query(..., alias="to", pattern="^(btc|xmr)$"),
    amount_sats: int = Query(..., gt=0),
    provider: Optional[str] = Query(default=None),
    user: AuthUser = Depends(get_current_user),
    service: SwapService = Depends(_swap_service),
):
    check_rate_limit(request, "swap_quote", limit=60, window_seconds=60)
    try:
        quote = service.get_quote(
            user.id,
            from_asset=from_asset,
            to_asset=to_asset,
            amount_atomic=amount_sats,
            provider_id=provider,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return quote.to_dict()


@router.post("/execute")
def swap_execute(
    body: ExecuteSwapRequest,
    request: Request,
    user: AuthUser = Depends(require_wallet_unlocked),
    db: WalletDatabase = Depends(get_db),
    service: SwapService = Depends(_swap_service),
):
    check_rate_limit(request, "swap_execute", limit=20, window_seconds=60)
    try:
        result = service.execute_swap(
            user.id,
            quote_id=body.quote_id,
            destination_wallet_id=body.destination_wallet_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    db.add_audit(
        "SWAP_EXECUTE",
        user_id=user.id,
        details=(
            f"swap_id={result['swap_id']} {result['from_asset']}→{result['to_asset']} "
            f"send={result['send_amount_atomic']} provider={result['provider']}"
        ),
        ip=_client_ip(request),
    )
    return result


@router.get("/history")
def swap_history(
    limit: int = Query(default=50, ge=1, le=100),
    user: AuthUser = Depends(get_current_user),
    service: SwapService = Depends(_swap_service),
):
    return {"swaps": service.list_swaps(user.id, limit=limit)}


@router.patch("/{swap_id}/txids")
def attach_swap_txids(
    swap_id: int,
    body: AttachSwapTxidsRequest,
    request: Request,
    user: AuthUser = Depends(get_current_user),
    db: WalletDatabase = Depends(get_db),
    service: SwapService = Depends(_swap_service),
):
    if body.from_txid is None and body.to_txid is None:
        raise HTTPException(status_code=400, detail="Provide from_txid and/or to_txid")
    try:
        result = service.attach_txids(
            swap_id,
            user.id,
            from_txid=body.from_txid,
            to_txid=body.to_txid,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    db.add_audit(
        "SWAP_TX_LINKED",
        user_id=user.id,
        details=f"swap_id={swap_id} from={bool(body.from_txid)} to={bool(body.to_txid)}",
        ip=_client_ip(request),
    )
    return result


@router.get("/{swap_id}")
def swap_status(
    swap_id: int,
    user: AuthUser = Depends(get_current_user),
    service: SwapService = Depends(_swap_service),
):
    try:
        return service.get_swap(swap_id, user.id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
