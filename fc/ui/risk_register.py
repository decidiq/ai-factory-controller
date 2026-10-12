"""Risk Register - data-driven dengan heat map (DARK)."""
import math

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from ..kpi import risk_table
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
        return f"{f:,.0f}".replace(",", ".")
    except (ValueError, TypeError):
        return str(v) if v is not None else "—"


GLASS_CSS = """
<style>
.rr-glass {
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
.rr-glass::before {
    content: '';
    position: absolute;
    top: 0; left: 17px;
    width: 35px; height: 3px;
    background: var(--accent, #a489ff);
    border-radius: 0 0 5px 5px;
}
.rr-glass:hover {
    transform: translateY(-2px);
    border-color: #8c79d7;
    box-shadow: 0 10px 24px rgba(8, 8, 33, 0.45);
}
.rr-glass-label {
    color: #b8bedb;
    font-weight: 600;
    font-size: 0.62rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 6px;
}
.rr-glass-value {
    color: #ffffff;
    font-weight: 800;
    font-size: 1.5rem;
    letter-spacing: -0.04em;
    line-height: 1.15;
    margin-bottom: 4px;
}
.rr-glass-note {
    color: #8793bc;
    font-size: 0.68rem;
    line-height: 1.3;
    margin-top: 6px;
}
.rr-glass-delta {
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.03em;
    margin-top: 6px;
    text-transform: uppercase;
}

.rr-banner {
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
.rr-banner::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 4px;
    background: linear-gradient(90deg, #ff9eaa 0%, #f7d578 50%, #77edb4 100%);
}
.rr-block { flex: 1; min-width: 160px; }
.rr-block-label {
    font-size: 0.62rem;
    font-weight: 800;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-bottom: 6px;
}
.rr-block-value {
    font-size: 1.6rem;
    font-weight: 800;
    color: #ffffff;
    letter-spacing: -0.04em;
    line-height: 1.15;
    margin-bottom: 4px;
}
.rr-block-sub {
    font-size: 0.75rem;
    color: #adb6d5;
}

.rr-risk-card {
    background: #1b1e3e;
    border: 1px solid #343858;
    border-radius: 12px;
    padding: 16px 20px;
    margin-bottom: 12px;
    box-shadow: 0 9px 30px rgba(6, 9, 23, 0.13);
    position: relative;
    transition: transform 0.15s ease, border-color 0.15s ease;
}
.rr-risk-card:hover {
    transform: translateX(4px);
    border-color: #8c79d7;
}
.rr-risk-name {
    font-size: 0.95rem;
    font-weight: 700;
    color: #f5f6ff;
    margin-bottom: 6px;
}
.rr-risk-meta {
    font-size: 0.78rem;
    color: #adb6d5;
}
.rr-risk-score {
    padding: 10px 18px;
    border-radius: 10px;
    text-align: center;
    min-width: 100px;
}
.rr-risk-score-label {
    font-size: 0.6rem;
    font-weight: 800;
    letter-spacing: 0.08em;
}
.rr-risk-score-value {
    font-size: 1.5rem;
    font-weight: 800;
    letter-spacing: -0.04em;
    line-height: 1;
    margin: 2px 0;
}
.rr-risk-score-level {
    font-size: 0.68rem;
    font-weight: 700;
    text-transform: uppercase;
}
</style>
"""


def _inject_css():
    st.markdown(GLASS_CSS, unsafe_allow_html=True)


def _glass_card(col, label: str, value: str, accent: str = "#a489ff",
                note: str = None, delta: str = None,
                delta_color: str = None) -> None:
    note_html = f'<div class="rr-glass-note">{note}</div>' if note else ""
    delta_html = ""
    if delta:
        c = delta_color or "#77edb4"
        delta_html = f'<div class="rr-glass-delta" style="color:{c};">{delta}</div>'
    html = (
        f'<div class="rr-glass" style="--accent: {accent};">'
        f'<div class="rr-glass-label">{label}</div>'
        f'<div class="rr-glass-value">{value}</div>'
        f'{delta_html}'
        f'{note_html}'
        f'</div>')
    col.markdown(html, unsafe_allow_html=True)


