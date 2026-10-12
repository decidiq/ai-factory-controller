"""Halaman What-If Simulator (DARK)."""
import math

import pandas as pd
import streamlit as st

from ..intel.what_if import Scenario, simulate
from ..kpi import Scope, cogm_for_scope, scope_production, summarize
from ..pipeline import Dataset
from .components import (page_header, mini_health_score,
                         format_period_label, compute_health_score,
                         section_divider, render_table)


def _fmt_thousand(v, decimals: int = 0) -> str:
    try:
        if v is None: return "—"
        f = float(v)
        if math.isnan(f) or math.isinf(f): return "—"
        if decimals > 0:
            return f"{f:,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return f"{f:,.0f}".replace(",", ".")
    except (ValueError, TypeError):
        return str(v) if v is not None else "—"


def _fmt_pct(v, decimals: int = 2) -> str:
    try:
        if v is None: return "—"
        f = float(v)
        if math.isnan(f) or math.isinf(f): return "—"
        return f"{f:.{decimals}f}".replace(".", ",") + "%"
    except (ValueError, TypeError):
        return str(v) if v is not None else "—"


def _fmt_rp(v, compact: bool = False) -> str:
    try:
        if v is None: return "—"
        f = float(v)
        if math.isnan(f) or math.isinf(f): return "—"
        if compact:
            if abs(f) >= 1_000_000_000:
                return "Rp " + f"{f/1_000_000_000:.2f}".replace(".", ",") + " M"
            if abs(f) >= 1_000_000:
                return "Rp " + f"{f/1_000_000:.1f}".replace(".", ",") + " jt"
        return "Rp " + f"{f:,.0f}".replace(",", ".")
    except (ValueError, TypeError):
        return str(v) if v is not None else "—"


GLASS_CSS = """
<style>
.wi-glass {
    position: relative;
    background: linear-gradient(145deg, #1a1d3d, #151933);
    border: 1px solid #343858;
    border-radius: 12px;
    padding: 16px 18px;
    box-shadow: 0 9px 30px rgba(6, 9, 23, 0.13);
    transition: transform 0.2s ease, border-color 0.2s ease;
    overflow: hidden;
    min-height: 110px;
    margin-bottom: 8px;
}
.wi-glass::before {
    content: '';
    position: absolute;
    top: 0; left: 17px;
    width: 35px; height: 3px;
    background: var(--accent, #a489ff);
    border-radius: 0 0 5px 5px;
}
.wi-glass:hover {
    transform: translateY(-2px);
    border-color: #8c79d7;
    box-shadow: 0 10px 24px rgba(8, 8, 33, 0.45);
}
.wi-glass-label {
    color: #b8bedb;
    font-weight: 600;
    font-size: 0.62rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 6px;
}
.wi-glass-value {
    color: #ffffff;
    font-weight: 800;
    font-size: 1.4rem;
    letter-spacing: -0.04em;
    line-height: 1.15;
    margin-bottom: 4px;
}
.wi-glass-note {
    color: #8793bc;
    font-size: 0.68rem;
    line-height: 1.3;
    margin-top: 6px;
}
.wi-glass-delta {
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.03em;
    margin-top: 6px;
}
</style>
"""


def _inject_css():
    st.markdown(GLASS_CSS, unsafe_allow_html=True)


def _active_targets():
    from ..config import TARGETS as DEFAULT_TARGETS
    return st.session_state.get("_targets") or DEFAULT_TARGETS


def _glass_card(col, label: str, value: str, accent: str = "#a489ff",
                note: str = None, delta: str = None,
                delta_color: str = None) -> None:
    note_html = f'<div class="wi-glass-note">{note}</div>' if note else ""
    delta_html = ""
    if delta:
        c = delta_color or "#77edb4"
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


def _render_baseline(prod, cogm_kpi, material_share):
    baseline_output = float(prod["Output_Kg"].sum()) if len(prod) else 0.0
    baseline_cogm = cogm_kpi.value if cogm_kpi.available else 0

    c1, c2, c3 = st.columns(3, gap="medium")
    _glass_card(c1, "Output Saat Ini", f"{_fmt_thousand(baseline_output)} Kg",
                "#a489ff", note="Total output terfilter")
    _glass_card(c2, "COGM Saat Ini", _fmt_rp(baseline_cogm),
                "#ec3f92", note=f"Rp {_fmt_thousand(baseline_cogm)}")
    _glass_card(c3, "Material Share", _fmt_pct(material_share * 100, 0),
                "#f7d578", note="Porsi biaya material dari COGM")
    return baseline_output, baseline_cogm


