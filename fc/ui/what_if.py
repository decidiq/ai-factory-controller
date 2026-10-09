"""Halaman What-If Simulator — premium UI."""
import pandas as pd
import streamlit as st

from ..intel.what_if import Scenario, simulate
from ..kpi import Scope, cogm_for_scope, scope_production, summarize
from ..pipeline import Dataset
from .components import (page_header, mini_health_score,
                         format_period_label, compute_health_score,
                         section_divider)


# ==================== CSS GLASSMORPHISM ====================
GLASS_CSS = """
<style>
.wi-glass {
    position: relative;
    background: linear-gradient(135deg, #FFFFFF 0%, #F5F3FF 100%);
    border: 1px solid rgba(196, 181, 253, 0.5);
    border-radius: 16px;
    padding: 16px 18px;
    box-shadow: 0 6px 20px rgba(139, 92, 246, 0.08);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    overflow: hidden;
    min-height: 100px;
    margin-bottom: 8px;
}
.wi-glass::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, var(--accent, #8B5CF6) 0%, #EC4899 100%);
}
.wi-glass:hover {
    transform: translateY(-3px);
    box-shadow: 0 16px 32px rgba(139, 92, 246, 0.18);
    border-color: rgba(139, 92, 246, 0.6);
}
.wi-glass-label {
    color: #6D28D9;
    font-weight: 700;
    font-size: 0.66rem;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    margin-bottom: 6px;
}
.wi-glass-value {
    color: #0F172A;
    font-weight: 800;
    font-size: 1.4rem;
    letter-spacing: -0.5px;
    line-height: 1.1;
    margin-bottom: 4px;
}
.wi-glass-note {
    color: #94A3B8;
    font-size: 0.68rem;
    font-style: italic;
    line-height: 1.3;
}
.wi-glass-delta {
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.3px;
}
</style>
"""


def _inject_css():
    st.markdown(GLASS_CSS, unsafe_allow_html=True)


def _active_targets():
    from ..config import TARGETS as DEFAULT_TARGETS
    return st.session_state.get("_targets") or DEFAULT_TARGETS


def _glass_card(col, label: str, value: str, accent: str = "#8B5CF6",
                note: str = None, delta: str = None,
                delta_color: str = None) -> None:
    note_html = f'<div class="wi-glass-note">{note}</div>' if note else ""
    delta_html = ""
    if delta:
        c = delta_color or "#10B981"
        delta_html = f'<div class="wi-glass-delta" style="color:{c};">{delta}</div>'
    html = (
        f'<div class="wi-glass" style="--accent: {accent};">'
        f'<div class="wi-glass-label">{label}</div>'
        f'<div class="wi-glass-value">{value}</div>'
        f'{delta_html}'
        f'{note_html}'
        f'</div>'
    )
    col.markdown(html, unsafe_allow_html=True)


def _fmt_rp(v: float) -> str:
    if abs(v) >= 1_000_000_000:
        return f"Rp {v/1_000_000_000:.2f} M"
    if abs(v) >= 1_000_000:
        return f"Rp {v/1_000_000:.1f} jt"
    return f"Rp {v:,.0f}"


# ==================== BASELINE ====================
def _render_baseline(prod, cogm_kpi, material_share):
    baseline_output = float(prod["Output_Kg"].sum()) if len(prod) else 0.0
    baseline_cogm = cogm_kpi.value if cogm_kpi.available else 0

    c1, c2, c3 = st.columns(3)
    _glass_card(c1, "Output Saat Ini", f"{baseline_output:,.0f} Kg",
                "#8B5CF6", note="Total output terfilter")
    _glass_card(c2, "COGM Saat Ini", f"Rp {baseline_cogm:,.0f}",
                "#EC4899", note="Cost of Goods Manufactured")
    _glass_card(c3, "Material Share", f"{material_share*100:.0f}%",
                "#F59E0B", note="Porsi biaya material dari COGM")

    return baseline_output, baseline_cogm


# ==================== SLIDERS ====================
def _render_slider_panel():
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


