"""Inventory Analysis - data-driven (BRD 6) — Premium UI."""
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


# ==================== CSS GLASSMORPHISM ====================
GLASS_CSS = """
<style>
.ia-glass {
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
.ia-glass::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, var(--accent, #8B5CF6) 0%, #EC4899 100%);
}
.ia-glass:hover {
    transform: translateY(-3px);
    box-shadow: 0 16px 32px rgba(139, 92, 246, 0.18);
    border-color: rgba(139, 92, 246, 0.6);
}
.ia-glass-label {
    color: #6D28D9;
    font-weight: 700;
    font-size: 0.66rem;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    margin-bottom: 6px;
}
.ia-glass-value {
    color: #0F172A;
    font-weight: 800;
    font-size: 1.45rem;
    letter-spacing: -0.5px;
    line-height: 1.1;
    margin-bottom: 4px;
}
.ia-glass-note {
    color: #94A3B8;
    font-size: 0.68rem;
    font-style: italic;
    line-height: 1.3;
}
.ia-glass-delta {
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.3px;
}

.ia-banner {
    background: linear-gradient(135deg, #0F172A 0%, #1E1B4B 100%);
    border-radius: 16px;
    padding: 20px 26px;
    color: white;
    box-shadow: 0 12px 32px rgba(30, 27, 75, 0.25);
    border: 1px solid rgba(139, 92, 246, 0.3);
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
    background: linear-gradient(90deg, #10B981 0%, #F59E0B 50%, #EF4444 100%);
}
.ia-block { flex: 1; min-width: 160px; }
.ia-block-label {
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    margin-bottom: 6px;
}
.ia-block-value {
    font-size: 1.8rem;
    font-weight: 900;
    color: #FFFFFF;
    letter-spacing: -1px;
    line-height: 1.1;
    margin-bottom: 2px;
}
.ia-block-sub {
    font-size: 0.75rem;
    color: #94A3B8;
}
</style>
"""


def _inject_css():
    st.markdown(GLASS_CSS, unsafe_allow_html=True)


def _active_targets():
    from ..config import TARGETS as DEFAULT_TARGETS
    return st.session_state.get("_targets") or DEFAULT_TARGETS


# ==================== HELPERS ====================
def _glass_card(col, label: str, value: str, accent: str = "#8B5CF6",
                note: str = None, delta: str = None,
                delta_color: str = None) -> None:
    note_html = f'<div class="ia-glass-note">{note}</div>' if note else ""
    delta_html = ""
    if delta:
        c = delta_color or "#10B981"
        delta_html = f'<div class="ia-glass-delta" style="color:{c};">{delta}</div>'
    html = (
        f'<div class="ia-glass" style="--accent: {accent};">'
        f'<div class="ia-glass-label">{label}</div>'
        f'<div class="ia-glass-value">{value}</div>'
        f'{delta_html}'
        f'{note_html}'
        f'</div>'
    )
    col.markdown(html, unsafe_allow_html=True)


