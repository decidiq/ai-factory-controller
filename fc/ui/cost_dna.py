"""Halaman Cost DNA — variance decomposition & waterfall premium."""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from ..intel.cost_dna import decompose_variance, waterfall_cogm
from ..kpi import Scope, cogm_for_scope
from ..pipeline import Dataset
from .charts import CATEGORY_COLORS, COLORS, apply_theme, pie_chart


def _periods(df):
    if df is None or df.empty or "Period" not in df.columns:
        return []
    return sorted([str(p) for p in df["Period"].dropna().unique() if str(p).strip()])


def _render_kpi_cards(cogm_kpi, breakdown, dec=None):
    """KPI cards di atas dengan format Rupiah singkat."""
    st.markdown("### 📊 Ringkasan COGM")

    total = cogm_kpi.value
    n_comp = len(breakdown)
    top_comp = max(breakdown, key=breakdown.get) if breakdown else "—"
    top_val = breakdown.get(top_comp, 0)

    def _fmt_rp(v: float) -> str:
        """Format Rupiah singkat."""
        if abs(v) >= 1_000_000_000:
            return f"Rp {v/1_000_000_000:.2f} M"
        if abs(v) >= 1_000_000:
            return f"Rp {v/1_000_000:.1f} jt"
        return f"Rp {v:,.0f}"

    cols = st.columns(4)
    cols[0].metric("Total COGM", _fmt_rp(total),
                   help=f"Rp {total:,.0f}")
    cols[1].metric("Komponen", f"{n_comp} kategori")
    cols[2].metric(
        "Terbesar",
        f"{top_comp}",
        delta=f"{_fmt_rp(top_val)}",
        delta_color="off",
    )

    if dec is not None and abs(dec.total) > 1:
        cols[3].metric(
            "Δ COGM (MoM)",
            _fmt_rp(dec.total),
            delta=("Naik" if dec.total > 0 else "Turun"),
            delta_color="inverse" if dec.total > 0 else "normal",
            help=f"Rp {dec.total:,.0f}",
        )
    else:
        cols[3].metric("Δ COGM (MoM)", "—",
                       help="Pilih 2 periode untuk lihat perubahan")
        
