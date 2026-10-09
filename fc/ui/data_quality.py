"""Halaman Kualitas Data - laporan validasi (BRD 5.5) dan kamus data (BRD 5.4)."""
import pandas as pd
import streamlit as st

from ..pipeline import Dataset
from ..schema import SHEETS

_LEVEL = {"required": "Wajib", "kpi": "Untuk KPI", "optional": "Opsional"}


# ==================== CSS GLASSMORPHISM ====================
GLASS_CSS = """
<style>
.dq-glass {
    position: relative;
    background: linear-gradient(135deg, #FFFFFF 0%, #F5F3FF 100%);
    border: 1px solid rgba(196, 181, 253, 0.5);
    border-radius: 16px;
    padding: 16px 18px;
    box-shadow: 0 6px 20px rgba(139, 92, 246, 0.08);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    overflow: hidden;
    min-height: 100px;
    margin-bottom: 8px;
}
.dq-glass::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, var(--accent, #8B5CF6) 0%, #EC4899 100%);
}
.dq-glass:hover {
    transform: translateY(-3px);
    box-shadow: 0 16px 32px rgba(139, 92, 246, 0.18);
    border-color: rgba(139, 92, 246, 0.6);
}
.dq-glass-label {
    color: #6D28D9;
    font-weight: 700;
    font-size: 0.66rem;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    margin-bottom: 6px;
}
.dq-glass-value {
    color: #0F172A;
    font-weight: 800;
    font-size: 1.45rem;
    letter-spacing: -0.5px;
    line-height: 1.1;
    margin-bottom: 4px;
}
.dq-glass-note {
    color: #94A3B8;
    font-size: 0.68rem;
    font-style: italic;
    line-height: 1.3;
}
.dq-glass-delta {
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.3px;
}

/* Banner */
.dq-banner {
    background: linear-gradient(135deg, #0F172A 0%, #1E1B4B 100%);
    border-radius: 16px;
    padding: 20px 26px;
    color: white;
    box-shadow: 0 12px 32px rgba(30, 27, 75, 0.25);
    border: 1px solid rgba(139, 92, 246, 0.3);
    margin-bottom: 20px;
    position: relative;
    overflow: hidden;
    display: flex;
    gap: 30px;
    flex-wrap: wrap;
    align-items: center;
}
.dq-banner::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 4px;
    background: linear-gradient(90deg, var(--b-accent, #10B981) 0%, #EC4899 100%);
}
.dq-block { flex: 1; min-width: 160px; }
.dq-block-label {
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    margin-bottom: 6px;
}
.dq-block-value {
    font-size: 1.8rem;
    font-weight: 900;
    color: #FFFFFF;
    letter-spacing: -1px;
    line-height: 1.1;
    margin-bottom: 2px;
}
.dq-block-sub {
    font-size: 0.75rem;
    color: #94A3B8;
}
</style>
"""


def _inject_css():
    st.markdown(GLASS_CSS, unsafe_allow_html=True)


# ==================== HELPERS ====================
def _glass_card(col, label: str, value: str, accent: str = "#8B5CF6",
                note: str = None, delta: str = None,
                delta_color: str = None) -> None:
    note_html = f'<div class="dq-glass-note">{note}</div>' if note else ""
    delta_html = ""
    if delta:
        c = delta_color or "#10B981"
        delta_html = f'<div class="dq-glass-delta" style="color:{c};">{delta}</div>'
    html = (
        f'<div class="dq-glass" style="--accent: {accent};">'
        f'<div class="dq-glass-label">{label}</div>'
        f'<div class="dq-glass-value">{value}</div>'
        f'{delta_html}'
        f'{note_html}'
        f'</div>'
    )
    col.markdown(html, unsafe_allow_html=True)


def _compute_quality_stats(ds: Dataset):
    """Hitung statistik kualitas data dari report."""
    rep = ds.report

    total_rows = 0
    total_sheets = 0
    rows_rejected = 0

    try:
        summary = rep.summary_frame()
        total_sheets = len(summary)

        # Cari kolom jumlah baris (case-insensitive)
        row_col = None
        for c in summary.columns:
            if any(k in str(c).lower() for k in ("rows", "baris", "total")):
                row_col = c
                break
        if row_col is not None:
            total_rows = int(pd.to_numeric(summary[row_col], errors="coerce").fillna(0).sum())
    except Exception:
        pass

    # Ambil rows_rejected langsung dari report (atribut)
    try:
        rows_rejected = int(getattr(rep, "rows_rejected", 0) or 0)
    except Exception:
        rows_rejected = 0

    if total_rows == 0 and rows_rejected == 0:
        total_rows = 1  # hindari divide by zero, tidak dipakai untuk display bila 0

    valid_rows = max(0, total_rows - rows_rejected)
    quality_score = (valid_rows / total_rows * 100) if total_rows > 0 else 100.0

    return {
        "total_rows": total_rows,
        "total_sheets": total_sheets,
        "rows_rejected": rows_rejected,
        "valid_rows": valid_rows,
        "quality_score": quality_score,
    }


