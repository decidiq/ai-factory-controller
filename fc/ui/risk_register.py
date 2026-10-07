"""Risk Register - data-driven dengan heat map (BRD 5.4 & 6)."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from ..kpi import risk_table
from ..pipeline import Dataset
from .charts import COLORS, apply_theme


def _render_kpi(tbl):
    """4 KPI cards untuk Risk."""
    st.markdown("### 🛡️ Ringkasan Risiko")

    total = len(tbl)
    high = int((tbl["Level"] == "Tinggi").sum())
    medium = int((tbl["Level"] == "Sedang").sum())
    low = int((tbl["Level"] == "Rendah").sum())

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Risiko", f"{total}")
    c2.metric("🔴 Tinggi (≥6)", f"{high}",
              delta="Perlu aksi" if high > 0 else "Aman",
              delta_color="inverse" if high > 0 else "off")
    c3.metric("🟡 Sedang (3-5)", f"{medium}")
    c4.metric("🟢 Rendah (<3)", f"{low}")


def _render_heatmap(tbl):
    """Heat map Probability × Impact."""
    st.markdown("### 🔥 Heat Map Risiko")
    st.caption("Probabilitas (x) × Dampak (y). Zona merah = prioritas tertinggi.")

    # Buat matrix 3×3 (skala 1-3)
    matrix = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
    for _, r in tbl.iterrows():
        try:
            p = int(r["Probability_Val"]) - 1
            i = int(r["Impact_Val"]) - 1
            if 0 <= p <= 2 and 0 <= i <= 2:
                matrix[i][p] += 1  # row = impact, col = probability
        except (ValueError, TypeError, KeyError):
            pass

    # Z matrix untuk warna (score = p * i)
    z_score = [
        [1 * 1, 1 * 2, 1 * 3],
        [2 * 1, 2 * 2, 2 * 3],
        [3 * 1, 3 * 2, 3 * 3],
    ]

    # Text = jumlah risiko di cell itu
    text = [[str(v) if v > 0 else "" for v in row] for row in matrix]

    fig = go.Figure(go.Heatmap(
        z=z_score,
        x=["Low (1)", "Medium (2)", "High (3)"],
        y=["Low (1)", "Medium (2)", "High (3)"],
        colorscale=[
            [0.0, "#10B981"],   # score 1 - green
            [0.33, "#F59E0B"],  # score 4 - yellow
            [0.66, "#EF4444"],  # score 6 - red
            [1.0, "#991B1B"],   # score 9 - dark red
        ],
        text=text,
        texttemplate="<b>%{text}</b>",
        textfont=dict(size=24, color="#FFFFFF", family="Inter"),
        hovertemplate=(
            "<b>Probability:</b> %{x}<br>"
            "<b>Impact:</b> %{y}<br>"
            "<b>Score:</b> %{z}<extra></extra>"
        ),
        showscale=False,
        xgap=3, ygap=3,
    ))

    fig = apply_theme(fig, height=420)
    fig.update_layout(
        xaxis=dict(
            title=dict(text="<b>Probability</b>", font=dict(size=13)),
            tickfont=dict(size=12),
            side="bottom",
        ),
        yaxis=dict(
            title=dict(text="<b>Impact</b>", font=dict(size=13)),
            tickfont=dict(size=12),
        ),
        margin=dict(t=40, b=80, l=80, r=40),
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_risk_list(tbl):
    """Risk list dengan cards berwarna."""
    st.markdown("### 📋 Daftar Risiko")
    st.caption("Diurutkan berdasarkan skor (Probability × Impact).")

    # Sort by Score
    tbl_sorted = tbl.sort_values("Score", ascending=False).reset_index(drop=True)

    for _, r in tbl_sorted.iterrows():
        level = r["Level"]
        score = int(r["Score"])

        color_map = {
            "Tinggi": {"border": COLORS["danger"], "bg": "#FEF2F2", "icon": "🔴"},
            "Sedang": {"border": COLORS["warning"], "bg": "#FFFBEB", "icon": "🟡"},
            "Rendah": {"border": COLORS["success"], "bg": "#ECFDF5", "icon": "🟢"},
        }
        style = color_map.get(level, color_map["Rendah"])

        # Get optional fields
        risk_name = str(r.get("Risk", "—"))
        status = str(r.get("Status", "—"))

        st.markdown(f"""
        <div style="
            background: #FFFFFF;
            border: 1px solid #E9D5FF;
            border-left: 5px solid {style['border']};
            border-radius: 12px;
            padding: 16px 20px;
            margin-bottom: 12px;
            box-shadow: 0 2px 6px rgba(139, 92, 246, 0.05);
        ">
            <div style="display: flex; justify-content: space-between; align-items: start;">
                <div style="flex: 1;">
                    <div style="
                        font-size: 1rem;
                        font-weight: 700;
                        color: #1E1B4B;
                        margin-bottom: 6px;
                    ">{style['icon']} {risk_name}</div>
                    <div style="font-size: 0.85rem; color: #64748B;">
                        <strong>Status:</strong> {status} ·
                        <strong>Probability:</strong> {int(r['Probability_Val'])} ·
                        <strong>Impact:</strong> {int(r['Impact_Val'])}
                    </div>
                </div>
                <div style="
                    background: {style['bg']};
                    color: {style['border']};
                    padding: 10px 18px;
                    border-radius: 10px;
                    text-align: center;
                    min-width: 100px;
                    margin-left: 16px;
                ">
                    <div style="font-size: 0.7rem; font-weight: 700; letter-spacing: 0.8px;">
                        SCORE
                    </div>
                    <div style="font-size: 1.6rem; font-weight: 800; letter-spacing: -0.8px; line-height: 1;">
                        {score}
                    </div>
                    <div style="font-size: 0.75rem; font-weight: 600; margin-top: 2px;">
                        {level}
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)


