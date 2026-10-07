"""Predictive Analytics — forecast, anomali, stock-out (BRD 8)."""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from ..intel.predictive import (detect_anomalies, forecast_output,
                                 predict_slow_moving, predict_stockout)
from ..kpi import Scope, scope_production
from ..pipeline import Dataset
from .charts import COLORS, apply_theme


# ==================== FORECAST ====================

def _render_forecast(ds: Dataset, scope: Scope) -> None:
    st.subheader("📈 Forecast Output Produksi")
    st.caption("Prediksi output harian dengan Holt-Winters + confidence interval.")

    prod = scope_production(ds.production, scope)
    if prod.empty or "Date" not in prod.columns:
        st.info("Data produksi tidak tersedia.")
        return

    c1, c2 = st.columns([1, 2])
    with c1:
        periods = st.slider("Hari ke depan", 3, 30, 7)
        show_ci = st.checkbox("Tampilkan confidence interval", value=True)

    result = forecast_output(prod, periods=periods, backtest=True)

    if not result.values:
        st.warning(result.note)
        return

    # Persiapkan data historis
    df = prod.copy()
    df["Date"] = pd.to_datetime(df["Date"])
    hist = df.groupby("Date", as_index=False)["Output_Kg"].sum().sort_values("Date")

    fig = go.Figure()

    # Trace historis
    fig.add_trace(go.Scatter(
        x=hist["Date"], y=hist["Output_Kg"],
        mode="lines+markers", name="Historis",
        line=dict(color=COLORS["primary"], width=2.5, shape="spline"),
        marker=dict(size=4, color=COLORS["primary"],
                    line=dict(color="#FFFFFF", width=1.5)),
    ))

    # Label angka di ~10 titik historis
    n_hist = len(hist)
    step = max(1, n_hist // 10)
    for i in range(0, n_hist, step):
        row = hist.iloc[i]
        fig.add_annotation(
            x=row["Date"], y=row["Output_Kg"],
            text=f"<b>{row['Output_Kg']:,.0f}</b>",
            showarrow=False, yshift=14,
            font=dict(size=9, color=COLORS["primary_dark"], family="Inter"),
            bgcolor="rgba(245, 243, 255, 0.9)",
            bordercolor=COLORS["primary_light"],
            borderwidth=1, borderpad=2,
        )

    # Trace forecast
    fig.add_trace(go.Scatter(
        x=result.dates, y=result.values,
        mode="lines+markers", name=f"Forecast ({result.method})",
        line=dict(color=COLORS["warning"], width=2.5, dash="dash"),
        marker=dict(size=7, color=COLORS["warning"],
                    line=dict(color="#FFFFFF", width=2)),
    ))

    # Label forecast values
    for d, v in zip(result.dates, result.values):
        fig.add_annotation(
            x=d, y=v,
            text=f"<b>{v:,.0f}</b>",
            showarrow=False, yshift=16,
            font=dict(size=9, color="#92400E", family="Inter"),
            bgcolor="rgba(255, 251, 235, 0.95)",
            bordercolor=COLORS["warning"],
            borderwidth=1, borderpad=2,
        )

    # Confidence interval
    if show_ci:
        fig.add_trace(go.Scatter(
            x=result.dates + result.dates[::-1],
            y=result.upper + result.lower[::-1],
            fill="toself", fillcolor="rgba(245,158,11,0.15)",
            line=dict(color="rgba(255,255,255,0)"),
            name="95% CI", showlegend=True,
        ))

    fig = apply_theme(fig, height=440)
    fig.update_layout(
        yaxis_title="<b>Output (Kg)</b>",
        xaxis_title="",
        hovermode="x unified",
        margin=dict(t=60, b=60, l=60, r=40),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Kartu ringkasan
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Metode", result.method)

    mape_val = result.mape
    m2.metric(
        "MAPE",
        f"{mape_val:.1f}%" if mape_val is not None else "—",
        delta=("✅ Sesuai target" if mape_val is not None and mape_val <= 15
               else "⚠️ > 15%") if mape_val is not None else None,
        delta_color=("normal" if mape_val is not None and mape_val <= 15
                     else "inverse") if mape_val is not None else "off",
    )
    m3.metric("Rata-rata Forecast", f"{sum(result.values) / len(result.values):,.0f} Kg")
    m4.metric("Total Forecast", f"{sum(result.values):,.0f} Kg")

    if result.note:
        st.caption(result.note)


# ==================== ANOMALY ====================

def _render_anomaly(ds: Dataset, scope: Scope) -> None:
    st.subheader("🔍 Outlier Detection")
    st.caption("Isolation Forest mendeteksi pola scrap di luar kebiasaan.")

    prod = scope_production(ds.production, scope)
    if prod.empty:
        st.info("Data produksi tidak tersedia.")
        return

    c1, c2 = st.columns([1, 3])
    with c1:
        contamination = st.slider(
            "Sensitivitas (%)", 1, 20, 5, 1,
            help="Estimasi % data yang dianggap anomali.",
        ) / 100

    result = detect_anomalies(prod, contamination=contamination)

    if result.total == 0:
        st.success(f"✅ Tidak ada anomali terdeteksi. (Metode: {result.method})")
        return

    # KPI Cards
    k1, k2, k3 = st.columns(3)
    k1.metric("Jumlah Anomali", result.total)
    k2.metric("Persentase", f"{result.total / len(prod) * 100:.1f}%")
    k3.metric("Metode", result.method)

    # Scatter dengan zona aman
    df = prod.copy()
    if "Date" not in df.columns:
        return

    df["Date"] = pd.to_datetime(df["Date"])
    df["Scrap_Pct"] = (df["Scrap_Kg"] / df["Input_Kg"].replace(0, pd.NA)) * 100
    df["Is_Anomaly"] = df.index.isin(result.anomalies.index)

    # Hitung threshold
    mean_scrap = df["Scrap_Pct"].mean()
    std_scrap = df["Scrap_Pct"].std()
    upper_bound = mean_scrap + 2 * std_scrap
    lower_bound = max(0, mean_scrap - 2 * std_scrap)

    # Sort: normal dulu, anomali di atas
    df_sorted = df.sort_values("Is_Anomaly")

    fig = go.Figure()

    # Zona aman
    fig.add_hrect(
        y0=lower_bound, y1=upper_bound,
        fillcolor="rgba(16, 185, 129, 0.08)",
        line_width=0,
        annotation_text="<b>Zona Normal (μ ± 2σ)</b>",
        annotation_position="top left",
        annotation_font=dict(size=10, color=COLORS["success"]),
    )

    # Normal points
    normal = df_sorted[~df_sorted["Is_Anomaly"]]
    fig.add_trace(go.Scatter(
        x=normal["Date"], y=normal["Scrap_Pct"],
        mode="markers", name="Normal",
        marker=dict(
            size=8, color=COLORS["primary"],
            line=dict(color="#FFFFFF", width=1.5),
            opacity=0.7,
        ),
        hovertemplate="<b>%{x|%d %b}</b><br>Scrap: %{y:.2f}%<extra></extra>",
    ))

    # Anomaly points
    anomalies = df_sorted[df_sorted["Is_Anomaly"]]
    fig.add_trace(go.Scatter(
        x=anomalies["Date"], y=anomalies["Scrap_Pct"],
        mode="markers", name="Anomali",
        marker=dict(
            size=13, color=COLORS["danger"], symbol="diamond",
            line=dict(color="#FFFFFF", width=2),
        ),
        hovertemplate="<b>🚨 ANOMALI</b><br>%{x|%d %b %Y}<br>Scrap: %{y:.2f}%<extra></extra>",
    ))

    # Label anomali (max 8)
    for _, row in anomalies.head(8).iterrows():
        fig.add_annotation(
            x=row["Date"], y=row["Scrap_Pct"],
            text=f"<b>{row['Scrap_Pct']:.1f}%</b>",
            showarrow=True, arrowhead=2, arrowcolor=COLORS["danger"],
            ax=0, ay=-28,
            font=dict(size=9, color="#991B1B", family="Inter"),
            bgcolor="rgba(254, 242, 242, 0.95)",
            bordercolor=COLORS["danger"],
            borderwidth=1, borderpad=3,
        )

    # Garis rata-rata
    fig.add_hline(
        y=mean_scrap,
        line_dash="dash", line_color=COLORS["primary_dark"], line_width=1.5,
        annotation_text=f"<b>AVG {mean_scrap:.2f}%</b>",
        annotation_position="right",
        annotation_font=dict(size=10, color=COLORS["primary_dark"]),
    )

    fig = apply_theme(fig, height=420)
    fig.update_layout(
        yaxis_title="<b>Scrap (%)</b>",
        xaxis_title="",
        hovermode="closest",
        margin=dict(t=40, b=60, l=60, r=100),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Detail expander
    with st.expander(f"📋 Lihat detail {result.total} anomali"):
        cols = [c for c in ("Date", "Plant", "Line", "Machine",
                            "Output_Kg", "Scrap_Kg", "Scrap_Pct")
                if c in result.anomalies.columns]
        st.dataframe(
            result.anomalies[cols].reset_index(drop=True),
            use_container_width=True,
        )


# ==================== STOCK-OUT ====================

def _render_stockout(ds: Dataset) -> None:
    st.subheader("📦 Prediksi Stock-Out")
    st.caption("Kapan material akan habis berdasarkan pemakaian rata-rata.")

    risks = predict_stockout(ds.inventory)
    if not risks:
        st.info("Data inventory tidak tersedia.")
        return

    # Kartu ringkasan
    critical = sum(1 for r in risks if r.status == "critical")
    warning = sum(1 for r in risks if r.status == "warning")
    ok = sum(1 for r in risks if r.status == "ok")

    c1, c2, c3 = st.columns(3)
    c1.metric("🔴 Kritis (<14 hari)", critical)
    c2.metric("🟡 Peringatan (<30 hari)", warning)
    c3.metric("🟢 Aman", ok)

    st.markdown("")

    # Bar chart
    st.markdown("#### 📊 Sisa Hari Sampai Stock-Out")
    st.caption("Semakin pendek = semakin urgent. Garis merah = batas kritis (14 hari).")

    df = pd.DataFrame([
        {
            "Material": r.material,
            "Days": r.days_until_empty if r.days_until_empty else 999,
            "Status": r.status,
            "Stock_Kg": r.stock_kg,
            "Daily_Usage": r.daily_usage,
        }
        for r in risks
        if r.days_until_empty is not None
    ])

    if df.empty:
        st.info("Tidak ada material dengan konsumsi terdeteksi.")
        return

    df = df.sort_values("Days", ascending=True).reset_index(drop=True)

    # Colors
    color_map = {
        "critical": COLORS["danger"],
        "warning": COLORS["warning"],
        "ok": COLORS["success"],
    }
    colors = [color_map.get(s, COLORS["text_muted"]) for s in df["Status"]]

    # Text labels
    text_labels = [
        "<b>∞</b>" if row["Days"] >= 999 else f"<b>{int(row['Days'])} hari</b>"
        for _, row in df.iterrows()
    ]

    fig = go.Figure(go.Bar(
        x=df["Material"],
        y=df["Days"].clip(upper=120),
        orientation="v",
        marker=dict(color=colors, line=dict(width=0)),
        text=text_labels,
        textposition="outside",
        textfont=dict(size=11, color=COLORS["text"], family="Inter"),
        cliponaxis=False,
        hovertemplate=(
            "<b>%{x}</b><br>"
            "Stok: %{customdata[0]:,.0f} Kg<br>"
            "Usage: %{customdata[1]:,.0f} Kg/hari<br>"
            "Sisa: %{y:.0f} hari<extra></extra>"
        ),
        customdata=df[["Stock_Kg", "Daily_Usage"]].values,
    ))

    # Threshold lines
    fig.add_hline(
        y=14, line_dash="dash", line_color=COLORS["danger"], line_width=2,
        annotation_text="<b>KRITIS (14 hari)</b>",
        annotation_position="right",
        annotation_font=dict(size=10, color=COLORS["danger"]),
    )
    fig.add_hline(
        y=30, line_dash="dash", line_color=COLORS["warning"], line_width=1.5,
        annotation_text="<b>Warning (30 hari)</b>",
        annotation_position="right",
        annotation_font=dict(size=10, color=COLORS["warning"]),
    )

    fig = apply_theme(fig, height=400)
    fig.update_layout(
        yaxis_title="<b>Sisa Hari</b>",
        xaxis_title="<b>Material</b>",
        xaxis=dict(tickfont=dict(size=10)),
        margin=dict(t=40, b=80, l=60, r=120),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Detail table
    st.markdown("#### 📋 Detail Stock")
    rows = []
    for r in risks:
        icon = {"critical": "🔴", "warning": "🟡", "ok": "🟢"}[r.status]
        rows.append({
            "Material": r.material,
            "Stok (Kg)": f"{r.stock_kg:,.0f}",
            "Usage/Bln (Kg)": f"{r.monthly_usage:,.0f}",
            "Hari Tersisa": (f"{r.days_until_empty:.0f}"
                             if r.days_until_empty is not None else "—"),
            "Status": f"{icon} {r.status.capitalize()}",
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


# ==================== SLOW-MOVING ====================

def _render_slow_moving(ds: Dataset) -> None:
    st.subheader("🐢 Prediksi Slow-Moving")
    st.caption("Material yang berisiko jadi slow-moving / dead stock.")

    results = predict_slow_moving(ds.inventory)
    if not results:
        st.info("Data inventory tidak tersedia.")
        return

    rows = []
    for r in results:
        icon = {
            "dead_stock": "⚫",
            "slow_moving": "🔴",
            "watch": "🟡",
            "ok": "🟢",
        }.get(r.risk_level, "⚪")
        rows.append({
            "Material": r.material,
            "Days Inventory": (f"{r.current_days:.0f}"
                               if r.current_days is not None else "—"),
            "Trend": r.trend,
            "Prediksi 30 hari": (f"{r.predicted_days_30d:.0f}"
                                  if r.predicted_days_30d is not None else "—"),
            "Status": f"{icon} {r.risk_level.replace('_', ' ').title()}",
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


# ==================== MAIN ====================

def render(ds: Dataset, scope: Scope) -> None:
    st.title("🔮 Predictive Analytics")
    st.caption("Forecast output, deteksi anomali scrap, prediksi stock-out (BRD 8).")

    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Forecast Output",
        "🔍 Anomali Scrap",
        "📦 Stock-Out",
        "🐢 Slow-Moving",
    ])

    with tab1:
        _render_forecast(ds, scope)
    with tab2:
        _render_anomaly(ds, scope)
    with tab3:
        _render_stockout(ds)
    with tab4:
        _render_slow_moving(ds)