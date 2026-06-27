"""Ensure wallet API responses never leak encrypted_seed."""
from __future__ import annotations

from src.database import WalletDatabase

SECRET_FIELD = "encrypted_seed"
FAKE_SEED = "cwenc1:pytest-secret-ciphertext-should-never-leak"


def _auth_headers(client) -> dict[str, str]:
    res = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "testpassword123"},
    )
    assert res.status_code == 200, res.text
    token = res.json()["token"]
    return {"Authorization": f"Bearer {token}"}


def _seed_wallet_with_secret(db_path: str) -> int:
    db = WalletDatabase(db_path)
    admin = db.get_user_by_username("admin")
    assert admin is not None
    return db.create_wallet(
        admin["id"],
        name="pytest-secret-wallet",
        network="testnet",
        xpub="tpubpytest000000000000000000000000000000000000000000000000000000",
        encrypted_seed=FAKE_SEED,
        encryption_version=2,
    )


def test_list_wallets_never_returns_encrypted_seed(client):
    test_client, db_path = client
    wallet_id = _seed_wallet_with_secret(db_path)
    headers = _auth_headers(test_client)

    res = test_client.get("/api/wallets", headers=headers)
    assert res.status_code == 200
    wallets = res.json()
    assert len(wallets) >= 1
    match = next(w for w in wallets if w["id"] == wallet_id)
    assert SECRET_FIELD not in match
    assert all(SECRET_FIELD not in w for w in wallets)


def test_get_wallet_never_returns_encrypted_seed(client):
    test_client, db_path = client
    wallet_id = _seed_wallet_with_secret(db_path)
    headers = _auth_headers(test_client)

    res = test_client.get(f"/api/wallets/{wallet_id}", headers=headers)
    assert res.status_code == 200
    wallet = res.json()
    assert wallet["id"] == wallet_id
    assert SECRET_FIELD not in wallet

    db = WalletDatabase(db_path)
    internal = db.get_wallet_with_secrets(wallet_id, db.get_user_by_username("admin")["id"])
    assert internal is not None
    assert internal.get(SECRET_FIELD) == FAKE_SEED
