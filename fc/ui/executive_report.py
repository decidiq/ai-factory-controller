"""Executive Report - Executive Briefing Deck + export PDF/Excel/PPT (DARK)."""
import datetime
import math

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
from .components import (page_header, mini_health_score,
                         format_period_label, compute_health_score,
                         section_divider)


# ==================== NUMBER FORMATTING (Indonesian) ====================
def _fmt_thousand(v, decimals: int = 0) -> str:
    """2.889.047.350 atau 1.234,57"""
    try:
        if v is None:
            return "—"
        f = float(v)
        if math.isnan(f) or math.isinf(f):
            return "—"
        if decimals > 0:
            return f"{f:,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return f"{f:,.0f}".replace(",", ".")
    except (ValueError, TypeError):
        return str(v) if v is not None else "—"


def _fmt_pct(v, decimals: int = 2) -> str:
    """-3.7872 → '-3,79%'"""
    try:
        if v is None:
            return "—"
        f = float(v)
        if math.isnan(f) or math.isinf(f):
            return "—"
        return f"{f:.{decimals}f}".replace(".", ",") + "%"
    except (ValueError, TypeError):
        return str(v) if v is not None else "—"


def _fmt_rp(v, compact: bool = False) -> str:
    """Rp 2.889.047.350 atau Rp 2,89 M (compact)"""
    try:
        if v is None:
            return "—"
        f = float(v)
        if math.isnan(f) or math.isinf(f):
            return "—"
        if compact:
            if abs(f) >= 1_000_000_000:
                return "Rp " + f"{f/1_000_000_000:.2f}".replace(".", ",") + " M"
            if abs(f) >= 1_000_000:
                return "Rp " + f"{f/1_000_000:.1f}".replace(".", ",") + " jt"
            if abs(f) >= 1_000:
                return "Rp " + f"{f/1_000:.1f}".replace(".", ",") + " rb"
        return "Rp " + f"{f:,.0f}".replace(",", ".")
    except (ValueError, TypeError):
        return str(v) if v is not None else "—"


# ==================== CSS (DARK) ====================
EXEC_CSS = """
<style>
/* Glass Card */
.exec-glass {
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
.exec-glass::before {
    content: '';
    position: absolute;
    top: 0; left: 17px;
    width: 35px; height: 3px;
    background: var(--accent, #a489ff);
    border-radius: 0 0 5px 5px;
}
.exec-glass:hover {
    transform: translateY(-2px);
    border-color: #8c79d7;
    box-shadow: 0 10px 24px rgba(8, 8, 33, 0.45);
}
.exec-glass-label {
    color: #b8bedb;
    font-weight: 600;
    font-size: 0.62rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 6px;
}
.exec-glass-value {
    color: #ffffff;
    font-weight: 800;
    font-size: 1.35rem;
    letter-spacing: -0.04em;
    line-height: 1.15;
    margin-bottom: 4px;
}
.exec-glass-note {
    color: #8793bc;
    font-size: 0.68rem;
    line-height: 1.3;
    margin-top: 6px;
}

/* Health Banner */
.exec-health-banner {
    background: linear-gradient(110deg, #30265e, #211b47 55%, #171b3c);
    border-radius: 16px;
    padding: 22px 26px;
    color: #ffffff;
    box-shadow: 0 9px 30px rgba(6, 9, 23, 0.13);
    border: 1px solid #5e5090;
    display: flex;
    align-items: center;
    gap: 26px;
    flex-wrap: wrap;
    margin-bottom: 20px;
}
.exec-health-left { min-width: 160px; }
.exec-health-label {
    font-size: 0.62rem;
    font-weight: 800;
    letter-spacing: 0.12em;
    color: #c9b9f8;
    text-transform: uppercase;
    margin-bottom: 6px;
}
.exec-health-score {
    font-size: 2.2rem;
    font-weight: 800;
    line-height: 1;
    letter-spacing: -0.04em;
    color: #ffffff;
}
.exec-health-score-max { font-size: 1rem; color: #c8c2ee; font-weight: 600; }
.exec-health-status {
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.06em;
    margin-top: 6px;
    text-transform: uppercase;
}
.exec-health-right { flex: 1; min-width: 200px; }
.exec-health-track {
    height: 8px;
    background: #55517e;
    border-radius: 50px;
    overflow: hidden;
    margin-bottom: 8px;
}
.exec-health-fill {
    height: 100%;
    border-radius: 50px;
}
.exec-health-meta {
    font-size: 0.72rem;
    color: #adb6d5;
}
</style>
"""


