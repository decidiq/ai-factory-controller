"""Halaman Cost DNA — variance decomposition & waterfall premium."""
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
)


# ==================== CSS ====================
GLASS_CSS = """
<style>
.dna-glass {
    position: relative;
    background: linear-gradient(135deg, #FFFFFF 0%, #F5F3FF 100%);
    border: 1px solid rgba(196, 181, 253, 0.5);
    border-radius: 16px;
    padding: 18px 20px;
    box-shadow: 0 6px 20px rgba(139, 92, 246, 0.08);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    overflow: hidden;
    min-height: 108px;
    margin-bottom: 8px;
}
.dna-glass::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, var(--accent, #8B5CF6) 0%, #EC4899 100%);
}
.dna-glass:hover {
    transform: translateY(-3px);
    box-shadow: 0 16px 32px rgba(139, 92, 246, 0.18);
    border-color: rgba(139, 92, 246, 0.6);
}
.dna-glass-label {
    color: #6D28D9;
    font-weight: 700;
    font-size: 0.68rem;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    margin-bottom: 6px;
}
.dna-glass-value {
    color: #0F172A;
    font-weight: 800;
    font-size: 1.5rem;
    letter-spacing: -0.5px;
    line-height: 1.1;
    margin-bottom: 4px;
}
.dna-glass-delta {
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.3px;
}
.dna-glass-note {
    color: #94A3B8;
    font-size: 0.68rem;
    font-style: italic;
    line-height: 1.3;
}

.penyebab-banner {
    background: linear-gradient(135deg, #0F172A 0%, #1E1B4B 100%);
    border-radius: 16px;
    padding: 24px 30px;
    color: white;
    box-shadow: 0 12px 32px rgba(30, 27, 75, 0.25);
    border: 1px solid rgba(139, 92, 246, 0.3);
    margin-top: 20px;
    position: relative;
    overflow: hidden;
}
.penyebab-banner::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 4px;
    background: linear-gradient(90deg, #F59E0B 0%, #EC4899 100%);
}
.penyebab-label {
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 1.5px;
    color: #FBBF24;
    text-transform: uppercase;
    margin-bottom: 8px;
}
.penyebab-title {
    font-size: 1.6rem;
    font-weight: 900;
    color: #FFFFFF;
    letter-spacing: -0.5px;
    line-height: 1.1;
    margin-bottom: 8px;
}
.penyebab-desc {
    font-size: 0.95rem;
    color: #C4B5FD;
}
.penyebab-desc strong { color: #FBBF24; }
</style>
"""


def _inject_css():
    st.markdown(GLASS_CSS, unsafe_allow_html=True)


def _active_targets():
    return st.session_state.get("_targets") or DEFAULT_TARGETS


@st.cache_data(show_spinner=False)
def _cached_decompose(curr_df: pd.DataFrame, prev_df: pd.DataFrame, plant):
    return decompose_variance(curr_df, prev_df, scope_plant=plant)


def _fmt_rp(v: float) -> str:
    if abs(v) >= 1_000_000_000:
        return f"Rp {v/1_000_000_000:.2f} M"
    if abs(v) >= 1_000_000:
        return f"Rp {v/1_000_000:.1f} jt"
    return f"Rp {v:,.0f}"


def _glass_metric(col, label: str, value: str, delta: str = None,
                  delta_color: str = None, accent: str = "#8B5CF6",
                  note: str = None) -> None:
    delta_html = ""
    if delta is not None:
        color = delta_color or "#10B981"
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


