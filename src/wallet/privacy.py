"""Wasabi-style UTXO privacy scoring, flagging, and recommendations."""
from __future__ import annotations

from typing import Any, Callable, Optional

ADDRESS_REUSE = "address_reuse"
ROUND_AMOUNT = "round_amount"
LABELED = "labeled"
FROZEN = "frozen"

_FLAG_LABELS: dict[str, str] = {
    ADDRESS_REUSE: "Address reuse",
    ROUND_AMOUNT: "Round amount",
    LABELED: "Labeled UTXO",
    FROZEN: "Frozen",
}


def build_address_counts(utxos: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for u in utxos:
        addr = u.get("address") or ""
        if addr:
            counts[addr] = counts.get(addr, 0) + 1
    return counts


def compute_utxo_flags(utxo: dict, address_counts: dict[str, int]) -> list[str]:
    flags: list[str] = []
    addr = utxo.get("address") or ""
    if addr and address_counts.get(addr, 0) > 1:
        flags.append(ADDRESS_REUSE)
    amt = utxo["amount_sats"]
    if amt >= 100_000 and amt % 100_000 == 0:
        flags.append(ROUND_AMOUNT)
    if utxo.get("label"):
        flags.append(LABELED)
    if utxo.get("frozen"):
        flags.append(FROZEN)
    return flags


def apply_privacy_scores(db: Any, wallet_id: int) -> None:
    utxos = db.list_utxos(wallet_id)
    address_counts = build_address_counts(utxos)
    for u in utxos:
        flags = compute_utxo_flags(u, address_counts)
        db.set_utxo_privacy_flags(
            wallet_id,
            u["txid"],
            u["vout"],
            ",".join(flags) if flags else None,
        )


def _collect_entities(
    utxos: list[dict],
    label_rows: list[dict],
    address_label_lookup: Callable[[str], Optional[dict]],
) -> tuple[list[str], int]:
    entities: list[str] = []
    exchange_exposure = 0

    for row in label_rows:
        name = row.get("label") or row.get("entity")
        if name and name not in entities:
            entities.append(name)
        if (row.get("entity") or "").lower() == "exchange":
            exchange_exposure += 1

    for u in utxos:
        label = u.get("label")
        if label and label not in entities:
            entities.append(label)
        addr = u.get("address")
        if addr:
            addr_label = address_label_lookup(addr)
            if addr_label:
                ent = addr_label.get("label")
                if ent and ent not in entities:
                    entities.append(ent)

    return entities, exchange_exposure


def _count_flagged_utxos(utxos: list[dict]) -> tuple[int, int, dict[str, int]]:
    private = 0
    non_private = 0
    flag_counts: dict[str, int] = {}

    for u in utxos:
        flags = [f for f in (u.get("privacy_flags") or "").split(",") if f]
        privacy_flags = [f for f in flags if f != FROZEN]
        if privacy_flags:
            non_private += 1
        else:
            private += 1
        for flag in flags:
            flag_counts[flag] = flag_counts.get(flag, 0) + 1

    return private, non_private, flag_counts


def generate_recommendations(
    utxos: list[dict],
    *,
    private: int,
    non_private: int,
    exchange_exposure: int,
    flag_counts: dict[str, int],
) -> list[dict[str, str]]:
    recs: list[dict[str, str]] = []

    if not utxos:
        return recs

    reuse_count = flag_counts.get(ADDRESS_REUSE, 0)
    round_count = flag_counts.get(ROUND_AMOUNT, 0)

    if reuse_count:
        recs.append(
            {
                "id": "address_reuse",
                "severity": "critical",
                "title": "Avoid address reuse",
                "detail": (
                    f"{reuse_count} UTXO(s) share an address with other coins. "
                    "Receive to fresh addresses and avoid spending reused outputs together."
                ),
            }
        )

    if round_count:
        recs.append(
            {
                "id": "round_amounts",
                "severity": "warning",
                "title": "Round amounts stand out",
                "detail": (
                    f"{round_count} UTXO(s) have round BTC amounts. "
                    "Consider CoinJoin or splitting outputs to reduce fingerprinting."
                ),
            }
        )

    if exchange_exposure:
        recs.append(
            {
                "id": "exchange_exposure",
                "severity": "warning",
                "title": "Exchange-linked funds detected",
                "detail": (
                    f"{exchange_exposure} label(s) mark exchange exposure. "
                    "Mix or segregate these UTXOs before linking them to personal spends."
                ),
            }
        )

    frozen_spendable = sum(1 for u in utxos if u.get("frozen"))
    if frozen_spendable:
        recs.append(
            {
                "id": "frozen_utxos",
                "severity": "info",
                "title": "Frozen UTXOs excluded from sends",
                "detail": (
                    f"{frozen_spendable} UTXO(s) are frozen in Coin Control. "
                    "Unfreeze when you are ready to spend them."
                ),
            }
        )

    score = int(100 * private / len(utxos)) if utxos else 100
    if score < 70 and non_private:
        recs.append(
            {
                "id": "low_score",
                "severity": "warning",
                "title": "Privacy score is below average",
                "detail": (
                    f"{non_private} of {len(utxos)} UTXO(s) carry privacy flags. "
                    "Review Coin Control and label sensitive outputs."
                ),
            }
        )
    elif score >= 90 and not recs:
        recs.append(
            {
                "id": "good_score",
                "severity": "info",
                "title": "Strong UTXO hygiene",
                "detail": "Most outputs look unlinkable. Keep using fresh receive addresses.",
            }
        )

    return recs


def summarize_privacy(
    utxos: list[dict],
    label_rows: list[dict],
    address_label_lookup: Callable[[str], Optional[dict]],
) -> dict[str, Any]:
    entities, exchange_exposure = _collect_entities(
        utxos, label_rows, address_label_lookup
    )
    private, non_private, flag_counts = _count_flagged_utxos(utxos)
    score = int(100 * private / len(utxos)) if utxos else 100

    recommendations = generate_recommendations(
        utxos,
        private=private,
        non_private=non_private,
        exchange_exposure=exchange_exposure,
        flag_counts=flag_counts,
    )

    return {
        "privacy_score": score,
        "private_utxos": private,
        "non_private_utxos": non_private,
        "entities": entities,
        "exchange_exposure": exchange_exposure,
        "flag_counts": {k: v for k, v in flag_counts.items()},
        "recommendations": recommendations,
        "message": None if utxos else "Sync wallet to analyze privacy",
    }


def flag_label(flag: str) -> str:
    return _FLAG_LABELS.get(flag, flag.replace("_", " ").title())
