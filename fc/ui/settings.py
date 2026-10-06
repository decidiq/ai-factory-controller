"""Halaman Pengaturan Target KPI — bisa diubah dari UI (BRD 4)."""
import datetime

import pandas as pd
import streamlit as st

from .. import audit, settings as settings_mgr
from ..pipeline import Dataset


def _render_current_vs_default(setting_key: str, current_val, default_val) -> str:
    """Bandingkan nilai sekarang vs default."""
    try:
        if abs(float(current_val) - float(default_val)) < 1e-9:
            return "= default"
        return f"default: {default_val}"
    except (TypeError, ValueError):
        return ""


def render(ds: Dataset, scope) -> None:
    st.title("⚙️ Pengaturan Target KPI")
    st.caption(
        "Ubah target tanpa sentuh kode. Semua perubahan tercatat di audit trail "
        "dan langsung berlaku ke seluruh aplikasi."
    )

    # ---- Info user ----
    username = st.session_state.get("username", "system")
    st.info(f"👤 Login sebagai: **{username}**")

    # ---- Ambil nilai saat ini & default ----
    current = settings_mgr.get_current_dict()

    # ---- Grouping untuk UI ----
    OPERATIONAL_KEYS = ["target_yield", "target_scrap", "target_oee"]
    COST_KEYS = ["max_cost_per_kg", "utility_share_max", "variance_tolerance_pct"]
    INVENTORY_KEYS = ["slow_moving_days"]

    new_values = {}

    # ============ OPERASIONAL ============
    st.subheader("📊 Target Operasional")
    st.caption("Target untuk Yield, Scrap, dan OEE — dipakai di Dashboard, Alert, dan Executive Report.")

    cols = st.columns(3)
    for i, key in enumerate(OPERATIONAL_KEYS):
        meta = settings_mgr.SETTING_META[key]
        with cols[i]:
            val = st.number_input(
                meta["label"],
                min_value=float(meta["min"]),
                max_value=float(meta["max"]),
                value=float(current.get(key, meta["default"])),
                step=0.1,
                help=meta["help"],
                key=f"input_{key}",
            )
            new_values[key] = val
            if abs(val - meta["default"]) > 1e-9:
                st.caption(f"⚡ Berbeda dari default ({meta['default']})")

    st.markdown("---")

    # ============ BIAYA ============
    st.subheader("💰 Target Biaya")
    st.caption("Batas dan toleransi untuk pengendalian biaya produksi.")

    cols = st.columns(3)
    for i, key in enumerate(COST_KEYS):
        meta = settings_mgr.SETTING_META[key]
        with cols[i]:
            step = 100_000 if "cost" in key else 0.1
            val = st.number_input(
                meta["label"],
                min_value=float(meta["min"]),
                max_value=float(meta["max"]),
                value=float(current.get(key, meta["default"])),
                step=float(step),
                help=meta["help"],
                key=f"input_{key}",
            )
            new_values[key] = val
            if abs(val - meta["default"]) > 1e-9:
                st.caption(f"⚡ Berbeda dari default ({meta['default']})")

    st.markdown("---")

    # ============ INVENTORY ============
    st.subheader("📦 Target Inventory")
    st.caption("Threshold untuk klasifikasi slow-moving inventory.")

    cols = st.columns(3)
    for i, key in enumerate(INVENTORY_KEYS):
        meta = settings_mgr.SETTING_META[key]
        with cols[i]:
            val = st.number_input(
                meta["label"],
                min_value=int(meta["min"]),
                max_value=int(meta["max"]),
                value=int(current.get(key, meta["default"])),
                step=1,
                help=meta["help"],
                key=f"input_{key}",
            )
            new_values[key] = val
            if abs(val - meta["default"]) > 1e-9:
                st.caption(f"⚡ Berbeda dari default ({meta['default']})")

    st.markdown("---")

    # ============ AKSI ============
    st.subheader("💾 Simpan Perubahan")

    col_save, col_reset, col_info = st.columns([1, 1, 2])

    with col_save:
        if st.button("💾 Simpan", type="primary", use_container_width=True):
            changes = settings_mgr.save_targets(new_values, user=username)
            if changes:
                st.success(f"✅ {len(changes)} perubahan disimpan. Berlaku ke seluruh aplikasi.")
                with st.expander("Lihat detail perubahan"):
                    for c in changes:
                        st.markdown(f"- `{c}`")
                st.rerun()
            else:
                st.info("Tidak ada perubahan untuk disimpan.")

    with col_reset:
        if st.button("🔄 Reset ke Default", use_container_width=True):
            settings_mgr.reset_targets(user=username)
            st.success("✅ Semua target dikembalikan ke default.")
            st.rerun()

    with col_info:
        st.caption(
            "Perubahan langsung dipakai di Dashboard, Alert, Executive Report, "
            "Recommendation Engine, dan Predictive Analytics."
        )

    # ============ PREVIEW DAMPAK ============
    with st.expander("🔍 Preview — Target Sekarang vs Default"):
        preview_rows = []
        for key, meta in settings_mgr.SETTING_META.items():
            field = settings_mgr.SETTING_TO_FIELD[key]
            cur_val = current.get(key, meta["default"])
            default_val = meta["default"]
            is_changed = abs(cur_val - default_val) > 1e-9
            preview_rows.append({
                "Setting": meta["label"],
                "Nilai Sekarang": cur_val,
                "Default": default_val,
                "Status": "⚡ Diubah" if is_changed else "✅ Default",
            })
        st.dataframe(pd.DataFrame(preview_rows), use_container_width=True, hide_index=True)

    st.markdown("---")

    # ============ RIWAYAT ============
    st.subheader("📜 Riwayat Perubahan Target")
    st.caption("Setiap perubahan tercatat permanen di audit trail.")

    history = settings_mgr.get_settings_history(limit=20)

    if not history:
        st.info("Belum ada perubahan. Semua nilai masih default.")
        return

    rows = []
    for h in history:
        try:
            import json as _json
            details = _json.loads(h.get("details", "{}"))
            changes_list = details.get("changes", [])
            changes_str = " · ".join(changes_list) if changes_list else "-"
        except Exception:
            changes_str = "-"

        rows.append({
            "Waktu": h.get("timestamp", ""),
            "User": h.get("user", ""),
            "Perubahan": changes_str,
        })

    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)