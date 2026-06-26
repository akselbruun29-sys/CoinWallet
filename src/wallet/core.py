"""Wallet orchestration service."""
from __future__ import annotations

from typing import Optional

from src.database import WalletDatabase
from src.wallet.bdk_wallet import WalletEngine
from src.wallet.keys import (
    account_xpub_from_mnemonic,
    derivation_path_for_network,
    encrypt_mnemonic_with_dek,
    generate_wallet_keys,
)
from src.wallet.vault import get_unlocked_dek


class WalletService:
    def __init__(self, db: Optional[WalletDatabase] = None):
        self.db = db or WalletDatabase()
        self.engine = WalletEngine(self.db)

    def _mainnet_allowed(self) -> bool:
        import os

        if os.getenv("ALLOW_MAINNET", "").lower() in ("true", "1", "yes"):
            return True
        return self.db.get_setting("allow_mainnet", "false").lower() == "true"

    def _ensure_network_allowed(self, network: str) -> None:
        if network == "mainnet" and not self._mainnet_allowed():
            raise ValueError(
                "Mainnet wallets are disabled. Set ALLOW_MAINNET=true in .env to enable."
            )

    def create_wallet_with_keys(self, user_id: int, name: str, network: str = "testnet") -> tuple[int, str]:
        self._ensure_network_allowed(network)
        dek = get_unlocked_dek(user_id)
        if dek is None:
            raise ValueError("Wallet locked — set up and unlock your wallet passphrase first")

        keys = generate_wallet_keys(network, dek=dek)
        wallet_id = self.db.create_wallet(
            user_id,
            name,
            network=network,
            xpub=keys.xpub,
            encrypted_seed=keys.encrypted_seed,
            derivation_path=keys.derivation_path,
            encryption_version=2,
        )
        return wallet_id, keys.mnemonic

    def import_wallet_with_mnemonic(
        self, user_id: int, name: str, mnemonic: str, network: str = "testnet"
    ) -> int:
        self._ensure_network_allowed(network)
        from mnemonic import Mnemonic

        phrase = " ".join(mnemonic.strip().lower().split())
        if not Mnemonic("english").check(phrase):
            raise ValueError("Invalid mnemonic phrase")

        if network not in ("testnet", "signet", "regtest", "mainnet"):
            raise ValueError(f"Unsupported network: {network}")

        dek = get_unlocked_dek(user_id)
        if dek is None:
            raise ValueError("Wallet locked — set up and unlock your wallet passphrase first")

        return self.db.create_wallet(
            user_id,
            name,
            network=network,
            xpub=account_xpub_from_mnemonic(phrase, network),
            encrypted_seed=encrypt_mnemonic_with_dek(phrase, dek),
            derivation_path=derivation_path_for_network(network),
            encryption_version=2,
        )

    def sync(self, wallet_id: int, user_id: int) -> dict:
        return self.engine.sync_wallet(wallet_id, user_id)

    def get_sync_status(self, wallet_id: int, user_id: int) -> dict:
        return self.engine.get_sync_status(wallet_id, user_id)

    def get_balance(self, wallet_id: int, user_id: int) -> dict:
        return self.engine.get_balance(wallet_id, user_id)

    def get_utxos(self, wallet_id: int, user_id: int) -> list:
        return self.engine.get_utxos(wallet_id, user_id)

    def get_transactions(self, wallet_id: int, user_id: int, limit: int = 50) -> list:
        return self.engine.get_transactions(wallet_id, user_id, limit=limit)

    def get_receive_address(self, wallet_id: int, user_id: int) -> dict:
        return self.engine.get_receive_address(wallet_id, user_id)

    def get_stats(self, wallet_id: int, user_id: int) -> dict:
        return self.engine.get_stats(wallet_id, user_id)

    def get_privacy_summary(self, wallet_id: int, user_id: int) -> dict:
        return self.engine.get_privacy_summary(wallet_id, user_id)

    def preview_send(
        self,
        wallet_id: int,
        user_id: int,
        address: str,
        amount_sats: int,
        fee_rate_sat_vb: Optional[int] = None,
        utxo_refs: Optional[list[dict]] = None,
    ) -> dict:
        return self.engine.preview_send(
            wallet_id, user_id, address, amount_sats, fee_rate_sat_vb, utxo_refs
        )

    def send(
        self,
        wallet_id: int,
        user_id: int,
        address: str,
        amount_sats: int,
        fee_rate_sat_vb: Optional[int] = None,
        utxo_refs: Optional[list[dict]] = None,
    ) -> dict:
        return self.engine.send(
            wallet_id, user_id, address, amount_sats, fee_rate_sat_vb, utxo_refs
        )

    def any_wallet_synced(self, user_id: int) -> bool:
        for w in self.db.list_wallets(user_id):
            if w.get("last_synced_height", 0) > 0:
                return True
        return False