# ==================== RESULT ====================
def _render_result(result, baseline_output, baseline_cogm):
    savings = result.savings_annual
    if savings > 0:
        impact_icon = "💚"
        impact_label = "COST SAVING TAHUNAN"
        impact_bg = "linear-gradient(135deg, #10B981 0%, #059669 100%)"
    elif savings < 0:
        impact_icon = "⚠️"
        impact_label = "KENAIKAN BIAYA TAHUNAN"
        impact_bg = "linear-gradient(135deg, #EF4444 0%, #DC2626 100%)"
    else:
        impact_icon = "➖"
        impact_label = "TIDAK ADA PERUBAHAN SIGNIFIKAN"
        impact_bg = "linear-gradient(135deg, #64748B 0%, #475569 100%)"

    impact_val = _fmt_rp(abs(savings)) if savings != 0 else "Rp 0"

    st.markdown(f"""
    <div style="
        background: {impact_bg};
        color: #FFFFFF;
        padding: 26px 30px;
        border-radius: 16px;
        box-shadow: 0 10px 30px rgba(16, 185, 129, 0.25);
        margin-bottom: 24px;
    ">
        <div style="font-size: 0.75rem; letter-spacing: 1.5px; opacity: 0.9;
            font-weight: 600; margin-bottom: 8px;">{impact_icon} {impact_label}</div>
        <div style="font-size: 2.6rem; font-weight: 800; letter-spacing: -1.5px;
            line-height: 1.1;">{impact_val}</div>
        <div style="font-size: 0.85rem; opacity: 0.9; margin-top: 8px;">
            Asumsi: 12 bulan dengan output yang sama.</div>
    </div>
    """, unsafe_allow_html=True)

    # Metric comparisons (glass)
    st.markdown("#### 📊 Perbandingan Detail")
    c1, c2, c3 = st.columns(3)

    delta_output = result.output_kg - baseline_output
    delta_cogm = result.cogm - baseline_cogm
    delta_cpk = result.cost_per_kg - result.baseline_cost_per_kg

    _glass_card(c1, "Output Baru", f"{result.output_kg:,.0f} Kg", "#8B5CF6",
                delta=f"{delta_output:+,.0f} Kg",
                delta_color=("#10B981" if delta_output >= 0 else "#EF4444"))
    _glass_card(c2, "COGM Baru", f"Rp {result.cogm:,.0f}", "#EC4899",
                delta=f"Rp {delta_cogm:+,.0f}",
                delta_color=("#EF4444" if delta_cogm > 0 else "#10B981"))
    _glass_card(c3, "Cost/Kg Baru", f"Rp {result.cost_per_kg:,.0f}", "#F59E0B",
                delta=f"Rp {delta_cpk:+,.0f}",
                delta_color=("#EF4444" if delta_cpk > 0 else "#10B981"))

    # Additional metrics
    c4, c5, c6 = st.columns(3)
    _glass_card(c4, "Baseline Cost/Kg",
                f"Rp {result.baseline_cost_per_kg:,.0f}", "#94A3B8",
                note="Kondisi saat ini")
    _glass_card(c5, "Δ Cost/Kg", f"Rp {delta_cpk:+,.0f}",
                "#EF4444" if delta_cpk > 0 else "#10B981",
                note="Perubahan per Kg")
    pct_out = (delta_output / baseline_output * 100) if baseline_output > 0 else 0
    _glass_card(c6, "Δ Output", f"{delta_output:+,.0f} Kg",
                "#3B82F6", note=f"{pct_out:+.1f}% dari baseline")

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


# ==================== SAVE SCENARIO ====================
def _render_scenario_save(current_scenario, result):
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


# ==================== MAIN ====================
def render(ds: Dataset, scope: Scope) -> None:
    _inject_css()

    # ===== HEADER KONSISTEN =====
    page_header(
        title="What-If Simulator",
        subtitle=(
            f"Sumber: {ds.report.source_label} · "
            f"Simulasikan skenario bisnis & lihat dampaknya secara real-time"
        ),
        granularity="Multi",
        period_label=format_period_label(scope),
        icon="🎯",
    )

    prod = scope_production(ds.production, scope)
    baseline_output = float(prod["Output_Kg"].sum()) if len(prod) else 0.0
    cogm_kpi, breakdown = cogm_for_scope(ds.costs, ds.production, scope)

    if not cogm_kpi.available or baseline_output <= 0:
        st.warning("⚠️ Baseline tidak dapat dihitung. Butuh data produksi & biaya pada filter ini.")
        return

    baseline_cogm = cogm_kpi.value
    material_share = (breakdown.get("Material", 0) / baseline_cogm) if baseline_cogm else 0.6

    # ===== MINI HEALTH SCORE =====
    targets_default = _active_targets()
    try:
        s = summarize(ds, scope)
        score, status, color = compute_health_score(s, targets_default)
        mini_health_score(score, status, color)
    except Exception:
        pass

    # ===== SECTION 1: BASELINE =====
    section_divider(
        title="Baseline (Kondisi Saat Ini)",
        subtitle="Kondisi aktual sebelum simulasi. Acuan untuk perbandingan.",
        icon="📊",
        badge="BASELINE",
        color="#8B5CF6",
        bg1="#F5F3FF",
        bg2="#FFFFFF",
    )

    _, baseline_cogm_val = _render_baseline(prod, cogm_kpi, material_share)

    # ===== SECTION 2: PARAMETER SKENARIO =====
    section_divider(
        title="Parameter Skenario",
        subtitle="Geser slider untuk simulasi perubahan. Hasil update secara real-time.",
        icon="🎚️",
        badge="INPUT",
        color="#3B82F6",
        bg1="#EFF6FF",
        bg2="#FFFFFF",
    )

    scenario = _render_slider_panel()

    result = simulate(
        baseline_output_kg=baseline_output,
        baseline_cogm=baseline_cogm_val,
        material_cost_share=material_share,
        scenario=scenario,
    )

    # ===== SECTION 3: HASIL SIMULASI =====
    section_divider(
        title="Hasil Simulasi",
        subtitle="Dampak skenario terhadap COGM, Cost/Kg, dan potensi cost saving.",
        icon="🎯",
        badge="OUTPUT",
        color="#10B981",
        bg1="#ECFDF5",
        bg2="#FFFFFF",
    )

    _render_result(result, baseline_output, baseline_cogm_val)

    # ===== SAVE SCENARIO =====
    section_divider(
        title="Kelola Skenario",
        subtitle="Simpan, bandingkan, dan kelola skenario simulasi Anda.",
        icon="💾",
        badge="MANAGE",
        color="#EC4899",
        bg1="#FDF2F8",
        bg2="#FFFFFF",
    )

    _render_scenario_save(scenario, result)
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