"""Halaman Cost DNA — variance decomposition & waterfall (DARK)."""
import math

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from ..config import TARGETS as DEFAULT_TARGETS
from ..intel.cost_dna import decompose_variance, waterfall_cogm
from ..kpi import Scope, cogm_for_scope, summarize
from ..pipeline import Dataset
from .charts import CATEGORY_COLORS, COLORS, apply_theme, pie_chart
from .components import (
    page_header, mini_health_score, format_period_label,
    compute_health_score, section_divider,
    detect_partial_periods, partial_warning_banner,
    period_selector, filter_dataset_by_period,
    project_month_end_cogm, render_projection_card,
    render_table,
)


# ==================== NUMBER FORMATTERS ====================
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


def _fmt_rp(v, compact: bool = False) -> str:
    try:
        if v is None: return "—"
        f = float(v)
        if math.isnan(f) or math.isinf(f): return "—"
        if compact:
            if abs(f) >= 1_000_000_000:
                return "Rp " + f"{f/1_000_000_000:.2f}".replace(".", ",") + " M"
            if abs(f) >= 1_000_000:
                return "Rp " + f"{f/1_000_000:.1f}".replace(".", ",") + " jt"
        return "Rp " + f"{f:,.0f}".replace(",", ".")
    except (ValueError, TypeError):
        return str(v) if v is not None else "—"


# ==================== CSS (DARK) ====================
GLASS_CSS = """
<style>
.dna-glass {
    position: relative;
    background: linear-gradient(145deg, #1a1d3d, #151933);
    border: 1px solid #343858;
    border-radius: 12px;
    padding: 18px 20px;
    box-shadow: 0 9px 30px rgba(6, 9, 23, 0.13);
    transition: transform 0.2s ease, border-color 0.2s ease;
    overflow: hidden;
    min-height: 110px;
    margin-bottom: 8px;
}
.dna-glass::before {
    content: '';
    position: absolute;
    top: 0; left: 17px;
    width: 35px; height: 3px;
    background: var(--accent, #a489ff);
    border-radius: 0 0 5px 5px;
}
.dna-glass:hover {
    transform: translateY(-2px);
    border-color: #8c79d7;
    box-shadow: 0 10px 24px rgba(8, 8, 33, 0.45);
}
.dna-glass-label {
    color: #b8bedb;
    font-weight: 600;
    font-size: 0.62rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 6px;
}
.dna-glass-value {
    color: #ffffff;
    font-weight: 800;
    font-size: 1.45rem;
    letter-spacing: -0.04em;
    line-height: 1.15;
    margin-bottom: 4px;
}
.dna-glass-delta {
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.03em;
    margin-top: 6px;
    text-transform: uppercase;
}
.dna-glass-note {
    color: #8793bc;
    font-size: 0.68rem;
    line-height: 1.3;
    margin-top: 6px;
}

.penyebab-banner {
    background: linear-gradient(110deg, #30265e, #211b47 55%, #171b3c);
    border-radius: 16px;
    padding: 24px 30px;
    color: #ffffff;
    box-shadow: 0 9px 30px rgba(6, 9, 23, 0.13);
    border: 1px solid #5e5090;
    margin-top: 20px;
    position: relative;
    overflow: hidden;
}
.penyebab-banner::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 4px;
    background: linear-gradient(90deg, #f7d578 0%, #71d5e9 100%);
}
.penyebab-label {
    font-size: 0.62rem;
    font-weight: 800;
    letter-spacing: 0.12em;
    color: #f7d578;
    text-transform: uppercase;
    margin-bottom: 8px;
}
.penyebab-title {
    font-size: 1.5rem;
    font-weight: 800;
    color: #ffffff;
    letter-spacing: -0.03em;
    line-height: 1.1;
    margin-bottom: 8px;
}
.penyebab-desc {
    font-size: 0.9rem;
    color: #dce0f4;
}
.penyebab-desc strong { color: #f7d578; }
</style>
"""


