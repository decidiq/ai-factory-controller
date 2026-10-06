"""Halaman Dashboard - alert impact Rp + perbandingan periode MoM."""
import streamlit as st

from ..config import TARGETS as DEFAULT_TARGETS
from ..intel.alert_impact import compute_alerts
from ..intel.period_compare import available_periods, compare_periods
from ..kpi import KPI, Scope, scope_production, summarize
from ..pipeline import Dataset


def _active_targets():
    """Target aktif — dari session (Settings) atau default."""
    return st.session_state.get("_targets") or DEFAULT_TARGETS


def _metric(col, label: str, kpi: KPI, fmt: str) -> None:
    if kpi.available:
        col.metric(label + (" (estimasi)" if kpi.status == "estimate" else ""),
                   fmt.format(kpi.value))
        if kpi.note:
            col.caption(kpi.note)
    else:
        col.metric(label, "—")
        col.caption(f"Data tidak tersedia: {kpi.note}")


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
    prev = c1.selectbox("Periode Sebelumnya", periods,
                        index=max(0, len(periods) - 2), key="dc_prev")
    curr = c2.selectbox("Periode Sekarang", periods,
                        index=len(periods) - 1, key="dc_curr")

    if prev == curr:
        st.warning("Pilih periode yang berbeda.")
        return

    comps = compare_periods(ds, prev, curr)

    rows = []
    for c in comps:
        improving = c.is_improving
        if improving is True:
            status = "✅ Membaik"
        elif improving is False:
            status = "🔴 Memburuk"
        else:
            status = "➖ Stabil"
        rows.append({
            "KPI": c.label,
            prev: c.fmt_value(c.prev_value),
            curr: c.fmt_value(c.curr_value),
            "Δ": c.fmt_delta(),
            "Δ %": c.fmt_pct(),
            "Status": status,
        })

    import pandas as pd
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    worsening = [c for c in comps if c.is_improving is False]
    if worsening:
        labels = ", ".join(c.label for c in worsening)
        st.warning(f"⚠️ **{len(worsening)} KPI memburuk** dibanding {prev}: {labels}")


def render(ds: Dataset, scope: Scope) -> None:
    import plotly.express as px

    s = summarize(ds, scope)
    targets = _active_targets()

    st.title("🏭 AI FACTORY CONTROLLER")
    st.markdown("##### *Manufacturing Cost Control & Performance Dashboard*")

    # Info target aktif
    st.caption(
        f"Sumber: {ds.report.source_label} · Data dibaca: {ds.report.loaded_at} · "
        f"{s.production_rows:,} baris produksi"
    )
    st.caption(
        f"🎯 Target aktif: Yield ≥ {targets.yield_min:g}% · "
        f"Scrap ≤ {targets.scrap_max:g}% · OEE ≥ {targets.oee_min:g}%"
    )

    st.markdown("---")

    # ---- Alert ----
    alerts = compute_alerts(s, targets)
    if alerts:
        st.subheader("🚨 Peringatan Aktif (diurutkan berdasarkan dampak Rp)")

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

    st.markdown("---")

    # ---- KPI Utama ----
    r1 = st.columns(3)
    _metric(r1[0], "Production Volume", s.output_kg, "{:,.0f} Kg")
    _metric(r1[1], "Yield", s.yield_pct, "{:.2f}%")
    _metric(r1[2], "OEE", s.oee.oee, "{:.2f}%")

    r2 = st.columns(3)
    _metric(r2[0], "Scrap", s.scrap_pct, "{:.2f}%")
    _metric(r2[1], "Cost/Kg", s.cost_per_kg, "Rp {:,.0f}")
    _metric(r2[2], "COGM", s.cogm, "Rp {:,.0f}")

    with st.expander("Rincian OEE (Availability × Performance × Quality)"):
        c = st.columns(3)
        _metric(c[0], "Availability", s.oee.availability, "{:.2f}%")
        _metric(c[1], "Performance", s.oee.performance, "{:.2f}%")
        _metric(c[2], "Quality", s.oee.quality, "{:.2f}%")

    st.markdown("---")

    # ---- Perbandingan Periode ----
    st.subheader("📅 Perbandingan Periode (MoM)")
    st.caption("Bandingkan KPI antar 2 bulan untuk melihat tren.")
    _render_period_compare(ds)

    st.markdown("---")

    c_score, c_cogm, c_trend = st.columns([1, 1.2, 1.4])

    with c_score:
        st.subheader("🏆 Controller Score")
        if s.score.score is None:
            st.metric("Controller Score", "—")
            st.caption(s.score.note)
        else:
            st.metric("Controller Score", f"{s.score.score}/100")
            (st.success if s.score.score >= 90 else st.info if s.score.score >= 80
             else st.warning if s.score.score >= 70 else st.error)(s.score.category)
            for r in s.score.reasons:
                st.caption("• " + r)
            if s.score.note:
                st.caption(s.score.note)
        st.caption(f"Target: Yield ≥ {targets.yield_min:g}% · "
                   f"Scrap ≤ {targets.scrap_max:g}% · OEE ≥ {targets.oee_min:g}%")

    with c_cogm:
        st.subheader("🥧 Struktur COGM")
        if s.breakdown:
            fig = px.pie(names=list(s.breakdown), values=list(s.breakdown.values()), hole=0.45)
            fig.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=300)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info(f"Data tidak tersedia: {s.cogm.note}")

    with c_trend:
        st.subheader("📈 Output Harian")
        prod = scope_production(ds.production, scope)
        if len(prod):
            daily = prod.groupby("Date", as_index=False)["Output_Kg"].sum()
            fig = px.line(daily, x="Date", y="Output_Kg", markers=False)
            fig.update_layout(margin=dict(t=10, b=10, l=10, r=10),
                              height=300, yaxis_title="Kg", xaxis_title="")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Tidak ada data produksi pada filter terpilih.")