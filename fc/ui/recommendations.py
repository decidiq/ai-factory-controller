"""Halaman Recommendation Engine — saran aksi konkret dengan impact Rp."""
import pandas as pd
import streamlit as st

from .. import audit
from ..config import TARGETS as DEFAULT_TARGETS
from ..intel.recommend import generate_recommendations
from ..kpi import Scope, summarize
from ..pipeline import Dataset


# ==================== CSS GLASSMORPHISM ====================
GLASS_CSS = """
<style>
.rc-glass {
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
.rc-glass::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, var(--accent, #8B5CF6) 0%, #EC4899 100%);
}
.rc-glass:hover {
    transform: translateY(-3px);
    box-shadow: 0 16px 32px rgba(139, 92, 246, 0.18);
    border-color: rgba(139, 92, 246, 0.6);
}
.rc-glass-label {
    color: #6D28D9;
    font-weight: 700;
    font-size: 0.66rem;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    margin-bottom: 6px;
}
.rc-glass-value {
    color: #0F172A;
    font-weight: 800;
    font-size: 1.4rem;
    letter-spacing: -0.5px;
    line-height: 1.1;
    margin-bottom: 4px;
}
.rc-glass-note {
    color: #94A3B8;
    font-size: 0.68rem;
    font-style: italic;
    line-height: 1.3;
}

/* Banner */
.rc-banner {
    background: linear-gradient(135deg, #0F172A 0%, #1E1B4B 100%);
    border-radius: 16px;
    padding: 22px 28px;
    color: white;
    box-shadow: 0 12px 32px rgba(30, 27, 75, 0.25);
    border: 1px solid rgba(139, 92, 246, 0.3);
    margin-bottom: 20px;
    position: relative;
    overflow: hidden;
}
.rc-banner::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 4px;
    background: linear-gradient(90deg, #8B5CF6 0%, #EC4899 100%);
}
.rc-banner-label {
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 1.5px;
    color: #A78BFA;
    text-transform: uppercase;
    margin-bottom: 8px;
}
.rc-banner-value {
    font-size: 2.2rem;
    font-weight: 900;
    color: #FFFFFF;
    letter-spacing: -1.2px;
    line-height: 1.1;
    margin-bottom: 6px;
}
.rc-banner-desc {
    font-size: 0.88rem;
    color: #C4B5FD;
}
.rc-banner-desc strong { color: #FBBF24; }

/* Recommendation Card */
.rec-card {
    background: #FFFFFF;
    border: 1px solid #E9D5FF;
    border-radius: 14px;
    padding: 22px 24px;
    margin-bottom: 18px;
    box-shadow: 0 4px 16px rgba(139, 92, 246, 0.06), 0 1px 3px rgba(0,0,0,0.03);
    transition: all 0.25s ease;
    position: relative;
}
.rec-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 12px 28px rgba(139, 92, 246, 0.14);
}
.rec-badge {
    display: inline-block;
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.8px;
    padding: 4px 10px;
    border-radius: 6px;
    margin-bottom: 8px;
}
.rec-title {
    font-size: 1.2rem;
    font-weight: 700;
    color: #1E1B4B;
    line-height: 1.3;
    letter-spacing: -0.3px;
}
.rec-meta {
    font-size: 0.72rem;
    color: #6D28D9;
    font-weight: 600;
    margin-top: 6px;
    letter-spacing: 0.3px;
}
.rec-savings {
    text-align: right;
    color: #FFFFFF;
    padding: 12px 18px;
    border-radius: 12px;
    min-width: 140px;
    box-shadow: 0 4px 14px rgba(139, 92, 246, 0.3);
}
.rec-savings-label {
    font-size: 0.62rem;
    letter-spacing: 1px;
    opacity: 0.9;
    font-weight: 600;
}
.rec-savings-value {
    font-size: 1.3rem;
    font-weight: 800;
    letter-spacing: -0.5px;
    margin-top: 2px;
}
.rec-context {
    font-size: 0.9rem;
    color: #475569;
    line-height: 1.55;
    margin-top: 14px;
    padding: 12px 14px;
    background: #F8FAFC;
    border-radius: 8px;
}

/* Step items */
.rec-step {
    padding: 10px 14px;
    margin: 6px 0;
    background: linear-gradient(90deg, #F5F3FF 0%, #FFFFFF 100%);
    border-left: 3px solid #8B5CF6;
    border-radius: 6px;
    font-size: 0.88rem;
    color: #334155;
}
.rec-step-num {
    color: #6D28D9;
    font-weight: 700;
}
</style>
"""


