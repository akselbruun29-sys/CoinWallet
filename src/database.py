"""SQLite database for wallet platform."""
import logging
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

USER_ROLES = ("admin", "user", "pending")

logger = logging.getLogger(__name__)


class WalletDatabase:
    """SQLite wrapper for users, wallets, and audit data."""

    def __init__(self, db_path: Optional[str] = None):
        import os

        self.db_path = Path(db_path or os.getenv("WALLET_DB", "wallet.db"))
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

        if "encryption_version" not in wallet_cols:
            conn.execute(
                "ALTER TABLE wallets ADD COLUMN encryption_version INTEGER DEFAULT 1"
            )

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
                SELECT wallet_key_salt, wallet_key_verifier
                FROM users WHERE id = ?
                """,
                (user_id,),
            ).fetchone()
            if not row:
                return None
            return {
                "wallet_key_salt": row["wallet_key_salt"],
                "wallet_key_verifier": row["wallet_key_verifier"],
            }

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

    def list_wallets(self, user_id: int) -> list[dict]:
        with self.get_connection() as conn:
            rows = conn.execute(
                """
                SELECT id, user_id, name, xpub, derivation_path, network,
                       receive_index, last_synced_height, encryption_version, created_at
                FROM wallets WHERE user_id = ?
                ORDER BY created_at ASC
                """,
                (user_id,),
            ).fetchall()
            return [dict(r) for r in rows]

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
                """
                SELECT id, user_id, name, xpub, derivation_path, network,
                       receive_index, last_synced_height, created_at
                FROM wallets WHERE id = ? AND user_id = ?
                """,
                (wallet_id, user_id),
            ).fetchone()
            return dict(row) if row else None

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
    ) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO wallets (
                    user_id, name, network, xpub, encrypted_seed,
                    derivation_path, encryption_version
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    name,
                    network,
                    xpub,
                    encrypted_seed,
                    derivation_path,
                    encryption_version,
                ),
            )
            conn.commit()
            return cursor.lastrowid

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
        }
        with self.get_connection() as conn:
            rows = conn.execute("SELECT key, value FROM system_settings").fetchall()
            stored = {r["key"]: r["value"] for r in rows}
        return {**defaults, **stored}
