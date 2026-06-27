"""JSON-RPC client for monero-wallet-rpc (local sidecar)."""
from __future__ import annotations

import os
from typing import Any, Optional

import requests

from src.wallet.xmr.keys import DEFAULT_XMR_NETWORK, XMR_NETWORKS

DEFAULT_WALLET_RPC = {
    "mainnet": "http://127.0.0.1:18082/json_rpc",
    "testnet": "http://127.0.0.1:18083/json_rpc",
    "stagenet": "http://127.0.0.1:38088/json_rpc",
}


def wallet_rpc_url(network: str, db: Any | None = None) -> str:
    env = os.getenv("XMR_WALLET_RPC_URI", "").strip()
    if env:
        return env if env.endswith("/json_rpc") else f"{env.rstrip('/')}/json_rpc"
    if db is not None:
        custom = (db.get_setting("xmr_wallet_rpc_uri") or "").strip()
        if custom:
            return custom if custom.endswith("/json_rpc") else f"{custom.rstrip('/')}/json_rpc"
    per_net = os.getenv(f"XMR_WALLET_RPC_URI_{network.upper()}", "").strip()
    if per_net:
        return per_net if per_net.endswith("/json_rpc") else f"{per_net.rstrip('/')}/json_rpc"
    return DEFAULT_WALLET_RPC.get(network, DEFAULT_WALLET_RPC[DEFAULT_XMR_NETWORK])


class WalletRpcError(Exception):
    pass


class WalletRpcClient:
    """Thin wrapper around monero-wallet-rpc JSON-RPC."""

    def __init__(
        self,
        network: str,
        db: Any | None = None,
        *,
        url: Optional[str] = None,
        username: str = "",
        password: str = "",
    ):
        if network not in XMR_NETWORKS:
            raise ValueError(f"Unsupported XMR network: {network}")
        self.network = network
        self.url = url or wallet_rpc_url(network, db)
        self.username = username or os.getenv("XMR_WALLET_RPC_USER", "")
        self.password = password or os.getenv("XMR_WALLET_RPC_PASSWORD", "")
        self.session = requests.Session()

    def call(self, method: str, params: Optional[dict] = None) -> dict:
        payload = {
            "jsonrpc": "2.0",
            "id": "coinwallet",
            "method": method,
            "params": params or {},
        }
        auth = (self.username, self.password) if self.username else None
        try:
            resp = self.session.post(self.url, json=payload, auth=auth, timeout=120)
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as exc:
            raise WalletRpcError(
                f"Cannot reach monero-wallet-rpc at {self.url}. "
                f"Start the sidecar for {self.network} and retry. ({exc})"
            ) from exc
        if "error" in data and data["error"]:
            err = data["error"]
            message = err.get("message", str(err))
            raise WalletRpcError(message)
        return data.get("result") or {}

    def close_wallet(self) -> None:
        try:
            self.call("close_wallet")
        except WalletRpcError:
            pass

    def restore_deterministic_wallet(
        self,
        filename: str,
        seed: str,
        *,
        restore_height: int = 0,
        password: str = "",
    ) -> None:
        self.call(
            "restore_deterministic_wallet",
            {
                "filename": filename,
                "seed": seed,
                "seed_offset": 0,
                "restore_height": restore_height,
                "password": password,
                "language": "English",
                "autosave_current": True,
            },
        )

    def refresh(self) -> None:
        self.call("refresh")

    def get_height(self) -> int:
        result = self.call("get_height")
        return int(result.get("height") or 0)

    def get_balance(self, account_index: int = 0) -> dict[str, int]:
        result = self.call("get_balance", {"account_index": account_index})
        return {
            "balance": int(result.get("balance") or 0),
            "unlocked_balance": int(result.get("unlocked_balance") or 0),
        }

    def get_transfers(self, account_index: int = 0) -> dict[str, list[dict]]:
        result = self.call(
            "get_transfers",
            {
                "in": True,
                "out": True,
                "pending": True,
                "pool": True,
                "failed": False,
                "filter_by_height": False,
                "account_index": account_index,
            },
        )
        return {
            key: list(result.get(key) or [])
            for key in ("in", "out", "pending", "pool")
        }

    def get_address(self, account_index: int = 0, address_index: int = 0) -> str:
        result = self.call(
            "get_address",
            {"account_index": account_index, "address_index": [address_index]},
        )
        addresses = result.get("addresses") or []
        if not addresses:
            raise WalletRpcError("No address returned from wallet-rpc")
        return str(addresses[0].get("address") or addresses[0])

    def create_address(self, account_index: int = 0, label: str = "") -> dict:
        result = self.call(
            "create_address",
            {"account_index": account_index, "label": label},
        )
        return {
            "address": str(result.get("address") or ""),
            "address_index": int(result.get("address_index") or 0),
        }

    def transfer(
        self,
        destinations: list[dict],
        *,
        account_index: int = 0,
        priority: int = 1,
        do_not_relay: bool = False,
    ) -> dict:
        result = self.call(
            "transfer",
            {
                "destinations": destinations,
                "account_index": account_index,
                "subaddr_indices": [0],
                "priority": priority,
                "ring_size": 11,
                "get_tx_key": False,
                "do_not_relay": do_not_relay,
            },
        )
        tx_hash = result.get("tx_hash")
        if not tx_hash:
            tx_list = result.get("tx_hash_list") or []
            tx_hash = tx_list[0] if tx_list else ""
        return {
            "tx_hash": str(tx_hash or ""),
            "fee": int(result.get("fee") or 0),
            "weight": int(result.get("weight") or 0),
        }

    def backend_name(self) -> str:
        return "monero-wallet-rpc"
