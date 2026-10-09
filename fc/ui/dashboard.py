"""Halaman Dashboard - Glassmorphism UI + section dividers (bulanan vs harian)."""
import streamlit as st
import plotly.express as px

from ..config import TARGETS as DEFAULT_TARGETS
from ..intel.alert_impact import compute_alerts
from ..intel.period_compare import available_periods, compare_periods
from ..kpi import KPI, Scope, scope_production, summarize
from ..pipeline import Dataset


# ==================== CSS GLASSMORPHISM ====================
GLASS_CSS = """
<style>
.glass-metric {
    position: relative;
    background: linear-gradient(135deg, #FFFFFF 0%, #F5F3FF 100%);
    border: 1px solid rgba(196, 181, 253, 0.5);
    border-radius: 16px;
    padding: 18px 20px;
    box-shadow: 0 6px 20px rgba(139, 92, 246, 0.08);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    overflow: hidden;
    min-height: 105px;
    margin-bottom: 8px;
}
.glass-metric::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, var(--accent, #8B5CF6) 0%, #EC4899 100%);
}
.glass-metric:hover {
    transform: translateY(-3px);
    box-shadow: 0 16px 32px rgba(139, 92, 246, 0.18);
    border-color: rgba(139, 92, 246, 0.6);
}
.glass-metric-label {
    color: #6D28D9;
    font-weight: 700;
    font-size: 0.68rem;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    margin-bottom: 6px;
}
.glass-metric-value {
    color: #0F172A;
    font-weight: 800;
    font-size: 1.55rem;
    letter-spacing: -0.5px;
    line-height: 1.1;
    margin-bottom: 2px;
}
.glass-metric-note {
    color: #94A3B8;
    font-size: 0.68rem;
    font-style: italic;
    line-height: 1.3;
}
</style>
"""


def _inject_css():
    st.markdown(GLASS_CSS, unsafe_allow_html=True)


# ==================== CACHED HELPERS ====================
@st.cache_data(show_spinner=False)
def _cached_summarize(ds: Dataset, scope: Scope):
    return summarize(ds, scope)


def _active_targets():
    return st.session_state.get("_targets") or DEFAULT_TARGETS


def _glass_metric_html(label: str, kpi: KPI, fmt: str, accent: str = "#8B5CF6") -> str:
    if kpi.available:
        display = fmt.format(kpi.value)
        note_html = f'<div class="glass-metric-note">{kpi.note}</div>' if kpi.note else ''
    else:
        display = "—"
        note_html = f'<div class="glass-metric-note">Tidak tersedia: {kpi.note}</div>'

    return (
        f'<div class="glass-metric" style="--accent: {accent};">'
        f'  <div class="glass-metric-label">{label}</div>'
        f'  <div class="glass-metric-value">{display}</div>'
        f'  {note_html}'
        f'</div>'
    )


def _glass_metric(col, label: str, kpi: KPI, fmt: str, accent: str = "#8B5CF6") -> None:
    col.markdown(_glass_metric_html(label, kpi, fmt, accent), unsafe_allow_html=True)


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
        return score, "Excellent", "#10B981"
    elif score >= 80:
        return score, "Good", "#8B5CF6"
    elif score >= 70:
        return score, "Fair", "#F59E0B"
    return score, "Needs Attention", "#EF4444"


def _render_alert(alert) -> None:
    icon = {"high": "🔴", "medium": "🟡", "info": "🔵"}.get(alert.severity, "⚪")
    text = (
        f"{icon} **{alert.title}**  \n"
        f"{alert.message}  \n"
        f"💰 **Dampak: Rp {alert.monthly_rp:,.0f}/bulan "
        f"(Rp {alert.annual_rp:,.0f}/tahun)**  \n"
        f"🔧 {alert.fix_hint}"
    )
    if alert.severity == "high":
        st.error(text)
    elif alert.severity == "medium":
        st.warning(text)
    else:
        st.info(text)


