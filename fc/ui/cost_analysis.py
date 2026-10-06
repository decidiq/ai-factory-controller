"""Cost Analysis - data-driven (BRD 6: COGM, Cost/Kg, Pareto)."""
import pandas as pd
import plotly.express as px
import streamlit as st

from ..config import targets_from_config
from ..kpi import Scope, cogm_for_scope, cost_per_kg, scope_production
from ..pipeline import Dataset


def render(ds: Dataset, scope: Scope) -> None:
    st.title("💰 Cost Analysis & COGM Controller")
    st.markdown("Analisis biaya operasional, Pareto material, dan struktur COGM.")

    if ds.costs is None or ds.costs.empty:
        st.warning("Data biaya tidak tersedia.")
        return

    targets = targets_from_config(ds.config)
    cogm, breakdown = cogm_for_scope(ds.costs, ds.production, scope)
    prod = scope_production(ds.production, scope)
    output_kg = float(prod["Output_Kg"].sum()) if len(prod) else 0.0

    if not cogm.available:
        st.info(f"COGM tidak dapat dihitung: {cogm.note}")
        return

    cpk = cost_per_kg(cogm, output_kg)

    c1, c2, c3 = st.columns(3)
    c1.metric("Total COGM", f"Rp {cogm.value:,.0f}")
    c2.metric("Output (Kg)", f"{output_kg:,.0f}")
    if cpk.available:
        c3.metric("Cost/Kg", f"Rp {cpk.value:,.0f}")
        if targets.max_cost_per_kg > 0 and cpk.value > targets.max_cost_per_kg:
            st.warning(f"⚠️ Cost/Kg Rp {cpk.value:,.0f} melampaui batas "
                       f"Rp {targets.max_cost_per_kg:,.0f}.")
    else:
        c3.metric("Cost/Kg", "—")
        c3.caption(cpk.note)

    if breakdown:
        st.subheader("Distribusi Komponen COGM")
        df_c = pd.DataFrame(list(breakdown.items()), columns=["Category", "Cost"])
        df_c = df_c[df_c["Cost"] > 0]
        if not df_c.empty:
            fig = px.pie(df_c, names="Category", values="Cost", hole=0.45)
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(df_c, use_container_width=True, hide_index=True)

    # Pareto Raw Material Top 10
    if (ds.raw_material is not None and not ds.raw_material.empty
            and "Material" in ds.raw_material.columns
            and "Cost" in ds.raw_material.columns):
        st.subheader("Pareto Material Top 10")
        rm = ds.raw_material.copy()
        if scope.plant and "Plant" in rm.columns:
            rm = rm[rm["Plant"].eq(scope.plant).fillna(False)]
        if not rm.empty:
            top = (rm.groupby("Material", as_index=False)["Cost"].sum()
                     .sort_values("Cost", ascending=False).head(10))
            top["Cumulative_Pct"] = top["Cost"].cumsum() / top["Cost"].sum() * 100
            fig = px.bar(top, x="Material", y="Cost", text_auto=",.0f")
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(top, use_container_width=True, hide_index=True)
    else:
        st.info("Data Raw_Material tidak tersedia.")