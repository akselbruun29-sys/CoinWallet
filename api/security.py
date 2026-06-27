"""Wallet passphrase and unlock session API."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from api.auth import AuthUser, get_any_authenticated_user, get_current_user, get_db
from api.rate_limit import check_rate_limit
from src.database import WalletDatabase
from src.wallet.keys import (
    decrypt_mnemonic,
    decrypt_mnemonic_with_dek,
    encrypt_mnemonic_with_dek,
)
from src.wallet.vault import (
    derive_user_dek,
    get_unlocked_dek,
    lock_user,
    make_wallet_verifier,
    new_wallet_salt,
    unlock_status,
    unlock_ttl_seconds,
    unlock_user,
    verify_wallet_passphrase,
)

router = APIRouter(prefix="/api/security", tags=["security"])


class PassphraseRequest(BaseModel):
    passphrase: str = Field(..., min_length=8)


class ChangePassphraseRequest(BaseModel):
    current_passphrase: str = Field(..., min_length=8)
    new_passphrase: str = Field(..., min_length=8)


class MainnetAckRequest(BaseModel):
    acknowledged: bool = Field(..., description="Must be true to record mainnet risk acceptance")


def _migrate_wallets_to_v2(
    db: WalletDatabase, user_id: int, dek: bytes
) -> int:
    migrated = 0
    for wallet in db.list_wallets_with_secrets(user_id):
        version = wallet.get("encryption_version") or 1
        if version >= 2:
            continue
        mnemonic = decrypt_mnemonic(wallet["encrypted_seed"])
        encrypted = encrypt_mnemonic_with_dek(mnemonic, dek)
        db.update_wallet_encryption(wallet["id"], encrypted, encryption_version=2)
        migrated += 1
    return migrated


def _security_payload(user_id: int, db: WalletDatabase) -> dict:
    security = db.get_wallet_security(user_id) or {}
    status = unlock_status(user_id)
    legacy_count = sum(
        1
        for w in db.list_wallets_with_secrets(user_id)
        if (w.get("encryption_version") or 1) < 2
    )
    return {
        "has_wallet_passphrase": bool(security.get("wallet_key_verifier")),
        "unlocked": status["unlocked"],
        "expires_at": status["expires_at"],
        "unlock_ttl_seconds": unlock_ttl_seconds(),
        "legacy_wallet_count": legacy_count,
        "wallet_count": db.count_user_wallets(user_id),
        "admin_cannot_decrypt": bool(security.get("wallet_key_verifier")),
        "mainnet_acknowledged": bool(db.get_mainnet_ack_at(user_id)),
        "mainnet_ack_at": db.get_mainnet_ack_at(user_id),
    }


@router.get("/wallet")
def wallet_security_status(
    user: AuthUser = Depends(get_any_authenticated_user),
    db: WalletDatabase = Depends(get_db),
):
    return _security_payload(user.id, db)


@router.post("/wallet/passphrase/setup")
def setup_wallet_passphrase(
    body: PassphraseRequest,
    request: Request,
    user: AuthUser = Depends(get_current_user),
    db: WalletDatabase = Depends(get_db),
):
    check_rate_limit(request, "wallet_unlock")
    security = db.get_wallet_security(user.id) or {}
    if security.get("wallet_key_verifier"):
        raise HTTPException(
            status_code=400, detail="Wallet passphrase already configured"
        )

    salt = new_wallet_salt()
    dek = derive_user_dek(body.passphrase, salt, user.id)
    verifier = make_wallet_verifier(dek)
    db.set_wallet_security(user.id, salt, verifier)
    migrated = _migrate_wallets_to_v2(db, user.id, dek)
    expires_at = unlock_user(user.id, dek)

    db.add_audit(
        "WALLET_PASSPHRASE_SET",
        user_id=user.id,
        details=f"migrated_wallets={migrated}",
        ip=request.client.host if request.client else "",
    )
    return {
        **_security_payload(user.id, db),
        "migrated_wallets": migrated,
        "expires_at": expires_at,
    }


@router.post("/wallet/unlock")
def unlock_wallet(
    body: PassphraseRequest,
    request: Request,
    user: AuthUser = Depends(get_current_user),
    db: WalletDatabase = Depends(get_db),
):
    check_rate_limit(request, "wallet_unlock")
    security = db.get_wallet_security(user.id) or {}
    salt = security.get("wallet_key_salt")
    verifier = security.get("wallet_key_verifier")
    if not salt or not verifier:
        raise HTTPException(
            status_code=400,
            detail="Set a wallet passphrase in Security before unlocking",
        )

    if not verify_wallet_passphrase(body.passphrase, salt, user.id, verifier):
        db.add_audit(
            "WALLET_UNLOCK_FAILED",
            user_id=user.id,
            ip=request.client.host if request.client else "",
        )
        raise HTTPException(status_code=401, detail="Invalid wallet passphrase")

    dek = derive_user_dek(body.passphrase, salt, user.id)
    expires_at = unlock_user(user.id, dek)
    db.add_audit(
        "WALLET_UNLOCKED",
        user_id=user.id,
        ip=request.client.host if request.client else "",
    )
    return {**_security_payload(user.id, db), "expires_at": expires_at}


@router.post("/wallet/lock")
def lock_wallet(
    user: AuthUser = Depends(get_current_user),
    db: WalletDatabase = Depends(get_db),
):
    lock_user(user.id)
    db.add_audit("WALLET_LOCKED", user_id=user.id)
    return _security_payload(user.id, db)


@router.post("/wallet/passphrase/change")
def change_wallet_passphrase(
    body: ChangePassphraseRequest,
    user: AuthUser = Depends(get_current_user),
    db: WalletDatabase = Depends(get_db),
):
    security = db.get_wallet_security(user.id) or {}
    salt = security.get("wallet_key_salt")
    verifier = security.get("wallet_key_verifier")
    if not salt or not verifier:
        raise HTTPException(status_code=400, detail="Wallet passphrase not configured")

    if not verify_wallet_passphrase(
        body.current_passphrase, salt, user.id, verifier
    ):
        raise HTTPException(status_code=401, detail="Current wallet passphrase is wrong")

    old_dek = derive_user_dek(body.current_passphrase, salt, user.id)
    if get_unlocked_dek(user.id) is None:
        unlock_user(user.id, old_dek)

    new_salt = new_wallet_salt()
    new_dek = derive_user_dek(body.new_passphrase, new_salt, user.id)
    new_verifier = make_wallet_verifier(new_dek)

    for wallet in db.list_wallets_with_secrets(user.id):
        version = wallet.get("encryption_version") or 1
        if version >= 2:
            mnemonic = decrypt_mnemonic_with_dek(wallet["encrypted_seed"], old_dek)
        else:
            mnemonic = decrypt_mnemonic(wallet["encrypted_seed"])
        encrypted = encrypt_mnemonic_with_dek(mnemonic, new_dek)
        db.update_wallet_encryption(wallet["id"], encrypted, encryption_version=2)

    db.set_wallet_security(user.id, new_salt, new_verifier)
    unlock_user(user.id, new_dek)
    db.add_audit("WALLET_PASSPHRASE_CHANGED", user_id=user.id)
    return _security_payload(user.id, db)


@router.post("/wallet/migrate")
def migrate_legacy_wallets(
    body: PassphraseRequest,
    request: Request,
    user: AuthUser = Depends(get_current_user),
    db: WalletDatabase = Depends(get_db),
):
    """Re-encrypt legacy v1 wallets using the user's wallet passphrase."""
    check_rate_limit(request, "wallet_unlock")
    security = db.get_wallet_security(user.id) or {}
    salt = security.get("wallet_key_salt")
    verifier = security.get("wallet_key_verifier")
    if not salt or not verifier:
        raise HTTPException(status_code=400, detail="Set wallet passphrase first")
    if not verify_wallet_passphrase(body.passphrase, salt, user.id, verifier):
        db.add_audit(
            "WALLET_UNLOCK_FAILED",
            user_id=user.id,
            ip=request.client.host if request.client else "",
        )
        raise HTTPException(status_code=401, detail="Invalid wallet passphrase")

    dek = derive_user_dek(body.passphrase, salt, user.id)
    migrated = _migrate_wallets_to_v2(db, user.id, dek)
    unlock_user(user.id, dek)
    db.add_audit(
        "WALLET_MIGRATED",
        user_id=user.id,
        details=f"migrated_wallets={migrated}",
        ip=request.client.host if request.client else "",
    )
    return {**_security_payload(user.id, db), "migrated_wallets": migrated}


