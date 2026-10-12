"""Inventory Analysis (DARK)."""
import math

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from ..config import targets_from_config
from ..kpi import Scope, inventory_table
from ..pipeline import Dataset
from .charts import COLORS, apply_theme
from .components import (page_header, mini_health_score,
                         format_period_label, compute_health_score,
                         section_divider)


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


GLASS_CSS = """
<style>
.ia-glass {
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
.ia-glass::before {
    content: '';
    position: absolute;
    top: 0; left: 17px;
    width: 35px; height: 3px;
    background: var(--accent, #a489ff);
    border-radius: 0 0 5px 5px;
}
.ia-glass:hover {
    transform: translateY(-2px);
    border-color: #8c79d7;
    box-shadow: 0 10px 24px rgba(8, 8, 33, 0.45);
}
.ia-glass-label {
    color: #b8bedb;
    font-weight: 600;
    font-size: 0.62rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 6px;
}
.ia-glass-value {
    color: #ffffff;
    font-weight: 800;
    font-size: 1.45rem;
    letter-spacing: -0.04em;
    line-height: 1.15;
    margin-bottom: 4px;
}
.ia-glass-note {
    color: #8793bc;
    font-size: 0.68rem;
    line-height: 1.3;
    margin-top: 6px;
}
.ia-glass-delta {
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.03em;
    margin-top: 6px;
    text-transform: uppercase;
}

.ia-banner {
    background: linear-gradient(110deg, #30265e, #211b47 55%, #171b3c);
    border-radius: 16px;
    padding: 22px 26px;
    color: #ffffff;
    box-shadow: 0 9px 30px rgba(6, 9, 23, 0.13);
    border: 1px solid #5e5090;
    margin-bottom: 20px;
    position: relative;
    overflow: hidden;
    display: flex;
    gap: 30px;
    flex-wrap: wrap;
    align-items: center;
}
.ia-banner::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 4px;
    background: linear-gradient(90deg, #77edb4 0%, #f7d578 50%, #ff9eaa 100%);
}
.ia-block { flex: 1; min-width: 160px; }
.ia-block-label {
    font-size: 0.62rem;
    font-weight: 800;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-bottom: 6px;
}
.ia-block-value {
    font-size: 1.6rem;
    font-weight: 800;
    color: #ffffff;
    letter-spacing: -0.04em;
    line-height: 1.15;
    margin-bottom: 4px;
}
.ia-block-sub {
    font-size: 0.75rem;
    color: #adb6d5;
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
    note_html = f'<div class="ia-glass-note">{note}</div>' if note else ""
    delta_html = ""
    if delta:
        c = delta_color or "#77edb4"
        delta_html = f'<div class="ia-glass-delta" style="color:{c};">{delta}</div>'
    html = (
        f'<div class="ia-glass" style="--accent: {accent};">'
        f'<div class="ia-glass-label">{label}</div>'
        f'<div class="ia-glass-value">{value}</div>'
        f'{delta_html}'
        f'{note_html}'
        f'</div>')
    col.markdown(html, unsafe_allow_html=True)


def _render_kpi(inv_tbl, targets):
    st.markdown("#### 📦 Ringkasan Inventory")
    total_kg = float(inv_tbl["Stock_Kg"].sum())
    total_items = len(inv_tbl)
    slow = int((inv_tbl["Status"] == "Slow Moving").sum())
    dead = int((inv_tbl["Status"] == "Dead Stock").sum())

    c1, c2, c3, c4 = st.columns(4, gap="medium")
    _glass_card(c1, "Jenis Material", str(total_items), "#a489ff",
                note="Total SKU terdaftar")
    _glass_card(c2, "Total Stok", f"{_fmt_thousand(total_kg)} Kg", "#71d5e9",
                note="Akumulasi seluruh material")
    _glass_card(c3, "Slow Moving", str(slow), "#f7d578",
                delta=f"> {targets.slow_moving_days} hari",
                delta_color=("#ff9eaa" if slow > 0 else "#77edb4"))
    _glass_card(c4, "Dead Stock", str(dead), "#ff9eaa",
                delta=("Perlu likuidasi" if dead > 0 else "Aman"),
                delta_color=("#ff9eaa" if dead > 0 else "#77edb4"))

    total_value_risk = slow + dead
    if total_value_risk > 0:
        html = (
            f'<div class="ia-banner">'
            f'<div class="ia-block">'
            f'<div class="ia-block-label" style="color:#f7d578;">⚠️ TOTAL PERHATIAN</div>'
            f'<div class="ia-block-value">{total_value_risk}</div>'
            f'<div class="ia-block-sub">Material perlu tindakan</div>'
            f'</div>'
            f'<div class="ia-block">'
            f'<div class="ia-block-label" style="color:#f7d578;">🟡 SLOW MOVING</div>'
            f'<div class="ia-block-value">{slow}</div>'
            f'<div class="ia-block-sub">Perputaran lambat</div>'
            f'</div>'
            f'<div class="ia-block">'
            f'<div class="ia-block-label" style="color:#ff9eaa;">🔴 DEAD STOCK</div>'
            f'<div class="ia-block-value">{dead}</div>'
            f'<div class="ia-block-sub">Perlu likuidasi</div>'
            f'</div>'
            f'</div>')
    else:
        html = (
            f'<div class="ia-banner">'
            f'<div class="ia-block">'
            f'<div class="ia-block-label" style="color:#77edb4;">✅ STATUS INVENTORY</div>'
            f'<div class="ia-block-value">Sehat</div>'
            f'<div class="ia-block-sub">Semua material dalam kondisi optimal</div>'
            f'</div>'
            f'<div class="ia-block">'
            f'<div class="ia-block-label" style="color:#c9b9f8;">📦 TOTAL MATERIAL</div>'
            f'<div class="ia-block-value">{total_items}</div>'
            f'<div class="ia-block-sub">SKU terdaftar</div>'
            f'</div>'
            f'<div class="ia-block">'
            f'<div class="ia-block-label" style="color:#c9b9f8;">⚖️ TOTAL STOK</div>'
            f'<div class="ia-block-value">{_fmt_thousand(total_kg)}</div>'
            f'<div class="ia-block-sub">Kg</div>'
            f'</div>'
            f'</div>')
    st.markdown(html, unsafe_allow_html=True)


def _render_days_chart(inv_tbl, targets):
    st.markdown("#### 📊 Days Inventory per Material")
    st.caption(f"Semakin tinggi = semakin lama menganggur. "
               f"Batas slow-moving: **{targets.slow_moving_days} hari**.")
    df = inv_tbl.copy()
    df = df[df["Days_Inventory"].notna()].sort_values(
        "Days_Inventory", ascending=True).reset_index(drop=True)
    if df.empty:
        st.info("Tidak ada data Days Inventory.")
        return

    color_map = {"Normal": COLORS["success"], "Slow Moving": COLORS["warning"],
                 "Dead Stock": COLORS["danger"]}
    colors = [color_map.get(s, COLORS["text_muted"]) for s in df["Status"]]
    text_labels = [
        (f"<b>{_fmt_thousand(v, 0)} hari</b>" if pd.notna(v) else "<b>∞</b>")
        for v in df["Days_Inventory"]]

    fig = go.Figure(go.Bar(
        x=df["Material"], y=df["Days_Inventory"].clip(upper=120),
        orientation="v",
        marker=dict(color=colors, line=dict(width=0)),
        text=text_labels, textposition="outside",
        textfont=dict(size=11, color=COLORS["text"], family="DM Sans"),
        cliponaxis=False,
        hovertemplate=("<b>%{x}</b><br>"
                       "Stok: %{customdata[0]:,.0f} Kg<br>"
                       "Usage/bulan: %{customdata[1]:,.0f} Kg<br>"
                       "Days Inventory: %{y:.0f} hari<extra></extra>"),
        customdata=df[["Stock_Kg", "Monthly_Usage"]].values))
    fig.add_hline(y=targets.slow_moving_days, line_dash="dash",
                  line_color=COLORS["warning"], line_width=2,
                  annotation_text=f"<b>Slow ({targets.slow_moving_days} hari)</b>",
                  annotation_position="right",
                  annotation_font=dict(size=10, color=COLORS["warning"]))
    fig = apply_theme(fig, height=420)
    fig.update_layout(
        yaxis_title="<b>Days Inventory (hari)</b>",
        xaxis_title="<b>Material</b>",
        xaxis=dict(tickfont=dict(size=11)),
        margin=dict(t=40, b=80, l=60, r=100))
    st.plotly_chart(fig, width='stretch')


def _render_detail_table(inv_tbl):
    st.markdown("#### 📋 Detail Inventory")
    df = inv_tbl.copy()
    display = pd.DataFrame({
        "Material": df["Material"],
        "Stok (Kg)": df["Stock_Kg"].apply(lambda x: _fmt_thousand(x)),
        "Usage/bulan (Kg)": df["Monthly_Usage"].apply(lambda x: _fmt_thousand(x)),
        "Days Inventory": df["Days_Inventory"].apply(
            lambda x: _fmt_thousand(x, 0) if pd.notna(x) else "∞"),
        "Status": df["Status"].map({
            "Normal": "🟢 Normal", "Slow Moving": "🟡 Slow Moving",
            "Dead Stock": "🔴 Dead Stock"})})
    st.dataframe(display, width='stretch', hide_index=True)


def render(ds: Dataset, scope: Scope) -> None:
    _inject_css()
    page_header(
        title="Inventory Analysis",
        subtitle=(f"Sumber: {ds.report.source_label} · "
                  f"Analisis perputaran stok, deteksi slow-moving & dead stock"),
        granularity="Snapshot",
        period_label=format_period_label(scope),
        icon="📦")

    inv = ds.inventory
    if inv is None or inv.empty:
        st.warning("Data Inventory tidak tersedia (sheet 'Inventory').")
        st.info("Sesuai BRD 5.5: tidak ada data pengganti yang ditampilkan.")
        return
    if not {"Material", "Stock_Kg", "Monthly_Usage"} <= set(inv.columns):
        st.error("Sheet Inventory harus punya kolom: Material, Stock_Kg, Monthly_Usage.")
        return

    targets_default = _active_targets()
    try:
        from ..kpi import summarize
        s = summarize(ds, scope)
        score, status, color = compute_health_score(s, targets_default)
        mini_health_score(score, status, color)
    except Exception:
        pass

    st.markdown("""
    <div style="background: #242748;
        border-left: 4px solid #71d5e9;border-radius: 10px;padding: 14px 18px;
        margin: 12px 0 20px 0;display: flex;gap: 12px;align-items: start;">
        <div style="font-size: 1.2rem;flex-shrink:0;">ℹ️</div>
        <div style="font-size: 0.82rem;color: #dce0f4;line-height: 1.55;">
        <strong style="color:#71d5e9;">Status Saat Ini:</strong>
        Halaman ini menampilkan <strong>posisi stok saat ini</strong> (snapshot).
        Untuk tren perubahan stok dari waktu ke waktu, tambahkan kolom
        <code style="background:#1a1d3d;color:#a489ff;padding:2px 6px;
        border-radius:4px;font-family:monospace;">Period</code> di sheet Inventory.
        </div>
        </div>
    """, unsafe_allow_html=True)

    targets = targets_from_config(ds.config)
    tbl = inventory_table(inv)
    _render_kpi(tbl, targets)
    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)
    _render_days_chart(tbl, targets)
    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)
    _render_detail_table(tbl)

    st.markdown("---")
    st.markdown("### 💡 Insight & Action Plan")
    slow_materials = tbl[tbl["Status"] == "Slow Moving"]["Material"].tolist()
    dead_materials = tbl[tbl["Status"] == "Dead Stock"]["Material"].tolist()
    c1, c2 = st.columns(2, gap="medium")
    with c1:
        if slow_materials:
            st.warning(f"⚠️ **Slow Moving:** {', '.join(slow_materials)}\n\n"
                       f"**Aksi:** Kurangi pemesanan atau cari buyer alternatif.")
        else:
            st.success("✅ Tidak ada material slow-moving.")
    with c2:
        if dead_materials:
            st.error(f"🔴 **Dead Stock:** {', '.join(dead_materials)}\n\n"
                     f"**Aksi:** Likuidasi atau alokasikan ke line lain.")
        else:
            st.success("✅ Tidak ada dead stock.")