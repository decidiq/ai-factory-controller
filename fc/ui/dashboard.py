"""Halaman Dashboard — Dark Premium Theme + layout presisi."""
import math

import streamlit as st
import plotly.express as px

from ..config import TARGETS as DEFAULT_TARGETS
from ..intel.alert_impact import compute_alerts
from ..intel.period_compare import available_periods, compare_periods
from ..kpi import KPI, Scope, scope_production, summarize
from ..pipeline import Dataset


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


def _fmt_rp(v) -> str:
    try:
        if v is None: return "—"
        f = float(v)
        if math.isnan(f) or math.isinf(f): return "—"
        return "Rp " + f"{f:,.0f}".replace(",", ".")
    except (ValueError, TypeError):
        return str(v) if v is not None else "—"


def _df_height(n_rows: int, row_px: int = 35, header_px: int = 45, max_px: int = 400) -> int:
    """Hitung tinggi dataframe otomatis dari jumlah baris (max 400px)."""
    return min(header_px + row_px * n_rows, max_px)


# ==================== CSS ====================
DASH_CSS = """
<style>
.dash-kpi-row [data-testid="column"] {
    display: flex !important; flex-direction: column !important;
}
.dash-kpi-row [data-testid="column"] > div:first-child { flex: 1 !important; }
.dash-score-wrap { margin: 8px 0 24px 0; }
.dash-highlights [data-testid="column"] {
    display: flex !important; flex-direction: column !important;
}
.dash-highlights [data-testid="column"] > div:first-child { flex: 1 !important; }
.dash-chart-grid [data-testid="stPlotlyChart"] { min-height: 300px; }
.dash-gap-sm { height: 12px; }
.dash-gap-md { height: 20px; }
.dash-gap-lg { height: 28px; }
</style>
"""


def _inject_css():
    st.markdown(DASH_CSS, unsafe_allow_html=True)


# ==================== CACHED ====================
@st.cache_data(show_spinner=False)
def _cached_summarize(ds: Dataset, scope: Scope):
    return summarize(ds, scope)


def _active_targets():
    return st.session_state.get("_targets") or DEFAULT_TARGETS


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
    if score >= 90: return score, "Excellent", "#10B981"
    if score >= 80: return score, "Good", "#8B5CF6"
    if score >= 70: return score, "Fair", "#F59E0B"
    return score, "Needs Attention", "#EF4444"


# ==================== HEADER ====================
def _render_header(ds: Dataset, s) -> None:
    source = getattr(ds.report, "source_label", "—")
    loaded = getattr(ds.report, "loaded_at", "—")
    rows = getattr(s, "production_rows", 0)
    html = (
        f'<div style="margin-bottom:22px;">'
        f'<div style="display:flex;justify-content:space-between;align-items:center;'
        f'gap:12px;margin-bottom:14px;flex-wrap:wrap;">'
        f'<span style="color:#adb6d5;font-size:0.75rem;">Workspace / '
        f'<strong style="color:#f5f6ff;font-weight:700;">Dashboard</strong></span>'
        f'<span style="display:inline-flex;align-items:center;border:1px solid #765da7;'
        f'background:#302650;color:#e3cfff;border-radius:30px;padding:6px 11px;'
        f'font-weight:700;font-size:0.66rem;letter-spacing:0.06em;">'
        f'DEMO DATA / SIMULATED</span></div>'
        f'<p style="font-size:0.62rem;color:#a59bde;font-weight:800;'
        f'letter-spacing:0.12em;text-transform:uppercase;margin:0 0 8px 0;">'
        f'DECISIONIQ / EXECUTIVE OVERVIEW</p>'
        f'<h1 style="font-size:2rem;font-weight:800;letter-spacing:-0.045em;'
        f'color:#f5f6ff;margin:0 0 8px 0;line-height:1.15;">🏭 Dashboard</h1>'
        f'<p style="color:#adb6d5;font-size:0.85rem;margin:0;line-height:1.5;">'
        f'Sumber: {source} · Dibaca: {loaded} · '
        f'<strong style="color:#dce0f4;">{_fmt_thousand(rows)} baris produksi</strong>'
        f'</p></div>'
    )
    st.markdown(html, unsafe_allow_html=True)


