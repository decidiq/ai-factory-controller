"""Predictive Analytics — forecast, anomali, stock-out (BRD 8) — Premium UI."""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from ..intel.predictive import (detect_anomalies, forecast_output,
                                 predict_slow_moving, predict_stockout)
from ..kpi import Scope, scope_production
from ..pipeline import Dataset
from .charts import COLORS, apply_theme


# ==================== CSS GLASSMORPHISM ====================
GLASS_CSS = """
<style>
.pr-glass {
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
.pr-glass::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, var(--accent, #8B5CF6) 0%, #EC4899 100%);
}
.pr-glass:hover {
    transform: translateY(-3px);
    box-shadow: 0 16px 32px rgba(139, 92, 246, 0.18);
    border-color: rgba(139, 92, 246, 0.6);
}
.pr-glass-label {
    color: #6D28D9;
    font-weight: 700;
    font-size: 0.66rem;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    margin-bottom: 6px;
}
.pr-glass-value {
    color: #0F172A;
    font-weight: 800;
    font-size: 1.4rem;
    letter-spacing: -0.5px;
    line-height: 1.1;
    margin-bottom: 2px;
}
.pr-glass-note {
    color: #94A3B8;
    font-size: 0.68rem;
    font-style: italic;
    line-height: 1.3;
}
.pr-glass-delta {
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.3px;
}

/* Insight Banner */
.pr-banner {
    background: linear-gradient(135deg, #0F172A 0%, #1E1B4B 100%);
    border-radius: 16px;
    padding: 20px 26px;
    color: white;
    box-shadow: 0 12px 32px rgba(30, 27, 75, 0.25);
    border: 1px solid rgba(139, 92, 246, 0.3);
    margin-bottom: 20px;
    position: relative;
    overflow: hidden;
}
.pr-banner::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 4px;
    background: linear-gradient(90deg, var(--b-accent, #8B5CF6) 0%, #EC4899 100%);
}
.pr-banner-label {
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 1.5px;
    color: var(--b-label, #FBBF24);
    text-transform: uppercase;
    margin-bottom: 8px;
}
.pr-banner-title {
    font-size: 1.35rem;
    font-weight: 900;
    color: #FFFFFF;
    letter-spacing: -0.5px;
    line-height: 1.15;
    margin-bottom: 6px;
}
.pr-banner-desc {
    font-size: 0.88rem;
    color: #C4B5FD;
    line-height: 1.5;
}
.pr-banner-desc strong { color: #FBBF24; }
</style>
"""


def _inject_css():
    st.markdown(GLASS_CSS, unsafe_allow_html=True)


# ==================== HELPERS ====================
def _glass_card(col, label: str, value: str, accent: str = "#8B5CF6",
                note: str = None, delta: str = None,
                delta_color: str = None) -> None:
    note_html = f'<div class="pr-glass-note">{note}</div>' if note else ""
    delta_html = ""
    if delta:
        c = delta_color or "#10B981"
        delta_html = f'<div class="pr-glass-delta" style="color:{c};">{delta}</div>'
    html = (
        f'<div class="pr-glass" style="--accent: {accent};">'
        f'<div class="pr-glass-label">{label}</div>'
        f'<div class="pr-glass-value">{value}</div>'
        f'{delta_html}'
        f'{note_html}'
        f'</div>'
    )
    col.markdown(html, unsafe_allow_html=True)


