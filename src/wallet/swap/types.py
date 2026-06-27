"""Swap quote types."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class ProviderInfo:
    id: str
    name: str
    type: str  # atomic | documented | api
    custodial: bool
    disclosure: str
    enabled: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SwapFees:
    network: int
    provider: int

    def to_dict(self) -> dict[str, int]:
        return {"network": self.network, "provider": self.provider}


@dataclass
class SwapQuote:
    quote_id: str
    provider_id: str
    from_asset: str
    to_asset: str
    send_amount_atomic: int
    receive_amount_atomic: int
    rate: float
    fees: SwapFees
    min_send_atomic: int
    max_send_atomic: int
    expires_at: str
    disclosure: str
    network: str = "testnet"
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "quote_id": self.quote_id,
            "provider": self.provider_id,
            "from_asset": self.from_asset,
            "to_asset": self.to_asset,
            "send_amount_atomic": self.send_amount_atomic,
            "receive_amount_atomic": self.receive_amount_atomic,
            "amount_sats": self.send_amount_atomic,
            "rate": self.rate,
            "fees": self.fees.to_dict(),
            "min": self.min_send_atomic,
            "max": self.max_send_atomic,
            "expires_at": self.expires_at,
            "disclosure": self.disclosure,
            "network": self.network,
            **self.extra,
        }