# ==================== SCORE PANEL ====================
def _render_score_panel(s, targets) -> None:
    from .components import score_panel
    score, status, color = _health_score(s, targets)
    parts = []
    if s.output_kg.available:
        parts.append(f"Output {_fmt_thousand(s.output_kg.value)} Kg")
    if s.yield_pct.available:
        parts.append(f"Yield {_fmt_pct(s.yield_pct.value)}")
    if s.oee.oee.available:
        parts.append(f"OEE {_fmt_pct(s.oee.oee.value)}")
    if s.scrap_pct.available:
        parts.append(f"Scrap {_fmt_pct(s.scrap_pct.value)}")
    summary = " · ".join(parts) if parts else "Ringkasan performa periode terfilter."
    delta = f"Status: {status} · Periode terfilter"
    st.markdown('<div class="dash-score-wrap"></div>', unsafe_allow_html=True)
    score_panel(score, status, summary, delta_text=delta)


# ==================== KPI GRID ====================
def _render_kpi_grid(s, targets) -> None:
    from .components import section_header, kpi_card
    section_header("KPI Utama",
                   "Delapan indikator utama performa pabrik pada periode terfilter",
                   "8 METRICS")
    st.markdown('<div class="dash-kpi-row">', unsafe_allow_html=True)

    r1 = st.columns(4, gap="medium")
    with r1[0]:
        val = f"{_fmt_thousand(s.output_kg.value)} Kg" if s.output_kg.available else "—"
        kpi_card("Production Volume", val, "Total output periode", accent="#a489ff")
    with r1[1]:
        val = _fmt_pct(s.yield_pct.value) if s.yield_pct.available else "—"
        ok = s.yield_pct.available and s.yield_pct.value >= targets.yield_min
        kpi_card("Yield", val, f"Target ≥ {targets.yield_min:g}%", accent="#77edb4",
                 status="BAIK" if ok else "PERHATIAN",
                 status_color="#77edb4" if ok else "#f7d578")
    with r1[2]:
        val = _fmt_pct(s.oee.oee.value) if s.oee.oee.available else "—"
        ok = s.oee.oee.available and s.oee.oee.value >= targets.oee_min
        kpi_card("OEE", val, f"Target ≥ {targets.oee_min:g}%", accent="#71d5e9",
                 status="BAIK" if ok else "PERHATIAN",
                 status_color="#77edb4" if ok else "#f7d578")
    with r1[3]:
        val = _fmt_pct(s.scrap_pct.value) if s.scrap_pct.available else "—"
        ok = s.scrap_pct.available and s.scrap_pct.value <= targets.scrap_max
        kpi_card("Scrap Rate", val, f"Target ≤ {targets.scrap_max:g}%", accent="#ff9eaa",
                 status="BAIK" if ok else "PERHATIAN",
                 status_color="#77edb4" if ok else "#f7d578")

    st.markdown('<div class="dash-gap-sm"></div>', unsafe_allow_html=True)

    r2 = st.columns(4, gap="medium")
    with r2[0]:
        val = _fmt_rp(s.cost_per_kg.value) if s.cost_per_kg.available else "—"
        kpi_card("Cost / Kg", val, "Biaya produksi per Kg", accent="#bc9cf6")
    with r2[1]:
        val = _fmt_rp(s.cogm.value) if s.cogm.available else "—"
        kpi_card("COGM", val, "Cost of Goods Manufactured", accent="#ec3f92")
    with r2[2]:
        val = _fmt_pct(s.oee.availability.value) if s.oee.availability.available else "—"
        kpi_card("Availability", val, "OEE component", accent="#a489ff")
    with r2[3]:
        val = _fmt_pct(s.oee.quality.value) if s.oee.quality.available else "—"
        kpi_card("Quality", val, "OEE component", accent="#89d84a")

    st.markdown('</div>', unsafe_allow_html=True)