def _banner(label: str, title: str, desc: str = "",
            accent: str = "#8B5CF6", label_color: str = "#FBBF24") -> None:
    desc_html = f'<div class="pr-banner-desc">{desc}</div>' if desc else ""
    html = (
        f'<div class="pr-banner" style="--b-accent: {accent}; --b-label: {label_color};">'
        f'<div class="pr-banner-label">{label}</div>'
        f'<div class="pr-banner-title">{title}</div>'
        f'{desc_html}'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


# ==================== CACHED WRAPPERS ====================
@st.cache_data(show_spinner=False)
def _cached_forecast(_prod_hash: str, periods: int):
    """Cache forecast berdasarkan hash data produksi & periods."""
    return None  # placeholder


@st.cache_data(show_spinner=False)
def _cached_anomalies(_prod_hash: str, contamination: float):
    return None  # placeholder


# ==================== FORECAST ====================
def _render_forecast(ds: Dataset, scope: Scope) -> None:
    st.markdown("### 📈 Forecast Output Produksi")
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

    # Banner insight
    avg_forecast = sum(result.values) / len(result.values)
    mape_txt = f"MAPE {result.mape:.1f}%" if result.mape is not None else "MAPE —"
    _banner(
        "🔮 FORECAST INSIGHT",
        f"Rata-rata prediksi: {avg_forecast:,.0f} Kg/hari",
        f"Metode: <strong>{result.method}</strong> · Akurasi: <strong>{mape_txt}</strong> · Periode: <strong>{periods} hari ke depan</strong>",
        accent="#F59E0B",
        label_color="#FBBF24",
    )

    # Persiapkan data historis
    df = prod.copy()
    df["Date"] = pd.to_datetime(df["Date"])
    hist = df.groupby("Date", as_index=False)["Output_Kg"].sum().sort_values("Date")

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=hist["Date"], y=hist["Output_Kg"],
        mode="lines+markers", name="Historis",
        line=dict(color=COLORS["primary"], width=2.5, shape="spline"),
        marker=dict(size=4, color=COLORS["primary"],
                    line=dict(color="#FFFFFF", width=1.5)),
    ))

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

    fig.add_trace(go.Scatter(
        x=result.dates, y=result.values,
        mode="lines+markers", name=f"Forecast ({result.method})",
        line=dict(color=COLORS["warning"], width=2.5, dash="dash"),
        marker=dict(size=7, color=COLORS["warning"],
                    line=dict(color="#FFFFFF", width=2)),
    ))

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

    # Kartu ringkasan (glass)
    m1, m2, m3, m4 = st.columns(4)
    _glass_card(m1, "Metode", result.method, "#8B5CF6",
                note="Algoritma forecast")
    if result.mape is not None:
        good = result.mape <= 15
        _glass_card(m2, "MAPE", f"{result.mape:.1f}%",
                    "#10B981" if good else "#EF4444",
                    delta=("✅ Sesuai target" if good else "⚠️ > 15%"),
                    delta_color=("#10B981" if good else "#EF4444"))
    else:
        _glass_card(m2, "MAPE", "—", "#94A3B8", note="Tidak tersedia")
    _glass_card(m3, "Rata-rata Forecast",
                f"{avg_forecast:,.0f} Kg", "#EC4899",
                note="per hari")
    _glass_card(m4, "Total Forecast",
                f"{sum(result.values):,.0f} Kg", "#F59E0B",
                note=f"{periods} hari")

    if result.note:
        st.caption(result.note)


