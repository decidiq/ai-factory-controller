"""Halaman Institutional Memory — pola keputusan user (BRD 8, Fase 3)."""
import datetime

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from .. import db
from ..intel.memory import (compute_stats, compute_weekly_trend,
                             generate_insights, get_all_decisions_with_outcome)


def _render_header(stats) -> None:
    """Kartu ringkasan di atas halaman."""
    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Total Keputusan", stats.total)

    if stats.total > 0:
        rate_delta = "🟢 Baik" if stats.acceptance_rate >= 60 else \
                     "🟡 Sedang" if stats.acceptance_rate >= 40 else "🔴 Rendah"
        c2.metric(
            "Acceptance Rate",
            f"{stats.acceptance_rate:.1f}%",
            delta=rate_delta,
            delta_color="normal" if stats.acceptance_rate >= 60 else
                        "off" if stats.acceptance_rate >= 40 else "inverse",
        )
    else:
        c2.metric("Acceptance Rate", "—")

    c3.metric("✅ Disetujui", stats.approved)
    c4.metric("❌ Ditolak", stats.rejected)


def _render_impact_card(stats) -> None:
    """Kartu dampak finansial."""
    if stats.total_impact_rp <= 0:
        return

    impact = stats.total_impact_rp
    if impact >= 1_000_000_000:
        val = f"Rp {impact/1_000_000_000:.2f} M"
    elif impact >= 1_000_000:
        val = f"Rp {impact/1_000_000:.1f} jt"
    else:
        val = f"Rp {impact:,.0f}"

    st.success(
        f"💰 **Total potensi penghematan dari keputusan yang disetujui: {val}**  \n"
        f"Dari {stats.approved} rekomendasi yang Anda approve. "
        f"Pastikan semuanya dieksekusi & diukur hasilnya."
    )


def _render_insights(insights) -> None:
    """Tampilkan insight dalam grid."""
    if not insights:
        return

    st.markdown("### 🧠 Insight Otomatis dari Keputusan Anda")

    for ins in insights:
        with st.container(border=True):
            c1, c2 = st.columns([3, 1])
            with c1:
                st.markdown(f"#### {ins.icon} {ins.title}")
                st.markdown(ins.description)
            with c2:
                if ins.metric:
                    st.metric("Metrik", ins.metric)