def _render_slider_panel():
    st.caption("Atur nilai untuk simulasi. Hasil berubah secara real-time.")
    c1, c2 = st.columns(2, gap="medium")
    with c1:
        yield_pct = st.slider("📈 Yield (%)", 90.0, 100.0, 97.5, 0.1)
        scrap_pct = st.slider("🗑️ Scrap (%)", 0.0, 10.0, 2.2, 0.1)
    with c2:
        resin_price = st.slider("💰 Perubahan Harga Material (%)", -20, 30, 0, 1)
        volume_pct = st.slider("📦 Perubahan Volume Produksi (%)", -30, 50, 0, 1)
    return Scenario(yield_pct=yield_pct, scrap_pct=scrap_pct,
                    resin_price_pct=resin_price, volume_pct=volume_pct)


def _render_result(result, baseline_output, baseline_cogm):
    savings = result.savings_annual
    if savings > 0:
        impact_icon = "💚"
        impact_label = "COST SAVING TAHUNAN"
        impact_bg = "linear-gradient(135deg, #172d35 0%, #1f4a44 100%)"
    elif savings < 0:
        impact_icon = "⚠️"
        impact_label = "KENAIKAN BIAYA TAHUNAN"
        impact_bg = "linear-gradient(135deg, #35243a 0%, #4a2d3a 100%)"
    else:
        impact_icon = "➖"
        impact_label = "TIDAK ADA PERUBAHAN SIGNIFIKAN"
        impact_bg = "linear-gradient(135deg, #242748 0%, #1a1d3d 100%)"
    impact_val = _fmt_rp(abs(savings)) if savings != 0 else "Rp 0"

    st.markdown(f"""
    <div style="
        background: {impact_bg};
        color: #FFFFFF;
        padding: 26px 30px;
        border-radius: 16px;
        box-shadow: 0 9px 30px rgba(6, 9, 23, 0.13);
        border: 1px solid #5e5090;
        margin-bottom: 24px;
        position: relative;
        overflow: hidden;
    ">
        <div style="font-size: 0.62rem; letter-spacing: 0.12em; opacity: 0.9;
            font-weight: 800; margin-bottom: 8px; text-transform: uppercase;">
            {impact_icon} {impact_label}</div>
        <div style="font-size: 2.4rem; font-weight: 800; letter-spacing: -0.04em;
            line-height: 1.1;">{impact_val}</div>
        <div style="font-size: 0.82rem; opacity: 0.9; margin-top: 8px;">
            Asumsi: 12 bulan dengan output yang sama.</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("#### 📊 Perbandingan Detail")
    c1, c2, c3 = st.columns(3, gap="medium")
    delta_output = result.output_kg - baseline_output
    delta_cogm = result.cogm - baseline_cogm
    delta_cpk = result.cost_per_kg - result.baseline_cost_per_kg

    _glass_card(c1, "Output Baru", f"{_fmt_thousand(result.output_kg)} Kg", "#a489ff",
                delta=f"{_fmt_thousand(delta_output, 0)} Kg",
                delta_color=("#77edb4" if delta_output >= 0 else "#ff9eaa"))
    _glass_card(c2, "COGM Baru", _fmt_rp(result.cogm), "#ec3f92",
                delta=f"{_fmt_rp(delta_cogm)}",
                delta_color=("#ff9eaa" if delta_cogm > 0 else "#77edb4"))
    _glass_card(c3, "Cost/Kg Baru", _fmt_rp(result.cost_per_kg), "#f7d578",
                delta=f"{_fmt_rp(delta_cpk)}",
                delta_color=("#ff9eaa" if delta_cpk > 0 else "#77edb4"))

    c4, c5, c6 = st.columns(3, gap="medium")
    _glass_card(c4, "Baseline Cost/Kg",
                _fmt_rp(result.baseline_cost_per_kg), "#adb6d5",
                note="Kondisi saat ini")
    _glass_card(c5, "Δ Cost/Kg", _fmt_rp(delta_cpk),
                "#ff9eaa" if delta_cpk > 0 else "#77edb4",
                note="Perubahan per Kg")
    pct_out = (delta_output / baseline_output * 100) if baseline_output > 0 else 0
    _glass_card(c6, "Δ Output", f"{_fmt_thousand(delta_output, 0)} Kg",
                "#71d5e9", note=f"{_fmt_pct(pct_out, 1)} dari baseline")

    st.markdown("#### 📊 Baseline vs Simulasi")
    from .charts import comparison_bar
    fig = comparison_bar(
        labels=["Output (Kg)", "COGM (Rp)", "Cost/Kg (Rp)"],
        baseline=[baseline_output, baseline_cogm, result.baseline_cost_per_kg],
        simulasi=[result.output_kg, result.cogm, result.cost_per_kg],
        height=340)
    st.plotly_chart(fig, width='stretch')


def _render_scenario_save(current_scenario, result):
    st.markdown("### 💾 Simpan Skenario")
    st.caption("Simpan kombinasi parameter untuk dibandingkan nanti.")
    c1, c2 = st.columns([3, 1], gap="medium")
    with c1:
        name = st.text_input("Nama Skenario",
                             placeholder="mis. Optimis Q4 — Yield 99% + Scrap 1.5%",
                             label_visibility="collapsed")
    with c2:
        save_btn = st.button("💾 Simpan", type="primary", width='stretch')

    if save_btn and name:
        st.session_state.setdefault("what_if_scenarios", []).append({
            "name": name, "yield": current_scenario.yield_pct,
            "scrap": current_scenario.scrap_pct, "resin": current_scenario.resin_price_pct,
            "volume": current_scenario.volume_pct, "cogm": result.cogm,
            "cost_kg": result.cost_per_kg, "savings": result.savings_annual})
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
        lambda x: f"{_fmt_rp(x)}" if x != 0 else "—")
    display_df["COGM"] = display_df["cogm"].apply(_fmt_rp)
    display_df["Cost/Kg"] = display_df["cost_kg"].apply(_fmt_rp)
    display_cols = ["name", "yield", "scrap", "resin", "volume",
                    "cogm", "cost_kg", "Cost Saving"]
    rename_map = {"name": "Nama", "yield": "Yield (%)", "scrap": "Scrap (%)",
                  "resin": "Δ Harga (%)", "volume": "Δ Volume (%)",
                  "cogm": "COGM", "cost_kg": "Cost/Kg"}
    render_table(display_df[display_cols].rename(columns=rename_map),
                 max_height="300px")
    c1, c2 = st.columns([1, 4], gap="medium")
    with c1:
        if st.button("🗑 Hapus Semua", width='stretch'):
            st.session_state["what_if_scenarios"] = []
            st.rerun()
    with c2:
        st.caption(f"Total {len(scenarios)} skenario tersimpan di sesi ini.")


def render(ds: Dataset, scope: Scope) -> None:
    _inject_css()
    page_header(
        title="What-If Simulator",
        subtitle=(f"Sumber: {ds.report.source_label} · "
                  f"Simulasikan skenario bisnis & lihat dampaknya secara real-time"),
        granularity="Multi",
        period_label=format_period_label(scope),
        icon="🎯")

    prod = scope_production(ds.production, scope)
    baseline_output = float(prod["Output_Kg"].sum()) if len(prod) else 0.0
    cogm_kpi, breakdown = cogm_for_scope(ds.costs, ds.production, scope)
    if not cogm_kpi.available or baseline_output <= 0:
        st.warning("⚠️ Baseline tidak dapat dihitung.")
        return
    baseline_cogm = cogm_kpi.value
    material_share = (breakdown.get("Material", 0) / baseline_cogm) if baseline_cogm else 0.6

    targets_default = _active_targets()
    try:
        s = summarize(ds, scope)
        score, status, color = compute_health_score(s, targets_default)
        mini_health_score(score, status, color)
    except Exception:
        pass

    section_divider(title="Baseline (Kondisi Saat Ini)",
                    subtitle="Kondisi aktual sebelum simulasi. Acuan untuk perbandingan.",
                    icon="📊", badge="BASELINE", color="#a489ff",
                    bg1="#242748", bg2="#1a1d3d")
    _, baseline_cogm_val = _render_baseline(prod, cogm_kpi, material_share)

    section_divider(title="Parameter Skenario",
                    subtitle="Geser slider untuk simulasi perubahan. Hasil update secara real-time.",
                    icon="🎚️", badge="INPUT", color="#71d5e9",
                    bg1="#242748", bg2="#1a1d3d")
    scenario = _render_slider_panel()
    result = simulate(baseline_output_kg=baseline_output,
                       baseline_cogm=baseline_cogm_val,
                       material_cost_share=material_share,
                       scenario=scenario)

    section_divider(title="Hasil Simulasi",
                    subtitle="Dampak skenario terhadap COGM, Cost/Kg, dan potensi cost saving.",
                    icon="🎯", badge="OUTPUT", color="#77edb4",
                    bg1="#242748", bg2="#1a1d3d")
    _render_result(result, baseline_output, baseline_cogm_val)

    section_divider(title="Kelola Skenario",
                    subtitle="Simpan, bandingkan, dan kelola skenario simulasi Anda.",
                    icon="💾", badge="MANAGE", color="#ec3f92",
                    bg1="#242748", bg2="#1a1d3d")
    _render_scenario_save(scenario, result)
    _render_saved_scenarios()

    st.markdown("---")
    with st.expander("ℹ️ Cara kerja What-If Simulator"):
        st.markdown(
            "**Model simulasi:**\n"
            "- **Yield effect** — yield naik X% → COGM turun ~X%\n"
            "- **Volume effect** — volume naik → fixed cost ter-dilusi\n"
            "- **Price effect** — harga material naik X% → COGM naik X × material_share\n\n"
            "**Cost saving tahunan** = (Cost/Kg baseline − Cost/Kg baru) × Output baru × 12.")