def _render_kpi(tbl):
    st.markdown("### 🛡️ Ringkasan Risiko")
    total = len(tbl)
    high = int((tbl["Level"] == "Tinggi").sum())
    medium = int((tbl["Level"] == "Sedang").sum())
    low = int((tbl["Level"] == "Rendah").sum())

    c1, c2, c3, c4 = st.columns(4, gap="medium")
    _glass_card(c1, "Total Risiko", str(total), "#a489ff",
                note="Terdaftar dalam register")
    _glass_card(c2, "🔴 Tinggi (≥6)", str(high), "#ff9eaa",
                delta=("Perlu aksi segera" if high > 0 else "Aman"),
                delta_color=("#ff9eaa" if high > 0 else "#77edb4"))
    _glass_card(c3, "🟡 Sedang (3-5)", str(medium), "#f7d578",
                note="Pantau berkala")
    _glass_card(c4, "🟢 Rendah (<3)", str(low), "#77edb4",
                note="Terkendali")

    if high > 0:
        html = (
            f'<div class="rr-banner">'
            f'<div class="rr-block">'
            f'<div class="rr-block-label" style="color:#ff9eaa;">🔴 RISIKO TINGGI</div>'
            f'<div class="rr-block-value">{high}</div>'
            f'<div class="rr-block-sub">Perlu tindakan segera</div>'
            f'</div>'
            f'<div class="rr-block">'
            f'<div class="rr-block-label" style="color:#f7d578;">🟡 RISIKO SEDANG</div>'
            f'<div class="rr-block-value">{medium}</div>'
            f'<div class="rr-block-sub">Pantau berkala</div>'
            f'</div>'
            f'<div class="rr-block">'
            f'<div class="rr-block-label" style="color:#77edb4;">🟢 RISIKO RENDAH</div>'
            f'<div class="rr-block-value">{low}</div>'
            f'<div class="rr-block-sub">Terkendali</div>'
            f'</div>'
            f'</div>')
    else:
        html = (
            f'<div class="rr-banner">'
            f'<div class="rr-block">'
            f'<div class="rr-block-label" style="color:#77edb4;">✅ STATUS RISIKO</div>'
            f'<div class="rr-block-value">Terkendali</div>'
            f'<div class="rr-block-sub">Tidak ada risiko level tinggi</div>'
            f'</div>'
            f'<div class="rr-block">'
            f'<div class="rr-block-label" style="color:#f7d578;">🟡 SEDANG</div>'
            f'<div class="rr-block-value">{medium}</div>'
            f'<div class="rr-block-sub">Pantau berkala</div>'
            f'</div>'
            f'<div class="rr-block">'
            f'<div class="rr-block-label" style="color:#77edb4;">🟢 RENDAH</div>'
            f'<div class="rr-block-value">{low}</div>'
            f'<div class="rr-block-sub">Terkendali</div>'
            f'</div>'
            f'</div>')
    st.markdown(html, unsafe_allow_html=True)


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

    z_score = [[1, 2, 3], [2, 4, 6], [3, 6, 9]]
    text = [[str(v) if v > 0 else "" for v in row] for row in matrix]

    fig = go.Figure(go.Heatmap(
        z=z_score,
        x=["Low (1)", "Medium (2)", "High (3)"],
        y=["Low (1)", "Medium (2)", "High (3)"],
        colorscale=[[0.0, "#77edb4"], [0.33, "#f7d578"],
                    [0.66, "#ff9eaa"], [1.0, "#991B1B"]],
        text=text, texttemplate="<b>%{text}</b>",
        textfont=dict(size=24, color="#FFFFFF", family="DM Sans"),
        hovertemplate=("<b>Probability:</b> %{x}<br>"
                       "<b>Impact:</b> %{y}<br>"
                       "<b>Score:</b> %{z}<extra></extra>"),
        showscale=False, xgap=3, ygap=3))
    fig = apply_theme(fig, height=420)
    fig.update_layout(
        xaxis=dict(title=dict(text="<b>Probability</b>", font=dict(size=13)),
                   tickfont=dict(size=12), side="bottom"),
        yaxis=dict(title=dict(text="<b>Impact</b>", font=dict(size=13)),
                   tickfont=dict(size=12)),
        margin=dict(t=40, b=80, l=80, r=40))
    st.plotly_chart(fig, width='stretch')


def _render_risk_list(tbl):
    st.markdown("### 📋 Daftar Risiko")
    st.caption("Diurutkan berdasarkan skor (Probability × Impact).")
    tbl_sorted = tbl.sort_values("Score", ascending=False).reset_index(drop=True)

    for _, r in tbl_sorted.iterrows():
        level = r["Level"]
        score = int(r["Score"])
        color_map = {
            "Tinggi": {"border": COLORS["danger"], "bg": "#35243a", "icon": "🔴"},
            "Sedang": {"border": COLORS["warning"], "bg": "#302b30", "icon": "🟡"},
            "Rendah": {"border": COLORS["success"], "bg": "#172d35", "icon": "🟢"}}
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
            f'</div>')
        st.markdown(html, unsafe_allow_html=True)


