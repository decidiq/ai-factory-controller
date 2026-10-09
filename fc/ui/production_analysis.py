"""Production Analysis - data-driven via fc.kpi (BRD 6) — Premium UI."""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from ..config import TARGETS as DEFAULT_TARGETS
from ..kpi import (Scope, oee_kpi, scrap_kpi, scope_production, summarize, yield_kpi)
from ..pipeline import Dataset
from .charts import COLORS, apply_theme, line_chart
from .components import (page_header, mini_health_score, format_period_label,
                         compute_health_score, section_divider)


# ==================== CSS GLASSMORPHISM ====================
GLASS_CSS = """
<style>
.pa-glass {
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
.pa-glass::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, var(--accent, #8B5CF6) 0%, #EC4899 100%);
}
.pa-glass:hover {
    transform: translateY(-3px);
    box-shadow: 0 16px 32px rgba(139, 92, 246, 0.18);
    border-color: rgba(139, 92, 246, 0.6);
}
.pa-glass-label {
    color: #6D28D9;
    font-weight: 700;
    font-size: 0.66rem;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    margin-bottom: 6px;
}
.pa-glass-value {
    color: #0F172A;
    font-weight: 800;
    font-size: 1.4rem;
    letter-spacing: -0.5px;
    line-height: 1.1;
    margin-bottom: 2px;
}
.pa-glass-note {
    color: #94A3B8;
    font-size: 0.68rem;
    font-style: italic;
    line-height: 1.3;
}

/* Performance Banner */
.perf-banner {
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
.perf-banner::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 4px;
    background: linear-gradient(90deg, #10B981 0%, #EC4899 100%);
}
.perf-block { flex: 1; min-width: 200px; }
.perf-label {
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    margin-bottom: 6px;
}
.perf-value {
    font-size: 1.5rem;
    font-weight: 900;
    color: #FFFFFF;
    letter-spacing: -0.5px;
    line-height: 1.1;
    margin-bottom: 4px;
}
.perf-sub {
    font-size: 0.78rem;
    color: #94A3B8;
}
</style>
"""


def _inject_css():
    st.markdown(GLASS_CSS, unsafe_allow_html=True)


# ==================== HELPERS ====================
def _active_targets():
    return st.session_state.get("_targets") or DEFAULT_TARGETS


def _fmt(kpi, fmt: str, default: str = "—") -> str:
    if kpi.available:
        return fmt.format(kpi.value)
    return default


def _glass_card(col, label: str, value: str, accent: str = "#8B5CF6",
                note: str = None) -> None:
    note_html = f'<div class="pa-glass-note">{note}</div>' if note else ""
    html = (
        f'<div class="pa-glass" style="--accent: {accent};">'
        f'<div class="pa-glass-label">{label}</div>'
        f'<div class="pa-glass-value">{value}</div>'
        f'{note_html}'
        f'</div>'
    )
    col.markdown(html, unsafe_allow_html=True)


# ==================== KPI CARDS ====================
def _render_kpi_cards(prod, y, s, o):
    st.markdown("### 📊 Ringkasan Produksi")

    c = st.columns(4)
    _glass_card(c[0], "Yield", _fmt(y, "{:.2f}%"), "#10B981",
                note=y.note if not y.available else None)
    _glass_card(c[1], "Scrap", _fmt(s, "{:.2f}%"), "#F59E0B",
                note=s.note if not s.available else None)
    _glass_card(c[2], "OEE", _fmt(o.oee, "{:.2f}%"), "#3B82F6",
                note=o.oee.note if not o.oee.available else None)
    _glass_card(c[3], "Baris Data", f"{len(prod):,}", "#8B5CF6",
                note="Total baris produksi terfilter")

    with st.expander("🔍 Rincian OEE (Availability × Performance × Quality)"):
        cc = st.columns(3)
        _glass_card(cc[0], "Availability", _fmt(o.availability, "{:.2f}%"), "#8B5CF6")
        _glass_card(cc[1], "Performance", _fmt(o.performance, "{:.2f}%"), "#A855F7")
        _glass_card(cc[2], "Quality", _fmt(o.quality, "{:.2f}%"), "#EC4899")


