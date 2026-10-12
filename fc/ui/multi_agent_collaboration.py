"""Multi-Agent Collaboration - COMING SOON di Tahap 5 (DARK)."""
import streamlit as st


GLASS_CSS = """
<style>
.ma-banner {
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
.ma-banner::before {
    content: '';
    position: absolute;
    top: -80px; right: -80px;
    width: 260px; height: 260px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(247, 213, 120, 0.28) 0%, transparent 70%);
    pointer-events: none;
}
.ma-badge {
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
.ma-title {
    font-size: 1.8rem;
    font-weight: 800;
    color: #ffffff;
    letter-spacing: -0.04em;
    line-height: 1.15;
    margin-bottom: 12px;
    position: relative;
    z-index: 1;
}
.ma-desc {
    font-size: 0.9rem;
    color: #dce0f4;
    line-height: 1.6;
    max-width: 720px;
    position: relative;
    z-index: 1;
}
.ma-desc strong { color: #f7d578; }

.ma-roadmap {
    position: relative;
    background: linear-gradient(145deg, #1a1d3d, #151933);
    border: 1px solid #343858;
    border-radius: 14px;
    padding: 20px 22px;
    box-shadow: 0 9px 30px rgba(6, 9, 23, 0.13);
    margin-bottom: 14px;
    transition: transform 0.2s ease, border-color 0.2s ease;
    overflow: hidden;
}
.ma-roadmap::before {
    content: '';
    position: absolute;
    top: 0; left: 0; bottom: 0;
    width: 4px;
    background: linear-gradient(180deg, #a489ff 0%, #71d5e9 100%);
}
.ma-roadmap:hover {
    transform: translateY(-2px);
    border-color: #8c79d7;
    box-shadow: 0 10px 24px rgba(8, 8, 33, 0.45);
}
.ma-roadmap-icon {
    font-size: 1.6rem;
    margin-bottom: 8px;
    display: block;
}
.ma-roadmap-title {
    font-size: 0.95rem;
    font-weight: 800;
    color: #f5f6ff;
    letter-spacing: -0.02em;
    margin-bottom: 6px;
}
.ma-roadmap-desc {
    font-size: 0.82rem;
    color: #adb6d5;
    line-height: 1.5;
}
.ma-roadmap-phase {
    display: inline-block;
    background: #242748;
    color: #c4aaff;
    font-size: 0.62rem;
    font-weight: 800;
    letter-spacing: 0.08em;
    padding: 3px 8px;
    border-radius: 6px;
    margin-top: 10px;
    border: 1px solid #343858;
}
</style>
"""


def _inject_css():
    st.markdown(GLASS_CSS, unsafe_allow_html=True)


def render(ds, scope) -> None:
    _inject_css()
    st.title("🤖 Multi-Agent Factory Collaboration")

    html = (
        f'<div class="ma-banner">'
        f'<div class="ma-badge">⏳ COMING SOON — TAHAP 5</div>'
        f'<div class="ma-title">Fitur ini belum tersedia</div>'
        f'<div class="ma-desc">'
        f'Sesuai <strong>BRD bagian 8 (Kejujuran Klaim)</strong> dan roadmap Tahap 5, '
        f'orkestrasi multi-agen akan dibangun pada Tahap 5. '
        f'Tahap 1 hanya menyediakan lapisan analitik read-only. '
        f'<strong>Tidak ada agen AI yang berkoordinasi atau mengeksekusi tindakan.</strong>'
        f'</div></div>')
    st.markdown(html, unsafe_allow_html=True)

    st.markdown("### 🗺️ Yang Akan Hadir di Tahap 5")
    st.caption("Rencana pengembangan fitur kolaborasi multi-agen.")

    roadmap = [
        ("📦", "Inventory Agent", "Memantau stok, prediksi stock-out, dan otomatis buat reorder request.", "FASE 5A"),
        ("⚙️", "Production Agent", "Optimasi jadwal produksi, deteksi anomali, dan rekomendasi parameter mesin.", "FASE 5A"),
        ("🔧", "Maintenance Agent", "Prediksi kerusakan mesin (predictive maintenance) dan penjadwalan servis.", "FASE 5B"),
        ("💰", "Finance Agent", "Analisis biaya real-time, proyeksi cash flow, dan optimasi budget.", "FASE 5B"),
        ("🤝", "Cross-Agent Collaboration", "Agen-agen saling berkoordinasi dengan explainability untuk keputusan kompleks.", "FASE 5C"),
        ("👤", "Human-in-the-Loop", "Setiap rekomendasi agen membutuhkan persetujuan manusia sebelum eksekusi.", "FASE 5C"),
        ("📋", "Audit Trail Permanen", "Semua keputusan agen dan manusia tercatat di database SQLite.", "FASE 5C"),
    ]

    c1, c2 = st.columns(2, gap="medium")
    for i, (icon, title, desc, phase) in enumerate(roadmap):
        html = (
            f'<div class="ma-roadmap">'
            f'<span class="ma-roadmap-icon">{icon}</span>'
            f'<div class="ma-roadmap-title">{title}</div>'
            f'<div class="ma-roadmap-desc">{desc}</div>'
            f'<div class="ma-roadmap-phase">{phase}</div>'
            f'</div>')
        target = c1 if i % 2 == 0 else c2
        with target:
            st.markdown(html, unsafe_allow_html=True)

    st.markdown("---")
    st.info("💡 **Kenapa belum tersedia?** Sesuai prinsip BRD: *'Jangan klaim fitur "
            "yang belum ada.'* Decidiq memilih transparan tentang roadmap daripada "
            "menampilkan fitur palsu. Fase 5 akan dibangun setelah fondasi data "
            "(Fase 1), intelijen analitik (Fase 2), dan memory (Fase 3) matang.")