def _inject_css():
    st.markdown(GLASS_CSS, unsafe_allow_html=True)


def _active_targets():
    return st.session_state.get("_targets") or DEFAULT_TARGETS


@st.cache_data(show_spinner=False)
def _cached_decompose(curr_df: pd.DataFrame, prev_df: pd.DataFrame, plant):
    return decompose_variance(curr_df, prev_df, scope_plant=plant)


def _glass_metric(col, label: str, value: str, delta: str = None,
                  delta_color: str = None, accent: str = "#a489ff",
                  note: str = None) -> None:
    delta_html = ""
    if delta is not None:
        color = delta_color or "#77edb4"
        delta_html = f'<div class="dna-glass-delta" style="color:{color};">{delta}</div>'
    note_html = f'<div class="dna-glass-note">{note}</div>' if note else ""
    html = (
        f'<div class="dna-glass" style="--accent: {accent};">'
        f'<div class="dna-glass-label">{label}</div>'
        f'<div class="dna-glass-value">{value}</div>'
        f'{delta_html}'
        f'{note_html}'
        f'</div>'
    )
    col.markdown(html, unsafe_allow_html=True)


def _periods(df):
    if df is None or df.empty or "Period" not in df.columns:
        return []
    return sorted([str(p) for p in df["Period"].dropna().unique() if str(p).strip()])


# ==================== KPI ====================
def _render_kpi_cards(cogm_kpi, breakdown, dec=None):
    st.markdown("#### 📊 Ringkasan COGM")
    total = cogm_kpi.value
    n_comp = len(breakdown)
    top_comp = max(breakdown, key=breakdown.get) if breakdown else "—"
    top_val = breakdown.get(top_comp, 0)

    cols = st.columns(4, gap="medium")
    _glass_metric(cols[0], "Total COGM", _fmt_rp(total),
                  accent="#a489ff", note=f"Rp {_fmt_thousand(total)}")
    _glass_metric(cols[1], "Komponen Biaya", f"{n_comp} kategori",
                  accent="#71d5e9", note="Kategori yang membentuk COGM")
    _glass_metric(cols[2], "Komponen Terbesar", top_comp,
                  accent="#ec3f92", note=_fmt_rp(top_val))

    if dec is not None and abs(dec.total) > 1:
        is_up = dec.total > 0
        _glass_metric(cols[3], "Δ COGM (MoM)", _fmt_rp(dec.total),
                      delta=("▲ NAIK" if is_up else "▼ TURUN"),
                      delta_color=("#ff9eaa" if is_up else "#77edb4"),
                      accent="#f7d578")
    else:
        _glass_metric(cols[3], "Δ COGM (MoM)", "—", accent="#adb6d5",
                      note="Pilih 2 periode untuk lihat perubahan")


def _render_waterfall(cogm_kpi, breakdown):
    st.markdown("#### 🌊 Waterfall COGM")
    st.caption("Breakdown komponen biaya yang membentuk COGM.")

    df_c = waterfall_cogm(breakdown)
    if df_c.empty:
        st.info("Tidak ada breakdown komponen.")
        return

    fig = go.Figure(go.Waterfall(
        name="COGM", orientation="v",
        measure=["relative"] * len(df_c) + ["total"],
        x=list(df_c["Category"]) + ["<b>COGM Total</b>"],
        y=list(df_c["Cost"]) + [df_c["Cost"].sum()],
        text=[f"<b>{_fmt_thousand(c/1_000_000, 0)} jt</b>" for c in df_c["Cost"]]
             + [f"<b>{_fmt_thousand(df_c['Cost'].sum()/1_000_000, 0)} jt</b>"],
        textposition="outside",
        textfont=dict(size=11, color=COLORS["text"], family="DM Sans"),
        connector={"line": {"color": "#5e5090", "width": 2, "dash": "dot"}},
        increasing={"marker": {"color": COLORS["primary"], "line": {"width": 0}}},
        decreasing={"marker": {"color": COLORS["danger"], "line": {"width": 0}}},
        totals={"marker": {"color": COLORS["accent"], "line": {"width": 0}}},
        hovertemplate="<b>%{x}</b><br>Rp %{y:,.0f}<extra></extra>",
    ))
    fig = apply_theme(fig, height=520)
    fig.update_layout(
        showlegend=False,
        yaxis=dict(title=dict(text="<b>Nilai (Rp)</b>", font=dict(size=12)),
                   tickformat=",.0f", tickfont=dict(size=10)),
        xaxis=dict(title=dict(text="<b>Komponen Biaya</b>", font=dict(size=12)),
                   tickfont=dict(size=11)),
        margin=dict(t=60, b=80, l=80, r=40))
    st.plotly_chart(fig, width='stretch')


