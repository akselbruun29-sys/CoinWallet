"""Registered swap providers."""
from __future__ import annotations

import os

from src.database import WalletDatabase
from src.wallet.swap.base import SwapProvider, SwapProviderError
from src.wallet.swap.providers.haveno import HavenoProvider
from src.wallet.swap.providers.rate_table import RateTableProvider

_PROVIDERS: dict[str, SwapProvider] = {
    RateTableProvider.PROVIDER_ID: RateTableProvider(),
    HavenoProvider.PROVIDER_ID: HavenoProvider(),
}

DEFAULT_PROVIDER_ID = RateTableProvider.PROVIDER_ID


def _provider_allowlist() -> frozenset[str] | None:
    raw = os.getenv("SWAP_PROVIDER_ALLOWLIST", "").strip()
    if not raw:
        return None
    return frozenset(part.strip() for part in raw.split(",") if part.strip())


def _is_provider_allowed(provider_id: str) -> bool:
    if provider_id not in _PROVIDERS:
        return False
    allowlist = _provider_allowlist()
    if allowlist is None:
        return True
    return provider_id in allowlist


def list_providers(db: WalletDatabase) -> list[dict]:
    return [
        p.info(db).to_dict()
        for pid, p in _PROVIDERS.items()
        if _is_provider_allowed(pid)
    ]


def get_provider(provider_id: str) -> SwapProvider:
    if not _is_provider_allowed(provider_id):
        raise SwapProviderError(f"Swap provider not allowed: {provider_id}")
    provider = _PROVIDERS.get(provider_id)
    if not provider:
        raise SwapProviderError(f"Unknown swap provider: {provider_id}")
    return provider


def resolve_provider(db: WalletDatabase, provider_id: str | None) -> SwapProvider:
    if provider_id:
        return get_provider(provider_id)
    for candidate in (DEFAULT_PROVIDER_ID, HavenoProvider.PROVIDER_ID):
        if not _is_provider_allowed(candidate):
            continue
        info = get_provider(candidate).info(db)
        if info.enabled:
            return get_provider(candidate)
    raise SwapProviderError("No swap providers are enabled")
