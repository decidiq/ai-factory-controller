"""AI Factory OS - COMING SOON di Tahap 5 (DARK)."""
import streamlit as st


GLASS_CSS = """
<style>
.os-banner {
    background: linear-gradient(110deg, #30265e, #211b47 55%, #171b3c);
    border-radius: 18px;
    padding: 32px 36px;
    color: #ffffff;
    box-shadow: 0 9px 30px rgba(6, 9, 23, 0.13);
    border: 1px solid #5e5090;
    margin-bottom: 24px;
    position: relative;
    overflow: hidden;
}
.os-banner::before {
    content: '';
    position: absolute;
    top: -80px; right: -80px;
    width: 260px; height: 260px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(247, 213, 120, 0.28) 0%, transparent 70%);
    pointer-events: none;
}
.os-badge {
    display: inline-block;
    background: rgba(247, 213, 120, 0.15);
    color: #f7d578;
    font-size: 0.66rem;
    font-weight: 800;
    letter-spacing: 0.12em;
    padding: 5px 12px;
    border-radius: 999px;
    border: 1px solid rgba(247, 213, 120, 0.4);
    margin-bottom: 14px;
    position: relative;
    z-index: 1;
}
.os-title {
    font-size: 1.8rem;
    font-weight: 800;
    color: #ffffff;
    letter-spacing: -0.04em;
    line-height: 1.15;
    margin-bottom: 12px;
    position: relative;
    z-index: 1;
}
.os-desc {
    font-size: 0.9rem;
    color: #dce0f4;
    line-height: 1.6;
    max-width: 720px;
    position: relative;
    z-index: 1;
}
.os-desc strong { color: #f7d578; }

.os-list {
    background: #1b1e3e;
    border: 1px solid #343858;
    border-left: 4px solid #a489ff;
    border-radius: 12px;
    padding: 18px 22px;
    margin-bottom: 16px;
}
.os-list-item {
    color: #dce0f4;
    font-size: 0.88rem;
    line-height: 1.7;
    padding: 4px 0;
}
.os-list-item strong { color: #f5f6ff; }
</style>
"""


def _inject_css():
    st.markdown(GLASS_CSS, unsafe_allow_html=True)


def render(ds, scope) -> None:
    _inject_css()
    st.title("⚡ AI Factory OS")

    html = (
        f'<div class="os-banner">'
        f'<div class="os-badge">⏳ COMING SOON — TAHAP 5</div>'
        f'<div class="os-title">Fitur ini belum tersedia</div>'
        f'<div class="os-desc">'
        f'Sesuai <strong>BRD bagian 8 (Kejujuran Klaim)</strong> dan roadmap Tahap 5, '
        f'<strong>AI Factory OS</strong> akan dibangun pada Tahap 5. '
        f'Tahap 1 hanya menyediakan lapisan analitik read-only. '
        f'Tidak ada eksekusi otomatis, auto-PO, atau blockchain audit trail saat ini.'
        f'</div></div>')
    st.markdown(html, unsafe_allow_html=True)

    st.markdown("### 🗺️ Item Roadmap Tahap 5")
    html = (
        f'<div class="os-list">'
        f'<div class="os-list-item">🤖 <strong>Agen AI untuk Manajemen Risiko</strong> — deteksi & mitigasi otomatis</div>'
        f'<div class="os-list-item">📊 <strong>Asisten Rapat Eksekutif</strong> — briefing otomatis + insight</div>'
        f'<div class="os-list-item">👤 <strong>Persetujuan Manusia (Human-in-the-Loop)</strong> — setiap aksi butuh approval</div>'
        f'<div class="os-list-item">🔒 <strong>Audit Trail Permanen</strong> — migrasi SQLite → PostgreSQL enterprise</div>'
        f'<div class="os-list-item">🔌 <strong>Konektor Enterprise</strong> — SAP, Odoo, Google Sheets</div>'
        f'<div class="os-list-item">📱 <strong>Mobile App</strong> — monitoring dari HP</div>'
        f'</div>')
    st.markdown(html, unsafe_allow_html=True)

    st.info("💡 **Kenapa belum tersedia?** Decidiq memilih transparan tentang roadmap "
            "daripada menampilkan fitur palsu. Fase 5 dibangun setelah fondasi "
            "data (Fase 1), intelijen analitik (Fase 2), dan memory (Fase 3) matang.")