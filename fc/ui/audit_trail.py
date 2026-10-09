"""Halaman Audit Trail - lihat semua log aksi user (BRD 7)."""
import pandas as pd
import streamlit as st

from .. import audit


# ==================== CSS GLASSMORPHISM ====================
GLASS_CSS = """
<style>
.at-glass {
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
.at-glass::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, var(--accent, #8B5CF6) 0%, #EC4899 100%);
}
.at-glass:hover {
    transform: translateY(-3px);
    box-shadow: 0 16px 32px rgba(139, 92, 246, 0.18);
    border-color: rgba(139, 92, 246, 0.6);
}
.at-glass-label {
    color: #6D28D9;
    font-weight: 700;
    font-size: 0.66rem;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    margin-bottom: 6px;
}
.at-glass-value {
    color: #0F172A;
    font-weight: 800;
    font-size: 1.5rem;
    letter-spacing: -0.5px;
    line-height: 1.1;
    margin-bottom: 4px;
}
.at-glass-note {
    color: #94A3B8;
    font-size: 0.68rem;
    font-style: italic;
    line-height: 1.3;
}

/* Banner */
.at-banner {
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
.at-banner::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 4px;
    background: linear-gradient(90deg, #8B5CF6 0%, #EC4899 100%);
}
.at-block { flex: 1; min-width: 160px; }
.at-block-label {
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    margin-bottom: 6px;
    color: #A78BFA;
}
.at-block-value {
    font-size: 1.6rem;
    font-weight: 900;
    color: #FFFFFF;
    letter-spacing: -0.5px;
    line-height: 1.15;
    margin-bottom: 2px;
}
.at-block-sub {
    font-size: 0.75rem;
    color: #94A3B8;
}
</style>
"""


def _inject_css():
    st.markdown(GLASS_CSS, unsafe_allow_html=True)


# ==================== HELPERS ====================
def _glass_card(col, label: str, value: str, accent: str = "#8B5CF6",
                note: str = None) -> None:
    note_html = f'<div class="at-glass-note">{note}</div>' if note else ""
    html = (
        f'<div class="at-glass" style="--accent: {accent};">'
        f'<div class="at-glass-label">{label}</div>'
        f'<div class="at-glass-value">{value}</div>'
        f'{note_html}'
        f'</div>'
    )
    col.markdown(html, unsafe_allow_html=True)


# ==================== STATS + BANNER ====================
def _render_stats(stats, logs=None):
    st.markdown("### 📊 Ringkasan Audit")

    c1, c2, c3 = st.columns(3)
    _glass_card(c1, "Total Audit Log", f"{stats['total_audit']:,}", "#8B5CF6",
                note="Semua aksi tercatat")
    _glass_card(c2, "Total Keputusan", f"{stats['total_decisions']:,}", "#3B82F6",
                note="Decision log")
    _glass_card(c3, "Total Model Runs", f"{stats['total_model_runs']:,}", "#EC4899",
                note="Pemanggilan model/AI")

    # Banner dengan log terbaru
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
            f'<div class="at-block-value">{stats["total_audit"]:,}</div>'
            f'<div class="at-block-sub">Database SQLite</div>'
            f'</div>'
            f'</div>'
        )
        st.markdown(html, unsafe_allow_html=True)


# ==================== MAIN ====================
def render(ds, scope) -> None:
    _inject_css()

    st.title("📋 Audit Trail")
    st.caption(
        "Catatan permanen semua aksi user: login, load data, ekspor, chat. "
        "Tersimpan di database SQLite (BRD 7)."
    )

    # Statistik
    stats = audit.get_stats()

    # Ambil log terbaru untuk banner
    try:
        _banner_logs = audit.get_recent_logs(limit=1)
    except Exception:
        _banner_logs = []

    _render_stats(stats, _banner_logs)

    st.markdown("---")

    # Filter
    st.markdown("### 🔍 Filter")
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        limit = st.selectbox("Tampilkan", [50, 100, 250, 500, 1000], index=1)
    with col2:
        action_filter = st.text_input(
            "Filter aksi (opsional)",
            placeholder="mis. login, export, load_data",
        )
    with col3:
        st.write("")
        st.write("")
        show = st.button("🔄 Muat Ulang", use_container_width=True)

    # Tabel log
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

    st.dataframe(df, use_container_width=True, hide_index=True)

    # Ringkasan per action
    st.markdown("---")
    st.markdown("### 📊 Ringkasan Aksi")
    if len(df):
        summary = df["Aksi"].value_counts().reset_index()
        summary.columns = ["Aksi", "Jumlah"]
        st.dataframe(summary, use_container_width=True, hide_index=True)

    # Info DB
    st.markdown("---")
    st.caption(
        "📁 Database: `data/afc.db` (SQLite) — "
        "bisa diakses langsung dengan tools SQLite untuk audit eksternal."
    )