"""Predictive Analytics — forecast, anomali, stock-out (BRD 8)."""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from ..intel.predictive import (detect_anomalies, forecast_output,
                                 predict_slow_moving, predict_stockout)
from ..kpi import Scope, scope_production
from ..pipeline import Dataset


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

    # Bangun DataFrame historis + forecast
    df = prod.copy()
    df["Date"] = pd.to_datetime(df["Date"])
    hist = df.groupby("Date", as_index=False)["Output_Kg"].sum().sort_values("Date")

    fig = go.Figure()

    # Historis
    fig.add_trace(go.Scatter(
        x=hist["Date"], y=hist["Output_Kg"],
        mode="lines", name="Historis",
        line=dict(color="#3b82f6", width=2),
    ))

    # Forecast
    fig.add_trace(go.Scatter(
        x=result.dates, y=result.values,
        mode="lines+markers", name=f"Forecast ({result.method})",
        line=dict(color="#f59e0b", width=2, dash="dash"),
        marker=dict(size=6),
    ))

    # Confidence interval
    if show_ci:
        fig.add_trace(go.Scatter(
            x=result.dates + result.dates[::-1],
            y=result.upper + result.lower[::-1],
            fill="toself", fillcolor="rgba(245,158,11,0.15)",
            line=dict(color="rgba(255,255,255,0)"),
            name="95% CI", showlegend=True,
        ))

    fig.update_layout(
        height=420, margin=dict(t=20, b=40, l=20, r=20),
        yaxis_title="Kg", xaxis_title="",
        hovermode="x unified", legend=dict(orientation="h", y=-0.15),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Kartu ringkasan
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Metode", result.method)
    m2.metric("MAPE",
              f"{result.mape:.1f}%" if result.mape is not None else "—",
              delta="✅ Sesuai target" if result.mape is not None and result.mape <= 15 else
                    "⚠️ > 15%",
              delta_color="normal" if result.mape is not None and result.mape <= 15 else "inverse")
    m3.metric("Rata-rata Forecast", f"{sum(result.values) / len(result.values):,.0f} Kg")
    m4.metric("Total Forecast", f"{sum(result.values):,.0f} Kg")

    if result.note:
        st.caption(result.note)


def _render_anomaly(ds: Dataset, scope: Scope) -> None:
    st.subheader("🔍 Deteksi Anomali Scrap")
    st.caption("Isolation Forest untuk mendeteksi pola scrap di luar kebiasaan.")

    prod = scope_production(ds.production, scope)
    if prod.empty:
        st.info("Data produksi tidak tersedia.")
        return

    c1, c2 = st.columns([1, 3])
    with c1:
        contamination = st.slider("Sensitivitas (%)", 1, 20, 5, 1,
                                   help="Estimasi persentase data yang dianggap anomali.") / 100

    result = detect_anomalies(prod, contamination=contamination)

    if result.total == 0:
        st.success(f"✅ Tidak ada anomali terdeteksi. (Metode: {result.method})")
        return

    c1, c2, c3 = st.columns(3)
    c1.metric("Jumlah Anomali", result.total)
    c2.metric("Persentase", f"{result.total / len(prod) * 100:.1f}%")
    c3.metric("Metode", result.method)

    st.markdown(f"**Threshold:** {result.threshold_info}")

    # Tampilkan scatter dengan titik anomali
    df = prod.copy()
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"])
        df["Scrap_Pct"] = (df["Scrap_Kg"] / df["Input_Kg"].replace(0, pd.NA)) * 100
        df["Is_Anomaly"] = df.index.isin(result.anomalies.index)

        fig = px.scatter(
            df, x="Date", y="Scrap_Pct",
            color="Is_Anomaly",
            color_discrete_map={True: "#dc2626", False: "#3b82f6"},
            labels={"Is_Anomaly": "Anomali", "Scrap_Pct": "Scrap (%)"},
            title="Sebaran Scrap Harian",
        )
        fig.update_layout(height=340, margin=dict(t=40, b=20, l=20, r=20))
        st.plotly_chart(fig, use_container_width=True)

    with st.expander(f"Lihat detail {result.total} anomali"):
        cols = [c for c in ("Date", "Plant", "Line", "Machine",
                            "Output_Kg", "Scrap_Kg", "Scrap_Pct")
                if c in result.anomalies.columns]
        st.dataframe(result.anomalies[cols].reset_index(drop=True),
                     use_container_width=True)


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

    # Tabel
    rows = []
    for r in risks:
        icon = {"critical": "🔴", "warning": "🟡", "ok": "🟢"}[r.status]
        rows.append({
            "Material": r.material,
            "Stok (Kg)": f"{r.stock_kg:,.0f}",
            "Usage/Bln (Kg)": f"{r.monthly_usage:,.0f}",
            "Hari Tersisa": f"{r.days_until_empty:.0f}" if r.days_until_empty is not None else "—",
            "Status": f"{icon} {r.status.capitalize()}",
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


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
            "Days Inventory": f"{r.current_days:.0f}" if r.current_days is not None else "—",
            "Trend": r.trend,
            "Prediksi 30 hari": f"{r.predicted_days_30d:.0f}" if r.predicted_days_30d is not None else "—",
            "Status": f"{icon} {r.risk_level.replace('_', ' ').title()}",
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


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