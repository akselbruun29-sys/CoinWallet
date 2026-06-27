"""Deposit and payout address validation with checksum checks."""
from __future__ import annotations


def validate_btc_address(address: str) -> bool:
    addr = address.strip()
    if not addr or len(addr) < 14:
        return False
    try:
        from embit.script import address_to_scriptpubkey

        address_to_scriptpubkey(addr)
        return True
    except Exception:
        return False


def validate_xmr_address(address: str) -> bool:
    addr = address.strip()
    if not addr:
        return False
    try:
        from monero.address import address as xmr_address

        xmr_address(addr)
        return True
    except Exception:
        return False


def validate_deposit_address(asset: str, address: str) -> bool:
    asset = asset.strip().lower()
    if asset == "btc":
        return validate_btc_address(address)
    if asset == "xmr":
        return validate_xmr_address(address)
    return False
