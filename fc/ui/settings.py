"""Halaman Pengaturan Target KPI — global + per periode (BRD 4)."""
import datetime

import pandas as pd
import streamlit as st

from .. import audit, settings as settings_mgr
from ..pipeline import Dataset


# ==================== CSS ====================
GLASS_CSS = """
<style>
.set-banner {
    background: linear-gradient(135deg, #0F172A 0%, #1E1B4B 60%, #4C1D95 100%);
    border-radius: 16px;
    padding: 24px 30px;
    color: white;
    box-shadow: 0 12px 32px rgba(30, 27, 75, 0.25);
    border: 1px solid rgba(139, 92, 246, 0.3);
    margin-bottom: 20px;
    position: relative;
    overflow: hidden;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 20px;
    flex-wrap: wrap;
}
.set-banner::before {
    content: '';
    position: absolute;
    top: -80px; right: -80px;
    width: 260px; height: 260px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(139, 92, 246, 0.35) 0%, transparent 70%);
    pointer-events: none;
}
.set-banner-label {
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 1.5px;
    color: #A78BFA;
    text-transform: uppercase;
    margin-bottom: 8px;
    position: relative;
    z-index: 1;
}
.set-banner-title {
    font-size: 1.6rem;
    font-weight: 900;
    color: #FFFFFF;
    letter-spacing: -0.6px;
    line-height: 1.15;
    margin-bottom: 6px;
    position: relative;
    z-index: 1;
}
.set-banner-desc {
    font-size: 0.88rem;
    color: #C4B5FD;
    line-height: 1.5;
    max-width: 600px;
    position: relative;
    z-index: 1;
}
.set-user-badge {
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(167, 139, 250, 0.4);
    border-radius: 12px;
    padding: 12px 18px;
    text-align: right;
    position: relative;
    z-index: 1;
    min-width: 200px;
}
.set-user-label {
    font-size: 0.66rem;
    letter-spacing: 1.2px;
    color: #A78BFA;
    text-transform: uppercase;
    font-weight: 700;
    margin-bottom: 4px;
}
.set-user-name {
    font-size: 1rem;
    font-weight: 800;
    color: #FFFFFF;
    letter-spacing: -0.3px;
}

/* Section header */
.set-section {
    color: #6D28D9;
    font-size: 0.72rem;
    font-weight: 800;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    padding: 10px 0 6px 0;
    border-bottom: 2px solid #E9D5FF;
    margin: 20px 0 14px 0;
    position: relative;
}
.set-section::after {
    content: '';
    position: absolute;
    bottom: -2px; left: 0;
    width: 60px; height: 2px;
    background: linear-gradient(90deg, #8B5CF6 0%, #EC4899 100%);
}
</style>
"""


def _inject_css():
    st.markdown(GLASS_CSS, unsafe_allow_html=True)


# ==================== BANNER ====================
def _render_banner(username: str):
    html = (
        f'<div class="set-banner">'
        f'<div>'
        f'<div class="set-banner-label">⚙️ PENGATURAN TARGET KPI</div>'
        f'<div class="set-banner-title">Kelola target tanpa sentuh kode</div>'
        f'<div class="set-banner-desc">'
        f'Ubah target operasional, biaya, dan inventory. '
        f'Semua perubahan tercatat otomatis di <strong>audit trail</strong> untuk '
        f'transparansi dan governance.'
        f'</div>'
        f'</div>'
        f'<div class="set-user-badge">'
        f'<div class="set-user-label">LOGIN SEBAGAI</div>'
        f'<div class="set-user-name">👤 {username}</div>'
        f'</div>'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


# ==================== GLOBAL TARGETS ====================
def _render_global_targets(username: str) -> None:
    st.markdown(
        '<div class="set-section">🌍 TARGET GLOBAL (DEFAULT)</div>',
        unsafe_allow_html=True,
    )
    st.caption(
        "Target ini berlaku untuk semua periode, kecuali di-override oleh Target per Periode."
    )

    current = settings_mgr.get_current_dict()

    OPERATIONAL_KEYS = ["target_yield", "target_scrap", "target_oee"]
    COST_KEYS = ["max_cost_per_kg", "utility_share_max", "variance_tolerance_pct"]
    INVENTORY_KEYS = ["slow_moving_days"]

    new_values = {}

    # Operasional
    st.markdown("##### 🎯 Target Operasional")
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
                key=f"glob_{key}",
            )
            new_values[key] = val

    # Biaya
    st.markdown("##### 💰 Target Biaya")
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
                key=f"glob_{key}",
            )
            new_values[key] = val

    # Inventory
    st.markdown("##### 📦 Target Inventory")
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
                key=f"glob_{key}",
            )
            new_values[key] = val

    st.markdown("")
    col_save, col_reset, col_info = st.columns([1, 1, 2])

    with col_save:
        if st.button("💾 Simpan Global", type="primary",
                     use_container_width=True, key="save_global"):
            changes = settings_mgr.save_targets(new_values, user=username)
            if changes:
                st.success(f"✅ {len(changes)} perubahan disimpan.")
                with st.expander("Lihat detail"):
                    for c in changes:
                        st.markdown(f"- `{c}`")
                st.rerun()
            else:
                st.info("ℹ️ Tidak ada perubahan.")

    with col_reset:
        if st.button("🔄 Reset ke Default", use_container_width=True,
                     key="reset_global"):
            settings_mgr.reset_targets(user=username)
            st.success("✅ Semua target global dikembalikan ke default.")
            st.rerun()

    with col_info:
        st.caption("Global target berlaku sebagai default.")