# ==================== KPI CARDS ====================
def _render_kpi_cards(cogm_kpi, breakdown, dec=None):
    st.markdown("#### 📊 Ringkasan COGM")

    total = cogm_kpi.value
    n_comp = len(breakdown)
    top_comp = max(breakdown, key=breakdown.get) if breakdown else "—"
    top_val = breakdown.get(top_comp, 0)

    cols = st.columns(4)
    _glass_metric(cols[0], "Total COGM", _fmt_rp(total),
                  accent="#8B5CF6", note=f"Rp {total:,.0f}")
    _glass_metric(cols[1], "Komponen Biaya", f"{n_comp} kategori",
                  accent="#3B82F6", note="Kategori yang membentuk COGM")
    _glass_metric(cols[2], "Komponen Terbesar", top_comp,
                  accent="#EC4899", note=_fmt_rp(top_val))

    if dec is not None and abs(dec.total) > 1:
        is_up = dec.total > 0
        _glass_metric(cols[3], "Δ COGM (MoM)", _fmt_rp(dec.total),
                      delta=("▲ NAIK" if is_up else "▼ TURUN"),
                      delta_color=("#EF4444" if is_up else "#10B981"),
                      accent="#F59E0B")
    else:
        _glass_metric(cols[3], "Δ COGM (MoM)", "—",
                      accent="#94A3B8",
                      note="Pilih 2 periode untuk lihat perubahan")


