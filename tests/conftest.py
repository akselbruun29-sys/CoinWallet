"""Shared pytest fixtures for API tests."""
from __future__ import annotations

import importlib
from collections import defaultdict
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path, monkeypatch) -> Generator[tuple[TestClient, str], None, None]:
    db_path = tmp_path / "test_wallet.db"
    monkeypatch.setenv("WALLET_DB", str(db_path))
    monkeypatch.setenv("STRICT_SECRETS", "false")
    monkeypatch.setenv("COINWALLET_PRODUCTION", "false")
    monkeypatch.setenv("SESSION_SECRET", "pytest-session-secret-key-32chars")
    monkeypatch.setenv("WALLET_ENCRYPTION_KEY", "pytest-wallet-encryption-key-long-enough")
    monkeypatch.setenv("ADMIN_USERNAME", "admin")
    monkeypatch.setenv("ADMIN_PASSWORD", "testpassword123")
    monkeypatch.setenv("ADMIN_PASSWORD_HASH", "")
    monkeypatch.setattr("dotenv.load_dotenv", lambda *args, **kwargs: None)

    import api.main as main_module
    import api.rate_limit as rate_limit_module

    importlib.reload(main_module)
    rate_limit_module._attempts = defaultdict(list)

    yield TestClient(main_module.app, base_url="http://127.0.0.1"), str(db_path)
