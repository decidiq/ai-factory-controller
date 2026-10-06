"""Halaman Cost DNA — variance decomposition & waterfall."""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from ..intel.cost_dna import decompose_variance, waterfall_cogm
from ..kpi import Scope, cogm_for_scope
from ..pipeline import Dataset


def _periods(df):
    if df is None or df.empty or "Period" not in df.columns:
        return []
    return sorted([str(p) for p in df["Period"].dropna().unique() if str(p).strip()])


def render(ds: Dataset, scope: Scope) -> None:
    st.title("💰 Cost DNA Engine")
    st.markdown("Uraikan perubahan biaya: **harga**, **volume**, **mix**, **efisiensi**.")

    if ds.costs is None or ds.costs.empty:
        st.warning("Data biaya tidak tersedia.")
        return

    cogm_kpi, breakdown = cogm_for_scope(ds.costs, ds.production, scope)

    if not cogm_kpi.available or not breakdown:
        st.info(f"COGM tidak dapat dihitung: {cogm_kpi.note}")
        return

    st.subheader("📊 Waterfall COGM")
    df_c = waterfall_cogm(breakdown)
    if not df_c.empty:
        fig = go.Figure(go.Waterfall(
            name="COGM",
            orientation="v",
            measure=["relative"] * len(df_c) + ["total"],
            x=list(df_c["Category"]) + ["COGM Total"],
            y=list(df_c["Cost"]) + [df_c["Cost"].sum()],
            text=[f"Rp {c:,.0f}" for c in df_c["Cost"]] + [f"Rp {df_c['Cost'].sum():,.0f}"],
            textposition="outside",
            connector={"line": {"color": "#94a3b8"}},
        ))
        fig.update_layout(height=460, showlegend=False,
                          yaxis_title="Rp", xaxis_title="",
                          margin=dict(t=30, b=40, l=20, r=20))
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df_c, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("🔍 Variance Decomposition")

    periods = _periods(ds.raw_material)
    if len(periods) < 2:
        st.info("Butuh minimal **2 periode** di kolom **Period** sheet Raw_Material.")
        return

    c1, c2 = st.columns(2)
    p_prev = c1.selectbox("Periode Sebelumnya", periods,
                          index=max(0, len(periods) - 2))
    p_curr = c2.selectbox("Periode Sekarang", periods,
                          index=len(periods) - 1)

    if p_prev == p_curr:
        st.warning("Pilih periode yang berbeda.")
        return

    rm = ds.raw_material
    prev = rm[rm["Period"] == p_prev] if "Period" in rm.columns else pd.DataFrame()
    curr = rm[rm["Period"] == p_curr] if "Period" in rm.columns else pd.DataFrame()

    if prev.empty or curr.empty:
        st.info("Data Raw_Material untuk periode terpilih tidak tersedia.")
        return

    dec = decompose_variance(curr, prev, scope_plant=scope.plant)

    if abs(dec.total) < 1:
        st.success("Tidak ada perubahan signifikan.")
        return

    df_dec = pd.DataFrame(
        [{"Komponen": k, "Nilai": v} for k, v in dec.as_dict().items() if abs(v) > 1]
    )
    if not df_dec.empty:
        fig = px.bar(df_dec, x="Nilai", y="Komponen", orientation="h",
                     text="Nilai", color="Nilai",
                     color_continuous_scale=["#16a34a", "#eab308", "#dc2626"])
        fig.update_traces(texttemplate="Rp %{text:,.0f}", textposition="outside")
        fig.update_layout(height=340, showlegend=False, coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    total = dec.total
    st.markdown(f"**Total perubahan COGM:** Rp {total:,.0f}")
    top_k, top_v = max(dec.as_dict().items(), key=lambda kv: abs(kv[1]))
    pct = abs(top_v) / abs(total) * 100 if total else 0
    st.markdown(f"**Penyebab utama:** {top_k} — Rp {top_v:,.0f} ({pct:.0f}%)")