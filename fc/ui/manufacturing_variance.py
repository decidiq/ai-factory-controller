"""Manufacturing Variance — Budget vs Actual premium (BRD 6)."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from ..config import targets_from_config
from ..kpi import variance_table
from ..pipeline import Dataset
from .charts import COLORS, apply_theme


# ==================== CSS GLASSMORPHISM ====================
GLASS_CSS = """
<style>
.mv-glass {
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
.mv-glass::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, var(--accent, #8B5CF6) 0%, #EC4899 100%);
}
.mv-glass:hover {
    transform: translateY(-3px);
    box-shadow: 0 16px 32px rgba(139, 92, 246, 0.18);
    border-color: rgba(139, 92, 246, 0.6);
}
.mv-glass-label {
    color: #6D28D9;
    font-weight: 700;
    font-size: 0.66rem;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    margin-bottom: 6px;
}
.mv-glass-value {
    color: #0F172A;
    font-weight: 800;
    font-size: 1.35rem;
    letter-spacing: -0.5px;
    line-height: 1.1;
    margin-bottom: 4px;
}
.mv-glass-note {
    color: #94A3B8;
    font-size: 0.68rem;
    font-style: italic;
    line-height: 1.3;
}
.mv-glass-delta {
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.3px;
}

/* Banner */
.mv-banner {
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
.mv-banner::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 4px;
    background: linear-gradient(90deg, var(--b-accent, #8B5CF6) 0%, #EC4899 100%);
}
.mv-block { flex: 1; min-width: 160px; }
.mv-block-label {
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    margin-bottom: 6px;
}
.mv-block-value {
    font-size: 1.8rem;
    font-weight: 900;
    color: #FFFFFF;
    letter-spacing: -1px;
    line-height: 1.1;
    margin-bottom: 2px;
}
.mv-block-sub {
    font-size: 0.75rem;
    color: #94A3B8;
}
</style>
"""


def _inject_css():
    st.markdown(GLASS_CSS, unsafe_allow_html=True)


# ==================== HELPERS ====================
def _fmt_rp(v: float) -> str:
    if abs(v) >= 1_000_000_000:
        return f"Rp {v/1_000_000_000:.2f} M"
    if abs(v) >= 1_000_000:
        return f"Rp {v/1_000_000:.1f} jt"
    return f"Rp {v:,.0f}"


def _glass_card(col, label: str, value: str, accent: str = "#8B5CF6",
                note: str = None, delta: str = None,
                delta_color: str = None) -> None:
    note_html = f'<div class="mv-glass-note">{note}</div>' if note else ""
    delta_html = ""
    if delta:
        c = delta_color or "#10B981"
        delta_html = f'<div class="mv-glass-delta" style="color:{c};">{delta}</div>'
    html = (
        f'<div class="mv-glass" style="--accent: {accent};">'
        f'<div class="mv-glass-label">{label}</div>'
        f'<div class="mv-glass-value">{value}</div>'
        f'{delta_html}'
        f'{note_html}'
        f'</div>'
    )
    col.markdown(html, unsafe_allow_html=True)


# ==================== KPI CARDS ====================
def _render_kpi_cards(tbl, targets):
    st.markdown("### 💰 Ringkasan Budget vs Actual")

    total_budget = tbl["Budget"].sum()
    total_actual = tbl["Actual"].sum()
    total_variance = tbl["Variance"].sum()
    utilization = (total_actual / total_budget * 100) if total_budget > 0 else 0

    is_over = total_variance > 0
    tolerance = targets.variance_tolerance_pct
    within_tolerance = abs(utilization - 100) <= tolerance

    c1, c2, c3, c4 = st.columns(4)
    _glass_card(c1, "Total Budget", _fmt_rp(total_budget), "#8B5CF6",
                note=f"Rp {total_budget:,.0f}")
    _glass_card(c2, "Total Actual", _fmt_rp(total_actual), "#EC4899",
                note=f"Rp {total_actual:,.0f}")
    _glass_card(c3, "Total Variance", _fmt_rp(total_variance),
                "#EF4444" if is_over else "#10B981",
                delta=("⚠️ Over Budget" if is_over else "✅ Under Budget"),
                delta_color=("#EF4444" if is_over else "#10B981"))
    _glass_card(c4, "Budget Utilization", f"{utilization:.1f}%",
                "#3B82F6" if within_tolerance else "#F59E0B",
                delta=f"Toleransi ±{tolerance:g}%",
                delta_color=("#10B981" if within_tolerance else "#F59E0B"))

    # Banner status
    if is_over:
        html = (
            f'<div class="mv-banner" style="--b-accent: #EF4444;">'
            f'<div class="mv-block">'
            f'<div class="mv-block-label" style="color:#F87171;">⚠️ STATUS BUDGET</div>'
            f'<div class="mv-block-value">Over Budget</div>'
            f'<div class="mv-block-sub">Total variance {_fmt_rp(total_variance)}</div>'
            f'</div>'
            f'<div class="mv-block">'
            f'<div class="mv-block-label" style="color:#A78BFA;">💰 TOTAL BUDGET</div>'
            f'<div class="mv-block-value">{_fmt_rp(total_budget)}</div>'
            f'<div class="mv-block-sub">Alokasi</div>'
            f'</div>'
            f'<div class="mv-block">'
            f'<div class="mv-block-label" style="color:#A78BFA;">📊 UTILIZATION</div>'
            f'<div class="mv-block-value">{utilization:.1f}%</div>'
            f'<div class="mv-block-sub">Dari budget</div>'
            f'</div>'
            f'</div>'
        )
        st.markdown(html, unsafe_allow_html=True)
    else:
        html = (
            f'<div class="mv-banner" style="--b-accent: #10B981;">'
            f'<div class="mv-block">'
            f'<div class="mv-block-label" style="color:#34D399;">✅ STATUS BUDGET</div>'
            f'<div class="mv-block-value">Under Budget</div>'
            f'<div class="mv-block-sub">Penghematan {_fmt_rp(abs(total_variance))}</div>'
            f'</div>'
            f'<div class="mv-block">'
            f'<div class="mv-block-label" style="color:#A78BFA;">💰 TOTAL BUDGET</div>'
            f'<div class="mv-block-value">{_fmt_rp(total_budget)}</div>'
            f'<div class="mv-block-sub">Alokasi</div>'
            f'</div>'
            f'<div class="mv-block">'
            f'<div class="mv-block-label" style="color:#A78BFA;">📊 UTILIZATION</div>'
            f'<div class="mv-block-value">{utilization:.1f}%</div>'
            f'<div class="mv-block-sub">Dari budget</div>'
            f'</div>'
            f'</div>'
        )
        st.markdown(html, unsafe_allow_html=True)


# ==================== BAR CHART ====================
def _render_bar_chart(tbl):
    st.markdown("### 📊 Variance per Kategori")
    st.caption("Perbandingan Budget vs Actual untuk setiap kategori biaya.")

    fig = go.Figure()

    fig.add_trace(go.Bar(
        name="Budget",
        x=tbl["Category"], y=tbl["Budget"],
        marker=dict(color=COLORS["primary"], line=dict(width=0)),
        text=[f"<b>Rp {v/1_000_000:.1f} jt</b>" for v in tbl["Budget"]],
        textposition="outside",
        textfont=dict(size=11, color=COLORS["primary_dark"], family="Inter"),
        cliponaxis=False,
        hovertemplate="<b>%{x}</b><br>Budget: Rp %{y:,.0f}<extra></extra>",
    ))

    fig.add_trace(go.Bar(
        name="Actual",
        x=tbl["Category"], y=tbl["Actual"],
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
        bargap=0.35, bargroupgap=0.1,
        yaxis=dict(
            title=dict(text="<b>Nilai (Rp)</b>", font=dict(size=12, color=COLORS["text"])),
            tickformat=",.0f", tickfont=dict(size=10),
        ),
        xaxis=dict(
            title=dict(text="<b>Kategori</b>", font=dict(size=12, color=COLORS["text"])),
            tickfont=dict(size=12, color=COLORS["text"]),
        ),
        legend=dict(orientation="h", y=-0.15, x=0.5, xanchor="center"),
        margin=dict(t=60, b=80, l=80, r=40),
    )
    st.plotly_chart(fig, use_container_width=True)


# ==================== VARIANCE CHART ====================
def _render_variance_chart(tbl):
    st.markdown("### 📉 Variance per Kategori (Rp)")
    st.caption("Berapa selisih Actual vs Budget? Merah = Over, Hijau = Under.")

    colors = [
        COLORS["danger"] if v > 0 else COLORS["success"]
        for v in tbl["Variance"]
    ]

    fig = go.Figure(go.Bar(
        x=tbl["Category"], y=tbl["Variance"],
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

    fig.add_hline(
        y=0, line_dash="dash", line_color=COLORS["text_muted"], line_width=1.5,
    )

    fig = apply_theme(fig, height=380)
    fig.update_layout(
        showlegend=False,
        yaxis=dict(
            title=dict(text="<b>Variance (Rp)</b>", font=dict(size=12, color=COLORS["text"])),
            tickformat=",.0f", tickfont=dict(size=10),
            zeroline=True, zerolinecolor=COLORS["text_muted"], zerolinewidth=2,
        ),
        xaxis=dict(
            title=dict(text="<b>Kategori</b>", font=dict(size=12, color=COLORS["text"])),
            tickfont=dict(size=12, color=COLORS["text"]),
        ),
        margin=dict(t=60, b=80, l=80, r=40),
    )
    st.plotly_chart(fig, use_container_width=True)


# ==================== TABLE ====================
def _render_table(tbl):
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


# ==================== MAIN ====================
def render(ds: Dataset, scope) -> None:
    _inject_css()

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

    _render_kpi_cards(tbl, targets)

    st.markdown("---")
    _render_bar_chart(tbl)

    st.markdown("---")
    _render_variance_chart(tbl)

    st.markdown("---")
    _render_table(tbl)

    st.markdown("---")
    st.info(
        f"💡 **Toleransi variance:** ±{targets.variance_tolerance_pct:g}% "
        f"(BRD 6). Variance di luar toleransi ditandai sebagai "
        f"Over/Under Budget."
    )