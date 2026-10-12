"""Predictive Analytics (DARK + Format Indonesia)."""
import math

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from ..intel.predictive import (detect_anomalies, forecast_output,
                                 predict_slow_moving, predict_stockout)
from ..kpi import Scope, scope_production
from ..pipeline import Dataset
from .charts import COLORS, apply_theme
from .components import render_table


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


# ==================== CSS (DARK) ====================
GLASS_CSS = """
<style>
.pr-glass {
    position: relative;
    background: linear-gradient(145deg, #1a1d3d, #151933);
    border: 1px solid #343858;
    border-radius: 12px;
    padding: 16px 18px;
    box-shadow: 0 9px 30px rgba(6, 9, 23, 0.13);
    transition: transform 0.2s ease, border-color 0.2s ease;
    overflow: hidden;
    min-height: 110px;
}
.pr-glass::before {
    content: '';
    position: absolute;
    top: 0; left: 17px;
    width: 35px; height: 3px;
    background: var(--accent, #a489ff);
    border-radius: 0 0 5px 5px;
}
.pr-glass:hover {
    transform: translateY(-2px);
    border-color: #8c79d7;
    box-shadow: 0 10px 24px rgba(8, 8, 33, 0.45);
}
.pr-glass-label {
    color: #b8bedb;
    font-weight: 600;
    font-size: 0.62rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 6px;
}
.pr-glass-value {
    color: #ffffff;
    font-weight: 800;
    font-size: 1.45rem;
    letter-spacing: -0.04em;
    line-height: 1.15;
    margin-bottom: 4px;
}
.pr-glass-note {
    color: #8793bc;
    font-size: 0.68rem;
    line-height: 1.3;
    margin-top: 6px;
}
.pr-glass-delta {
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.03em;
    margin-top: 6px;
    text-transform: uppercase;
}

.pr-banner {
    background: linear-gradient(110deg, #30265e, #211b47 55%, #171b3c);
    border: 1px solid #5e5090;
    border-radius: 16px;
    padding: 22px 26px;
    color: #ffffff;
    box-shadow: 0 9px 30px rgba(6, 9, 23, 0.13);
    margin-bottom: 20px;
    position: relative;
    overflow: hidden;
}
.pr-banner::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 4px;
    background: linear-gradient(90deg, var(--b-accent, #a489ff) 0%, #71d5e9 100%);
}
.pr-banner-label {
    font-size: 0.62rem;
    font-weight: 800;
    letter-spacing: 0.12em;
    color: var(--b-label, #f7d578);
    text-transform: uppercase;
    margin-bottom: 8px;
}
.pr-banner-title {
    font-size: 1.3rem;
    font-weight: 800;
    color: #ffffff;
    letter-spacing: -0.03em;
    line-height: 1.15;
    margin-bottom: 6px;
}
.pr-banner-desc {
    font-size: 0.85rem;
    color: #dce0f4;
    line-height: 1.5;
}
.pr-banner-desc strong { color: #f7d578; }
</style>
"""


def _inject_css():
    st.markdown(GLASS_CSS, unsafe_allow_html=True)


def _glass_card(col, label: str, value: str, accent: str = "#a489ff",
                note: str = None, delta: str = None,
                delta_color: str = None) -> None:
    note_html = f'<div class="pr-glass-note">{note}</div>' if note else ""
    delta_html = ""
    if delta:
        c = delta_color or "#77edb4"
        delta_html = f'<div class="pr-glass-delta" style="color:{c};">{delta}</div>'
    html = (
        f'<div class="pr-glass" style="--accent: {accent};">'
        f'<div class="pr-glass-label">{label}</div>'
        f'<div class="pr-glass-value">{value}</div>'
        f'{delta_html}'
        f'{note_html}'
        f'</div>')
    col.markdown(html, unsafe_allow_html=True)