def _inject_css():
    st.markdown(GLASS_CSS, unsafe_allow_html=True)


# ==================== HELPERS ====================
def _active_targets():
    return st.session_state.get("_targets") or DEFAULT_TARGETS


def _severity_color(severity: str) -> dict:
    palette = {
        "high": {"border": "#EF4444", "bg": "#FEF2F2", "icon": "🔴", "label": "PRIORITAS TINGGI"},
        "medium": {"border": "#F59E0B", "bg": "#FFFBEB", "icon": "🟡", "label": "PRIORITAS SEDANG"},
        "info": {"border": "#3B82F6", "bg": "#EFF6FF", "icon": "🔵", "label": "INFORMASI"},
    }
    return palette.get(severity, palette["info"])


def _fmt_rp(v: float) -> str:
    if abs(v) >= 1_000_000_000:
        return f"Rp {v/1_000_000_000:.2f} M"
    if abs(v) >= 1_000_000:
        return f"Rp {v/1_000_000:.1f} jt"
    return f"Rp {v:,.0f}"


def _glass_card(col, label: str, value: str, accent: str = "#8B5CF6",
                note: str = None) -> None:
    note_html = f'<div class="rc-glass-note">{note}</div>' if note else ""
    html = (
        f'<div class="rc-glass" style="--accent: {accent};">'
        f'<div class="rc-glass-label">{label}</div>'
        f'<div class="rc-glass-value">{value}</div>'
        f'{note_html}'
        f'</div>'
    )
    col.markdown(html, unsafe_allow_html=True)


# ==================== REC CARD ====================
def _render_rec_card(rec, index: int) -> None:
    style = _severity_color(rec.severity)
    icon = style["icon"]

    savings_label = 'HEMAT/TAHUN' if rec.annual_rp > 0 else 'CASH RECOVERY'
    savings_value = (
        f"Rp {rec.annual_rp/1_000_000:.1f} jt" if rec.annual_rp > 0
        else f"Rp {rec.monthly_rp/1_000_000:.1f} jt"
    )

    # Card utama (single-line HTML)
    html = (
        f'<div class="rec-card" style="border-left: 5px solid {style["border"]};">'
        f'<div style="display:flex; justify-content:space-between; align-items:start;">'
        f'<div style="flex:1;">'
        f'<div class="rec-badge" style="background:{style["bg"]}; color:{style["border"]};">{style["label"]}</div>'
        f'<div class="rec-title">{icon} #{index} — {rec.title}</div>'
        f'<div class="rec-meta">KATEGORI: {rec.category.upper()} · KEYAKINAN: {rec.confidence_pct}%</div>'
        f'</div>'
        f'<div class="rec-savings" style="background: linear-gradient(135deg, #8B5CF6 0%, #EC4899 100%);">'
        f'<div class="rec-savings-label">{savings_label}</div>'
        f'<div class="rec-savings-value">{savings_value}</div>'
        f'</div>'
        f'</div>'
        f'<div class="rec-context"><strong style="color:#1E1B4B;">Konteks:</strong> {rec.context}</div>'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)

    # Steps & actions dalam expander
    with st.expander(f"📋 Lihat langkah konkret & aksi", expanded=False):
        st.markdown("**Langkah yang harus dilakukan:**")
        for i, step in enumerate(rec.steps, 1):
            step_html = (
                f'<div class="rec-step">'
                f'<span class="rec-step-num">{i}.</span> {step}'
                f'</div>'
            )
            st.markdown(step_html, unsafe_allow_html=True)

        st.caption(f"📎 Sumber data: {rec.data_source}")

        st.markdown("")
        col_a, col_b, col_c = st.columns([1, 1, 3])

        with col_a:
            if st.button("✅ Setujui", key=f"approve_{index}",
                         type="primary", use_container_width=True):
                audit.log_decision(
                    recommendation=rec.title,
                    decision="approved",
                    notes=f"Impact: Rp {rec.annual_rp:,.0f}/tahun, Confidence: {rec.confidence_pct}%",
                )
                st.success(f"✅ Rekomendasi #{index} disetujui & tercatat di audit trail.")

        with col_b:
            if st.button("❌ Tolak", key=f"reject_{index}",
                         use_container_width=True):
                audit.log_decision(
                    recommendation=rec.title,
                    decision="rejected",
                    notes="Ditolak oleh user",
                )
                st.info(f"Rekomendasi #{index} ditolak.")

        with col_c:
            st.caption("Keputusan tercatat permanen di database.")


