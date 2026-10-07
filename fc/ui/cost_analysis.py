"""Cost Analysis — COGM breakdown, Pareto, Cost/Kg trend premium."""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from ..config import targets_from_config
from ..kpi import Scope, cogm_for_scope, cost_per_kg, scope_production
from ..pipeline import Dataset
from .charts import CATEGORY_COLORS, COLORS, apply_theme, pie_chart


def _fmt_rp(v: float) -> str:
    """Format Rupiah singkat."""
    if abs(v) >= 1_000_000_000:
        return f"Rp {v/1_000_000_000:.2f} M"
    if abs(v) >= 1_000_000:
        return f"Rp {v/1_000_000:.1f} jt"
    return f"Rp {v:,.0f}"


def _render_kpi(cogm_kpi, cpk, output_kg, targets, breakdown):
    """KPI cards di atas."""
    st.markdown("### 💰 Ringkasan Biaya")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Total COGM", _fmt_rp(cogm_kpi.value),
              help=f"Rp {cogm_kpi.value:,.0f}")

    c2.metric("Output", f"{output_kg:,.0f} Kg")

    if cpk.available:
        delta_color = "inverse" if (targets.max_cost_per_kg > 0
                                     and cpk.value > targets.max_cost_per_kg) else "normal"
        c3.metric("Cost/Kg", f"Rp {cpk.value:,.0f}",
                  delta=(f"Batas Rp {targets.max_cost_per_kg:,.0f}"
                         if targets.max_cost_per_kg > 0 else None),
                  delta_color=delta_color)
    else:
        c3.metric("Cost/Kg", "—")
        c3.caption(cpk.note)

    if breakdown:
        top_cat = max(breakdown.items(), key=lambda kv: kv[1])
        c4.metric("Komponen Terbesar", top_cat[0],
                  delta=f"{_fmt_rp(top_cat[1])}",
                  delta_color="off")


def _render_cogm_breakdown(breakdown):
    """Pie + table komponen COGM."""
    st.markdown("### 🥧 Komposisi COGM")
    st.caption("Distribusi setiap komponen biaya terhadap COGM total.")

    df = pd.DataFrame(
        list(breakdown.items()), columns=["Komponen", "Nilai"]
    ).sort_values("Nilai", ascending=False)

    total = df["Nilai"].sum()
    center = (f"Rp {total/1_000_000_000:.2f} M"
              if total >= 1e9 else f"Rp {total/1_000_000:.1f} jt")

    c1, c2 = st.columns([1, 1.2])

    with c1:
        fig = px.pie(df, names="Komponen", values="Nilai", hole=0.55)
        fig = pie_chart(fig, height=380, center_text=center)
        fig.update_traces(
            textinfo="label+percent",
            textposition="inside",
            textfont=dict(size=11, color="#FFFFFF", family="Inter"),
        )
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        df_display = df.copy()
        df_display["Nilai (Rp)"] = df_display["Nilai"].apply(lambda x: f"Rp {x:,.0f}")
        df_display["Porsi (%)"] = (df_display["Nilai"] / total * 100).round(1)
        df_display["Porsi (%)"] = df_display["Porsi (%)"].apply(lambda x: f"{x}%")

        st.markdown("**Detail Komponen:**")
        st.dataframe(
            df_display[["Komponen", "Nilai (Rp)", "Porsi (%)"]],
            use_container_width=True,
            hide_index=True,
            height=380,
        )


