"""Swap provider interface."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from src.database import WalletDatabase
from src.wallet.swap.types import ProviderInfo, SwapQuote


class SwapProviderError(Exception):
    pass


class SwapProvider(ABC):
    @abstractmethod
    def info(self, db: WalletDatabase) -> ProviderInfo:
        raise NotImplementedError

    @abstractmethod
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
        raise NotImplementedError
