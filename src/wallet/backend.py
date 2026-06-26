"""Blockchain backends — Esplora (default) and optional Bitcoin Core RPC."""
from __future__ import annotations

import os
from typing import Any, Optional, Protocol

import requests

from src.wallet.keys import esplora_base_url


class ChainBackend(Protocol):
    network: str

    def tip_height(self) -> int: ...
    def address_utxos(self, address: str) -> list[dict]: ...
    def address_transactions(self, address: str) -> list[dict]: ...
    def broadcast_tx(self, tx_hex: str) -> str: ...
    def suggested_fee_rate(self) -> int: ...
    def peer_count(self) -> int: ...
    def backend_name(self) -> str: ...


class EsploraBackend:
    def __init__(self, network: str = "testnet"):
        self.network = network
        self.base_url = esplora_base_url(network)
        self.session = requests.Session()
        proxy = os.getenv("HTTP_PROXY") or os.getenv("HTTPS_PROXY")
        if os.getenv("TOR_ENABLED", "false").lower() == "true" and proxy:
            self.session.proxies.update({"http": proxy, "https": proxy})

    def backend_name(self) -> str:
        return "esplora"

    def peer_count(self) -> int:
        return 0

    def _get(self, path: str) -> Any:
        url = f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"
        resp = self.session.get(url, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def _post_text(self, path: str, body: str) -> str:
        url = f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"
        resp = self.session.post(url, data=body, timeout=30)
        if resp.status_code >= 400:
            raise ValueError(resp.text or resp.reason)
        return resp.text.strip()

    def tip_height(self) -> int:
        return int(self._get("blocks/tip/height"))

    def address_utxos(self, address: str) -> list[dict]:
        return self._get(f"address/{address}/utxo")

    def address_transactions(self, address: str) -> list[dict]:
        return self._get(f"address/{address}/txs")

    def broadcast_tx(self, tx_hex: str) -> str:
        return self._post_text("tx", tx_hex)

    def fee_estimates(self) -> dict[str, float]:
        try:
            return self._get("fee-estimates")
        except Exception:
            return {"6": 5.0}

    def suggested_fee_rate(self) -> int:
        estimates = self.fee_estimates()
        for blocks in ("3", "6", "10", "18"):
            if blocks in estimates:
                return max(1, int(estimates[blocks]))
        return 5


class BitcoinCoreBackend:
    """Hybrid backend: Core RPC for chain tip, fees, broadcast; Esplora for address indexes."""

    def __init__(self, network: str = "testnet"):
        self.network = network
        self.rpc_url = os.getenv("BITCOIN_RPC_URI", "http://127.0.0.1:18332")
        self.rpc_user = os.getenv("BITCOIN_RPC_USER", "")
        self.rpc_password = os.getenv("BITCOIN_RPC_PASSWORD", "")
        self.session = requests.Session()
        self._esplora = EsploraBackend(network)

    def backend_name(self) -> str:
        return "core"

    def _rpc(self, method: str, params: Optional[list] = None) -> Any:
        payload = {"jsonrpc": "1.0", "id": "wallet-vault", "method": method, "params": params or []}
        auth = (self.rpc_user, self.rpc_password) if self.rpc_user else None
        resp = self.session.post(self.rpc_url, json=payload, auth=auth, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if data.get("error"):
            raise ValueError(data["error"])
        return data["result"]

    def tip_height(self) -> int:
        return int(self._rpc("getblockcount"))

    def peer_count(self) -> int:
        info = self._rpc("getnetworkinfo")
        return int(info.get("connections", 0))

    def address_utxos(self, address: str) -> list[dict]:
        return self._esplora.address_utxos(address)

    def address_transactions(self, address: str) -> list[dict]:
        return self._esplora.address_transactions(address)

    def broadcast_tx(self, tx_hex: str) -> str:
        return self._rpc("sendrawtransaction", [tx_hex])

    def suggested_fee_rate(self) -> int:
        try:
            result = self._rpc("estimatesmartfee", [6])
            feerate = result.get("feerate")
            if feerate:
                return max(1, int(feerate * 100_000))
        except Exception:
            pass
        return self._esplora.suggested_fee_rate()


def get_backend(network: str, db: Optional[Any] = None) -> ChainBackend:
    backend_type = os.getenv("BITCOIN_BACKEND_TYPE", "esplora").lower()
    if db is not None:
        backend_type = db.get_setting("backend_type", backend_type).lower()

    if backend_type == "core":
        return BitcoinCoreBackend(network)
    return EsploraBackend(network)