def _render_action_plan(tbl):
    """Action plan untuk risiko tinggi."""
    st.markdown("---")
    st.markdown("### 💡 Action Plan")

    high_risks = tbl[tbl["Level"] == "Tinggi"]

    if high_risks.empty:
        st.success("✅ Tidak ada risiko level tinggi. Semua terkendali.")
        return

    st.warning(
        f"⚠️ **{len(high_risks)} risiko level TINGGI** perlu tindakan segera."
    )

    for _, r in high_risks.iterrows():
        with st.expander(f"🔴 {r['Risk']} — Score {int(r['Score'])}"):
            st.markdown(f"**Probability:** {int(r['Probability_Val'])} (1-3)")
            st.markdown(f"**Impact:** {int(r['Impact_Val'])} (1-3)")
            st.markdown(f"**Status:** {r.get('Status', '—')}")
            if r.get("Probability"):
                st.caption(f"Teks asli: Probability = {r['Probability']}")
            if r.get("Impact"):
                st.caption(f"Teks asli: Impact = {r['Impact']}")


def render(ds: Dataset, scope) -> None:
    st.title("🛡️ Risk Register")
    st.caption("Pemantauan risiko operasional pabrik dengan heat map (BRD 5.4 & 6).")

    risk = ds.risk
    if risk is None or risk.empty:
        st.warning("Data Risk_Register tidak tersedia (sheet 'Risk_Register').")
        st.info("Sesuai BRD 5.5: tidak ada data pengganti yang ditampilkan.")
        return

    if "Risk" not in risk.columns:
        st.error("Sheet Risk_Register harus punya kolom **Risk**.")
        st.dataframe(risk.head(20), use_container_width=True)
        return

    if not {"Probability_Val", "Impact_Val"} <= set(risk.columns):
        st.error(
            "Sheet Risk_Register butuh **Probability_Val** & **Impact_Val** "
            "(skala 1-3)."
        )
        st.dataframe(risk, use_container_width=True, hide_index=True)
        return

    tbl = risk_table(risk)

    # 1. KPI cards
    _render_kpi(tbl)

    st.markdown("---")

    # 2. Heat map + Risk list (side by side)
    col_left, col_right = st.columns([1, 1.2])

    with col_left:
        _render_heatmap(tbl)

    with col_right:
        st.markdown("### 📊 Distribusi Level")
        st.caption("Jumlah risiko per level.")

        level_counts = tbl["Level"].value_counts().reset_index()
        level_counts.columns = ["Level", "Jumlah"]

        color_map = {"Tinggi": COLORS["danger"], "Sedang": COLORS["warning"],
                     "Rendah": COLORS["success"]}
        colors = [color_map.get(l, COLORS["text_muted"]) for l in level_counts["Level"]]

        fig = go.Figure(go.Bar(
            x=level_counts["Level"],
            y=level_counts["Jumlah"],
            marker=dict(color=colors, line=dict(width=0)),
            text=[f"<b>{v}</b>" for v in level_counts["Jumlah"]],
            textposition="outside",
            textfont=dict(size=13, color=COLORS["text"], family="Inter"),
            cliponaxis=False,
        ))

        fig = apply_theme(fig, height=300)
        fig.update_layout(
            showlegend=False,
            yaxis_title="<b>Jumlah</b>",
            xaxis_title="",
        )
        st.plotly_chart(fig, use_container_width=True)

        # Stats kecil
        c1, c2 = st.columns(2)
        c1.metric("Rata-rata Score", f"{tbl['Score'].mean():.1f}")
        c2.metric("Max Score", f"{int(tbl['Score'].max())}")

    st.markdown("---")

    # 3. Risk list
    _render_risk_list(tbl)

    # 4. Action plan
    _render_action_plan(tbl)