def _render_composition(cogm_kpi, breakdown):
    st.markdown("#### 🥧 Komposisi Biaya")
    st.caption("Distribusi porsi setiap komponen terhadap COGM.")

    df_c = pd.DataFrame(list(breakdown.items()), columns=["Komponen", "Nilai"]).sort_values("Nilai", ascending=False)
    total = df_c["Nilai"].sum()
    center_text = (f"Rp {total/1_000_000_000:.2f} M" if total >= 1e9
                   else f"Rp {total/1_000_000:.1f} jt")

    fig = px.pie(df_c, names="Komponen", values="Nilai", hole=0.55)
    fig = pie_chart(fig, height=420, center_text=center_text)
    fig.update_traces(textinfo="label+percent", textposition="inside",
                      textfont=dict(size=11, color="#FFFFFF", family="DM Sans"))
    st.plotly_chart(fig, width='stretch')


def _render_detail_table(breakdown):
    with st.expander("📋 Lihat detail komponen biaya"):
        total = sum(breakdown.values())
        rows = []
        for cat, val in sorted(breakdown.items(), key=lambda x: -x[1]):
            pct = val / total * 100 if total else 0
            rows.append({
                "Komponen": cat,
                "Nilai (Rp)": _fmt_rp(val),
                "Porsi (%)": _fmt_pct(pct, 1),
            })
        # render_table DI LUAR loop — cuma render 1x dengan semua baris
        if rows:
            render_table(pd.DataFrame(rows), max_height="300px")


