"""Settings manager — target KPI yang bisa diubah dari UI (BRD 4).

Membaca/menyimpan target dari database (app_settings table).
Fallback ke DEFAULT_TARGETS dari config jika belum diatur.

Semua perubahan tercatat di audit trail (siapa, kapan, dari apa ke apa).
"""
from dataclasses import replace
from typing import Dict, List, Optional

from . import db
from .config import DEFAULT_TARGETS, Targets


# Mapping nama setting (di DB) → nama field di Targets
SETTING_TO_FIELD = {
    "target_yield": "yield_min",
    "target_scrap": "scrap_max",
    "target_oee": "oee_min",
    "utility_share_max": "utility_share_max",
    "slow_moving_days": "slow_moving_days",
    "variance_tolerance_pct": "variance_tolerance_pct",
    "max_cost_per_kg": "max_cost_per_kg",
}

# Metadata untuk UI (label, tipe, batas)
SETTING_META = {
    "target_yield": {
        "label": "Target Yield (%)",
        "type": "float", "min": 0.0, "max": 100.0,
        "default": DEFAULT_TARGETS.yield_min,
        "help": "Yield minimum yang dianggap sehat",
    },
    "target_scrap": {
        "label": "Target Scrap (%)",
        "type": "float", "min": 0.0, "max": 100.0,
        "default": DEFAULT_TARGETS.scrap_max,
        "help": "Scrap maksimum yang masih dapat diterima",
    },
    "target_oee": {
        "label": "Target OEE (%)",
        "type": "float", "min": 0.0, "max": 100.0,
        "default": DEFAULT_TARGETS.oee_min,
        "help": "OEE minimum yang dianggap sehat",
    },
    "utility_share_max": {
        "label": "Utility Share Max (%)",
        "type": "float", "min": 0.0, "max": 100.0,
        "default": DEFAULT_TARGETS.utility_share_max,
        "help": "Porsi biaya utilitas maksimum terhadap COGM",
    },
    "slow_moving_days": {
        "label": "Slow-Moving Threshold (hari)",
        "type": "int", "min": 1, "max": 365,
        "default": DEFAULT_TARGETS.slow_moving_days,
        "help": "Hari untuk kategorikan inventory slow-moving",
    },
    "variance_tolerance_pct": {
        "label": "Variance Tolerance (%)",
        "type": "float", "min": 0.0, "max": 50.0,
        "default": DEFAULT_TARGETS.variance_tolerance_pct,
        "help": "Toleransi variance biaya vs budget",
    },
    "max_cost_per_kg": {
        "label": "Max Cost/Kg (Rp)",
        "type": "float", "min": 0.0, "max": 1_000_000_000.0,
        "default": DEFAULT_TARGETS.max_cost_per_kg,
        "help": "Batas atas Cost/Kg — 0 = tidak aktif",
    },
}


def get_targets() -> Targets:
    """Baca target dari DB, fallback ke default.

    Returns:
        Targets dengan nilai yang sudah di-override dari DB.
    """
    try:
        db.init_db()
        raw = db.get_all_settings()
    except Exception:
        return DEFAULT_TARGETS

    if not raw:
        return DEFAULT_TARGETS

    kwargs = {}
    for setting_key, field_name in SETTING_TO_FIELD.items():
        if setting_key in raw:
            try:
                meta = SETTING_META.get(setting_key, {})
                v_type = meta.get("type", "float")
                if v_type == "int":
                    kwargs[field_name] = int(float(raw[setting_key]))
                else:
                    kwargs[field_name] = float(raw[setting_key])
            except (ValueError, TypeError):
                pass

    if not kwargs:
        return DEFAULT_TARGETS

    return replace(DEFAULT_TARGETS, **kwargs)


def save_targets(new_values: Dict[str, float],
                 user: str = "system") -> List[str]:
    """Simpan perubahan target. Return list perubahan untuk audit.

    Args:
        new_values: {"target_yield": 98.5, ...}
        user: username yang melakukan perubahan

    Returns:
        List string ["target_yield: 98.0 → 98.5", ...] untuk audit log
    """
    db.init_db()
    current = get_targets()
    changes = []

    payload = {}
    for setting_key, new_val in new_values.items():
        if setting_key not in SETTING_TO_FIELD:
            continue

        field_name = SETTING_TO_FIELD[setting_key]
        old_val = getattr(current, field_name, None)

        # Skip kalau tidak ada perubahan
        try:
            if old_val is not None and abs(float(old_val) - float(new_val)) < 1e-9:
                continue
        except (TypeError, ValueError):
            pass

        payload[setting_key] = str(new_val)
        changes.append(f"{setting_key}: {old_val} → {new_val}")

    if payload:
        db.set_settings_bulk(payload, user=user)
        # Log ke audit
        try:
            db.log_action(
                action="settings_changed",
                user=user,
                details={"changes": changes},
            )
        except Exception:
            pass

    return changes


def reset_targets(user: str = "system") -> None:
    """Reset semua target ke default."""
    db.init_db()
    current = get_targets()
    changes = []
    for setting_key, field_name in SETTING_TO_FIELD.items():
        old_val = getattr(current, field_name, None)
        default_val = getattr(DEFAULT_TARGETS, field_name, None)
        if old_val != default_val:
            changes.append(f"{setting_key}: {old_val} → {default_val}")

    # Hapus semua setting
    try:
        with db.get_conn() as conn:
            conn.execute("DELETE FROM app_settings")
    except Exception:
        pass

    if changes:
        try:
            db.log_action(
                action="settings_reset",
                user=user,
                details={"changes": changes},
            )
        except Exception:
            pass


def get_settings_history(limit: int = 20) -> List[Dict]:
    """Ambil riwayat perubahan settings dari audit log."""
    try:
        rows = db.get_audit_log(limit=limit, action="settings_changed")
        return rows
    except Exception:
        return []


def get_current_dict() -> Dict[str, float]:
    """Ambil nilai setting saat ini sebagai dict (untuk form prefill)."""
    t = get_targets()
    return {
        setting_key: getattr(t, field_name, 0)
        for setting_key, field_name in SETTING_TO_FIELD.items()
    }