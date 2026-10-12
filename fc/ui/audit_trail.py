"""Halaman Audit Trail (DARK)."""
import pandas as pd
import streamlit as st

from .. import audit
from .components import render_table


GLASS_CSS = """
<style>
.at-glass {
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
.at-glass::before {
    content: '';
    position: absolute;
    top: 0; left: 17px;
    width: 35px; height: 3px;
    background: var(--accent, #a489ff);
    border-radius: 0 0 5px 5px;
}
.at-glass:hover {
    transform: translateY(-2px);
    border-color: #8c79d7;
    box-shadow: 0 10px 24px rgba(8, 8, 33, 0.45);
}
.at-glass-label {
    color: #b8bedb;
    font-weight: 600;
    font-size: 0.62rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 6px;
}
.at-glass-value {
    color: #ffffff;
    font-weight: 800;
    font-size: 1.5rem;
    letter-spacing: -0.04em;
    line-height: 1.15;
    margin-bottom: 4px;
}
.at-glass-note {
    color: #8793bc;
    font-size: 0.68rem;
    line-height: 1.3;
    margin-top: 6px;
}

.at-banner {
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
.at-banner::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 4px;
    background: linear-gradient(90deg, #a489ff 0%, #71d5e9 100%);
}
.at-block { flex: 1; min-width: 160px; }
.at-block-label {
    font-size: 0.62rem;
    font-weight: 800;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-bottom: 6px;
    color: #c9b9f8;
}
.at-block-value {
    font-size: 1.5rem;
    font-weight: 800;
    color: #ffffff;
    letter-spacing: -0.04em;
    line-height: 1.15;
    margin-bottom: 4px;
}
.at-block-sub {
    font-size: 0.75rem;
    color: #adb6d5;
}
</style>
"""


def _inject_css():
    st.markdown(GLASS_CSS, unsafe_allow_html=True)


def _fmt_thousand(v) -> str:
    try:
        if v is None: return "—"
        return f"{int(v):,}".replace(",", ".")
    except (ValueError, TypeError):
        return str(v) if v is not None else "—"


def _glass_card(col, label: str, value: str, accent: str = "#a489ff",
                note: str = None) -> None:
    note_html = f'<div class="at-glass-note">{note}</div>' if note else ""
    html = (
        f'<div class="at-glass" style="--accent: {accent};">'
        f'<div class="at-glass-label">{label}</div>'
        f'<div class="at-glass-value">{value}</div>'
        f'{note_html}'
        f'</div>')
    col.markdown(html, unsafe_allow_html=True)


def _render_stats(stats, logs=None):
    st.markdown("### 📊 Ringkasan Audit")
    c1, c2, c3 = st.columns(3, gap="medium")
    _glass_card(c1, "Total Audit Log", _fmt_thousand(stats['total_audit']),
                "#a489ff", note="Semua aksi tercatat")
    _glass_card(c2, "Total Keputusan", _fmt_thousand(stats['total_decisions']),
                "#71d5e9", note="Decision log")
    _glass_card(c3, "Total Model Runs", _fmt_thousand(stats['total_model_runs']),
                "#ec3f92", note="Pemanggilan model/AI")

    if logs:
        last = logs[0]
        last_time = last.get("timestamp", "—")
        last_user = last.get("user", "—")
        last_action = last.get("action", "—")
        html = (
            f'<div class="at-banner">'
            f'<div class="at-block">'
            f'<div class="at-block-label">🕐 AKTIVITAS TERBARU</div>'
            f'<div class="at-block-value">{last_action}</div>'
            f'<div class="at-block-sub">{last_time}</div>'
            f'</div>'
            f'<div class="at-block">'
            f'<div class="at-block-label">👤 USER TERAKHIR</div>'
            f'<div class="at-block-value">{last_user}</div>'
            f'<div class="at-block-sub">Pelaku aksi terakhir</div>'
            f'</div>'
            f'<div class="at-block">'
            f'<div class="at-block-label">📋 TOTAL LOG</div>'
            f'<div class="at-block-value">{_fmt_thousand(stats["total_audit"])}</div>'
            f'<div class="at-block-sub">Database SQLite</div>'
            f'</div>'
            f'</div>')
        st.markdown(html, unsafe_allow_html=True)


def render(ds, scope) -> None:
    _inject_css()
    st.title("📋 Audit Trail")
    st.caption("Catatan permanen semua aksi user: login, load data, ekspor, chat. "
               "Tersimpan di database SQLite (BRD 7).")

    stats = audit.get_stats()
    try:
        _banner_logs = audit.get_recent_logs(limit=1)
    except Exception:
        _banner_logs = []
    _render_stats(stats, _banner_logs)

    st.markdown("---")
    st.markdown("### 🔍 Filter")
    col1, col2, col3 = st.columns([2, 2, 1], gap="medium")
    with col1:
        limit = st.selectbox("Tampilkan", [50, 100, 250, 500, 1000], index=1)
    with col2:
        action_filter = st.text_input("Filter aksi (opsional)",
                                       placeholder="mis. login, export, load_data")
    with col3:
        st.write("")
        st.write("")
        show = st.button("🔄 Muat Ulang", width='stretch')

    st.markdown("### 📜 Log Terbaru")
    logs = audit.get_recent_logs(limit=limit)
    if action_filter:
        logs = [l for l in logs if action_filter.lower() in l["action"].lower()]

    if not logs:
        st.info("Belum ada log. Coba lakukan aksi (login, buka halaman, ekspor).")
        return

    df = pd.DataFrame(logs)
    df = df[["timestamp", "user", "action", "source_label", "details"]]
    df.columns = ["Waktu", "User", "Aksi", "Sumber Data", "Detail"]
    render_table(df, max_height="500px")

    st.markdown("---")
    st.markdown("### 📊 Ringkasan Aksi")
    if len(df):
        summary = df["Aksi"].value_counts().reset_index()
        summary.columns = ["Aksi", "Jumlah"]
        render_table(summary, max_height="300px")

    st.markdown("---")
    st.caption("📁 Database: `data/afc.db` (SQLite) — "
               "bisa diakses langsung dengan tools SQLite untuk audit eksternal.")