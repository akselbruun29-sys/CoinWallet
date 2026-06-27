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
from src.wallet.mainnet_gate import ensure_mainnet_ready, ensure_no_legacy_wallets, ensure_wallet_mainnet_ready
from src.wallet.vault import get_unlocked_dek
from src.wallet.xmr.keys import (
    DEFAULT_XMR_NETWORK,
    XMR_NETWORKS,
    generate_xmr_wallet_keys,
    import_xmr_wallet_keys,
)
from src.wallet.xmr.ops import XmrOpsEngine
from src.wallet.xmr.sync import XmrSyncEngine


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
        ensure_mainnet_ready(self.db, user_id, network)
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
            asset_type="btc",
        )
        return wallet_id, keys.mnemonic

    def import_wallet_with_mnemonic(
        self, user_id: int, name: str, mnemonic: str, network: str = "testnet"
    ) -> int:
        self._ensure_network_allowed(network)
        ensure_mainnet_ready(self.db, user_id, network)
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
            asset_type="btc",
        )

    def create_xmr_wallet_with_keys(
        self, user_id: int, name: str, network: str = DEFAULT_XMR_NETWORK
    ) -> tuple[int, str]:
        if network not in XMR_NETWORKS:
            raise ValueError(f"Unsupported XMR network: {network}")
        if network == "mainnet":
            ensure_mainnet_ready(self.db, user_id, "mainnet")
        dek = get_unlocked_dek(user_id)
        if dek is None:
            raise ValueError("Wallet locked — set up and unlock your wallet passphrase first")

        keys = generate_xmr_wallet_keys(network, dek)
        wallet_id = self.db.create_wallet(
            user_id,
            name,
            network=network,
            encrypted_seed=keys.encrypted_seed,
            encryption_version=2,
            asset_type="xmr",
            xmr_primary_address=keys.primary_address,
            xmr_encrypted_view_key=keys.encrypted_view_key,
            xmr_account_index=keys.account_index,
        )
        return wallet_id, keys.mnemonic

    def import_xmr_wallet_with_mnemonic(
        self, user_id: int, name: str, mnemonic: str, network: str = DEFAULT_XMR_NETWORK
    ) -> int:
        if network not in XMR_NETWORKS:
            raise ValueError(f"Unsupported XMR network: {network}")
        if network == "mainnet":
            ensure_mainnet_ready(self.db, user_id, "mainnet")
        dek = get_unlocked_dek(user_id)
        if dek is None:
            raise ValueError("Wallet locked — set up and unlock your wallet passphrase first")

        keys = import_xmr_wallet_keys(mnemonic, network, dek)
        return self.db.create_wallet(
            user_id,
            name,
            network=network,
            encrypted_seed=keys.encrypted_seed,
            encryption_version=2,
            asset_type="xmr",
            xmr_primary_address=keys.primary_address,
            xmr_encrypted_view_key=keys.encrypted_view_key,
            xmr_account_index=keys.account_index,
        )

    def _xmr_engine(self) -> XmrSyncEngine:
        return XmrSyncEngine(self.db)

    def _xmr_ops(self) -> XmrOpsEngine:
        return XmrOpsEngine(self.db)

    def _is_xmr_wallet(self, wallet_id: int, user_id: int) -> bool:
        wallet = self.db.get_wallet(wallet_id, user_id)
        return bool(wallet and wallet.get("asset_type") == "xmr")

    def sync(self, wallet_id: int, user_id: int) -> dict:
        if self._is_xmr_wallet(wallet_id, user_id):
            return self._xmr_engine().sync_wallet(wallet_id, user_id)
        return self.engine.sync_wallet(wallet_id, user_id)

    def get_sync_status(self, wallet_id: int, user_id: int) -> dict:
        if self._is_xmr_wallet(wallet_id, user_id):
            return self._xmr_engine().get_sync_status(wallet_id, user_id)
        return self.engine.get_sync_status(wallet_id, user_id)

    def get_balance(self, wallet_id: int, user_id: int) -> dict:
        if self._is_xmr_wallet(wallet_id, user_id):
            return self._xmr_engine().get_balance(wallet_id, user_id)
        return self.engine.get_balance(wallet_id, user_id)

    def get_utxos(self, wallet_id: int, user_id: int) -> list:
        return self.engine.get_utxos(wallet_id, user_id)

    def get_transactions(self, wallet_id: int, user_id: int, limit: int = 50) -> list:
        return self.engine.get_transactions(wallet_id, user_id, limit=limit)

    def get_receive_address(
        self, wallet_id: int, user_id: int, *, subaddress: bool = True
    ) -> dict:
        ensure_no_legacy_wallets(self.db, user_id)
        if self._is_xmr_wallet(wallet_id, user_id):
            return self._xmr_ops().get_receive_address(
                wallet_id, user_id, subaddress=subaddress
            )
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
        ensure_no_legacy_wallets(self.db, user_id)
        if self._is_xmr_wallet(wallet_id, user_id):
            priority = 1
            if fee_rate_sat_vb is not None and fee_rate_sat_vb >= 3:
                priority = 2
            return self._xmr_ops().preview_send(
                wallet_id, user_id, address, amount_sats, priority=priority
            )
        ensure_wallet_mainnet_ready(self.db, user_id, wallet_id)
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
        ensure_no_legacy_wallets(self.db, user_id)
        if self._is_xmr_wallet(wallet_id, user_id):
            priority = 1
            if fee_rate_sat_vb is not None and fee_rate_sat_vb >= 3:
                priority = 2
            return self._xmr_ops().send(
                wallet_id, user_id, address, amount_sats, priority=priority
            )
        ensure_wallet_mainnet_ready(self.db, user_id, wallet_id)
        return self.engine.send(
            wallet_id, user_id, address, amount_sats, fee_rate_sat_vb, utxo_refs
        )

    def any_wallet_synced(self, user_id: int) -> bool:
        for w in self.db.list_wallets(user_id):
            if w.get("last_synced_height", 0) > 0:
                return True
        return False