# ==================== KPI CARDS + BANNER ====================
def _render_kpi(ds: Dataset):
    stats = _compute_quality_stats(ds)

    score = stats["quality_score"]
    rejected = stats["rows_rejected"]

    if score >= 99 and rejected == 0:
        status = "Excellent"
        color = "#10B981"
    elif score >= 95:
        status = "Good"
        color = "#8B5CF6"
    elif score >= 85:
        status = "Warning"
        color = "#F59E0B"
    else:
        status = "Critical"
        color = "#EF4444"

    st.markdown("### 📊 Ringkasan Kualitas Data")

    c1, c2, c3, c4 = st.columns(4)
    _glass_card(c1, "Total Baris", f"{stats['total_rows']:,}", "#8B5CF6",
                note=f"{stats['total_sheets']} sheet terbaca")
    _glass_card(c2, "Baris Valid", f"{stats['valid_rows']:,}", "#10B981",
                note="Lolos validasi")
    _glass_card(c3, "Baris Ditolak", f"{rejected:,}",
                "#EF4444" if rejected > 0 else "#10B981",
                delta=("⚠️ Perlu perbaikan" if rejected > 0 else "✅ Bersih"),
                delta_color=("#EF4444" if rejected > 0 else "#10B981"))
    _glass_card(c4, "Quality Score", f"{score:.1f}%", color,
                delta=f"Status: {status}",
                delta_color=color)

    # Banner
    html = (
        f'<div class="dq-banner" style="--b-accent: {color};">'
        f'<div class="dq-block">'
        f'<div class="dq-block-label" style="color:{color};">📋 STATUS KUALITAS</div>'
        f'<div class="dq-block-value">{status}</div>'
        f'<div class="dq-block-sub">Quality Score {score:.1f}%</div>'
        f'</div>'
        f'<div class="dq-block">'
        f'<div class="dq-block-label" style="color:#A78BFA;">📁 SHEET TERBACA</div>'
        f'<div class="dq-block-value">{stats["total_sheets"]}</div>'
        f'<div class="dq-block-sub">Sumber data</div>'
        f'</div>'
        f'<div class="dq-block">'
        f'<div class="dq-block-label" style="color:#A78BFA;">⚠️ BARIS DITOLAK</div>'
        f'<div class="dq-block-value">{rejected}</div>'
        f'<div class="dq-block-sub">Dari total {stats["total_rows"]:,} baris</div>'
        f'</div>'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


# ==================== ISSUES ====================
def render_issues(ds: Dataset) -> None:
    rep = ds.report

    st.markdown("#### 📋 Ringkasan per Sheet")
    try:
        st.dataframe(rep.summary_frame(), use_container_width=True, hide_index=True)
    except Exception as e:
        st.info(f"Ringkasan tidak tersedia: {e}")

    st.markdown("#### 🔍 Temuan Validasi")
    try:
        frame = rep.to_frame()
        if frame.empty:
            st.success("✅ Tidak ada temuan. Seluruh data lolos validasi.")
        else:
            st.dataframe(frame, use_container_width=True, hide_index=True)
    except Exception as e:
        st.info(f"Detail temuan tidak tersedia: {e}")


def render_blocking(ds: Dataset) -> None:
    _inject_css()
    st.error(
        "Data tidak dapat dipakai. Tidak ada angka yang ditampilkan sampai "
        "masalah berikut diperbaiki (sistem tidak memakai data pengganti)."
    )
    render_issues(ds)


# ==================== MAIN ====================
def render(ds: Dataset) -> None:
    _inject_css()

    st.title("🧪 Kualitas Data")
    st.caption(f"Sumber: {ds.report.source_label} · Dibaca: {ds.report.loaded_at}")

    # KPI + Banner
    _render_kpi(ds)

    st.markdown("---")

    # Ringkasan & temuan
    render_issues(ds)

    st.markdown("---")

    # Kamus data
    st.markdown("#### 📚 Kamus Data")
    st.caption(
        "Struktur kolom yang diharapkan. Kolom 'Untuk KPI' tidak memblokir "
        "pembacaan, tetapi KPI terkait akan tampil 'Data tidak tersedia' "
        "bila kolom tidak ada."
    )
    rows = [{"Sheet": sh.name, "Kolom": c.name, "Tipe": c.kind, "Satuan": c.unit,
             "Level": _LEVEL[c.level], "Dipakai untuk": c.feeds or sh.module}
            for sh in SHEETS for c in sh.columns]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)