# ==================== VARIANCE DECOMPOSITION ====================
def _render_variance_decomposition(ds, scope):
    st.markdown("#### 🔍 Variance Decomposition")
    st.caption("Urai perubahan COGM jadi harga, volume, mix, dan efisiensi.")

    periods = _periods(ds.raw_material)
    if len(periods) < 2:
        st.info("Butuh minimal **2 periode** di kolom **Period** sheet biaya.")
        return None

    partials = detect_partial_periods(ds.production)
    c1, c2 = st.columns(2, gap="medium")
    p_prev = c1.selectbox("Periode Sebelumnya", periods,
                          index=max(0, len(periods) - 2), key="dna_prev_v3")
    p_curr = c2.selectbox("Periode Sekarang", periods,
                          index=len(periods) - 1, key="dna_curr_v3")

    if p_prev in partials:
        partial_warning_banner({p_prev}, ds.production)
    if p_curr in partials:
        partial_warning_banner({p_curr}, ds.production)

    if p_prev == p_curr:
        st.warning("Pilih periode yang berbeda.")
        return None

    # ============================================================
    # SECTION A: BREAKDOWN PER KOMPONEN BIAYA (BARU)
    # ============================================================
    st.markdown("##### 📋 Variance per Komponen Biaya")
    st.caption(f"Perbandingan tiap komponen COGM antara **{p_prev}** dan **{p_curr}**.")

    from ..intel.cost_dna import component_variance_from_cogm
    comp_df = component_variance_from_cogm(ds, p_prev, p_curr, scope=scope)

    if comp_df.empty:
        st.info("Tidak ada perubahan komponen yang signifikan antar periode ini.")
    else:
        # Format untuk display
        comp_display = comp_df.copy()
        comp_display["Sebelum"] = comp_display["Sebelum"].apply(_fmt_rp)
        comp_display["Sekarang"] = comp_display["Sekarang"].apply(_fmt_rp)
        comp_display["Δ"] = comp_display["Δ"].apply(
            lambda x: f"+{_fmt_rp(x)}" if x > 0 else f"−{_fmt_rp(abs(x))}")
        comp_display["Δ %"] = comp_display["Δ %"].apply(
            lambda x: f"{x:+.1f}%".replace(".", ","))

        # Tampilkan total perubahan
        total_delta = comp_df["Δ"].sum()
        is_up = total_delta > 0
        st.markdown(
            f'<div style="background:#1b1e3e;border:1px solid #343858;'
            f'border-left:4px solid {"#ff9eaa" if is_up else "#77edb4"};'
            f'border-radius:10px;padding:12px 16px;margin:8px 0 16px 0;">'
            f'<div style="color:#adb6d5;font-size:0.68rem;font-weight:700;'
            f'letter-spacing:0.06em;text-transform:uppercase;">'
            f'Total Perubahan COGM</div>'
            f'<div style="color:#ffffff;font-size:1.3rem;font-weight:800;'
            f'margin-top:4px;">'
            f'{"+" if is_up else "−"}{_fmt_rp(abs(total_delta))}</div>'
            f'</div>',
            unsafe_allow_html=True)

        render_table(comp_display, max_height="400px")

    # ============================================================
    # SECTION B: DECOMPOSITION DRIVER (price/volume/mix/eff) — EXISTING
    # ============================================================
    st.markdown("##### 🎯 Analisis Driver Material")
    st.caption("Urai perubahan biaya **Material** jadi harga, volume, mix, dan efisiensi.")

    rm = ds.raw_material
    prev = rm[rm["Period"] == p_prev] if "Period" in rm.columns else pd.DataFrame()
    curr = rm[rm["Period"] == p_curr] if "Period" in rm.columns else pd.DataFrame()
    if prev.empty or curr.empty:
        st.info("Data Raw_Material untuk periode terpilih tidak tersedia.")
        return None

    dec = _cached_decompose(curr, prev, scope.plant)

    if abs(dec.total) < 1:
        st.success("Tidak ada perubahan signifikan pada biaya Material.")
        return None

    cogm_prev_mat = prev["Cost"].sum() if "Cost" in prev.columns else 0
    cogm_curr_mat = curr["Cost"].sum() if "Cost" in curr.columns else 0
    is_up = dec.total > 0

    m1, m2, m3 = st.columns(3, gap="medium")
    _glass_metric(m1, f"Material {p_prev}", _fmt_rp(cogm_prev_mat),
                  accent="#adb6d5", note=f"Rp {_fmt_thousand(cogm_prev_mat)}")
    _glass_metric(m2, f"Material {p_curr}", _fmt_rp(cogm_curr_mat),
                  delta=f"Rp {_fmt_thousand(cogm_curr_mat - cogm_prev_mat)}",
                  delta_color=("#ff9eaa" if is_up else "#77edb4"),
                  accent="#a489ff", note=f"Rp {_fmt_thousand(cogm_curr_mat)}")
    _glass_metric(m3, "Total Perubahan Material", _fmt_rp(dec.total),
                  delta=("▲ NAIK" if is_up else "▼ TURUN"),
                  delta_color=("#ff9eaa" if is_up else "#77edb4"),
                  accent="#f7d578")

    st.markdown("")

    # Waterfall Variance
    st.markdown("##### 🌊 Waterfall Variance (Material)")
    st.caption(f"Dari Material {p_prev} → kontribusi tiap driver → Material {p_curr}.")

    components = [
        ("Harga Material", dec.price),
        ("Volume Produksi", dec.volume),
        ("Mix Produk", dec.mix),
        ("Efisiensi", dec.efficiency),
    ]
    components = [(k, v) for k, v in components if abs(v) >= 1_000_000]

    if not components:
        st.info("Tidak ada komponen variance yang signifikan (≥ Rp 1 jt).")
        return dec

    labels = ["Material " + p_prev] + [k for k, v in components] + ["Material " + p_curr]
    measures = ["absolute"] + ["relative"] * len(components) + ["total"]
    values = [cogm_prev_mat] + [v for k, v in components] + [cogm_curr_mat]

    text_labels = []
    for i, v in enumerate(values):
        if measures[i] in ("absolute", "total"):
            text_labels.append(f"<b>Rp {_fmt_thousand(v/1_000_000, 0)} jt</b>")
        else:
            text_labels.append(f"<b>{'+' if v > 0 else ''}Rp {_fmt_thousand(v/1_000_000, 0)} jt</b>")

    fig = go.Figure(go.Waterfall(
        name="Variance", orientation="v", measure=measures,
        x=labels, y=values, text=text_labels, textposition="outside",
        textfont=dict(size=11, color=COLORS["text"], family="DM Sans"),
        connector={"line": {"color": "#5e5090", "width": 2, "dash": "dot"}},
        increasing={"marker": {"color": COLORS["danger"], "line": {"width": 0}}},
        decreasing={"marker": {"color": COLORS["success"], "line": {"width": 0}}},
        totals={"marker": {"color": COLORS["primary"], "line": {"width": 0}}},
        hovertemplate="<b>%{x}</b><br>Rp %{y:,.0f}<extra></extra>"))
    fig = apply_theme(fig, height=500)
    fig.update_layout(
        showlegend=False,
        yaxis=dict(title=dict(text="<b>Nilai Material (Rp)</b>", font=dict(size=12)),
                   tickformat=",.0f", tickfont=dict(size=10)),
        xaxis=dict(title=dict(text="<b>Driver</b>", font=dict(size=12)),
                   tickfont=dict(size=11)),
        margin=dict(t=60, b=80, l=80, r=40))
    st.plotly_chart(fig, width='stretch')

    # Pie Kontribusi
    st.markdown("##### 🥧 Kontribusi Tiap Driver Material")
    st.caption("Porsi pengaruh masing-masing driver terhadap total perubahan Material.")

    df_pie = pd.DataFrame([
        {"Komponen": k, "Pengaruh": abs(v), "Nilai": v} for k, v in components
    ])
    total_abs = df_pie["Pengaruh"].sum()
    df_pie["Porsi_%"] = df_pie["Pengaruh"] / total_abs * 100 if total_abs else 0

    col_pie, col_table = st.columns([1, 1.3], gap="medium")

    with col_pie:
        fig_pie = go.Figure(go.Pie(
            labels=df_pie["Komponen"], values=df_pie["Pengaruh"], hole=0.55,
            marker=dict(colors=CATEGORY_COLORS[:len(df_pie)],
                        line=dict(color="#0d1026", width=3)),
            textinfo="label+percent",
            textfont=dict(size=11, color="#FFFFFF", family="DM Sans"),
            hovertemplate="<b>%{label}</b><br>Rp %{value:,.0f}<br>%{percent}<extra></extra>"))
        fig_pie.add_annotation(
            text=(f"<b>Rp {_fmt_thousand(total_abs/1_000_000, 0)} jt</b>"
                  f"<br><span style='font-size:9px;color:#adb6d5'>TOTAL |Δ|</span>"),
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=14, color=COLORS["text"], family="DM Sans"))
        fig_pie = apply_theme(fig_pie, height=360)
        fig_pie.update_layout(showlegend=False, margin=dict(t=20, b=20, l=20, r=20))
        st.plotly_chart(fig_pie, width='stretch')

    with col_table:
        df_table = df_pie.copy()
        df_table["Nilai_Fmt"] = df_table["Nilai"].apply(
            lambda x: f"+{_fmt_rp(x)}" if x > 0 else f"−{_fmt_rp(abs(x))}")
        df_table["Porsi_Fmt"] = df_table["Porsi_%"].apply(lambda x: f"{x:.1f}%".replace(".", ","))
        df_table["Arah"] = df_table["Nilai"].apply(
            lambda x: "🔴 Naik" if x > 0 else "🟢 Turun")

        st.markdown("**Detail Kontribusi Driver:**")
        render_table(
            df_table[["Komponen", "Nilai_Fmt", "Porsi_Fmt", "Arah"]].rename(columns={
                "Nilai_Fmt": "Nilai (Rp)", "Porsi_Fmt": "Porsi"}),
            max_height="360px")

    # Penyebab utama
    top_k, top_v = max(dec.as_dict().items(), key=lambda kv: abs(kv[1]))
    pct = abs(top_v) / abs(dec.total) * 100 if dec.total else 0

    st.markdown(f"""
    <div class="penyebab-banner">
        <div class="penyebab-label">🎯 Driver Utama Perubahan Material</div>
        <div class="penyebab-title">{top_k}</div>
        <div class="penyebab-desc">
            Kontribusi <strong>{_fmt_rp(top_v)}</strong> ({_fmt_pct(pct, 0)} dari total perubahan Material)
        </div>
    </div>
    """, unsafe_allow_html=True)

    return dec

