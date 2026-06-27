"""Swap quote orchestration."""
from __future__ import annotations

import json
import re
import time
from datetime import datetime, timezone
from typing import Optional

from src.database import WalletDatabase
from src.wallet.addresses import validate_deposit_address
from src.wallet.mainnet_gate import ensure_mainnet_ready, ensure_no_legacy_wallets
from src.wallet.swap.base import SwapProviderError
from src.wallet.swap.explorer import enrich_swap_record
from src.wallet.swap.registry import resolve_provider
from src.wallet.swap.types import SwapQuote
from src.wallet.xmr.keys import DEFAULT_XMR_NETWORK

SWAP_PAIRS = {("btc", "xmr"), ("xmr", "btc")}
_TXID_RE = re.compile(r"^[0-9a-fA-F]{64}$")

_quote_cache: dict[str, tuple[float, SwapQuote]] = {}


def _cache_quote(quote: SwapQuote) -> None:
    try:
        expires = datetime.fromisoformat(quote.expires_at.replace("Z", "+00:00"))
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        expires_ts = expires.timestamp()
    except ValueError:
        expires_ts = time.time() + 300
    _quote_cache[quote.quote_id] = (expires_ts, quote)


def get_cached_quote(quote_id: str) -> Optional[SwapQuote]:
    entry = _quote_cache.get(quote_id)
    if not entry:
        return None
    expires_ts, quote = entry
    if time.time() > expires_ts:
        _quote_cache.pop(quote_id, None)
        return None
    return quote


def _quote_expired(quote: SwapQuote) -> bool:
    try:
        expires = datetime.fromisoformat(quote.expires_at.replace("Z", "+00:00"))
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) >= expires
    except ValueError:
        return False


def _network_for_swap(db: WalletDatabase) -> str:
    return (db.get_setting("network") or "testnet").strip().lower()


def _valid_txid(txid: str) -> bool:
    return bool(_TXID_RE.match(txid.strip()))