# ==================== PERIOD TARGETS ====================
def _render_period_targets(username: str) -> None:
    st.markdown(
        '<div class="set-section">📅 TARGET PER PERIODE</div>',
        unsafe_allow_html=True,
    )
    st.caption("Definisikan target spesifik untuk range bulan tertentu.")

    periods = settings_mgr.list_target_periods()

    if periods:
        st.markdown("**Target Periode Aktif:**")
        for p in periods:
            _render_period_card(p, username)
    else:
        st.info("Belum ada target periode. Tambahkan di bawah.")

    st.markdown("---")
    st.markdown("##### ➕ Tambah Target Periode Baru")

    col1, col2 = st.columns(2)

    bulan_options = [f"2026-{m:02d}" for m in range(1, 13)] + \
                     [f"2027-{m:02d}" for m in range(1, 13)]

    with col1:
        period_start = st.selectbox("Dari Bulan", bulan_options, index=0,
                                     key="new_period_start")
    with col2:
        period_end = st.selectbox("Sampai Bulan", bulan_options, index=2,
                                   key="new_period_end")

    if period_start > period_end:
        st.error("'Dari Bulan' harus lebih kecil atau sama dengan 'Sampai Bulan'.")
        return

    st.markdown("**Target untuk Periode Ini:**")

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        val_yield = st.number_input("Target Yield (%)", 0.0, 100.0, 98.0, 0.1,
                                     key="new_period_yield")
    with col_b:
        val_scrap = st.number_input("Target Scrap (%)", 0.0, 100.0, 2.0, 0.1,
                                     key="new_period_scrap")
    with col_c:
        val_oee = st.number_input("Target OEE (%)", 0.0, 100.0, 85.0, 0.1,
                                   key="new_period_oee")

    col_d, col_e = st.columns(2)
    with col_d:
        val_cost = st.number_input("Max Cost/Kg (Rp)", 0.0, 1e9, 12500.0, 500.0,
                                    key="new_period_cost")
    with col_e:
        reason = st.text_input("Alasan (opsional)",
                                placeholder="mis. Q1 2026",
                                key="new_period_reason")

    if st.button("💾 Simpan Target Periode", type="primary", key="save_period"):
        values = {
            "target_yield": val_yield,
            "target_scrap": val_scrap,
            "target_oee": val_oee,
            "max_cost_per_kg": val_cost,
        }
        try:
            settings_mgr.save_target_period(
                period_start=period_start,
                period_end=period_end,
                values=values,
                user=username,
                reason=reason,
            )
            st.success(f"✅ Target periode {period_start} - {period_end} disimpan.")
            st.rerun()
        except Exception as e:
            st.error(f"Gagal menyimpan: {e}")


def _render_period_card(p: dict, username: str) -> None:
    with st.container(border=True):
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"**📅 {p['period_start']} s/d {p['period_end']}**")
            if p.get("reason"):
                st.caption(f"Alasan: {p['reason']}")
            if p.get("created_by"):
                st.caption(f"Dibuat oleh: {p['created_by']} - {p.get('created_at', '')}")
        with col2:
            if st.button("🗑️ Hapus",
                         key=f"del_{p['period_start']}_{p['period_end']}",
                         use_container_width=True):
                settings_mgr.delete_target_period(
                    p["period_start"], p["period_end"], user=username)
                st.rerun()

        params = p.get("parameters", {})
        if params:
            cols = st.columns(min(len(params), 4))
            for i, (k, v) in enumerate(params.items()):
                meta = settings_mgr.SETTING_META.get(k, {})
                label = meta.get("label", k)
                unit = meta.get("unit", "")
                with cols[i % len(cols)]:
                    if unit == "Rp":
                        st.metric(label, f"Rp {v:,.0f}")
                    elif unit == "%":
                        st.metric(label, f"{v:.1f}%")
                    else:
                        st.metric(label, f"{v}")


# ==================== HISTORY ====================
def _render_history() -> None:
    st.markdown(
        '<div class="set-section">📜 RIWAYAT PERUBAHAN TARGET</div>',
        unsafe_allow_html=True,
    )
    history = settings_mgr.get_settings_history(limit=20)
    if not history:
        st.info("Belum ada perubahan target.")
        return
    rows = []
    for h in history:
        try:
            import json as _json
            details = _json.loads(h.get("details", "{}"))
            changes_list = details.get("changes", [])
            changes_str = " · ".join(changes_list) if changes_list else "—"
        except Exception:
            changes_str = "—"
        rows.append({
            "Waktu": h.get("timestamp", ""),
            "User": h.get("user", ""),
            "Aksi": h.get("action", ""),
            "Perubahan": changes_str,
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


# ==================== MAIN ====================
def render(ds: Dataset, scope) -> None:
    _inject_css()

    st.title("⚙️ Pengaturan Target KPI")

    username = st.session_state.get("username", "system")
    _render_banner(username)

    tab1, tab2, tab3 = st.tabs([
        "🌍 Target Global",
        "📅 Target per Periode",
        "📜 Riwayat",
    ])

    with tab1:
        _render_global_targets(username)
    with tab2:
        _render_period_targets(username)
    with tab3:
        _render_history()