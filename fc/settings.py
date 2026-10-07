"""Settings manager — target KPI global & per periode (BRD 4 + 6)."""
from dataclasses import replace
from typing import Dict, List, Optional

from . import db
from .config import DEFAULT_TARGETS, Targets


SETTING_TO_FIELD = {
    "target_yield": "yield_min",
    "target_scrap": "scrap_max",
    "target_oee": "oee_min",
    "utility_share_max": "utility_share_max",
    "slow_moving_days": "slow_moving_days",
    "variance_tolerance_pct": "variance_tolerance_pct",
    "max_cost_per_kg": "max_cost_per_kg",
}

SETTING_META = {
    "target_yield": {"label": "Target Yield (%)", "type": "float", "min": 0.0, "max": 100.0,
                     "default": DEFAULT_TARGETS.yield_min, "help": "Yield minimum", "unit": "%"},
    "target_scrap": {"label": "Target Scrap (%)", "type": "float", "min": 0.0, "max": 100.0,
                     "default": DEFAULT_TARGETS.scrap_max, "help": "Scrap maksimum", "unit": "%"},
    "target_oee": {"label": "Target OEE (%)", "type": "float", "min": 0.0, "max": 100.0,
                   "default": DEFAULT_TARGETS.oee_min, "help": "OEE minimum", "unit": "%"},
    "utility_share_max": {"label": "Utility Share Max (%)", "type": "float", "min": 0.0, "max": 100.0,
                          "default": DEFAULT_TARGETS.utility_share_max, "help": "Porsi utilitas max", "unit": "%"},
    "slow_moving_days": {"label": "Slow-Moving Threshold (hari)", "type": "int", "min": 1, "max": 365,
                         "default": DEFAULT_TARGETS.slow_moving_days, "help": "Batas slow-moving", "unit": "hari"},
    "variance_tolerance_pct": {"label": "Variance Tolerance (%)", "type": "float", "min": 0.0, "max": 50.0,
                               "default": DEFAULT_TARGETS.variance_tolerance_pct, "help": "Toleransi variance", "unit": "%"},
    "max_cost_per_kg": {"label": "Max Cost/Kg (Rp)", "type": "float", "min": 0.0, "max": 1_000_000_000.0,
                        "default": DEFAULT_TARGETS.max_cost_per_kg, "help": "Batas atas Cost/Kg", "unit": "Rp"},
}


def get_targets() -> Targets:
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


def save_targets(new_values: Dict[str, float], user: str = "system") -> List[str]:
    db.init_db()
    current = get_targets()
    changes = []
    payload = {}
    for setting_key, new_val in new_values.items():
        if setting_key not in SETTING_TO_FIELD:
            continue
        field_name = SETTING_TO_FIELD[setting_key]
        old_val = getattr(current, field_name, None)
        try:
            if old_val is not None and abs(float(old_val) - float(new_val)) < 1e-9:
                continue
        except (TypeError, ValueError):
            pass
        payload[setting_key] = str(new_val)
        changes.append(f"{setting_key}: {old_val} to {new_val}")
    if payload:
        db.set_settings_bulk(payload, user=user)
        try:
            db.log_action(action="settings_changed", user=user,
                          details={"changes": changes})
        except Exception:
            pass
    return changes


def reset_targets(user: str = "system") -> None:
    db.init_db()
    try:
        with db.get_conn() as conn:
            conn.execute("DELETE FROM app_settings")
    except Exception:
        pass
    try:
        db.log_action(action="settings_reset", user=user, details={})
    except Exception:
        pass


def get_settings_history(limit: int = 20) -> List[Dict]:
    try:
        return db.get_audit_log(limit=limit, action="settings_changed")
    except Exception:
        return []


def get_current_dict() -> Dict[str, float]:
    t = get_targets()
    return {k: getattr(t, f, 0) for k, f in SETTING_TO_FIELD.items()}


def get_targets_for_date(target_date: Optional[str]) -> Targets:
    global_targets = get_targets()
    if not target_date:
        return global_targets
    try:
        overrides = db.get_targets_for_date(target_date)
    except Exception:
        return global_targets
    if not overrides:
        return global_targets
    kwargs = {}
    for param_key, value in overrides.items():
        field_name = SETTING_TO_FIELD.get(param_key)
        if field_name:
            kwargs[field_name] = value
    if not kwargs:
        return global_targets
    return replace(global_targets, **kwargs)


def list_target_periods() -> List[Dict]:
    try:
        rows = db.get_targets_by_period()
    except Exception:
        return []
    periods = {}
    for r in rows:
        key = (r["period_start"], r["period_end"])
        if key not in periods:
            periods[key] = {
                "period_start": r["period_start"],
                "period_end": r["period_end"],
                "reason": r.get("reason", "") or "",
                "created_by": r.get("created_by", "") or "",
                "created_at": r.get("created_at", "") or "",
                "parameters": {},
            }
        periods[key]["parameters"][r["parameter"]] = r["value"]
    result = list(periods.values())
    result.sort(key=lambda x: x["period_start"])
    return result


def save_target_period(period_start: str, period_end: str,
                       values: Dict[str, float],
                       user: str = "system", reason: str = "") -> None:
    if not period_start or not period_end:
        raise ValueError("Periode harus diisi")
    if period_start > period_end:
        raise ValueError("Tanggal mulai harus <= tanggal akhir")
    db.init_db()
    db.save_target_period_bulk(period_start, period_end, values,
                                user=user, reason=reason)
    try:
        db.log_action(action="target_period_saved", user=user,
                      details={"period": f"{period_start} - {period_end}",
                               "values": values, "reason": reason})
    except Exception:
        pass


def delete_target_period(period_start: str, period_end: str,
                         user: str = "system") -> None:
    db.init_db()
    db.delete_target_period(period_start, period_end)
    try:
        db.log_action(action="target_period_deleted", user=user,
                      details={"period": f"{period_start} - {period_end}"})
    except Exception:
        pass


# ==================== ACTIVE TARGETS BY SCOPE ====================

def get_active_targets(scope) -> Targets:
    """Ambil target aktif berdasarkan scope filter (tanggal/periode).

    Logic:
      1. Ambil reference date dari scope (pakai scope.end, fallback scope.start)
      2. Kalau ada target periode untuk bulan itu → pakai
      3. Kalau tidak → fallback ke global

    Dipakai di app.py untuk auto-load target sesuai filter user.
    """
    global_targets = get_targets()

    if scope is None:
        return global_targets

    # Ambil reference date
    ref_date = None
    try:
        if getattr(scope, "end", None):
            end = scope.end
            ref_date = end.strftime("%Y-%m") if hasattr(end, "strftime") else str(end)[:7]
        elif getattr(scope, "start", None):
            start = scope.start
            ref_date = start.strftime("%Y-%m") if hasattr(start, "strftime") else str(start)[:7]
    except Exception:
        pass

    if not ref_date:
        return global_targets

    return get_targets_for_date(ref_date)