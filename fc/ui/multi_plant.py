"""Multi-Plant & Cost Allocation (DARK)."""
import math

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from ..config import TARGETS as DEFAULT_TARGETS
from ..kpi import Scope, scope_production, summarize
from ..pipeline import Dataset
from .charts import CATEGORY_COLORS, COLORS, apply_theme
from .components import (
    page_header, mini_health_score, format_period_label,
    compute_health_score, section_divider,
    detect_partial_periods, partial_warning_banner,
    period_selector, filter_dataset_by_period,
    project_month_end_cogm, render_projection_card,
)


# ==================== NUMBER FORMATTERS ====================
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
.mp-glass {
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
.mp-glass::before {
    content: '';
    position: absolute;
    top: 0; left: 17px;
    width: 35px; height: 3px;
    background: var(--accent, #a489ff);
    border-radius: 0 0 5px 5px;
}
.mp-glass:hover {
    transform: translateY(-2px);
    border-color: #8c79d7;
    box-shadow: 0 10px 24px rgba(8, 8, 33, 0.45);
}
.mp-glass-label {
    color: #b8bedb;
    font-weight: 600;
    font-size: 0.62rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 6px;
}
.mp-glass-value {
    color: #ffffff;
    font-weight: 800;
    font-size: 1.45rem;
    letter-spacing: -0.04em;
    line-height: 1.15;
    margin-bottom: 4px;
}
.mp-glass-note {
    color: #8793bc;
    font-size: 0.68rem;
    line-height: 1.3;
    margin-top: 6px;
}
.mp-glass-delta {
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.03em;
    margin-top: 6px;
    text-transform: uppercase;
}

.mp-banner {
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
.mp-banner::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 4px;
    background: linear-gradient(90deg, #77edb4 0%, #71d5e9 100%);
}
.mp-block { flex: 1; min-width: 160px; }
.mp-block-label {
    font-size: 0.62rem;
    font-weight: 800;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-bottom: 6px;
}
.mp-block-value {
    font-size: 1.6rem;
    font-weight: 800;
    color: #ffffff;
    letter-spacing: -0.04em;
    line-height: 1.15;
    margin-bottom: 4px;
}
.mp-block-sub {
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
    note_html = f'<div class="mp-glass-note">{note}</div>' if note else ""
    delta_html = ""
    if delta:
        c = delta_color or "#77edb4"
        delta_html = f'<div class="mp-glass-delta" style="color:{c};">{delta}</div>'
    html = (
        f'<div class="mp-glass" style="--accent: {accent};">'
        f'<div class="mp-glass-label">{label}</div>'
        f'<div class="mp-glass-value">{value}</div>'
        f'{delta_html}'
        f'{note_html}'
        f'</div>'
    )
    col.markdown(html, unsafe_allow_html=True)


# ==================== KPI ====================
def _render_kpi(agg):
    st.markdown("#### 🏭 Ringkasan Multi-Plant")

    total_plants = len(agg)
    total_output = agg["Output_Kg"].sum()
    total_cost = agg["Cost"].sum() if agg["Cost"].notna().any() else 0
    avg_cost_kg = (total_cost / total_output) if total_output > 0 else 0
    top = agg.loc[agg["Output_Kg"].idxmax()]

    c1, c2, c3, c4 = st.columns(4, gap="medium")
    _glass_card(c1, "Jumlah Plant", str(total_plants), "#a489ff",
                note="Lokasi produksi aktif")
    _glass_card(c2, "Total Output", f"{_fmt_thousand(total_output)} Kg", "#71d5e9",
                note="Akumulasi semua plant")

    if total_cost > 0:
        _glass_card(c3, "Total Cost", _fmt_rp(total_cost), "#ec3f92",
                    note=f"Rp {_fmt_thousand(total_cost)}")
        _glass_card(c4, "Avg Cost/Kg", _fmt_rp(avg_cost_kg), "#f7d578",
                    note="Rata-rata tertimbang")
    else:
        _glass_card(c3, "Total Cost", "—", "#adb6d5",
                    note="Dimensi biaya per plant belum tersedia")
        _glass_card(c4, "Avg Cost/Kg", "—", "#adb6d5",
                    note="Data belum lengkap")

    html = (
        f'<div class="mp-banner">'
        f'<div class="mp-block">'
        f'<div class="mp-block-label" style="color:#77edb4;">🏆 TOP PERFORMER</div>'
        f'<div class="mp-block-value">{top["Plant"]}</div>'
        f'<div class="mp-block-sub">Output {_fmt_thousand(top["Output_Kg"])} Kg</div>'
        f'</div>'
        f'<div class="mp-block">'
        f'<div class="mp-block-label" style="color:#c9b9f8;">📊 SHARE OF OUTPUT</div>'
        f'<div class="mp-block-value">{_fmt_pct(top["Share_Pct"], 1)}</div>'
        f'<div class="mp-block-sub">Dari total produksi grup</div>'
        f'</div>'
        f'<div class="mp-block">'
        f'<div class="mp-block-label" style="color:#c9b9f8;">🏭 TOTAL PLANT</div>'
        f'<div class="mp-block-value">{total_plants}</div>'
        f'<div class="mp-block-sub">Lokasi aktif</div>'
        f'</div>'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def _render_output_comparison(agg):
    st.markdown("#### 📊 Perbandingan Output per Plant")
    st.caption("Total output produksi setiap plant.")

    df = agg.sort_values("Output_Kg", ascending=False).reset_index(drop=True)

    fig = go.Figure(go.Bar(
        x=df["Plant"], y=df["Output_Kg"],
        marker=dict(color=COLORS["primary"], line=dict(width=0)),
        text=[f"<b>{_fmt_thousand(v)} Kg</b>" for v in df["Output_Kg"]],
        textposition="outside",
        textfont=dict(size=12, color=COLORS["text"], family="DM Sans"),
        cliponaxis=False,
        hovertemplate="<b>%{x}</b><br>Output: %{y:,.0f} Kg<extra></extra>"))
    avg = df["Output_Kg"].mean()
    fig.add_hline(y=avg, line_dash="dash", line_color=COLORS["accent"], line_width=2,
                  annotation_text=f"<b>AVG {_fmt_thousand(avg)} Kg</b>",
                  annotation_position="right",
                  annotation_font=dict(size=11, color=COLORS["accent_dark"]))
    fig = apply_theme(fig, height=400)
    fig.update_layout(
        showlegend=False,
        yaxis=dict(title="<b>Output (Kg)</b>", tickformat=",.0f"),
        xaxis=dict(title="<b>Plant</b>", tickfont=dict(size=12)),
        margin=dict(t=60, b=60, l=80, r=100))
    st.plotly_chart(fig, width='stretch')


def _render_share_pie(agg):
    st.markdown("#### 🥧 Share of Output")
    st.caption("Porsi output setiap plant terhadap total produksi.")

    df = agg.sort_values("Output_Kg", ascending=False).reset_index(drop=True)

    fig = go.Figure(go.Pie(
        labels=df["Plant"], values=df["Output_Kg"], hole=0.55,
        marker=dict(colors=CATEGORY_COLORS[:len(df)],
                    line=dict(color="#0d1026", width=3)),
        textinfo="label+percent",
        textposition="inside",
        textfont=dict(size=11, color="#FFFFFF", family="DM Sans"),
        hovertemplate="<b>%{label}</b><br>%{value:,.0f} Kg<br>%{percent}<extra></extra>"))

    total = df["Output_Kg"].sum()
    fig.add_annotation(
        text=f"<b>{_fmt_thousand(total/1000, 1)} ton</b><br><span style='font-size:10px;color:#adb6d5'>TOTAL</span>",
        x=0.5, y=0.5, showarrow=False,
        font=dict(size=16, color=COLORS["text"], family="DM Sans"))
    fig = apply_theme(fig, height=380)
    fig.update_layout(
        showlegend=True,
        legend=dict(orientation="v", yanchor="middle", y=0.5,
                    xanchor="left", x=1.02,
                    font=dict(size=11, color=COLORS["text_axis"])))
    st.plotly_chart(fig, width='stretch')


def _render_cost_comparison(agg):
    if not agg["Cost_Kg"].notna().any():
        return

    st.markdown("#### 💰 Cost/Kg per Plant")
    st.caption("Plant mana yang paling efisien dari sisi biaya per kilogram?")

    df = agg[agg["Cost_Kg"].notna()].sort_values("Cost_Kg", ascending=True).reset_index(drop=True)
    if df.empty:
        return

    min_cost = df["Cost_Kg"].min()
    max_cost = df["Cost_Kg"].max()
    colors = []
    for v in df["Cost_Kg"]:
        if v == min_cost: colors.append(COLORS["success"])
        elif v == max_cost: colors.append(COLORS["danger"])
        else: colors.append(COLORS["warning"])

    fig = go.Figure(go.Bar(
        x=df["Cost_Kg"], y=df["Plant"], orientation="h",
        marker=dict(color=colors, line=dict(width=0)),
        text=[f"<b>{_fmt_rp(v)}/Kg</b>" for v in df["Cost_Kg"]],
        textposition="outside",
        textfont=dict(size=11, color=COLORS["text"], family="DM Sans"),
        cliponaxis=False,
        hovertemplate="<b>%{y}</b><br>Cost/Kg: Rp %{x:,.0f}<extra></extra>"))
    fig = apply_theme(fig, height=300)
    fig.update_layout(
        showlegend=False,
        xaxis=dict(title="<b>Cost/Kg (Rp)</b>", tickformat=",.0f"),
        yaxis=dict(title="", tickfont=dict(size=12)),
        margin=dict(t=40, b=60, l=140, r=120))
    st.plotly_chart(fig, width='stretch')


def _render_table(agg):
    st.markdown("#### 📋 Detail per Plant")

    df = agg.copy()
    df["Output_Formatted"] = df["Output_Kg"].apply(lambda x: f"{_fmt_thousand(x)} Kg")
    df["Share_Formatted"] = df["Share_Pct"].apply(lambda x: _fmt_pct(x, 1))

    if df["Cost"].notna().any():
        df["Cost_Formatted"] = df["Cost"].apply(
            lambda x: _fmt_rp(x) if pd.notna(x) else "—")
        df["Cost_Kg_Formatted"] = df["Cost_Kg"].apply(
            lambda x: _fmt_rp(x) if pd.notna(x) else "—")
        display = pd.DataFrame({
            "Plant": df["Plant"],
            "Output (Kg)": df["Output_Formatted"],
            "Share": df["Share_Formatted"],
            "Total Cost": df["Cost_Formatted"],
            "Cost/Kg": df["Cost_Kg_Formatted"],
            "Baris Data": df["Rows"].apply(lambda x: _fmt_thousand(x)),
        })
    else:
        display = pd.DataFrame({
            "Plant": df["Plant"],
            "Output (Kg)": df["Output_Formatted"],
            "Share": df["Share_Formatted"],
            "Baris Data": df["Rows"].apply(lambda x: _fmt_thousand(x)),
        })

    st.dataframe(display, width='stretch', hide_index=True)


def _render_insights(agg):
    st.markdown("#### 💡 Insight")
    top = agg.loc[agg["Output_Kg"].idxmax()]
    st.success(
        f"🏆 **Top Performer:** {top['Plant']} menghasilkan "
        f"**{_fmt_thousand(top['Output_Kg'])} Kg** ({_fmt_pct(top['Share_Pct'], 1)} dari total output).")

    if len(agg) > 1:
        low = agg.loc[agg["Output_Kg"].idxmin()]
        st.info(
            f"📉 **Perlu perhatian:** {low['Plant']} menghasilkan "
            f"**{_fmt_thousand(low['Output_Kg'])} Kg** ({_fmt_pct(low['Share_Pct'], 1)}%).")

    if agg["Cost_Kg"].notna().any() and len(agg[agg["Cost_Kg"].notna()]) > 1:
        best_cost = agg.loc[agg["Cost_Kg"].idxmin()]
        worst_cost = agg.loc[agg["Cost_Kg"].idxmax()]
        gap = worst_cost["Cost_Kg"] - best_cost["Cost_Kg"]
        st.warning(
            f"💰 **Efisiensi:** {best_cost['Plant']} ({_fmt_rp(best_cost['Cost_Kg'])}/Kg) "
            f"vs {worst_cost['Plant']} ({_fmt_rp(worst_cost['Cost_Kg'])}/Kg). "
            f"Selisih **{_fmt_rp(gap)}/Kg** — potensi belajar antar plant.")


# ==================== AGG ====================
def _build_agg(ds, scope, selected_period):
    costs_f, prod_f = filter_dataset_by_period(ds, selected_period)
    prod_agg = scope_production(prod_f, scope)
    if prod_agg.empty:
        return None
    agg = prod_agg.groupby("Plant", as_index=False).agg(
        Output_Kg=("Output_Kg", "sum"),
        Rows=("Output_Kg", "count"))
    if agg.empty:
        return None
    agg["Share_Pct"] = agg["Output_Kg"] / agg["Output_Kg"].sum() * 100

    if (costs_f is not None and not costs_f.empty
            and "Plant" in costs_f.columns and costs_f["Plant"].notna().any()):
        c_by_plant = costs_f.groupby("Plant", as_index=False)["Cost"].sum()
        agg = agg.merge(c_by_plant, on="Plant", how="left")
        agg["Cost"] = agg["Cost"].fillna(0)
        agg["Cost_Kg"] = agg["Cost"] / agg["Output_Kg"].replace(0, pd.NA)
    else:
        agg["Cost"] = pd.NA
        agg["Cost_Kg"] = pd.NA
    return agg


# ==================== MAIN ====================
def render(ds: Dataset, scope: Scope) -> None:
    _inject_css()
    page_header(
        title="Multi-Plant & Cost Allocation",
        subtitle=(f"Sumber: {ds.report.source_label} · "
                  f"Konsolidasi produksi & biaya lintas plant"),
        granularity="Multi",
        period_label=format_period_label(scope),
        icon="🏭")

    if ds.production is None or ds.production.empty:
        st.warning("Data produksi tidak tersedia.")
        return
    if "Plant" not in ds.production.columns:
        st.info("Kolom **Plant** tidak ada di sheet Production. Fitur multi-plant tidak tersedia.")
        return

    targets = _active_targets()
    try:
        summary = summarize(ds, scope)
        score, status, color = compute_health_score(summary, targets)
        mini_health_score(score, status, color)
    except Exception:
        pass

    section_divider(
        title="Multi-Plant Analysis",
        subtitle="Pilih periode di bawah untuk lihat breakdown bulan tertentu.",
        icon="🏭", badge="MULTI-PLANT", color="#a489ff",
        bg1="#242748", bg2="#1a1d3d")

    selected_period, periods, partials = period_selector(ds, key="mp_period_selector")

    if selected_period and selected_period in partials:
        partial_warning_banner({selected_period}, ds.production)

    st.markdown("")
    agg = _build_agg(ds, scope, selected_period)
    if agg is None or agg.empty:
        st.info("Tidak ada data produksi pada filter terpilih.")
        return

    if not agg["Cost"].notna().any():
        st.info("ℹ️ Dimensi biaya per Plant belum tersedia. Analisis Cost/Kg per Plant tidak dapat dihitung.")

    if selected_period and selected_period in partials:
        costs_f, prod_f = filter_dataset_by_period(ds, selected_period)
        proj = project_month_end_cogm(costs_f, prod_f, selected_period)
        render_projection_card(proj)

    _render_kpi(agg)
    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

    col_left, col_right = st.columns([1.4, 1], gap="medium")
    with col_left:
        _render_output_comparison(agg)
    with col_right:
        _render_share_pie(agg)

    if agg["Cost_Kg"].notna().any():
        st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)
        _render_cost_comparison(agg)

    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)
    _render_table(agg)
    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)
    _render_insights(agg)