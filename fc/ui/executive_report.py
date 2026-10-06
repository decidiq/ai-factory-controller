"""Executive Report - data-driven + narasi + ekspor PDF/Excel/PPT (BRD 2.5 & 10)."""
import datetime

import streamlit as st

from ..config import TARGETS as DEFAULT_TARGETS
from ..intel.alert_impact import compute_alerts
from ..intel.narrative import generate_narrative
from ..intel.period_compare import available_periods, compare_periods
from ..kpi import Scope, inventory_table, summarize, variance_table
from ..pipeline import Dataset
from ..report.pdf_export import generate_pdf
from ..report.excel_export import generate_excel
from ..report.ppt_export import generate_ppt


def _active_targets():
    """Target aktif — dari session (Settings) atau default."""
    return st.session_state.get("_targets") or DEFAULT_TARGETS


def _render_narrative(narrative) -> None:
    st.markdown("### 📰 Ringkasan Eksekutif")
    st.markdown(f"#### {narrative.headline}")
    st.markdown(narrative.executive_summary)
    st.markdown("")

    col1, col2 = st.columns(2)

    with col1:
        if narrative.achievements.items:
            st.markdown(f"**{narrative.achievements.icon} {narrative.achievements.title}**")
            for item in narrative.achievements.items:
                st.markdown(f"- {item}")
            st.markdown("")

        if narrative.criticals.items:
            st.markdown(f"**{narrative.criticals.icon} {narrative.criticals.title}**")
            for item in narrative.criticals.items:
                st.markdown(f"- {item}")
            st.markdown("")

    with col2:
        if narrative.warnings.items:
            st.markdown(f"**{narrative.warnings.icon} {narrative.warnings.title}**")
            for item in narrative.warnings.items:
                st.markdown(f"- {item}")
            st.markdown("")

        if narrative.recommendations.items:
            st.markdown(f"**{narrative.recommendations.icon} {narrative.recommendations.title}**")
            for i, item in enumerate(narrative.recommendations.items, 1):
                st.markdown(f"{i}. {item}")
            st.markdown("")

    st.info(narrative.closing)


