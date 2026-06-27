"""Block explorer URLs for swap transaction links."""
from __future__ import annotations


def tx_explorer_url(asset: str, txid: str, network: str) -> str:
    asset = asset.strip().lower()
    network = network.strip().lower()
    txid = txid.strip()
    if asset == "xmr":
        if network == "mainnet":
            return f"https://xmrchain.net/tx/{txid}"
        if network == "testnet":
            return f"https://testnet.xmrchain.net/tx/{txid}"
        return f"https://stagenet.xmrchain.net/tx/{txid}"
    if network == "mainnet":
        return f"https://blockstream.info/tx/{txid}"
    if network == "signet":
        return f"https://blockstream.info/signet/tx/{txid}"
    return f"https://blockstream.info/testnet/tx/{txid}"


def enrich_swap_record(row: dict) -> dict:
    """Add explorer_links for attached transaction IDs."""
    from_asset = row.get("from_asset") or "btc"
    to_asset = row.get("to_asset") or "xmr"
    from_network = row.get("from_network") or "testnet"
    to_network = row.get("to_network") or "stagenet"

    links: dict[str, str | None] = {"from": None, "to": None}
    from_txid = row.get("from_txid")
    to_txid = row.get("to_txid")
    if from_txid:
        links["from"] = tx_explorer_url(from_asset, from_txid, from_network)
    if to_txid:
        links["to"] = tx_explorer_url(to_asset, to_txid, to_network)

    return {**row, "explorer_links": links}
