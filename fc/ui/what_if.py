"""Halaman What-If Simulator."""
import pandas as pd
import streamlit as st

from ..intel.what_if import Scenario, simulate
from ..kpi import Scope, cogm_for_scope, scope_production
from ..pipeline import Dataset


def render(ds: Dataset, scope: Scope) -> None:
    st.title("🎛 What-If Simulator")
    st.markdown("Simulasikan skenario bisnis dan lihat dampaknya ke COGM & Cost/Kg secara real-time.")

    prod = scope_production(ds.production, scope)
    baseline_output = float(prod["Output_Kg"].sum()) if len(prod) else 0.0
    cogm_kpi, breakdown = cogm_for_scope(ds.costs, ds.production, scope)

    if not cogm_kpi.available or baseline_output <= 0:
        st.warning("Baseline tidak dapat dihitung (butuh data produksi & biaya pada filter ini).")
        return

    baseline_cogm = cogm_kpi.value
    material_share = (breakdown.get("Material", 0) / baseline_cogm) if baseline_cogm else 0.6

    st.markdown("### 🎚 Parameter Skenario")
    c1, c2 = st.columns(2)
    with c1:
        yield_pct = st.slider("Yield (%)", 90.0, 100.0, 97.5, 0.1)
        scrap_pct = st.slider("Scrap (%)", 0.0, 10.0, 2.2, 0.1)
        resin_price = st.slider("Perubahan Harga Material (%)", -20, 30, 0, 1)
    with c2:
        volume_pct = st.slider("Perubahan Volume Produksi (%)", -30, 50, 0, 1)
        st.metric("Baseline Output", f"{baseline_output:,.0f} Kg")
        st.metric("Baseline COGM", f"Rp {baseline_cogm:,.0f}")

    scenario = Scenario(
        yield_pct=yield_pct, scrap_pct=scrap_pct,
        resin_price_pct=resin_price, volume_pct=volume_pct,
    )

    result = simulate(
        baseline_output_kg=baseline_output,
        baseline_cogm=baseline_cogm,
        material_cost_share=material_share,
        scenario=scenario,
    )

    st.markdown("---")
    st.subheader("📊 Hasil Simulasi")

    m1, m2, m3 = st.columns(3)
    m1.metric("Output Baru", f"{result.output_kg:,.0f} Kg",
              delta=f"{(result.output_kg - baseline_output):+,.0f} Kg")
    m2.metric("COGM Baru", f"Rp {result.cogm:,.0f}",
              delta=f"Rp {result.cogm - baseline_cogm:+,.0f}",
              delta_color="inverse")
    m3.metric("Cost/Kg Baru", f"Rp {result.cost_per_kg:,.0f}",
              delta=f"Rp {result.cost_per_kg - result.baseline_cost_per_kg:+,.0f}",
              delta_color="inverse")

    st.markdown("### 💰 Hemat Tahunan")
    if result.savings_annual > 0:
        st.success(f"**Rp {result.savings_annual:,.0f}** (asumsi 12 bulan output sama)")
    elif result.savings_annual < 0:
        st.error(f"**Rp {abs(result.savings_annual):,.0f}** kenaikan biaya tahunan")
    else:
        st.info("Tidak ada perubahan signifikan.")

    st.markdown("---")
    st.markdown("### 💾 Simpan Skenario")
    name = st.text_input("Nama skenario", placeholder="mis. Optimis Q4")
    if st.button("Simpan") and name:
        st.session_state.setdefault("what_if_scenarios", []).append({
            "name": name, "yield": yield_pct, "scrap": scrap_pct,
            "resin": resin_price, "volume": volume_pct,
            "cogm": result.cogm, "cost_kg": result.cost_per_kg,
            "savings": result.savings_annual,
        })
        st.success(f"Skenario '{name}' tersimpan.")

    if st.session_state.get("what_if_scenarios"):
        st.markdown("### 📋 Skenario Tersimpan")
        df = pd.DataFrame(st.session_state["what_if_scenarios"])
        st.dataframe(df, use_container_width=True, hide_index=True)
        if st.button("🗑 Hapus semua skenario"):
            st.session_state["what_if_scenarios"] = []
            st.rerun()