def render(ds: Dataset, scope: Scope) -> None:
    st.title("📊 Executive Report")
    st.caption(f"Sumber: {ds.report.source_label} · Dibaca: {ds.report.loaded_at}")

    if ds.is_demo:
        st.warning("🧪 **DEMO DATA** — angka di bawah adalah data contoh.")

    s = summarize(ds, scope)
    targets = _active_targets()

    # ---- Info Header ----
    plant_label = scope.plant or "Semua Plant"
    line_label = scope.line or "Semua Line"
    period = (f"{scope.start} s/d {scope.end}"
              if scope.start and scope.end else "Semua periode")

    c1, c2 = st.columns(2)
    c1.markdown(f"**Plant:** {plant_label}  \n**Line:** {line_label}")
    c2.markdown(f"**Periode:** {period}  \n**Cetak:** {datetime.datetime.now():%d-%m-%Y %H:%M}")

    st.caption(
        f"🎯 Target aktif: Yield ≥ {targets.yield_min:g}% · "
        f"Scrap ≤ {targets.scrap_max:g}% · OEE ≥ {targets.oee_min:g}%"
    )

    st.markdown("---")

    # ---- Narasi Eksekutif ----
    narrative = generate_narrative(ds, s, targets)
    _render_narrative(narrative)

    st.markdown("---")

    # ---- Ringkasan KPI ----
    st.subheader("📊 Ringkasan KPI")

    def _fmt(kpi, fmt):
        return fmt.format(kpi.value) if kpi.available else "—"

    r1 = st.columns(4)
    r1[0].metric("Output", _fmt(s.output_kg, "{:,.0f} Kg"))
    r1[1].metric("Yield", _fmt(s.yield_pct, "{:.2f}%"))
    r1[2].metric("Scrap", _fmt(s.scrap_pct, "{:.2f}%"))
    r1[3].metric("OEE", _fmt(s.oee.oee, "{:.2f}%"))

    r2 = st.columns(4)
    r2[0].metric("COGM", _fmt(s.cogm, "Rp {:,.0f}"))
    r2[1].metric("Cost/Kg", _fmt(s.cost_per_kg, "Rp {:,.0f}"))
    r2[2].metric("Score", f"{s.score.score}/100" if s.score.score is not None else "—")
    r2[3].metric("Kategori", s.score.category)

    # ---- Peringatan Aktif ----
    alerts = compute_alerts(s, targets)
    if alerts:
        st.markdown("### 🚨 Peringatan Aktif")
        total_annual = sum(abs(a.annual_rp) for a in alerts)
        st.markdown(f"**Total potensi dampak: Rp {total_annual:,.0f}/tahun**")
        for a in alerts:
            icon = {"high": "🔴", "medium": "🟡", "info": "🔵"}.get(a.severity, "⚪")
            st.markdown(
                f"{icon} **{a.title}**  \n"
                f"{a.message}  \n"
                f"💰 Dampak: Rp {a.monthly_rp:,.0f}/bulan "
                f"(Rp {a.annual_rp:,.0f}/tahun)  \n"
                f"🔧 {a.fix_hint}"
            )

    st.markdown("---")

    # ---- Perbandingan Periode ----
    periods = available_periods(ds)
    if len(periods) >= 2:
        st.markdown("### 📅 Perbandingan Periode (MoM)")
        if len(periods) >= 3:
            prev, curr = periods[-3], periods[-2]
            st.caption(f"Membandingkan {prev} dengan {curr} (2 bulan penuh terakhir).")
        else:
            prev, curr = periods[-2], periods[-1]
            st.caption(f"Membandingkan {prev} dengan {curr}.")

        comps = compare_periods(ds, prev, curr)
        rows = []
        for c in comps:
            improving = c.is_improving
            status = "✅ Membaik" if improving is True else \
                     ("🔴 Memburuk" if improving is False else "➖ Stabil")
            rows.append({
                "KPI": c.label,
                prev: c.fmt_value(c.prev_value),
                curr: c.fmt_value(c.curr_value),
                "Δ": c.fmt_delta(),
                "Δ %": c.fmt_pct(),
                "Status": status,
            })
        import pandas as pd
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        st.markdown("---")

    # ---- Variance Biaya ----
    if (ds.budget is not None and not ds.budget.empty
            and {"Category", "Budget", "Actual"} <= set(ds.budget.columns)):
        st.markdown("### 💰 Variance Biaya")
        st.dataframe(variance_table(ds.budget), use_container_width=True, hide_index=True)
        st.markdown("---")

    # ---- Inventaris ----
    if ds.inventory is not None and not ds.inventory.empty:
        st.markdown("### 📦 Inventaris")
        it = inventory_table(ds.inventory)
        col_a, col_b = st.columns(2)
        col_a.metric("Slow Moving", int((it["Status"] == "Slow Moving").sum()))
        col_b.metric("Dead Stock", int((it["Status"] == "Dead Stock").sum()))
        st.markdown("---")

    # ---- Ekspor (3 format: PDF, Excel, PPT) ----
    st.subheader("📤 Ekspor Laporan")

    col_pdf, col_excel, col_ppt = st.columns(3)

    with col_pdf:
        if st.button("📄 Buat PDF", type="primary", use_container_width=True):
            with st.spinner("Membuat PDF..."):
                try:
                    pdf_path = generate_pdf(ds, scope, targets=targets)
                    with open(pdf_path, "rb") as f:
                        st.download_button(
                            label="⬇️ Unduh PDF",
                            data=f.read(),
                            file_name=pdf_path,
                            mime="application/pdf",
                            use_container_width=True,
                        )
                except Exception as e:
                    st.error(f"Gagal membuat PDF: {e}")

    with col_excel:
        if st.button("📊 Buat Excel", use_container_width=True):
            with st.spinner("Membuat Excel..."):
                try:
                    xlsx_data = generate_excel(ds, scope, targets=targets)
                    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    st.download_button(
                        label="⬇️ Unduh Excel",
                        data=xlsx_data,
                        file_name=f"executive_report_{ts}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,
                    )
                except Exception as e:
                    st.error(f"Gagal membuat Excel: {e}")

    with col_ppt:
        if st.button("📽️ Buat PPT", use_container_width=True):
            with st.spinner("Membuat PPT..."):
                try:
                    ppt_data = generate_ppt(ds, scope, targets)
                    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    st.download_button(
                        label="⬇️ Unduh PPT",
                        data=ppt_data,
                        file_name=f"executive_report_{ts}.pptx",
                        mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                        use_container_width=True,
                    )
                except Exception as e:
                    st.error(f"Gagal membuat PPT: {e}")

    st.info("📄 PDF: narasi + KPI · 📊 Excel: 8 sheet data · 📽️ PPT: 6 slide presentasi")