"""Database SQLite untuk audit trail permanen (BRD 7).

Menyimpan:
  - audit_log           : semua aksi user
  - decisions           : keputusan user
  - model_runs          : log prediksi
  - users               : akun user
  - app_settings        : konfigurasi global
  - targets_by_period   : target KPI per periode (Factory Accounting)
"""
import hashlib
import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional

DB_PATH = os.environ.get("AFC_DB_PATH", "data/afc.db")
PBKDF2_ITERATIONS = 200_000


def _ensure_dir():
    d = os.path.dirname(DB_PATH)
    if d and not os.path.exists(d):
        os.makedirs(d, exist_ok=True)


@contextmanager
def get_conn():
    _ensure_dir()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    """Buat tabel jika belum ada."""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.executescript("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                user TEXT NOT NULL,
                action TEXT NOT NULL,
                details TEXT,
                source_label TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_log(user);
            CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_log(action);
            CREATE INDEX IF NOT EXISTS idx_audit_ts ON audit_log(timestamp);

            CREATE TABLE IF NOT EXISTS decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                user TEXT NOT NULL,
                recommendation TEXT NOT NULL,
                decision TEXT NOT NULL,
                outcome_30d TEXT,
                outcome_60d TEXT,
                outcome_90d TEXT,
                notes TEXT
            );

            CREATE TABLE IF NOT EXISTS model_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                model_name TEXT NOT NULL,
                params TEXT,
                metrics TEXT,
                notes TEXT
            );

            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                role TEXT NOT NULL,
                display_name TEXT,
                created_at TEXT NOT NULL,
                last_login TEXT,
                active INTEGER DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS app_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                updated_by TEXT
            );

            -- ==================== TABEL BARU ====================
            CREATE TABLE IF NOT EXISTS targets_by_period (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                period_start TEXT NOT NULL,
                period_end TEXT NOT NULL,
                parameter TEXT NOT NULL,
                value REAL NOT NULL,
                reason TEXT,
                created_at TEXT NOT NULL,
                created_by TEXT,
                UNIQUE(period_start, period_end, parameter)
            );
            CREATE INDEX IF NOT EXISTS idx_targets_period ON targets_by_period(period_start, period_end);
        """)

        row = cur.execute("SELECT COUNT(*) AS n FROM users").fetchone()
        if row and row["n"] == 0:
            _seed_default_users(cur)


def _seed_default_users(cur) -> None:
    defaults = [
        ("admin", "admin123", "Factory Manager / Plant Controller", "Administrator"),
        ("gm", "gm123", "Director / GM", "General Manager"),
        ("demo", "demo123", "Factory Manager / Plant Controller", "Demo User"),
    ]
    for username, password, role, display in defaults:
        h, s = hash_password(password)
        cur.execute(
            "INSERT INTO users (username, password_hash, salt, role, display_name, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (username, h, s, role, display, datetime.now().isoformat(timespec="seconds")),
        )


# ==================== PASSWORD ====================

def hash_password(password: str, salt: Optional[str] = None) -> tuple:
    if salt is None:
        salt = os.urandom(16).hex()
    h = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"),
                            bytes.fromhex(salt), PBKDF2_ITERATIONS)
    return h.hex(), salt


def verify_password(password: str, password_hash: str, salt: str) -> bool:
    h, _ = hash_password(password, salt)
    return hashlib.compare_digest(h, password_hash)


# ==================== USER ====================

def get_user(username: str) -> Optional[Dict]:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE username = ? AND active = 1", (username,)
        ).fetchone()
        return dict(row) if row else None


def list_users() -> List[Dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT username, role, display_name, created_at, last_login, active "
            "FROM users ORDER BY username"
        ).fetchall()
        return [dict(r) for r in rows]


def create_user(username: str, password: str, role: str, display_name: str = "") -> bool:
    try:
        h, s = hash_password(password)
        with get_conn() as conn:
            conn.execute(
                "INSERT INTO users (username, password_hash, salt, role, display_name, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (username, h, s, role, display_name or username,
                 datetime.now().isoformat(timespec="seconds")),
            )
        return True
    except sqlite3.IntegrityError:
        return False


def update_last_login(username: str) -> None:
    with get_conn() as conn:
        conn.execute("UPDATE users SET last_login = ? WHERE username = ?",
                     (datetime.now().isoformat(timespec="seconds"), username))


# ==================== AUDIT ====================

def log_action(action: str, user: str = "system",
               details: Optional[Dict[str, Any]] = None,
               source_label: str = "") -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO audit_log (timestamp, user, action, details, source_label) "
            "VALUES (?, ?, ?, ?, ?)",
            (datetime.now().isoformat(timespec="seconds"), user, action,
             json.dumps(details or {}, ensure_ascii=False), source_label),
        )


def log_decision(recommendation: str, decision: str,
                 user: str = "system", notes: str = "") -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO decisions (timestamp, user, recommendation, decision, notes) "
            "VALUES (?, ?, ?, ?, ?)",
            (datetime.now().isoformat(timespec="seconds"), user, recommendation, decision, notes),
        )
        return cur.lastrowid


def log_model_run(model_name: str, params: Dict[str, Any],
                  metrics: Dict[str, Any], notes: str = "") -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO model_runs (timestamp, model_name, params, metrics, notes) "
            "VALUES (?, ?, ?, ?, ?)",
            (datetime.now().isoformat(timespec="seconds"), model_name,
             json.dumps(params, ensure_ascii=False),
             json.dumps(metrics, ensure_ascii=False), notes),
        )


def get_audit_log(limit: int = 100, user: Optional[str] = None,
                  action: Optional[str] = None) -> List[Dict]:
    query = "SELECT * FROM audit_log WHERE 1=1"
    params: list = []
    if user:
        query += " AND user = ?"
        params.append(user)
    if action:
        query += " AND action = ?"
        params.append(action)
    query += " ORDER BY id DESC LIMIT ?"
    params.append(limit)
    with get_conn() as conn:
        return [dict(r) for r in conn.execute(query, params).fetchall()]


def get_decisions(limit: int = 100) -> List[Dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM decisions ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]


def count_rows(table: str) -> int:
    allowed = {"audit_log", "decisions", "model_runs", "users",
               "app_settings", "targets_by_period"}
    if table not in allowed:
        raise ValueError(f"Tabel tidak dikenal: {table}")
    with get_conn() as conn:
        row = conn.execute(f"SELECT COUNT(*) AS n FROM {table}").fetchone()
        return row["n"] if row else 0


# ==================== APP SETTINGS (Global) ====================

def get_setting(key: str, default: Optional[str] = None) -> Optional[str]:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT value FROM app_settings WHERE key = ?", (key,)
        ).fetchone()
        return row["value"] if row else default


def get_all_settings() -> Dict[str, str]:
    with get_conn() as conn:
        rows = conn.execute("SELECT key, value FROM app_settings").fetchall()
        return {r["key"]: r["value"] for r in rows}


def set_setting(key: str, value: str, user: str = "system") -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO app_settings (key, value, updated_at, updated_by) "
            "VALUES (?, ?, ?, ?) "
            "ON CONFLICT(key) DO UPDATE SET "
            "value = excluded.value, updated_at = excluded.updated_at, "
            "updated_by = excluded.updated_by",
            (key, value, datetime.now().isoformat(timespec="seconds"), user),
        )


def set_settings_bulk(settings: Dict[str, str], user: str = "system") -> None:
    now = datetime.now().isoformat(timespec="seconds")
    with get_conn() as conn:
        for key, value in settings.items():
            conn.execute(
                "INSERT INTO app_settings (key, value, updated_at, updated_by) "
                "VALUES (?, ?, ?, ?) "
                "ON CONFLICT(key) DO UPDATE SET "
                "value = excluded.value, updated_at = excluded.updated_at, "
                "updated_by = excluded.updated_by",
                (key, str(value), now, user),
            )


def delete_setting(key: str) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM app_settings WHERE key = ?", (key,))


# ==================== TARGETS BY PERIOD (BARU) ====================

def get_targets_by_period() -> List[Dict]:
    """Ambil semua target per periode, diurutkan by tanggal mulai."""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM targets_by_period ORDER BY period_start ASC, parameter ASC"
        ).fetchall()
        return [dict(r) for r in rows]


def get_targets_for_date(target_date: str) -> Dict[str, float]:
    """Ambil target aktif untuk tanggal tertentu (YYYY-MM-DD).

    Return dict: {parameter: value}.
    Kalau ada beberapa range overlap, yang paling terakhir di-set menang.
    """
    if not target_date:
        return {}
    # Ambil format YYYY-MM untuk comparison
    try:
        month_key = target_date[:7]  # '2026-01'
    except Exception:
        return {}

    with get_conn() as conn:
        rows = conn.execute(
            "SELECT parameter, value FROM targets_by_period "
            "WHERE period_start <= ? AND period_end >= ? "
            "ORDER BY created_at DESC",
            (month_key, month_key),
        ).fetchall()

    result = {}
    for r in rows:
        param = r["parameter"]
        if param not in result:  # yang pertama = yang paling baru
            result[param] = float(r["value"])
    return result


def get_target_period(period_start: str, period_end: str) -> Dict[str, float]:
    """Ambil semua parameter target dalam range periode tertentu."""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT parameter, value FROM targets_by_period "
            "WHERE period_start = ? AND period_end = ?",
            (period_start, period_end),
        ).fetchall()
    return {r["parameter"]: float(r["value"]) for r in rows}


def upsert_target_period(period_start: str, period_end: str,
                          parameter: str, value: float,
                          user: str = "system",
                          reason: str = "") -> None:
    """Simpan/update satu target per periode."""
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO targets_by_period "
            "(period_start, period_end, parameter, value, reason, created_at, created_by) "
            "VALUES (?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(period_start, period_end, parameter) DO UPDATE SET "
            "value = excluded.value, reason = excluded.reason, "
            "created_at = excluded.created_at, created_by = excluded.created_by",
            (period_start, period_end, parameter, float(value), reason,
             datetime.now().isoformat(timespec="seconds"), user),
        )


def save_target_period_bulk(period_start: str, period_end: str,
                             values: Dict[str, float],
                             user: str = "system",
                             reason: str = "") -> None:
    """Simpan banyak parameter sekaligus untuk 1 range periode."""
    for param, val in values.items():
        upsert_target_period(period_start, period_end, param, val, user, reason)


def delete_target_period(period_start: str, period_end: str) -> None:
    """Hapus semua target dalam range periode."""
    with get_conn() as conn:
        conn.execute(
            "DELETE FROM targets_by_period WHERE period_start = ? AND period_end = ?",
            (period_start, period_end),
        )


def delete_target_period_param(period_start: str, period_end: str,
                                parameter: str) -> None:
    """Hapus 1 parameter dalam range periode."""
    with get_conn() as conn:
        conn.execute(
            "DELETE FROM targets_by_period "
            "WHERE period_start = ? AND period_end = ? AND parameter = ?",
            (period_start, period_end, parameter),
        )