def require_wallet_unlocked(
    user: AuthUser = Depends(get_current_user),
    db: WalletDatabase = Depends(get_db),
) -> AuthUser:
    security = db.get_wallet_security(user.id) or {}
    if not security.get("wallet_key_verifier"):
        raise HTTPException(
            status_code=403,
            detail="Set your wallet passphrase in Security before using wallet keys",
        )
    if get_unlocked_dek(user.id) is None:
        raise HTTPException(
            status_code=403,
            detail="Wallet locked — unlock with your wallet passphrase",
        )
    return user


@router.post("/wallet/mainnet/acknowledge")
def acknowledge_mainnet_risks(
    body: MainnetAckRequest,
    request: Request,
    user: AuthUser = Depends(require_wallet_unlocked),
    db: WalletDatabase = Depends(get_db),
):
    if not body.acknowledged:
        raise HTTPException(status_code=400, detail="Mainnet acknowledgment must be accepted")

    if db.get_mainnet_ack_at(user.id):
        return _security_payload(user.id, db)

    ack_at = db.set_mainnet_ack(user.id)
    db.add_audit(
        "MAINNET_ACKNOWLEDGED",
        user_id=user.id,
        details=f"ack_at={ack_at}",
        ip=request.client.host if request.client else "",
    )
    return _security_payload(user.id, db)