def _render_weekly_trend() -> None:
    """Chart trend keputusan per minggu."""
    st.markdown("### 📈 Tren Keputusan (8 Minggu Terakhir)")

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

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df["week"], y=df["approved"],
        name="Disetujui", marker_color="#16a34a",
    ))
    fig.add_trace(go.Bar(
        x=df["week"], y=df["rejected"],
        name="Ditolak", marker_color="#dc2626",
    ))
    fig.update_layout(
        barmode="stack",
        height=320,
        margin=dict(t=20, b=40, l=20, r=20),
        yaxis_title="Jumlah Keputusan",
        xaxis_title="",
        legend=dict(orientation="h", y=-0.15),
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_category_breakdown(stats) -> None:
    """Breakdown kategori rekomendasi."""
    if not stats.top_categories:
        return

    st.markdown("### 🎯 Kategori Rekomendasi")

    df = pd.DataFrame(stats.top_categories, columns=["Kategori", "Jumlah"])

    # Label cantik
    label_map = {
        "yield": "Yield", "scrap": "Scrap", "oee": "OEE",
        "cost": "Biaya", "utility": "Utilitas",
        "inventory": "Inventory", "dead_stock": "Dead Stock",
        "supplier": "Supplier", "other": "Lainnya",
    }
    df["Kategori"] = df["Kategori"].map(lambda k: label_map.get(k, k.title()))

    c1, c2 = st.columns([1, 1])

    with c1:
        fig = px.pie(df, names="Kategori", values="Jumlah", hole=0.45)
        fig.update_layout(height=300, margin=dict(t=10, b=10, l=10, r=10))
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.dataframe(df, use_container_width=True, hide_index=True)


def _render_decisions_log() -> None:
    """Tabel lengkap semua keputusan."""
    st.markdown("### 📋 Log Keputusan")

    try:
        rows = get_all_decisions_with_outcome(limit=200)
    except Exception as e:
        st.warning(f"Tidak dapat memuat log: {e}")
        return

    if not rows:
        st.info("Belum ada keputusan tercatat.")
        return

    df = pd.DataFrame(rows)

    # Pilih kolom penting
    cols = [c for c in ("timestamp", "user", "recommendation",
                        "decision", "notes", "outcome_30d",
                        "outcome_60d", "outcome_90d")
            if c in df.columns]
    df = df[cols]

    # Rename untuk display
    rename = {
        "timestamp": "Waktu", "user": "User",
        "recommendation": "Rekomendasi", "decision": "Keputusan",
        "notes": "Catatan", "outcome_30d": "Hasil 30 Hari",
        "outcome_60d": "Hasil 60 Hari", "outcome_90d": "Hasil 90 Hari",
    }
    df = df.rename(columns=rename)

    # Format keputusan dengan emoji
    if "Keputusan" in df.columns:
        df["Keputusan"] = df["Keputusan"].map(lambda d:
            "✅ Disetujui" if "approve" in str(d).lower() else
            "❌ Ditolak" if "reject" in str(d).lower() else str(d))

    st.dataframe(df, use_container_width=True, hide_index=True)


def _render_outcome_tracker() -> None:
    """Form untuk update outcome keputusan (30/60/90 hari)."""
    with st.expander("📝 Update Outcome Keputusan (30/60/90 Hari)"):
        st.caption(
            "Catat hasil nyata dari keputusan yang sudah dieksekusi. "
            "Data ini akan dipakai untuk melatih rekomendasi ke depannya."
        )

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

        selected = st.selectbox("Pilih Keputusan", list(options.keys()))
        decision_id = options[selected]

        c1, c2, c3 = st.columns(3)

        with c1:
            days = st.selectbox("Periode", [30, 60, 90], index=0)
        with c2:
            outcome = st.text_input(
                "Hasil Nyata (opsional)",
                placeholder="mis. Yield naik 1,2 pp",
            )
        with c3:
            st.write("")
            st.write("")
            if st.button("💾 Simpan Outcome", use_container_width=True):
                if outcome.strip():
                    from ..intel.memory import update_outcome
                    if update_outcome(decision_id, days, outcome.strip()):
                        st.success(f"✅ Outcome {days} hari untuk #{decision_id} disimpan.")
                        st.rerun()
                    else:
                        st.error("Gagal menyimpan outcome.")
                else:
                    st.warning("Masukkan hasil nyata dulu.")


def render(ds, scope) -> None:
    st.title("🧠 Institutional Memory")
    st.caption(
        "AI belajar dari keputusan Anda. Semakin banyak keputusan, "
        "semakin pintar rekomendasi ke depannya (BRD 8, Fase 3)."
    )

    # Hitung stats
    try:
        stats = compute_stats(limit=500)
    except Exception as e:
        st.error(f"Gagal memuat statistik: {e}")
        return

    # ===== KARTU RINGKASAN =====
    _render_header(stats)
    st.markdown("")

    # ===== IMPACT CARD =====
    if stats.approved > 0:
        _render_impact_card(stats)
        st.markdown("")

    st.markdown("---")

    # ===== INSIGHTS =====
    try:
        insights = generate_insights(stats, min_decisions=3)
        _render_insights(insights)
    except Exception as e:
        st.warning(f"Tidak dapat generate insight: {e}")

    st.markdown("---")

    # ===== TABS =====
    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Tren Mingguan",
        "🎯 Kategori",
        "📋 Log Keputusan",
        "📝 Update Outcome",
    ])

    with tab1:
        _render_weekly_trend()

    with tab2:
        _render_category_breakdown(stats)

    with tab3:
        _render_decisions_log()

    with tab4:
        _render_outcome_tracker()

    # ===== FOOTER INFO =====
    st.markdown("---")
    with st.expander("ℹ️ Cara kerja Institutional Memory"):
        st.markdown(
            "**Konsep:** Setiap keputusan Anda (approve/reject) dicatat di database. "
            "Sistem menganalisis pola untuk:\n\n"
            "- 📊 **Acceptance rate** — seberapa relevan rekomendasi kami\n"
            "- 🎯 **Kategori dominan** — area apa yang paling perlu perhatian\n"
            "- 💰 **Total impact** — berapa potensi penghematan dari keputusan Anda\n"
            "- 📈 **Trend** — pola keputusan dari minggu ke minggu\n\n"
            "**Ke depannya:** Sistem akan pakai data ini untuk "
            "**memprioritaskan rekomendasi** sesuai preferensi Anda. "
            "Semakin banyak data, semakin akurat.\n\n"
            "**Berdasarkan BRD 8 (Tata Kelola AI):** "
            "Semua keputusan lewat human-in-the-loop, dan tercatat permanen di audit trail."
        )