def _inject_css():
    st.markdown(EXEC_CSS, unsafe_allow_html=True)


# ==================== HELPERS ====================
def _active_targets():
    return st.session_state.get("_targets") or DEFAULT_TARGETS


def _glass_card(col, label: str, value: str, accent: str = "#a489ff",
                note: str = None) -> None:
    """Glass card single-line HTML (aman dari bug markdown) — dark."""
    note_html = f'<div class="exec-glass-note">{note}</div>' if note else ""
    html = (
        f'<div class="exec-glass" style="--accent: {accent};">'
        f'<div class="exec-glass-label">{label}</div>'
        f'<div class="exec-glass-value">{value}</div>'
        f'{note_html}'
        f'</div>'
    )
    col.markdown(html, unsafe_allow_html=True)


def _health_score(s, targets):
    components, weights = [], []
    if s.yield_pct.available:
        components.append(min(100.0, max(0.0, (s.yield_pct.value / targets.yield_min) * 100)))
        weights.append(0.30)
    if s.oee.oee.available:
        components.append(min(100.0, max(0.0, (s.oee.oee.value / targets.oee_min) * 100)))
        weights.append(0.30)
    if s.scrap_pct.available:
        components.append(min(100.0, max(0.0, (1 - s.scrap_pct.value / (targets.scrap_max * 2)) * 100)))
        weights.append(0.20)
    if s.cost_per_kg.available:
        components.append(85.0)
        weights.append(0.20)
    if not components:
        return 0.0, "No Data", "#94A3B8"
    tw = sum(weights)
    score = sum(c * w for c, w in zip(components, weights)) / tw if tw else 0.0
    if score >= 90:
        return score, "Excellent", "#77edb4"
    elif score >= 80:
        return score, "Good", "#a489ff"
    elif score >= 70:
        return score, "Fair", "#f7d578"
    return score, "Needs Attention", "#ff9eaa"


