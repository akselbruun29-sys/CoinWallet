"""Documented rate-table swap quotes for testnet/stagenet development."""
from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from src.database import WalletDatabase
from src.wallet.swap.base import SwapProvider, SwapProviderError
from src.wallet.swap.types import ProviderInfo, SwapFees, SwapQuote

BTC_ATOMIC = 100_000_000
XMR_ATOMIC = 1_000_000_000_000
QUOTE_TTL_SECONDS = 300

DEFAULT_BTC_TO_XMR = 0.15
DEFAULT_PROVIDER_FEE_BPS = 30
DEFAULT_BTC_NETWORK_FEE = 2_500
DEFAULT_XMR_NETWORK_FEE = 500_000_000


def _env_float(key: str, default: float) -> float:
    raw = os.getenv(key, "").strip()
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _env_int(key: str, default: int) -> int:
    raw = os.getenv(key, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _rate_btc_to_xmr(db: WalletDatabase) -> float:
    custom = (db.get_setting("swap_rate_btc_to_xmr") or "").strip()
    if custom:
        try:
            return float(custom)
        except ValueError:
            pass
    return _env_float("SWAP_RATE_BTC_TO_XMR", DEFAULT_BTC_TO_XMR)


def _rate_xmr_to_btc(db: WalletDatabase) -> float:
    custom = (db.get_setting("swap_rate_xmr_to_btc") or "").strip()
    if custom:
        try:
            return float(custom)
        except ValueError:
            pass
    inverse = _rate_btc_to_xmr(db)
    if inverse <= 0:
        return 1.0 / DEFAULT_BTC_TO_XMR
    return 1.0 / inverse


class RateTableProvider(SwapProvider):
    PROVIDER_ID = "rate_table"

    def info(self, db: WalletDatabase) -> ProviderInfo:
        enabled = self._enabled(db)
        return ProviderInfo(
            id=self.PROVIDER_ID,
            name="Documented rate table (dev/test)",
            type="documented",
            custodial=False,
            enabled=enabled,
            disclosure=(
                "Quotes use configurable reference rates for testnet/stagenet only. "
                "No external liquidity provider is contacted. For production, prefer "
                "Haveno P2P or a disclosed custodial API with explicit user consent."
            ),
        )

    def _enabled(self, db: WalletDatabase) -> bool:
        if os.getenv("SWAP_RATE_TABLE_ENABLED", "").lower() == "true":
            return True
        if os.getenv("SWAP_RATE_TABLE_ENABLED", "").lower() == "false":
            return False
        network = (db.get_setting("network") or "testnet").strip().lower()
        return network not in ("mainnet",)

    def quote(
        self,
        db: WalletDatabase,
        *,
        from_asset: str,
        to_asset: str,
        amount_atomic: int,
        network: str,
        user_id: Optional[int] = None,
    ) -> SwapQuote:
        if not self._enabled(db):
            raise SwapProviderError(
                "Rate table provider is disabled on mainnet. Choose Haveno or a disclosed API."
            )
        if network == "mainnet":
            raise SwapProviderError("Rate table quotes are not available on mainnet.")

        pair = (from_asset, to_asset)
        if pair == ("btc", "xmr"):
            rate = _rate_btc_to_xmr(db)
            min_send = _env_int("SWAP_MIN_BTC_SATS", 10_000)
            max_send = _env_int("SWAP_MAX_BTC_SATS", 100_000_000)
            network_fee = _env_int("SWAP_BTC_NETWORK_FEE_SATS", DEFAULT_BTC_NETWORK_FEE)
            gross_receive = int((amount_atomic / BTC_ATOMIC) * rate * XMR_ATOMIC)
        elif pair == ("xmr", "btc"):
            rate = _rate_xmr_to_btc(db)
            min_send = _env_int("SWAP_MIN_XMR_ATOMIC", XMR_ATOMIC // 100_000)
            max_send = _env_int("SWAP_MAX_XMR_ATOMIC", XMR_ATOMIC)
            network_fee = _env_int("SWAP_XMR_NETWORK_FEE_ATOMIC", DEFAULT_XMR_NETWORK_FEE)
            gross_receive = int((amount_atomic / XMR_ATOMIC) * rate * BTC_ATOMIC)
        else:
            raise SwapProviderError(f"Unsupported pair: {from_asset} → {to_asset}")

        if amount_atomic < min_send:
            raise SwapProviderError(f"Amount below minimum ({min_send} atomic units)")
        if amount_atomic > max_send:
            raise SwapProviderError(f"Amount above maximum ({max_send} atomic units)")

        fee_bps = _env_int("SWAP_PROVIDER_FEE_BPS", DEFAULT_PROVIDER_FEE_BPS)
        provider_fee = (gross_receive * fee_bps) // 10_000
        receive_amount = max(0, gross_receive - provider_fee)

        expires = datetime.now(timezone.utc) + timedelta(seconds=QUOTE_TTL_SECONDS)
        return SwapQuote(
            quote_id=str(uuid.uuid4()),
            provider_id=self.PROVIDER_ID,
            from_asset=from_asset,
            to_asset=to_asset,
            send_amount_atomic=amount_atomic,
            receive_amount_atomic=receive_amount,
            rate=rate,
            fees=SwapFees(network=network_fee, provider=provider_fee),
            min_send_atomic=min_send,
            max_send_atomic=max_send,
            expires_at=expires.isoformat(),
            disclosure=self.info(db).disclosure,
            network=network,
        )