# ==================== HIGHLIGHTS ====================
def _render_highlights(s, targets, alerts) -> None:
    from .components import section_header, highlight_card
    section_header("Executive Highlights",
                   "Sorotan untuk keputusan operasional periode terpilih",
                   "RINGKASAN")
    st.markdown('<div class="dash-highlights">', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4, gap="medium")

    with c1:
        if s.yield_pct.available and s.yield_pct.value >= targets.yield_min:
            body = f"Yield {_fmt_pct(s.yield_pct.value)} di atas target · OEE {_fmt_pct(s.oee.oee.value)}"
        else:
            body = f"Yield {_fmt_pct(s.yield_pct.value)} — perlu ditingkatkan. OEE {_fmt_pct(s.oee.oee.value)}"
        highlight_card("Pencapaian", body, color="#77edb4", bg="#172d35", line="#276956")

    with c2:
        if s.scrap_pct.available:
            body = f"Scrap {_fmt_pct(s.scrap_pct.value)} · target ≤ {targets.scrap_max:g}%. Periksa setup dan changeover."
        else:
            body = "Data scrap belum tersedia untuk periode ini."
        highlight_card("Perhatian", body, color="#f7d578", bg="#302b30", line="#756036")

    with c3:
        if alerts:
            top = alerts[0]
            body = f"{top.title} · Dampak {_fmt_rp(top.annual_rp)}/tahun."
        else:
            body = "Tidak ada risiko aktif terdeteksi pada periode ini."
        highlight_card("Risiko", body, color="#ff9eaa", bg="#35243a", line="#794456")

    with c4:
        if s.score.reasons:
            body = " · ".join(s.score.reasons[:2])
        else:
            body = "Pertahankan performa saat ini dan pantau KPI kunci."
        highlight_card("Rekomendasi", body, color="#c4aaff", bg="#292449", line="#6551a0")

    st.markdown('</div>', unsafe_allow_html=True)


# ==================== KPI vs TARGET ====================
def _render_kpi_vs_target(s, targets) -> None:
    from .components import section_header
    from .charts import gauge
    section_header("KPI vs Target",
                   "Visual pencapaian target · garis penanda = target",
                   "TARGET")
    g1, g2, g3 = st.columns(3, gap="medium")
    with g1:
        if s.yield_pct.available:
            st.plotly_chart(gauge("Yield", s.yield_pct.value, targets.yield_min,
                                  min_val=85, max_val=100, higher_is_better=True),
                            width='stretch')
    with g2:
        if s.scrap_pct.available:
            st.plotly_chart(gauge("Scrap", s.scrap_pct.value, targets.scrap_max,
                                  min_val=0, max_val=10, higher_is_better=False),
                            width='stretch')
    with g3:
        if s.oee.oee.available:
            st.plotly_chart(gauge("OEE", s.oee.oee.value, targets.oee_min,
                                  min_val=60, max_val=100, higher_is_better=True),
                            width='stretch')


# ==================== COST ALERTS ====================
def _render_alerts(s, targets) -> None:
    from .components import section_header
    alerts = compute_alerts(s, targets)
    section_header(
        "Cost Alert Aktif",
        "Peringatan otomatis dengan dampak finansial terukur",
        f"{len(alerts)} ALERT" if alerts else "AMAN")

    if not alerts:
        st.success("✅ Tidak ada peringatan aktif. Semua KPI dalam batas target.")
        return

    total_annual = sum(abs(a.annual_rp) for a in alerts)

    # Total banner (compact)
    if total_annual > 0:
        st.markdown(
            f'<div style="background:#302b30;border:1px solid #756036;'
            f'border-radius:10px;padding:12px 16px;margin-bottom:10px;">'
            f'<span style="color:#f7d578;font-weight:800;font-size:0.62rem;'
            f'letter-spacing:0.08em;text-transform:uppercase;">💰 Total Potensi Dampak</span>'
            f'<div style="color:#ffffff;font-size:1.1rem;font-weight:800;'
            f'margin-top:4px;letter-spacing:-0.02em;">'
            f'{_fmt_rp(total_annual)} / tahun</div>'
            f'</div>',
            unsafe_allow_html=True)

    # Compact alert cards
    for a in alerts:
        icon_map = {"high": "🔴", "medium": "🟡", "info": "🔵"}
        border_map = {"high": "#ff9eaa", "medium": "#f7d578", "info": "#71d5e9"}
        bg_map = {"high": "#35243a", "medium": "#302b30", "info": "#242748"}

        icon = icon_map.get(a.severity, "⚪")
        border = border_map.get(a.severity, "#adb6d5")
        bg = bg_map.get(a.severity, "#242748")

        st.markdown(
            f'<div style="background:{bg};border:1px solid #343858;'
            f'border-left:4px solid {border};border-radius:10px;'
            f'padding:12px 14px;margin-bottom:8px;">'
            f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">'
            f'<span style="font-size:0.9rem;">{icon}</span>'
            f'<span style="color:#f5f6ff;font-weight:700;font-size:0.85rem;'
            f'letter-spacing:-0.01em;">{a.title}</span>'
            f'</div>'
            f'<div style="color:#adb6d5;font-size:0.78rem;line-height:1.4;'
            f'margin-bottom:6px;">{a.message}</div>'
            f'<div style="display:flex;justify-content:space-between;'
            f'align-items:center;gap:12px;flex-wrap:wrap;">'
            f'<span style="color:#f7d578;font-weight:700;font-size:0.72rem;">'
            f'💰 {_fmt_rp(a.monthly_rp)}/bln · {_fmt_rp(a.annual_rp)}/thn</span>'
            f'<span style="color:#8793bc;font-size:0.7rem;font-style:italic;">'
            f'🔧 {a.fix_hint}</span>'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True)


