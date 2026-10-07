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


# ==================== HELPER FUNCTIONS ====================

def _render_template_prompt():
    """Halaman download template — dipakai di mode 'Unggah Excel' kalau belum upload."""
    try:
        from fc.template import generate_template
    except Exception as e:
        st.error(f"Template tidak tersedia: {e}")
        return

    st.title("📤 Upload File Excel Anda")
    st.markdown(
        "### Belum punya file Excel?\n"
        "Download **template Excel** dulu → isi dengan data pabrik → upload kembali."
    )
    st.markdown("---")
    st.markdown("### 📋 Format Template — 11 Sheet")
    st.markdown(
        "| # | Sheet | Isi |\n"
        "|---|-------|-----|\n"
        "| 1 | **Production** | Data produksi harian |\n"
        "| 2 | **Raw_Material** | Material, Cost, Qty_Kg |\n"
        "| 3 | **Packaging** | Biaya kemasan |\n"
        "| 4 | **Direct_Labor** | Biaya tenaga kerja |\n"
        "| 5 | **Utility** | Biaya listrik, air |\n"
        "| 6 | **Maintenance** | Biaya pemeliharaan |\n"
        "| 7 | **Depreciation** | Penyusutan bulanan |\n"
        "| 8 | **Budget** | Budget vs Actual |\n"
        "| 9 | **Inventory** | Stok material |\n"
        "| 10 | **Risk_Register** | Daftar risiko |\n"
        "| 11 | **Config** | Target KPI (opsional) |\n"
    )
    st.info(
        "💡 **Kolom WAJIB:** Date, Machine, Output_Kg (Production); "
        "Material, Cost, Qty_Kg (Raw_Material). Kolom lain opsional."
    )
    st.markdown("---")

    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        template_bytes = generate_template()
        st.download_button(
            label="📄 Download Template Excel",
            data=template_bytes,
            file_name="decidiq_template.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            type="primary",
            key="tmpl_main_download",
        )
    st.stop()


def _render_sidebar_template_button():
    """Tombol download template kecil di sidebar — dipakai di beberapa mode."""
    st.sidebar.markdown("**📥 Belum punya file Excel?**")
    try:
        from fc.template import generate_template
        st.sidebar.download_button(
            label="📄 Download Template",
            data=generate_template(),
            file_name="decidiq_template.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            key="sidebar_tmpl_dl",
        )
    except Exception:
        pass
    st.sidebar.markdown("---")


def _is_demo_path(path: str) -> bool:
    if not path:
        return False
    return any(h in os.path.basename(path).lower()
               for h in ("demo", "sample", "contoh"))


@st.cache_data(show_spinner="Membaca dan memvalidasi data...")
def _load_file(path: str, mtime: float, is_demo: bool) -> Dataset:
    return load_dataset(ExcelConnector(path), is_demo=is_demo)


@st.cache_data(show_spinner="Membaca dan memvalidasi data...")
def _load_upload(content: bytes, name: str) -> Dataset:
    return load_dataset(ExcelConnector(io.BytesIO(content), label=name),
                        is_demo=_is_demo_path(name))


@st.cache_data(show_spinner="Menyiapkan data demo...")
def _load_demo() -> Dataset:
    return load_dataset(MemoryConnector(make_demo_frames(), label="DEMO DATA"),
                        is_demo=True)


# ==================== SIDEBAR ====================

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

# Label radio HARUS sama persis dengan kondisi if-elif di bawah
mode = st.sidebar.radio(
    "Sumber",
    ["📁 Path File Excel", "📤 Unggah Excel", "🧪 Mode Demo"],
    label_visibility="collapsed",
    key="data_mode",
)

if st.sidebar.button("🔄 Refresh data"):
    audit.log("refresh_data")
    st.cache_data.clear()
    st.rerun()

st.sidebar.markdown("---")


# ==================== MODE SELECTION ====================

if mode == "📁 Path File Excel":
    # Text input untuk path file
    _render_sidebar_template_button()

    path = st.sidebar.text_input("Path file", DEFAULT_DATA_FILE)
    ds = _load_file(
        path,
        os.path.getmtime(path) if os.path.exists(path) else 0.0,
        _is_demo_path(path),
    )

elif mode == "📤 Unggah Excel":
    # File uploader + prompt template
    _render_sidebar_template_button()

    up = st.sidebar.file_uploader("📤 Pilih file .xlsx", type=["xlsx"],
                                   key="upload_main")
    if up is None:
        _render_template_prompt()  # ⬅️ panggil helper, tidak duplikat
    ds = _load_upload(up.getvalue(), up.name)

else:  # Mode Demo
    ds = _load_demo()


# ==================== STATUS DATA ====================

if ds.is_demo:
    st.warning("🧪 **DEMO DATA** - angka di bawah adalah data contoh, bukan data pabrik Anda.")

if not ds.ok:
    st.title("🧪 Kualitas Data")
    data_quality.render_blocking(ds)
    st.stop()

if ds.report.rows_rejected:
    st.warning(f"⚠️ {ds.report.rows_rejected} baris data ditolak oleh validasi. "
               "Lihat menu **Kualitas Data**.")


# ==================== FILTER GLOBAL ====================

st.sidebar.markdown("---")
st.sidebar.subheader("📅 Periode Analisis")

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
    today = hi

    if preset == "Semua Data":
        start, end = lo, hi
    elif preset == "30 Hari Terakhir":
        start = max(lo, today - timedelta(days=30))
        end = hi
    elif preset == "Bulan Ini":
        start = max(lo, date(today.year, today.month, 1))
        end = hi
    elif preset == "Bulan Lalu":
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


# ==================== ROUTING ====================

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