def _render_pareto(ds, scope):
    """Pareto Material Top 10 dengan bar + cumulative line."""
    st.markdown("### 📊 Pareto Material Top 10")
    st.caption("Aturan 80/20: 20% material = 80% biaya. Fokus negosiasi di sini.")

    rm = ds.raw_material
    if rm is None or rm.empty or "Material" not in rm.columns:
        st.info("Data Raw_Material tidak tersedia.")
        return

    if scope.plant and "Plant" in rm.columns:
        rm = rm[rm["Plant"].eq(scope.plant).fillna(False)]

    if rm.empty or "Cost" not in rm.columns:
        st.info("Tidak ada data biaya material pada filter ini.")
        return

    top = (rm.groupby("Material", as_index=False)["Cost"].sum()
             .sort_values("Cost", ascending=False)
             .head(10)
             .reset_index(drop=True))

    total_cost = top["Cost"].sum()
    top["Cumulative_Pct"] = (top["Cost"].cumsum() / total_cost * 100)
    top["Cost_Jt"] = top["Cost"] / 1_000_000

    fig = go.Figure()

    # Bar
    fig.add_trace(go.Bar(
        x=top["Material"],
        y=top["Cost_Jt"],
        name="Cost (Rp jt)",
        marker=dict(color=COLORS["primary"], line=dict(width=0)),
        text=[f"<b>Rp {c:,.0f} jt</b>" for c in top["Cost_Jt"]],
        textposition="outside",
        textfont=dict(size=10, color=COLORS["text"], family="Inter"),
        cliponaxis=False,
        hovertemplate="<b>%{x}</b><br>Rp %{y:,.0f} jt<extra></extra>",
        yaxis="y",
    ))

    # Cumulative line
    fig.add_trace(go.Scatter(
        x=top["Material"],
        y=top["Cumulative_Pct"],
        name="Cumulative (%)",
        mode="lines+markers",
        line=dict(color=COLORS["accent"], width=3),
        marker=dict(size=9, color=COLORS["accent"],
                    line=dict(color="#FFFFFF", width=2)),
        hovertemplate="<b>%{x}</b><br>Cumulative: %{y:.1f}%<extra></extra>",
        yaxis="y2",
    ))

    fig.add_hline(
        y=80, line_dash="dash", line_color=COLORS["warning"], line_width=2,
        annotation_text="<b>80%</b>", annotation_position="right",
        annotation_font=dict(size=10, color=COLORS["warning"]),
        yref="y2",
    )

    fig = apply_theme(fig, height=460)
    fig.update_layout(
        showlegend=True,
        legend=dict(orientation="h", y=-0.15, x=0.5, xanchor="center"),
        xaxis=dict(
            title=dict(text="<b>Material</b>", font=dict(size=12)),
            tickfont=dict(size=10),
            tickangle=-30,
        ),
        yaxis=dict(
            title=dict(text="<b>Cost (Rp jt)</b>", font=dict(size=12)),
            tickfont=dict(size=10, color=COLORS["primary"]),
            title_font=dict(color=COLORS["primary"]),
        ),
        yaxis2=dict(
            title=dict(text="<b>Cumulative (%)</b>", font=dict(size=12)),
            tickfont=dict(size=10, color=COLORS["accent"]),
            title_font=dict(color=COLORS["accent"]),
            overlaying="y",
            side="right",
            range=[0, 105],
            showgrid=False,
        ),
        margin=dict(t=40, b=120, l=70, r=70),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Insight
    above_80 = (top["Cumulative_Pct"] <= 80).sum() + 1
    st.info(
        f"💡 **Insight:** {above_80} dari {len(top)} material teratas "
        f"berkontribusi hingga **80% dari total biaya material**. "
        f"Fokus negosiasi di sini!"
    )


def _render_cost_kg_trend(ds, scope):
    """Trend Cost/Kg per bulan."""
    st.markdown("### 📈 Trend Cost/Kg per Bulan")
    st.caption("Apakah biaya per Kg naik atau turun dari waktu ke waktu?")

    costs = ds.costs
    if costs is None or costs.empty or "Period" not in costs.columns:
        st.info("Data biaya per periode tidak tersedia.")
        return

    c = costs.copy()
    c = c[c["Period"].notna()]

    if scope.plant and "Plant" in c.columns:
        c = c[c["Plant"].eq(scope.plant).fillna(False)]

    if c.empty:
        st.info("Tidak ada data biaya per periode pada filter ini.")
        return

    # Aggregate cost by period
    cost_by_period = c.groupby("Period", as_index=False)["Cost"].sum()

    # Aggregate output by period
    prod = scope_production(ds.production, scope)
    if prod.empty or "Date" not in prod.columns:
        st.info("Tidak ada data produksi.")
        return

    prod_copy = prod.copy()
    prod_copy["Date"] = pd.to_datetime(prod_copy["Date"])
    prod_copy["Period"] = prod_copy["Date"].dt.strftime("%Y-%m")
    output_by_period = prod_copy.groupby("Period", as_index=False)["Output_Kg"].sum()

    # Merge
    merged = cost_by_period.merge(output_by_period, on="Period", how="inner")
    if merged.empty:
        st.info("Tidak dapat match periode biaya & produksi.")
        return

    merged["Cost_Per_Kg"] = merged["Cost"] / merged["Output_Kg"].replace(0, pd.NA)
    merged = merged.dropna(subset=["Cost_Per_Kg"]).sort_values("Period")

    if merged.empty:
        st.info("Cost/Kg tidak dapat dihitung.")
        return

    # Bar chart Cost/Kg per period
    fig = go.Figure(go.Bar(
        x=merged["Period"],
        y=merged["Cost_Per_Kg"],
        marker=dict(
            color=merged["Cost_Per_Kg"],
            colorscale=[
                [0, COLORS["success"]],
                [0.5, COLORS["warning"]],
                [1, COLORS["danger"]],
            ],
            line=dict(width=0),
        ),
        text=[f"<b>Rp {v:,.0f}</b>" for v in merged["Cost_Per_Kg"]],
        textposition="outside",
        textfont=dict(size=11, color=COLORS["text"], family="Inter"),
        cliponaxis=False,
        hovertemplate=(
            "<b>%{x}</b><br>"
            "Cost/Kg: Rp %{y:,.0f}<extra></extra>"
        ),
    ))

    # AVG line
    avg = merged["Cost_Per_Kg"].mean()
    fig.add_hline(
        y=avg, line_dash="dash", line_color=COLORS["primary_dark"], line_width=2,
        annotation_text=f"<b>AVG Rp {avg:,.0f}</b>",
        annotation_position="right",
        annotation_font=dict(size=10, color=COLORS["primary_dark"]),
    )

    fig = apply_theme(fig, height=380)
    fig.update_layout(
        showlegend=False,
        yaxis=dict(title="<b>Cost/Kg (Rp)</b>", tickformat=",.0f"),
        xaxis=dict(title="<b>Periode</b>", tickfont=dict(size=11)),
        margin=dict(t=40, b=60, l=80, r=100),
    )
    st.plotly_chart(fig, use_container_width=True)


def render(ds: Dataset, scope: Scope) -> None:
    st.title("💰 Cost Analysis")
    st.caption("Analisis COGM, Pareto material, dan trend Cost/Kg.")

    if ds.costs is None or ds.costs.empty:
        st.warning("Data biaya tidak tersedia.")
        return

    targets = targets_from_config(ds.config)
    cogm_kpi, breakdown = cogm_for_scope(ds.costs, ds.production, scope)
    prod = scope_production(ds.production, scope)
    output_kg = float(prod["Output_Kg"].sum()) if len(prod) else 0.0

    if not cogm_kpi.available:
        st.info(f"COGM tidak dapat dihitung: {cogm_kpi.note}")
        return

    cpk = cost_per_kg(cogm_kpi, output_kg)

    # 1. KPI cards
    _render_kpi(cogm_kpi, cpk, output_kg, targets, breakdown)

    st.markdown("---")

    # 2. COGM Breakdown
    if breakdown:
        _render_cogm_breakdown(breakdown)
        st.markdown("---")

    # 3. Pareto Material
    _render_pareto(ds, scope)

    st.markdown("---")

    # 4. Cost/Kg trend
    _render_cost_kg_trend(ds, scope)