# ==================== KPI CARDS ====================
def _render_kpi(inv_tbl, targets):
    st.markdown("#### 📦 Ringkasan Inventory")

    total_kg = float(inv_tbl["Stock_Kg"].sum())
    total_items = len(inv_tbl)
    slow = int((inv_tbl["Status"] == "Slow Moving").sum())
    dead = int((inv_tbl["Status"] == "Dead Stock").sum())

    c1, c2, c3, c4 = st.columns(4)
    _glass_card(c1, "Jenis Material", str(total_items), "#8B5CF6",
                note="Total SKU terdaftar")
    _glass_card(c2, "Total Stok", f"{total_kg:,.0f} Kg", "#3B82F6",
                note="Akumulasi seluruh material")
    _glass_card(c3, "Slow Moving", str(slow), "#F59E0B",
                delta=f"> {targets.slow_moving_days} hari",
                delta_color=("#EF4444" if slow > 0 else "#10B981"))
    _glass_card(c4, "Dead Stock", str(dead), "#EF4444",
                delta=("Perlu likuidasi" if dead > 0 else "Aman"),
                delta_color=("#EF4444" if dead > 0 else "#10B981"))

    total_value_risk = slow + dead
    if total_value_risk > 0:
        html = (
            f'<div class="ia-banner">'
            f'<div class="ia-block">'
            f'<div class="ia-block-label" style="color:#FBBF24;">⚠️ TOTAL PERHATIAN</div>'
            f'<div class="ia-block-value">{total_value_risk}</div>'
            f'<div class="ia-block-sub">Material perlu tindakan</div>'
            f'</div>'
            f'<div class="ia-block">'
            f'<div class="ia-block-label" style="color:#FBBF24;">🟡 SLOW MOVING</div>'
            f'<div class="ia-block-value">{slow}</div>'
            f'<div class="ia-block-sub">Perputaran lambat</div>'
            f'</div>'
            f'<div class="ia-block">'
            f'<div class="ia-block-label" style="color:#F87171;">🔴 DEAD STOCK</div>'
            f'<div class="ia-block-value">{dead}</div>'
            f'<div class="ia-block-sub">Perlu likuidasi</div>'
            f'</div>'
            f'</div>'
        )
    else:
        html = (
            f'<div class="ia-banner">'
            f'<div class="ia-block">'
            f'<div class="ia-block-label" style="color:#34D399;">✅ STATUS INVENTORY</div>'
            f'<div class="ia-block-value">Sehat</div>'
            f'<div class="ia-block-sub">Semua material dalam kondisi optimal</div>'
            f'</div>'
            f'<div class="ia-block">'
            f'<div class="ia-block-label" style="color:#A78BFA;">📦 TOTAL MATERIAL</div>'
            f'<div class="ia-block-value">{total_items}</div>'
            f'<div class="ia-block-sub">SKU terdaftar</div>'
            f'</div>'
            f'<div class="ia-block">'
            f'<div class="ia-block-label" style="color:#A78BFA;">⚖️ TOTAL STOK</div>'
            f'<div class="ia-block-value">{total_kg:,.0f}</div>'
            f'<div class="ia-block-sub">Kg</div>'
            f'</div>'
            f'</div>'
        )
    st.markdown(html, unsafe_allow_html=True)


# ==================== DAYS CHART ====================
def _render_days_chart(inv_tbl, targets):
    st.markdown("#### 📊 Days Inventory per Material")
    st.caption(
        f"Semakin tinggi = semakin lama menganggur. "
        f"Batas slow-moving: **{targets.slow_moving_days} hari**."
    )

    df = inv_tbl.copy()
    df = df[df["Days_Inventory"].notna()].sort_values(
        "Days_Inventory", ascending=True
    ).reset_index(drop=True)

    if df.empty:
        st.info("Tidak ada data Days Inventory.")
        return

    color_map = {
        "Normal": COLORS["success"],
        "Slow Moving": COLORS["warning"],
        "Dead Stock": COLORS["danger"],
    }
    colors = [color_map.get(s, COLORS["text_muted"]) for s in df["Status"]]

    text_labels = [
        (f"<b>{v:.0f} hari</b>" if pd.notna(v) else "<b>∞</b>")
        for v in df["Days_Inventory"]
    ]

    fig = go.Figure(go.Bar(
        x=df["Material"],
        y=df["Days_Inventory"].clip(upper=120),
        orientation="v",
        marker=dict(color=colors, line=dict(width=0)),
        text=text_labels,
        textposition="outside",
        textfont=dict(size=11, color=COLORS["text"], family="Inter"),
        cliponaxis=False,
        hovertemplate=(
            "<b>%{x}</b><br>"
            "Stok: %{customdata[0]:,.0f} Kg<br>"
            "Usage/bulan: %{customdata[1]:,.0f} Kg<br>"
            "Days Inventory: %{y:.0f} hari<extra></extra>"
        ),
        customdata=df[["Stock_Kg", "Monthly_Usage"]].values,
    ))

    fig.add_hline(
        y=targets.slow_moving_days,
        line_dash="dash", line_color=COLORS["warning"], line_width=2,
        annotation_text=f"<b>Slow ({targets.slow_moving_days} hari)</b>",
        annotation_position="right",
        annotation_font=dict(size=10, color=COLORS["warning"]),
    )

    fig = apply_theme(fig, height=420)
    fig.update_layout(
        yaxis_title="<b>Days Inventory (hari)</b>",
        xaxis_title="<b>Material</b>",
        xaxis=dict(tickfont=dict(size=11)),
        margin=dict(t=40, b=80, l=60, r=100),
    )
    st.plotly_chart(fig, use_container_width=True)


