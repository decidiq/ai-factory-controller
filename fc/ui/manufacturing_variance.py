"""Manufacturing Variance — Budget vs Actual (DARK)."""
import math

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from ..config import TARGETS as DEFAULT_TARGETS, targets_from_config
from ..kpi import variance_table, summarize
from ..pipeline import Dataset
from .charts import COLORS, apply_theme
from .components import (
    page_header, mini_health_score, format_period_label,
    compute_health_score, section_divider,
)


def _fmt_thousand(v, decimals: int = 0) -> str:
    try:
        if v is None: return "—"
        f = float(v)
        if math.isnan(f) or math.isinf(f): return "—"
        if decimals > 0:
            return f"{f:,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return f"{f:,.0f}".replace(",", ".")
    except (ValueError, TypeError):
        return str(v) if v is not None else "—"


def _fmt_pct(v, decimals: int = 2) -> str:
    try:
        if v is None: return "—"
        f = float(v)
        if math.isnan(f) or math.isinf(f): return "—"
        return f"{f:.{decimals}f}".replace(".", ",") + "%"
    except (ValueError, TypeError):
        return str(v) if v is not None else "—"


def _fmt_rp(v, compact: bool = False) -> str:
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
.mv-glass {
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
.mv-glass::before {
    content: '';
    position: absolute;
    top: 0; left: 17px;
    width: 35px; height: 3px;
    background: var(--accent, #a489ff);
    border-radius: 0 0 5px 5px;
}
.mv-glass:hover {
    transform: translateY(-2px);
    border-color: #8c79d7;
    box-shadow: 0 10px 24px rgba(8, 8, 33, 0.45);
}
.mv-glass-label {
    color: #b8bedb;
    font-weight: 600;
    font-size: 0.62rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 6px;
}
.mv-glass-value {
    color: #ffffff;
    font-weight: 800;
    font-size: 1.35rem;
    letter-spacing: -0.04em;
    line-height: 1.15;
    margin-bottom: 4px;
}
.mv-glass-note {
    color: #8793bc;
    font-size: 0.68rem;
    line-height: 1.3;
    margin-top: 6px;
}
.mv-glass-delta {
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.03em;
    margin-top: 6px;
    text-transform: uppercase;
}

.mv-banner {
    background: linear-gradient(110deg, #30265e, #211b47 55%, #171b3c);
    border-radius: 16px;
    padding: 22px 26px;
    color: #ffffff;
    box-shadow: 0 9px 30px rgba(6, 9, 23, 0.13);
    border: 1px solid #5e5090;
    margin-bottom: 20px;
    position: relative;
    overflow: hidden;
    display: flex;
    gap: 30px;
    flex-wrap: wrap;
    align-items: center;
}
.mv-banner::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 4px;
    background: linear-gradient(90deg, var(--b-accent, #a489ff) 0%, #71d5e9 100%);
}
.mv-block { flex: 1; min-width: 160px; }
.mv-block-label {
    font-size: 0.62rem;
    font-weight: 800;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-bottom: 6px;
}
.mv-block-value {
    font-size: 1.6rem;
    font-weight: 800;
    color: #ffffff;
    letter-spacing: -0.04em;
    line-height: 1.15;
    margin-bottom: 4px;
}
.mv-block-sub {
    font-size: 0.75rem;
    color: #adb6d5;
}
</style>
"""


def _inject_css():
    st.markdown(GLASS_CSS, unsafe_allow_html=True)


def _active_targets():
    return st.session_state.get("_targets") or DEFAULT_TARGETS


def _glass_card(col, label: str, value: str, accent: str = "#a489ff",
                note: str = None, delta: str = None,
                delta_color: str = None) -> None:
    note_html = f'<div class="mv-glass-note">{note}</div>' if note else ""
    delta_html = ""
    if delta:
        c = delta_color or "#77edb4"
        delta_html = f'<div class="mv-glass-delta" style="color:{c};">{delta}</div>'
    html = (
        f'<div class="mv-glass" style="--accent: {accent};">'
        f'<div class="mv-glass-label">{label}</div>'
        f'<div class="mv-glass-value">{value}</div>'
        f'{delta_html}'
        f'{note_html}'
        f'</div>'
    )
    col.markdown(html, unsafe_allow_html=True)


def _render_kpi_cards(tbl, targets):
    st.markdown("#### 💰 Ringkasan Budget vs Actual")

    total_budget = tbl["Budget"].sum()
    total_actual = tbl["Actual"].sum()
    total_variance = tbl["Variance"].sum()
    utilization = (total_actual / total_budget * 100) if total_budget > 0 else 0

    is_over = total_variance > 0
    tolerance = targets.variance_tolerance_pct
    within_tolerance = abs(utilization - 100) <= tolerance

    c1, c2, c3, c4 = st.columns(4, gap="medium")
    _glass_card(c1, "Total Budget", _fmt_rp(total_budget), "#a489ff",
                note=f"Rp {_fmt_thousand(total_budget)}")
    _glass_card(c2, "Total Actual", _fmt_rp(total_actual), "#ec3f92",
                note=f"Rp {_fmt_thousand(total_actual)}")
    _glass_card(c3, "Total Variance", _fmt_rp(total_variance),
                "#ff9eaa" if is_over else "#77edb4",
                delta=("⚠️ Over Budget" if is_over else "✅ Under Budget"),
                delta_color=("#ff9eaa" if is_over else "#77edb4"))
    _glass_card(c4, "Budget Utilization", _fmt_pct(utilization, 1),
                "#71d5e9" if within_tolerance else "#f7d578",
                delta=f"Toleransi ±{tolerance:g}%",
                delta_color=("#77edb4" if within_tolerance else "#f7d578"))

    if is_over:
        html = (
            f'<div class="mv-banner" style="--b-accent: #ff9eaa;">'
            f'<div class="mv-block">'
            f'<div class="mv-block-label" style="color:#ff9eaa;">⚠️ STATUS BUDGET</div>'
            f'<div class="mv-block-value">Over Budget</div>'
            f'<div class="mv-block-sub">Total variance {_fmt_rp(total_variance)}</div>'
            f'</div>'
            f'<div class="mv-block">'
            f'<div class="mv-block-label" style="color:#c9b9f8;">💰 TOTAL BUDGET</div>'
            f'<div class="mv-block-value">{_fmt_rp(total_budget)}</div>'
            f'<div class="mv-block-sub">Alokasi</div>'
            f'</div>'
            f'<div class="mv-block">'
            f'<div class="mv-block-label" style="color:#c9b9f8;">📊 UTILIZATION</div>'
            f'<div class="mv-block-value">{_fmt_pct(utilization, 1)}</div>'
            f'<div class="mv-block-sub">Dari budget</div>'
            f'</div>'
            f'</div>'
        )
    else:
        html = (
            f'<div class="mv-banner" style="--b-accent: #77edb4;">'
            f'<div class="mv-block">'
            f'<div class="mv-block-label" style="color:#77edb4;">✅ STATUS BUDGET</div>'
            f'<div class="mv-block-value">Under Budget</div>'
            f'<div class="mv-block-sub">Penghematan {_fmt_rp(abs(total_variance))}</div>'
            f'</div>'
            f'<div class="mv-block">'
            f'<div class="mv-block-label" style="color:#c9b9f8;">💰 TOTAL BUDGET</div>'
            f'<div class="mv-block-value">{_fmt_rp(total_budget)}</div>'
            f'<div class="mv-block-sub">Alokasi</div>'
            f'</div>'
            f'<div class="mv-block">'
            f'<div class="mv-block-label" style="color:#c9b9f8;">📊 UTILIZATION</div>'
            f'<div class="mv-block-value">{_fmt_pct(utilization, 1)}</div>'
            f'<div class="mv-block-sub">Dari budget</div>'
            f'</div>'
            f'</div>'
        )
    st.markdown(html, unsafe_allow_html=True)


def _render_bar_chart(tbl):
    st.markdown("#### 📊 Variance per Kategori")
    st.caption("Perbandingan Budget vs Actual untuk setiap kategori biaya.")

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Budget", x=tbl["Category"], y=tbl["Budget"],
        marker=dict(color=COLORS["primary"], line=dict(width=0)),
        text=[f"<b>{_fmt_rp(v, compact=True)}</b>" for v in tbl["Budget"]],
        textposition="outside",
        textfont=dict(size=11, color=COLORS["primary_light"], family="DM Sans"),
        cliponaxis=False,
        hovertemplate="<b>%{x}</b><br>Budget: Rp %{y:,.0f}<extra></extra>"))
    fig.add_trace(go.Bar(
        name="Actual", x=tbl["Category"], y=tbl["Actual"],
        marker=dict(color=COLORS["accent"], line=dict(width=0)),
        text=[f"<b>{_fmt_rp(v, compact=True)}</b>" for v in tbl["Actual"]],
        textposition="outside",
        textfont=dict(size=11, color="#71d5e9", family="DM Sans"),
        cliponaxis=False,
        hovertemplate="<b>%{x}</b><br>Actual: Rp %{y:,.0f}<extra></extra>"))

    fig = apply_theme(fig, height=440)
    fig.update_layout(
        barmode="group", bargap=0.35, bargroupgap=0.1,
        yaxis=dict(title=dict(text="<b>Nilai (Rp)</b>", font=dict(size=12, color=COLORS["text"])),
                   tickformat=",.0f", tickfont=dict(size=10)),
        xaxis=dict(title=dict(text="<b>Kategori</b>", font=dict(size=12, color=COLORS["text"])),
                   tickfont=dict(size=12, color=COLORS["text"])),
        legend=dict(orientation="h", y=-0.15, x=0.5, xanchor="center"),
        margin=dict(t=60, b=80, l=80, r=40))
    st.plotly_chart(fig, width='stretch')


def _render_variance_chart(tbl):
    st.markdown("#### 📉 Variance per Kategori (Rp)")
    st.caption("Berapa selisih Actual vs Budget? Merah = Over, Hijau = Under.")

    colors = [COLORS["danger"] if v > 0 else COLORS["success"] for v in tbl["Variance"]]

    fig = go.Figure(go.Bar(
        x=tbl["Category"], y=tbl["Variance"],
        marker=dict(color=colors, line=dict(width=0)),
        text=[f"<b>{'+' if v > 0 else '−'}{_fmt_rp(abs(v), compact=True)}</b>"
              for v in tbl["Variance"]],
        textposition="outside",
        textfont=dict(size=11, color=COLORS["text"], family="DM Sans"),
        cliponaxis=False,
        hovertemplate="<b>%{x}</b><br>Variance: Rp %{y:,.0f}<extra></extra>"))
    fig.add_hline(y=0, line_dash="dash", line_color=COLORS["text_muted"], line_width=1.5)

    fig = apply_theme(fig, height=380)
    fig.update_layout(
        showlegend=False,
        yaxis=dict(title=dict(text="<b>Variance (Rp)</b>", font=dict(size=12, color=COLORS["text"])),
                   tickformat=",.0f", tickfont=dict(size=10),
                   zeroline=True, zerolinecolor=COLORS["text_muted"], zerolinewidth=2),
        xaxis=dict(title=dict(text="<b>Kategori</b>", font=dict(size=12, color=COLORS["text"])),
                   tickfont=dict(size=12, color=COLORS["text"])),
        margin=dict(t=60, b=80, l=80, r=40))
    st.plotly_chart(fig, width='stretch')


def _render_table(tbl):
    st.markdown("#### 📋 Tabel Detail Variance")

    display = tbl.copy()
    display["Budget"] = display["Budget"].apply(_fmt_rp)
    display["Actual"] = display["Actual"].apply(_fmt_rp)
    display["Variance"] = display["Variance"].apply(
        lambda x: f"{'+' if x > 0 else '−'}{_fmt_rp(abs(x))}")
    display["Variance_Pct"] = display["Variance_Pct"].apply(
        lambda x: f"{_fmt_pct(x, 2)}" if pd.notna(x) else "—")
    display["Utilization_Pct"] = display["Utilization_Pct"].apply(
        lambda x: f"{_fmt_pct(x, 2)}" if pd.notna(x) else "—")
    display["Status"] = display["Status"].map({
        "Over Budget": "🔴 Over Budget",
        "Under Budget": "🟢 Under Budget",
        "On Budget": "🟡 On Budget"})
    display = display.rename(columns={
        "Variance_Pct": "Variance %",
        "Utilization_Pct": "Utilization %"})
    st.dataframe(display, width='stretch', hide_index=True)


def render(ds: Dataset, scope) -> None:
    _inject_css()
    page_header(
        title="Manufacturing Variance",
        subtitle=(f"Sumber: {ds.report.source_label} · "
                  f"Analisis Budget vs Actual per kategori biaya"),
        granularity="Total",
        period_label=format_period_label(scope),
        icon="⚖️")

    budget = ds.budget
    if budget is None or budget.empty:
        st.warning("Sheet **Budget** tidak tersedia.")
        return
    if not {"Category", "Budget"} <= set(budget.columns):
        st.error("Sheet Budget harus punya kolom **Category** dan **Budget**.")
        return
    if "Actual" not in budget.columns or budget["Actual"].isna().all():
        st.error("Kolom **Actual** belum ada atau kosong di sheet Budget.")
        return

    targets = _active_targets()
    try:
        summary = summarize(ds, scope)
        score, status, color = compute_health_score(summary, targets)
        mini_health_score(score, status, color)
    except Exception:
        pass

    section_divider(
        title="Budget vs Actual",
        subtitle="Perbandingan alokasi budget dengan realisasi aktual per kategori biaya.",
        icon="📊", badge="TOTAL", color="#a489ff",
        bg1="#242748", bg2="#1a1d3d")

    if "Period" not in budget.columns:
        st.info("ℹ️ **Sheet Budget tidak memiliki dimensi bulan.** "
                "Angka di bawah adalah **total semua periode** (Year-to-Date).")

    tbl = variance_table(budget)
    _render_kpi_cards(tbl, targets)
    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)
    _render_bar_chart(tbl)
    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)
    _render_variance_chart(tbl)
    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)
    _render_table(tbl)
    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)
    st.info(f"💡 **Toleransi variance:** ±{targets.variance_tolerance_pct:g}% (BRD 6).")