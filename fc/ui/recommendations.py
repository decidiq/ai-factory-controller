"""Halaman Recommendation Engine — saran aksi konkret dengan impact Rp."""
import pandas as pd
import streamlit as st

from .. import audit
from ..config import TARGETS as DEFAULT_TARGETS
from ..intel.recommend import generate_recommendations
from ..kpi import Scope, summarize
from ..pipeline import Dataset


def _active_targets():
    return st.session_state.get("_targets") or DEFAULT_TARGETS


def _severity_color(severity: str) -> dict:
    """Return warna untuk tiap severity."""
    palette = {
        "high": {"border": "#EF4444", "bg": "#FEF2F2", "icon": "🔴", "label": "PRIORITAS TINGGI"},
        "medium": {"border": "#F59E0B", "bg": "#FFFBEB", "icon": "🟡", "label": "PRIORITAS SEDANG"},
        "info": {"border": "#3B82F6", "bg": "#EFF6FF", "icon": "🔵", "label": "INFORMASI"},
    }
    return palette.get(severity, palette["info"])


def _render_rec_card(rec, index: int) -> None:
    """Tampilkan kartu rekomendasi premium."""
    style = _severity_color(rec.severity)
    icon = style["icon"]

    # Custom card
    st.markdown(f"""
    <div style="
        background: #FFFFFF;
        border: 1px solid #E9D5FF;
        border-left: 5px solid {style['border']};
        border-radius: 14px;
        padding: 24px 26px;
        margin-bottom: 20px;
        box-shadow: 0 4px 16px rgba(139, 92, 246, 0.06), 0 1px 3px rgba(0,0,0,0.03);
        transition: all 0.25s ease;
    ">
        <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 14px;">
            <div style="flex: 1;">
                <div style="
                    display: inline-block;
                    background: {style['bg']};
                    color: {style['border']};
                    font-size: 0.7rem;
                    font-weight: 700;
                    letter-spacing: 0.8px;
                    padding: 4px 10px;
                    border-radius: 6px;
                    margin-bottom: 8px;
                ">{style['label']}</div>
                <div style="
                    font-size: 1.25rem;
                    font-weight: 700;
                    color: #1E1B4B;
                    line-height: 1.3;
                    letter-spacing: -0.3px;
                ">{icon} #{index} — {rec.title}</div>
                <div style="
                    font-size: 0.75rem;
                    color: #6D28D9;
                    font-weight: 600;
                    margin-top: 6px;
                    letter-spacing: 0.3px;
                ">KATEGORI: {rec.category.upper()} · KEYAKINAN: {rec.confidence_pct}%</div>
            </div>
            <div style="
                text-align: right;
                background: linear-gradient(135deg, #8B5CF6 0%, #EC4899 100%);
                color: #FFFFFF;
                padding: 12px 18px;
                border-radius: 12px;
                min-width: 140px;
                box-shadow: 0 4px 14px rgba(139, 92, 246, 0.3);
            ">
                <div style="font-size: 0.65rem; letter-spacing: 1px; opacity: 0.9; font-weight: 600;">
                    {'HEMAT/TAHUN' if rec.annual_rp > 0 else 'CASH RECOVERY'}
                </div>
                <div style="font-size: 1.35rem; font-weight: 800; letter-spacing: -0.5px; margin-top: 2px;">
                    {'Rp ' + f'{rec.annual_rp/1_000_000:.1f} jt' if rec.annual_rp > 0 else 'Rp ' + f'{rec.monthly_rp/1_000_000:.1f} jt'}
                </div>
            </div>
        </div>
        <div style="
            font-size: 0.92rem;
            color: #475569;
            line-height: 1.55;
            margin-bottom: 16px;
            padding: 12px 14px;
            background: #F8FAFC;
            border-radius: 8px;
        ">
            <strong style="color: #1E1B4B;">Konteks:</strong> {rec.context}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Steps & buttons dalam expander
    with st.expander(f"📋 Lihat langkah konkret & aksi", expanded=False):
        st.markdown("**Langkah yang harus dilakukan:**")
        for i, step in enumerate(rec.steps, 1):
            st.markdown(
                f'<div style="'
                f'padding: 10px 14px; margin: 6px 0; '
                f'background: linear-gradient(90deg, #F5F3FF 0%, #FFFFFF 100%); '
                f'border-left: 3px solid #8B5CF6; border-radius: 6px; '
                f'font-size: 0.9rem; color: #334155;'
                f'"><strong style="color: #6D28D9;">{i}.</strong> {step}</div>',
                unsafe_allow_html=True
            )

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


def render(ds: Dataset, scope: Scope) -> None:
    st.title("🎯 Priority Actions")
    st.caption("Action plan otomatis dengan Financial Impact terukur. "
               "Setiap keputusan disimpan untuk Institutional Memory (BRD 8).")

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
    c1.metric("Total Rekomendasi", len(recs))
    c2.metric("🔴 Prioritas Tinggi", high_count)
    c3.metric("💰 Cost Saving Tahunan",
              f"Rp {total_annual / 1_000_000_000:.2f} M" if total_annual >= 1e9
              else f"Rp {total_annual / 1_000_000:.1f} jt",
              help=f"Rp {total_annual:,.0f}")
    c4.metric("💵 Cash Recovery",
              f"Rp {total_cash / 1_000_000:.0f} jt" if total_cash else "—",
              help="One-time")

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