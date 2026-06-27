"""SQLite database for wallet platform."""
import logging
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

USER_ROLES = ("admin", "user", "pending")
ASSET_TYPES = ("btc", "xmr")

logger = logging.getLogger(__name__)


class WalletDatabase:
    """SQLite wrapper for users, wallets, and audit data."""

    def __init__(self, db_path: Optional[str] = None):
        import os

        from src.db_at_rest import prepare_db_path

        raw_path = Path(db_path or os.getenv("WALLET_DB", "wallet.db"))
        self.db_path = prepare_db_path(raw_path)
        self._init_db()
        self._seed_admin_from_env()
        logger.info("Database initialized at %s", self.db_path)

    def _init_db(self) -> None:
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    email TEXT,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'user',
                    is_active INTEGER NOT NULL DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_login DATETIME
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS wallets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    encrypted_seed TEXT,
                    xpub TEXT,
                    derivation_path TEXT DEFAULT "m/84'/0'/0'",
                    network TEXT NOT NULL DEFAULT 'testnet',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS utxos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    wallet_id INTEGER NOT NULL,
                    txid TEXT NOT NULL,
                    vout INTEGER NOT NULL,
                    amount_sats INTEGER NOT NULL,
                    address TEXT,
                    confirmations INTEGER DEFAULT 0,
                    is_spent INTEGER DEFAULT 0,
                    label TEXT,
                    frozen INTEGER DEFAULT 0,
                    privacy_flags TEXT,
                    UNIQUE(wallet_id, txid, vout),
                    FOREIGN KEY (wallet_id) REFERENCES wallets(id)
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    wallet_id INTEGER NOT NULL,
                    txid TEXT NOT NULL,
                    direction TEXT NOT NULL,
                    amount_sats INTEGER NOT NULL,
                    fee_sats INTEGER DEFAULT 0,
                    block_height INTEGER,
                    timestamp DATETIME,
                    raw_json TEXT,
                    label TEXT,
                    FOREIGN KEY (wallet_id) REFERENCES wallets(id)
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS labels (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    wallet_id INTEGER NOT NULL,
                    target_type TEXT NOT NULL,
                    target_id TEXT NOT NULL,
                    label TEXT NOT NULL,
                    entity TEXT,
                    FOREIGN KEY (wallet_id) REFERENCES wallets(id)
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    action TEXT NOT NULL,
                    details TEXT,
                    ip TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS leaderboard_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    display_name TEXT NOT NULL,
                    balance_sats INTEGER NOT NULL DEFAULT 0,
                    network TEXT NOT NULL,
                    opted_in INTEGER NOT NULL DEFAULT 0,
                    remote_token TEXT,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, network),
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS global_leaderboard_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    token_hash TEXT NOT NULL,
                    display_name TEXT NOT NULL,
                    balance_sats INTEGER NOT NULL DEFAULT 0,
                    network TEXT NOT NULL,
                    opted_in INTEGER NOT NULL DEFAULT 1,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(token_hash, network)
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS swaps (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    quote_id TEXT NOT NULL,
                    provider_id TEXT NOT NULL,
                    from_asset TEXT NOT NULL,
                    to_asset TEXT NOT NULL,
                    send_amount_atomic INTEGER NOT NULL,
                    receive_amount_atomic INTEGER NOT NULL,
                    status TEXT NOT NULL DEFAULT 'awaiting_deposit',
                    deposit_address TEXT,
                    deposit_amount_atomic INTEGER,
                    destination_wallet_id INTEGER,
                    provider_ref TEXT,
                    from_txid TEXT,
                    to_txid TEXT,
                    from_network TEXT,
                    to_network TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    settled_at DATETIME,
                    expires_at DATETIME,
                    raw_json TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (destination_wallet_id) REFERENCES wallets(id)
                )
            """)

            conn.commit()
            self._migrate_schema(conn)

    def _migrate_schema(self, conn: sqlite3.Connection) -> None:
        """Add columns introduced after initial schema."""
        wallet_cols = {r[1] for r in conn.execute("PRAGMA table_info(wallets)").fetchall()}
        if "receive_index" not in wallet_cols:
            conn.execute("ALTER TABLE wallets ADD COLUMN receive_index INTEGER DEFAULT 0")
        if "last_synced_height" not in wallet_cols:
            conn.execute("ALTER TABLE wallets ADD COLUMN last_synced_height INTEGER DEFAULT 0")
        if "change_index" not in wallet_cols:
            conn.execute("ALTER TABLE wallets ADD COLUMN change_index INTEGER DEFAULT 0")

        utxo_cols = {r[1] for r in conn.execute("PRAGMA table_info(utxos)").fetchall()}
        if "derivation_index" not in utxo_cols:
            conn.execute("ALTER TABLE utxos ADD COLUMN derivation_index INTEGER")
        if "is_change" not in utxo_cols:
            conn.execute("ALTER TABLE utxos ADD COLUMN is_change INTEGER DEFAULT 0")

        user_cols = {r[1] for r in conn.execute("PRAGMA table_info(users)").fetchall()}
        if "wallet_key_salt" not in user_cols:
            conn.execute("ALTER TABLE users ADD COLUMN wallet_key_salt TEXT")
        if "wallet_key_verifier" not in user_cols:
            conn.execute("ALTER TABLE users ADD COLUMN wallet_key_verifier TEXT")
        if "mainnet_ack_at" not in user_cols:
            conn.execute("ALTER TABLE users ADD COLUMN mainnet_ack_at DATETIME")

        if "encryption_version" not in wallet_cols:
            conn.execute(
                "ALTER TABLE wallets ADD COLUMN encryption_version INTEGER DEFAULT 1"
            )
        if "asset_type" not in wallet_cols:
            conn.execute(
                "ALTER TABLE wallets ADD COLUMN asset_type TEXT NOT NULL DEFAULT 'btc'"
            )
            conn.execute(
                "UPDATE wallets SET asset_type = 'btc' WHERE asset_type IS NULL OR asset_type = ''"
            )
        if "xmr_primary_address" not in wallet_cols:
            conn.execute("ALTER TABLE wallets ADD COLUMN xmr_primary_address TEXT")
        if "xmr_restore_height" not in wallet_cols:
            conn.execute(
                "ALTER TABLE wallets ADD COLUMN xmr_restore_height INTEGER DEFAULT 0"
            )
        if "xmr_account_index" not in wallet_cols:
            conn.execute(
                "ALTER TABLE wallets ADD COLUMN xmr_account_index INTEGER DEFAULT 0"
            )
        if "xmr_encrypted_view_key" not in wallet_cols:
            conn.execute("ALTER TABLE wallets ADD COLUMN xmr_encrypted_view_key TEXT")

        conn.execute("""
            CREATE TABLE IF NOT EXISTS swaps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                quote_id TEXT NOT NULL,
                provider_id TEXT NOT NULL,
                from_asset TEXT NOT NULL,
                to_asset TEXT NOT NULL,
                send_amount_atomic INTEGER NOT NULL,
                receive_amount_atomic INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'awaiting_deposit',
                deposit_address TEXT,
                deposit_amount_atomic INTEGER,
                destination_wallet_id INTEGER,
                provider_ref TEXT,
                from_txid TEXT,
                to_txid TEXT,
                from_network TEXT,
                to_network TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                settled_at DATETIME,
                expires_at DATETIME,
                raw_json TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (destination_wallet_id) REFERENCES wallets(id)
            )
        """)

        swap_cols = {r[1] for r in conn.execute("PRAGMA table_info(swaps)").fetchall()}
        for col, ddl in (
            ("from_txid", "TEXT"),
            ("to_txid", "TEXT"),
            ("from_network", "TEXT"),
            ("to_network", "TEXT"),
        ):
            if col not in swap_cols:
                conn.execute(f"ALTER TABLE swaps ADD COLUMN {col} {ddl}")

        leaderboard_cols = {
            r[1] for r in conn.execute("PRAGMA table_info(leaderboard_entries)").fetchall()
        }
        if "remote_token" not in leaderboard_cols:
            conn.execute("ALTER TABLE leaderboard_entries ADD COLUMN remote_token TEXT")

        conn.execute("""
            CREATE TABLE IF NOT EXISTS global_leaderboard_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                token_hash TEXT NOT NULL,
                display_name TEXT NOT NULL,
                balance_sats INTEGER NOT NULL DEFAULT 0,
                network TEXT NOT NULL,
                opted_in INTEGER NOT NULL DEFAULT 1,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(token_hash, network)
            )
        """)

        conn.commit()

    def _seed_admin_from_env(self) -> None:
        """Create initial admin from env vars when no users exist."""
        import os

        import bcrypt

        if self.count_users() > 0:
            return

        username = os.getenv("ADMIN_USERNAME", "admin")
        password_hash = os.getenv("ADMIN_PASSWORD_HASH", "").strip().strip('"').strip("'")
        if not password_hash:
            plain = os.getenv("ADMIN_PASSWORD", "")
            if plain:
                password_hash = bcrypt.hashpw(
                    plain.encode(), bcrypt.gensalt()
                ).decode()
            else:
                return

        self.create_user(username, password_hash, role="admin")
        logger.info("Seeded admin user from environment: %s", username)

    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(str(self.db_path), timeout=10)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _row_to_user(self, row: sqlite3.Row) -> dict:
        return {
            "id": row["id"],
            "username": row["username"],
            "email": row["email"],
            "role": row["role"],
            "is_active": bool(row["is_active"]),
            "created_at": row["created_at"],
            "last_login": row["last_login"],
            "has_wallet_passphrase": bool(row["wallet_key_verifier"])
            if "wallet_key_verifier" in row.keys()
            else False,
        }

    # --- Users ---

    def count_users(self) -> int:
        with self.get_connection() as conn:
            return conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]

    def create_user(
        self,
        username: str,
        password_hash: str,
        role: str = "user",
        email: Optional[str] = None,
    ) -> int:
        if role not in USER_ROLES:
            raise ValueError(f"Invalid role: {role}")

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO users (username, email, password_hash, role)
                VALUES (?, ?, ?, ?)
                """,
                (username, email, password_hash, role),
            )
            conn.commit()
            return cursor.lastrowid

    def get_user_by_username(self, username: str) -> Optional[dict]:
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE username = ?", (username,)
            ).fetchone()
            return self._row_to_user(row) if row else None

    def get_user_by_id(self, user_id: int) -> Optional[dict]:
        with self.get_connection() as conn:
            row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
            return self._row_to_user(row) if row else None

    def get_user_password_hash(self, username: str) -> Optional[str]:
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT password_hash FROM users WHERE username = ?", (username,)
            ).fetchone()
            return row["password_hash"] if row else None

    def update_last_login(self, user_id: int) -> None:
        with self.get_connection() as conn:
            conn.execute(
                "UPDATE users SET last_login = ? WHERE id = ?",
                (datetime.utcnow().isoformat(), user_id),
            )
            conn.commit()

    def list_users(self) -> list[dict]:
        with self.get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM users ORDER BY created_at ASC"
            ).fetchall()
            return [self._row_to_user(r) for r in rows]

    def update_user(
        self,
        user_id: int,
        *,
        role: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> bool:
        updates: list[str] = []
        params: list[Any] = []

        if role is not None:
            if role not in USER_ROLES:
                raise ValueError(f"Invalid role: {role}")
            updates.append("role = ?")
            params.append(role)
        if is_active is not None:
            updates.append("is_active = ?")
            params.append(1 if is_active else 0)

        if not updates:
            return False

        params.append(user_id)
        with self.get_connection() as conn:
            cursor = conn.execute(
                f"UPDATE users SET {', '.join(updates)} WHERE id = ?",
                params,
            )
            conn.commit()
            return cursor.rowcount > 0

    def change_password(self, user_id: int, password_hash: str) -> None:
        with self.get_connection() as conn:
            conn.execute(
                "UPDATE users SET password_hash = ? WHERE id = ?",
                (password_hash, user_id),
            )
            conn.commit()

    def get_wallet_security(self, user_id: int) -> Optional[dict]:
        with self.get_connection() as conn:
            row = conn.execute(
                """
                SELECT wallet_key_salt, wallet_key_verifier, mainnet_ack_at
                FROM users WHERE id = ?
                """,
                (user_id,),
            ).fetchone()
            if not row:
                return None
            return {
                "wallet_key_salt": row["wallet_key_salt"],
                "wallet_key_verifier": row["wallet_key_verifier"],
                "mainnet_ack_at": row["mainnet_ack_at"]
                if "mainnet_ack_at" in row.keys()
                else None,
            }

    def get_mainnet_ack_at(self, user_id: int) -> Optional[str]:
        security = self.get_wallet_security(user_id)
        if not security:
            return None
        return security.get("mainnet_ack_at")

    def set_mainnet_ack(self, user_id: int) -> str:
        now = datetime.utcnow().isoformat()
        with self.get_connection() as conn:
            conn.execute(
                "UPDATE users SET mainnet_ack_at = ? WHERE id = ?",
                (now, user_id),
            )
            conn.commit()
        return now

    def set_wallet_security(
        self, user_id: int, salt: str, verifier: str
    ) -> None:
        with self.get_connection() as conn:
            conn.execute(
                """
                UPDATE users
                SET wallet_key_salt = ?, wallet_key_verifier = ?
                WHERE id = ?
                """,
                (salt, verifier, user_id),
            )
            conn.commit()

    def count_admins(self) -> int:
        with self.get_connection() as conn:
            return conn.execute(
                "SELECT COUNT(*) FROM users WHERE role = 'admin' AND is_active = 1"
            ).fetchone()[0]

    def count_user_wallets(self, user_id: int) -> int:
        with self.get_connection() as conn:
            return conn.execute(
                "SELECT COUNT(*) FROM wallets WHERE user_id = ?", (user_id,)
            ).fetchone()[0]

    def list_users_with_stats(self) -> list[dict]:
        with self.get_connection() as conn:
            rows = conn.execute(
                """
                SELECT u.*, COUNT(w.id) AS wallet_count
                FROM users u
                LEFT JOIN wallets w ON w.user_id = u.id
                GROUP BY u.id
                ORDER BY u.created_at ASC
                """
            ).fetchall()
            result = []
            for row in rows:
                user = self._row_to_user(row)
                user["wallet_count"] = row["wallet_count"]
                result.append(user)
            return result

    # --- Wallets ---

    _WALLET_PUBLIC_COLUMNS = """
        id, user_id, name, asset_type, xpub, derivation_path, network,
        xmr_primary_address, xmr_restore_height, xmr_account_index,
        receive_index, last_synced_height, encryption_version, created_at
    """

    def list_wallets(
        self, user_id: int, asset_type: Optional[str] = None
    ) -> list[dict]:
        query = f"""
            SELECT {self._WALLET_PUBLIC_COLUMNS}
            FROM wallets WHERE user_id = ?
        """
        params: list[Any] = [user_id]
        if asset_type is not None:
            if asset_type not in ASSET_TYPES:
                raise ValueError(f"Invalid asset_type: {asset_type}")
            query += " AND asset_type = ?"
            params.append(asset_type)
        query += " ORDER BY created_at ASC"
        with self.get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [self._normalize_wallet_row(dict(r)) for r in rows]

    @staticmethod
    def _normalize_wallet_row(row: dict) -> dict:
        row.setdefault("asset_type", "btc")
        return row

    def list_wallets_with_secrets(self, user_id: int) -> list[dict]:
        with self.get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM wallets WHERE user_id = ? ORDER BY created_at ASC",
                (user_id,),
            ).fetchall()
            return [dict(r) for r in rows]

    def update_wallet_encryption(
        self, wallet_id: int, encrypted_seed: str, encryption_version: int
    ) -> None:
        with self.get_connection() as conn:
            conn.execute(
                """
                UPDATE wallets
                SET encrypted_seed = ?, encryption_version = ?
                WHERE id = ?
                """,
                (encrypted_seed, encryption_version, wallet_id),
            )
            conn.commit()

    def get_wallet(self, wallet_id: int, user_id: int) -> Optional[dict]:
        with self.get_connection() as conn:
            row = conn.execute(
                f"""
                SELECT {self._WALLET_PUBLIC_COLUMNS}
                FROM wallets WHERE id = ? AND user_id = ?
                """,
                (wallet_id, user_id),
            ).fetchone()
            return self._normalize_wallet_row(dict(row)) if row else None

    def get_wallet_with_secrets(self, wallet_id: int, user_id: int) -> Optional[dict]:
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM wallets WHERE id = ? AND user_id = ?",
                (wallet_id, user_id),
            ).fetchone()
            return dict(row) if row else None

    def get_wallet_internal(self, wallet_id: int) -> Optional[dict]:
        with self.get_connection() as conn:
            row = conn.execute("SELECT * FROM wallets WHERE id = ?", (wallet_id,)).fetchone()
            return dict(row) if row else None

    def create_wallet(
        self,
        user_id: int,
        name: str,
        network: str = "testnet",
        xpub: Optional[str] = None,
        encrypted_seed: Optional[str] = None,
        derivation_path: Optional[str] = None,
        encryption_version: int = 2,
        *,
        asset_type: str = "btc",
        xmr_primary_address: Optional[str] = None,
        xmr_restore_height: int = 0,
        xmr_account_index: int = 0,
        xmr_encrypted_view_key: Optional[str] = None,
    ) -> int:
        if asset_type not in ASSET_TYPES:
            raise ValueError(f"Invalid asset_type: {asset_type}")
        if asset_type == "btc" and not xpub:
            raise ValueError("BTC wallets require xpub")
        if asset_type == "xmr" and not xmr_primary_address:
            raise ValueError("XMR wallets require xmr_primary_address")

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO wallets (
                    user_id, name, network, asset_type, xpub, encrypted_seed,
                    derivation_path, encryption_version,
                    xmr_primary_address, xmr_restore_height, xmr_account_index,
                    xmr_encrypted_view_key
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    name,
                    network,
                    asset_type,
                    xpub,
                    encrypted_seed,
                    derivation_path,
                    encryption_version,
                    xmr_primary_address,
                    xmr_restore_height,
                    xmr_account_index,
                    xmr_encrypted_view_key,
                ),
            )
            conn.commit()
            return cursor.lastrowid

    def update_wallet_xmr_sync(
        self,
        wallet_id: int,
        *,
        restore_height: Optional[int] = None,
        receive_index: Optional[int] = None,
    ) -> None:
        updates: list[str] = []
        params: list[Any] = []
        if restore_height is not None:
            updates.append("xmr_restore_height = ?")
            params.append(restore_height)
        if receive_index is not None:
            updates.append("receive_index = ?")
            params.append(receive_index)
        if not updates:
            return
        params.append(wallet_id)
        with self.get_connection() as conn:
            conn.execute(
                f"UPDATE wallets SET {', '.join(updates)} WHERE id = ?",
                params,
            )
            conn.commit()

    def set_receive_index(self, wallet_id: int, index: int) -> None:
        with self.get_connection() as conn:
            conn.execute(
                "UPDATE wallets SET receive_index = ? WHERE id = ?",
                (index, wallet_id),
            )
            conn.commit()

    def set_change_index(self, wallet_id: int, index: int) -> None:
        with self.get_connection() as conn:
            conn.execute(
                "UPDATE wallets SET change_index = ? WHERE id = ?",
                (index, wallet_id),
            )
            conn.commit()

    def update_wallet_sync(self, wallet_id: int, height: int) -> None:
        with self.get_connection() as conn:
            conn.execute(
                "UPDATE wallets SET last_synced_height = ? WHERE id = ?",
                (height, wallet_id),
            )
            conn.commit()

    def clear_utxos(self, wallet_id: int) -> None:
        with self.get_connection() as conn:
            conn.execute("DELETE FROM utxos WHERE wallet_id = ?", (wallet_id,))
            conn.commit()

    def upsert_utxo(
        self,
        wallet_id: int,
        txid: str,
        vout: int,
        amount_sats: int,
        address: str,
        confirmations: int = 0,
        derivation_index: Optional[int] = None,
        is_change: bool = False,
    ) -> None:
        with self.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO utxos (wallet_id, txid, vout, amount_sats, address,
                                   confirmations, is_spent, derivation_index, is_change)
                VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?)
                ON CONFLICT(wallet_id, txid, vout) DO UPDATE SET
                    amount_sats = excluded.amount_sats,
                    address = excluded.address,
                    confirmations = excluded.confirmations,
                    is_spent = 0,
                    derivation_index = excluded.derivation_index,
                    is_change = excluded.is_change
                """,
                (wallet_id, txid, vout, amount_sats, address, confirmations, derivation_index, int(is_change)),
            )
            conn.commit()

    def list_utxos(self, wallet_id: int) -> list[dict]:
        with self.get_connection() as conn:
            rows = conn.execute(
                """
                SELECT txid, vout, amount_sats, address, confirmations, is_spent,
                       label, frozen, derivation_index, is_change, privacy_flags
                FROM utxos WHERE wallet_id = ? AND is_spent = 0
                ORDER BY amount_sats DESC
                """,
                (wallet_id,),
            ).fetchall()
            return [dict(r) for r in rows]

    def list_utxos_for_address(self, wallet_id: int, address: str) -> list[dict]:
        with self.get_connection() as conn:
            rows = conn.execute(
                """
                SELECT txid, vout, amount_sats, address, confirmations, is_spent,
                       label, frozen, derivation_index, is_change, privacy_flags
                FROM utxos
                WHERE wallet_id = ? AND address = ? AND is_spent = 0
                """,
                (wallet_id, address),
            ).fetchall()
            return [dict(r) for r in rows]

    def list_spendable_utxos(self, wallet_id: int, min_confirmations: int = 0) -> list[dict]:
        with self.get_connection() as conn:
            rows = conn.execute(
                """
                SELECT txid, vout, amount_sats, address, confirmations, derivation_index, is_change
                FROM utxos
                WHERE wallet_id = ? AND is_spent = 0 AND frozen = 0
                  AND confirmations >= ?
                ORDER BY amount_sats DESC
                """,
                (wallet_id, min_confirmations),
            ).fetchall()
            return [dict(r) for r in rows]

    def mark_utxo_spent(self, wallet_id: int, txid: str, vout: int) -> None:
        with self.get_connection() as conn:
            conn.execute(
                "UPDATE utxos SET is_spent = 1 WHERE wallet_id = ? AND txid = ? AND vout = ?",
                (wallet_id, txid, vout),
            )
            conn.commit()

    def update_utxo(
        self,
        wallet_id: int,
        txid: str,
        vout: int,
        *,
        frozen: Optional[bool] = None,
        label: Optional[str] = None,
    ) -> Optional[dict]:
        updates: list[str] = []
        params: list[Any] = []

        if frozen is not None:
            updates.append("frozen = ?")
            params.append(1 if frozen else 0)
        if label is not None:
            updates.append("label = ?")
            params.append(label)

        if not updates:
            return self.get_utxo(wallet_id, txid, vout)

        params.extend([wallet_id, txid, vout])
        with self.get_connection() as conn:
            cursor = conn.execute(
                f"UPDATE utxos SET {', '.join(updates)} WHERE wallet_id = ? AND txid = ? AND vout = ? AND is_spent = 0",
                params,
            )
            conn.commit()
            if cursor.rowcount == 0:
                return None
        return self.get_utxo(wallet_id, txid, vout)

    def set_utxo_privacy_flags(
        self, wallet_id: int, txid: str, vout: int, flags: Optional[str]
    ) -> None:
        with self.get_connection() as conn:
            conn.execute(
                "UPDATE utxos SET privacy_flags = ? WHERE wallet_id = ? AND txid = ? AND vout = ?",
                (flags, wallet_id, txid, vout),
            )
            conn.commit()

    def get_utxo(self, wallet_id: int, txid: str, vout: int) -> Optional[dict]:
        with self.get_connection() as conn:
            row = conn.execute(
                """
                SELECT txid, vout, amount_sats, address, confirmations, is_spent,
                       label, frozen, derivation_index, is_change, privacy_flags
                FROM utxos WHERE wallet_id = ? AND txid = ? AND vout = ?
                """,
                (wallet_id, txid, vout),
            ).fetchone()
            return dict(row) if row else None

    def wallet_balance_sats(self, wallet_id: int) -> tuple[int, int]:
        with self.get_connection() as conn:
            confirmed = conn.execute(
                """
                SELECT COALESCE(SUM(amount_sats), 0) FROM utxos
                WHERE wallet_id = ? AND is_spent = 0 AND confirmations >= 1
                """,
                (wallet_id,),
            ).fetchone()[0]
            unconfirmed = conn.execute(
                """
                SELECT COALESCE(SUM(amount_sats), 0) FROM utxos
                WHERE wallet_id = ? AND is_spent = 0 AND confirmations < 1
                """,
                (wallet_id,),
            ).fetchone()[0]
            return int(confirmed), int(unconfirmed)

    def upsert_transaction(
        self,
        wallet_id: int,
        txid: str,
        direction: str,
        amount_sats: int,
        fee_sats: int = 0,
        block_height: Optional[int] = None,
        timestamp: Optional[str] = None,
        raw_json: Optional[str] = None,
    ) -> None:
        with self.get_connection() as conn:
            existing = conn.execute(
                "SELECT id FROM transactions WHERE wallet_id = ? AND txid = ?",
                (wallet_id, txid),
            ).fetchone()
            if existing:
                conn.execute(
                    """
                    UPDATE transactions SET direction = ?, amount_sats = ?, fee_sats = ?,
                        block_height = ?, timestamp = ?, raw_json = ?
                    WHERE wallet_id = ? AND txid = ?
                    """,
                    (direction, amount_sats, fee_sats, block_height, timestamp, raw_json, wallet_id, txid),
                )
            else:
                conn.execute(
                    """
                    INSERT INTO transactions (wallet_id, txid, direction, amount_sats, fee_sats,
                                              block_height, timestamp, raw_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (wallet_id, txid, direction, amount_sats, fee_sats, block_height, timestamp, raw_json),
                )
            conn.commit()

    def list_transactions(self, wallet_id: int, limit: int = 50) -> list[dict]:
        with self.get_connection() as conn:
            rows = conn.execute(
                """
                SELECT txid, direction, amount_sats, fee_sats, block_height, timestamp, label
                FROM transactions WHERE wallet_id = ?
                ORDER BY COALESCE(timestamp, '') DESC, id DESC
                LIMIT ?
                """,
                (wallet_id, limit),
            ).fetchall()
            return [dict(r) for r in rows]

    # --- Labels ---

    def upsert_label(
        self,
        wallet_id: int,
        target_type: str,
        target_id: str,
        label: str,
        entity: Optional[str] = None,
    ) -> dict:
        with self.get_connection() as conn:
            existing = conn.execute(
                """
                SELECT id FROM labels
                WHERE wallet_id = ? AND target_type = ? AND target_id = ?
                """,
                (wallet_id, target_type, target_id),
            ).fetchone()
            if existing:
                conn.execute(
                    """
                    UPDATE labels SET label = ?, entity = ?
                    WHERE wallet_id = ? AND target_type = ? AND target_id = ?
                    """,
                    (label, entity, wallet_id, target_type, target_id),
                )
            else:
                conn.execute(
                    """
                    INSERT INTO labels (wallet_id, target_type, target_id, label, entity)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (wallet_id, target_type, target_id, label, entity),
                )
            if target_type == "tx":
                conn.execute(
                    "UPDATE transactions SET label = ? WHERE wallet_id = ? AND txid = ?",
                    (label, wallet_id, target_id),
                )
            conn.commit()
        row = self.get_label(wallet_id, target_type, target_id)
        return row or {
            "wallet_id": wallet_id,
            "target_type": target_type,
            "target_id": target_id,
            "label": label,
            "entity": entity,
        }

    def get_label(
        self, wallet_id: int, target_type: str, target_id: str
    ) -> Optional[dict]:
        with self.get_connection() as conn:
            row = conn.execute(
                """
                SELECT wallet_id, target_type, target_id, label, entity
                FROM labels
                WHERE wallet_id = ? AND target_type = ? AND target_id = ?
                """,
                (wallet_id, target_type, target_id),
            ).fetchone()
            return dict(row) if row else None

    def list_labels(self, wallet_id: int, target_type: Optional[str] = None) -> list[dict]:
        with self.get_connection() as conn:
            if target_type:
                rows = conn.execute(
                    """
                    SELECT wallet_id, target_type, target_id, label, entity
                    FROM labels WHERE wallet_id = ? AND target_type = ?
                    ORDER BY target_id
                    """,
                    (wallet_id, target_type),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT wallet_id, target_type, target_id, label, entity
                    FROM labels WHERE wallet_id = ?
                    ORDER BY target_type, target_id
                    """,
                    (wallet_id,),
                ).fetchall()
            return [dict(r) for r in rows]

    def delete_label(self, wallet_id: int, target_type: str, target_id: str) -> bool:
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                DELETE FROM labels
                WHERE wallet_id = ? AND target_type = ? AND target_id = ?
                """,
                (wallet_id, target_type, target_id),
            )
            if target_type == "tx":
                conn.execute(
                    "UPDATE transactions SET label = NULL WHERE wallet_id = ? AND txid = ?",
                    (wallet_id, target_id),
                )
            conn.commit()
            return cursor.rowcount > 0

    def delete_wallet(self, wallet_id: int, user_id: int) -> bool:
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT id FROM wallets WHERE id = ? AND user_id = ?",
                (wallet_id, user_id),
            ).fetchone()
            if not row:
                return False
            conn.execute("DELETE FROM utxos WHERE wallet_id = ?", (wallet_id,))
            conn.execute("DELETE FROM transactions WHERE wallet_id = ?", (wallet_id,))
            conn.execute("DELETE FROM labels WHERE wallet_id = ?", (wallet_id,))
            conn.execute("DELETE FROM wallets WHERE id = ?", (wallet_id,))
            conn.commit()
            return True

    # --- Audit ---

    def add_audit(
        self,
        action: str,
        user_id: Optional[int] = None,
        details: str = "",
        ip: Optional[str] = None,
    ) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO audit_log (user_id, action, details, ip)
                VALUES (?, ?, ?, ?)
                """,
                (user_id, action, details, ip),
            )
            conn.commit()
            return cursor.lastrowid

    def get_audit_log(self, limit: int = 50) -> list[dict]:
        with self.get_connection() as conn:
            rows = conn.execute(
                """
                SELECT a.*, u.username
                FROM audit_log a
                LEFT JOIN users u ON u.id = a.user_id
                ORDER BY a.timestamp DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
            return [dict(r) for r in rows]

    # --- System settings ---

    def get_setting(self, key: str, default: str = "") -> str:
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT value FROM system_settings WHERE key = ?", (key,)
            ).fetchone()
            return row["value"] if row else default

    def set_setting(self, key: str, value: str) -> None:
        with self.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO system_settings (key, value) VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
                """,
                (key, value),
            )
            conn.commit()

    def get_system_settings(self) -> dict[str, str]:
        import os

        defaults = {
            "network": os.getenv("BITCOIN_NETWORK", "testnet"),
            "backend_uri": os.getenv("BITCOIN_BACKEND_URI", ""),
            "tor_enabled": os.getenv("TOR_ENABLED", "false"),
            "coordinator_uri": os.getenv("COORDINATOR_URI", ""),
            "allow_mainnet": os.getenv("ALLOW_MAINNET", "false"),
            "backend_type": os.getenv("BITCOIN_BACKEND_TYPE", "esplora"),
            "wallet_unlock_ttl": os.getenv("WALLET_UNLOCK_TTL", "900"),
        }
        with self.get_connection() as conn:
            rows = conn.execute("SELECT key, value FROM system_settings").fetchall()
            stored = {r["key"]: r["value"] for r in rows}
        return {**defaults, **stored}

    # --- Leaderboard ---

    def user_total_balance_sats(self, user_id: int, network: str) -> int:
        total = 0
        for wallet in self.list_wallets(user_id):
            if wallet["network"] != network:
                continue
            confirmed, unconfirmed = self.wallet_balance_sats(wallet["id"])
            total += confirmed + unconfirmed
        return total

    def get_leaderboard_entry(self, user_id: int, network: str) -> Optional[dict]:
        with self.get_connection() as conn:
            row = conn.execute(
                """
                SELECT user_id, display_name, balance_sats, network, opted_in, remote_token, updated_at
                FROM leaderboard_entries
                WHERE user_id = ? AND network = ?
                """,
                (user_id, network),
            ).fetchone()
            if not row:
                return None
            return {
                "user_id": row["user_id"],
                "display_name": row["display_name"],
                "balance_sats": row["balance_sats"],
                "network": row["network"],
                "opted_in": bool(row["opted_in"]),
                "remote_token": row["remote_token"],
                "updated_at": row["updated_at"],
            }

    def set_leaderboard_opt_in(
        self,
        user_id: int,
        network: str,
        display_name: str,
        opted_in: bool,
        balance_sats: int = 0,
        remote_token: str | None = None,
    ) -> None:
        with self.get_connection() as conn:
            if not opted_in:
                conn.execute(
                    "DELETE FROM leaderboard_entries WHERE user_id = ? AND network = ?",
                    (user_id, network),
                )
                conn.commit()
                return

            conn.execute(
                """
                INSERT INTO leaderboard_entries (
                    user_id, display_name, balance_sats, network, opted_in, remote_token, updated_at
                )
                VALUES (?, ?, ?, ?, 1, ?, ?)
                ON CONFLICT(user_id, network) DO UPDATE SET
                    display_name = excluded.display_name,
                    balance_sats = excluded.balance_sats,
                    opted_in = 1,
                    remote_token = COALESCE(excluded.remote_token, leaderboard_entries.remote_token),
                    updated_at = excluded.updated_at
                """,
                (
                    user_id,
                    display_name,
                    balance_sats,
                    network,
                    remote_token,
                    datetime.utcnow().isoformat(),
                ),
            )
            conn.commit()

    def update_leaderboard_balance(
        self, user_id: int, network: str, balance_sats: int
    ) -> bool:
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                UPDATE leaderboard_entries
                SET balance_sats = ?, updated_at = ?
                WHERE user_id = ? AND network = ? AND opted_in = 1
                """,
                (balance_sats, datetime.utcnow().isoformat(), user_id, network),
            )
            conn.commit()
            return cursor.rowcount > 0

    def list_leaderboard(self, network: str, limit: int = 100) -> list[dict]:
        with self.get_connection() as conn:
            rows = conn.execute(
                """
                SELECT display_name, balance_sats, updated_at
                FROM leaderboard_entries
                WHERE network = ? AND opted_in = 1
                ORDER BY balance_sats DESC, updated_at ASC
                LIMIT ?
                """,
                (network, limit),
            ).fetchall()
            return [
                {
                    "rank": idx + 1,
                    "display_name": row["display_name"],
                    "balance_sats": row["balance_sats"],
                    "updated_at": row["updated_at"],
                }
                for idx, row in enumerate(rows)
            ]

    def get_leaderboard_rank(self, user_id: int, network: str) -> Optional[int]:
        with self.get_connection() as conn:
            row = conn.execute(
                """
                SELECT balance_sats FROM leaderboard_entries
                WHERE user_id = ? AND network = ? AND opted_in = 1
                """,
                (user_id, network),
            ).fetchone()
            if not row:
                return None
            rank = conn.execute(
                """
                SELECT COUNT(*) + 1 FROM leaderboard_entries
                WHERE network = ? AND opted_in = 1 AND balance_sats > ?
                """,
                (network, row["balance_sats"]),
            ).fetchone()[0]
            return int(rank)

    def upsert_global_leaderboard(
        self,
        token_hash: str,
        display_name: str,
        network: str,
        balance_sats: int,
        *,
        opted_in: bool = True,
    ) -> None:
        with self.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO global_leaderboard_entries (
                    token_hash, display_name, balance_sats, network, opted_in, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(token_hash, network) DO UPDATE SET
                    display_name = excluded.display_name,
                    balance_sats = excluded.balance_sats,
                    opted_in = excluded.opted_in,
                    updated_at = excluded.updated_at
                """,
                (
                    token_hash,
                    display_name,
                    balance_sats,
                    network,
                    1 if opted_in else 0,
                    datetime.utcnow().isoformat(),
                ),
            )
            conn.commit()

    def update_global_leaderboard_balance(
        self, token_hash: str, network: str, balance_sats: int
    ) -> bool:
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                UPDATE global_leaderboard_entries
                SET balance_sats = ?, updated_at = ?
                WHERE token_hash = ? AND network = ? AND opted_in = 1
                """,
                (balance_sats, datetime.utcnow().isoformat(), token_hash, network),
            )
            conn.commit()
            return cursor.rowcount > 0

    def delete_global_leaderboard(self, token_hash: str, network: str) -> None:
        with self.get_connection() as conn:
            conn.execute(
                """
                DELETE FROM global_leaderboard_entries
                WHERE token_hash = ? AND network = ?
                """,
                (token_hash, network),
            )
            conn.commit()

    def get_global_leaderboard_entry(
        self, token_hash: str, network: str
    ) -> Optional[dict]:
        with self.get_connection() as conn:
            row = conn.execute(
                """
                SELECT token_hash, display_name, balance_sats, network, opted_in, updated_at
                FROM global_leaderboard_entries
                WHERE token_hash = ? AND network = ?
                """,
                (token_hash, network),
            ).fetchone()
            if not row:
                return None
            return {
                "token_hash": row["token_hash"],
                "display_name": row["display_name"],
                "balance_sats": row["balance_sats"],
                "network": row["network"],
                "opted_in": bool(row["opted_in"]),
                "updated_at": row["updated_at"],
            }

    def list_global_leaderboard(self, network: str, limit: int = 100) -> list[dict]:
        with self.get_connection() as conn:
            rows = conn.execute(
                """
                SELECT display_name, balance_sats, updated_at
                FROM global_leaderboard_entries
                WHERE network = ? AND opted_in = 1
                ORDER BY balance_sats DESC, updated_at ASC
                LIMIT ?
                """,
                (network, limit),
            ).fetchall()
            return [
                {
                    "rank": idx + 1,
                    "display_name": row["display_name"],
                    "balance_sats": row["balance_sats"],
                    "updated_at": row["updated_at"],
                }
                for idx, row in enumerate(rows)
            ]

    def get_global_leaderboard_rank(self, token_hash: str, network: str) -> Optional[int]:
        with self.get_connection() as conn:
            row = conn.execute(
                """
                SELECT balance_sats FROM global_leaderboard_entries
                WHERE token_hash = ? AND network = ? AND opted_in = 1
                """,
                (token_hash, network),
            ).fetchone()
            if not row:
                return None
            rank = conn.execute(
                """
                SELECT COUNT(*) + 1 FROM global_leaderboard_entries
                WHERE network = ? AND opted_in = 1 AND balance_sats > ?
                """,
                (network, row["balance_sats"]),
            ).fetchone()[0]
            return int(rank)

    # --- Swaps ---

    def create_swap(
        self,
        user_id: int,
        *,
        quote_id: str,
        provider_id: str,
        from_asset: str,
        to_asset: str,
        send_amount_atomic: int,
        receive_amount_atomic: int,
        status: str,
        destination_wallet_id: Optional[int] = None,
        deposit_address: Optional[str] = None,
        deposit_amount_atomic: Optional[int] = None,
        expires_at: Optional[str] = None,
        raw_json: Optional[str] = None,
        from_network: Optional[str] = None,
        to_network: Optional[str] = None,
        from_txid: Optional[str] = None,
        to_txid: Optional[str] = None,
    ) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO swaps (
                    user_id, quote_id, provider_id, from_asset, to_asset,
                    send_amount_atomic, receive_amount_atomic, status,
                    destination_wallet_id, deposit_address, deposit_amount_atomic,
                    expires_at, raw_json, from_network, to_network, from_txid, to_txid
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    quote_id,
                    provider_id,
                    from_asset,
                    to_asset,
                    send_amount_atomic,
                    receive_amount_atomic,
                    status,
                    destination_wallet_id,
                    deposit_address,
                    deposit_amount_atomic,
                    expires_at,
                    raw_json,
                    from_network,
                    to_network,
                    from_txid,
                    to_txid,
                ),
            )
            conn.commit()
            return int(cursor.lastrowid)

    def get_swap(self, swap_id: int, user_id: int) -> Optional[dict]:
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM swaps WHERE id = ? AND user_id = ?",
                (swap_id, user_id),
            ).fetchone()
            return dict(row) if row else None

    def list_swaps(self, user_id: int, limit: int = 50) -> list[dict]:
        with self.get_connection() as conn:
            rows = conn.execute(
                """
                SELECT * FROM swaps WHERE user_id = ?
                ORDER BY created_at DESC LIMIT ?
                """,
                (user_id, limit),
            ).fetchall()
            return [dict(r) for r in rows]

    def update_swap_txids(
        self,
        swap_id: int,
        user_id: int,
        *,
        from_txid: Optional[str] = None,
        to_txid: Optional[str] = None,
        status: Optional[str] = None,
    ) -> Optional[dict]:
        row = self.get_swap(swap_id, user_id)
        if not row:
            return None
        fields: list[str] = []
        values: list = []
        if from_txid is not None:
            fields.append("from_txid = ?")
            values.append(from_txid.strip() or None)
        if to_txid is not None:
            fields.append("to_txid = ?")
            values.append(to_txid.strip() or None)
        if status is not None:
            fields.append("status = ?")
            values.append(status)
        if not fields:
            return row
        values.extend([swap_id, user_id])
        with self.get_connection() as conn:
            conn.execute(
                f"UPDATE swaps SET {', '.join(fields)} WHERE id = ? AND user_id = ?",
                values,
            )
            conn.commit()
        return self.get_swap(swap_id, user_id)

    def update_swap_status(
        self,
        swap_id: int,
        user_id: int,
        status: str,
        *,
        settled_at: Optional[str] = None,
        provider_ref: Optional[str] = None,
    ) -> bool:
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                UPDATE swaps
                SET status = ?, settled_at = COALESCE(?, settled_at),
                    provider_ref = COALESCE(?, provider_ref)
                WHERE id = ? AND user_id = ?
                """,
                (status, settled_at, provider_ref, swap_id, user_id),
            )
            conn.commit()
            return cursor.rowcount > 0