# ==================== PERFORMANCE BANNER ====================
def _render_perf_banner(prod):
    if "Line" not in prod.columns or prod.empty:
        return

    try:
        agg = prod.groupby("Line", as_index=False).agg(
            Output=("Output_Kg", "sum"),
            Input=("Input_Kg", "sum") if "Input_Kg" in prod.columns else ("Output_Kg", "sum"),
        )
        if "Input_Kg" in prod.columns:
            agg["Yield_%"] = (agg["Output"] / agg["Input"].replace(0, pd.NA)) * 100
            agg = agg.dropna(subset=["Yield_%"])
            if agg.empty:
                return

            best = agg.loc[agg["Yield_%"].idxmax()]
            worst = agg.loc[agg["Yield_%"].idxmin()]

            html = (
                f'<div class="perf-banner">'
                f'<div class="perf-block">'
                f'<div class="perf-label" style="color:#34D399;">🏆 Line Terbaik</div>'
                f'<div class="perf-value">{best["Line"]}</div>'
                f'<div class="perf-sub">Yield {best["Yield_%"]:.2f}% · Output {best["Output"]:,.0f} Kg</div>'
                f'</div>'
                f'<div class="perf-block">'
                f'<div class="perf-label" style="color:#F87171;">⚠️ Line Perlu Perhatian</div>'
                f'<div class="perf-value">{worst["Line"]}</div>'
                f'<div class="perf-sub">Yield {worst["Yield_%"]:.2f}% · Output {worst["Output"]:,.0f} Kg</div>'
                f'</div>'
                f'</div>'
            )
            st.markdown(html, unsafe_allow_html=True)
    except Exception:
        return


# ==================== MONTHLY SECTION ====================
def _render_monthly_section(prod):
    """Section khusus: trend BULANAN."""
    section_divider(
        title="Analisis Bulanan",
        subtitle="Ringkasan performa per bulan. Cocok untuk laporan & tren jangka menengah.",
        icon="📆",
        badge="BULANAN",
        color="#8B5CF6",
        bg1="#F5F3FF",
        bg2="#FFFFFF",
    )

    # Persiapkan data bulanan
    df = prod.copy()
    df["Date"] = pd.to_datetime(df["Date"])
    df["Period"] = df["Date"].dt.strftime("%Y-%m")

    # Agregasi per bulan
    cols_to_sum = ["Output_Kg"]
    if "Input_Kg" in df.columns:
        cols_to_sum.append("Input_Kg")
    if "Scrap_Kg" in df.columns:
        cols_to_sum.append("Scrap_Kg")

    monthly = df.groupby("Period", as_index=False)[cols_to_sum].sum().sort_values("Period")

    if monthly.empty:
        st.info("Tidak ada data bulanan pada filter terpilih.")
        return

    # Hitung KPI per bulan
    if "Input_Kg" in monthly.columns:
        monthly["Yield_%"] = (monthly["Output_Kg"] / monthly["Input_Kg"].replace(0, pd.NA)) * 100
    if "Scrap_Kg" in monthly.columns and "Input_Kg" in monthly.columns:
        monthly["Scrap_%"] = (monthly["Scrap_Kg"] / monthly["Input_Kg"].replace(0, pd.NA)) * 100

    # Bar chart: Output per bulan
    fig = go.Figure(go.Bar(
        x=monthly["Period"],
        y=monthly["Output_Kg"],
        marker=dict(
            color=monthly["Output_Kg"],
            colorscale=[[0, "#C4B5FD"], [1, "#8B5CF6"]],
            line=dict(width=0),
        ),
        text=[f"<b>{v:,.0f} Kg</b>" for v in monthly["Output_Kg"]],
        textposition="outside",
        textfont=dict(size=11, color=COLORS["text"], family="Inter"),
        cliponaxis=False,
        hovertemplate="<b>%{x}</b><br>Output: %{y:,.0f} Kg<extra></extra>",
    ))

    avg = monthly["Output_Kg"].mean()
    fig.add_hline(
        y=avg, line_dash="dash", line_color=COLORS["accent"], line_width=2,
        annotation_text=f"<b>AVG {avg:,.0f} Kg</b>",
        annotation_position="right",
        annotation_font=dict(size=10, color=COLORS["accent_dark"]),
    )

    fig = apply_theme(fig, height=320)
    fig.update_layout(
        showlegend=False,
        yaxis=dict(title="<b>Total Output (Kg)</b>", tickformat=",.0f"),
        xaxis=dict(title="<b>Bulan</b>"),
        margin=dict(t=40, b=50, l=80, r=100),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Tabel MoM
    st.markdown("**Detail per Bulan:**")
    table_rows = []
    for _, row in monthly.iterrows():
        entry = {
            "Bulan": row["Period"],
            "Output (Kg)": f"{row['Output_Kg']:,.0f}",
        }
        if "Input_Kg" in monthly.columns:
            entry["Input (Kg)"] = f"{row['Input_Kg']:,.0f}"
        if "Yield_%" in monthly.columns and pd.notna(row["Yield_%"]):
            entry["Yield (%)"] = f"{row['Yield_%']:.2f}%"
        if "Scrap_%" in monthly.columns and pd.notna(row["Scrap_%"]):
            entry["Scrap (%)"] = f"{row['Scrap_%']:.2f}%"
        table_rows.append(entry)

    st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)