# ==================== WATERFALL COGM ====================
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
        text=[f"<b>{c/1_000_000:,.0f} jt</b>" for c in df_c["Cost"]]
             + [f"<b>{df_c['Cost'].sum()/1_000_000:,.0f} jt</b>"],
        textposition="outside",
        textfont=dict(size=11, color=COLORS["text"], family="Inter"),
        connector={"line": {"color": "#C4B5FD", "width": 2, "dash": "dot"}},
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
        margin=dict(t=60, b=80, l=80, r=40),
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_composition(cogm_kpi, breakdown):
    st.markdown("#### 🥧 Komposisi Biaya")
    st.caption("Distribusi porsi setiap komponen terhadap COGM.")

    df_c = pd.DataFrame(
        list(breakdown.items()), columns=["Komponen", "Nilai"]
    ).sort_values("Nilai", ascending=False)

    total = df_c["Nilai"].sum()
    center_text = (f"Rp {total/1_000_000_000:.2f} M" if total >= 1e9
                   else f"Rp {total/1_000_000:.1f} jt")

    fig = px.pie(df_c, names="Komponen", values="Nilai", hole=0.55)
    fig = pie_chart(fig, height=420, center_text=center_text)
    fig.update_traces(
        textinfo="label+percent",
        textposition="inside",
        textfont=dict(size=11, color="#FFFFFF", family="Inter"),
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_detail_table(breakdown):
    with st.expander("📋 Lihat detail komponen biaya"):
        total = sum(breakdown.values())
        rows = []
        for cat, val in sorted(breakdown.items(), key=lambda x: -x[1]):
            pct = val / total * 100 if total else 0
            rows.append({
                "Komponen": cat,
                "Nilai (Rp)": f"Rp {val:,.0f}",
                "Porsi (%)": f"{pct:.1f}%",
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


# ==================== VARIANCE DECOMPOSITION ====================
def _render_variance_decomposition(ds, scope):
    st.markdown("#### 🔍 Variance Decomposition")
    st.caption("Urai perubahan COGM jadi harga, volume, mix, dan efisiensi.")

    periods = _periods(ds.raw_material)
    if len(periods) < 2:
        st.info("Butuh minimal **2 periode** di kolom **Period** sheet Raw_Material.")
        return None

    partials = detect_partial_periods(ds.production)

    c1, c2 = st.columns(2)
    p_prev = c1.selectbox("Periode Sebelumnya", periods,
                          index=max(0, len(periods) - 2), key="dna_prev_v2")
    p_curr = c2.selectbox("Periode Sekarang", periods,
                          index=len(periods) - 1, key="dna_curr_v2")

    # Warning kalau salah satu partial
    if p_prev in partials:
        partial_warning_banner({p_prev}, ds.production)
    if p_curr in partials:
        partial_warning_banner({p_curr}, ds.production)

    if p_prev == p_curr:
        st.warning("Pilih periode yang berbeda.")
        return None

    rm = ds.raw_material
    prev = rm[rm["Period"] == p_prev] if "Period" in rm.columns else pd.DataFrame()
    curr = rm[rm["Period"] == p_curr] if "Period" in rm.columns else pd.DataFrame()

    if prev.empty or curr.empty:
        st.info("Data Raw_Material untuk periode terpilih tidak tersedia.")
        return None

    dec = _cached_decompose(curr, prev, scope.plant)

    if abs(dec.total) < 1:
        st.success("Tidak ada perubahan signifikan pada COGM antara 2 periode.")
        return None

    cogm_prev = prev["Cost"].sum() if "Cost" in prev.columns else 0
    cogm_curr = curr["Cost"].sum() if "Cost" in curr.columns else 0
    is_up = dec.total > 0

    m1, m2, m3 = st.columns(3)
    _glass_metric(m1, f"COGM {p_prev}", _fmt_rp(cogm_prev),
                  accent="#94A3B8", note=f"Rp {cogm_prev:,.0f}")
    _glass_metric(m2, f"COGM {p_curr}", _fmt_rp(cogm_curr),
                  delta=f"Rp {cogm_curr - cogm_prev:+,.0f}",
                  delta_color=("#EF4444" if is_up else "#10B981"),
                  accent="#8B5CF6", note=f"Rp {cogm_curr:,.0f}")
    _glass_metric(m3, "Total Perubahan", _fmt_rp(dec.total),
                  delta=("▲ NAIK" if is_up else "▼ TURUN"),
                  delta_color=("#EF4444" if is_up else "#10B981"),
                  accent="#F59E0B")

    st.markdown("")

    # Waterfall Variance
    st.markdown("##### 🌊 Waterfall Variance")
    st.caption(f"Dari COGM {p_prev} → kontribusi tiap komponen → COGM {p_curr}.")

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

    labels = ["COGM " + p_prev] + [k for k, v in components] + ["COGM " + p_curr]
    measures = ["absolute"] + ["relative"] * len(components) + ["total"]
    values = [cogm_prev] + [v for k, v in components] + [cogm_curr]

    text_labels = []
    for i, v in enumerate(values):
        if measures[i] in ("absolute", "total"):
            text_labels.append(f"<b>Rp {v/1_000_000:,.0f} jt</b>")
        else:
            text_labels.append(f"<b>{'+' if v > 0 else ''}Rp {v/1_000_000:,.0f} jt</b>")

    fig = go.Figure(go.Waterfall(
        name="Variance", orientation="v", measure=measures,
        x=labels, y=values, text=text_labels, textposition="outside",
        textfont=dict(size=11, color=COLORS["text"], family="Inter"),
        connector={"line": {"color": "#94A3B8", "width": 2, "dash": "dot"}},
        increasing={"marker": {"color": COLORS["danger"], "line": {"width": 0}}},
        decreasing={"marker": {"color": COLORS["success"], "line": {"width": 0}}},
        totals={"marker": {"color": COLORS["primary"], "line": {"width": 0}}},
        hovertemplate="<b>%{x}</b><br>Rp %{y:,.0f}<extra></extra>",
    ))
    fig = apply_theme(fig, height=500)
    fig.update_layout(
        showlegend=False,
        yaxis=dict(title=dict(text="<b>Nilai COGM (Rp)</b>", font=dict(size=12)),
                   tickformat=",.0f", tickfont=dict(size=10)),
        xaxis=dict(title=dict(text="<b>Komponen</b>", font=dict(size=12)),
                   tickfont=dict(size=11)),
        margin=dict(t=60, b=80, l=80, r=40),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Pie Kontribusi
    st.markdown("##### 🥧 Kontribusi Tiap Komponen")
    st.caption("Porsi pengaruh masing-masing komponen terhadap total perubahan.")

    df_pie = pd.DataFrame([
        {"Komponen": k, "Pengaruh": abs(v), "Nilai": v}
        for k, v in components
    ])
    total_abs = df_pie["Pengaruh"].sum()
    df_pie["Porsi_%"] = df_pie["Pengaruh"] / total_abs * 100 if total_abs else 0

    col_pie, col_table = st.columns([1, 1.3])

    with col_pie:
        fig_pie = go.Figure(go.Pie(
            labels=df_pie["Komponen"], values=df_pie["Pengaruh"], hole=0.55,
            marker=dict(colors=CATEGORY_COLORS[:len(df_pie)],
                        line=dict(color="#FFFFFF", width=3)),
            textinfo="label+percent",
            textfont=dict(size=11, color="#FFFFFF", family="Inter"),
            hovertemplate="<b>%{label}</b><br>Rp %{value:,.0f}<br>%{percent}<extra></extra>",
        ))
        fig_pie.add_annotation(
            text=(f"<b>Rp {total_abs/1_000_000:,.0f} jt</b>"
                  f"<br><span style='font-size:9px;color:#94A3B8'>TOTAL |Δ|</span>"),
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=14, color=COLORS["text"], family="Inter"),
        )
        fig_pie = apply_theme(fig_pie, height=360)
        fig_pie.update_layout(showlegend=False, margin=dict(t=20, b=20, l=20, r=20))
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_table:
        df_table = df_pie.copy()
        df_table["Nilai_Fmt"] = df_table["Nilai"].apply(
            lambda x: f"+Rp {x:,.0f}" if x > 0 else f"−Rp {abs(x):,.0f}")
        df_table["Porsi_Fmt"] = df_table["Porsi_%"].apply(lambda x: f"{x:.1f}%")
        df_table["Arah"] = df_table["Nilai"].apply(
            lambda x: "🔴 Naik" if x > 0 else "🟢 Turun")

        st.markdown("**Detail Kontribusi:**")
        st.dataframe(
            df_table[["Komponen", "Nilai_Fmt", "Porsi_Fmt", "Arah"]].rename(columns={
                "Nilai_Fmt": "Nilai (Rp)", "Porsi_Fmt": "Porsi",
            }),
            use_container_width=True, hide_index=True,
        )

    # Detail per Material
    st.markdown("##### 📋 Detail Perubahan per Material")
    st.caption("Material mana yang paling berkontribusi terhadap perubahan?")

    if "Material" in prev.columns and "Material" in curr.columns:
        prev_agg = prev.groupby("Material", as_index=False).agg(
            Qty_Prev=("Qty_Kg", "sum"), Cost_Prev=("Cost", "sum"))
        curr_agg = curr.groupby("Material", as_index=False).agg(
            Qty_Curr=("Qty_Kg", "sum"), Cost_Curr=("Cost", "sum"))
        merged = prev_agg.merge(curr_agg, on="Material", how="outer").fillna(0)

        merged["Δ_Cost"] = merged["Cost_Curr"] - merged["Cost_Prev"]
        merged["Δ_Qty"] = merged["Qty_Curr"] - merged["Qty_Prev"]
        merged["Abs_Delta"] = merged["Δ_Cost"].abs()
        merged = merged.sort_values("Abs_Delta", ascending=False).drop(columns="Abs_Delta")

        display = pd.DataFrame({
            "Material": merged["Material"],
            "Qty Sebelum": merged["Qty_Prev"].apply(lambda x: f"{x:,.0f} kg"),
            "Qty Sekarang": merged["Qty_Curr"].apply(lambda x: f"{x:,.0f} kg"),
            "Δ Qty": merged["Δ_Qty"].apply(
                lambda x: f"+{x:,.0f} kg" if x >= 0 else f"−{abs(x):,.0f} kg"),
            "Cost Sebelum": merged["Cost_Prev"].apply(lambda x: f"Rp {x:,.0f}"),
            "Cost Sekarang": merged["Cost_Curr"].apply(lambda x: f"Rp {x:,.0f}"),
            "Δ Cost": merged["Δ_Cost"].apply(
                lambda x: f"+Rp {x:,.0f}" if x >= 0 else f"−Rp {abs(x):,.0f}"),
        })
        st.dataframe(display, use_container_width=True, hide_index=True)

    # Penyebab Utama
    top_k, top_v = max(dec.as_dict().items(), key=lambda kv: abs(kv[1]))
    pct = abs(top_v) / abs(dec.total) * 100 if dec.total else 0

    st.markdown(f"""
    <div class="penyebab-banner">
        <div class="penyebab-label">🎯 Penyebab Utama Perubahan COGM</div>
        <div class="penyebab-title">{top_k}</div>
        <div class="penyebab-desc">
            Kontribusi <strong>Rp {top_v:,.0f}</strong> ({pct:.0f}% dari total perubahan)
        </div>
    </div>
    """, unsafe_allow_html=True)

    return dec


# ==================== MAIN RENDER ====================
def render(ds: Dataset, scope: Scope) -> None:
    _inject_css()

    # ===== HEADER =====
    page_header(
        title="Cost DNA Engine",
        subtitle=(
            f"Sumber: {ds.report.source_label} · "
            f"Analisis mengapa biaya berubah (harga, volume, mix, efisiensi)"
        ),
        granularity="Multi",
        period_label=format_period_label(scope),
        icon="🧬",
    )

    if ds.costs is None or ds.costs.empty:
        st.warning("Data biaya tidak tersedia.")
        return

    # ===== MINI HEALTH SCORE =====
    targets = _active_targets()
    try:
        summary = summarize(ds, scope)
        score, status, color = compute_health_score(summary, targets)
        mini_health_score(score, status, color)
    except Exception:
        pass

    # ===== SECTION 1: TOTAL COGM =====
    section_divider(
        title="Total COGM",
        subtitle="Pilih periode di bawah untuk lihat breakdown bulan tertentu.",
        icon="📊",
        badge="TOTAL",
        color="#8B5CF6",
        bg1="#F5F3FF",
        bg2="#FFFFFF",
    )

    # ===== PERIOD SELECTOR =====
    selected_period, periods, partials = period_selector(
        ds, key="dna_period_selector",
    )

    # Warning kalau partial
    if selected_period and selected_period in partials:
        partial_warning_banner({selected_period}, ds.production)

    st.markdown("")

    # ===== FILTER DATA SESUAI PERIODE =====
    costs_f, prod_f = filter_dataset_by_period(ds, selected_period)

    # Hitung COGM
    cogm_kpi, breakdown = cogm_for_scope(costs_f, prod_f, scope)

    if not cogm_kpi.available or not breakdown:
        st.info(f"COGM tidak dapat dihitung: {cogm_kpi.note}")
        return

    # ===== PROYEKSI (kalau partial) =====
    if selected_period and selected_period in partials:
        proj = project_month_end_cogm(costs_f, prod_f, selected_period)
        render_projection_card(proj)

    # ===== HITUNG VARIANCE UNTUK KPI CARD =====
    dec_for_kpi = None
    if len(periods) >= 2 and selected_period is None:
        rm = ds.raw_material
        p_prev, p_curr = periods[-2], periods[-1]
        prev = rm[rm["Period"] == p_prev] if "Period" in rm.columns else pd.DataFrame()
        curr = rm[rm["Period"] == p_curr] if "Period" in rm.columns else pd.DataFrame()
        if not prev.empty and not curr.empty:
            dec_for_kpi = _cached_decompose(curr, prev, scope.plant)

    # KPI Cards
    _render_kpi_cards(cogm_kpi, breakdown, dec_for_kpi)

    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

    # Waterfall + Composition
    col_left, col_right = st.columns([1.6, 1])
    with col_left:
        _render_waterfall(cogm_kpi, breakdown)
    with col_right:
        _render_composition(cogm_kpi, breakdown)

    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
    _render_detail_table(breakdown)

    # ===== SECTION 2: VARIANCE BULANAN =====
    section_divider(
        title="Variance Bulanan",
        subtitle="Perbandingan bulan-ke-bulan. Urai perubahan COGM jadi harga, volume, mix, efisiensi.",
        icon="📆",
        badge="BULANAN",
        color="#8B5CF6",
        bg1="#F5F3FF",
        bg2="#FFFFFF",
    )

    _render_variance_decomposition(ds, scope)