def _render_action_plan(tbl):
    st.markdown("---")
    st.markdown("### 💡 Action Plan")
    high_risks = tbl[tbl["Level"] == "Tinggi"]
    if high_risks.empty:
        st.success("✅ Tidak ada risiko level tinggi. Semua terkendali.")
        return
    st.warning(f"⚠️ **{len(high_risks)} risiko level TINGGI** perlu tindakan segera.")
    for _, r in high_risks.iterrows():
        with st.expander(f"🔴 {r['Risk']} — Score {int(r['Score'])}"):
            st.markdown(f"**Probability:** {int(r['Probability_Val'])} (1-3)")
            st.markdown(f"**Impact:** {int(r['Impact_Val'])} (1-3)")
            st.markdown(f"**Status:** {r.get('Status', '—')}")


def render(ds: Dataset, scope) -> None:
    _inject_css()
    from ..config import TARGETS as DEFAULT_TARGETS
    from ..kpi import summarize

    page_header(
        title="Risk Register",
        subtitle=(f"Sumber: {ds.report.source_label} · "
                  f"Pemantauan risiko operasional pabrik dengan heat map"),
        granularity="Snapshot",
        period_label=format_period_label(scope),
        icon="🛡️")

    targets = st.session_state.get("_targets") or DEFAULT_TARGETS
    try:
        s = summarize(ds, scope)
        score, status, color = compute_health_score(s, targets)
        mini_health_score(score, status, color)
    except Exception:
        pass

    st.markdown("""
    <div style="background: #242748;
        border-left: 4px solid #71d5e9;border-radius: 10px;padding: 14px 18px;
        margin: 12px 0 20px 0;display: flex;gap: 12px;align-items: start;">
        <div style="font-size: 1.2rem;flex-shrink:0;">ℹ️</div>
        <div style="font-size: 0.82rem;color: #dce0f4;line-height: 1.55;">
        <strong style="color:#71d5e9;">Standar Risk Register:</strong>
        Halaman ini menampilkan <strong>risiko yang masih aktif saat ini</strong>
        (bukan historis per bulan). Fokus: identifikasi & mitigasi risiko yang
        perlu ditangani <em>sekarang</em>.
        </div>
        </div>
    """, unsafe_allow_html=True)

    risk = ds.risk
    if risk is None or risk.empty:
        st.warning("Data Risk_Register tidak tersedia (sheet 'Risk_Register').")
        return
    if "Risk" not in risk.columns:
        st.error("Sheet Risk_Register harus punya kolom **Risk**.")
        st.dataframe(risk.head(20), width='stretch')
        return
    if not {"Probability_Val", "Impact_Val"} <= set(risk.columns):
        st.error("Sheet Risk_Register butuh **Probability_Val** & **Impact_Val** (skala 1-3).")
        st.dataframe(risk, width='stretch', hide_index=True)
        return

    tbl = risk_table(risk)
    _render_kpi(tbl)
    st.markdown("---")

    col_left, col_right = st.columns([1, 1.2], gap="medium")
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
            x=level_counts["Level"], y=level_counts["Jumlah"],
            marker=dict(color=colors, line=dict(width=0)),
            text=[f"<b>{v}</b>" for v in level_counts["Jumlah"]],
            textposition="outside",
            textfont=dict(size=13, color=COLORS["text"], family="DM Sans"),
            cliponaxis=False))
        fig = apply_theme(fig, height=300)
        fig.update_layout(showlegend=False,
                          yaxis_title="<b>Jumlah</b>", xaxis_title="")
        st.plotly_chart(fig, width='stretch')

        c1, c2 = st.columns(2, gap="medium")
        _glass_card(c1, "Rata-rata Score", f"{tbl['Score'].mean():.1f}",
                    "#a489ff", note="Skor rata-rata seluruh risiko")
        _glass_card(c2, "Max Score", f"{int(tbl['Score'].max())}",
                    "#ff9eaa", note="Skor tertinggi terdeteksi")

    st.markdown("---")
    _render_risk_list(tbl)
    _render_action_plan(tbl)