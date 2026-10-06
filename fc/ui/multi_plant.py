"""Multi-Plant & Cost Allocation - data-driven (BRD 6)."""
import pandas as pd
import plotly.express as px
import streamlit as st

from ..kpi import Scope, scope_production
from ..pipeline import Dataset


def render(ds: Dataset, scope: Scope) -> None:
    st.title("🏭 Multi-Plant & Cost Allocation")

    if ds.production is None or ds.production.empty:
        st.warning("Data produksi tidak tersedia.")
        return
    if "Plant" not in ds.production.columns:
        st.info("Kolom **Plant** tidak ada di sheet Production. Fitur multi-plant tidak tersedia.")
        return

    prod = scope_production(ds.production, scope)
    if prod.empty:
        st.info("Tidak ada data produksi pada filter terpilih.")
        return

    agg = prod.groupby("Plant", as_index=False).agg(
        Output_Kg=("Output_Kg", "sum"),
        Rows=("Output_Kg", "count"),
    )
    agg["Share_Pct"] = agg["Output_Kg"] / agg["Output_Kg"].sum() * 100

    costs = ds.costs
    if (costs is not None and not costs.empty
            and "Plant" in costs.columns and costs["Plant"].notna().any()):
        c_by_plant = costs.groupby("Plant", as_index=False)["Cost"].sum()
        agg = agg.merge(c_by_plant, on="Plant", how="left")
        agg["Cost"] = agg["Cost"].fillna(0)
        agg["Cost_Kg"] = agg["Cost"] / agg["Output_Kg"].replace(0, pd.NA)
    else:
        agg["Cost"] = pd.NA
        agg["Cost_Kg"] = pd.NA
        st.info("Dimensi biaya per Plant belum tersedia → kolom Cost tidak diisi.")

    st.subheader("Ringkasan per Plant")
    st.dataframe(agg, use_container_width=True, hide_index=True)

    fig = px.bar(agg, x="Plant", y="Output_Kg", text_auto=",.0f",
                 title="Total Output per Plant (Kg)")
    st.plotly_chart(fig, use_container_width=True)

    if agg["Cost"].notna().any() and agg["Cost"].sum() > 0:
        fig2 = px.pie(agg, names="Plant", values="Cost", hole=0.45,
                      title="Distribusi Biaya per Plant")
        st.plotly_chart(fig2, use_container_width=True)