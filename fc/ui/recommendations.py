"""Halaman Recommendation Engine — saran aksi konkret dengan impact Rp."""
import pandas as pd
import streamlit as st

from .. import audit
from ..config import TARGETS as DEFAULT_TARGETS
from ..intel.recommend import generate_recommendations
from ..kpi import Scope, summarize
from ..pipeline import Dataset


def _active_targets():
    """Target aktif — dari session (Settings) atau default."""
    return st.session_state.get("_targets") or DEFAULT_TARGETS


def _render_rec_card(rec, index: int) -> None:
    icon = {"high": "🔴", "medium": "🟡", "info": "🔵"}.get(rec.severity, "⚪")

    with st.container(border=True):
        col_head, col_impact = st.columns([3, 1])

        with col_head:
            st.markdown(f"### {icon} Rekomendasi #{index} — {rec.title}")
            st.caption(f"Kategori: `{rec.category}` · Keyakinan: **{rec.confidence_pct}%**")

        with col_impact:
            if rec.annual_rp > 0:
                st.metric("Hemat Tahunan",
                          f"Rp {rec.annual_rp / 1_000_000:,.1f} jt",
                          help=f"Rp {rec.annual_rp:,.0f}")
            else:
                st.metric("Cash Recovery",
                          f"Rp {rec.monthly_rp / 1_000_000:,.1f} jt",
                          help="One-time")

        st.markdown(f"**Konteks:** {rec.context}")

        st.markdown("**Langkah konkret:**")
        for i, step in enumerate(rec.steps, 1):
            st.markdown(f"{i}. {step}")

        st.caption(f"📎 Sumber data: {rec.data_source}")

        col_a, col_b, col_c = st.columns([1, 1, 3])

        if col_a.button("✅ Setujui", key=f"approve_{index}",
                        use_container_width=True):
            audit.log_decision(
                recommendation=rec.title,
                decision="approved",
                notes=f"Impact: Rp {rec.annual_rp:,.0f}/tahun, Confidence: {rec.confidence_pct}%",
            )
            st.success(f"✅ Rekomendasi #{index} disetujui & dicatat di audit trail.")

        if col_b.button("❌ Tolak", key=f"reject_{index}",
                        use_container_width=True):
            audit.log_decision(
                recommendation=rec.title,
                decision="rejected",
                notes="Ditolak oleh user",
            )
            st.info(f"Rekomendasi #{index} ditolak.")


def render(ds: Dataset, scope: Scope) -> None:
    st.title("🎯 Recommendation Engine")
    st.caption("Saran aksi konkret dengan estimasi hemat Rp. "
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
    c3.metric("💰 Potensi Hemat/Tahun",
              f"Rp {total_annual / 1_000_000_000:.2f} M",
              help=f"Rp {total_annual:,.0f}")
    c4.metric("💵 Cash Recovery",
              f"Rp {total_cash / 1_000_000:.0f} jt" if total_cash else "—",
              help="One-time")

    st.markdown("---")

    with st.expander("ℹ️ Cara kerja Recommendation Engine"):
        st.markdown(
            "Engine menganalisis:\n"
            "- **Alert aktif** (Yield, Scrap, OEE, Cost, Utility)\n"
            "- **Data inventory** (stock-out, slow-moving, dead stock)\n"
            "- **Data produksi** (performa aktual)\n\n"
            "Setiap rekomendasi menyertakan:\n"
            "- **Estimasi hemat Rp** (dihitung dari gap × volume × harga material)\n"
            "- **Tingkat keyakinan** (berdasar jumlah data & ketersediaan KPI)\n"
            "- **Langkah konkret** (bukan saran umum)\n\n"
            "Sesuai **BRD 8**, setiap rekomendasi membutuhkan persetujuan manusia "
            "(human-in-the-loop) dan keputusan tercatat permanen di audit trail."
        )

    st.markdown("---")

    st.subheader(f"📋 Daftar Rekomendasi (diurutkan prioritas)")

    for i, rec in enumerate(recs, 1):
        _render_rec_card(rec, i)
        st.markdown("")

    st.markdown("---")
    st.info(
        "💡 **Tips:** Klik **Setujui** untuk setiap rekomendasi yang akan dieksekusi. "
        "Keputusan akan tercatat permanen di database dan bisa dilihat di menu **Audit Trail**. "
        "Fitur **Institutional Memory** (Fase 3) akan belajar dari pola keputusan Anda."
    )