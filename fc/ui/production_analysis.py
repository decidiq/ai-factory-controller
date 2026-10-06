"""Production Analysis - data-driven via fc.kpi (BRD 6)."""
import plotly.express as px
import streamlit as st

from ..kpi import Scope, oee_kpi, scrap_kpi, scope_production, yield_kpi
from ..pipeline import Dataset


def _fmt(col, label, kpi, fmt):
    if kpi.available:
        col.metric(label + (" (estimasi)" if kpi.status == "estimate" else ""),
                   fmt.format(kpi.value))
        if kpi.note:
            col.caption(kpi.note)
    else:
        col.metric(label, "—")
        col.caption(f"Tidak tersedia: {kpi.note}")


def render(ds: Dataset, scope: Scope) -> None:
    st.title("📈 Production Analysis")

    prod = scope_production(ds.production, scope)
    if prod.empty:
        st.info("Tidak ada data produksi pada filter terpilih.")
        return

    y = yield_kpi(prod)
    s = scrap_kpi(prod, y)
    o = oee_kpi(prod)

    c = st.columns(4)
    _fmt(c[0], "Yield", y, "{:.2f}%")
    _fmt(c[1], "Scrap", s, "{:.2f}%")
    _fmt(c[2], "OEE", o.oee, "{:.2f}%")
    c[3].metric("Baris Produksi", f"{len(prod):,}")

    with st.expander("Rincian OEE"):
        cc = st.columns(3)
        _fmt(cc[0], "Availability", o.availability, "{:.2f}%")
        _fmt(cc[1], "Performance", o.performance, "{:.2f}%")
        _fmt(cc[2], "Quality", o.quality, "{:.2f}%")

    st.subheader("Tren Harian")
    cols_y = ["Output_Kg"] + (["Scrap_Kg"] if "Scrap_Kg" in prod.columns else [])
    daily = prod.groupby("Date", as_index=False)[cols_y].sum()
    fig = px.line(daily, x="Date", y=cols_y, markers=False)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Detail Data Produksi")
    st.dataframe(prod, use_container_width=True, hide_index=True)