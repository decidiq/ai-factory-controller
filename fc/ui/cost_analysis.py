"""Cost Analysis — COGM breakdown, Pareto, Cost/Kg trend premium."""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from ..config import TARGETS as DEFAULT_TARGETS, targets_from_config
from ..kpi import Scope, cogm_for_scope, cost_per_kg, scope_production, summarize
from ..pipeline import Dataset
from .charts import CATEGORY_COLORS, COLORS, apply_theme, pie_chart
from .components import (page_header, mini_health_score, format_period_label,
                         compute_health_score, section_divider)


# ==================== CSS GLASSMORPHISM ====================
GLASS_CSS = """
<style>
.ca-glass {
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
.ca-glass::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, var(--accent, #8B5CF6) 0%, #EC4899 100%);
}
.ca-glass:hover {
    transform: translateY(-3px);
    box-shadow: 0 16px 32px rgba(139, 92, 246, 0.18);
    border-color: rgba(139, 92, 246, 0.6);
}
.ca-glass-label {
    color: #6D28D9;
    font-weight: 700;
    font-size: 0.68rem;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    margin-bottom: 6px;
}
.ca-glass-value {
    color: #0F172A;
    font-weight: 800;
    font-size: 1.5rem;
    letter-spacing: -0.5px;
    line-height: 1.1;
    margin-bottom: 4px;
}
.ca-glass-note {
    color: #94A3B8;
    font-size: 0.68rem;
    font-style: italic;
    line-height: 1.3;
}
.ca-glass-delta {
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.3px;
}

/* Top Component Banner */
.top-banner {
    background: linear-gradient(135deg, #0F172A 0%, #1E1B4B 100%);
    border-radius: 16px;
    padding: 22px 28px;
    color: white;
    box-shadow: 0 12px 32px rgba(30, 27, 75, 0.25);
    border: 1px solid rgba(139, 92, 246, 0.3);
    margin-bottom: 20px;
    position: relative;
    overflow: hidden;
}
.top-banner::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 4px;
    background: linear-gradient(90deg, #F59E0B 0%, #EC4899 100%);
}
.top-label {
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 1.5px;
    color: #FBBF24;
    text-transform: uppercase;
    margin-bottom: 8px;
}
.top-title {
    font-size: 1.5rem;
    font-weight: 900;
    color: #FFFFFF;
    letter-spacing: -0.5px;
    line-height: 1.1;
    margin-bottom: 8px;
}
.top-desc {
    font-size: 0.92rem;
    color: #C4B5FD;
}
.top-desc strong { color: #FBBF24; }
</style>
"""


def _inject_css():
    st.markdown(GLASS_CSS, unsafe_allow_html=True)


# ==================== HELPERS ====================
def _active_targets():
    return st.session_state.get("_targets") or DEFAULT_TARGETS


def _fmt_rp(v: float) -> str:
    if abs(v) >= 1_000_000_000:
        return f"Rp {v/1_000_000_000:.2f} M"
    if abs(v) >= 1_000_000:
        return f"Rp {v/1_000_000:.1f} jt"
    return f"Rp {v:,.0f}"


@st.cache_data(show_spinner=False)
def _cached_cogm(_costs, _production, plant, line, start, end):
    scope = Scope(plant, line, start, end)
    return cogm_for_scope(_costs, _production, scope)


def _glass_card(col, label: str, value: str, accent: str = "#8B5CF6",
                note: str = None, delta: str = None,
                delta_color: str = None) -> None:
    note_html = f'<div class="ca-glass-note">{note}</div>' if note else ""
    delta_html = ""
    if delta:
        c = delta_color or "#10B981"
        delta_html = f'<div class="ca-glass-delta" style="color:{c};">{delta}</div>'
    html = (
        f'<div class="ca-glass" style="--accent: {accent};">'
        f'<div class="ca-glass-label">{label}</div>'
        f'<div class="ca-glass-value">{value}</div>'
        f'{delta_html}'
        f'{note_html}'
        f'</div>'
    )
    col.markdown(html, unsafe_allow_html=True)


