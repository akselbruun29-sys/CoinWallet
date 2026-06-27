"""Leaderboard display-name validation and balance update guards."""
from __future__ import annotations

import pytest

from api.leaderboard import validate_display_name
from src.database import WalletDatabase


def _auth_headers(test_client) -> dict[str, str]:
    res = test_client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "testpassword123"},
    )
    assert res.status_code == 200, res.text
    return {"Authorization": f"Bearer {res.json()['token']}"}


@pytest.mark.parametrize(
    "name",
    ["Alice", "bob_42", "Sat Stacker", "a1", "Valid-Name"],
)
def test_validate_display_name_accepts_valid_names(name: str):
    assert validate_display_name(name) == name.strip()


@pytest.mark.parametrize(
    "name",
    ["", "x", "bad@name", "name!", "a" * 33],
)
def test_validate_display_name_rejects_invalid_names(name: str):
    with pytest.raises(ValueError, match="Display name must be"):
        validate_display_name(name)


@pytest.mark.parametrize(
    "name",
    ["admin", "CoinWallet", "OfficialSupport", "moderator_bot"],
)
def test_validate_display_name_rejects_reserved_names(name: str):
    with pytest.raises(ValueError, match="impersonate"):
        validate_display_name(name)


def test_opt_in_rejects_invalid_display_name(client):
    test_client, _ = client
    headers = _auth_headers(test_client)

    res = test_client.post(
        "/api/leaderboard/opt-in",
        json={"display_name": "admin", "opted_in": True, "network": "testnet"},
        headers=headers,
    )
    assert res.status_code == 400
    assert "impersonate" in res.json()["detail"]


def test_opt_in_accepts_valid_display_name(client):
    test_client, _ = client
    headers = _auth_headers(test_client)

    res = test_client.post(
        "/api/leaderboard/opt-in",
        json={"display_name": "Stacker One", "opted_in": True, "network": "testnet"},
        headers=headers,
    )
    assert res.status_code == 200
    body = res.json()
    assert body["opted_in"] is True
    assert body["display_name"] == "Stacker One"


def test_update_requires_opt_in(client):
    test_client, _ = client
    headers = _auth_headers(test_client)

    res = test_client.post(
        "/api/leaderboard/update",
        json={"balance_sats": 0, "network": "testnet"},
        headers=headers,
    )
    assert res.status_code == 400
    assert "opt-in" in res.json()["detail"].lower()


def test_update_rejects_balance_mismatch(client):
    test_client, db_path = client
    headers = _auth_headers(test_client)

    opt_in = test_client.post(
        "/api/leaderboard/opt-in",
        json={"display_name": "Balance Test", "opted_in": True, "network": "testnet"},
        headers=headers,
    )
    assert opt_in.status_code == 200

    res = test_client.post(
        "/api/leaderboard/update",
        json={"balance_sats": 1_000_000, "network": "testnet"},
        headers=headers,
    )
    assert res.status_code == 400
    assert "does not match" in res.json()["detail"]


def test_update_rejects_impossible_balance_jump(client, monkeypatch):
    test_client, db_path = client
    headers = _auth_headers(test_client)
    db = WalletDatabase(db_path)
    admin = db.get_user_by_username("admin")
    assert admin is not None

    db.set_leaderboard_opt_in(
        admin["id"],
        "testnet",
        "Jump Test",
        True,
        balance_sats=50_000,
        remote_token="pytest-token",
    )

    import api.leaderboard as lb_module

    monkeypatch.setattr(
        WalletDatabase,
        "user_total_balance_sats",
        lambda self, user_id, network: 500_000,
    )
    lb_module._last_balance_update.clear()

    res = test_client.post(
        "/api/leaderboard/update",
        json={"balance_sats": 500_000, "network": "testnet"},
        headers=headers,
    )
    assert res.status_code == 400
    assert "Impossible balance increase" in res.json()["detail"]
