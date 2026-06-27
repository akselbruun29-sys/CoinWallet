"""Monero 25-word mnemonic generation and encrypted seed/view-key storage."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import monero.const as xmr_const
from monero.seed import Seed

from src.wallet.keys import decrypt_mnemonic_with_dek, encrypt_mnemonic_with_dek

DEFAULT_XMR_NETWORK = "stagenet"
XMR_NETWORKS = ("stagenet", "testnet", "mainnet")

_NET_MAP = {
    "mainnet": xmr_const.NET_MAIN,
    "stagenet": xmr_const.NET_STAGE,
    "testnet": xmr_const.NET_TEST,
}


@dataclass
class XmrWalletKeys:
    mnemonic: str
    primary_address: str
    encrypted_seed: str
    encrypted_view_key: str
    network: str
    account_index: int = 0


def normalize_mnemonic(phrase: str) -> str:
    return " ".join(phrase.strip().lower().split())


def monero_net_for_network(network: str) -> str:
    if network not in _NET_MAP:
        raise ValueError(f"Unsupported XMR network: {network}")
    return _NET_MAP[network]


def validate_xmr_mnemonic(phrase: str) -> bool:
    normalized = normalize_mnemonic(phrase)
    words = normalized.split()
    if len(words) not in (13, 25):
        return False
    try:
        Seed(normalized)
        return True
    except (ValueError, TypeError):
        return False


def seed_from_mnemonic(phrase: str) -> Seed:
    normalized = normalize_mnemonic(phrase)
    if not validate_xmr_mnemonic(normalized):
        raise ValueError("Invalid Monero mnemonic phrase")
    return Seed(normalized)


def primary_address_from_mnemonic(phrase: str, network: str) -> str:
    seed = seed_from_mnemonic(phrase)
    return str(seed.public_address(net=monero_net_for_network(network)))


def _encrypt_secret(value: str, dek: bytes) -> str:
    return encrypt_mnemonic_with_dek(value, dek)


def _decrypt_secret(encrypted: str, dek: bytes) -> str:
    return decrypt_mnemonic_with_dek(encrypted, dek)


def _keys_from_seed(seed: Seed, network: str, dek: bytes) -> XmrWalletKeys:
    net = monero_net_for_network(network)
    primary = str(seed.public_address(net=net))
    view_key = str(seed.secret_view_key())
    mnemonic = seed.phrase
    return XmrWalletKeys(
        mnemonic=mnemonic,
        primary_address=primary,
        encrypted_seed=_encrypt_secret(mnemonic, dek),
        encrypted_view_key=_encrypt_secret(view_key, dek),
        network=network,
    )


def generate_xmr_wallet_keys(
    network: str = DEFAULT_XMR_NETWORK, dek: bytes | None = None
) -> XmrWalletKeys:
    if dek is None:
        raise ValueError("User DEK required for XMR wallet encryption")
    if network not in XMR_NETWORKS:
        raise ValueError(f"Unsupported XMR network: {network}")
    return _keys_from_seed(Seed(), network, dek)


def import_xmr_wallet_keys(
    mnemonic: str, network: str, dek: bytes, *, account_index: int = 0
) -> XmrWalletKeys:
    if network not in XMR_NETWORKS:
        raise ValueError(f"Unsupported XMR network: {network}")
    keys = _keys_from_seed(seed_from_mnemonic(mnemonic), network, dek)
    keys.account_index = account_index
    return keys


def decrypt_xmr_wallet_secrets(
    wallet: dict,
    user_id: int,
) -> tuple[str, str]:
    """Return (mnemonic, secret_view_key) for internal sync/signing only — never expose via API."""
    from src.wallet.vault import get_unlocked_dek

    if wallet.get("asset_type") != "xmr":
        raise ValueError("Not an XMR wallet")
    dek = get_unlocked_dek(user_id)
    if dek is None:
        raise ValueError("Wallet locked — unlock with your wallet passphrase")
    encrypted_seed = wallet.get("encrypted_seed")
    encrypted_view = wallet.get("xmr_encrypted_view_key")
    if not encrypted_seed or not encrypted_view:
        raise ValueError("XMR wallet secrets missing")
    if (wallet.get("encryption_version") or 1) < 2:
        raise ValueError("XMR wallets require v2 user encryption")
    mnemonic = _decrypt_secret(encrypted_seed, dek)
    view_key = _decrypt_secret(encrypted_view, dek)
    return mnemonic, view_key
