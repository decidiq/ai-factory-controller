"""Executive Report - data-driven + narasi + ekspor PDF/Excel/PPT."""
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
    return st.session_state.get("_targets") or DEFAULT_TARGETS


def _render_header(ds, scope, targets) -> None:
    """Header premium dengan gradient."""
    plant_label = scope.plant or "Semua Plant"
    line_label = scope.line or "Semua Line"
    period = (f"{scope.start} s/d {scope.end}"
              if scope.start and scope.end else "Semua periode")

    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #1E1B4B 0%, #4C1D95 50%, #8B5CF6 100%);
        color: #FFFFFF;
        padding: 28px 32px;
        border-radius: 16px;
        box-shadow: 0 10px 30px rgba(139, 92, 246, 0.25);
        margin-bottom: 24px;
    ">
        <div style="
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 16px;
        ">
            <div>
                <div style="
                    font-size: 0.75rem;
                    letter-spacing: 1.5px;
                    opacity: 0.85;
                    font-weight: 600;
                    margin-bottom: 6px;
                ">📊 EXECUTIVE REPORT</div>
                <div style="
                    font-size: 1.9rem;
                    font-weight: 800;
                    letter-spacing: -1px;
                    line-height: 1.1;
                ">Decidiq — Performance Summary</div>
                <div style="
                    font-size: 0.9rem;
                    opacity: 0.9;
                    margin-top: 8px;
                    font-weight: 500;
                ">{plant_label} · {line_label} · {period}</div>
            </div>
            <div style="
                text-align: right;
                background: rgba(255,255,255,0.15);
                padding: 14px 20px;
                border-radius: 12px;
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255,255,255,0.2);
            ">
                <div style="font-size: 0.7rem; letter-spacing: 1px; opacity: 0.85; font-weight: 600;">TARGET AKTIF</div>
                <div style="font-size: 0.85rem; font-weight: 600; margin-top: 6px; line-height: 1.6;">
                    Yield ≥ {targets.yield_min:g}% · Scrap ≤ {targets.scrap_max:g}% · OEE ≥ {targets.oee_min:g}%
                </div>
                <div style="font-size: 0.7rem; opacity: 0.8; margin-top: 4px;">
                    Dibaca: {ds.report.loaded_at[:16]}
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def _render_narrative(narrative) -> None:
    """Narasi eksekutif dengan layout modern."""
    st.markdown("### 📰 Executive Summary")

    # Headline
    st.markdown(f"""
    <div style="
        background: linear-gradient(90deg, #F5F3FF 0%, #FAF5FF 100%);
        border-left: 5px solid #8B5CF6;
        padding: 16px 20px;
        border-radius: 10px;
        margin-bottom: 16px;
    ">
        <div style="font-size: 1.15rem; font-weight: 700; color: #1E1B4B; letter-spacing: -0.3px;">
            {narrative.headline}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Executive summary paragraph
    st.markdown(f"""
    <div style="
        background: #FFFFFF;
        border: 1px solid #E9D5FF;
        border-radius: 12px;
        padding: 20px 24px;
        margin-bottom: 20px;
        font-size: 0.95rem;
        color: #334155;
        line-height: 1.7;
    ">
        {narrative.executive_summary}
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        if narrative.achievements.items:
            st.markdown(f"""
            <div style="
                background: #ECFDF5;
                border-left: 4px solid #10B981;
                padding: 16px 20px;
                border-radius: 10px;
                margin-bottom: 14px;
            ">
                <div style="font-size: 0.9rem; font-weight: 700; color: #065F46; margin-bottom: 10px;">
                    {narrative.achievements.icon} {narrative.achievements.title}
                </div>
                {"".join(f'<div style="font-size: 0.85rem; color: #064E3B; padding: 4px 0;">• {item}</div>' for item in narrative.achievements.items)}
            </div>
            """, unsafe_allow_html=True)

        if narrative.criticals.items:
            st.markdown(f"""
            <div style="
                background: #FEF2F2;
                border-left: 4px solid #EF4444;
                padding: 16px 20px;
                border-radius: 10px;
                margin-bottom: 14px;
            ">
                <div style="font-size: 0.9rem; font-weight: 700; color: #991B1B; margin-bottom: 10px;">
                    {narrative.criticals.icon} {narrative.criticals.title}
                </div>
                {"".join(f'<div style="font-size: 0.85rem; color: #7F1D1D; padding: 4px 0;">• {item}</div>' for item in narrative.criticals.items)}
            </div>
            """, unsafe_allow_html=True)

    with col2:
        if narrative.warnings.items:
            st.markdown(f"""
            <div style="
                background: #FFFBEB;
                border-left: 4px solid #F59E0B;
                padding: 16px 20px;
                border-radius: 10px;
                margin-bottom: 14px;
            ">
                <div style="font-size: 0.9rem; font-weight: 700; color: #92400E; margin-bottom: 10px;">
                    {narrative.warnings.icon} {narrative.warnings.title}
                </div>
                {"".join(f'<div style="font-size: 0.85rem; color: #78350F; padding: 4px 0;">• {item}</div>' for item in narrative.warnings.items)}
            </div>
            """, unsafe_allow_html=True)

        if narrative.recommendations.items:
            st.markdown(f"""
            <div style="
                background: #F5F3FF;
                border-left: 4px solid #8B5CF6;
                padding: 16px 20px;
                border-radius: 10px;
                margin-bottom: 14px;
            ">
                <div style="font-size: 0.9rem; font-weight: 700; color: #4C1D95; margin-bottom: 10px;">
                    {narrative.recommendations.icon} {narrative.recommendations.title}
                </div>
                {"".join(f'<div style="font-size: 0.85rem; color: #3B0764; padding: 4px 0;">{i}. {item}</div>' for i, item in enumerate(narrative.recommendations.items, 1))}
            </div>
            """, unsafe_allow_html=True)

    # Closing
    st.info(narrative.closing)


def _render_kpi_grid(s) -> None:
    """Grid KPI dengan card premium."""
    st.markdown("### 📊 Ringkasan KPI")

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
    r2[2].metric("Cost Control Score",
                 f"{s.score.score}/100" if s.score.score is not None else "—")
    r2[3].metric("Kategori", s.score.category)


def _render_alerts(alerts) -> None:
    """Render alerts dengan format premium."""
    if not alerts:
        return

    st.markdown("### 🚨 Cost Alert")

    total_annual = sum(abs(a.annual_rp) for a in alerts)
    st.markdown(f"""
    <div style="
        background: #FEF2F2;
        border: 1px solid #FECACA;
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 16px;
    ">
        <div style="font-size: 0.8rem; color: #991B1B; font-weight: 600; letter-spacing: 0.5px;">
            💰 TOTAL POTENSI DAMPAK
        </div>
        <div style="font-size: 1.6rem; font-weight: 800; color: #7F1D1D; letter-spacing: -0.8px; margin-top: 4px;">
            Rp {total_annual:,.0f}/tahun
        </div>
        <div style="font-size: 0.85rem; color: #991B1B; margin-top: 4px;">
            Yang bisa dihemat jika semua masalah diperbaiki.
        </div>
    </div>
    """, unsafe_allow_html=True)

    for a in alerts:
        icon = {"high": "🔴", "medium": "🟡", "info": "🔵"}.get(a.severity, "⚪")
        color = {"high": "#EF4444", "medium": "#F59E0B", "info": "#3B82F6"}.get(a.severity, "#64748B")

        st.markdown(f"""
        <div style="
            background: #FFFFFF;
            border: 1px solid #E9D5FF;
            border-left: 5px solid {color};
            border-radius: 12px;
            padding: 16px 20px;
            margin-bottom: 12px;
        ">
            <div style="font-size: 1rem; font-weight: 700; color: #1E1B4B; margin-bottom: 6px;">
                {icon} {a.title}
            </div>
            <div style="font-size: 0.85rem; color: #64748B; margin-bottom: 8px;">
                {a.message}
            </div>
            <div style="font-size: 0.9rem; font-weight: 700; color: #DC2626; margin-bottom: 6px;">
                💰 Rp {a.monthly_rp:,.0f}/bulan · Rp {a.annual_rp:,.0f}/tahun
            </div>
            <div style="font-size: 0.82rem; color: #475569; font-style: italic;">
                🔧 {a.fix_hint}
            </div>
        </div>
        """, unsafe_allow_html=True)


def _render_mom(ds) -> None:
    """Perbandingan periode MoM."""
    periods = available_periods(ds)
    if len(periods) < 2:
        return

    st.markdown("### 📅 Month-over-Month (MoM)")

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


def _render_variance_and_inventory(ds) -> None:
    """Variance biaya + inventaris."""
    col1, col2 = st.columns(2)

    with col1:
        if (ds.budget is not None and not ds.budget.empty
                and {"Category", "Budget", "Actual"} <= set(ds.budget.columns)):
            st.markdown("### 💰 Variance Biaya")
            st.dataframe(variance_table(ds.budget),
                         use_container_width=True, hide_index=True)

    with col2:
        if ds.inventory is not None and not ds.inventory.empty:
            st.markdown("### 📦 Inventaris")
            it = inventory_table(ds.inventory)
            slow = int((it["Status"] == "Slow Moving").sum())
            dead = int((it["Status"] == "Dead Stock").sum())

            c1, c2 = st.columns(2)
            c1.metric("Slow Moving", slow)
            c2.metric("Dead Stock", dead)


def _render_export_buttons(ds, scope, targets) -> None:
    """Tombol ekspor premium."""
    st.markdown("### 📤 Export Report")
    st.caption("Download laporan dalam berbagai format.")

    col_pdf, col_excel, col_ppt = st.columns(3)

    with col_pdf:
        if st.button("📄 Buat PDF", type="primary", use_container_width=True):
            with st.spinner("Membuat PDF..."):
                try:
                    pdf_path = generate_pdf(ds, scope, targets=targets)
                    with open(pdf_path, "rb") as f:
                        st.download_button(
                            label="⬇️ Download PDF",
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
                        label="⬇️ Download Excel",
                        data=xlsx_data,
                        file_name=f"decidiq_report_{ts}.xlsx",
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
                        label="⬇️ Download PPT",
                        data=ppt_data,
                        file_name=f"decidiq_report_{ts}.pptx",
                        mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                        use_container_width=True,
                    )
                except Exception as e:
                    st.error(f"Gagal membuat PPT: {e}")

    st.caption("📄 PDF: narasi + KPI · 📊 Excel: 8 sheet data · 📽️ PPT: 6 slide presentasi")


def render(ds: Dataset, scope: Scope) -> None:
    targets = _active_targets()
    s = summarize(ds, scope)

    # Header premium
    _render_header(ds, scope, targets)

    if ds.is_demo:
        st.warning("🧪 **DEMO DATA** — angka di bawah adalah data contoh.")

    st.markdown("---")

    # Narrative
    narrative = generate_narrative(ds, s, targets)
    _render_narrative(narrative)

    st.markdown("---")

    # KPI Grid
    _render_kpi_grid(s)

    st.markdown("---")

    # Cost Alert
    alerts = compute_alerts(s, targets)
    _render_alerts(alerts)

    st.markdown("---")

    # MoM
    _render_mom(ds)

    st.markdown("---")

    # Variance & Inventory
    _render_variance_and_inventory(ds)

    st.markdown("---")

    # Export Buttons
    _render_export_buttons(ds, scope, targets)