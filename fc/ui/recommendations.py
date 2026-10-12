"""Halaman Recommendation Engine (DARK + Format Indonesia)."""
import math

import pandas as pd
import streamlit as st

from .. import audit
from ..config import TARGETS as DEFAULT_TARGETS
from ..intel.recommend import generate_recommendations
from ..kpi import Scope, summarize
from ..pipeline import Dataset


def _fmt_thousand(v, decimals: int = 0) -> str:
    try:
        if v is None: return "—"
        f = float(v)
        if math.isnan(f) or math.isinf(f): return "—"
        return f"{f:,.0f}".replace(",", ".")
    except (ValueError, TypeError):
        return str(v) if v is not None else "—"


def _fmt_rp(v, compact: bool = True) -> str:
    try:
        if v is None: return "—"
        f = float(v)
        if math.isnan(f) or math.isinf(f): return "—"
        if compact:
            if abs(f) >= 1_000_000_000:
                return "Rp " + f"{f/1_000_000_000:.2f}".replace(".", ",") + " M"
            if abs(f) >= 1_000_000:
                return "Rp " + f"{f/1_000_000:.1f}".replace(".", ",") + " jt"
        return "Rp " + f"{f:,.0f}".replace(",", ".")
    except (ValueError, TypeError):
        return str(v) if v is not None else "—"


# ==================== CSS (DARK) ====================
GLASS_CSS = """
<style>
.rc-glass {
    position: relative;
    background: linear-gradient(145deg, #1a1d3d, #151933);
    border: 1px solid #343858;
    border-radius: 12px;
    padding: 16px 18px;
    box-shadow: 0 9px 30px rgba(6, 9, 23, 0.13);
    transition: transform 0.2s ease, border-color 0.2s ease;
    overflow: hidden;
    min-height: 110px;
    margin-bottom: 8px;
}
.rc-glass::before {
    content: '';
    position: absolute;
    top: 0; left: 17px;
    width: 35px; height: 3px;
    background: var(--accent, #a489ff);
    border-radius: 0 0 5px 5px;
}
.rc-glass:hover {
    transform: translateY(-2px);
    border-color: #8c79d7;
    box-shadow: 0 10px 24px rgba(8, 8, 33, 0.45);
}
.rc-glass-label {
    color: #b8bedb;
    font-weight: 600;
    font-size: 0.62rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 6px;
}
.rc-glass-value {
    color: #ffffff;
    font-weight: 800;
    font-size: 1.4rem;
    letter-spacing: -0.04em;
    line-height: 1.15;
    margin-bottom: 4px;
}
.rc-glass-note {
    color: #8793bc;
    font-size: 0.68rem;
    line-height: 1.3;
    margin-top: 6px;
}

.rc-banner {
    background: linear-gradient(110deg, #30265e, #211b47 55%, #171b3c);
    border: 1px solid #5e5090;
    border-radius: 16px;
    padding: 22px 28px;
    color: #ffffff;
    box-shadow: 0 9px 30px rgba(6, 9, 23, 0.13);
    margin-bottom: 20px;
    position: relative;
    overflow: hidden;
}
.rc-banner::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 4px;
    background: linear-gradient(90deg, #a489ff 0%, #71d5e9 100%);
}
.rc-banner-label {
    font-size: 0.62rem;
    font-weight: 800;
    letter-spacing: 0.12em;
    color: #c9b9f8;
    text-transform: uppercase;
    margin-bottom: 8px;
}
.rc-banner-value {
    font-size: 2rem;
    font-weight: 800;
    color: #ffffff;
    letter-spacing: -0.04em;
    line-height: 1.1;
    margin-bottom: 6px;
}
.rc-banner-desc {
    font-size: 0.85rem;
    color: #dce0f4;
}
.rc-banner-desc strong { color: #f7d578; }

.rec-card {
    background: #1b1e3e;
    border: 1px solid #343858;
    border-radius: 14px;
    padding: 22px 24px;
    margin-bottom: 18px;
    box-shadow: 0 9px 30px rgba(6, 9, 23, 0.13);
    transition: all 0.25s ease;
    position: relative;
}
.rec-card:hover {
    transform: translateY(-2px);
    border-color: #8c79d7;
}
.rec-badge {
    display: inline-block;
    font-size: 0.62rem;
    font-weight: 800;
    letter-spacing: 0.06em;
    padding: 4px 10px;
    border-radius: 6px;
    margin-bottom: 8px;
    text-transform: uppercase;
}
.rec-title {
    font-size: 1.1rem;
    font-weight: 700;
    color: #f5f6ff;
    line-height: 1.3;
    letter-spacing: -0.02em;
}
.rec-meta {
    font-size: 0.7rem;
    color: #c4aaff;
    font-weight: 600;
    margin-top: 6px;
    letter-spacing: 0.03em;
}
.rec-savings {
    text-align: right;
    color: #ffffff;
    padding: 12px 18px;
    border-radius: 12px;
    min-width: 140px;
}
.rec-savings-label {
    font-size: 0.6rem;
    letter-spacing: 0.08em;
    opacity: 0.9;
    font-weight: 700;
}
.rec-savings-value {
    font-size: 1.25rem;
    font-weight: 800;
    letter-spacing: -0.03em;
    margin-top: 2px;
}
.rec-context {
    font-size: 0.85rem;
    color: #dce0f4;
    line-height: 1.55;
    margin-top: 14px;
    padding: 12px 14px;
    background: #242748;
    border-radius: 8px;
    border: 1px solid #343858;
}
.rec-context strong { color: #a489ff; }

.rec-step {
    padding: 10px 14px;
    margin: 6px 0;
    background: linear-gradient(90deg, #242748 0%, #1a1d3d 100%);
    border-left: 3px solid #a489ff;
    border-radius: 6px;
    font-size: 0.85rem;
    color: #dce0f4;
}
.rec-step-num {
    color: #c4aaff;
    font-weight: 700;
}
</style>
"""