# ==================== ANALYSIS ====================
def _render_analysis(s) -> None:
    from .components import section_header, render_empty_state
    from .charts import pie_chart
    section_header("Analisis Biaya", "Cost Control Score dan struktur COGM", "COST")
    tab_score, tab_cogm = st.tabs(["🏆 Cost Control Score", "🥧 Struktur COGM"])

    with tab_score:
        if s.score.score is None:
            st.metric("Cost Control Score", "—")
            st.caption(s.score.note)
        else:
            c1, c2 = st.columns([1, 2], gap="medium")
            with c1:
                st.metric("Cost Control Score", f"{s.score.score}/100")
            with c2:
                if s.score.score >= 90: st.success(f"✅ {s.score.category}")
                elif s.score.score >= 80: st.info(f"ℹ️ {s.score.category}")
                elif s.score.score >= 70: st.warning(f"⚠️ {s.score.category}")
                else: st.error(f"🔴 {s.score.category}")
            for r in s.score.reasons:
                st.caption("• " + r)
            if s.score.note: st.caption(s.score.note)

    with tab_cogm:
        if s.breakdown:
            total = sum(s.breakdown.values())
            center = (f"Rp {total/1_000_000_000:.2f} M" if total >= 1e9
                      else f"Rp {total/1_000_000:.1f} jt")
            fig = px.pie(names=list(s.breakdown),
                         values=list(s.breakdown.values()), hole=0.55)
            fig = pie_chart(fig, height=320, center_text=center)
            st.plotly_chart(fig, width='stretch')
        else:
            render_empty_state(
                title="Breakdown COGM Tidak Tersedia",
                reason=f"Sistem belum bisa menghitung komposisi COGM. Alasan: *{s.cogm.note}*",
                icon="🥧",
                hint="Pastikan sheet biaya Anda berisi kolom **Cost** dan **Period**.")


# ==================== MoM ====================
def _render_monthly(ds: Dataset) -> None:
    from .components import section_header, render_empty_state
    section_header("Analisis Bulanan",
                   "Perbandingan bulan-ke-bulan (MoM) · cocok untuk laporan",
                   "MoM")
    periods = available_periods(ds)
    if len(periods) < 2:
        render_empty_state(
            title="Belum Cukup Periode untuk Perbandingan",
            reason=f"Saat ini hanya ada **{len(periods)} periode**. Butuh minimal **2 periode**.",
            icon="📆",
            hint="Pastikan file Excel punya kolom **Period** berisi >1 bulan.")
        return
    c1, c2 = st.columns(2, gap="medium")
    if len(periods) >= 3:
        prev = c1.selectbox("Periode Sebelumnya", periods, index=len(periods) - 3, key="dc_prev_v3")
        curr = c2.selectbox("Periode Sekarang", periods, index=len(periods) - 2, key="dc_curr_v3")
    else:
        prev = c1.selectbox("Periode Sebelumnya", periods, index=0, key="dc_prev_v3")
        curr = c2.selectbox("Periode Sekarang", periods, index=len(periods) - 1, key="dc_curr_v3")
    if prev == curr:
        st.warning("Pilih periode yang berbeda.")
        return
    comps = compare_periods(ds, prev, curr)
    rows = []
    for c in comps:
        if c.is_improving is True: status = "✅ Membaik"
        elif c.is_improving is False: status = "🔴 Memburuk"
        else: status = "➖ Stabil"
        rows.append({
            "KPI": c.label, prev: c.fmt_value(c.prev_value),
            curr: c.fmt_value(c.curr_value),
            "Δ": c.fmt_delta(), "Δ %": c.fmt_pct(), "Status": status,
        })
    import pandas as pd
    df_mom = pd.DataFrame(rows)
    from .components import render_table
    render_table(df_mom, max_height="400px")

    worsening = [c for c in comps if c.is_improving is False]
    if worsening:
        labels = ", ".join(c.label for c in worsening)
        st.warning(f"⚠️ **{len(worsening)} KPI memburuk** dibanding {prev}: {labels}")


