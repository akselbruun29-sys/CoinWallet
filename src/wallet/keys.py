"""BIP39/BIP84 key generation and seed encryption."""
import base64
import hashlib
import os
from dataclasses import dataclass
from typing import Optional

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from embit import bip32, bip39
from embit.networks import NETWORKS
from embit.script import p2wpkh
from mnemonic import Mnemonic


NETWORK_CONFIG = {
    "testnet": {"embit": "test", "coin_type": 1},
    "mainnet": {"embit": "main", "coin_type": 0},
    "signet": {"embit": "signet", "coin_type": 1},
    "regtest": {"embit": "regtest", "coin_type": 1},
}

DEFAULT_ESPLORA = {
    "testnet": "https://blockstream.info/testnet/api/",
    "mainnet": "https://blockstream.info/api/",
    "signet": "https://blockstream.info/signet/api/",
    "regtest": "http://127.0.0.1:3002/",
}


@dataclass
class WalletKeys:
    mnemonic: str
    xpub: str
    derivation_path: str
    encrypted_seed: str


def _encryption_key() -> bytes:
    raw = os.getenv("WALLET_ENCRYPTION_KEY", "")
    if not raw:
        raise ValueError("WALLET_ENCRYPTION_KEY is not set in environment")
    return hashlib.sha256(raw.encode()).digest()


def encrypt_mnemonic_with_dek(mnemonic: str, dek: bytes) -> str:
    aesgcm = AESGCM(dek)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, mnemonic.encode("utf-8"), None)
    return base64.b64encode(nonce + ciphertext).decode("ascii")


def decrypt_mnemonic_with_dek(encrypted: str, dek: bytes) -> str:
    data = base64.b64decode(encrypted)
    nonce, ciphertext = data[:12], data[12:]
    return AESGCM(dek).decrypt(nonce, ciphertext, None).decode("utf-8")


def encrypt_mnemonic(mnemonic: str, dek: Optional[bytes] = None) -> str:
    key = dek if dek is not None else _encryption_key()
    return encrypt_mnemonic_with_dek(mnemonic, key)


def decrypt_mnemonic(encrypted: str, dek: Optional[bytes] = None) -> str:
    key = dek if dek is not None else _encryption_key()
    return decrypt_mnemonic_with_dek(encrypted, key)


def derivation_path_for_network(network: str) -> str:
    coin = NETWORK_CONFIG.get(network, NETWORK_CONFIG["testnet"])["coin_type"]
    return f"m/84'/{coin}'/0'"


def generate_wallet_keys(network: str = "testnet", dek: Optional[bytes] = None) -> WalletKeys:
    if network not in NETWORK_CONFIG:
        raise ValueError(f"Unsupported network: {network}")

    mnemonic = Mnemonic("english").generate(strength=128)
    path = derivation_path_for_network(network)
    xpub = account_xpub_from_mnemonic(mnemonic, network)
    if dek is None:
        encrypted = encrypt_mnemonic(mnemonic)
    else:
        encrypted = encrypt_mnemonic_with_dek(mnemonic, dek)
    return WalletKeys(
        mnemonic=mnemonic,
        xpub=xpub,
        derivation_path=path,
        encrypted_seed=encrypted,
    )


def account_xpub_from_mnemonic(mnemonic: str, network: str) -> str:
    account = account_key_from_mnemonic(mnemonic, network)
    return account.to_public().to_string()


def account_key_from_mnemonic(mnemonic: str, network: str) -> bip32.HDKey:
    seed = bip39.mnemonic_to_seed(mnemonic)
    root = bip32.HDKey.from_seed(seed)
    path = derivation_path_for_network(network)
    return root.derive(path)


def account_key_from_encrypted_seed(
    encrypted_seed: str, network: str, user_id: Optional[int] = None, encryption_version: int = 1
) -> bip32.HDKey:
    mnemonic = decrypt_wallet_seed(
        encrypted_seed, network, user_id=user_id, encryption_version=encryption_version
    )
    return account_key_from_mnemonic(mnemonic, network)


def decrypt_wallet_seed(
    encrypted_seed: str,
    network: str,
    *,
    user_id: Optional[int] = None,
    encryption_version: int = 1,
) -> str:
    if encryption_version >= 2:
        if user_id is None:
            raise ValueError("user_id required for user-encrypted wallets")
        from src.wallet.vault import get_unlocked_dek

        dek = get_unlocked_dek(user_id)
        if not dek:
            raise ValueError("Wallet locked — unlock with your wallet passphrase")
        return decrypt_mnemonic_with_dek(encrypted_seed, dek)
    return decrypt_mnemonic(encrypted_seed)


def account_key_from_wallet(wallet: dict, user_id: int) -> bip32.HDKey:
    mnemonic = decrypt_wallet_seed(
        wallet["encrypted_seed"],
        wallet["network"],
        user_id=user_id,
        encryption_version=wallet.get("encryption_version") or 1,
    )
    return account_key_from_mnemonic(mnemonic, wallet["network"])


def receive_address(account: bip32.HDKey, network: str, index: int) -> str:
    embit_net = NETWORKS[NETWORK_CONFIG[network]["embit"]]
    child = account.derive(f"m/0/{index}")
    return p2wpkh(child).address(embit_net)


def receive_script_pubkey(account: bip32.HDKey, index: int) -> bytes:
    child = account.derive(f"m/0/{index}")
    return bytes(p2wpkh(child).script_pubkey())


def signing_key_for_index(account: bip32.HDKey, index: int) -> bip32.HDKey:
    return account.derive(f"m/0/{index}")


def change_address(account: bip32.HDKey, network: str, index: int) -> str:
    embit_net = NETWORKS[NETWORK_CONFIG[network]["embit"]]
    child = account.derive(f"m/1/{index}")
    return p2wpkh(child).address(embit_net)


def change_script_pubkey(account: bip32.HDKey, index: int) -> bytes:
    child = account.derive(f"m/1/{index}")
    return bytes(p2wpkh(child).script_pubkey())


def change_signing_key_for_index(account: bip32.HDKey, index: int) -> bip32.HDKey:
    return account.derive(f"m/1/{index}")


def esplora_base_url(network: str) -> str:
    custom = os.getenv("BITCOIN_BACKEND_URI", "").strip()
    if custom:
        return custom if custom.endswith("/") else f"{custom}/"
    return DEFAULT_ESPLORA.get(network, DEFAULT_ESPLORA["testnet"])
