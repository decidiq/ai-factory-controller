"""Manufacturing Variance — Budget vs Actual premium (BRD 6)."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from ..config import targets_from_config
from ..kpi import variance_table
from ..pipeline import Dataset
from .charts import COLORS, apply_theme


def _render_kpi_cards(tbl, targets):
    """KPI cards: Total Budget, Actual, Variance, Utilization."""
    st.markdown("### 💰 Ringkasan Budget vs Actual")

    total_budget = tbl["Budget"].sum()
    total_actual = tbl["Actual"].sum()
    total_variance = tbl["Variance"].sum()
    utilization = (total_actual / total_budget * 100) if total_budget > 0 else 0

    def _fmt_rp(v: float) -> str:
        """Format Rupiah singkat."""
        if abs(v) >= 1_000_000_000:
            return f"Rp {v/1_000_000_000:.2f} M"
        if abs(v) >= 1_000_000:
            return f"Rp {v/1_000_000:.1f} jt"
        return f"Rp {v:,.0f}"

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Budget", _fmt_rp(total_budget),
              help=f"Rp {total_budget:,.0f}")
    c2.metric("Total Actual", _fmt_rp(total_actual),
              help=f"Rp {total_actual:,.0f}")

    variance_status = "Over Budget" if total_variance > 0 else "Under Budget"
    c3.metric(
        "Total Variance",
        _fmt_rp(total_variance),
        delta=variance_status,
        delta_color="inverse" if total_variance > 0 else "normal",
        help=f"Rp {total_variance:,.0f}",
    )

    c4.metric(
        "Budget Utilization",
        f"{utilization:.1f}%",
        delta=f"Toleransi ±{targets.variance_tolerance_pct:g}%",
        delta_color="off",
    )

def _render_bar_chart(tbl):
    """Bar chart Budget vs Actual dengan label nilai."""
    st.markdown("### 📊 Variance per Kategori")
    st.caption("Perbandingan Budget vs Actual untuk setiap kategori biaya.")

    fig = go.Figure()

    # Trace Budget
    fig.add_trace(go.Bar(
        name="Budget",
        x=tbl["Category"],
        y=tbl["Budget"],
        marker=dict(color=COLORS["primary"], line=dict(width=0)),
        text=[f"<b>Rp {v/1_000_000:.1f} jt</b>" for v in tbl["Budget"]],
        textposition="outside",
        textfont=dict(size=11, color=COLORS["primary_dark"], family="Inter"),
        cliponaxis=False,
        hovertemplate="<b>%{x}</b><br>Budget: Rp %{y:,.0f}<extra></extra>",
    ))

    # Trace Actual
    fig.add_trace(go.Bar(
        name="Actual",
        x=tbl["Category"],
        y=tbl["Actual"],
        marker=dict(color=COLORS["accent"], line=dict(width=0)),
        text=[f"<b>Rp {v/1_000_000:.1f} jt</b>" for v in tbl["Actual"]],
        textposition="outside",
        textfont=dict(size=11, color=COLORS["accent_dark"], family="Inter"),
        cliponaxis=False,
        hovertemplate="<b>%{x}</b><br>Actual: Rp %{y:,.0f}<extra></extra>",
    ))

    fig = apply_theme(fig, height=440)
    fig.update_layout(
        barmode="group",
        bargap=0.35,
        bargroupgap=0.1,
        yaxis=dict(
            title=dict(text="<b>Nilai (Rp)</b>", font=dict(size=12, color=COLORS["text"])),
            tickformat=",.0f",
            tickfont=dict(size=10),
        ),
        xaxis=dict(
            title=dict(text="<b>Kategori</b>", font=dict(size=12, color=COLORS["text"])),
            tickfont=dict(size=12, color=COLORS["text"]),
        ),
        legend=dict(
            orientation="h", y=-0.15, x=0.5, xanchor="center",
        ),
        margin=dict(t=60, b=80, l=80, r=40),
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_variance_chart(tbl):
    """Bar chart Variance (Actual - Budget) dengan warna by status."""
    st.markdown("### 📉 Variance per Kategori (Rp)")
    st.caption("Berapa selisih Actual vs Budget? Merah = Over, Hijau = Under.")

    # Warna by variance
    colors = [
        COLORS["danger"] if v > 0 else COLORS["success"]
        for v in tbl["Variance"]
    ]

    fig = go.Figure(go.Bar(
        x=tbl["Category"],
        y=tbl["Variance"],
        marker=dict(color=colors, line=dict(width=0)),
        text=[
            f"<b>{'+' if v > 0 else '−'}Rp {abs(v)/1_000_000:.1f} jt</b>"
            for v in tbl["Variance"]
        ],
        textposition="outside",
        textfont=dict(size=11, color=COLORS["text"], family="Inter"),
        cliponaxis=False,
        hovertemplate="<b>%{x}</b><br>Variance: Rp %{y:,.0f}<extra></extra>",
    ))

    # Garis nol
    fig.add_hline(
        y=0, line_dash="dash", line_color=COLORS["text_muted"], line_width=1.5,
    )

    fig = apply_theme(fig, height=380)
    fig.update_layout(
        showlegend=False,
        yaxis=dict(
            title=dict(text="<b>Variance (Rp)</b>", font=dict(size=12, color=COLORS["text"])),
            tickformat=",.0f",
            tickfont=dict(size=10),
            zeroline=True, zerolinecolor=COLORS["text_muted"], zerolinewidth=2,
        ),
        xaxis=dict(
            title=dict(text="<b>Kategori</b>", font=dict(size=12, color=COLORS["text"])),
            tickfont=dict(size=12, color=COLORS["text"]),
        ),
        margin=dict(t=60, b=80, l=80, r=40),
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_table(tbl):
    """Tabel detail variance."""
    st.markdown("### 📋 Tabel Detail Variance")

    display = tbl.copy()
    display["Budget"] = display["Budget"].apply(lambda x: f"Rp {x:,.0f}")
    display["Actual"] = display["Actual"].apply(lambda x: f"Rp {x:,.0f}")
    display["Variance"] = display["Variance"].apply(
        lambda x: f"{'+' if x > 0 else '−'}Rp {abs(x):,.0f}"
    )
    display["Variance_Pct"] = display["Variance_Pct"].apply(
        lambda x: f"{x:+.2f}%" if pd.notna(x) else "—"
    )
    display["Utilization_Pct"] = display["Utilization_Pct"].apply(
        lambda x: f"{x:.2f}%" if pd.notna(x) else "—"
    )

    # Emoji status
    display["Status"] = display["Status"].map({
        "Over Budget": "🔴 Over Budget",
        "Under Budget": "🟢 Under Budget",
        "On Budget": "🟡 On Budget",
    })

    display = display.rename(columns={
        "Variance_Pct": "Variance %",
        "Utilization_Pct": "Utilization %",
    })

    st.dataframe(display, use_container_width=True, hide_index=True)


def render(ds: Dataset, scope) -> None:
    st.title("⚖️ Manufacturing Variance")
    st.caption("Analisis Budget vs Actual per kategori biaya (BRD 6).")

    budget = ds.budget
    if budget is None or budget.empty:
        st.warning("Sheet **Budget** tidak tersedia.")
        return

    if not {"Category", "Budget"} <= set(budget.columns):
        st.error("Sheet Budget harus punya kolom **Category** dan **Budget**.")
        return

    if "Actual" not in budget.columns or budget["Actual"].isna().all():
        st.error(
            "Kolom **Actual** belum ada atau kosong di sheet Budget. "
            "Sesuai BRD 5.4: Actual perlu diturunkan dari sheet biaya. "
            "Tidak ada angka pengganti yang ditampilkan."
        )
        return

    targets = targets_from_config(ds.config)
    tbl = variance_table(budget)

    # 1. KPI cards
    _render_kpi_cards(tbl, targets)

    st.markdown("---")

    # 2. Bar chart Budget vs Actual
    _render_bar_chart(tbl)

    st.markdown("---")

    # 3. Bar chart Variance
    _render_variance_chart(tbl)

    st.markdown("---")

    # 4. Tabel detail
    _render_table(tbl)

    st.markdown("---")
    st.info(
        f"💡 **Toleransi variance:** ±{targets.variance_tolerance_pct:g}% "
        f"(BRD 6). Variance di luar toleransi ditandai sebagai "
        f"Over/Under Budget."
    )