# ==================== SECTION 1: TOTAL ====================
def _render_kpi(cogm_kpi, cpk, output_kg, targets, breakdown):
    st.markdown("#### 💰 Ringkasan Biaya Total")

    c1, c2, c3, c4 = st.columns(4)

    _glass_card(c1, "Total COGM", _fmt_rp(cogm_kpi.value),
                accent="#8B5CF6", note=f"Rp {cogm_kpi.value:,.0f}")

    _glass_card(c2, "Output", f"{output_kg:,.0f} Kg",
                accent="#3B82F6", note="Total produksi terfilter")

    if cpk.available:
        over = (targets.max_cost_per_kg > 0
                and cpk.value > targets.max_cost_per_kg)
        delta_txt = (f"Batas Rp {targets.max_cost_per_kg:,.0f}"
                     if targets.max_cost_per_kg > 0 else None)
        _glass_card(c3, "Cost/Kg", f"Rp {cpk.value:,.0f}",
                    accent="#EC4899", delta=delta_txt,
                    delta_color=("#EF4444" if over else "#10B981"))
    else:
        _glass_card(c3, "Cost/Kg", "—", accent="#94A3B8", note=cpk.note)

    if breakdown:
        top_cat, top_val = max(breakdown.items(), key=lambda kv: kv[1])
        _glass_card(c4, "Komponen Terbesar", top_cat,
                    accent="#F59E0B", note=_fmt_rp(top_val))
    else:
        _glass_card(c4, "Komponen Terbesar", "—", accent="#94A3B8")


def _render_top_banner(breakdown):
    if not breakdown:
        return
    top_cat, top_val = max(breakdown.items(), key=lambda kv: kv[1])
    total = sum(breakdown.values())
    pct = (top_val / total * 100) if total else 0

    st.markdown(f"""
    <div class="top-banner">
        <div class="top-label">🏆 Komponen Biaya Terbesar</div>
        <div class="top-title">{top_cat}</div>
        <div class="top-desc">
            Kontribusi <strong>{_fmt_rp(top_val)}</strong> ({pct:.1f}% dari total COGM)
        </div>
    </div>
    """, unsafe_allow_html=True)


def _render_cogm_breakdown(breakdown):
    st.markdown("#### 🥧 Komposisi COGM")
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
            use_container_width=True, hide_index=True, height=380,
        )


