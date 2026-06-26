"""Wallet engine — BIP84 wallet with Esplora sync (embit; bdk-python unavailable on Windows)."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from embit import bip32
from embit.finalizer import finalize_psbt
from embit.psbt import PSBT
from embit.script import Script, p2wpkh
from embit.transaction import Transaction, TransactionInput, TransactionOutput

from src.database import WalletDatabase
from src.wallet.backend import ChainBackend, EsploraBackend, get_backend
from src.wallet.keys import (
    account_key_from_wallet,
    change_address,
    change_script_pubkey,
    change_signing_key_for_index,
    receive_address,
    receive_script_pubkey,
    signing_key_for_index,
)

logger = logging.getLogger(__name__)

GAP_LIMIT = 20
DUST_SATS = 546


class WalletEngine:
    def __init__(self, db: WalletDatabase):
        self.db = db

    def _wallet_row(self, wallet_id: int, user_id: int) -> dict:
        wallet = self.db.get_wallet_with_secrets(wallet_id, user_id)
        if not wallet:
            raise ValueError("Wallet not found")
        if not wallet.get("encrypted_seed"):
            raise ValueError("Wallet has no keys — recreate wallet")
        return wallet

    def _account(self, wallet: dict, user_id: int) -> bip32.HDKey:
        return account_key_from_wallet(wallet, user_id)

    def _backend(self, network: str) -> ChainBackend:
        return get_backend(network, self.db)

    def sync_wallet(self, wallet_id: int, user_id: int) -> dict:
        wallet = self._wallet_row(wallet_id, user_id)
        backend = self._backend(wallet["network"])
        account = self._account(wallet, user_id)
        tip = backend.tip_height()

        receive_index = wallet.get("receive_index") or 0
        change_index = wallet.get("change_index") or 0
        scan_to = max(receive_index + GAP_LIMIT, GAP_LIMIT)
        change_scan_to = max(change_index + GAP_LIMIT, GAP_LIMIT)
        seen_txids: set[str] = set()

        for idx in range(scan_to + 1):
            address = receive_address(account, wallet["network"], idx)
            self._scan_address(
                wallet_id,
                wallet["network"],
                address,
                backend,
                tip,
                idx,
                is_change=False,
                seen_txids=seen_txids,
            )

        for idx in range(change_scan_to + 1):
            address = change_address(account, wallet["network"], idx)
            self._scan_address(
                wallet_id,
                wallet["network"],
                address,
                backend,
                tip,
                idx,
                is_change=True,
                seen_txids=seen_txids,
            )

        self.db.update_wallet_sync(wallet_id, tip)
        self._score_wallet_privacy(wallet_id)
        return self.get_sync_status(wallet_id, user_id)

    def _scan_address(
        self,
        wallet_id: int,
        network: str,
        address: str,
        backend: ChainBackend,
        tip: int,
        derivation_index: int,
        *,
        is_change: bool,
        seen_txids: set[str],
    ) -> None:
        try:
            utxos = backend.address_utxos(address)
            txs = backend.address_transactions(address)
        except Exception as exc:
            logger.warning("Esplora error for %s: %s", address, exc)
            return

        live_keys: set[tuple[str, int]] = set()
        for utxo in utxos:
            live_keys.add((utxo["txid"], utxo["vout"]))
            self.db.upsert_utxo(
                wallet_id=wallet_id,
                txid=utxo["txid"],
                vout=utxo["vout"],
                amount_sats=utxo["value"],
                address=address,
                confirmations=utxo.get("status", {}).get("confirmed", False)
                and max(0, tip - utxo.get("status", {}).get("block_height", tip) + 1)
                or 0,
                derivation_index=derivation_index,
                is_change=is_change,
            )

        for db_utxo in self.db.list_utxos_for_address(wallet_id, address):
            key = (db_utxo["txid"], db_utxo["vout"])
            if key not in live_keys:
                self.db.mark_utxo_spent(wallet_id, key[0], key[1])

        for tx in txs:
            if tx["txid"] in seen_txids:
                continue
            seen_txids.add(tx["txid"])
            self._mirror_transaction(wallet_id, network, tx)

    def _mirror_transaction(self, wallet_id: int, network: str, tx: dict) -> None:
        status = tx.get("status", {})
        block_height = status.get("block_height")
        ts = status.get("block_time")
        timestamp = (
            datetime.fromtimestamp(ts, tz=timezone.utc).isoformat() if ts else None
        )

        wallet_addresses = self._known_addresses(wallet_id, network)
        net_sats = 0
        direction = "unknown"

        for vout in tx.get("vout", []):
            addr = vout.get("scriptpubkey_address")
            if addr in wallet_addresses:
                net_sats += vout.get("value", 0)

        for vin in tx.get("vin", []):
            prev = vin.get("prevout") or {}
            addr = prev.get("scriptpubkey_address")
            if addr in wallet_addresses:
                net_sats -= prev.get("value", 0)

        if net_sats > 0:
            direction = "receive"
        elif net_sats < 0:
            direction = "send"

        fee = tx.get("fee", 0) or 0
        self.db.upsert_transaction(
            wallet_id=wallet_id,
            txid=tx["txid"],
            direction=direction,
            amount_sats=abs(net_sats),
            fee_sats=fee,
            block_height=block_height,
            timestamp=timestamp,
            raw_json=str(tx)[:8000],
        )

    def _known_addresses(self, wallet_id: int, network: str) -> set[str]:
        wallet = self.db.get_wallet_internal(wallet_id)
        if not wallet or not wallet.get("encrypted_seed"):
            return set()
        account = account_key_from_encrypted_seed(wallet["encrypted_seed"], network)
        receive_index = wallet.get("receive_index") or 0
        change_index = wallet.get("change_index") or 0
        scan_to = max(receive_index + GAP_LIMIT, GAP_LIMIT)
        change_scan_to = max(change_index + GAP_LIMIT, GAP_LIMIT)
        addresses = {receive_address(account, network, i) for i in range(scan_to + 1)}
        addresses |= {change_address(account, network, i) for i in range(change_scan_to + 1)}
        return addresses

    def get_sync_status(self, wallet_id: int, user_id: int) -> dict:
        wallet = self._wallet_row(wallet_id, user_id)
        backend = self._backend(wallet["network"])
        try:
            tip = backend.tip_height()
        except Exception as exc:
            return {
                "wallet_id": wallet_id,
                "synced": False,
                "progress": 0,
                "block_height": wallet.get("last_synced_height") or 0,
                "message": str(exc),
            }

        last = wallet.get("last_synced_height") or 0
        synced = last >= tip and last > 0
        progress = min(100, int((last / tip) * 100)) if tip else 0
        return {
            "wallet_id": wallet_id,
            "synced": synced,
            "progress": progress,
            "block_height": tip,
            "last_synced_height": last,
        }

    def get_balance(self, wallet_id: int, user_id: int) -> dict:
        self._wallet_row(wallet_id, user_id)
        confirmed, unconfirmed = self.db.wallet_balance_sats(wallet_id)
        return {
            "confirmed_sats": confirmed,
            "unconfirmed_sats": unconfirmed,
            "total_sats": confirmed + unconfirmed,
        }

    def get_utxos(self, wallet_id: int, user_id: int) -> list[dict]:
        self._wallet_row(wallet_id, user_id)
        return self.db.list_utxos(wallet_id)

    def get_transactions(self, wallet_id: int, user_id: int, limit: int = 50) -> list[dict]:
        self._wallet_row(wallet_id, user_id)
        return self.db.list_transactions(wallet_id, limit=limit)

    def get_receive_address(self, wallet_id: int, user_id: int, advance: bool = True) -> dict:
        wallet = self._wallet_row(wallet_id, user_id)
        account = self._account(wallet, user_id)
        index = wallet.get("receive_index") or 0
        address = receive_address(account, wallet["network"], index)
        if advance:
            self.db.set_receive_index(wallet_id, index + 1)
        return {"address": address, "network": wallet["network"], "index": index}

    def get_stats(self, wallet_id: int, user_id: int) -> dict:
        self._wallet_row(wallet_id, user_id)
        txs = self.db.list_transactions(wallet_id, limit=500)
        utxos = self.db.list_utxos(wallet_id)
        received = sum(t["amount_sats"] for t in txs if t["direction"] == "receive")
        sent = sum(t["amount_sats"] for t in txs if t["direction"] == "send")
        fees = sum(t.get("fee_sats") or 0 for t in txs if t["direction"] == "send")
        privacy = self.get_privacy_summary(wallet_id, user_id)
        return {
            "balance_history": self._balance_history(wallet_id, txs),
            "tx_count": len(txs),
            "total_received_sats": received,
            "total_sent_sats": sent,
            "fees_paid_sats": fees,
            "utxo_count": len(utxos),
            "privacy_score": privacy["privacy_score"],
        }

    def _balance_history(self, wallet_id: int, txs: list[dict]) -> list[dict]:
        if not txs:
            confirmed, unconfirmed = self.db.wallet_balance_sats(wallet_id)
            total = confirmed + unconfirmed
            if total <= 0:
                return []
            from datetime import date

            return [{"date": date.today().isoformat(), "sats": total}]

        ordered = sorted(txs, key=lambda t: (t.get("timestamp") or "", t.get("txid") or ""))
        balance = 0
        history: list[dict] = []
        for t in ordered:
            if t["direction"] == "receive":
                balance += t["amount_sats"]
            elif t["direction"] == "send":
                balance -= t["amount_sats"] + (t.get("fee_sats") or 0)
            day = (t.get("timestamp") or "")[:10]
            if day:
                history.append({"date": day, "sats": max(0, balance)})
        return history

    def get_privacy_summary(self, wallet_id: int, user_id: int) -> dict:
        if not self.db.get_wallet(wallet_id, user_id):
            raise ValueError("Wallet not found")
        utxos = self.db.list_utxos(wallet_id)
        private = 0
        non_private = 0
        entities: list[str] = []

        for row in self.db.list_labels(wallet_id):
            name = row.get("label") or row.get("entity")
            if name and name not in entities:
                entities.append(name)

        exchange_exposure = sum(
            1
            for row in self.db.list_labels(wallet_id)
            if (row.get("entity") or "").lower() == "exchange"
        )

        for u in utxos:
            flags = [f for f in (u.get("privacy_flags") or "").split(",") if f]
            if flags:
                non_private += 1
            else:
                private += 1
            label = u.get("label")
            if label and label not in entities:
                entities.append(label)
            addr = u.get("address")
            if addr:
                addr_label = self.db.get_label(wallet_id, "address", addr)
                if addr_label:
                    ent = addr_label.get("label")
                    if ent and ent not in entities:
                        entities.append(ent)

        score = int(100 * private / len(utxos)) if utxos else 100
        return {
            "privacy_score": score,
            "private_utxos": private,
            "non_private_utxos": non_private,
            "entities": entities,
            "exchange_exposure": exchange_exposure,
            "message": None if utxos else "Sync wallet to analyze privacy",
        }

    def _score_wallet_privacy(self, wallet_id: int) -> None:
        utxos = self.db.list_utxos(wallet_id)
        address_counts: dict[str, int] = {}
        for u in utxos:
            addr = u.get("address") or ""
            if addr:
                address_counts[addr] = address_counts.get(addr, 0) + 1

        for u in utxos:
            flags: list[str] = []
            addr = u.get("address") or ""
            if addr and address_counts.get(addr, 0) > 1:
                flags.append("address_reuse")
            amt = u["amount_sats"]
            if amt >= 100_000 and amt % 100_000 == 0:
                flags.append("round_amount")
            if u.get("label"):
                flags.append("labeled")

            self.db.set_utxo_privacy_flags(
                wallet_id,
                u["txid"],
                u["vout"],
                ",".join(flags) if flags else None,
            )

    def preview_send(
        self,
        wallet_id: int,
        user_id: int,
        address: str,
        amount_sats: int,
        fee_rate_sat_vb: Optional[int] = None,
        utxo_refs: Optional[list[dict]] = None,
    ) -> dict:
        wallet = self._wallet_row(wallet_id, user_id)
        backend = self._backend(wallet["network"])
        fee_rate = fee_rate_sat_vb or backend.suggested_fee_rate()
        account = self._account(wallet, user_id)

        selected, fee_sats, change_sats = self._pick_inputs(
            wallet_id, amount_sats, fee_rate, utxo_refs
        )
        outputs = [TransactionOutput(amount_sats, Script.from_address(address))]
        if change_sats > DUST_SATS:
            change_idx = wallet.get("change_index") or 0
            change_addr = change_address(account, wallet["network"], change_idx)
            outputs.append(TransactionOutput(change_sats, Script.from_address(change_addr)))

        tx = self._build_unsigned_tx(selected, outputs)
        vsize = max(140, 10 + 68 * len(selected) + 31 * len(outputs))
        return {
            "address": address,
            "amount_sats": amount_sats,
            "fee_sats": fee_sats,
            "fee_rate_sat_vb": fee_rate,
            "change_sats": change_sats,
            "input_count": len(selected),
            "estimated_vsize": vsize,
            "hex_preview": tx.serialize().hex()[:64] + "...",
        }

    def send(
        self,
        wallet_id: int,
        user_id: int,
        address: str,
        amount_sats: int,
        fee_rate_sat_vb: Optional[int] = None,
        utxo_refs: Optional[list[dict]] = None,
    ) -> dict:
        wallet = self._wallet_row(wallet_id, user_id)
        backend = self._backend(wallet["network"])
        fee_rate = fee_rate_sat_vb or backend.suggested_fee_rate()
        account = self._account(wallet, user_id)

        selected, fee_sats, change_sats = self._pick_inputs(
            wallet_id, amount_sats, fee_rate, utxo_refs
        )
        outputs = [TransactionOutput(amount_sats, Script.from_address(address))]
        change_idx = wallet.get("change_index") or 0
        if change_sats > DUST_SATS:
            change_addr = change_address(account, wallet["network"], change_idx)
            outputs.append(TransactionOutput(change_sats, Script.from_address(change_addr)))

        tx = self._build_unsigned_tx(selected, outputs)
        psbt = PSBT(tx=tx)

        for i, utxo in enumerate(selected):
            idx = utxo.get("derivation_index") or 0
            if utxo.get("is_change"):
                script = change_script_pubkey(account, idx)
                key = change_signing_key_for_index(account, idx)
            else:
                script = receive_script_pubkey(account, idx)
                key = signing_key_for_index(account, idx)
            psbt.inputs[i].witness_utxo = TransactionOutput(utxo["amount_sats"], script)
            psbt.inputs[i].witness_script = script
            psbt.sign_with(key)

        final_tx = finalize_psbt(psbt)
        if final_tx is None:
            raise ValueError("Failed to finalize transaction — signing error")
        tx_hex = final_tx.serialize().hex()
        txid = backend.broadcast_tx(tx_hex)

        for utxo in selected:
            self.db.mark_utxo_spent(wallet_id, utxo["txid"], utxo["vout"])

        if change_sats > DUST_SATS:
            self.db.set_change_index(wallet_id, change_idx + 1)

        self.db.upsert_transaction(
            wallet_id=wallet_id,
            txid=txid,
            direction="send",
            amount_sats=amount_sats,
            fee_sats=fee_sats,
            block_height=None,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        return {
            "txid": txid,
            "fee_sats": fee_sats,
            "amount_sats": amount_sats,
            "hex": tx_hex,
        }

    def _pick_inputs(
        self,
        wallet_id: int,
        amount_sats: int,
        fee_rate: int,
        utxo_refs: Optional[list[dict]] = None,
    ) -> tuple[list[dict], int, int]:
        spendable = self.db.list_spendable_utxos(wallet_id)
        if not spendable:
            raise ValueError("No spendable UTXOs — sync wallet and receive funds first")

        if not utxo_refs:
            return self._coin_select(spendable, amount_sats, fee_rate)

        key_map = {(u["txid"], u["vout"]): u for u in spendable}
        selected: list[dict] = []
        for ref in utxo_refs:
            utxo = key_map.get((ref["txid"], ref["vout"]))
            if not utxo:
                raise ValueError(f"UTXO not spendable: {ref['txid'][:8]}:{ref['vout']}")
            selected.append(utxo)

        total = sum(u["amount_sats"] for u in selected)
        output_count = 2
        fee_sats = fee_rate * (10 + 68 * len(selected) + 31 * output_count)
        change = total - amount_sats - fee_sats
        if change <= DUST_SATS:
            output_count = 1
            fee_sats = fee_rate * (10 + 68 * len(selected) + 31 * output_count)
            change = total - amount_sats - fee_sats
        if total < amount_sats + fee_sats:
            raise ValueError("Selected UTXOs insufficient for amount + fee")
        return selected, fee_sats, change

    def _coin_select(
        self, utxos: list[dict], amount_sats: int, fee_rate: int
    ) -> tuple[list[dict], int, int]:
        sorted_utxos = sorted(utxos, key=lambda u: u["amount_sats"], reverse=True)
        selected: list[dict] = []
        total = 0

        for utxo in sorted_utxos:
            selected.append(utxo)
            total += utxo["amount_sats"]
            fee_sats = fee_rate * (10 + 68 * len(selected) + 31 * 2)
            if total >= amount_sats + fee_sats:
                change = total - amount_sats - fee_sats
                return selected, fee_sats, change

        raise ValueError("Insufficient funds for amount + fee")

    def _build_unsigned_tx(
        self, utxos: list[dict], outputs: list[TransactionOutput]
    ) -> Transaction:
        vin = [
            TransactionInput(bytes.fromhex(u["txid"])[::-1], u["vout"]) for u in utxos
        ]
        return Transaction(vin, outputs)