def _render_period_compare(ds: Dataset) -> None:
    periods = available_periods(ds)
    if len(periods) < 2:
        st.info("Butuh minimal 2 periode untuk perbandingan.")
        return

    c1, c2 = st.columns(2)
    if len(periods) >= 3:
        prev = c1.selectbox("Periode Sebelumnya", periods, index=len(periods) - 3, key="dc_prev_v2")
        curr = c2.selectbox("Periode Sekarang", periods, index=len(periods) - 2, key="dc_curr_v2")
    else:
        prev = c1.selectbox("Periode Sebelumnya", periods, index=0, key="dc_prev_v2")
        curr = c2.selectbox("Periode Sekarang", periods, index=len(periods) - 1, key="dc_curr_v2")

    if prev == curr:
        st.warning("Pilih periode yang berbeda.")
        return

    comps = compare_periods(ds, prev, curr)
    rows = []
    for c in comps:
        if c.is_improving is True:
            status = "✅ Membaik"
        elif c.is_improving is False:
            status = "🔴 Memburuk"
        else:
            status = "➖ Stabil"
        rows.append({
            "KPI": c.label, prev: c.fmt_value(c.prev_value),
            curr: c.fmt_value(c.curr_value),
            "Δ": c.fmt_delta(), "Δ %": c.fmt_pct(), "Status": status,
        })

    import pandas as pd
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    worsening = [c for c in comps if c.is_improving is False]
    if worsening:
        labels = ", ".join(c.label for c in worsening)
        st.warning(f"⚠️ **{len(worsening)} KPI memburuk** dibanding {prev}: {labels}")


# ==================== SECTION 1: KPI TOTAL ====================
def _render_section_total(s, targets, ds):
    from .components import section_divider

    section_divider(
        title="KPI Total",
        subtitle="Ringkasan performa periode terfilter. Angka adalah TOTAL, bukan per bulan atau per hari.",
        icon="📊",
        badge="TOTAL",
        color="#8B5CF6",
        bg1="#F5F3FF",
        bg2="#FFFFFF",
    )

    # KPI Cards (6 kartu)
    r1 = st.columns(3)
    _glass_metric(r1[0], "Production Volume", s.output_kg, "{:,.0f} Kg", "#8B5CF6")
    _glass_metric(r1[1], "Yield", s.yield_pct, "{:.2f}%", "#10B981")
    _glass_metric(r1[2], "OEE", s.oee.oee, "{:.2f}%", "#3B82F6")

    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

    r2 = st.columns(3)
    _glass_metric(r2[0], "Scrap", s.scrap_pct, "{:.2f}%", "#F59E0B")
    _glass_metric(r2[1], "Cost/Kg", s.cost_per_kg, "Rp {:,.0f}", "#EC4899")
    _glass_metric(r2[2], "COGM", s.cogm, "Rp {:,.0f}", "#6366F1")

    # OEE Breakdown
    with st.expander("🔍 Rincian OEE (Availability × Performance × Quality)"):
        c = st.columns(3)
        _glass_metric(c[0], "Availability", s.oee.availability, "{:.2f}%", "#8B5CF6")
        _glass_metric(c[1], "Performance", s.oee.performance, "{:.2f}%", "#A855F7")
        _glass_metric(c[2], "Quality", s.oee.quality, "{:.2f}%", "#EC4899")

    st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)

    # KPI vs Target (Gauge)
    from .charts import gauge
    st.markdown("#### 🎯 KPI vs Target")
    st.caption("Visual pencapaian target. Garis oranye = target.")

    g1, g2, g3 = st.columns(3)
    with g1:
        if s.yield_pct.available:
            st.plotly_chart(gauge("Yield", s.yield_pct.value, targets.yield_min,
                                  min_val=85, max_val=100, higher_is_better=True),
                            use_container_width=True)
    with g2:
        if s.scrap_pct.available:
            st.plotly_chart(gauge("Scrap", s.scrap_pct.value, targets.scrap_max,
                                  min_val=0, max_val=10, higher_is_better=False),
                            use_container_width=True)
    with g3:
        if s.oee.oee.available:
            st.plotly_chart(gauge("OEE", s.oee.oee.value, targets.oee_min,
                                  min_val=60, max_val=100, higher_is_better=True),
                            use_container_width=True)

    st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)

    # Cost Alert
    alerts = compute_alerts(s, targets)
    st.markdown("#### 🚨 Cost Alert Aktif")
    st.caption("Diurutkan berdasarkan Financial Impact.")

    if alerts:
        total_annual = sum(abs(a.annual_rp) for a in alerts)
        if total_annual > 0:
            st.markdown(
                f"**Total potensi dampak: Rp {total_annual:,.0f}/tahun** "
                f"— ini yang bisa dihemat jika semua masalah diperbaiki."
            )
        for a in alerts:
            _render_alert(a)
    else:
        st.success("✅ Tidak ada peringatan aktif. Semua KPI dalam batas target.")

    st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)

    # Bottom Charts (Cost Control Score + COGM)
    st.markdown("#### 📊 Analisis Biaya")
    tab_score, tab_cogm = st.tabs(["🏆 Cost Control Score", "🥧 Struktur COGM"])

    with tab_score:
        if s.score.score is None:
            st.metric("Cost Control Score", "—")
            st.caption(s.score.note)
        else:
            st.metric("Cost Control Score", f"{s.score.score}/100")
            (st.success if s.score.score >= 90 else st.info if s.score.score >= 80
             else st.warning if s.score.score >= 70 else st.error)(s.score.category)
            for r in s.score.reasons:
                st.caption("• " + r)
            if s.score.note:
                st.caption(s.score.note)

    with tab_cogm:
        from .charts import pie_chart
        if s.breakdown:
            total = sum(s.breakdown.values())
            center = (f"Rp {total/1_000_000_000:.2f} M" if total >= 1e9
                      else f"Rp {total/1_000_000:.1f} jt")
            fig = px.pie(names=list(s.breakdown),
                         values=list(s.breakdown.values()), hole=0.55)
            fig = pie_chart(fig, height=380, center_text=center)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info(f"Data tidak tersedia: {s.cogm.note}")