def _render_pareto(ds, scope):
    st.markdown("#### 📊 Pareto Material Top 10")
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
             .head(10).reset_index(drop=True))

    total_cost = top["Cost"].sum()
    top["Cumulative_Pct"] = (top["Cost"].cumsum() / total_cost * 100)
    top["Cost_Jt"] = top["Cost"] / 1_000_000

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=top["Material"], y=top["Cost_Jt"], name="Cost (Rp jt)",
        marker=dict(color=COLORS["primary"], line=dict(width=0)),
        text=[f"<b>Rp {c:,.0f} jt</b>" for c in top["Cost_Jt"]],
        textposition="outside",
        textfont=dict(size=10, color=COLORS["text"], family="Inter"),
        cliponaxis=False,
        hovertemplate="<b>%{x}</b><br>Rp %{y:,.0f} jt<extra></extra>",
        yaxis="y",
    ))

    fig.add_trace(go.Scatter(
        x=top["Material"], y=top["Cumulative_Pct"], name="Cumulative (%)",
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
        xaxis=dict(title=dict(text="<b>Material</b>", font=dict(size=12)),
                   tickfont=dict(size=10), tickangle=-30),
        yaxis=dict(title=dict(text="<b>Cost (Rp jt)</b>", font=dict(size=12)),
                   tickfont=dict(size=10, color=COLORS["primary"]),
                   title_font=dict(color=COLORS["primary"])),
        yaxis2=dict(title=dict(text="<b>Cumulative (%)</b>", font=dict(size=12)),
                    tickfont=dict(size=10, color=COLORS["accent"]),
                    title_font=dict(color=COLORS["accent"]),
                    overlaying="y", side="right", range=[0, 105], showgrid=False),
        margin=dict(t=40, b=120, l=70, r=70),
    )
    st.plotly_chart(fig, use_container_width=True)

    above_80 = (top["Cumulative_Pct"] <= 80).sum() + 1
    st.info(
        f"💡 **Insight:** {above_80} dari {len(top)} material teratas "
        f"berkontribusi hingga **80% dari total biaya material**. "
        f"Fokus negosiasi di sini!"
    )


# ==================== SECTION 2: TREND BULANAN ====================
def _render_cost_kg_trend(ds, scope):
    from .components import detect_partial_periods, partial_warning_banner

    st.markdown("#### 📈 Trend Cost/Kg per Bulan")
    st.caption("Perkembangan biaya per bulan. Bulan yang belum closing ditandai ⚠️ PARTIAL.")

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

    cost_by_period = c.groupby("Period", as_index=False)["Cost"].sum()
    prod = scope_production(ds.production, scope)
    if prod.empty or "Date" not in prod.columns:
        st.info("Tidak ada data produksi.")
        return

    prod_copy = prod.copy()
    prod_copy["Date"] = pd.to_datetime(prod_copy["Date"])
    prod_copy["Period"] = prod_copy["Date"].dt.strftime("%Y-%m")
    output_by_period = prod_copy.groupby("Period", as_index=False)["Output_Kg"].sum()

    merged = cost_by_period.merge(output_by_period, on="Period", how="inner")
    if merged.empty:
        st.info("Tidak dapat match periode biaya & produksi.")
        return

    merged["Cost_Per_Kg"] = merged["Cost"] / merged["Output_Kg"].replace(0, pd.NA)
    merged = merged.dropna(subset=["Cost_Per_Kg"]).sort_values("Period")

    if merged.empty:
        st.info("Cost/Kg tidak dapat dihitung.")
        return

    # ===== Deteksi partial =====
    partials = detect_partial_periods(prod)
    partial_warning_banner(partials, prod)

    # ===== Label & warna per bar =====
    # Konversi Period jadi label teks biasa (tanpa HTML) agar x-axis jadi category
    x_labels = []
    bar_colors = []
    custom_hover = []

    vmin = merged["Cost_Per_Kg"].min()
    vmax = merged["Cost_Per_Kg"].max()

    def _color_for(v):
        if vmax == vmin:
            return COLORS["primary"]
        ratio = (v - vmin) / (vmax - vmin)
        if ratio < 0.33:
            return COLORS["success"]
        elif ratio < 0.66:
            return COLORS["warning"]
        return COLORS["danger"]

    for _, row in merged.iterrows():
        p = row["Period"]
        v = row["Cost_Per_Kg"]
        if p in partials:
            x_labels.append(f"{p} ⚠️")  # tanpa HTML
            bar_colors.append("#FCD34D")  # kuning muda
            custom_hover.append(f"<b>{p}</b> (PARTIAL)<br>Cost/Kg: Rp {v:,.0f}<br>"
                                f"<i>Data belum lengkap 1 bulan</i>")
        else:
            x_labels.append(p)
            bar_colors.append(_color_for(v))
            custom_hover.append(f"<b>{p}</b><br>Cost/Kg: Rp {v:,.0f}")

    fig = go.Figure(go.Bar(
        x=x_labels,
        y=merged["Cost_Per_Kg"],
        marker=dict(color=bar_colors, line=dict(width=0)),
        text=[f"<b>Rp {v:,.0f}</b>" for v in merged["Cost_Per_Kg"]],
        textposition="outside",
        textfont=dict(size=11, color=COLORS["text"], family="Inter"),
        cliponaxis=False,
        customdata=custom_hover,
        hovertemplate="%{customdata}<extra></extra>",
    ))

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
        xaxis=dict(
            title="<b>Periode</b>",
            tickfont=dict(size=11),
            type="category",  # ⬅️ INI KUNCINYA
        ),
        margin=dict(t=40, b=70, l=80, r=100),
    )
    st.plotly_chart(fig, use_container_width=True)

    # ===== Insight =====
    if partials:
        final_periods = [p for p in merged["Period"] if p not in partials]
        if len(final_periods) >= 2:
            first, last = final_periods[0], final_periods[-1]
            v_first = float(merged[merged["Period"] == first]["Cost_Per_Kg"].iloc[0])
            v_last = float(merged[merged["Period"] == last]["Cost_Per_Kg"].iloc[0])
            delta_pct = ((v_last - v_first) / v_first * 100) if v_first else 0
            trend = "naik" if delta_pct > 0 else "turun"
            st.info(
                f"💡 **Tren (bulan closing):** Cost/Kg {trend} "
                f"**{abs(delta_pct):.1f}%** dari **{first}** (Rp {v_first:,.0f}) "
                f"ke **{last}** (Rp {v_last:,.0f}). "
                f"Bulan **{sorted(partials)[-1]}** belum masuk hitungan tren karena partial."
            )