# ==================== DAILY SECTION ====================
def _render_daily_section(prod, daily):
    """Section khusus: trend HARIAN."""
    section_divider(
        title="Analisis Harian",
        subtitle="Detail per hari. Cocok untuk investigasi operasional & deteksi anomali.",
        icon="📅",
        badge="HARIAN",
        color="#3B82F6",
        bg1="#EFF6FF",
        bg2="#FFFFFF",
    )

    # Statistik harian
    _render_top_stats(daily)

    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

    # Trend chart
    _render_trend_chart(daily)

    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

    # Detail table
    _render_detail_table(prod)


def _render_top_stats(daily):
    total = daily["Output_Kg"].sum()
    avg = daily["Output_Kg"].mean()
    maxv = daily["Output_Kg"].max()
    minv = daily["Output_Kg"].min()

    max_date = daily.loc[daily["Output_Kg"].idxmax(), "Date"]
    min_date = daily.loc[daily["Output_Kg"].idxmin(), "Date"]

    c1, c2, c3, c4 = st.columns(4)
    _glass_card(c1, "Σ Total Output", f"{total:,.0f} Kg", "#8B5CF6",
                note=f"{len(daily)} hari produksi")
    _glass_card(c2, "μ Rata-rata", f"{avg:,.0f} Kg", "#3B82F6",
                note="per hari")
    _glass_card(c3, "▲ Tertinggi", f"{maxv:,.0f} Kg", "#10B981",
                note=max_date.strftime("%d %b %Y"))
    _glass_card(c4, "▼ Terendah", f"{minv:,.0f} Kg", "#EF4444",
                note=min_date.strftime("%d %b %Y"))


