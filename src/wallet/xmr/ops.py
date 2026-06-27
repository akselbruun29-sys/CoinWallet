"""Monero receive and send via wallet-rpc."""
from __future__ import annotations

from src.database import WalletDatabase
from src.wallet.mainnet_gate import ensure_wallet_mainnet_ready
from src.wallet.xmr.rpc import WalletRpcError
from src.wallet.xmr.session import open_wallet_rpc


class XmrOpsEngine:
    def __init__(self, db: WalletDatabase):
        self.db = db

    def get_receive_address(
        self,
        wallet_id: int,
        user_id: int,
        *,
        advance: bool = True,
        subaddress: bool = True,
    ) -> dict:
        rpc, wallet = open_wallet_rpc(self.db, wallet_id, user_id)
        network = wallet["network"]
        account_index = int(wallet.get("xmr_account_index") or 0)

        if not subaddress:
            primary = wallet.get("xmr_primary_address") or rpc.get_address(
                account_index, 0
            )
            return {
                "address": primary,
                "network": network,
                "index": 0,
                "address_type": "primary",
                "asset_type": "xmr",
            }

        created = rpc.create_address(account_index, label="coinwallet")
        address = created["address"]
        index = created["address_index"]
        if advance:
            self.db.set_receive_index(wallet_id, index + 1)
        return {
            "address": address,
            "network": network,
            "index": index,
            "address_type": "subaddress",
            "asset_type": "xmr",
        }

    def preview_send(
        self,
        wallet_id: int,
        user_id: int,
        address: str,
        amount_atomic: int,
        *,
        priority: int = 1,
    ) -> dict:
        ensure_wallet_mainnet_ready(self.db, user_id, wallet_id)
        rpc, wallet = open_wallet_rpc(self.db, wallet_id, user_id)
        account_index = int(wallet.get("xmr_account_index") or 0)
        try:
            result = rpc.transfer(
                [{"address": address, "amount": amount_atomic}],
                account_index=account_index,
                priority=priority,
                do_not_relay=True,
            )
        except WalletRpcError as exc:
            raise ValueError(str(exc)) from exc

        fee = int(result.get("fee") or 0)
        return {
            "address": address,
            "amount_sats": amount_atomic,
            "fee_sats": fee,
            "fee_rate_sat_vb": 0,
            "change_sats": 0,
            "input_count": 0,
            "estimated_vsize": int(result.get("weight") or 0),
            "asset_type": "xmr",
            "network": wallet["network"],
        }

    def send(
        self,
        wallet_id: int,
        user_id: int,
        address: str,
        amount_atomic: int,
        *,
        priority: int = 1,
    ) -> dict:
        ensure_wallet_mainnet_ready(self.db, user_id, wallet_id)
        rpc, wallet = open_wallet_rpc(self.db, wallet_id, user_id)
        account_index = int(wallet.get("xmr_account_index") or 0)
        try:
            result = rpc.transfer(
                [{"address": address, "amount": amount_atomic}],
                account_index=account_index,
                priority=priority,
                do_not_relay=False,
            )
        except WalletRpcError as exc:
            raise ValueError(str(exc)) from exc

        txid = result.get("tx_hash") or ""
        if not txid:
            raise ValueError("Transfer failed — no transaction hash returned")

        return {
            "txid": txid,
            "fee_sats": int(result.get("fee") or 0),
            "amount_sats": amount_atomic,
            "hex": "",
            "asset_type": "xmr",
            "network": wallet["network"],
        }
