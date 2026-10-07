"""Halaman What-If Simulator — premium UI."""
import pandas as pd
import streamlit as st

from ..intel.what_if import Scenario, simulate
from ..kpi import Scope, cogm_for_scope, scope_production
from ..pipeline import Dataset


def _render_header():
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #1E1B4B 0%, #4C1D95 50%, #8B5CF6 100%);
        color: #FFFFFF;
        padding: 24px 30px;
        border-radius: 16px;
        box-shadow: 0 10px 30px rgba(139, 92, 246, 0.25);
        margin-bottom: 24px;
    ">
        <div style="
            font-size: 0.75rem;
            letter-spacing: 1.5px;
            opacity: 0.85;
            font-weight: 600;
            margin-bottom: 8px;
        ">🎛 WHAT-IF SIMULATOR</div>
        <div style="
            font-size: 1.7rem;
            font-weight: 800;
            letter-spacing: -0.8px;
            line-height: 1.15;
        ">Simulasikan skenario bisnis Anda</div>
        <div style="
            font-size: 0.9rem;
            opacity: 0.9;
            margin-top: 8px;
        ">Geser slider untuk melihat dampak langsung ke COGM & Cost/Kg.</div>
    </div>
    """, unsafe_allow_html=True)


def _render_baseline(prod, cogm_kpi, material_share):
    """Card baseline info."""
    baseline_output = float(prod["Output_Kg"].sum()) if len(prod) else 0.0
    baseline_cogm = cogm_kpi.value if cogm_kpi.available else 0

    st.markdown("### 📊 Baseline (Current State)")

    c1, c2, c3 = st.columns(3)
    c1.metric("Output Saat Ini", f"{baseline_output:,.0f} Kg")
    c2.metric("COGM Saat Ini", f"Rp {baseline_cogm:,.0f}")
    c3.metric("Material Share", f"{material_share*100:.0f}%",
              help="Porsi biaya material terhadap COGM")

    return baseline_output, baseline_cogm


def _render_slider_panel():
    """Panel slider skenario."""
    st.markdown("### 🎚 Parameter Skenario")
    st.caption("Atur nilai untuk simulasi. Hasil berubah secara real-time.")

    c1, c2 = st.columns(2)

    with c1:
        yield_pct = st.slider(
            "📈 Yield (%)",
            min_value=90.0, max_value=100.0,
            value=97.5, step=0.1,
            help="Naikkan yield untuk simulasi perbaikan proses.",
        )
        scrap_pct = st.slider(
            "🗑️ Scrap (%)",
            min_value=0.0, max_value=10.0,
            value=2.2, step=0.1,
            help="Turunkan scrap untuk simulasi pengurangan pemborosan.",
        )

    with c2:
        resin_price = st.slider(
            "💰 Perubahan Harga Material (%)",
            min_value=-20, max_value=30,
            value=0, step=1,
            help="Simulasi kenaikan/penurunan harga supplier.",
        )
        volume_pct = st.slider(
            "📦 Perubahan Volume Produksi (%)",
            min_value=-30, max_value=50,
            value=0, step=1,
            help="Simulasi kenaikan/penurunan order.",
        )

    return Scenario(
        yield_pct=yield_pct,
        scrap_pct=scrap_pct,
        resin_price_pct=resin_price,
        volume_pct=volume_pct,
    )


def _render_result(result, baseline_output, baseline_cogm):
    """Hasil simulasi dengan visual premium."""
    st.markdown("### 🎯 Hasil Simulasi")

    # Big impact card
    savings = result.savings_annual
    if savings > 0:
        impact_color = "#10B981"
        impact_icon = "💚"
        impact_label = "COST SAVING TAHUNAN"
        impact_bg = "linear-gradient(135deg, #10B981 0%, #059669 100%)"
    elif savings < 0:
        impact_color = "#EF4444"
        impact_icon = "⚠️"
        impact_label = "KENAIKAN BIAYA TAHUNAN"
        impact_bg = "linear-gradient(135deg, #EF4444 0%, #DC2626 100%)"
    else:
        impact_color = "#64748B"
        impact_icon = "➖"
        impact_label = "TIDAK ADA PERUBAHAN SIGNIFIKAN"
        impact_bg = "linear-gradient(135deg, #64748B 0%, #475569 100%)"

    if savings >= 1_000_000_000:
        impact_val = f"Rp {savings/1_000_000_000:.2f} M"
    elif savings >= 1_000_000:
        impact_val = f"Rp {abs(savings)/1_000_000:.1f} jt"
    else:
        impact_val = f"Rp {abs(savings):,.0f}"

    st.markdown(f"""
    <div style="
        background: {impact_bg};
        color: #FFFFFF;
        padding: 26px 30px;
        border-radius: 16px;
        box-shadow: 0 10px 30px rgba(16, 185, 129, 0.25);
        margin-bottom: 24px;
    ">
        <div style="
            font-size: 0.75rem;
            letter-spacing: 1.5px;
            opacity: 0.9;
            font-weight: 600;
            margin-bottom: 8px;
        ">{impact_icon} {impact_label}</div>
        <div style="
            font-size: 2.6rem;
            font-weight: 800;
            letter-spacing: -1.5px;
            line-height: 1.1;
        ">{impact_val}</div>
        <div style="
            font-size: 0.85rem;
            opacity: 0.9;
            margin-top: 8px;
        ">Asumsi: 12 bulan dengan output yang sama.</div>
    </div>
    """, unsafe_allow_html=True)

    # Metric comparisons
    st.markdown("#### 📊 Perbandingan Detail")
    c1, c2, c3 = st.columns(3)

    with c1:
        delta_output = result.output_kg - baseline_output
        st.metric(
            "Output Baru",
            f"{result.output_kg:,.0f} Kg",
            delta=f"{delta_output:+,.0f} Kg",
        )

    with c2:
        delta_cogm = result.cogm - baseline_cogm
        st.metric(
            "COGM Baru",
            f"Rp {result.cogm:,.0f}",
            delta=f"Rp {delta_cogm:+,.0f}",
            delta_color="inverse",
        )

    with c3:
        delta_cpk = result.cost_per_kg - result.baseline_cost_per_kg
        st.metric(
            "Cost/Kg Baru",
            f"Rp {result.cost_per_kg:,.0f}",
            delta=f"Rp {delta_cpk:+,.0f}",
            delta_color="inverse",
        )

    # Additional metrics
    c4, c5, c6 = st.columns(3)
    c4.metric("Baseline Cost/Kg", f"Rp {result.baseline_cost_per_kg:,.0f}")
    c5.metric("Δ Cost/Kg", f"Rp {delta_cpk:+,.0f}")
    c6.metric(
        "Δ Output",
        f"{delta_output:+,.0f} Kg",
        delta=f"{(delta_output/baseline_output*100):+.1f}%" if baseline_output > 0 else "—",
    )

    # Comparison Chart
    st.markdown("#### 📊 Baseline vs Simulasi")
    from .charts import comparison_bar
    fig = comparison_bar(
        labels=["Output (Kg)", "COGM (Rp)", "Cost/Kg (Rp)"],
        baseline=[baseline_output, baseline_cogm, result.baseline_cost_per_kg],
        simulasi=[result.output_kg, result.cogm, result.cost_per_kg],
        height=340,
    )
    st.plotly_chart(fig, use_container_width=True)

def _render_scenario_save(current_scenario, result):
    """Form simpan skenario."""
    st.markdown("---")
    st.markdown("### 💾 Simpan Skenario")
    st.caption("Simpan kombinasi parameter untuk dibandingkan nanti.")

    c1, c2 = st.columns([3, 1])
    with c1:
        name = st.text_input(
            "Nama Skenario",
            placeholder="mis. Optimis Q4 — Yield 99% + Scrap 1.5%",
            label_visibility="collapsed",
        )
    with c2:
        save_btn = st.button("💾 Simpan", type="primary", use_container_width=True)

    if save_btn and name:
        st.session_state.setdefault("what_if_scenarios", []).append({
            "name": name,
            "yield": current_scenario.yield_pct,
            "scrap": current_scenario.scrap_pct,
            "resin": current_scenario.resin_price_pct,
            "volume": current_scenario.volume_pct,
            "cogm": result.cogm,
            "cost_kg": result.cost_per_kg,
            "savings": result.savings_annual,
        })
        st.success(f"✅ Skenario **'{name}'** tersimpan.")
        st.rerun()
    elif save_btn:
        st.warning("Masukkan nama skenario dulu.")


def _render_saved_scenarios():
    """Daftar skenario tersimpan."""
    scenarios = st.session_state.get("what_if_scenarios", [])
    if not scenarios:
        return

    st.markdown("### 📋 Skenario Tersimpan")

    df = pd.DataFrame(scenarios)

    display_df = df.copy()
    display_df["Cost Saving"] = display_df["savings"].apply(
        lambda x: f"Rp {x/1_000_000:+,.1f} jt" if x != 0 else "—"
    )
    display_df["COGM"] = display_df["cogm"].apply(lambda x: f"Rp {x:,.0f}")
    display_df["Cost/Kg"] = display_df["cost_kg"].apply(lambda x: f"Rp {x:,.0f}")

    display_cols = ["name", "yield", "scrap", "resin", "volume",
                    "cogm", "cost_kg", "Cost Saving"]
    rename_map = {
        "name": "Nama",
        "yield": "Yield (%)",
        "scrap": "Scrap (%)",
        "resin": "Δ Harga (%)",
        "volume": "Δ Volume (%)",
        "cogm": "COGM",
        "cost_kg": "Cost/Kg",
    }

    st.dataframe(
        display_df[display_cols].rename(columns=rename_map),
        use_container_width=True,
        hide_index=True,
    )

    c1, c2 = st.columns([1, 4])
    with c1:
        if st.button("🗑 Hapus Semua", use_container_width=True):
            st.session_state["what_if_scenarios"] = []
            st.rerun()
    with c2:
        st.caption(f"Total {len(scenarios)} skenario tersimpan di sesi ini.")


def render(ds: Dataset, scope: Scope) -> None:
    # Header premium
    _render_header()

    # Baseline check
    prod = scope_production(ds.production, scope)
    baseline_output = float(prod["Output_Kg"].sum()) if len(prod) else 0.0
    cogm_kpi, breakdown = cogm_for_scope(ds.costs, ds.production, scope)

    if not cogm_kpi.available or baseline_output <= 0:
        st.warning("⚠️ Baseline tidak dapat dihitung. Butuh data produksi & biaya pada filter ini.")
        return

    baseline_cogm = cogm_kpi.value
    material_share = (breakdown.get("Material", 0) / baseline_cogm) if baseline_cogm else 0.6

    # Baseline
    _, baseline_cogm_val = _render_baseline(prod, cogm_kpi, material_share)

    st.markdown("---")

    # Sliders
    scenario = _render_slider_panel()

    # Simulate
    result = simulate(
        baseline_output_kg=baseline_output,
        baseline_cogm=baseline_cogm_val,
        material_cost_share=material_share,
        scenario=scenario,
    )

    st.markdown("---")

    # Results
    _render_result(result, baseline_output, baseline_cogm_val)

    st.markdown("---")

    # Save scenario
    _render_scenario_save(scenario, result)

    # Saved scenarios
    _render_saved_scenarios()

    st.markdown("---")
    with st.expander("ℹ️ Cara kerja What-If Simulator"):
        st.markdown(
            "**Model simulasi:**\n"
            "- **Yield effect** — yield naik X% → COGM turun ~X% (dengan skala)\n"
            "- **Volume effect** — volume naik → fixed cost ter-dilusi (Cost/Kg turun)\n"
            "- **Price effect** — harga material naik X% → COGM naik X × material_share\n\n"
            "**Asumsi:**\n"
            "- Harga jual tetap (tidak berubah dengan volume)\n"
            "- Material cost share konstan\n"
            "- Fixed cost tidak berubah signifikan\n\n"
            "**Cost saving tahunan** = (Cost/Kg baseline − Cost/Kg baru) × Output baru × 12 bulan."
        )