"""Sync Monero wallets via local monero-wallet-rpc sidecar."""
from __future__ import annotations

import logging
from typing import Any

from src.database import WalletDatabase
from src.wallet.xmr.rpc import WalletRpcClient, WalletRpcError
from src.wallet.xmr.session import open_wallet_rpc

logger = logging.getLogger(__name__)

# Amounts stored in `amount_sats` columns as Monero atomic units (1 XMR = 1e12).
BALANCE_UTXO_TXID = "__xmr_balance__"


class XmrSyncEngine:
    def __init__(self, db: WalletDatabase):
        self.db = db

    def _wallet_row(self, wallet_id: int, user_id: int) -> dict:
        wallet = self.db.get_wallet_with_secrets(wallet_id, user_id)
        if not wallet:
            raise ValueError("Wallet not found")
        if wallet.get("asset_type") != "xmr":
            raise ValueError("Not an XMR wallet")
        return wallet

    def _rpc(self, network: str) -> WalletRpcClient:
        return WalletRpcClient(network, self.db)

    def sync_wallet(self, wallet_id: int, user_id: int) -> dict:
        rpc, wallet = open_wallet_rpc(self.db, wallet_id, user_id)
        network = wallet["network"]
        account_index = int(wallet.get("xmr_account_index") or 0)
        primary = wallet.get("xmr_primary_address") or ""
        restore_height = int(wallet.get("xmr_restore_height") or 0)

        rpc.refresh()

        tip = rpc.get_height()
        transfers = rpc.get_transfers(account_index=account_index)
        self.db.clear_utxos(wallet_id)
        self._mirror_transfers(wallet_id, transfers, tip)
        self._mirror_balance_utxo(wallet_id, rpc, account_index, primary, tip)

        self.db.update_wallet_sync(wallet_id, tip)
        if restore_height < tip:
            self.db.update_wallet_xmr_sync(wallet_id, restore_height=tip)

        return self.get_sync_status(wallet_id, user_id)

    def _mirror_transfers(
        self,
        wallet_id: int,
        transfers: dict[str, list[dict]],
        tip: int,
    ) -> None:
        seen: set[str] = set()

        for bucket, direction in (
            ("in", "receive"),
            ("pool", "receive"),
            ("pending", "receive"),
            ("out", "send"),
        ):
            for entry in transfers.get(bucket, []):
                txid = entry.get("txid")
                if not txid or txid in seen:
                    continue
                seen.add(txid)
                amount = int(entry.get("amount") or 0)
                fee = int(entry.get("fee") or 0) if direction == "send" else 0
                height = entry.get("height")
                block_height = int(height) if height is not None else None

                self.db.upsert_transaction(
                    wallet_id=wallet_id,
                    txid=txid,
                    direction=direction,
                    amount_sats=amount,
                    fee_sats=fee,
                    block_height=block_height,
                    timestamp=None,
                    raw_json=str(entry)[:8000],
                )

    def _mirror_balance_utxo(
        self,
        wallet_id: int,
        rpc: WalletRpcClient,
        account_index: int,
        primary: str,
        tip: int,
    ) -> None:
        """Aggregate unlocked balance as one spendable row until per-output tracking lands."""
        balances = rpc.get_balance(account_index=account_index)
        unlocked = int(balances.get("unlocked_balance") or 0)
        total = int(balances.get("balance") or 0)
        pending = max(0, total - unlocked)

        self.db.upsert_utxo(
            wallet_id=wallet_id,
            txid=BALANCE_UTXO_TXID,
            vout=0,
            amount_sats=unlocked,
            address=primary,
            confirmations=10 if unlocked else 0,
            derivation_index=0,
            is_change=False,
        )
        if pending:
            self.db.upsert_utxo(
                wallet_id=wallet_id,
                txid=f"{BALANCE_UTXO_TXID}_pending",
                vout=0,
                amount_sats=pending,
                address=primary,
                confirmations=0,
                derivation_index=0,
                is_change=False,
            )

    def get_sync_status(self, wallet_id: int, user_id: int) -> dict:
        wallet = self._wallet_row(wallet_id, user_id)
        network = wallet["network"]
        last = int(wallet.get("last_synced_height") or 0)
        try:
            tip = self._rpc(network).get_height()
        except WalletRpcError as exc:
            return {
                "wallet_id": wallet_id,
                "synced": False,
                "progress": 0,
                "block_height": last,
                "last_synced_height": last,
                "message": str(exc),
                "backend": "monero-wallet-rpc",
            }

        synced = last >= tip and last > 0
        progress = min(100, int((last / tip) * 100)) if tip else 0
        return {
            "wallet_id": wallet_id,
            "synced": synced,
            "progress": progress,
            "block_height": tip,
            "last_synced_height": last,
            "backend": "monero-wallet-rpc",
        }

    def get_balance(self, wallet_id: int, user_id: int) -> dict:
        self._wallet_row(wallet_id, user_id)
        confirmed, unconfirmed = self.db.wallet_balance_sats(wallet_id)
        return {
            "confirmed_sats": confirmed,
            "unconfirmed_sats": unconfirmed,
            "total_sats": confirmed + unconfirmed,
            "asset_type": "xmr",
        }

    def rpc_health(self, network: str) -> dict[str, Any]:
        try:
            rpc = self._rpc(network)
            height = rpc.get_height()
            return {
                "ok": True,
                "backend": rpc.backend_name(),
                "url": rpc.url,
                "height": height,
            }
        except WalletRpcError as exc:
            return {"ok": False, "backend": "monero-wallet-rpc", "message": str(exc)}