def _render_health_banner(score: float, status: str, color: str) -> None:
    html = (
        f'<div class="exec-health-banner">'
        f'<div class="exec-health-left">'
        f'<div class="exec-health-label">🏥 Plant Health Score</div>'
        f'<div class="exec-health-score">{score:.0f}<span class="exec-health-score-max">/100</span></div>'
        f'<div class="exec-health-status" style="color:{color};">● {status}</div>'
        f'</div>'
        f'<div class="exec-health-right">'
        f'<div class="exec-health-track">'
        f'<div class="exec-health-fill" style="width:{score}%; background: linear-gradient(90deg, #a489ff 0%, {color} 100%);"></div>'
        f'</div>'
        f'<div class="exec-health-meta">Agregat tertimbang dari Yield (30%), OEE (30%), Scrap (20%), dan Cost (20%).</div>'
        f'</div>'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


# ==================== NARRATIVE (DARK) ====================
def _render_narrative(narrative) -> None:
    st.markdown("### 📰 Executive Summary")

    st.markdown(f"""
    <div style="
        background: #1b1e3e;
        border-left: 5px solid #a489ff;
        padding: 16px 20px;
        border-radius: 10px;
        margin-bottom: 16px;
    ">
        <div style="font-size: 1.1rem; font-weight: 700; color: #f5f6ff;
            letter-spacing: -0.02em;">{narrative.headline}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div style="
        background: #191d3b;
        border: 1px solid #343858;
        border-radius: 12px;
        padding: 20px 24px;
        margin-bottom: 20px;
        font-size: 0.9rem;
        color: #dce0f4;
        line-height: 1.7;
    ">{narrative.executive_summary}</div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2, gap="medium")

    with col1:
        if narrative.achievements.items:
            items_html = "".join(
                f'<div style="font-size: 0.82rem; color: #d8dcf2; padding: 4px 0;">• {item}</div>'
                for item in narrative.achievements.items)
            st.markdown(f"""
            <div style="background: #172d35; border-left: 4px solid #276956;
                padding: 16px 20px; border-radius: 10px; margin-bottom: 14px;">
                <div style="font-size: 0.88rem; font-weight: 800; color: #77edb4;
                    margin-bottom: 10px;">{narrative.achievements.icon} {narrative.achievements.title}</div>
                {items_html}
            </div>
            """, unsafe_allow_html=True)

        if narrative.criticals.items:
            items_html = "".join(
                f'<div style="font-size: 0.82rem; color: #d8dcf2; padding: 4px 0;">• {item}</div>'
                for item in narrative.criticals.items)
            st.markdown(f"""
            <div style="background: #35243a; border-left: 4px solid #794456;
                padding: 16px 20px; border-radius: 10px; margin-bottom: 14px;">
                <div style="font-size: 0.88rem; font-weight: 800; color: #ff9eaa;
                    margin-bottom: 10px;">{narrative.criticals.icon} {narrative.criticals.title}</div>
                {items_html}
            </div>
            """, unsafe_allow_html=True)

    with col2:
        if narrative.warnings.items:
            items_html = "".join(
                f'<div style="font-size: 0.82rem; color: #d8dcf2; padding: 4px 0;">• {item}</div>'
                for item in narrative.warnings.items)
            st.markdown(f"""
            <div style="background: #302b30; border-left: 4px solid #756036;
                padding: 16px 20px; border-radius: 10px; margin-bottom: 14px;">
                <div style="font-size: 0.88rem; font-weight: 800; color: #f7d578;
                    margin-bottom: 10px;">{narrative.warnings.icon} {narrative.warnings.title}</div>
                {items_html}
            </div>
            """, unsafe_allow_html=True)

        if narrative.recommendations.items:
            items_html = "".join(
                f'<div style="font-size: 0.82rem; color: #d8dcf2; padding: 4px 0;">{i}. {item}</div>'
                for i, item in enumerate(narrative.recommendations.items, 1))
            st.markdown(f"""
            <div style="background: #292449; border-left: 4px solid #6551a0;
                padding: 16px 20px; border-radius: 10px; margin-bottom: 14px;">
                <div style="font-size: 0.88rem; font-weight: 800; color: #c4aaff;
                    margin-bottom: 10px;">{narrative.recommendations.icon} {narrative.recommendations.title}</div>
                {items_html}
            </div>
            """, unsafe_allow_html=True)

    st.info(narrative.closing)


# ==================== KPI GRID (DARK) ====================
def _render_kpi_grid(s) -> None:
    st.markdown("### 📊 Ringkasan KPI")

    def _show(kpi, fmt_fn):
        """Ambil value KPI dan format pakai fungsi custom."""
        if not kpi.available:
            return "—"
        return fmt_fn(kpi.value)

    r1 = st.columns(4, gap="medium")
    _glass_card(r1[0], "Production Volume",
                _show(s.output_kg, lambda v: _fmt_thousand(v) + " Kg"),
                "#a489ff")
    _glass_card(r1[1], "Yield", _show(s.yield_pct, _fmt_pct), "#77edb4")
    _glass_card(r1[2], "Scrap", _show(s.scrap_pct, _fmt_pct), "#f7d578")
    _glass_card(r1[3], "OEE", _show(s.oee.oee, _fmt_pct), "#71d5e9")

    st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)

    r2 = st.columns(4, gap="medium")
    _glass_card(r2[0], "COGM", _show(s.cogm, _fmt_rp), "#ec3f92")
    _glass_card(r2[1], "Cost/Kg", _show(s.cost_per_kg, _fmt_rp), "#c4aaff")
    score_val = f"{s.score.score}/100" if s.score.score is not None else "—"
    _glass_card(r2[2], "Cost Control Score", score_val, "#a489ff")
    _glass_card(r2[3], "Kategori", s.score.category or "—", "#89d84a")


# ==================== ALERTS (DARK) ====================
def _render_alerts(alerts) -> None:
    if not alerts:
        return

    st.markdown("### 🚨 Cost Alert")

    total_annual = sum(abs(a.annual_rp) for a in alerts)
    st.markdown(f"""
    <div style="background: #35243a; border: 1px solid #794456;
        border-radius: 12px; padding: 16px 20px; margin-bottom: 16px;">
        <div style="font-size: 0.7rem; color: #ff9eaa; font-weight: 800;
            letter-spacing: 0.06em; text-transform: uppercase;">💰 TOTAL POTENSI DAMPAK</div>
        <div style="font-size: 1.5rem; font-weight: 800; color: #ffffff;
            letter-spacing: -0.03em; margin-top: 6px;">{_fmt_rp(total_annual)}/tahun</div>
        <div style="font-size: 0.8rem; color: #d8dcf2; margin-top: 4px;">
            Yang bisa dihemat jika semua masalah diperbaiki.</div>
    </div>
    """, unsafe_allow_html=True)

    for a in alerts:
        icon = {"high": "🔴", "medium": "🟡", "info": "🔵"}.get(a.severity, "⚪")
        border = {"high": "#ff9eaa", "medium": "#f7d578", "info": "#71d5e9"}.get(a.severity, "#adb6d5")
        st.markdown(f"""
        <div style="background: #1b1e3e; border: 1px solid #343858;
            border-left: 5px solid {border}; border-radius: 12px;
            padding: 16px 20px; margin-bottom: 12px;">
            <div style="font-size: 0.95rem; font-weight: 700; color: #f5f6ff;
                margin-bottom: 6px;">{icon} {a.title}</div>
            <div style="font-size: 0.82rem; color: #adb6d5; margin-bottom: 8px;">{a.message}</div>
            <div style="font-size: 0.85rem; font-weight: 700; color: #ff9eaa;
                margin-bottom: 6px;">💰 {_fmt_rp(a.monthly_rp)}/bulan · {_fmt_rp(a.annual_rp)}/tahun</div>
            <div style="font-size: 0.78rem; color: #b8bedb; font-style: italic;">🔧 {a.fix_hint}</div>
        </div>
        """, unsafe_allow_html=True)


# ==================== MoM ====================
def _render_mom(ds) -> None:
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
        status = ("✅ Membaik" if improving is True
                  else ("🔴 Memburuk" if improving is False else "➖ Stabil"))
        rows.append({
            "KPI": c.label,
            prev: c.fmt_value(c.prev_value),
            curr: c.fmt_value(c.curr_value),
            "Δ": c.fmt_delta(),
            "Δ %": c.fmt_pct(),
            "Status": status,
        })
    import pandas as pd
    from .components import render_table
    render_table(pd.DataFrame(rows), max_height="350px")


# ==================== VARIANCE & INVENTORY ====================
def _render_variance_and_inventory(ds) -> None:
    col1, col2 = st.columns(2, gap="medium")
    with col1:
        if (ds.budget is not None and not ds.budget.empty
                and {"Category", "Budget", "Actual"} <= set(ds.budget.columns)):
            st.markdown("### 💰 Variance Biaya")

            tbl = variance_table(ds.budget).copy()

            # Format semua kolom numerik ke string Indonesia
            for col in tbl.columns:
                col_lower = str(col).lower()

                # Kolom persen
                if "pct" in col_lower or "%" in col_lower or "percent" in col_lower:
                    tbl[col] = tbl[col].apply(_fmt_pct)
                    continue

                # Kolom nilai uang
                if any(k in col_lower for k in ("budget", "actual", "variance")):
                    tbl[col] = tbl[col].apply(_fmt_rp)
                    continue

                # Kolom numerik lain (fallback)
                try:
                    import pandas as pd
                    if pd.api.types.is_numeric_dtype(tbl[col]):
                        if pd.api.types.is_float_dtype(tbl[col]):
                            tbl[col] = tbl[col].apply(lambda v: _fmt_thousand(v, 2))
                        else:
                            tbl[col] = tbl[col].apply(_fmt_thousand)
                except Exception:
                    pass

            from .components import render_table
            render_table(tbl, max_height="350px")

    with col2:
        if ds.inventory is not None and not ds.inventory.empty:
            st.markdown("### 📦 Inventaris")
            it = inventory_table(ds.inventory)
            slow = int((it["Status"] == "Slow Moving").sum())
            dead = int((it["Status"] == "Dead Stock").sum())
            c1, c2 = st.columns(2, gap="medium")
            _glass_card(c1, "Slow Moving", str(slow), "#f7d578")
            _glass_card(c2, "Dead Stock", str(dead), "#ff9eaa")


# ==================== EXPORT ====================
def _render_export_buttons(ds, scope, targets) -> None:
    st.markdown("### 📤 Export Report")
    st.caption("Download laporan dalam berbagai format.")

    col_pdf, col_excel, col_ppt = st.columns(3, gap="medium")

    with col_pdf:
        if st.button("📄 Buat PDF", type="primary", width='stretch'):
            with st.spinner("Membuat PDF..."):
                try:
                    pdf_path = generate_pdf(ds, scope, targets=targets)
                    with open(pdf_path, "rb") as f:
                        st.download_button(
                            label="⬇️ Download PDF", data=f.read(),
                            file_name=pdf_path, mime="application/pdf",
                            width='stretch',
                        )
                except Exception as e:
                    st.error(f"Gagal membuat PDF: {e}")

    with col_excel:
        if st.button("📊 Buat Excel", type="primary", width='stretch'):
            with st.spinner("Membuat Excel..."):
                try:
                    xlsx_data = generate_excel(ds, scope, targets=targets)
                    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    st.download_button(
                        label="⬇️ Download Excel", data=xlsx_data,
                        file_name=f"decidiq_report_{ts}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        width='stretch',
                    )
                except Exception as e:
                    st.error(f"Gagal membuat Excel: {e}")

    with col_ppt:
        if st.button("📽️ Buat PPT", type="primary", width='stretch'):
            with st.spinner("Membuat PPT..."):
                try:
                    ppt_data = generate_ppt(ds, scope, targets)
                    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    st.download_button(
                        label="⬇️ Download PPT", data=ppt_data,
                        file_name=f"decidiq_report_{ts}.pptx",
                        mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                        width='stretch',
                    )
                except Exception as e:
                    st.error(f"Gagal membuat PPT: {e}")

    st.caption("📄 PDF: narasi + KPI · 📊 Excel: 8 sheet data · 📽️ PPT: 6 slide presentasi")


# ==================== MAIN RENDER ====================
def render(ds: Dataset, scope: Scope) -> None:
    _inject_css()
    targets = _active_targets()
    s = summarize(ds, scope)

    page_header(
        title="Executive Report",
        subtitle=(
            f"Sumber: {ds.report.source_label} · "
            f"Laporan eksekutif performa pabrik · "
            f"Target: Yield ≥ {targets.yield_min:g}% · Scrap ≤ {targets.scrap_max:g}% · "
            f"OEE ≥ {targets.oee_min:g}%"
        ),
        granularity="Multi",
        period_label=format_period_label(scope),
        icon="📋",
    )

    try:
        score, status, color = compute_health_score(s, targets)
        mini_health_score(score, status, color)
    except Exception:
        pass

    if ds.is_demo:
        st.warning("🧪 **DEMO DATA** — angka di bawah adalah data contoh.")

    score, status, color = _health_score(s, targets)
    _render_health_banner(score, status, color)

    narrative = generate_narrative(ds, s, targets)
    _render_narrative(narrative)

    st.markdown("---")
    _render_kpi_grid(s)

    st.markdown("---")
    alerts = compute_alerts(s, targets)
    _render_alerts(alerts)

    st.markdown("---")
    _render_mom(ds)

    st.markdown("---")
    _render_variance_and_inventory(ds)

    st.markdown("---")
    _render_export_buttons(ds, scope, targets)