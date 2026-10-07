"""Decidiq - entry point (Tahap 1A: fondasi data & KPI).

Jalankan:  streamlit run app.py
"""
import io
import os

import pandas as pd
import streamlit as st

from fc import audit
from fc.config import DEFAULT_DATA_FILE
from fc.connectors import ExcelConnector, MemoryConnector
from fc.demo import make_demo_frames
from fc.kpi import Scope
from fc.pipeline import Dataset, load_dataset
from fc.ui import (
    auth, styles,
    dashboard, data_quality, audit_trail,
    production_analysis, cost_analysis,
    manufacturing_variance, inventory_analysis, risk_register,
    multi_plant, predictive_analytics,
    executive_report, ai_copilot,
    multi_agent_collaboration, ai_factory_os,
    cost_dna, what_if, recommendations,
    settings, memory,
)

st.set_page_config(page_title="Decidiq", layout="wide")
styles.inject()

# Inisialisasi DB audit (sekali saja)
try:
    from fc import db
    db.init_db()
except Exception as e:
    st.error(f"Gagal inisialisasi database audit: {e}")

auth.require_login()

def _is_demo_path(path: str) -> bool:
    if not path:
        return False
    return any(h in os.path.basename(path).lower() for h in ("demo", "sample", "contoh"))


@st.cache_data(show_spinner="Membaca dan memvalidasi data...")
def _load_file(path: str, mtime: float, is_demo: bool) -> Dataset:
    return load_dataset(ExcelConnector(path), is_demo=is_demo)


@st.cache_data(show_spinner="Membaca dan memvalidasi data...")
def _load_upload(content: bytes, name: str) -> Dataset:
    return load_dataset(ExcelConnector(io.BytesIO(content), label=name),
                        is_demo=_is_demo_path(name))


@st.cache_data(show_spinner="Menyiapkan data demo...")
def _load_demo() -> Dataset:
    return load_dataset(MemoryConnector(make_demo_frames(), label="DEMO DATA"), is_demo=True)


# ---------- sidebar ----------
role = st.session_state["role"]
st.sidebar.title("🎛 Control Panel")
st.sidebar.markdown(f"👤 **User:** `{st.session_state['username']}`")
st.sidebar.markdown(f"🛡 **Role:** `{role}`")
if st.sidebar.button("🚪 Keluar / Logout"):
    auth.logout()
st.sidebar.markdown("---")
menu = st.sidebar.radio("Navigation", auth.ROLE_MENUS[role])

st.sidebar.markdown("---")
st.sidebar.subheader("🗂 Sumber Data")
mode = st.sidebar.radio("Sumber", ["File Excel", "Unggah Excel", "Mode Demo"],
                        label_visibility="collapsed")
if st.sidebar.button("🔄 Refresh data"):
    audit.log("refresh_data")
    st.cache_data.clear()
    st.rerun()

if mode == "File Excel":
    path = st.sidebar.text_input("Path file", DEFAULT_DATA_FILE)
    ds = _load_file(path,
                    os.path.getmtime(path) if os.path.exists(path) else 0.0,
                    _is_demo_path(path))
elif mode == "Unggah Excel":
    up = st.sidebar.file_uploader("Pilih file .xlsx", type=["xlsx"])
    if up is None:
        st.info("Unggah file Excel di sidebar untuk memulai.")
        st.stop()
    ds = _load_upload(up.getvalue(), up.name)
else:
    ds = _load_demo()

# Log sumber data sekali per sesi
if st.session_state.get("_last_source") != ds.report.source_label:
    st.session_state["_last_source"] = ds.report.source_label
    st.session_state["_last_ds_label"] = ds.report.source_label
    audit.log("load_data", {
        "source": ds.report.source_label,
        "is_demo": ds.is_demo,
        "rows_rejected": ds.report.rows_rejected,
        "ok": ds.ok,
    })

# ---------- status data ----------
if ds.is_demo:
    st.warning("🧪 **DEMO DATA** - angka di bawah adalah data contoh, bukan data pabrik Anda.")
if not ds.ok:
    st.title("🧪 Kualitas Data")
    data_quality.render_blocking(ds)
    st.stop()
if ds.report.rows_rejected:
    st.warning(f"⚠️ {ds.report.rows_rejected} baris data ditolak oleh validasi. "
               "Lihat menu **Kualitas Data**.")