# ==================== ANOMALY ====================
def _render_anomaly(ds: Dataset, scope: Scope) -> None:
    st.markdown("### 🔍 Outlier Detection")
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

    # Banner insight
    pct = result.total / len(prod) * 100
    _banner(
        "🚨 ANOMALY DETECTED",
        f"{result.total} anomali terdeteksi ({pct:.1f}% dari data)",
        f"Metode: <strong>{result.method}</strong> · Sensitivitas: <strong>{contamination*100:.0f}%</strong> · Perlu investigasi lebih lanjut",
        accent="#EF4444",
        label_color="#F87171",
    )

    # KPI Cards
    k1, k2, k3 = st.columns(3)
    _glass_card(k1, "Jumlah Anomali", str(result.total), "#EF4444",
                note="Baris dengan pola tidak normal")
    _glass_card(k2, "Persentase", f"{pct:.1f}%", "#F59E0B",
                note="Dari total data produksi")
    _glass_card(k3, "Metode", result.method, "#8B5CF6",
                note="Deteksi outlier")

    # Scatter dengan zona aman
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
        fillcolor="rgba(16, 185, 129, 0.08)",
        line_width=0,
        annotation_text="<b>Zona Normal (μ ± 2σ)</b>",
        annotation_position="top left",
        annotation_font=dict(size=10, color=COLORS["success"]),
    )

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
    st.markdown("### 📦 Prediksi Stock-Out")
    st.caption("Kapan material akan habis berdasarkan pemakaian rata-rata.")

    risks = predict_stockout(ds.inventory)
    if not risks:
        st.info("Data inventory tidak tersedia.")
        return

    critical = sum(1 for r in risks if r.status == "critical")
    warning = sum(1 for r in risks if r.status == "warning")
    ok = sum(1 for r in risks if r.status == "ok")

    # Banner insight
    if critical > 0:
        _banner(
            "🔴 STOCK-OUT ALERT",
            f"{critical} material dalam status KRITIS",
            f"Segera reorder! <strong>{warning} material</strong> dalam status peringatan, <strong>{ok} aman</strong>.",
            accent="#EF4444", label_color="#F87171",
        )
    else:
        _banner(
            "📦 STOCK STATUS",
            "Semua material dalam kondisi aman",
            f"<strong>{warning} material</strong> dalam peringatan, <strong>{ok} aman</strong>.",
            accent="#10B981", label_color="#34D399",
        )

    # Kartu ringkasan
    c1, c2, c3 = st.columns(3)
    _glass_card(c1, "🔴 Kritis (<14 hari)", str(critical), "#EF4444",
                note="Segera reorder")
    _glass_card(c2, "🟡 Peringatan (<30 hari)", str(warning), "#F59E0B",
                note="Pantau ketat")
    _glass_card(c3, "🟢 Aman", str(ok), "#10B981",
                note="Stok mencukupi")

    st.markdown("")

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

    color_map = {
        "critical": COLORS["danger"],
        "warning": COLORS["warning"],
        "ok": COLORS["success"],
    }
    colors = [color_map.get(s, COLORS["text_muted"]) for s in df["Status"]]

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
    st.markdown("### 🐢 Prediksi Slow-Moving")
    st.caption("Material yang berisiko jadi slow-moving / dead stock.")

    results = predict_slow_moving(ds.inventory)
    if not results:
        st.info("Data inventory tidak tersedia.")
        return

    # Hitung agregat
    dead = sum(1 for r in results if r.risk_level == "dead_stock")
    slow = sum(1 for r in results if r.risk_level == "slow_moving")
    watch = sum(1 for r in results if r.risk_level == "watch")

    # Banner insight
    if dead > 0 or slow > 0:
        _banner(
            "🐢 SLOW-MOVING ALERT",
            f"{dead + slow} material berisiko slow-moving/dead stock",
            f"<strong>{dead} dead stock</strong> · <strong>{slow} slow moving</strong> · <strong>{watch} watch</strong>",
            accent="#F59E0B", label_color="#FBBF24",
        )
    else:
        _banner(
            "🐢 INVENTORY HEALTH",
            "Semua material dalam kondisi sehat",
            f"<strong>{watch} material</strong> dalam status watch.",
            accent="#10B981", label_color="#34D399",
        )

    # KPI glass cards
    c1, c2, c3, c4 = st.columns(4)
    _glass_card(c1, "⚫ Dead Stock", str(dead), "#0F172A",
                note="Tidak bergerak")
    _glass_card(c2, "🔴 Slow Moving", str(slow), "#EF4444",
                note="Pergerakan lambat")
    _glass_card(c3, "🟡 Watch", str(watch), "#F59E0B",
                note="Pantau")
    _glass_card(c4, "Total Material", str(len(results)), "#8B5CF6",
                note="Dianalisis")

    st.markdown("")

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
    _inject_css()

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