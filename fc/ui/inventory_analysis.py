"""Inventory Analysis - data-driven (BRD 6)."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from ..config import targets_from_config
from ..kpi import Scope, inventory_table
from ..pipeline import Dataset
from .charts import COLORS, apply_theme


def _render_kpi(inv_tbl, targets):
    """4 KPI cards untuk Inventory."""
    st.markdown("### 📦 Ringkasan Inventory")

    total_kg = float(inv_tbl["Stock_Kg"].sum())
    total_items = len(inv_tbl)
    slow = int((inv_tbl["Status"] == "Slow Moving").sum())
    dead = int((inv_tbl["Status"] == "Dead Stock").sum())

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Jenis Material", f"{total_items}")
    c2.metric("Total Stok", f"{total_kg:,.0f} Kg")
    c3.metric("Slow Moving", f"{slow}",
              delta=f"> {targets.slow_moving_days} hari",
              delta_color="off" if slow == 0 else "inverse")
    c4.metric("Dead Stock", f"{dead}",
              delta="Perlu likuidasi" if dead > 0 else "Aman",
              delta_color="off" if dead == 0 else "inverse")


def _render_days_chart(inv_tbl, targets):
    """Bar chart Days Inventory per material."""
    st.markdown("### 📊 Days Inventory per Material")
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

    # Warna by status
    color_map = {
        "Normal": COLORS["success"],
        "Slow Moving": COLORS["warning"],
        "Dead Stock": COLORS["danger"],
    }
    colors = [color_map.get(s, COLORS["text_muted"]) for s in df["Status"]]

    # Text label
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

    # Garis threshold
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


def _render_detail_table(inv_tbl):
    """Tabel detail dengan warna status."""
    st.markdown("### 📋 Detail Inventory")

    df = inv_tbl.copy()

    # Format
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


def render(ds: Dataset, scope: Scope) -> None:
    st.title("📦 Inventory Analysis")
    st.caption("Analisis perputaran stok, deteksi slow-moving, dan dead stock.")

    inv = ds.inventory
    if inv is None or inv.empty:
        st.warning("Data Inventory tidak tersedia (sheet 'Inventory').")
        st.info("Sesuai BRD 5.5: tidak ada data pengganti yang ditampilkan.")
        return

    if not {"Material", "Stock_Kg", "Monthly_Usage"} <= set(inv.columns):
        st.error("Sheet Inventory harus punya kolom: Material, Stock_Kg, Monthly_Usage.")
        return

    targets = targets_from_config(ds.config)
    tbl = inventory_table(inv)

    # 1. KPI cards
    _render_kpi(tbl, targets)

    st.markdown("---")

    # 2. Days Inventory chart
    _render_days_chart(tbl, targets)

    st.markdown("---")

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