# ==================== DETAIL TABLE ====================
def _render_detail_table(inv_tbl):
    st.markdown("#### 📋 Detail Inventory")

    df = inv_tbl.copy()

    display = pd.DataFrame({
        "Material": df["Material"],
        "Stok (Kg)": df["Stock_Kg"].apply(lambda x: f"{x:,.0f}"),
        "Usage/bulan (Kg)": df["Monthly_Usage"].apply(lambda x: f"{x:,.0f}"),
        "Days Inventory": df["Days_Inventory"].apply(
            lambda x: f"{x:.0f}" if pd.notna(x) else "∞"
        ),
        "Status": df["Status"].map({
            "Normal": "🟢 Normal",
            "Slow Moving": "🟡 Slow Moving",
            "Dead Stock": "🔴 Dead Stock",
        }),
    })

    st.dataframe(display, use_container_width=True, hide_index=True)


# ==================== MAIN ====================
def render(ds: Dataset, scope: Scope) -> None:
    _inject_css()

    # ===== HEADER KONSISTEN =====
    page_header(
        title="Inventory Analysis",
        subtitle=(
            f"Sumber: {ds.report.source_label} · "
            f"Analisis perputaran stok, deteksi slow-moving & dead stock"
        ),
        granularity="Snapshot",
        period_label=format_period_label(scope),
        icon="📦",
    )

    inv = ds.inventory
    if inv is None or inv.empty:
        st.warning("Data Inventory tidak tersedia (sheet 'Inventory').")
        st.info("Sesuai BRD 5.5: tidak ada data pengganti yang ditampilkan.")
        return

    if not {"Material", "Stock_Kg", "Monthly_Usage"} <= set(inv.columns):
        st.error("Sheet Inventory harus punya kolom: Material, Stock_Kg, Monthly_Usage.")
        return

    # ===== MINI HEALTH SCORE =====
    targets_default = _active_targets()
    try:
        from ..kpi import summarize
        s = summarize(ds, scope)
        score, status, color = compute_health_score(s, targets_default)
        mini_health_score(score, status, color)
    except Exception:
        pass

    # ===== INFO BOX (STANDAR INVENTORY SNAPSHOT) =====
    st.markdown("""
    <div style="background: linear-gradient(135deg, #EFF6FF 0%, #F0F9FF 100%);
        border-left: 4px solid #3B82F6;border-radius: 10px;padding: 12px 18px;
        margin: 12px 0 20px 0;display: flex;gap: 12px;align-items: start;">
        <div style="font-size: 1.2rem;flex-shrink:0;">ℹ️</div>
        <div style="font-size: 0.85rem;color: #1E3A8A;line-height: 1.5;">
        <strong style="color:#1E40AF;">Status Saat Ini:</strong>
        Halaman ini menampilkan <strong>posisi stok saat ini</strong> (snapshot).
        Untuk melihat tren perubahan stok dari waktu ke waktu, tambahkan kolom
        <code>Period</code> di sheet Inventory.
        </div>
        </div>
    """, unsafe_allow_html=True)

    targets = targets_from_config(ds.config)
    tbl = inventory_table(inv)

    # 1. KPI cards + Banner
    _render_kpi(tbl, targets)

    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

    # 2. Days Inventory chart
    _render_days_chart(tbl, targets)

    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

    # 3. Detail table
    _render_detail_table(tbl)

    # 4. Insights
    st.markdown("---")
    st.markdown("### 💡 Insight & Action Plan")

    slow_materials = tbl[tbl["Status"] == "Slow Moving"]["Material"].tolist()
    dead_materials = tbl[tbl["Status"] == "Dead Stock"]["Material"].tolist()

    c1, c2 = st.columns(2)

    with c1:
        if slow_materials:
            st.warning(
                f"⚠️ **Slow Moving:** {', '.join(slow_materials)}\n\n"
                f"**Aksi:** Kurangi pemesanan atau cari buyer alternatif."
            )
        else:
            st.success("✅ Tidak ada material slow-moving.")

    with c2:
        if dead_materials:
            st.error(
                f"🔴 **Dead Stock:** {', '.join(dead_materials)}\n\n"
                f"**Aksi:** Likuidasi atau alokasikan ke line lain."
            )
        else:
            st.success("✅ Tidak ada dead stock.")