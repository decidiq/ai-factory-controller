"""Risk Register - data-driven dengan heat map (BRD 5.4 & 6) — Premium UI."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from ..kpi import risk_table
from ..pipeline import Dataset
from .charts import COLORS, apply_theme


# ==================== CSS GLASSMORPHISM ====================
GLASS_CSS = """
<style>
.rr-glass {
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
.rr-glass::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, var(--accent, #8B5CF6) 0%, #EC4899 100%);
}
.rr-glass:hover {
    transform: translateY(-3px);
    box-shadow: 0 16px 32px rgba(139, 92, 246, 0.18);
    border-color: rgba(139, 92, 246, 0.6);
}
.rr-glass-label {
    color: #6D28D9;
    font-weight: 700;
    font-size: 0.66rem;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    margin-bottom: 6px;
}
.rr-glass-value {
    color: #0F172A;
    font-weight: 800;
    font-size: 1.5rem;
    letter-spacing: -0.5px;
    line-height: 1.1;
    margin-bottom: 4px;
}
.rr-glass-note {
    color: #94A3B8;
    font-size: 0.68rem;
    font-style: italic;
    line-height: 1.3;
}
.rr-glass-delta {
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.3px;
}

/* Risk Level Banner */
.rr-banner {
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
.rr-banner::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 4px;
    background: linear-gradient(90deg, #EF4444 0%, #F59E0B 50%, #10B981 100%);
}
.rr-block { flex: 1; min-width: 160px; }
.rr-block-label {
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    margin-bottom: 6px;
}
.rr-block-value {
    font-size: 1.8rem;
    font-weight: 900;
    color: #FFFFFF;
    letter-spacing: -1px;
    line-height: 1.1;
    margin-bottom: 2px;
}
.rr-block-sub {
    font-size: 0.75rem;
    color: #94A3B8;
}

/* Risk Card */
.rr-risk-card {
    background: #FFFFFF;
    border: 1px solid #E9D5FF;
    border-radius: 12px;
    padding: 16px 20px;
    margin-bottom: 12px;
    box-shadow: 0 2px 6px rgba(139, 92, 246, 0.05);
    position: relative;
    transition: transform 0.15s ease;
}
.rr-risk-card:hover {
    transform: translateX(4px);
    box-shadow: 0 6px 16px rgba(139, 92, 246, 0.12);
}
.rr-risk-name {
    font-size: 1rem;
    font-weight: 700;
    color: #1E1B4B;
    margin-bottom: 6px;
}
.rr-risk-meta {
    font-size: 0.82rem;
    color: #64748B;
}
.rr-risk-score {
    padding: 10px 18px;
    border-radius: 10px;
    text-align: center;
    min-width: 100px;
}
.rr-risk-score-label {
    font-size: 0.66rem;
    font-weight: 700;
    letter-spacing: 0.8px;
}
.rr-risk-score-value {
    font-size: 1.6rem;
    font-weight: 800;
    letter-spacing: -0.8px;
    line-height: 1;
    margin: 2px 0;
}
.rr-risk-score-level {
    font-size: 0.72rem;
    font-weight: 600;
}
</style>
"""


def _inject_css():
    st.markdown(GLASS_CSS, unsafe_allow_html=True)


# ==================== HELPERS ====================
def _glass_card(col, label: str, value: str, accent: str = "#8B5CF6",
                note: str = None, delta: str = None,
                delta_color: str = None) -> None:
    note_html = f'<div class="rr-glass-note">{note}</div>' if note else ""
    delta_html = ""
    if delta:
        c = delta_color or "#10B981"
        delta_html = f'<div class="rr-glass-delta" style="color:{c};">{delta}</div>'
    html = (
        f'<div class="rr-glass" style="--accent: {accent};">'
        f'<div class="rr-glass-label">{label}</div>'
        f'<div class="rr-glass-value">{value}</div>'
        f'{delta_html}'
        f'{note_html}'
        f'</div>'
    )
    col.markdown(html, unsafe_allow_html=True)


# ==================== KPI CARDS ====================
def _render_kpi(tbl):
    st.markdown("### 🛡️ Ringkasan Risiko")

    total = len(tbl)
    high = int((tbl["Level"] == "Tinggi").sum())
    medium = int((tbl["Level"] == "Sedang").sum())
    low = int((tbl["Level"] == "Rendah").sum())

    c1, c2, c3, c4 = st.columns(4)
    _glass_card(c1, "Total Risiko", str(total), "#8B5CF6",
                note="Terdaftar dalam register")
    _glass_card(c2, "🔴 Tinggi (≥6)", str(high), "#EF4444",
                delta=("Perlu aksi segera" if high > 0 else "Aman"),
                delta_color=("#EF4444" if high > 0 else "#10B981"))
    _glass_card(c3, "🟡 Sedang (3-5)", str(medium), "#F59E0B",
                note="Pantau berkala")
    _glass_card(c4, "🟢 Rendah (<3)", str(low), "#10B981",
                note="Terkendali")

    # Banner distribusi
    if high > 0:
        html = (
            f'<div class="rr-banner">'
            f'<div class="rr-block">'
            f'<div class="rr-block-label" style="color:#F87171;">🔴 RISIKO TINGGI</div>'
            f'<div class="rr-block-value">{high}</div>'
            f'<div class="rr-block-sub">Perlu tindakan segera</div>'
            f'</div>'
            f'<div class="rr-block">'
            f'<div class="rr-block-label" style="color:#FBBF24;">🟡 RISIKO SEDANG</div>'
            f'<div class="rr-block-value">{medium}</div>'
            f'<div class="rr-block-sub">Pantau berkala</div>'
            f'</div>'
            f'<div class="rr-block">'
            f'<div class="rr-block-label" style="color:#34D399;">🟢 RISIKO RENDAH</div>'
            f'<div class="rr-block-value">{low}</div>'
            f'<div class="rr-block-sub">Terkendali</div>'
            f'</div>'
            f'</div>'
        )
        st.markdown(html, unsafe_allow_html=True)
    else:
        html = (
            f'<div class="rr-banner">'
            f'<div class="rr-block">'
            f'<div class="rr-block-label" style="color:#34D399;">✅ STATUS RISIKO</div>'
            f'<div class="rr-block-value">Terkendali</div>'
            f'<div class="rr-block-sub">Tidak ada risiko level tinggi</div>'
            f'</div>'
            f'<div class="rr-block">'
            f'<div class="rr-block-label" style="color:#FBBF24;">🟡 SEDANG</div>'
            f'<div class="rr-block-value">{medium}</div>'
            f'<div class="rr-block-sub">Pantau berkala</div>'
            f'</div>'
            f'<div class="rr-block">'
            f'<div class="rr-block-label" style="color:#34D399;">🟢 RENDAH</div>'
            f'<div class="rr-block-value">{low}</div>'
            f'<div class="rr-block-sub">Terkendali</div>'
            f'</div>'
            f'</div>'
        )
        st.markdown(html, unsafe_allow_html=True)


# ==================== HEATMAP ====================
def _render_heatmap(tbl):
    st.markdown("### 🔥 Heat Map Risiko")
    st.caption("Probabilitas (x) × Dampak (y). Zona merah = prioritas tertinggi.")

    matrix = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
    for _, r in tbl.iterrows():
        try:
            p = int(r["Probability_Val"]) - 1
            i = int(r["Impact_Val"]) - 1
            if 0 <= p <= 2 and 0 <= i <= 2:
                matrix[i][p] += 1
        except (ValueError, TypeError, KeyError):
            pass

    z_score = [
        [1 * 1, 1 * 2, 1 * 3],
        [2 * 1, 2 * 2, 2 * 3],
        [3 * 1, 3 * 2, 3 * 3],
    ]

    text = [[str(v) if v > 0 else "" for v in row] for row in matrix]

    fig = go.Figure(go.Heatmap(
        z=z_score,
        x=["Low (1)", "Medium (2)", "High (3)"],
        y=["Low (1)", "Medium (2)", "High (3)"],
        colorscale=[
            [0.0, "#10B981"],
            [0.33, "#F59E0B"],
            [0.66, "#EF4444"],
            [1.0, "#991B1B"],
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
            tickfont=dict(size=12), side="bottom",
        ),
        yaxis=dict(
            title=dict(text="<b>Impact</b>", font=dict(size=13)),
            tickfont=dict(size=12),
        ),
        margin=dict(t=40, b=80, l=80, r=40),
    )
    st.plotly_chart(fig, use_container_width=True)


# ==================== RISK LIST ====================
def _render_risk_list(tbl):
    st.markdown("### 📋 Daftar Risiko")
    st.caption("Diurutkan berdasarkan skor (Probability × Impact).")

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

        risk_name = str(r.get("Risk", "—"))
        status = str(r.get("Status", "—"))
        p_val = int(r["Probability_Val"])
        i_val = int(r["Impact_Val"])

        html = (
            f'<div class="rr-risk-card" style="border-left: 5px solid {style["border"]};">'
            f'<div style="display:flex; justify-content:space-between; align-items:start;">'
            f'<div style="flex:1;">'
            f'<div class="rr-risk-name">{style["icon"]} {risk_name}</div>'
            f'<div class="rr-risk-meta">'
            f'<strong>Status:</strong> {status} · '
            f'<strong>Probability:</strong> {p_val} · '
            f'<strong>Impact:</strong> {i_val}'
            f'</div>'
            f'</div>'
            f'<div class="rr-risk-score" style="background:{style["bg"]}; color:{style["border"]}; margin-left:16px;">'
            f'<div class="rr-risk-score-label">SCORE</div>'
            f'<div class="rr-risk-score-value">{score}</div>'
            f'<div class="rr-risk-score-level">{level}</div>'
            f'</div>'
            f'</div>'
            f'</div>'
        )
        st.markdown(html, unsafe_allow_html=True)


# ==================== ACTION PLAN ====================
def _render_action_plan(tbl):
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


# ==================== MAIN ====================
def render(ds: Dataset, scope) -> None:
    _inject_css()

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

    # 1. KPI cards + Banner
    _render_kpi(tbl)

    st.markdown("---")

    # 2. Heat map + Distribusi bar (side by side)
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

        c1, c2 = st.columns(2)
        _glass_card(c1, "Rata-rata Score", f"{tbl['Score'].mean():.1f}",
                    "#8B5CF6", note="Skor rata-rata seluruh risiko")
        _glass_card(c2, "Max Score", f"{int(tbl['Score'].max())}",
                    "#EF4444", note="Skor tertinggi terdeteksi")

    st.markdown("---")

    # 3. Risk list
    _render_risk_list(tbl)

    # 4. Action plan
    _render_action_plan(tbl)