# ==================== MAIN ====================
def render(ds: Dataset, scope: Scope) -> None:
    _inject_css()

    st.title("🎯 Priority Actions")
    st.caption(
        "Action plan otomatis dengan Financial Impact terukur. "
        "Setiap keputusan disimpan untuk Institutional Memory (BRD 8)."
    )

    targets = _active_targets()
    st.caption(
        f"🎯 Target aktif: Yield ≥ {targets.yield_min:g}% · "
        f"Scrap ≤ {targets.scrap_max:g}% · OEE ≥ {targets.oee_min:g}%"
    )

    s = summarize(ds, scope)
    recs = generate_recommendations(ds, s, targets)

    if not recs:
        st.success("✅ Tidak ada rekomendasi saat ini. Semua KPI dalam target.")
        return

    # ==== RINGKASAN ====
    total_annual = sum(r.annual_rp for r in recs if r.annual_rp > 0)
    total_cash = sum(r.monthly_rp for r in recs if r.annual_rp == 0)
    high_count = sum(1 for r in recs if r.severity == "high")

    c1, c2, c3, c4 = st.columns(4)
    _glass_card(c1, "Total Rekomendasi", str(len(recs)), "#8B5CF6",
                note="Action items terdeteksi")
    _glass_card(c2, "🔴 Prioritas Tinggi", str(high_count),
                "#EF4444" if high_count > 0 else "#10B981",
                note="Perlu aksi segera")
    _glass_card(c3, "💰 Cost Saving Tahunan", _fmt_rp(total_annual),
                "#10B981", note="Potensi penghematan")
    _glass_card(c4, "💵 Cash Recovery",
                _fmt_rp(total_cash) if total_cash else "—",
                "#F59E0B", note="One-time recovery")

    # Banner highlight
    if high_count > 0:
        html = (
            f'<div class="rc-banner">'
            f'<div class="rc-banner-label">🎯 PRIORITY ACTIONS — ACTION REQUIRED</div>'
            f'<div class="rc-banner-value">{_fmt_rp(total_annual)}</div>'
            f'<div class="rc-banner-desc">'
            f'Potensi penghematan tahunan dari <strong>{len(recs)} rekomendasi</strong>. '
            f'<strong>{high_count} item</strong> berprioritas TINGGI dan perlu tindakan segera.'
            f'</div>'
            f'</div>'
        )
        st.markdown(html, unsafe_allow_html=True)
    else:
        html = (
            f'<div class="rc-banner">'
            f'<div class="rc-banner-label">🎯 PRIORITY ACTIONS</div>'
            f'<div class="rc-banner-value">{_fmt_rp(total_annual)}</div>'
            f'<div class="rc-banner-desc">'
            f'Potensi penghematan tahunan dari <strong>{len(recs)} rekomendasi</strong>. '
            f'Tidak ada item berprioritas tinggi saat ini.'
            f'</div>'
            f'</div>'
        )
        st.markdown(html, unsafe_allow_html=True)

    st.markdown("---")

    with st.expander("ℹ️ Cara kerja Recommendation Engine"):
        st.markdown(
            "Engine menganalisis:\n"
            "- **Cost Alert aktif** (Yield, Scrap, OEE, Cost, Utility)\n"
            "- **Data inventory** (stock-out, slow-moving, dead stock)\n"
            "- **Data produksi** (performa aktual)\n\n"
            "Setiap rekomendasi menyertakan:\n"
            "- **Estimasi Cost Saving** (dihitung dari gap × volume × harga material)\n"
            "- **Tingkat keyakinan** (berdasar jumlah data & ketersediaan KPI)\n"
            "- **Langkah konkret** (bukan saran umum)\n\n"
            "Sesuai **BRD 8**, setiap rekomendasi membutuhkan persetujuan manusia "
            "(human-in-the-loop) dan keputusan tercatat permanen di audit trail."
        )

    st.markdown("---")
    st.subheader(f"📋 Daftar Rekomendasi (diurutkan prioritas)")

    for i, rec in enumerate(recs, 1):
        _render_rec_card(rec, i)

    st.markdown("---")
    st.info(
        "💡 **Tips:** Klik **Setujui** untuk setiap rekomendasi yang akan dieksekusi. "
        "Keputusan akan tercatat permanen di database dan bisa dilihat di menu **Audit Trail**. "
        "Fitur **Institutional Memory** akan belajar dari pola keputusan Anda."
    )