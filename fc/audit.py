"""Wrapper audit trail untuk Streamlit.

Memudahkan pencatatan aksi user tanpa harus panggil db.py langsung.
Auto-init DB pada import pertama.
"""
import functools
from typing import Any, Dict, Optional

import streamlit as st

from . import db


# Auto-init DB saat modul di-import (idempotent)
_INITIALIZED = False


def _ensure_init() -> None:
    global _INITIALIZED
    if not _INITIALIZED:
        try:
            db.init_db()
            _INITIALIZED = True
        except Exception as e:
            st.error(f"Gagal inisialisasi database: {e}")


def _current_user() -> str:
    return st.session_state.get("username", "anonymous")


def _current_source() -> str:
    ds = st.session_state.get("_last_ds_label", "")
    return ds


def log(action: str, details: Optional[Dict[str, Any]] = None) -> None:
    """Catat aksi user saat ini."""
    _ensure_init()
    try:
        db.log_action(
            action=action,
            user=_current_user(),
            details=details or {},
            source_label=_current_source(),
        )
    except Exception as e:
        # Jangan sampai logging error menghentikan aplikasi
        print(f"[audit] Gagal log '{action}': {e}")


def log_login(username: str, role: str) -> None:
    _ensure_init()
    try:
        db.log_action(
            action="login",
            user=username,
            details={"role": role},
        )
    except Exception as e:
        print(f"[audit] Gagal log login: {e}")


def log_logout(username: str) -> None:
    _ensure_init()
    try:
        db.log_action(action="logout", user=username)
    except Exception as e:
        print(f"[audit] Gagal log logout: {e}")


def log_export(format_: str, filename: str = "") -> None:
    log("export", {"format": format_, "filename": filename})


def log_chat(question: str, answer: str) -> None:
    log("chat", {"question": question[:200], "answer_preview": answer[:200]})


def log_config_change(key: str, old: Any, new: Any) -> None:
    log("config_change", {"key": key, "old": old, "new": new})


def log_decision(recommendation: str, decision: str, notes: str = "") -> int:
    _ensure_init()
    try:
        return db.log_decision(
            recommendation=recommendation,
            decision=decision,
            user=_current_user(),
            notes=notes,
        )
    except Exception as e:
        print(f"[audit] Gagal log decision: {e}")
        return -1


def track(action: str):
    """Decorator untuk auto-track fungsi."""
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            log(action)
            return fn(*args, **kwargs)
        return wrapper
    return decorator


# ==== Helper untuk UI ====

def get_recent_logs(limit: int = 50) -> list:
    _ensure_init()
    try:
        return db.get_audit_log(limit=limit)
    except Exception:
        return []


def get_stats() -> Dict[str, int]:
    _ensure_init()
    try:
        return {
            "total_audit": db.count_rows("audit_log"),
            "total_decisions": db.count_rows("decisions"),
            "total_model_runs": db.count_rows("model_runs"),
        }
    except Exception:
        return {"total_audit": 0, "total_decisions": 0, "total_model_runs": 0}