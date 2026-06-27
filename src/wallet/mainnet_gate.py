"""Mainnet safety gates — v2 encryption, passphrase, and user acknowledgment."""
from __future__ import annotations

from src.wallet.vault import get_unlocked_dek


def ensure_mainnet_ready(db, user_id: int, network: str) -> None:
    """Raise ValueError if mainnet operations are not fully gated."""
    if network != "mainnet":
        return

    import os

    allowed = os.getenv("ALLOW_MAINNET", "").lower() in ("true", "1", "yes")
    if not allowed and db.get_setting("allow_mainnet", "false").lower() != "true":
        raise ValueError(
            "Mainnet is disabled on this instance. An admin must enable it in Settings."
        )

    security = db.get_wallet_security(user_id) or {}
    if not security.get("wallet_key_verifier"):
        raise ValueError(
            "Set and unlock your wallet passphrase in Security before using mainnet."
        )

    if get_unlocked_dek(user_id) is None:
        raise ValueError("Wallet locked — unlock with your wallet passphrase for mainnet.")

    if not db.get_mainnet_ack_at(user_id):
        raise ValueError(
            "Acknowledge mainnet risks in Security before creating or using mainnet wallets."
        )

    legacy = _legacy_wallet_count(db, user_id)
    if legacy:
        raise ValueError(
            f"Migrate {legacy} legacy wallet(s) to v2 encryption in Security before mainnet."
        )


def ensure_wallet_mainnet_ready(db, user_id: int, wallet_id: int) -> None:
    wallet = db.get_wallet(wallet_id, user_id)
    if not wallet:
        raise ValueError("Wallet not found")
    ensure_mainnet_ready(db, user_id, wallet.get("network", "testnet"))


def _legacy_wallet_count(db, user_id: int) -> int:
    return sum(
        1
        for w in db.list_wallets_with_secrets(user_id)
        if (w.get("encryption_version") or 1) < 2
    )


def ensure_no_legacy_wallets(db, user_id: int) -> None:
    """Block send/swap until v2 passphrase encryption is applied to all wallets."""
    legacy = _legacy_wallet_count(db, user_id)
    if legacy:
        raise ValueError(
            f"Migrate {legacy} legacy wallet(s) to v2 encryption in Security before sending or swapping."
        )
