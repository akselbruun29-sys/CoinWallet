"""Mainnet safety gates block send/swap without v2 encryption and user acknowledgment."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from src.database import WalletDatabase
from src.wallet.mainnet_gate import ensure_mainnet_ready, ensure_no_legacy_wallets
from src.wallet.swap.service import SwapService
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


def _seed_btc_wallet(
    db_path: str,
    *,
    network: str = "mainnet",
    encryption_version: int = 2,
) -> int:
    db = WalletDatabase(db_path)
    admin = db.get_user_by_username("admin")
    assert admin is not None
    db.set_setting("allow_mainnet", "true")
    return db.create_wallet(
        admin["id"],
        f"{network}-wallet",
        network=network,
        xpub="tpubpytest000000000000000000000000000000000000000000000000000000",
        encrypted_seed="cwenc1:pytest-seed",
        encryption_version=encryption_version,
        asset_type="btc",
    )


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


def test_ensure_mainnet_ready_ignores_testnet(client):
    _, db_path = client
    db = WalletDatabase(db_path)
    admin = db.get_user_by_username("admin")
    assert admin is not None
    ensure_mainnet_ready(db, admin["id"], "testnet")


def test_ensure_mainnet_ready_requires_admin_enable(client, monkeypatch):
    _, db_path = client
    db = WalletDatabase(db_path)
    admin = db.get_user_by_username("admin")
    assert admin is not None
    db.set_wallet_security(admin["id"], "salt", "verifier")
    monkeypatch.setattr(
        "src.wallet.mainnet_gate.get_unlocked_dek", lambda user_id: b"\x00" * 32
    )

    with pytest.raises(ValueError, match="Mainnet is disabled"):
        ensure_mainnet_ready(db, admin["id"], "mainnet")


def test_ensure_mainnet_ready_requires_user_ack(client, monkeypatch):
    _, db_path = client
    db = WalletDatabase(db_path)
    admin = db.get_user_by_username("admin")
    assert admin is not None
    db.set_setting("allow_mainnet", "true")
    db.set_wallet_security(admin["id"], "salt", "verifier")
    monkeypatch.setattr(
        "src.wallet.mainnet_gate.get_unlocked_dek", lambda user_id: b"\x00" * 32
    )

    with pytest.raises(ValueError, match="Acknowledge mainnet risks"):
        ensure_mainnet_ready(db, admin["id"], "mainnet")


def test_ensure_no_legacy_wallets_blocks_v1(client):
    _, db_path = client
    db = WalletDatabase(db_path)
    admin = db.get_user_by_username("admin")
    assert admin is not None
    db.create_wallet(
        admin["id"],
        "legacy",
        network="testnet",
        xpub="tpubpytest000000000000000000000000000000000000000000000000000000",
        encrypted_seed="legacy",
        encryption_version=1,
        asset_type="btc",
    )

    with pytest.raises(ValueError, match="Migrate .* legacy wallet"):
        ensure_no_legacy_wallets(db, admin["id"])


def test_send_preview_blocked_on_mainnet_without_ack(client):
    test_client, db_path = client
    headers = _auth_headers(test_client)
    _unlock_wallet(test_client, headers)
    wallet_id = _seed_btc_wallet(db_path, network="mainnet", encryption_version=2)

    res = test_client.post(
        f"/api/wallets/{wallet_id}/send/preview",
        json={
            "address": "bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf0ndq",
            "amount_sats": 1000,
        },
        headers=headers,
    )
    assert res.status_code == 400
    assert "Acknowledge mainnet risks" in res.json()["detail"]


def test_send_preview_blocked_with_legacy_wallet(client):
    test_client, db_path = client
    headers = _auth_headers(test_client)
    _unlock_wallet(test_client, headers)
    wallet_id = _seed_btc_wallet(db_path, network="testnet", encryption_version=1)

    res = test_client.post(
        f"/api/wallets/{wallet_id}/send/preview",
        json={
            "address": "tb1qar0srrr7xfkvy5l643lydnw9re59gtzzwf0ndq",
            "amount_sats": 1000,
        },
        headers=headers,
    )
    assert res.status_code == 400
    assert "legacy wallet" in res.json()["detail"].lower()


def test_swap_execute_blocked_on_mainnet_without_ack(client):
    test_client, db_path = client
    headers = _auth_headers(test_client)
    _unlock_wallet(test_client, headers)

    db = WalletDatabase(db_path)
    admin = db.get_user_by_username("admin")
    assert admin is not None
    db.set_setting("allow_mainnet", "true")
    db.set_setting("network", "mainnet")
    dest_id = _seed_xmr_wallet(db_path)

    import src.wallet.swap.service as swap_module

    quote = SwapQuote(
        quote_id="pytest-quote-mainnet-gate",
        provider_id="rate_table",
        from_asset="btc",
        to_asset="xmr",
        send_amount_atomic=100_000,
        receive_amount_atomic=15_000_000_000_000,
        rate=0.15,
        fees=SwapFees(network=500, provider=300),
        min_send_atomic=10_000,
        max_send_atomic=10_000_000_000,
        expires_at=(datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat(),
        disclosure="pytest",
        network="mainnet",
    )
    swap_module._cache_quote(quote)

    res = test_client.post(
        "/api/swap/execute",
        json={"quote_id": quote.quote_id, "destination_wallet_id": dest_id},
        headers=headers,
    )
    assert res.status_code == 400
    assert "Acknowledge mainnet risks" in res.json()["detail"]

    service = SwapService(db)
    with pytest.raises(ValueError, match="Acknowledge mainnet risks"):
        service.execute_swap(
            admin["id"],
            quote_id=quote.quote_id,
            destination_wallet_id=dest_id,
        )
