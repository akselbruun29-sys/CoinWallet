"""Per-user wallet encryption and in-memory unlock sessions."""
from __future__ import annotations

import base64
import hashlib
import os
import secrets
import time
from threading import Lock
from typing import Optional

import bcrypt

UNLOCK_TTL_SECONDS = int(os.getenv("WALLET_UNLOCK_TTL", "900"))  # 15 minutes

_unlocks: dict[int, tuple[bytes, float]] = {}
_lock = Lock()


def new_wallet_salt() -> str:
    return base64.b64encode(secrets.token_bytes(16)).decode("ascii")


def derive_user_dek(passphrase: str, salt_b64: str, user_id: int) -> bytes:
    pepper = os.getenv("WALLET_ENCRYPTION_KEY", "")
    if not pepper:
        raise ValueError("WALLET_ENCRYPTION_KEY is not set in environment")
    salt = base64.b64decode(salt_b64)
    material = f"wallet-vault-v2:{user_id}".encode()
    return hashlib.pbkdf2_hmac(
        "sha256",
        passphrase.encode("utf-8"),
        salt + pepper.encode("utf-8") + material,
        210_000,
        dklen=32,
    )


def make_wallet_verifier(dek: bytes) -> str:
    digest = hashlib.sha256(dek).digest()
    return bcrypt.hashpw(digest, bcrypt.gensalt()).decode("ascii")


def verify_wallet_passphrase(
    passphrase: str, salt_b64: str, user_id: int, verifier: str
) -> bool:
    try:
        dek = derive_user_dek(passphrase, salt_b64, user_id)
        digest = hashlib.sha256(dek).digest()
        return bcrypt.checkpw(digest, verifier.encode("ascii"))
    except (ValueError, TypeError):
        return False


def unlock_user(user_id: int, dek: bytes) -> float:
    expires_at = time.time() + UNLOCK_TTL_SECONDS
    with _lock:
        _unlocks[user_id] = (dek, expires_at)
    return expires_at


def lock_user(user_id: int) -> None:
    with _lock:
        _unlocks.pop(user_id, None)


def get_unlocked_dek(user_id: int) -> Optional[bytes]:
    with _lock:
        entry = _unlocks.get(user_id)
        if not entry:
            return None
        dek, expires_at = entry
        if time.time() >= expires_at:
            _unlocks.pop(user_id, None)
            return None
        return dek


def unlock_status(user_id: int) -> dict:
    with _lock:
        entry = _unlocks.get(user_id)
        if not entry:
            return {"unlocked": False, "expires_at": None}
        _, expires_at = entry
        if time.time() >= expires_at:
            _unlocks.pop(user_id, None)
            return {"unlocked": False, "expires_at": None}
        return {"unlocked": True, "expires_at": expires_at}


def touch_unlock(user_id: int) -> None:
    dek = get_unlocked_dek(user_id)
    if dek is not None:
        unlock_user(user_id, dek)
