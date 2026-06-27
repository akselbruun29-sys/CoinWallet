"""Swap execute rejects missing and expired quotes."""
from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone

import pytest

from src.database import WalletDatabase
from src.wallet.swap.service import SwapService, get_cached_quote
from src.wallet.swap.types import SwapFees, SwapQuote


def _auth_headers(test_client) -> dict[str, str]:
    res = test_client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "testpassword123"},
    )
    assert res.status_code == 200, res.text
    return {"Authorization": f"Bearer {res.json()['token']}"}


def _unlock_wallet(test_client, headers: dict[str, str]) -> None:
    res = test_client.post(
        "/api/security/wallet/passphrase/setup",
        json={"passphrase": "testpassphrase123"},
        headers=headers,
    )
    assert res.status_code == 200, res.text


def _seed_xmr_wallet(db_path: str) -> int:
    db = WalletDatabase(db_path)
    admin = db.get_user_by_username("admin")
    assert admin is not None
    return db.create_wallet(
        admin["id"],
        "xmr-dest",
        network="stagenet",
        encrypted_seed="cwenc1:pytest-xmr",
        encryption_version=2,
        asset_type="xmr",
        xmr_primary_address="4" + "A" * 94,
    )


def _make_quote(*, quote_id: str, expires_at: str) -> SwapQuote:
    return SwapQuote(
        quote_id=quote_id,
        provider_id="rate_table",
        from_asset="btc",
        to_asset="xmr",
        send_amount_atomic=100_000,
        receive_amount_atomic=15_000_000_000_000,
        rate=0.15,
        fees=SwapFees(network=500, provider=300),
        min_send_atomic=10_000,
        max_send_atomic=10_000_000_000,
        expires_at=expires_at,
        disclosure="pytest",
        network="testnet",
    )


def test_execute_swap_rejects_missing_quote(client):
    _, db_path = client
    db = WalletDatabase(db_path)
    admin = db.get_user_by_username("admin")
    assert admin is not None
    dest_id = _seed_xmr_wallet(db_path)

    service = SwapService(db)
    with pytest.raises(ValueError, match="Quote not found or expired"):
        service.execute_swap(
            admin["id"],
            quote_id="missing-quote-id",
            destination_wallet_id=dest_id,
        )


def test_execute_swap_rejects_expired_cached_quote(client):
    _, db_path = client
    db = WalletDatabase(db_path)
    admin = db.get_user_by_username("admin")
    assert admin is not None
    dest_id = _seed_xmr_wallet(db_path)

    import src.wallet.swap.service as swap_module

    quote = _make_quote(
        quote_id="expired-quote",
        expires_at=(datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat(),
    )
    swap_module._cache_quote(quote)
    assert get_cached_quote(quote.quote_id) is None

    service = SwapService(db)
    with pytest.raises(ValueError, match="Quote not found or expired"):
        service.execute_swap(
            admin["id"],
            quote_id=quote.quote_id,
            destination_wallet_id=dest_id,
        )


def test_execute_swap_rejects_stale_quote_after_expiry(client):
    _, db_path = client
    db = WalletDatabase(db_path)
    admin = db.get_user_by_username("admin")
    assert admin is not None
    dest_id = _seed_xmr_wallet(db_path)

    import src.wallet.swap.service as swap_module

    quote = _make_quote(
        quote_id="stale-quote",
        expires_at=(datetime.now(timezone.utc) - timedelta(seconds=30)).isoformat(),
    )
    swap_module._quote_cache[quote.quote_id] = (time.time() + 3600, quote)

    service = SwapService(db)
    with pytest.raises(ValueError, match="Quote expired"):
        service.execute_swap(
            admin["id"],
            quote_id=quote.quote_id,
            destination_wallet_id=dest_id,
        )


def test_swap_execute_api_rejects_expired_quote(client):
    test_client, db_path = client
    headers = _auth_headers(test_client)
    _unlock_wallet(test_client, headers)
    dest_id = _seed_xmr_wallet(db_path)

    import src.wallet.swap.service as swap_module

    quote = _make_quote(
        quote_id="api-expired-quote",
        expires_at=(datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat(),
    )
    swap_module._quote_cache[quote.quote_id] = (time.time() + 3600, quote)

    res = test_client.post(
        "/api/swap/execute",
        json={"quote_id": quote.quote_id, "destination_wallet_id": dest_id},
        headers=headers,
    )
    assert res.status_code == 400
    assert "expired" in res.json()["detail"].lower()