# ==================== MAIN RENDER ====================
def render(ds: Dataset, scope: Scope) -> None:
    _inject_css()

    # ===== HEADER =====
    page_header(
        title="Cost Analysis",
        subtitle=(
            f"Sumber: {ds.report.source_label} · "
            f"Analisis COGM, Pareto material, dan trend Cost/Kg"
        ),
        granularity="Multi",
        period_label=format_period_label(scope),
        icon="💰",
    )

    if ds.costs is None or ds.costs.empty:
        st.warning("Data biaya tidak tersedia.")
        return

    targets = targets_from_config(ds.config)

    # ===== MINI HEALTH SCORE =====
    active_targets = _active_targets()
    try:
        summary = summarize(ds, scope)
        score, status, color = compute_health_score(summary, active_targets)
        mini_health_score(score, status, color)
    except Exception:
        pass

    # ===== SECTION 1: TOTAL =====
    section_divider(
        title="Biaya per Periode",
        subtitle="Pilih periode di bawah untuk lihat breakdown komponen bulan tertentu.",
        icon="📊",
        badge="TOTAL",
        color="#8B5CF6",
        bg1="#F5F3FF",
        bg2="#FFFFFF",
    )

    # ===== PERIODE SELECTOR =====
    from .components import detect_partial_periods

    if "Period" in ds.costs.columns:
        periods = sorted([str(p) for p in ds.costs["Period"].dropna().unique() if str(p).strip()])
    else:
        periods = []

    partials = detect_partial_periods(ds.production)

    options = ["📊 Semua Periode (Total)"]
    period_map = {"📊 Semua Periode (Total)": None}

    for p in periods:
        label = f"📅 {p}"
        if p in partials:
            label += "  ⚠️ PARTIAL"
        options.append(label)
        period_map[label] = p

    selected = st.selectbox(
        "🔍 Pilih Periode untuk Analisis Breakdown",
        options=options,
        index=0,
        key="cost_period_selector",
    )
    selected_period = period_map[selected]

    # ===== WARNING KALAU PARTIAL =====
    
    if selected_period and selected_period in partials:
        from .components import partial_warning_banner
        partial_warning_banner({selected_period}, ds.production)
    # Proyeksi COGM akhir bulan (kalau periode partial)
    if selected_period and selected_period in partials:
        from .components import project_month_end_cogm, render_projection_card
        # Siapkan data filtered
        _costs_f = ds.costs[ds.costs["Period"] == selected_period].copy()
        _prod_f = ds.production.copy()
        if "Date" in _prod_f.columns:
            _prod_f["Date"] = pd.to_datetime(_prod_f["Date"])
            _prod_f["Period"] = _prod_f["Date"].dt.strftime("%Y-%m")
            _prod_f = _prod_f[_prod_f["Period"] == selected_period]

        _proj = project_month_end_cogm(_costs_f, _prod_f, selected_period)
        render_projection_card(_proj)

    st.markdown("")

    # ===== HITUNG COGM UNTUK PERIODE TERPILIH =====
    if selected_period is None:
        # Total semua periode — pakai cache
        cogm_kpi, breakdown = _cached_cogm(
            ds.costs, ds.production,
            scope.plant, scope.line, scope.start, scope.end,
        )
        prod = scope_production(ds.production, scope)
        output_kg = float(prod["Output_Kg"].sum()) if len(prod) else 0.0
    else:
        # Filter ke periode terpilih — HITUNG LANGSUNG (tanpa cache)
        costs_filtered = ds.costs[ds.costs["Period"] == selected_period].copy()

        prod_filtered = ds.production.copy()
        if "Date" in prod_filtered.columns:
            prod_filtered["Date"] = pd.to_datetime(prod_filtered["Date"])
            prod_filtered["Period"] = prod_filtered["Date"].dt.strftime("%Y-%m")
            prod_filtered = prod_filtered[prod_filtered["Period"] == selected_period]

        # Hitung COGM langsung dari data yang sudah difilter
        from ..kpi import cogm_for_scope as _cogm_direct
        scope_filtered = Scope(scope.plant, scope.line, scope.start, scope.end)
        cogm_kpi, breakdown = _cogm_direct(costs_filtered, prod_filtered, scope_filtered)

        output_kg = float(prod_filtered["Output_Kg"].sum()) if len(prod_filtered) else 0.0

    if not cogm_kpi.available:
        st.info(f"COGM tidak dapat dihitung: {cogm_kpi.note}")
        return

    cpk = cost_per_kg(cogm_kpi, output_kg)

    _render_kpi(cogm_kpi, cpk, output_kg, targets, breakdown)
    _render_top_banner(breakdown)

    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

    if breakdown:
        _render_cogm_breakdown(breakdown)

    # Pareto hanya tampil di mode Total
    if selected_period is None:
        st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)
        _render_pareto(ds, scope)
    else:
        st.info(
            f"ℹ️ **Pareto Material** hanya tersedia di mode **Semua Periode (Total)**. "
            f"Kembali ke mode Total untuk melihat analisis 80/20."
        )

    # ===== SECTION 2: TREND BULANAN =====
    section_divider(
        title="Trend Bulanan",
        subtitle="Perkembangan biaya dari bulan ke bulan. Cocok untuk melihat tren jangka menengah.",
        icon="📆",
        badge="BULANAN",
        color="#8B5CF6",
        bg1="#F5F3FF",
        bg2="#FFFFFF",
    )

    _render_cost_kg_trend(ds, scope)