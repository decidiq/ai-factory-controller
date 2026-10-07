"""Multi-Plant & Cost Allocation - data-driven (BRD 6)."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from ..kpi import Scope, scope_production
from ..pipeline import Dataset
from .charts import CATEGORY_COLORS, COLORS, apply_theme


def _render_kpi(agg):
    """KPI cards ringkasan multi-plant."""
    st.markdown("### 🏭 Ringkasan Multi-Plant")

    total_plants = len(agg)
    total_output = agg["Output_Kg"].sum()
    total_cost = agg["Cost"].sum() if agg["Cost"].notna().any() else 0
    avg_cost_kg = (total_cost / total_output) if total_output > 0 else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Jumlah Plant", f"{total_plants}")
    c2.metric("Total Output", f"{total_output:,.0f} Kg")

    if total_cost > 0:
        c3.metric("Total Cost", f"Rp {total_cost/1_000_000_000:.2f} M",
                  help=f"Rp {total_cost:,.0f}")
        c4.metric("Avg Cost/Kg", f"Rp {avg_cost_kg:,.0f}")
    else:
        c3.metric("Total Cost", "—",
                  help="Dimensi biaya per Plant belum tersedia")
        c4.metric("Avg Cost/Kg", "—")


def _render_output_comparison(agg):
    """Bar chart perbandingan output antar plant."""
    st.markdown("### 📊 Perbandingan Output per Plant")
    st.caption("Total output produksi setiap plant pada periode terpilih.")

    # Sort by output
    df = agg.sort_values("Output_Kg", ascending=False).reset_index(drop=True)

    fig = go.Figure(go.Bar(
        x=df["Plant"],
        y=df["Output_Kg"],
        marker=dict(color=COLORS["primary"], line=dict(width=0)),
        text=[f"<b>{v:,.0f} Kg</b>" for v in df["Output_Kg"]],
        textposition="outside",
        textfont=dict(size=12, color=COLORS["text"], family="Inter"),
        cliponaxis=False,
        hovertemplate="<b>%{x}</b><br>Output: %{y:,.0f} Kg<extra></extra>",
    ))

    # AVG line
    avg = df["Output_Kg"].mean()
    fig.add_hline(
        y=avg, line_dash="dash", line_color=COLORS["accent"], line_width=2,
        annotation_text=f"<b>AVG {avg:,.0f} Kg</b>",
        annotation_position="right",
        annotation_font=dict(size=11, color=COLORS["accent_dark"]),
    )

    fig = apply_theme(fig, height=400)
    fig.update_layout(
        showlegend=False,
        yaxis=dict(
            title="<b>Output (Kg)</b>",
            tickformat=",.0f",
        ),
        xaxis=dict(
            title="<b>Plant</b>",
            tickfont=dict(size=12),
        ),
        margin=dict(t=60, b=60, l=80, r=100),
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_share_pie(agg):
    """Pie chart share of output."""
    st.markdown("### 🥧 Share of Output")
    st.caption("Porsi output setiap plant terhadap total produksi.")

    df = agg.sort_values("Output_Kg", ascending=False).reset_index(drop=True)

    fig = go.Figure(go.Pie(
        labels=df["Plant"],
        values=df["Output_Kg"],
        hole=0.55,
        marker=dict(
            colors=CATEGORY_COLORS[:len(df)],
            line=dict(color="#FFFFFF", width=3),
        ),
        textinfo="label+percent",
        textposition="inside",
        textfont=dict(size=11, color="#FFFFFF", family="Inter"),
        hovertemplate="<b>%{label}</b><br>%{value:,.0f} Kg<br>%{percent}<extra></extra>",
    ))

    total = df["Output_Kg"].sum()
    fig.add_annotation(
        text=f"<b>{total/1000:,.1f} ton</b><br><span style='font-size:10px;color:#94A3B8'>TOTAL</span>",
        x=0.5, y=0.5, showarrow=False,
        font=dict(size=16, color=COLORS["text"], family="Inter"),
    )

    fig = apply_theme(fig, height=380)
    fig.update_layout(
        showlegend=True,
        legend=dict(
            orientation="v", yanchor="middle", y=0.5,
            xanchor="left", x=1.02,
            font=dict(size=11, color=COLORS["text_axis"]),
        ),
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_cost_comparison(agg):
    """Bar chart Cost/Kg per plant (kalau data biaya tersedia)."""
    if not agg["Cost_Kg"].notna().any():
        return

    st.markdown("### 💰 Cost/Kg per Plant")
    st.caption("Plant mana yang paling efisien dari sisi biaya per kilogram?")

    df = agg[agg["Cost_Kg"].notna()].sort_values("Cost_Kg", ascending=True).reset_index(drop=True)

    if df.empty:
        return

    # Warna: terendah hijau, tertinggi merah
    min_cost = df["Cost_Kg"].min()
    max_cost = df["Cost_Kg"].max()

    colors = []
    for v in df["Cost_Kg"]:
        if v == min_cost:
            colors.append(COLORS["success"])
        elif v == max_cost:
            colors.append(COLORS["danger"])
        else:
            colors.append(COLORS["warning"])

    fig = go.Figure(go.Bar(
        x=df["Cost_Kg"],
        y=df["Plant"],
        orientation="h",
        marker=dict(color=colors, line=dict(width=0)),
        text=[f"<b>Rp {v:,.0f}/Kg</b>" for v in df["Cost_Kg"]],
        textposition="outside",
        textfont=dict(size=11, color=COLORS["text"], family="Inter"),
        cliponaxis=False,
        hovertemplate="<b>%{y}</b><br>Cost/Kg: Rp %{x:,.0f}<extra></extra>",
    ))

    fig = apply_theme(fig, height=300)
    fig.update_layout(
        showlegend=False,
        xaxis=dict(title="<b>Cost/Kg (Rp)</b>", tickformat=",.0f"),
        yaxis=dict(title="", tickfont=dict(size=12)),
        margin=dict(t=40, b=60, l=140, r=120),
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_table(agg):
    """Tabel detail per plant."""
    st.markdown("### 📋 Detail per Plant")

    df = agg.copy()

    # Format
    df["Output_Formatted"] = df["Output_Kg"].apply(lambda x: f"{x:,.0f} Kg")
    df["Share_Formatted"] = df["Share_Pct"].apply(lambda x: f"{x:.1f}%")

    if df["Cost"].notna().any():
        df["Cost_Formatted"] = df["Cost"].apply(
            lambda x: f"Rp {x:,.0f}" if pd.notna(x) else "—"
        )
        df["Cost_Kg_Formatted"] = df["Cost_Kg"].apply(
            lambda x: f"Rp {x:,.0f}" if pd.notna(x) else "—"
        )

        display = pd.DataFrame({
            "Plant": df["Plant"],
            "Output (Kg)": df["Output_Formatted"],
            "Share": df["Share_Formatted"],
            "Total Cost": df["Cost_Formatted"],
            "Cost/Kg": df["Cost_Kg_Formatted"],
            "Baris Data": df["Rows"],
        })
    else:
        display = pd.DataFrame({
            "Plant": df["Plant"],
            "Output (Kg)": df["Output_Formatted"],
            "Share": df["Share_Formatted"],
            "Baris Data": df["Rows"],
        })

    st.dataframe(display, use_container_width=True, hide_index=True)


def render(ds: Dataset, scope: Scope) -> None:
    st.title("🏭 Multi-Plant & Cost Allocation")
    st.caption("Konsolidasi produksi & biaya lintas plant (BRD 6).")

    if ds.production is None or ds.production.empty:
        st.warning("Data produksi tidak tersedia.")
        return

    if "Plant" not in ds.production.columns:
        st.info(
            "Kolom **Plant** tidak ada di sheet Production. "
            "Fitur multi-plant tidak tersedia pada data ini."
        )
        return

    prod = scope_production(ds.production, scope)
    if prod.empty:
        st.info("Tidak ada data produksi pada filter terpilih.")
        return

    # Aggregate output per plant
    agg = prod.groupby("Plant", as_index=False).agg(
        Output_Kg=("Output_Kg", "sum"),
        Rows=("Output_Kg", "count"),
    )
    agg["Share_Pct"] = agg["Output_Kg"] / agg["Output_Kg"].sum() * 100

    # Coba join dengan data biaya per plant
    costs = ds.costs
    if (costs is not None and not costs.empty
            and "Plant" in costs.columns and costs["Plant"].notna().any()):
        c_by_plant = costs.groupby("Plant", as_index=False)["Cost"].sum()
        agg = agg.merge(c_by_plant, on="Plant", how="left")
        agg["Cost"] = agg["Cost"].fillna(0)
        agg["Cost_Kg"] = agg["Cost"] / agg["Output_Kg"].replace(0, pd.NA)
    else:
        agg["Cost"] = pd.NA
        agg["Cost_Kg"] = pd.NA
        st.info(
            "ℹ️ Dimensi biaya per Plant belum tersedia di sheet biaya. "
            "Analisis Cost/Kg per Plant tidak dapat dihitung."
        )

    # 1. KPI cards
    _render_kpi(agg)

    st.markdown("---")

    # 2. Output comparison + Pie
    col_left, col_right = st.columns([1.4, 1])

    with col_left:
        _render_output_comparison(agg)

    with col_right:
        _render_share_pie(agg)

    # 3. Cost/Kg comparison (kalau ada)
    if agg["Cost_Kg"].notna().any():
        st.markdown("---")
        _render_cost_comparison(agg)

    st.markdown("---")

    # 4. Detail table
    _render_table(agg)

    # 5. Insight
    st.markdown("---")
    st.markdown("### 💡 Insight")

    # Top plant
    top = agg.loc[agg["Output_Kg"].idxmax()]
    st.success(
        f"🏆 **Top Performer:** {top['Plant']} menghasilkan "
        f"**{top['Output_Kg']:,.0f} Kg** ({top['Share_Pct']:.1f}% dari total output)."
    )

    # Lowest plant
    if len(agg) > 1:
        low = agg.loc[agg["Output_Kg"].idxmin()]
        st.info(
            f"📉 **Perlu perhatian:** {low['Plant']} menghasilkan "
            f"**{low['Output_Kg']:,.0f} Kg** ({low['Share_Pct']:.1f}%)."
        )

    # Cost insight
    if agg["Cost_Kg"].notna().any() and len(agg[agg["Cost_Kg"].notna()]) > 1:
        best_cost = agg.loc[agg["Cost_Kg"].idxmin()]
        worst_cost = agg.loc[agg["Cost_Kg"].idxmax()]
        gap = worst_cost["Cost_Kg"] - best_cost["Cost_Kg"]

        st.warning(
            f"💰 **Efisiensi:** {best_cost['Plant']} (Rp {best_cost['Cost_Kg']:,.0f}/Kg) "
            f"vs {worst_cost['Plant']} (Rp {worst_cost['Cost_Kg']:,.0f}/Kg). "
            f"Selisih **Rp {gap:,.0f}/Kg** — potensi belajar antar plant."
        )