def _render_waterfall(cogm_kpi, breakdown):
    """Waterfall COGM dengan label nilai."""
    st.markdown("### 🌊 Waterfall COGM")
    st.caption("Breakdown komponen biaya yang membentuk COGM total. Label = nilai per komponen.")

    df_c = waterfall_cogm(breakdown)

    if df_c.empty:
        st.info("Tidak ada breakdown komponen.")
        return

    fig = go.Figure(go.Waterfall(
        name="COGM",
        orientation="v",
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
        yaxis=dict(
            title=dict(text="<b>Nilai (Rp)</b>", font=dict(size=12)),
            tickformat=",.0f",
            tickfont=dict(size=10),
        ),
        xaxis=dict(
            title=dict(text="<b>Komponen Biaya</b>", font=dict(size=12)),
            tickfont=dict(size=11),
        ),
        margin=dict(t=60, b=80, l=80, r=40),
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_composition(cogm_kpi, breakdown):
    """Donut chart komposisi biaya."""
    st.markdown("### 🥧 Komposisi Biaya")
    st.caption("Distribusi porsi setiap komponen terhadap COGM total.")

    df_c = pd.DataFrame(
        list(breakdown.items()), columns=["Komponen", "Nilai"]
    ).sort_values("Nilai", ascending=False)

    total = df_c["Nilai"].sum()
    center_text = f"Rp {total/1_000_000_000:.2f} M" if total >= 1e9 else f"Rp {total/1_000_000:.1f} jt"

    fig = px.pie(df_c, names="Komponen", values="Nilai", hole=0.55)
    fig = pie_chart(fig, height=420, center_text=center_text)
    fig.update_traces(
        textinfo="label+percent",
        textposition="inside",
        textfont=dict(size=11, color="#FFFFFF", family="Inter"),
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_variance_decomposition(ds, scope):
    """Variance decomposition dengan WATERFALL + tabel per material."""
    st.markdown("### 🔍 Variance Decomposition")
    st.caption("Urai perubahan COGM jadi harga, volume, mix, dan efisiensi.")

    periods = _periods(ds.raw_material)
    if len(periods) < 2:
        st.info("Butuh minimal **2 periode** di kolom **Period** sheet Raw_Material.")
        return None

    c1, c2 = st.columns(2)
    p_prev = c1.selectbox(
        "Periode Sebelumnya", periods,
        index=max(0, len(periods) - 2),
        key="dna_prev_v2",
    )
    p_curr = c2.selectbox(
        "Periode Sekarang", periods,
        index=len(periods) - 1,
        key="dna_curr_v2",
    )

    if p_prev == p_curr:
        st.warning("Pilih periode yang berbeda.")
        return None

    rm = ds.raw_material
    prev = rm[rm["Period"] == p_prev] if "Period" in rm.columns else pd.DataFrame()
    curr = rm[rm["Period"] == p_curr] if "Period" in rm.columns else pd.DataFrame()

    if prev.empty or curr.empty:
        st.info("Data Raw_Material untuk periode terpilih tidak tersedia.")
        return None

    dec = decompose_variance(curr, prev, scope_plant=scope.plant)

    if abs(dec.total) < 1:
        st.success("Tidak ada perubahan signifikan pada COGM antara 2 periode.")
        return None

    # ==================== HEADER METRIC ====================
    # Hitung COGM prev & curr dari raw_material
    cogm_prev = prev["Cost"].sum() if "Cost" in prev.columns else 0
    cogm_curr = curr["Cost"].sum() if "Cost" in curr.columns else 0

    delta_color = COLORS["danger"] if dec.total > 0 else COLORS["success"]
    delta_icon = "▲" if dec.total > 0 else "▼"
    delta_label = "NAIK" if dec.total > 0 else "TURUN"

    # 3 metric cards
    m1, m2, m3 = st.columns(3)
    m1.metric(f"COGM {p_prev}", f"Rp {cogm_prev:,.0f}")
    m2.metric(f"COGM {p_curr}", f"Rp {cogm_curr:,.0f}",
              delta=f"Rp {cogm_curr - cogm_prev:+,.0f}",
              delta_color="inverse")
    m3.metric("Total Perubahan", f"Rp {dec.total:,.0f}",
              delta=f"{delta_icon} {delta_label}",
              delta_color="inverse" if dec.total > 0 else "normal")

    st.markdown("")

    # ==================== WATERFALL VARIANCE ====================
    st.markdown("#### 🌊 Waterfall Variance")
    st.caption(f"Dari COGM {p_prev} → kontribusi tiap komponen → COGM {p_curr}.")

    # Siapkan data untuk waterfall
    components = [
        ("Harga Material", dec.price),
        ("Volume Produksi", dec.volume),
        ("Mix Produk", dec.mix),
        ("Efisiensi", dec.efficiency),
    ]
    # Filter komponen yang signifikan (>= 1jt)
    components = [(k, v) for k, v in components if abs(v) >= 1_000_000]

    if not components:
        st.info("Tidak ada komponen variance yang signifikan (≥ Rp 1 jt).")
        return dec

    labels = ["COGM " + p_prev] + [k for k, v in components] + ["COGM " + p_curr]
    measures = ["absolute"] + ["relative"] * len(components) + ["total"]
    values = [cogm_prev] + [v for k, v in components] + [cogm_curr]

    # Warna: increasing = merah (naik biaya = jelek), decreasing = hijau
    text_labels = []
    for i, v in enumerate(values):
        if measures[i] == "absolute" or measures[i] == "total":
            text_labels.append(f"<b>Rp {v/1_000_000:,.0f} jt</b>")
        else:
            text_labels.append(f"<b>{'+' if v > 0 else ''}Rp {v/1_000_000:,.0f} jt</b>")

    fig = go.Figure(go.Waterfall(
        name="Variance",
        orientation="v",
        measure=measures,
        x=labels,
        y=values,
        text=text_labels,
        textposition="outside",
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
        yaxis=dict(
            title=dict(text="<b>Nilai COGM (Rp)</b>", font=dict(size=12)),
            tickformat=",.0f",
            tickfont=dict(size=10),
        ),
        xaxis=dict(
            title=dict(text="<b>Komponen</b>", font=dict(size=12)),
            tickfont=dict(size=11),
        ),
        margin=dict(t=60, b=80, l=80, r=40),
    )
    st.plotly_chart(fig, use_container_width=True)

    # ==================== PIE KONTRIBUSI ====================
    st.markdown("#### 🥧 Kontribusi Tiap Komponen")
    st.caption("Porsi pengaruh masing-masing komponen terhadap total perubahan.")

    df_pie = pd.DataFrame([
        {"Komponen": k, "Pengaruh": abs(v), "Nilai": v}
        for k, v in components
    ])

    total_abs = df_pie["Pengaruh"].sum()
    df_pie["Porsi_%"] = df_pie["Pengaruh"] / total_abs * 100

    col_pie, col_table = st.columns([1, 1.3])

    with col_pie:
        fig_pie = go.Figure(go.Pie(
            labels=df_pie["Komponen"],
            values=df_pie["Pengaruh"],
            hole=0.55,
            marker=dict(
                colors=CATEGORY_COLORS[:len(df_pie)],
                line=dict(color="#FFFFFF", width=3),
            ),
            textinfo="label+percent",
            textfont=dict(size=11, color="#FFFFFF", family="Inter"),
            hovertemplate="<b>%{label}</b><br>Rp %{value:,.0f}<br>%{percent}<extra></extra>",
        ))
        fig_pie.add_annotation(
            text=f"<b>Rp {total_abs/1_000_000:,.0f} jt</b><br><span style='font-size:9px;color:#94A3B8'>TOTAL |Δ|</span>",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=14, color=COLORS["text"], family="Inter"),
        )
        fig_pie = apply_theme(fig_pie, height=360)
        fig_pie.update_layout(
            showlegend=False,
            margin=dict(t=20, b=20, l=20, r=20),
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_table:
        df_table = df_pie.copy()
        df_table["Nilai_Fmt"] = df_table["Nilai"].apply(
            lambda x: f"+Rp {x:,.0f}" if x > 0 else f"−Rp {abs(x):,.0f}"
        )
        df_table["Porsi_Fmt"] = df_table["Porsi_%"].apply(lambda x: f"{x:.1f}%")
        df_table["Arah"] = df_table["Nilai"].apply(
            lambda x: "🔴 Naik" if x > 0 else "🟢 Turun"
        )

        st.markdown("**Detail Kontribusi:**")
        st.dataframe(
            df_table[["Komponen", "Nilai_Fmt", "Porsi_Fmt", "Arah"]].rename(columns={
                "Nilai_Fmt": "Nilai (Rp)",
                "Porsi_Fmt": "Porsi",
            }),
            use_container_width=True,
            hide_index=True,
        )

    # ==================== DETAIL PER MATERIAL ====================
    st.markdown("#### 📋 Detail Perubahan per Material")
    st.caption("Material mana yang paling berkontribusi terhadap perubahan?")

    if "Material" in prev.columns and "Material" in curr.columns:
        # Aggregate per material
        prev_agg = prev.groupby("Material", as_index=False).agg(
            Qty_Prev=("Qty_Kg", "sum"),
            Cost_Prev=("Cost", "sum"),
        )
        curr_agg = curr.groupby("Material", as_index=False).agg(
            Qty_Curr=("Qty_Kg", "sum"),
            Cost_Curr=("Cost", "sum"),
        )
        merged = prev_agg.merge(curr_agg, on="Material", how="outer").fillna(0)

        # Hitung delta
        merged["Δ_Cost"] = merged["Cost_Curr"] - merged["Cost_Prev"]
        merged["Δ_Qty"] = merged["Qty_Curr"] - merged["Qty_Prev"]
        merged["Δ_Cost_%"] = (merged["Δ_Cost"] / merged["Cost_Prev"].replace(0, pd.NA)) * 100

        # Sort by abs delta
        merged["Abs_Delta"] = merged["Δ_Cost"].abs()
        merged = merged.sort_values("Abs_Delta", ascending=False).drop(columns="Abs_Delta")

        # Format tabel
        display = pd.DataFrame({
            "Material": merged["Material"],
            "Qty Sebelum": merged["Qty_Prev"].apply(lambda x: f"{x:,.0f} kg"),
            "Qty Sekarang": merged["Qty_Curr"].apply(lambda x: f"{x:,.0f} kg"),
            "Δ Qty": merged["Δ_Qty"].apply(
                lambda x: f"+{x:,.0f} kg" if x >= 0 else f"−{abs(x):,.0f} kg"
            ),
            "Cost Sebelum": merged["Cost_Prev"].apply(lambda x: f"Rp {x:,.0f}"),
            "Cost Sekarang": merged["Cost_Curr"].apply(lambda x: f"Rp {x:,.0f}"),
            "Δ Cost": merged["Δ_Cost"].apply(
                lambda x: f"+Rp {x:,.0f}" if x >= 0 else f"−Rp {abs(x):,.0f}"
            ),
        })

        st.dataframe(display, use_container_width=True, hide_index=True)

    # ==================== PENYEBAB UTAMA ====================
    top_k, top_v = max(dec.as_dict().items(), key=lambda kv: abs(kv[1]))
    pct = abs(top_v) / abs(dec.total) * 100 if dec.total else 0

    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #FFFBEB 0%, #FEF3C7 100%);
        border-left: 4px solid {COLORS['warning']};
        padding: 18px 22px;
        border-radius: 10px;
        margin-top: 20px;
    ">
        <div style="
            font-size: 0.75rem;
            color: #92400E;
            font-weight: 700;
            letter-spacing: 0.8px;
        ">🎯 PENYEBAB UTAMA</div>
        <div style="
            font-size: 1.3rem;
            font-weight: 800;
            color: #78350F;
            margin-top: 6px;
            letter-spacing: -0.3px;
        ">{top_k}</div>
        <div style="
            font-size: 0.92rem;
            color: #92400E;
            margin-top: 6px;
        ">Kontribusi <strong>Rp {top_v:,.0f}</strong> ({pct:.0f}% dari total perubahan)</div>
    </div>
    """, unsafe_allow_html=True)

    return dec

def _render_detail_table(breakdown):
    """Tabel detail komponen."""
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


def render(ds: Dataset, scope: Scope) -> None:
    st.title("🧬 Cost DNA Engine")
    st.caption(
        "Analisis mengapa biaya berubah: urai variance menjadi "
        "**harga**, **volume**, **mix produk**, dan **efisiensi**."
    )

    if ds.costs is None or ds.costs.empty:
        st.warning("Data biaya tidak tersedia.")
        return

    # --- COGM Data ---
    cogm_kpi, breakdown = cogm_for_scope(ds.costs, ds.production, scope)

    if not cogm_kpi.available or not breakdown:
        st.info(f"COGM tidak dapat dihitung: {cogm_kpi.note}")
        return

    # Hitung variance dulu (untuk KPI card)
    dec_for_kpi = None
    periods = _periods(ds.raw_material)
    if len(periods) >= 2:
        rm = ds.raw_material
        p_prev = periods[-2]
        p_curr = periods[-1]
        prev = rm[rm["Period"] == p_prev] if "Period" in rm.columns else pd.DataFrame()
        curr = rm[rm["Period"] == p_curr] if "Period" in rm.columns else pd.DataFrame()
        if not prev.empty and not curr.empty:
            dec_for_kpi = decompose_variance(curr, prev, scope_plant=scope.plant)

    # --- 1. KPI Cards ---
    _render_kpi_cards(cogm_kpi, breakdown, dec_for_kpi)

    st.markdown("---")

    # --- 2. Waterfall + Composition (side by side) ---
    col_left, col_right = st.columns([1.6, 1])

    with col_left:
        _render_waterfall(cogm_kpi, breakdown)

    with col_right:
        _render_composition(cogm_kpi, breakdown)

    st.markdown("---")

    # --- 3. Variance Decomposition ---
    _render_variance_decomposition(ds, scope)

    st.markdown("---")

    # --- 4. Detail Table ---
    _render_detail_table(breakdown)