def _inject_css():
    st.markdown(GLASS_CSS, unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def _cached_summarize(ds: Dataset, scope: Scope):
    return summarize(ds, scope)


@st.cache_data(show_spinner=False)
def _cached_recommendations(ds: Dataset, scope: Scope, targets):
    s = summarize(ds, scope)
    return generate_recommendations(ds, s, targets)


def _active_targets():
    return st.session_state.get("_targets") or DEFAULT_TARGETS


def _severity_color(severity: str) -> dict:
    palette = {
        "high": {"border": "#ff9eaa", "bg": "#35243a", "icon": "🔴", "label": "PRIORITAS TINGGI"},
        "medium": {"border": "#f7d578", "bg": "#302b30", "icon": "🟡", "label": "PRIORITAS SEDANG"},
        "info": {"border": "#71d5e9", "bg": "#242748", "icon": "🔵", "label": "INFORMASI"},
    }
    return palette.get(severity, palette["info"])


def _glass_card(col, label: str, value: str, accent: str = "#a489ff",
                note: str = None) -> None:
    note_html = f'<div class="rc-glass-note">{note}</div>' if note else ""
    html = (
        f'<div class="rc-glass" style="--accent: {accent};">'
        f'<div class="rc-glass-label">{label}</div>'
        f'<div class="rc-glass-value">{value}</div>'
        f'{note_html}'
        f'</div>')
    col.markdown(html, unsafe_allow_html=True)


def _render_rec_card(rec, index: int) -> None:
    style = _severity_color(rec.severity)
    icon = style["icon"]
    savings_label = 'HEMAT/TAHUN' if rec.annual_rp > 0 else 'CASH RECOVERY'
    savings_value = (
        _fmt_rp(rec.annual_rp) if rec.annual_rp > 0
        else _fmt_rp(rec.monthly_rp))

    html = (
        f'<div class="rec-card" style="border-left: 5px solid {style["border"]};">'
        f'<div style="display:flex; justify-content:space-between; align-items:start;">'
        f'<div style="flex:1;">'
        f'<div class="rec-badge" style="background:{style["bg"]}; color:{style["border"]}; border:1px solid {style["border"]};">{style["label"]}</div>'
        f'<div class="rec-title">{icon} #{index} — {rec.title}</div>'
        f'<div class="rec-meta">KATEGORI: {rec.category.upper()} · KEYAKINAN: {rec.confidence_pct}%</div>'
        f'</div>'
        f'<div class="rec-savings" style="background: linear-gradient(135deg, #713DEA 0%, #8B5CF6 100%);">'
        f'<div class="rec-savings-label">{savings_label}</div>'
        f'<div class="rec-savings-value">{savings_value}</div>'
        f'</div>'
        f'</div>'
        f'<div class="rec-context"><strong>Konteks:</strong> {rec.context}</div>'
        f'</div>')
    st.markdown(html, unsafe_allow_html=True)

    with st.expander(f"📋 Lihat langkah konkret & aksi", expanded=False):
        st.markdown("**Langkah yang harus dilakukan:**")
        for i, step in enumerate(rec.steps, 1):
            st.markdown(
                f'<div class="rec-step">'
                f'<span class="rec-step-num">{i}.</span> {step}'
                f'</div>', unsafe_allow_html=True)

        st.caption(f"📎 Sumber data: {rec.data_source}")
        st.markdown("")
        col_a, col_b, col_c = st.columns([1, 1, 3], gap="medium")

        with col_a:
            if st.button("✅ Setujui", key=f"approve_{index}",
                         type="primary", width='stretch'):
                audit.log_decision(
                    recommendation=rec.title, decision="approved",
                    notes=f"Impact: {_fmt_rp(rec.annual_rp, False)}/tahun, Confidence: {rec.confidence_pct}%")
                st.success(f"✅ Rekomendasi #{index} disetujui & tercatat di audit trail.")

        with col_b:
            if st.button("❌ Tolak", key=f"reject_{index}", width='stretch'):
                audit.log_decision(
                    recommendation=rec.title, decision="rejected",
                    notes="Ditolak oleh user")
                st.info(f"Rekomendasi #{index} ditolak.")

        with col_c:
            st.caption("Keputusan tercatat permanen di database.")


def render(ds: Dataset, scope: Scope) -> None:
    _inject_css()
    st.title("🎯 Priority Actions")
    st.caption("Action plan otomatis dengan Financial Impact terukur. "
               "Setiap keputusan disimpan untuk Institutional Memory (BRD 8).")

    targets = _active_targets()
    st.caption(f"🎯 Target aktif: Yield ≥ {targets.yield_min:g}% · "
               f"Scrap ≤ {targets.scrap_max:g}% · OEE ≥ {targets.oee_min:g}%")

    with st.spinner("🧠 Menganalisis rekomendasi..."):
        s = _cached_summarize(ds, scope)
        recs = _cached_recommendations(ds, scope, targets)

    if not recs:
        st.success("✅ Tidak ada rekomendasi saat ini. Semua KPI dalam target.")
        return

    total_annual = sum(r.annual_rp for r in recs if r.annual_rp > 0)
    total_cash = sum(r.monthly_rp for r in recs if r.annual_rp == 0)
    high_count = sum(1 for r in recs if r.severity == "high")

    c1, c2, c3, c4 = st.columns(4, gap="medium")
    _glass_card(c1, "Total Rekomendasi", str(len(recs)), "#a489ff",
                note="Action items terdeteksi")
    _glass_card(c2, "🔴 Prioritas Tinggi", str(high_count),
                "#ff9eaa" if high_count > 0 else "#77edb4",
                note="Perlu aksi segera")
    _glass_card(c3, "💰 Cost Saving Tahunan", _fmt_rp(total_annual),
                "#77edb4", note="Potensi penghematan")
    _glass_card(c4, "💵 Cash Recovery",
                _fmt_rp(total_cash) if total_cash else "—",
                "#f7d578", note="One-time recovery")

    if high_count > 0:
        html = (
            f'<div class="rc-banner">'
            f'<div class="rc-banner-label">🎯 PRIORITY ACTIONS — ACTION REQUIRED</div>'
            f'<div class="rc-banner-value">{_fmt_rp(total_annual)}</div>'
            f'<div class="rc-banner-desc">'
            f'Potensi penghematan tahunan dari <strong>{len(recs)} rekomendasi</strong>. '
            f'<strong>{high_count} item</strong> berprioritas TINGGI dan perlu tindakan segera.'
            f'</div></div>')
        st.markdown(html, unsafe_allow_html=True)
    else:
        html = (
            f'<div class="rc-banner">'
            f'<div class="rc-banner-label">🎯 PRIORITY ACTIONS</div>'
            f'<div class="rc-banner-value">{_fmt_rp(total_annual)}</div>'
            f'<div class="rc-banner-desc">'
            f'Potensi penghematan tahunan dari <strong>{len(recs)} rekomendasi</strong>. '
            f'Tidak ada item berprioritas tinggi saat ini.'
            f'</div></div>')
        st.markdown(html, unsafe_allow_html=True)

    st.markdown("---")

    with st.expander("ℹ️ Cara kerja Recommendation Engine"):
        st.markdown(
            "Engine menganalisis:\n"
            "- **Cost Alert aktif** (Yield, Scrap, OEE, Cost, Utility)\n"
            "- **Data inventory** (stock-out, slow-moving, dead stock)\n"
            "- **Data produksi** (performa aktual)\n\n"
            "Setiap rekomendasi menyertakan:\n"
            "- **Estimasi Cost Saving**\n"
            "- **Tingkat keyakinan** (confidence 0-100%)\n"
            "- **Langkah konkret**\n\n"
            "Sesuai **BRD 8**, setiap rekomendasi membutuhkan persetujuan manusia "
            "(human-in-the-loop) dan tercatat permanen di audit trail.")

    st.markdown("---")
    st.subheader(f"📋 Daftar Rekomendasi (diurutkan prioritas)")
    for i, rec in enumerate(recs, 1):
        _render_rec_card(rec, i)

    st.markdown("---")
    st.info("💡 **Tips:** Klik **Setujui** untuk rekomendasi yang akan dieksekusi. "
            "Keputusan tercatat permanen di menu **Audit Trail**.")