# ==================== SECTION 2: BULANAN ====================
def _render_section_monthly(ds):
    from .components import section_divider

    section_divider(
        title="Analisis Bulanan",
        subtitle="Perbandingan bulan-ke-bulan (MoM). Cocok untuk laporan & tren jangka menengah.",
        icon="📆",
        badge="BULANAN",
        color="#8B5CF6",
        bg1="#F5F3FF",
        bg2="#FFFFFF",
    )

    st.markdown("#### 📅 Month-over-Month (MoM)")
    st.caption("Bandingkan KPI antar 2 bulan untuk melihat tren.")
    _render_period_compare(ds)


# ==================== SECTION 3: HARIAN ====================
def _render_section_daily(ds, scope):
    from .components import section_divider

    section_divider(
        title="Trend Harian",
        subtitle="Detail per hari. Cocok untuk investigasi operasional & deteksi anomali.",
        icon="📅",
        badge="HARIAN",
        color="#3B82F6",
        bg1="#EFF6FF",
        bg2="#FFFFFF",
    )

    from .charts import line_chart, COLORS
    prod = scope_production(ds.production, scope)
    if not len(prod):
        st.info("Tidak ada data produksi pada filter terpilih.")
        return

    daily = prod.groupby("Date", as_index=False)["Output_Kg"].sum()
    daily = daily.sort_values("Date").reset_index(drop=True)

    n = len(daily)
    step = 1 if n <= 10 else 2 if n <= 20 else 4 if n <= 40 else 7

    fig = px.line(daily, x="Date", y="Output_Kg", markers=True)

    label_df = daily.iloc[::step].copy()
    for _, row in label_df.iterrows():
        fig.add_annotation(
            x=row["Date"], y=row["Output_Kg"],
            text=f"<b>{row['Output_Kg']:,.0f}</b>",
            showarrow=False, yshift=14,
            font=dict(size=9, color=COLORS["primary_dark"], family="Inter"),
            bgcolor="rgba(245, 243, 255, 0.9)",
            bordercolor=COLORS["primary_light"],
            borderwidth=1, borderpad=2,
        )

    avg_val = daily["Output_Kg"].mean()
    fig.add_hline(
        y=avg_val, line_dash="dash",
        line_color=COLORS["accent"], line_width=2,
        annotation_text=f"<b>AVG {avg_val:,.0f}</b>",
        annotation_position="right",
        annotation_font=dict(size=10, color=COLORS["accent_dark"], family="Inter"),
    )

    fig.update_traces(
        line=dict(color=COLORS["primary"]),
        marker=dict(size=5, color=COLORS["primary"],
                    line=dict(color="#FFFFFF", width=2)),
    )

    fig = line_chart(fig, height=360, y_title="Output (Kg)")
    fig.update_layout(margin=dict(t=50, b=60, l=60, r=80))
    st.plotly_chart(fig, use_container_width=True)


# ==================== MAIN RENDER ====================
def render(ds: Dataset, scope: Scope) -> None:
    _inject_css()
    s = _cached_summarize(ds, scope)
    targets = _active_targets()

    # Header + Mini Health Score
    from .components import page_header, mini_health_score, format_period_label
    page_header(
        title="Decidiq",
        subtitle=(
            f"Sumber: {ds.report.source_label} · Dibaca: {ds.report.loaded_at} · "
            f"{s.production_rows:,} baris produksi · "
            f"Target: Yield ≥ {targets.yield_min:g}% · Scrap ≤ {targets.scrap_max:g}% · "
            f"OEE ≥ {targets.oee_min:g}%"
        ),
        granularity="Multi",
        period_label=format_period_label(scope),
        icon="🏭",
    )

    score, status, color = _health_score(s, targets)
    mini_health_score(score, status, color)

    # ===== SECTION 1: KPI TOTAL =====
    _render_section_total(s, targets, ds)

    # ===== SECTION 2: ANALISIS BULANAN =====
    _render_section_monthly(ds)

    # ===== SECTION 3: TREND HARIAN =====
    _render_section_daily(ds, scope)