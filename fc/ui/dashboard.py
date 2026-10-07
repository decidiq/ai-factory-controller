"""Halaman Dashboard - alert impact Rp + perbandingan periode MoM."""
import streamlit as st

from ..config import TARGETS as DEFAULT_TARGETS
from ..intel.alert_impact import compute_alerts
from ..intel.period_compare import available_periods, compare_periods
from ..kpi import KPI, Scope, scope_production, summarize
from ..pipeline import Dataset


def _active_targets():
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

    if len(periods) >= 3:
        prev = c1.selectbox("Periode Sebelumnya", periods,
                            index=len(periods) - 3, key="dc_prev_v2")
        curr = c2.selectbox("Periode Sekarang", periods,
                            index=len(periods) - 2, key="dc_curr_v2")
    else:
        prev = c1.selectbox("Periode Sebelumnya", periods,
                            index=0, key="dc_prev_v2")
        curr = c2.selectbox("Periode Sekarang", periods,
                            index=len(periods) - 1, key="dc_curr_v2")

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

    st.title("🏭 DECIDIQ")
    st.markdown("##### *Decision Intelligence Dashboard*")

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
        st.subheader("🚨 Cost Alert Aktif (diurutkan berdasarkan Financial Impact)")

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

    # ---- KPI vs Target (Gauge) ----
    from .charts import gauge

    st.markdown("### 🎯 KPI vs Target")
    st.caption("Visual pencapaian target. Garis oranye = target.")

    g1, g2, g3 = st.columns(3)

    with g1:
        if s.yield_pct.available:
            st.plotly_chart(
                gauge("Yield", s.yield_pct.value, targets.yield_min,
                      min_val=85, max_val=100, higher_is_better=True),
                use_container_width=True,
            )

    with g2:
        if s.scrap_pct.available:
            st.plotly_chart(
                gauge("Scrap", s.scrap_pct.value, targets.scrap_max,
                      min_val=0, max_val=10, higher_is_better=False),
                use_container_width=True,
            )

    with g3:
        if s.oee.oee.available:
            st.plotly_chart(
                gauge("OEE", s.oee.oee.value, targets.oee_min,
                      min_val=60, max_val=100, higher_is_better=True),
                use_container_width=True,
            )

    st.markdown("---")

    # ---- Perbandingan Periode ----
    st.subheader("📅 Month-over-Month (MoM)")
    st.caption("Bandingkan KPI antar 2 bulan untuk melihat tren.")
    _render_period_compare(ds)

    st.markdown("---")

    # ---- Bottom Charts ----
    c_score, c_cogm, c_trend = st.columns([1, 1.2, 1.4])

    with c_score:
        st.subheader("🏆 Cost Control Score")
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

    with c_cogm:
        from .charts import pie_chart
        st.markdown(
            '<div style="font-weight:700;color:#1E1B4B;margin-bottom:8px;">'
            '🥧 Struktur COGM</div>',
            unsafe_allow_html=True,
        )
        if s.breakdown:
            total = sum(s.breakdown.values())
            center = (f"Rp {total/1_000_000_000:.2f} M" if total >= 1e9
                      else f"Rp {total/1_000_000:.1f} jt")
            fig = px.pie(names=list(s.breakdown),
                         values=list(s.breakdown.values()), hole=0.55)
            fig = pie_chart(fig, height=320, center_text=center)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info(f"Data tidak tersedia: {s.cogm.note}")

    with c_trend:
        from .charts import line_chart, COLORS
        st.markdown(
            '<div style="font-weight:700;color:#1E1B4B;margin-bottom:8px;">'
            '📈 Output Harian</div>',
            unsafe_allow_html=True,
        )
        prod = scope_production(ds.production, scope)
        if len(prod):
            daily = prod.groupby("Date", as_index=False)["Output_Kg"].sum()
            daily = daily.sort_values("Date").reset_index(drop=True)

            # Tentukan interval label: kalau data banyak, tampilkan setiap N titik
            n = len(daily)
            if n <= 10:
                step = 1      # semua
            elif n <= 20:
                step = 2      # setiap 2
            elif n <= 40:
                step = 4      # setiap 4
            else:
                step = 7      # setiap 7 (weekly)

            fig = px.line(daily, x="Date", y="Output_Kg", markers=True)

            # Label angka di titik yang sudah dipilih
            label_df = daily.iloc[::step].copy()
            for _, row in label_df.iterrows():
                fig.add_annotation(
                    x=row["Date"], y=row["Output_Kg"],
                    text=f"<b>{row['Output_Kg']:,.0f}</b>",
                    showarrow=False,
                    yshift=14,
                    font=dict(size=9, color=COLORS["primary_dark"],
                              family="Inter"),
                    bgcolor="rgba(245, 243, 255, 0.9)",
                    bordercolor=COLORS["primary_light"],
                    borderwidth=1, borderpad=2,
                )

            # Garis rata-rata
            avg_val = daily["Output_Kg"].mean()
            fig.add_hline(
                y=avg_val,
                line_dash="dash",
                line_color=COLORS["accent"],
                line_width=2,
                annotation_text=f"<b>AVG {avg_val:,.0f}</b>",
                annotation_position="right",
                annotation_font=dict(size=10, color=COLORS["accent_dark"],
                                     family="Inter"),
            )

            fig.update_traces(
                line=dict(color=COLORS["primary"]),
                marker=dict(size=5, color=COLORS["primary"],
                            line=dict(color="#FFFFFF", width=2)),
            )

            fig = line_chart(fig, height=360, y_title="Output (Kg)")
            fig.update_layout(margin=dict(t=50, b=60, l=60, r=80))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Tidak ada data produksi pada filter terpilih.")