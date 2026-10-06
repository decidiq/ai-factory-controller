"""Halaman Audit Trail - lihat semua log aksi user (BRD 7)."""
import pandas as pd
import streamlit as st

from .. import audit


def render(ds, scope) -> None:
    st.title("📋 Audit Trail")
    st.caption("Catatan permanen semua aksi user: login, load data, ekspor, chat. "
               "Tersimpan di database SQLite (BRD 7).")

    # ---- Statistik ----
    stats = audit.get_stats()
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Audit Log", f"{stats['total_audit']:,}")
    c2.metric("Total Keputusan", f"{stats['total_decisions']:,}")
    c3.metric("Total Model Runs", f"{stats['total_model_runs']:,}")

    st.markdown("---")

    # ---- Filter ----
    st.subheader("🔍 Filter")
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        limit = st.selectbox("Tampilkan", [50, 100, 250, 500, 1000], index=1)
    with col2:
        action_filter = st.text_input("Filter aksi (opsional)",
                                       placeholder="mis. login, export, load_data")
    with col3:
        st.write("")
        st.write("")
        show = st.button("🔄 Muat Ulang", use_container_width=True)

    # ---- Tabel log ----
    st.subheader("📜 Log Terbaru")
    logs = audit.get_recent_logs(limit=limit)
    if action_filter:
        logs = [l for l in logs if action_filter.lower() in l["action"].lower()]

    if not logs:
        st.info("Belum ada log. Coba lakukan aksi (login, buka halaman, ekspor).")
        return

    df = pd.DataFrame(logs)
    df = df[["timestamp", "user", "action", "source_label", "details"]]
    df.columns = ["Waktu", "User", "Aksi", "Sumber Data", "Detail"]

    st.dataframe(df, use_container_width=True, hide_index=True)

    # ---- Ringkasan per action ----
    st.markdown("---")
    st.subheader("📊 Ringkasan Aksi")
    if len(df):
        summary = df["Aksi"].value_counts().reset_index()
        summary.columns = ["Aksi", "Jumlah"]
        st.dataframe(summary, use_container_width=True, hide_index=True)

    # ---- Info DB ----
    st.markdown("---")
    st.caption("📁 Database: `data/afc.db` (SQLite) — "
               "bisa diakses langsung dengan tools SQLite untuk audit eksternal.")