# ==================== MAIN ====================
def render(ds: Dataset, scope: Scope) -> None:
    _inject_css()
    page_header(
        title="Cost DNA Engine",
        subtitle=(f"Sumber: {ds.report.source_label} · "
                  f"Analisis mengapa biaya berubah (harga, volume, mix, efisiensi)"),
        granularity="Multi",
        period_label=format_period_label(scope),
        icon="🧬")

    if ds.costs is None or ds.costs.empty:
        st.warning("Data biaya tidak tersedia.")
        return

    targets = _active_targets()
    try:
        summary = summarize(ds, scope)
        score, status, color = compute_health_score(summary, targets)
        mini_health_score(score, status, color)
    except Exception:
        pass

    section_divider(
        title="Total COGM",
        subtitle="Pilih periode di bawah untuk lihat breakdown bulan tertentu.",
        icon="📊", badge="TOTAL", color="#a489ff",
        bg1="#242748", bg2="#1a1d3d")

    selected_period, periods, partials = period_selector(ds, key="dna_period_selector")

    if selected_period and selected_period in partials:
        partial_warning_banner({selected_period}, ds.production)

    st.markdown("")

    costs_f, prod_f = filter_dataset_by_period(ds, selected_period)
    cogm_kpi, breakdown = cogm_for_scope(costs_f, prod_f, scope)

    if not cogm_kpi.available or not breakdown:
        st.info(f"COGM tidak dapat dihitung: {cogm_kpi.note}")
        return

    if selected_period and selected_period in partials:
        proj = project_month_end_cogm(costs_f, prod_f, selected_period)
        render_projection_card(proj)

    dec_for_kpi = None
    if len(periods) >= 2 and selected_period is None:
        rm = ds.raw_material
        p_prev, p_curr = periods[-2], periods[-1]
        prev = rm[rm["Period"] == p_prev] if "Period" in rm.columns else pd.DataFrame()
        curr = rm[rm["Period"] == p_curr] if "Period" in rm.columns else pd.DataFrame()
        if not prev.empty and not curr.empty:
            dec_for_kpi = _cached_decompose(curr, prev, scope.plant)

    _render_kpi_cards(cogm_kpi, breakdown, dec_for_kpi)

    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

    col_left, col_right = st.columns([1.6, 1], gap="medium")
    with col_left:
        _render_waterfall(cogm_kpi, breakdown)
    with col_right:
        _render_composition(cogm_kpi, breakdown)

    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
    _render_detail_table(breakdown)

    section_divider(
        title="Variance Bulanan",
        subtitle="Perbandingan bulan-ke-bulan. Urai perubahan COGM jadi harga, volume, mix, efisiensi.",
        icon="📆", badge="BULANAN", color="#a489ff",
        bg1="#242748", bg2="#1a1d3d")

    _render_variance_decomposition(ds, scope)