# ---------- filter global ----------
st.sidebar.markdown("---")
st.sidebar.subheader("📅 Periode Analisis")

# Preset periode
span = ds.date_span()
if span is not None:
    lo, hi = span
    
    preset = st.sidebar.radio(
        "Pilih Periode",
        ["Semua Data", "30 Hari Terakhir", "Bulan Ini", "Bulan Lalu", "Custom"],
        index=0,
        label_visibility="collapsed",
        key="period_preset",
    )
    
    from datetime import date, timedelta
    today = hi  # Pakai tanggal terakhir data, bukan hari ini
    
    if preset == "Semua Data":
        start, end = lo, hi
    elif preset == "30 Hari Terakhir":
        start = max(lo, today - timedelta(days=30))
        end = hi
    elif preset == "Bulan Ini":
        start = max(lo, date(today.year, today.month, 1))
        end = hi
    elif preset == "Bulan Lalu":
        # Bulan lalu
        first_this_month = date(today.year, today.month, 1)
        last_month_end = first_this_month - timedelta(days=1)
        start = max(lo, date(last_month_end.year, last_month_end.month, 1))
        end = last_month_end
    else:  # Custom
        dr = st.sidebar.date_input(
            "Pilih tanggal",
            value=(lo, hi),
            min_value=lo,
            max_value=hi,
            key="custom_date",
        )
        if isinstance(dr, (tuple, list)) and len(dr) == 2:
            start, end = dr[0], dr[1]
        elif isinstance(dr, (tuple, list)) and len(dr) == 1:
            start = end = dr[0]
        else:
            start = end = dr
    
    # Tampilkan periode aktif
    st.sidebar.caption(f"📆 Aktif: **{start}** s/d **{end}**")
else:
    start = end = None

# Filter Plant & Line
st.sidebar.markdown("---")
st.sidebar.subheader("🏭 Filter Plant & Line")

plants = ds.plants()
plant = st.sidebar.selectbox("Pilih Plant", ["Semua"] + plants) if plants else "Semua"
lines = ds.lines(None if plant == "Semua" else plant)
line = st.sidebar.selectbox("Pilih Lini Produksi", ["Semua"] + lines) if lines else "Semua"

scope = Scope(
    None if plant == "Semua" else plant,
    None if line == "Semua" else line,
    start, end,
)
# Muat targets dari DB — sesuaikan dengan filter tanggal aktif
try:
    from fc.settings import get_active_targets
    st.session_state["_targets"] = get_active_targets(scope)
except Exception:
    pass

# ---------- routing ----------
if menu == "Dashboard":
    dashboard.render(ds, scope)
elif menu == "Kualitas Data":
    data_quality.render(ds)
elif menu == "Audit Trail":
    audit_trail.render(ds, scope)
elif menu == "Cost DNA":
    cost_dna.render(ds, scope)
elif menu == "What-If Simulator":
    what_if.render(ds, scope)
elif menu == "Recommendations":
    recommendations.render(ds, scope)
elif menu == "Production Analysis":
    production_analysis.render(ds, scope)
elif menu == "Cost Analysis":
    cost_analysis.render(ds, scope)
elif menu == "Multi-Plant & Cost Allocation":
    multi_plant.render(ds, scope)
elif menu == "Manufacturing Variance":
    manufacturing_variance.render(ds, scope)
elif menu == "Inventory Analysis":
    inventory_analysis.render(ds, scope)
elif menu == "Risk Register":
    risk_register.render(ds, scope)
elif menu == "Predictive Analytics":
    predictive_analytics.render(ds, scope)
elif menu == "Executive Report":
    executive_report.render(ds, scope)
elif menu == "AI Copilot":
    ai_copilot.render(ds, scope)
elif menu == "Multi-Agent Collaboration":
    multi_agent_collaboration.render(ds, scope)
elif menu == "AI Factory OS (Phase 5)":
    ai_factory_os.render(ds, scope)
elif menu == "Settings":
    settings.render(ds, scope)
elif menu == "Memory":
    memory.render(ds, scope)
else:
    st.title(menu)
    st.info(f"Halaman '{menu}' belum dimigrasi ke struktur baru.")
    if ds.production is not None:
        st.dataframe(ds.production.head(50))