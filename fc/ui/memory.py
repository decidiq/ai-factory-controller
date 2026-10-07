"""Halaman Institutional Memory — pola keputusan user (BRD 8, Fase 3)."""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from .. import db
from ..intel.memory import (compute_stats, compute_weekly_trend,
                             generate_insights, get_all_decisions_with_outcome)
from .charts import CATEGORY_COLORS, COLORS, apply_theme


# ==================== HERO METRICS ====================

def _hero_card(icon: str, label: str, value: str, sub: str, color: str) -> str:
    """Generate HTML untuk hero metric card."""
    return f"""
    <div style="
        background: #FFFFFF;
        border: 1px solid #E9D5FF;
        border-left: 5px solid {color};
        border-radius: 14px;
        padding: 20px 22px;
        box-shadow: 0 2px 8px rgba(139, 92, 246, 0.06);
        height: 100%;
    ">
        <div style="
            font-size: 0.7rem;
            color: {color};
            font-weight: 700;
            letter-spacing: 0.8px;
            text-transform: uppercase;
            margin-bottom: 8px;
        ">{icon} {label}</div>
        <div style="
            font-size: 2rem;
            font-weight: 800;
            color: #0F172A;
            letter-spacing: -1px;
            line-height: 1.1;
        ">{value}</div>
        <div style="
            font-size: 0.8rem;
            color: #64748B;
            margin-top: 6px;
            font-weight: 500;
        ">{sub}</div>
    </div>
    """


def _render_hero(stats) -> None:
    """4 hero metric cards."""
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown(
            _hero_card("📊", "Total Keputusan", f"{stats.total}",
                       "Dari semua user", COLORS["primary"]),
            unsafe_allow_html=True,
        )

    with c2:
        if stats.total > 0:
            rate = stats.acceptance_rate
            if rate >= 60:
                color, sub = COLORS["success"], "🟢 Baik"
            elif rate >= 40:
                color, sub = COLORS["warning"], "🟡 Sedang"
            else:
                color, sub = COLORS["danger"], "🔴 Rendah"
            st.markdown(
                _hero_card("✅", "Acceptance Rate", f"{rate:.1f}%", sub, color),
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                _hero_card("✅", "Acceptance Rate", "—", "Belum ada data",
                           COLORS["text_muted"]),
                unsafe_allow_html=True,
            )

    with c3:
        st.markdown(
            _hero_card("👍", "Disetujui", f"{stats.approved}",
                       f"{stats.approved} dari {stats.total}", COLORS["success"]),
            unsafe_allow_html=True,
        )

    with c4:
        st.markdown(
            _hero_card("👎", "Ditolak", f"{stats.rejected}",
                       f"{stats.rejected} dari {stats.total}", COLORS["danger"]),
            unsafe_allow_html=True,
        )


