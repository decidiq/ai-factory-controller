"""Risk Register - data-driven (BRD 5.4 & 6)."""
import pandas as pd
import plotly.express as px
import streamlit as st

from ..kpi import risk_table
from ..pipeline import Dataset


def render(ds: Dataset, scope) -> None:
    st.title("🛡️ Risk Register & Operational Mitigation")

    risk = ds.risk
    if risk is None or risk.empty:
        st.warning("Data Risk_Register tidak tersedia (sheet 'Risk_Register').")
        st.info("Sesuai BRD 5.5: tidak ada data pengganti yang ditampilkan.")
        return

    if "Risk" not in risk.columns:
        st.error("Sheet Risk_Register harus punya kolom **Risk**.")
        st.dataframe(risk.head(20), use_container_width=True)
        return

    if not {"Probability_Val", "Impact_Val"} <= set(risk.columns):
        st.error("Sheet Risk_Register butuh **Probability_Val** & **Impact_Val** "
                 "(hasil pemetaan High/Medium/Low → 3/2/1, skala 1-3).")
        st.dataframe(risk, use_container_width=True, hide_index=True)
        return

    tbl = risk_table(risk)

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Risiko", len(tbl))
    c2.metric("Tinggi (≥6)", int((tbl["Level"] == "Tinggi").sum()))
    c3.metric("Sedang (3-5)", int((tbl["Level"] == "Sedang").sum()))

    st.subheader("Heat Map Risiko")
    try:
        heat = tbl.pivot_table(index="Impact_Val", columns="Probability_Val",
                               values="Risk", aggfunc="count", fill_value=0)
        fig = px.imshow(heat, text_auto=True, aspect="auto",
                        labels=dict(x="Probability (1-3)", y="Impact (1-3)", color="Jumlah"),
                        color_continuous_scale="OrRd")
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.info(f"Heat map tidak dapat dibuat: {e}")

    st.subheader("Daftar Risiko")
    cols = [c for c in ("Risk", "Status", "Probability", "Impact",
                        "Probability_Val", "Impact_Val", "Score", "Level")
            if c in tbl.columns]
    st.dataframe(tbl[cols], use_container_width=True, hide_index=True)