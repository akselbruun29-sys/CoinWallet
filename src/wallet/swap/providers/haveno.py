"""Haveno P2P swap provider (requires external Haveno API)."""
from __future__ import annotations

import os
from typing import Optional

from src.database import WalletDatabase
from src.wallet.swap.base import SwapProvider, SwapProviderError
from src.wallet.swap.types import ProviderInfo, SwapQuote


class HavenoProvider(SwapProvider):
    PROVIDER_ID = "haveno"

    def info(self, db: WalletDatabase) -> ProviderInfo:
        enabled = bool(self._api_url(db))
        return ProviderInfo(
            id=self.PROVIDER_ID,
            name="Haveno P2P",
            type="atomic",
            custodial=False,
            enabled=enabled,
            disclosure=(
                "Non-custodial atomic swaps via Haveno. Requires a running Haveno daemon "
                "or public API endpoint configured by the operator."
            ),
        )

    def _api_url(self, db: WalletDatabase) -> str:
        return (
            os.getenv("HAVENO_API_URL", "").strip()
            or (db.get_setting("haveno_api_url") or "").strip()
        )

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
        if not self._api_url(db):
            raise SwapProviderError(
                "Haveno is not configured. Set HAVENO_API_URL or haveno_api_url in settings."
            )
        raise SwapProviderError(
            "Haveno quote integration is not wired yet — use rate_table on testnet/stagenet."
        )