def _render_impact(stats) -> None:
    """Card besar Cost Saving."""
    if stats.total_impact_rp <= 0:
        return

    impact = stats.total_impact_rp
    if impact >= 1_000_000_000:
        val = f"Rp {impact/1_000_000_000:.2f} M"
    elif impact >= 1_000_000:
        val = f"Rp {impact/1_000_000:.1f} jt"
    else:
        val = f"Rp {impact:,.0f}"

    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #8B5CF6 0%, #EC4899 100%);
        color: #FFFFFF;
        padding: 26px 30px;
        border-radius: 16px;
        box-shadow: 0 10px 30px rgba(139, 92, 246, 0.25);
        margin: 20px 0;
    ">
        <div style="
            font-size: 0.75rem;
            letter-spacing: 1.5px;
            opacity: 0.9;
            font-weight: 700;
            margin-bottom: 8px;
        ">💰 COST SAVING DARI KEPUTUSAN ANDA</div>
        <div style="
            font-size: 2.6rem;
            font-weight: 800;
            letter-spacing: -1.5px;
            line-height: 1.1;
        ">{val}</div>
        <div style="
            font-size: 0.9rem;
            opacity: 0.9;
            margin-top: 10px;
        ">Dari <strong>{stats.approved}</strong> rekomendasi yang Anda setujui.
        Pastikan semuanya dieksekusi & diukur hasilnya.</div>
    </div>
    """, unsafe_allow_html=True)


# ==================== INSIGHTS ====================

def _render_insights(insights) -> None:
    """Insight cards premium — HTML kompak biar tidak ke-render sebagai teks."""
    if not insights:
        return

    st.markdown("### 🧠 AI Insight dari Keputusan Anda")

    for ins in insights:
        metric_html = ""
        if ins.metric:
            metric_html = (
                f'<div style="background:#F5F3FF;color:#6D28D9;padding:10px 16px;'
                f'border-radius:8px;font-weight:700;font-size:0.85rem;'
                f'white-space:nowrap;margin-left:16px;">{ins.metric}</div>'
            )

        html = (
            f'<div style="background:#FFFFFF;border:1px solid #E9D5FF;'
            f'border-left:4px solid {COLORS["primary"]};border-radius:12px;'
            f'padding:18px 22px;margin-bottom:12px;'
            f'box-shadow:0 2px 6px rgba(139,92,246,0.05);">'
            f'<div style="display:flex;justify-content:space-between;align-items:start;">'
            f'<div style="flex:1;">'
            f'<div style="font-size:1.05rem;font-weight:700;color:#1E1B4B;'
            f'margin-bottom:6px;letter-spacing:-0.2px;">{ins.icon} {ins.title}</div>'
            f'<div style="font-size:0.9rem;color:#475569;line-height:1.55;">'
            f'{ins.description}</div>'
            f'</div>'
            f'{metric_html}'
            f'</div>'
            f'</div>'
        )

        st.markdown(html, unsafe_allow_html=True)
        
# ==================== WEEKLY TREND ====================

def _render_trend() -> None:
    st.markdown("### 📈 Performance Trend")
    st.caption("Keputusan Anda dalam 8 minggu terakhir.")

    try:
        trend = compute_weekly_trend(weeks=8)
    except Exception as e:
        st.warning(f"Tidak dapat memuat tren: {e}")
        return

    if not trend:
        st.info("Belum ada data tren. Buat beberapa keputusan dulu.")
        return

    df = pd.DataFrame(trend)

    if df["total"].sum() == 0:
        st.info("Belum ada keputusan dalam 8 minggu terakhir.")
        return

    # Stacked bar dengan label
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=df["week"], y=df["approved"],
        name="Disetujui",
        marker=dict(color=COLORS["success"], line=dict(width=0)),
        text=[f"<b>{v}</b>" if v > 0 else "" for v in df["approved"]],
        textposition="inside",
        textfont=dict(size=11, color="#FFFFFF", family="Inter"),
        hovertemplate="<b>%{x}</b><br>Disetujui: %{y}<extra></extra>",
    ))

    fig.add_trace(go.Bar(
        x=df["week"], y=df["rejected"],
        name="Ditolak",
        marker=dict(color=COLORS["danger"], line=dict(width=0)),
        text=[f"<b>{v}</b>" if v > 0 else "" for v in df["rejected"]],
        textposition="inside",
        textfont=dict(size=11, color="#FFFFFF", family="Inter"),
        hovertemplate="<b>%{x}</b><br>Ditolak: %{y}<extra></extra>",
    ))

    # Total label di atas
    for _, row in df.iterrows():
        if row["total"] > 0:
            fig.add_annotation(
                x=row["week"], y=row["total"],
                text=f"<b>{row['total']}</b>",
                showarrow=False, yshift=12,
                font=dict(size=10, color=COLORS["text"], family="Inter"),
            )

    fig = apply_theme(fig, height=360)
    fig.update_layout(
        barmode="stack",
        yaxis_title="<b>Jumlah Keputusan</b>",
        xaxis_title="",
        legend=dict(orientation="h", y=-0.15, x=0.5, xanchor="center"),
        margin=dict(t=40, b=60, l=60, r=40),
    )
    st.plotly_chart(fig, use_container_width=True)


# ==================== CATEGORY BREAKDOWN ====================

def _render_category(stats) -> None:
    if not stats.top_categories:
        return

    st.markdown("### 🎯 Kategori Rekomendasi")

    df = pd.DataFrame(stats.top_categories, columns=["Kategori", "Jumlah"])

    label_map = {
        "yield": "Yield", "scrap": "Scrap", "oee": "OEE",
        "cost": "Cost Saving", "utility": "Utility",
        "inventory": "Inventory", "dead_stock": "Dead Stock",
        "supplier": "Supplier", "other": "Lainnya",
    }
    df["Kategori"] = df["Kategori"].map(lambda k: label_map.get(k, k.title()))

    c1, c2 = st.columns([1.3, 1])

    with c1:
        fig = go.Figure(go.Pie(
            labels=df["Kategori"],
            values=df["Jumlah"],
            hole=0.55,
            marker=dict(
                colors=CATEGORY_COLORS[:len(df)],
                line=dict(color="#FFFFFF", width=3),
            ),
            textinfo="label+percent",
            textposition="inside",
            textfont=dict(size=11, color="#FFFFFF", family="Inter"),
            hovertemplate="<b>%{label}</b><br>%{value} rekomendasi<br>%{percent}<extra></extra>",
        ))

        total = df["Jumlah"].sum()
        fig.add_annotation(
            text=f"<b>{total}</b><br><span style='font-size:9px;color:#94A3B8'>TOTAL</span>",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=18, color=COLORS["text"], family="Inter"),
        )

        fig = apply_theme(fig, height=340)
        fig.update_layout(
            showlegend=False,
            margin=dict(t=20, b=20, l=20, r=20),
        )
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.markdown("**Detail Kategori:**")
        df_display = df.rename(columns={"Kategori": "Kategori", "Jumlah": "Jumlah"})
        df_display["Porsi"] = (df_display["Jumlah"] / df_display["Jumlah"].sum() * 100).round(1)
        df_display["Porsi"] = df_display["Porsi"].apply(lambda x: f"{x}%")
        st.dataframe(df_display, use_container_width=True, hide_index=True, height=340)


# ==================== DECISIONS LOG ====================

def _render_log() -> None:
    st.markdown("### 📋 Log Keputusan")
    st.caption("Semua keputusan user tercatat permanen di database.")

    try:
        rows = get_all_decisions_with_outcome(limit=200)
    except Exception as e:
        st.warning(f"Tidak dapat memuat log: {e}")
        return

    if not rows:
        st.info("Belum ada keputusan tercatat.")
        return

    df = pd.DataFrame(rows)

    cols = [c for c in ("timestamp", "user", "recommendation",
                        "decision", "notes", "outcome_30d",
                        "outcome_60d", "outcome_90d")
            if c in df.columns]
    df = df[cols]

    rename = {
        "timestamp": "Waktu", "user": "User",
        "recommendation": "Rekomendasi", "decision": "Keputusan",
        "notes": "Catatan", "outcome_30d": "Hasil 30 Hari",
        "outcome_60d": "Hasil 60 Hari", "outcome_90d": "Hasil 90 Hari",
    }
    df = df.rename(columns=rename)

    if "Keputusan" in df.columns:
        df["Keputusan"] = df["Keputusan"].map(lambda d:
            "✅ Disetujui" if "approve" in str(d).lower() else
            "❌ Ditolak" if "reject" in str(d).lower() else str(d))

    st.dataframe(df, use_container_width=True, hide_index=True)


# ==================== OUTCOME TRACKER ====================

def _render_outcome() -> None:
    st.markdown("### 📝 Update Outcome Keputusan")
    st.caption("Catat hasil nyata dari keputusan yang sudah dieksekusi.")

    try:
        rows = get_all_decisions_with_outcome(limit=50)
    except Exception:
        rows = []

    if not rows:
        st.info("Belum ada keputusan untuk di-update.")
        return

    options = {
        f"#{r['id']} — {r['recommendation'][:60]}": r["id"]
        for r in rows
    }

    c1, c2, c3 = st.columns([2, 1, 2])

    with c1:
        selected = st.selectbox("Pilih Keputusan", list(options.keys()))
        decision_id = options[selected]

    with c2:
        days = st.selectbox("Periode", [30, 60, 90], index=0)

    with c3:
        outcome = st.text_input(
            "Hasil Nyata (opsional)",
            placeholder="mis. Yield naik 1,2 pp",
        )

    if st.button("💾 Simpan Outcome", type="primary"):
        if outcome.strip():
            from ..intel.memory import update_outcome
            if update_outcome(decision_id, days, outcome.strip()):
                st.success(f"✅ Outcome {days} hari untuk #{decision_id} disimpan.")
                st.rerun()
            else:
                st.error("Gagal menyimpan outcome.")
        else:
            st.warning("Masukkan hasil nyata dulu.")


# ==================== MAIN ====================

def render(ds, scope) -> None:
    st.title("🧠 Institutional Memory")
    st.caption(
        "AI belajar dari keputusan Anda. Semakin banyak keputusan, "
        "semakin pintar rekomendasi ke depannya (BRD 8, Fase 3)."
    )

    try:
        stats = compute_stats(limit=500)
    except Exception as e:
        st.error(f"Gagal memuat statistik: {e}")
        return

    # Hero metrics
    _render_hero(stats)

    # Impact card
    if stats.approved > 0:
        _render_impact(stats)

    st.markdown("---")

    # Insights
    try:
        insights = generate_insights(stats, min_decisions=3)
        _render_insights(insights)
    except Exception as e:
        st.warning(f"Tidak dapat generate insight: {e}")

    st.markdown("---")

    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Performance Trend",
        "🎯 Kategori",
        "📋 Log Keputusan",
        "📝 Update Outcome",
    ])

    with tab1:
        _render_trend()

    with tab2:
        _render_category(stats)

    with tab3:
        _render_log()

    with tab4:
        _render_outcome()

    st.markdown("---")

    with st.expander("ℹ️ Cara kerja Institutional Memory"):
        st.markdown(
            "**Konsep:** Setiap keputusan Anda (approve/reject) dicatat di database. "
            "Sistem menganalisis pola untuk:\n\n"
            "- 📊 **Acceptance rate** — seberapa relevan rekomendasi kami\n"
            "- 🎯 **Kategori dominan** — area apa yang paling perlu perhatian\n"
            "- 💰 **Total impact** — berapa potensi Cost Saving dari keputusan Anda\n"
            "- 📈 **Trend** — pola keputusan dari minggu ke minggu\n\n"
            "**Ke depannya:** Sistem akan pakai data ini untuk "
            "**memprioritaskan rekomendasi** sesuai preferensi Anda.\n\n"
            "**Berdasarkan BRD 8 (Tata Kelola AI):** "
            "Semua keputusan lewat human-in-the-loop, dan tercatat permanen di audit trail."
        )