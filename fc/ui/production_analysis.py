"""Production Analysis - data-driven via fc.kpi (BRD 6)."""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from ..kpi import (Scope, oee_kpi, scrap_kpi, scope_production, yield_kpi)
from ..pipeline import Dataset
from .charts import COLORS, apply_theme, line_chart


def _metric(col, label: str, kpi, fmt: str):
    if kpi.available:
        col.metric(
            label + (" (est.)" if kpi.status == "estimate" else ""),
            fmt.format(kpi.value),
        )
        if kpi.note:
            col.caption(kpi.note)
    else:
        col.metric(label, "—")
        col.caption(f"Tidak tersedia: {kpi.note}")


def _render_kpi_cards(prod, y, s, o):
    """KPI cards di atas chart."""
    st.markdown("### 📊 Ringkasan Produksi")

    c = st.columns(4)
    _metric(c[0], "Yield", y, "{:.2f}%")
    _metric(c[1], "Scrap", s, "{:.2f}%")
    _metric(c[2], "OEE", o.oee, "{:.2f}%")
    c[3].metric("Baris Data", f"{len(prod):,}")

    # OEE breakdown
    with st.expander("🔍 Rincian OEE (Availability × Performance × Quality)"):
        cc = st.columns(3)
        _metric(cc[0], "Availability", o.availability, "{:.2f}%")
        _metric(cc[1], "Performance", o.performance, "{:.2f}%")
        _metric(cc[2], "Quality", o.quality, "{:.2f}%")


def _render_top_stats(daily):
    """4 kartu statistik: Total, Rata-rata, Max, Min."""
    st.markdown("### 📈 Statistik Output Harian")

    total = daily["Output_Kg"].sum()
    avg = daily["Output_Kg"].mean()
    maxv = daily["Output_Kg"].max()
    minv = daily["Output_Kg"].min()

    max_date = daily.loc[daily["Output_Kg"].idxmax(), "Date"]
    min_date = daily.loc[daily["Output_Kg"].idxmin(), "Date"]

    # Custom HTML cards biar lebih menarik
    def _stat_card(icon, label, value, sub, color):
        return f"""
        <div style="
            background: #FFFFFF;
            border: 1px solid #E9D5FF;
            border-left: 4px solid {color};
            border-radius: 12px;
            padding: 16px 18px;
            height: 100%;
            box-shadow: 0 2px 6px rgba(139, 92, 246, 0.05);
        ">
            <div style="
                font-size: 0.7rem;
                color: {color};
                font-weight: 700;
                letter-spacing: 0.8px;
                text-transform: uppercase;
                margin-bottom: 6px;
            ">{icon} {label}</div>
            <div style="
                font-size: 1.5rem;
                font-weight: 800;
                color: #0F172A;
                letter-spacing: -0.5px;
                line-height: 1.1;
            ">{value}</div>
            <div style="
                font-size: 0.75rem;
                color: #64748B;
                margin-top: 4px;
            ">{sub}</div>
        </div>
        """

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(_stat_card("Σ", "Total Output", f"{total:,.0f} Kg",
                                f"{len(daily)} hari", COLORS["primary"]),
                    unsafe_allow_html=True)
    with c2:
        st.markdown(_stat_card("μ", "Rata-rata", f"{avg:,.0f} Kg",
                                "per hari", COLORS["info"]),
                    unsafe_allow_html=True)
    with c3:
        st.markdown(_stat_card("▲", "Tertinggi", f"{maxv:,.0f} Kg",
                                f"{max_date.strftime('%d %b')}", COLORS["success"]),
                    unsafe_allow_html=True)
    with c4:
        st.markdown(_stat_card("▼", "Terendah", f"{minv:,.0f} Kg",
                                f"{min_date.strftime('%d %b')}", COLORS["danger"]),
                    unsafe_allow_html=True)


def _render_trend_chart(daily):
    """Line chart output + scrap dengan label & AVG line."""
    st.markdown("### 📈 Performance Trend Harian")
    st.caption("Output harian dan scrap dalam periode terpilih. Angka di setiap titik = value.")

    # Determine label step
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

    # Dual axis: output (kiri) + scrap (kanan)
    from plotly.subplots import make_subplots
    fig = make_subplots(specs=[[{"secondary_y": has_scrap}]])

    # Trace Output
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

    # Trace Scrap
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

    # Label untuk Output
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

    # Garis AVG Output
    avg_output = daily["Output_Kg"].mean()
    fig.add_hline(
        y=avg_output,
        line_dash="dash",
        line_color=COLORS["primary_dark"],
        line_width=1.5,
        annotation_text=f"<b>AVG Output {avg_output:,.0f} Kg</b>",
        annotation_position="top left",
        annotation_font=dict(size=10, color=COLORS["primary_dark"], family="Inter"),
        secondary_y=False,
    )

    # Apply theme
    fig = apply_theme(fig, height=420)
    fig.update_layout(
        hovermode="x unified",
        margin=dict(t=50, b=60, l=60, r=60),
        legend=dict(orientation="h", y=-0.15, x=0.5, xanchor="center"),
    )
    fig.update_xaxes(title_text="")
    fig.update_yaxes(
        title_text="<b>Output (Kg)</b>",
        secondary_y=False,
        tickfont=dict(size=10),
    )
    if has_scrap:
        fig.update_yaxes(
            title_text="<b>Scrap (Kg)</b>",
            secondary_y=True,
            tickfont=dict(size=10, color=COLORS["danger"]),
            title_font=dict(color=COLORS["danger"], size=12),
        )

    st.plotly_chart(fig, use_container_width=True)


def _render_detail_table(prod):
    """Tabel detail produksi."""
    st.markdown("### 📋 Detail Data Produksi")
    st.caption(f"Menampilkan {len(prod):,} baris. Sortir dengan klik header kolom.")

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


def render(ds: Dataset, scope: Scope) -> None:
    st.title("📈 Production Analysis")
    st.caption(
        "Analisis performa produksi harian, yield, scrap, dan OEE "
        "berdasarkan data aktual pabrik."
    )

    prod = scope_production(ds.production, scope)
    if prod.empty:
        st.info("Tidak ada data produksi pada filter terpilih.")
        return

    # KPI
    y = yield_kpi(prod)
    s = scrap_kpi(prod, y)
    o = oee_kpi(prod)

    # 1. KPI Cards
    _render_kpi_cards(prod, y, s, o)

    st.markdown("---")

    # 2. Siapkan daily data
    cols_y = ["Output_Kg"] + (["Scrap_Kg"] if "Scrap_Kg" in prod.columns else [])
    daily = prod.groupby("Date", as_index=False)[cols_y].sum().sort_values("Date")

    # 3. Statistik ringkasan (Total, Avg, Max, Min)
    _render_top_stats(daily)

    st.markdown("---")

    # 4. Trend chart dengan label
    _render_trend_chart(daily)

    st.markdown("---")

    # 5. Detail table
    _render_detail_table(prod)