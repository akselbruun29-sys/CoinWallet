"""Wallet API routes."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from api.auth import AuthUser, get_current_user, get_db
from api.events import publish_wallet_event
from api.security import require_wallet_unlocked
from src.database import WalletDatabase
from src.wallet.core import WalletService

router = APIRouter(prefix="/api/wallets", tags=["wallets"])


def _wallet_service(db: WalletDatabase = Depends(get_db)) -> WalletService:
    return WalletService(db)


class CreateWalletRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=64)
    network: str = Field(default="testnet", pattern="^(testnet|signet|regtest|mainnet)$")


class ImportWalletRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=64)
    mnemonic: str = Field(..., min_length=12)
    network: str = Field(default="testnet", pattern="^(testnet|signet|regtest|mainnet)$")


class UpdateUtxoRequest(BaseModel):
    frozen: Optional[bool] = None
    label: Optional[str] = Field(default=None, max_length=128)


class UtxoRef(BaseModel):
    txid: str = Field(..., min_length=64, max_length=64)
    vout: int = Field(..., ge=0)


class SendRequest(BaseModel):
    address: str = Field(..., min_length=10)
    amount_sats: int = Field(..., gt=0)
    fee_rate_sat_vb: Optional[int] = Field(default=None, gt=0)
    utxos: Optional[list[UtxoRef]] = None


@router.get("")
def list_wallets(
    user: AuthUser = Depends(get_current_user),
    db: WalletDatabase = Depends(get_db),
):
    return db.list_wallets(user.id)


@router.post("")
def create_wallet(
    body: CreateWalletRequest,
    request: Request,
    user: AuthUser = Depends(require_wallet_unlocked),
    db: WalletDatabase = Depends(get_db),
    service: WalletService = Depends(_wallet_service),
):
    try:
        wallet_id, mnemonic = service.create_wallet_with_keys(
            user.id, body.name, network=body.network
        )
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    db.add_audit(
        "WALLET_CREATED",
        user_id=user.id,
        details=f"id={wallet_id} name={body.name}",
        ip=request.client.host if request.client else "",
    )
    wallet = db.get_wallet(wallet_id, user.id)
    return {**wallet, "mnemonic": mnemonic}


@router.post("/import")
def import_wallet(
    body: ImportWalletRequest,
    request: Request,
    user: AuthUser = Depends(require_wallet_unlocked),
    db: WalletDatabase = Depends(get_db),
    service: WalletService = Depends(_wallet_service),
):
    try:
        wallet_id = service.import_wallet_with_mnemonic(
            user.id, body.name, body.mnemonic, network=body.network
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    db.add_audit(
        "WALLET_IMPORTED",
        user_id=user.id,
        details=f"id={wallet_id} name={body.name}",
        ip=request.client.host if request.client else "",
    )
    return db.get_wallet(wallet_id, user.id)


def _get_wallet_or_404(wallet_id: int, user: AuthUser, db: WalletDatabase) -> dict:
    wallet = db.get_wallet(wallet_id, user.id)
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")
    return wallet


@router.get("/{wallet_id}")
def get_wallet(
    wallet_id: int,
    user: AuthUser = Depends(get_current_user),
    db: WalletDatabase = Depends(get_db),
):
    return _get_wallet_or_404(wallet_id, user, db)


@router.post("/{wallet_id}/sync")
def sync_wallet(
    wallet_id: int,
    user: AuthUser = Depends(require_wallet_unlocked),
    db: WalletDatabase = Depends(get_db),
    service: WalletService = Depends(_wallet_service),
):
    _get_wallet_or_404(wallet_id, user, db)
    try:
        result = service.sync(wallet_id, user.id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    publish_wallet_event(user.id, "wallet_synced", wallet_id=wallet_id)
    return result


@router.get("/{wallet_id}/balance")
def wallet_balance(
    wallet_id: int,
    user: AuthUser = Depends(get_current_user),
    db: WalletDatabase = Depends(get_db),
    service: WalletService = Depends(_wallet_service),
):
    _get_wallet_or_404(wallet_id, user, db)
    try:
        return service.get_balance(wallet_id, user.id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{wallet_id}/sync-status")
def sync_status(
    wallet_id: int,
    user: AuthUser = Depends(get_current_user),
    db: WalletDatabase = Depends(get_db),
    service: WalletService = Depends(_wallet_service),
):
    _get_wallet_or_404(wallet_id, user, db)
    try:
        return service.get_sync_status(wallet_id, user.id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{wallet_id}/utxos")
def wallet_utxos(
    wallet_id: int,
    user: AuthUser = Depends(get_current_user),
    db: WalletDatabase = Depends(get_db),
    service: WalletService = Depends(_wallet_service),
):
    _get_wallet_or_404(wallet_id, user, db)
    try:
        return service.get_utxos(wallet_id, user.id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.patch("/{wallet_id}/utxos/{txid}/{vout}")
def update_wallet_utxo(
    wallet_id: int,
    txid: str,
    vout: int,
    body: UpdateUtxoRequest,
    user: AuthUser = Depends(get_current_user),
    db: WalletDatabase = Depends(get_db),
):
    _get_wallet_or_404(wallet_id, user, db)
    if body.frozen is None and body.label is None:
        raise HTTPException(status_code=400, detail="No fields to update")
    utxo = db.update_utxo(
        wallet_id,
        txid,
        vout,
        frozen=body.frozen,
        label=body.label,
    )
    if not utxo:
        raise HTTPException(status_code=404, detail="UTXO not found")
    return utxo


@router.get("/{wallet_id}/transactions")
def wallet_transactions(
    wallet_id: int,
    limit: int = 50,
    user: AuthUser = Depends(get_current_user),
    db: WalletDatabase = Depends(get_db),
    service: WalletService = Depends(_wallet_service),
):
    _get_wallet_or_404(wallet_id, user, db)
    try:
        return service.get_transactions(wallet_id, user.id, limit=limit)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{wallet_id}/receive-address")
def receive_address(
    wallet_id: int,
    user: AuthUser = Depends(require_wallet_unlocked),
    db: WalletDatabase = Depends(get_db),
    service: WalletService = Depends(_wallet_service),
):
    _get_wallet_or_404(wallet_id, user, db)
    try:
        return service.get_receive_address(wallet_id, user.id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{wallet_id}/stats")
def wallet_stats(
    wallet_id: int,
    user: AuthUser = Depends(get_current_user),
    db: WalletDatabase = Depends(get_db),
    service: WalletService = Depends(_wallet_service),
):
    _get_wallet_or_404(wallet_id, user, db)
    try:
        return service.get_stats(wallet_id, user.id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{wallet_id}/privacy")
def wallet_privacy(
    wallet_id: int,
    user: AuthUser = Depends(get_current_user),
    db: WalletDatabase = Depends(get_db),
    service: WalletService = Depends(_wallet_service),
):
    _get_wallet_or_404(wallet_id, user, db)
    try:
        return service.get_privacy_summary(wallet_id, user.id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{wallet_id}/send/preview")
def send_preview(
    wallet_id: int,
    body: SendRequest,
    user: AuthUser = Depends(require_wallet_unlocked),
    db: WalletDatabase = Depends(get_db),
    service: WalletService = Depends(_wallet_service),
):
    _get_wallet_or_404(wallet_id, user, db)
    try:
        return service.preview_send(
            wallet_id,
            user.id,
            body.address,
            body.amount_sats,
            body.fee_rate_sat_vb,
            [u.model_dump() for u in body.utxos] if body.utxos else None,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{wallet_id}/send")
def send_funds(
    wallet_id: int,
    body: SendRequest,
    request: Request,
    user: AuthUser = Depends(require_wallet_unlocked),
    db: WalletDatabase = Depends(get_db),
    service: WalletService = Depends(_wallet_service),
):
    _get_wallet_or_404(wallet_id, user, db)
    try:
        result = service.send(
            wallet_id,
            user.id,
            body.address,
            body.amount_sats,
            body.fee_rate_sat_vb,
            [u.model_dump() for u in body.utxos] if body.utxos else None,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    db.add_audit(
        "TX_SENT",
        user_id=user.id,
        details=f"wallet_id={wallet_id} txid={result['txid']}",
        ip=request.client.host if request.client else "",
    )
    publish_wallet_event(
        user.id, "tx_sent", wallet_id=wallet_id, txid=result["txid"]
    )
    return result
