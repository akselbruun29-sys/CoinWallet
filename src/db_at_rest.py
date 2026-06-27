"""Optional AES-GCM encryption for the wallet SQLite file at rest (Phase 11.15)."""
from __future__ import annotations

import hashlib
import logging
import os
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

logger = logging.getLogger(__name__)

_MAGIC = b"CWDBENC1"
_KDF_ITERATIONS = 210_000


def encrypted_db_path(db_path: Path) -> Path:
    return db_path.with_name(db_path.name + ".cwenc")


def db_encryption_enabled() -> bool:
    return bool(os.getenv("WALLET_DB_KEY", "").strip())


def _derive_key(password: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        _KDF_ITERATIONS,
        dklen=32,
    )


def encrypt_file(plaintext_path: Path, enc_path: Path, password: str) -> None:
    salt = os.urandom(16)
    nonce = os.urandom(12)
    key = _derive_key(password, salt)
    plaintext = plaintext_path.read_bytes()
    ciphertext = AESGCM(key).encrypt(nonce, plaintext, None)
    enc_path.write_bytes(_MAGIC + salt + nonce + ciphertext)
    logger.info("Sealed wallet database at %s", enc_path)


def decrypt_file(enc_path: Path, plaintext_path: Path, password: str) -> None:
    payload = enc_path.read_bytes()
    if len(payload) < len(_MAGIC) + 16 + 12 + 16 or payload[: len(_MAGIC)] != _MAGIC:
        raise ValueError("Invalid encrypted wallet database format")
    salt = payload[len(_MAGIC) : len(_MAGIC) + 16]
    nonce = payload[len(_MAGIC) + 16 : len(_MAGIC) + 28]
    ciphertext = payload[len(_MAGIC) + 28 :]
    key = _derive_key(password, salt)
    plaintext = AESGCM(key).decrypt(nonce, ciphertext, None)
    plaintext_path.parent.mkdir(parents=True, exist_ok=True)
    plaintext_path.write_bytes(plaintext)
    logger.info("Opened encrypted wallet database at %s", plaintext_path)


def prepare_db_path(db_path: Path) -> Path:
    """Decrypt wallet.db.cwenc to wallet.db when WALLET_DB_KEY is configured."""
    password = os.getenv("WALLET_DB_KEY", "").strip()
    enc_path = encrypted_db_path(db_path)
    if not password:
        if enc_path.exists() and not db_path.exists():
            raise RuntimeError(
                f"Encrypted database {enc_path.name} exists but WALLET_DB_KEY is not set"
            )
        return db_path

    if enc_path.exists() and not db_path.exists():
        try:
            decrypt_file(enc_path, db_path, password)
        except Exception as exc:
            raise RuntimeError("Failed to decrypt wallet database — check WALLET_DB_KEY") from exc
    elif enc_path.exists() and db_path.exists():
        logger.warning(
            "Both %s and %s exist — using plaintext %s",
            db_path.name,
            enc_path.name,
            db_path.name,
        )
    return db_path


def seal_db_path(db_path: Path) -> None:
    """Encrypt wallet.db to wallet.db.cwenc and remove plaintext (graceful shutdown)."""
    password = os.getenv("WALLET_DB_KEY", "").strip()
    if not password or not db_path.exists():
        return
    enc_path = encrypted_db_path(db_path)
    try:
        encrypt_file(db_path, enc_path, password)
        db_path.unlink()
        logger.info("Wallet database sealed at rest (%s)", enc_path.name)
    except Exception:
        logger.exception("Failed to seal wallet database at rest")