def _banner(label: str, title: str, desc: str = "",
            accent: str = "#a489ff", label_color: str = "#f7d578") -> None:
    desc_html = f'<div class="pr-banner-desc">{desc}</div>' if desc else ""
    html = (
        f'<div class="pr-banner" style="--b-accent: {accent}; --b-label: {label_color};">'
        f'<div class="pr-banner-label">{label}</div>'
        f'<div class="pr-banner-title">{title}</div>'
        f'{desc_html}'
        f'</div>')
    st.markdown(html, unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def _cached_forecast(_prod_hash: str, periods: int):
    return None


@st.cache_data(show_spinner=False)
def _cached_anomalies(_prod_hash: str, contamination: float):
    return None


def _render_forecast(ds: Dataset, scope: Scope) -> None:
    st.markdown("### 📈 Forecast Output Produksi")
    st.caption("Prediksi output harian dengan Holt-Winters + confidence interval.")

    prod = scope_production(ds.production, scope)
    if prod.empty or "Date" not in prod.columns:
        st.info("Data produksi tidak tersedia.")
        return

    c1, c2 = st.columns([1, 2], gap="medium")
    with c1:
        periods = st.slider("Hari ke depan", 3, 30, 7)
        show_ci = st.checkbox("Tampilkan confidence interval", value=True)

    result = forecast_output(prod, periods=periods, backtest=True)
    if not result.values:
        st.warning(result.note)
        return

    avg_forecast = sum(result.values) / len(result.values)
    mape_txt = f"MAPE {_fmt_pct(result.mape, 1)}" if result.mape is not None else "MAPE —"
    _banner(
        "🔮 FORECAST INSIGHT",
        f"Rata-rata prediksi: {_fmt_thousand(avg_forecast)} Kg/hari",
        f"Metode: <strong>{result.method}</strong> · Akurasi: <strong>{mape_txt}</strong> · Periode: <strong>{periods} hari ke depan</strong>",
        accent="#f7d578", label_color="#f7d578")

    df = prod.copy()
    df["Date"] = pd.to_datetime(df["Date"])
    hist = df.groupby("Date", as_index=False)["Output_Kg"].sum().sort_values("Date")
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=hist["Date"], y=hist["Output_Kg"],
        mode="lines+markers", name="Historis",
        line=dict(color=COLORS["primary"], width=2.5, shape="spline"),
        marker=dict(size=4, color=COLORS["primary"],
                    line=dict(color="#0d1026", width=1.5))))

    n_hist = len(hist)
    step = max(1, n_hist // 10)
    for i in range(0, n_hist, step):
        row = hist.iloc[i]
        fig.add_annotation(
            x=row["Date"], y=row["Output_Kg"],
            text=f"<b>{_fmt_thousand(row['Output_Kg'])}</b>",
            showarrow=False, yshift=14,
            font=dict(size=9, color="#c4aaff", family="DM Sans"),
            bgcolor="rgba(26, 29, 61, 0.9)", bordercolor="#a489ff",
            borderwidth=1, borderpad=2)

    fig.add_trace(go.Scatter(
        x=result.dates, y=result.values,
        mode="lines+markers", name=f"Forecast ({result.method})",
        line=dict(color=COLORS["warning"], width=2.5, dash="dash"),
        marker=dict(size=7, color=COLORS["warning"],
                    line=dict(color="#0d1026", width=2))))

    for d, v in zip(result.dates, result.values):
        fig.add_annotation(
            x=d, y=v,
            text=f"<b>{_fmt_thousand(v)}</b>",
            showarrow=False, yshift=16,
            font=dict(size=9, color="#f7d578", family="DM Sans"),
            bgcolor="rgba(48, 43, 48, 0.9)", bordercolor="#f7d578",
            borderwidth=1, borderpad=2)

    if show_ci:
        fig.add_trace(go.Scatter(
            x=result.dates + result.dates[::-1],
            y=result.upper + result.lower[::-1],
            fill="toself", fillcolor="rgba(245,158,11,0.15)",
            line=dict(color="rgba(255,255,255,0)"),
            name="95% CI", showlegend=True))

    fig = apply_theme(fig, height=440)
    fig.update_layout(
        yaxis_title="<b>Output (Kg)</b>", xaxis_title="",
        hovermode="x unified", margin=dict(t=60, b=60, l=60, r=40))
    st.plotly_chart(fig, width='stretch')

    m1, m2, m3, m4 = st.columns(4, gap="medium")
    _glass_card(m1, "Metode", result.method, "#a489ff", note="Algoritma forecast")
    if result.mape is not None:
        good = result.mape <= 15
        _glass_card(m2, "MAPE", _fmt_pct(result.mape, 1),
                    "#77edb4" if good else "#ff9eaa",
                    delta=("✅ Sesuai target" if good else "⚠️ > 15%"),
                    delta_color=("#77edb4" if good else "#ff9eaa"))
    else:
        _glass_card(m2, "MAPE", "—", "#adb6d5", note="Tidak tersedia")
    _glass_card(m3, "Rata-rata Forecast",
                f"{_fmt_thousand(avg_forecast)} Kg", "#ec3f92", note="per hari")
    _glass_card(m4, "Total Forecast",
                f"{_fmt_thousand(sum(result.values))} Kg", "#f7d578",
                note=f"{periods} hari")

    if result.note:
        st.caption(result.note)


def _render_anomaly(ds: Dataset, scope: Scope) -> None:
    st.markdown("### 🔍 Outlier Detection")
    st.caption("Isolation Forest mendeteksi pola scrap di luar kebiasaan.")

    prod = scope_production(ds.production, scope)
    if prod.empty:
        st.info("Data produksi tidak tersedia.")
        return

    c1, c2 = st.columns([1, 3], gap="medium")
    with c1:
        contamination = st.slider("Sensitivitas (%)", 1, 20, 5, 1,
                                   help="Estimasi % data yang dianggap anomali.") / 100

    result = detect_anomalies(prod, contamination=contamination)
    if result.total == 0:
        st.success(f"✅ Tidak ada anomali terdeteksi. (Metode: {result.method})")
        return

    pct = result.total / len(prod) * 100
    _banner(
        "🚨 ANOMALY DETECTED",
        f"{result.total} anomali terdeteksi ({_fmt_pct(pct, 1)} dari data)",
        f"Metode: <strong>{result.method}</strong> · Sensitivitas: <strong>{contamination*100:.0f}%</strong> · Perlu investigasi lebih lanjut",
        accent="#ff9eaa", label_color="#ff9eaa")

    k1, k2, k3 = st.columns(3, gap="medium")
    _glass_card(k1, "Jumlah Anomali", str(result.total), "#ff9eaa",
                note="Baris dengan pola tidak normal")
    _glass_card(k2, "Persentase", _fmt_pct(pct, 1), "#f7d578",
                note="Dari total data produksi")
    _glass_card(k3, "Metode", result.method, "#a489ff", note="Deteksi outlier")

    df = prod.copy()
    if "Date" not in df.columns:
        return

    df["Date"] = pd.to_datetime(df["Date"])
    df["Scrap_Pct"] = (df["Scrap_Kg"] / df["Input_Kg"].replace(0, pd.NA)) * 100
    df["Is_Anomaly"] = df.index.isin(result.anomalies.index)

    mean_scrap = df["Scrap_Pct"].mean()
    std_scrap = df["Scrap_Pct"].std()
    upper_bound = mean_scrap + 2 * std_scrap
    lower_bound = max(0, mean_scrap - 2 * std_scrap)
    df_sorted = df.sort_values("Is_Anomaly")

    fig = go.Figure()
    fig.add_hrect(
        y0=lower_bound, y1=upper_bound,
        fillcolor="rgba(119, 237, 180, 0.08)", line_width=0,
        annotation_text="<b>Zona Normal (μ ± 2σ)</b>",
        annotation_position="top left",
        annotation_font=dict(size=10, color=COLORS["success"]))

    normal = df_sorted[~df_sorted["Is_Anomaly"]]
    fig.add_trace(go.Scatter(
        x=normal["Date"], y=normal["Scrap_Pct"], mode="markers", name="Normal",
        marker=dict(size=8, color=COLORS["primary"],
                    line=dict(color="#0d1026", width=1.5), opacity=0.7),
        hovertemplate="<b>%{x|%d %b}</b><br>Scrap: %{y:.2f}%<extra></extra>"))

    anomalies = df_sorted[df_sorted["Is_Anomaly"]]
    fig.add_trace(go.Scatter(
        x=anomalies["Date"], y=anomalies["Scrap_Pct"],
        mode="markers", name="Anomali",
        marker=dict(size=13, color=COLORS["danger"], symbol="diamond",
                    line=dict(color="#0d1026", width=2)),
        hovertemplate="<b>🚨 ANOMALI</b><br>%{x|%d %b %Y}<br>Scrap: %{y:.2f}%<extra></extra>"))

    for _, row in anomalies.head(8).iterrows():
        fig.add_annotation(
            x=row["Date"], y=row["Scrap_Pct"],
            text=f"<b>{_fmt_pct(row['Scrap_Pct'], 1)}</b>",
            showarrow=True, arrowhead=2, arrowcolor="#ff9eaa",
            ax=0, ay=-28,
            font=dict(size=9, color="#ff9eaa", family="DM Sans"),
            bgcolor="rgba(53, 36, 58, 0.9)", bordercolor="#ff9eaa",
            borderwidth=1, borderpad=3)

    fig.add_hline(
        y=mean_scrap, line_dash="dash", line_color=COLORS["primary_dark"],
        line_width=1.5,
        annotation_text=f"<b>AVG {_fmt_pct(mean_scrap, 2)}</b>",
        annotation_position="right",
        annotation_font=dict(size=10, color=COLORS["primary_dark"]))

    fig = apply_theme(fig, height=420)
    fig.update_layout(
        yaxis_title="<b>Scrap (%)</b>", xaxis_title="", hovermode="closest",
        margin=dict(t=40, b=60, l=60, r=100))
    st.plotly_chart(fig, width='stretch')

    with st.expander(f"📋 Lihat detail {result.total} anomali"):
        cols = [c for c in ("Date", "Plant", "Line", "Machine",
                            "Output_Kg", "Scrap_Kg", "Scrap_Pct")
                if c in result.anomalies.columns]
        render_table(result.anomalies[cols].reset_index(drop=True),
                     max_height="400px")


def _render_stockout(ds: Dataset) -> None:
    st.markdown("### 📦 Prediksi Stock-Out")
    st.caption("Kapan material akan habis berdasarkan pemakaian rata-rata.")

    risks = predict_stockout(ds.inventory)
    if not risks:
        st.info("Data inventory tidak tersedia.")
        return

    critical = sum(1 for r in risks if r.status == "critical")
    warning = sum(1 for r in risks if r.status == "warning")
    ok = sum(1 for r in risks if r.status == "ok")

    if critical > 0:
        _banner(
            "🔴 STOCK-OUT ALERT",
            f"{critical} material dalam status KRITIS",
            f"Segera reorder! <strong>{warning} material</strong> dalam status peringatan, <strong>{ok} aman</strong>.",
            accent="#ff9eaa", label_color="#ff9eaa")
    else:
        _banner(
            "📦 STOCK STATUS", "Semua material dalam kondisi aman",
            f"<strong>{warning} material</strong> dalam peringatan, <strong>{ok} aman</strong>.",
            accent="#77edb4", label_color="#77edb4")

    c1, c2, c3 = st.columns(3, gap="medium")
    _glass_card(c1, "🔴 Kritis (<14 hari)", str(critical), "#ff9eaa", note="Segera reorder")
    _glass_card(c2, "🟡 Peringatan (<30 hari)", str(warning), "#f7d578", note="Pantau ketat")
    _glass_card(c3, "🟢 Aman", str(ok), "#77edb4", note="Stok mencukupi")

    st.markdown("")
    st.markdown("#### 📊 Sisa Hari Sampai Stock-Out")

    df = pd.DataFrame([{
        "Material": r.material,
        "Days": r.days_until_empty if r.days_until_empty else 999,
        "Status": r.status,
        "Stock_Kg": r.stock_kg,
        "Daily_Usage": r.daily_usage,
    } for r in risks if r.days_until_empty is not None])

    if df.empty:
        st.info("Tidak ada material dengan konsumsi terdeteksi.")
        return

    df = df.sort_values("Days", ascending=True).reset_index(drop=True)
    color_map = {"critical": COLORS["danger"], "warning": COLORS["warning"],
                 "ok": COLORS["success"]}
    colors = [color_map.get(s, COLORS["text_muted"]) for s in df["Status"]]

    text_labels = [
        "<b>∞</b>" if row["Days"] >= 999 else f"<b>{int(row['Days'])} hari</b>"
        for _, row in df.iterrows()]

    fig = go.Figure(go.Bar(
        x=df["Material"], y=df["Days"].clip(upper=120), orientation="v",
        marker=dict(color=colors, line=dict(width=0)),
        text=text_labels, textposition="outside",
        textfont=dict(size=11, color=COLORS["text"], family="DM Sans"),
        cliponaxis=False,
        hovertemplate=("<b>%{x}</b><br>"
                       "Stok: %{customdata[0]:,.0f} Kg<br>"
                       "Usage: %{customdata[1]:,.0f} Kg/hari<br>"
                       "Sisa: %{y:.0f} hari<extra></extra>"),
        customdata=df[["Stock_Kg", "Daily_Usage"]].values))

    fig.add_hline(y=14, line_dash="dash", line_color=COLORS["danger"], line_width=2,
                  annotation_text="<b>KRITIS (14 hari)</b>",
                  annotation_position="right",
                  annotation_font=dict(size=10, color=COLORS["danger"]))
    fig.add_hline(y=30, line_dash="dash", line_color=COLORS["warning"], line_width=1.5,
                  annotation_text="<b>Warning (30 hari)</b>",
                  annotation_position="right",
                  annotation_font=dict(size=10, color=COLORS["warning"]))

    fig = apply_theme(fig, height=400)
    fig.update_layout(
        yaxis_title="<b>Sisa Hari</b>", xaxis_title="<b>Material</b>",
        xaxis=dict(tickfont=dict(size=10)),
        margin=dict(t=40, b=80, l=60, r=120))
    st.plotly_chart(fig, width='stretch')

    st.markdown("#### 📋 Detail Stock")
    rows = []
    for r in risks:
        icon = {"critical": "🔴", "warning": "🟡", "ok": "🟢"}[r.status]
        rows.append({
            "Material": r.material,
            "Stok (Kg)": _fmt_thousand(r.stock_kg),
            "Usage/Bln (Kg)": _fmt_thousand(r.monthly_usage),
            "Hari Tersisa": (_fmt_thousand(r.days_until_empty, 0)
                             if r.days_until_empty is not None else "—"),
            "Status": f"{icon} {r.status.capitalize()}"})
    render_table(pd.DataFrame(rows), max_height="350px")


def _render_slow_moving(ds: Dataset) -> None:
    st.markdown("### 🐢 Prediksi Slow-Moving")
    st.caption("Material yang berisiko jadi slow-moving / dead stock.")

    results = predict_slow_moving(ds.inventory)
    if not results:
        st.info("Data inventory tidak tersedia.")
        return

    dead = sum(1 for r in results if r.risk_level == "dead_stock")
    slow = sum(1 for r in results if r.risk_level == "slow_moving")
    watch = sum(1 for r in results if r.risk_level == "watch")

    if dead > 0 or slow > 0:
        _banner(
            "🐢 SLOW-MOVING ALERT",
            f"{dead + slow} material berisiko slow-moving/dead stock",
            f"<strong>{dead} dead stock</strong> · <strong>{slow} slow moving</strong> · <strong>{watch} watch</strong>",
            accent="#f7d578", label_color="#f7d578")
    else:
        _banner(
            "🐢 INVENTORY HEALTH", "Semua material dalam kondisi sehat",
            f"<strong>{watch} material</strong> dalam status watch.",
            accent="#77edb4", label_color="#77edb4")

    c1, c2, c3, c4 = st.columns(4, gap="medium")
    _glass_card(c1, "⚫ Dead Stock", str(dead), "#adb6d5", note="Tidak bergerak")
    _glass_card(c2, "🔴 Slow Moving", str(slow), "#ff9eaa", note="Pergerakan lambat")
    _glass_card(c3, "🟡 Watch", str(watch), "#f7d578", note="Pantau")
    _glass_card(c4, "Total Material", str(len(results)), "#a489ff", note="Dianalisis")

    st.markdown("")
    rows = []
    for r in results:
        icon = {"dead_stock": "⚫", "slow_moving": "🔴",
                "watch": "🟡", "ok": "🟢"}.get(r.risk_level, "⚪")
        rows.append({
            "Material": r.material,
            "Days Inventory": (_fmt_thousand(r.current_days, 0)
                               if r.current_days is not None else "—"),
            "Trend": r.trend,
            "Prediksi 30 hari": (_fmt_thousand(r.predicted_days_30d, 0)
                                  if r.predicted_days_30d is not None else "—"),
            "Status": f"{icon} {r.risk_level.replace('_', ' ').title()}"})
    render_table(pd.DataFrame(rows), max_height="350px")


def render(ds: Dataset, scope: Scope) -> None:
    _inject_css()
    st.title("🔮 Predictive Analytics")
    st.caption("Forecast output, deteksi anomali scrap, prediksi stock-out (BRD 8).")

    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Forecast Output", "🔍 Anomali Scrap",
        "📦 Stock-Out", "🐢 Slow-Moving"])
    with tab1: _render_forecast(ds, scope)
    with tab2: _render_anomaly(ds, scope)
    with tab3: _render_stockout(ds)
    with tab4: _render_slow_moving(ds)