class SwapService:
    def __init__(self, db: WalletDatabase):
        self.db = db

    def _network_for_asset(self, user_id: int, asset: str) -> str:
        wallets = self.db.list_wallets(user_id, asset_type=asset)
        if wallets:
            return str(wallets[0].get("network") or "testnet")
        if asset == "xmr":
            return DEFAULT_XMR_NETWORK
        return _network_for_swap(self.db)

    def _enrich(self, row: dict) -> dict:
        if not row.get("from_network"):
            row = {**row, "from_network": self._default_from_network(row)}
        if not row.get("to_network"):
            row = {**row, "to_network": self._default_to_network(row)}
        return enrich_swap_record(row)

    def _public_swap(self, row: dict, *, include_deposit: bool = False) -> dict:
        enriched = self._enrich(row)
        if not include_deposit:
            enriched.pop("deposit_address", None)
        return enriched

    def _default_from_network(self, row: dict) -> str:
        return "stagenet" if row.get("from_asset") == "xmr" else "testnet"

    def _default_to_network(self, row: dict) -> str:
        return "stagenet" if row.get("to_asset") == "xmr" else "testnet"

    def get_quote(
        self,
        user_id: int,
        *,
        from_asset: str,
        to_asset: str,
        amount_atomic: int,
        provider_id: str | None = None,
    ) -> SwapQuote:
        from_asset = from_asset.strip().lower()
        to_asset = to_asset.strip().lower()
        if from_asset == to_asset:
            raise ValueError("from and to assets must differ")
        if (from_asset, to_asset) not in SWAP_PAIRS:
            raise ValueError("Only BTC ↔ XMR swaps are supported")
        if amount_atomic <= 0:
            raise ValueError("amount must be positive")

        network = _network_for_swap(self.db)
        provider = resolve_provider(self.db, provider_id)
        try:
            quote = provider.quote(
                self.db,
                from_asset=from_asset,
                to_asset=to_asset,
                amount_atomic=amount_atomic,
                network=network,
                user_id=user_id,
            )
        except SwapProviderError as exc:
            raise ValueError(str(exc)) from exc

        _cache_quote(quote)
        return quote

    def execute_swap(
        self,
        user_id: int,
        *,
        quote_id: str,
        destination_wallet_id: int,
    ) -> dict:
        quote = get_cached_quote(quote_id)
        if not quote:
            raise ValueError("Quote not found or expired — request a new quote")
        if _quote_expired(quote):
            _quote_cache.pop(quote_id, None)
            raise ValueError("Quote expired — request a new quote")

        ensure_no_legacy_wallets(self.db, user_id)

        network = _network_for_swap(self.db)
        if network == "mainnet":
            ensure_mainnet_ready(self.db, user_id, "mainnet")

        wallet = self.db.get_wallet(destination_wallet_id, user_id)
        if not wallet:
            raise ValueError("Destination wallet not found")
        if wallet.get("asset_type") != quote.to_asset:
            raise ValueError(
                f"Destination wallet must be a {quote.to_asset.upper()} wallet"
            )

        from_network = self._network_for_asset(user_id, quote.from_asset)
        to_network = str(wallet.get("network") or self._network_for_asset(user_id, quote.to_asset))
        if quote.to_asset == "xmr" and to_network == "mainnet":
            ensure_mainnet_ready(self.db, user_id, "mainnet")
        if quote.from_asset == "xmr" and from_network == "mainnet":
            ensure_mainnet_ready(self.db, user_id, "mainnet")

        status = "awaiting_deposit"
        deposit_address = quote.extra.get("deposit_address") if quote.extra else None
        deposit_amount = quote.send_amount_atomic
        instructions = None

        if quote.provider_id == "rate_table":
            status = "awaiting_user_send"
            deposit_amount = None
            instructions = (
                f"Send {quote.send_amount_atomic} atomic units of {quote.from_asset.upper()} "
                f"from your {quote.from_asset.upper()} wallet using Send. "
                f"Expected receive: {quote.receive_amount_atomic} atomic units of "
                f"{quote.to_asset.upper()} to wallet #{destination_wallet_id}. "
                f"After sending, attach the transaction ID in Swap history."
            )

        deposit_checksum_valid = None
        if deposit_address:
            deposit_checksum_valid = validate_deposit_address(quote.from_asset, deposit_address)
            if not deposit_checksum_valid:
                raise ValueError("Provider returned a deposit address with invalid checksum")

        swap_id = self.db.create_swap(
            user_id,
            quote_id=quote.quote_id,
            provider_id=quote.provider_id,
            from_asset=quote.from_asset,
            to_asset=quote.to_asset,
            send_amount_atomic=quote.send_amount_atomic,
            receive_amount_atomic=quote.receive_amount_atomic,
            status=status,
            destination_wallet_id=destination_wallet_id,
            deposit_address=deposit_address,
            deposit_amount_atomic=deposit_amount,
            expires_at=quote.expires_at,
            raw_json=json.dumps(quote.to_dict())[:8000],
            from_network=from_network,
            to_network=to_network,
        )

        _quote_cache.pop(quote_id, None)

        row = self.db.get_swap(swap_id, user_id) or {}
        result = self._public_swap(row, include_deposit=True)
        result.update(
            {
                "swap_id": swap_id,
                "status": status,
                "from_asset": quote.from_asset,
                "to_asset": quote.to_asset,
                "send_amount_atomic": quote.send_amount_atomic,
                "receive_amount_atomic": quote.receive_amount_atomic,
                "deposit_address": deposit_address,
                "deposit_amount_atomic": deposit_amount,
                "destination_wallet_id": destination_wallet_id,
                "provider": quote.provider_id,
                "expires_at": quote.expires_at,
                "deposit_address_checksum_valid": deposit_checksum_valid,
            }
        )
        if instructions:
            result["instructions"] = instructions
        return result

    def list_swaps(self, user_id: int, limit: int = 50) -> list[dict]:
        return [
            self._public_swap(row) for row in self.db.list_swaps(user_id, limit=limit)
        ]

    def get_swap(self, swap_id: int, user_id: int) -> dict:
        row = self.db.get_swap(swap_id, user_id)
        if not row:
            raise ValueError("Swap not found")
        return self._public_swap(row)

    def attach_txids(
        self,
        swap_id: int,
        user_id: int,
        *,
        from_txid: Optional[str] = None,
        to_txid: Optional[str] = None,
    ) -> dict:
        row = self.db.get_swap(swap_id, user_id)
        if not row:
            raise ValueError("Swap not found")

        if from_txid is not None and from_txid.strip() and not _valid_txid(from_txid):
            raise ValueError("Invalid from_txid — expected 64-character hex hash")
        if to_txid is not None and to_txid.strip() and not _valid_txid(to_txid):
            raise ValueError("Invalid to_txid — expected 64-character hex hash")

        new_status = None
        has_from = bool((from_txid or "").strip() or row.get("from_txid"))
        has_to = bool((to_txid or "").strip() or row.get("to_txid"))
        if has_from and has_to:
            new_status = "completed"
        elif has_from and row.get("status") == "awaiting_user_send":
            new_status = "processing"

        updated = self.db.update_swap_txids(
            swap_id,
            user_id,
            from_txid=from_txid,
            to_txid=to_txid,
            status=new_status,
        )
        if not updated:
            raise ValueError("Swap not found")
        if new_status == "completed":
            self.db.update_swap_status(
                swap_id,
                user_id,
                "completed",
                settled_at=datetime.now(timezone.utc).isoformat(),
            )
            updated = self.db.get_swap(swap_id, user_id) or updated
        return self._public_swap(updated)
