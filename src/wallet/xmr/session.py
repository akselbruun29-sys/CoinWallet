"""Open a restored Monero wallet on the local wallet-rpc sidecar."""
from __future__ import annotations

from src.database import WalletDatabase
from src.wallet.xmr.keys import decrypt_xmr_wallet_secrets
from src.wallet.xmr.rpc import WalletRpcClient


def wallet_rpc_filename(wallet_id: int) -> str:
    return f"coinwallet_{wallet_id}"


def open_wallet_rpc(
    db: WalletDatabase, wallet_id: int, user_id: int
) -> tuple[WalletRpcClient, dict]:
    wallet = db.get_wallet_with_secrets(wallet_id, user_id)
    if not wallet:
        raise ValueError("Wallet not found")
    if wallet.get("asset_type") != "xmr":
        raise ValueError("Not an XMR wallet")

    mnemonic, _view_key = decrypt_xmr_wallet_secrets(wallet, user_id)
    network = wallet["network"]
    rpc = WalletRpcClient(network, db)
    restore_height = int(wallet.get("xmr_restore_height") or 0)

    rpc.close_wallet()
    rpc.restore_deterministic_wallet(
        wallet_rpc_filename(wallet_id),
        mnemonic,
        restore_height=restore_height,
    )
    return rpc, wallet