# ==================== DAILY TREND ====================
def _render_daily(ds: Dataset, scope: Scope) -> None:
    from .components import section_header, render_empty_state, is_filter_too_narrow
    from .charts import line_chart, COLORS
    section_header("Trend Harian",
                   "Detail per hari · investigasi operasional & deteksi anomali",
                   "HARIAN")
    prod = scope_production(ds.production, scope)
    if not len(prod):
        unfiltered = ds.production
        if is_filter_too_narrow(prod, unfiltered):
            render_empty_state(
                title="Filter Anda Terlalu Sempit",
                reason="Ada data produksi, tapi tidak ada yang cocok dengan filter aktif.",
                icon="🔍",
                hint="Coba longgarkan filter Plant, Line, atau perlebar tanggal di sidebar.")
        else:
            render_empty_state(
                title="Tidak Ada Data Produksi",
                reason="Sheet **Production** kosong atau tidak ada.",
                icon="📊",
                hint="Pastikan file Excel punya sheet **Production** dengan kolom Date, Machine, Output_Kg.")
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
            text=f"<b>{_fmt_thousand(row['Output_Kg'])}</b>",
            showarrow=False, yshift=14,
            font=dict(size=9, color=COLORS["primary_dark"], family="DM Sans"),
            bgcolor="rgba(26, 29, 61, 0.9)",
            bordercolor=COLORS["primary_light"],
            borderwidth=1, borderpad=2)
    avg_val = daily["Output_Kg"].mean()
    fig.add_hline(
        y=avg_val, line_dash="dash",
        line_color=COLORS["accent"], line_width=2,
        annotation_text=f"<b>AVG {_fmt_thousand(avg_val)}</b>",
        annotation_position="right",
        annotation_font=dict(size=10, color=COLORS["accent_dark"], family="DM Sans"))
    fig.update_traces(
        line=dict(color=COLORS["primary"]),
        marker=dict(size=5, color=COLORS["primary"], line=dict(color="#0d1026", width=2)))
    fig = line_chart(fig, height=340, y_title="Output (Kg)")
    fig.update_layout(margin=dict(t=50, b=60, l=60, r=80))
    st.plotly_chart(fig, width='stretch')


# ==================== MAIN ====================
def render(ds: Dataset, scope: Scope) -> None:
    _inject_css()
    s = _cached_summarize(ds, scope)
    targets = _active_targets()
    alerts = compute_alerts(s, targets)
    _render_header(ds, s)
    _render_score_panel(s, targets)
    _render_kpi_grid(s, targets)
    st.markdown('<div class="dash-gap-lg"></div>', unsafe_allow_html=True)
    _render_highlights(s, targets, alerts)
    st.markdown('<div class="dash-gap-lg"></div>', unsafe_allow_html=True)
    _render_kpi_vs_target(s, targets)
    st.markdown('<div class="dash-gap-lg"></div>', unsafe_allow_html=True)
    _render_alerts(s, targets)
    st.markdown('<div class="dash-gap-lg"></div>', unsafe_allow_html=True)
    _render_analysis(s)
    st.markdown('<div class="dash-gap-lg"></div>', unsafe_allow_html=True)
    _render_monthly(ds)
    st.markdown('<div class="dash-gap-lg"></div>', unsafe_allow_html=True)
    _render_daily(ds, scope)