# ==================== TREND CHART ====================
def _render_trend_chart(daily):
    n = len(daily)
    if n <= 10:
        step = 1
    elif n <= 20:
        step = 2
    elif n <= 40:
        step = 3
    else:
        step = 5

    has_scrap = "Scrap_Kg" in daily.columns
    fig = make_subplots(specs=[[{"secondary_y": has_scrap}]])

    fig.add_trace(
        go.Scatter(
            x=daily["Date"], y=daily["Output_Kg"],
            mode="lines+markers", name="Output (Kg)",
            line=dict(color=COLORS["primary"], width=2.5, shape="spline"),
            marker=dict(size=5, color=COLORS["primary"],
                        line=dict(color="#FFFFFF", width=1.5)),
        ),
        secondary_y=False,
    )

    if has_scrap:
        fig.add_trace(
            go.Scatter(
                x=daily["Date"], y=daily["Scrap_Kg"],
                mode="lines+markers", name="Scrap (Kg)",
                line=dict(color=COLORS["danger"], width=2.5, shape="spline"),
                marker=dict(size=5, color=COLORS["danger"],
                            line=dict(color="#FFFFFF", width=1.5)),
            ),
            secondary_y=True,
        )

    for i in range(0, n, step):
        row = daily.iloc[i]
        fig.add_annotation(
            x=row["Date"], y=row["Output_Kg"],
            text=f"<b>{row['Output_Kg']:,.0f}</b>",
            showarrow=False, yshift=14,
            font=dict(size=9, color=COLORS["primary_dark"], family="Inter"),
            bgcolor="rgba(245, 243, 255, 0.9)",
            bordercolor=COLORS["primary_light"],
            borderwidth=1, borderpad=2,
        )

    avg_output = daily["Output_Kg"].mean()
    fig.add_hline(
        y=avg_output, line_dash="dash",
        line_color=COLORS["primary_dark"], line_width=1.5,
        annotation_text=f"<b>AVG Output {avg_output:,.0f} Kg</b>",
        annotation_position="top left",
        annotation_font=dict(size=10, color=COLORS["primary_dark"], family="Inter"),
        secondary_y=False,
    )

    fig = apply_theme(fig, height=420)
    fig.update_layout(
        hovermode="x unified",
        margin=dict(t=50, b=60, l=60, r=60),
        legend=dict(orientation="h", y=-0.15, x=0.5, xanchor="center"),
    )
    fig.update_xaxes(title_text="")
    fig.update_yaxes(title_text="<b>Output (Kg)</b>", secondary_y=False,
                     tickfont=dict(size=10))
    if has_scrap:
        fig.update_yaxes(
            title_text="<b>Scrap (Kg)</b>", secondary_y=True,
            tickfont=dict(size=10, color=COLORS["danger"]),
            title_font=dict(color=COLORS["danger"], size=12),
        )

    st.plotly_chart(fig, use_container_width=True)


# ==================== DETAIL TABLE ====================
def _render_detail_table(prod):
    st.markdown(f"**Detail Data Produksi** — {len(prod):,} baris")
    st.caption("Sortir dengan klik header kolom.")

    display_cols = [c for c in (
        "Date", "Plant", "Line", "Machine", "Product",
        "Input_Kg", "Output_Kg", "Scrap_Kg",
        "Planned_Time_Min", "Downtime_Min", "Ideal_Rate_Kg_per_Min",
    ) if c in prod.columns]

    st.dataframe(
        prod[display_cols],
        use_container_width=True,
        hide_index=True,
        height=420,
    )


# ==================== MAIN RENDER ====================
def render(ds: Dataset, scope: Scope) -> None:
    _inject_css()

    prod = scope_production(ds.production, scope)

    page_header(
        title="Production Analysis",
        subtitle=(
            f"Sumber: {ds.report.source_label} · "
            f"{len(prod):,} baris produksi dalam periode terpilih"
        ),
        granularity="Multi",
        period_label=format_period_label(scope),
        icon="📈",
    )

    if prod.empty:
        st.info("Tidak ada data produksi pada filter terpilih.")
        return

    # KPI
    y = yield_kpi(prod)
    s = scrap_kpi(prod, y)
    o = oee_kpi(prod)

    # Mini health score
    targets = _active_targets()
    try:
        summary = summarize(ds, scope)
        score, status, color = compute_health_score(summary, targets)
        mini_health_score(score, status, color)
    except Exception:
        pass

    # KPI Cards + Perf Banner
    _render_kpi_cards(prod, y, s, o)
    _render_perf_banner(prod)

    # ===== SECTION 1: BULANAN =====
    _render_monthly_section(prod)

    # ===== SECTION 2: HARIAN =====
    cols_y = ["Output_Kg"] + (["Scrap_Kg"] if "Scrap_Kg" in prod.columns else [])
    daily = prod.groupby("Date", as_index=False)[cols_y].sum().sort_values("Date")
    _render_daily_section(prod, daily)