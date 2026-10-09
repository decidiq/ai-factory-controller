"""Multi-Agent Collaboration - BELUM TERSEDIA di Tahap 1 (BRD 8)."""
import streamlit as st


# ==================== CSS ====================
GLASS_CSS = """
<style>
.ma-banner {
    background: linear-gradient(135deg, #0F172A 0%, #1E1B4B 60%, #4C1D95 100%);
    border-radius: 18px;
    padding: 32px 36px;
    color: white;
    box-shadow: 0 12px 32px rgba(30, 27, 75, 0.25);
    border: 1px solid rgba(139, 92, 246, 0.3);
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
    background: radial-gradient(circle, rgba(245, 158, 11, 0.35) 0%, transparent 70%);
    pointer-events: none;
}
.ma-badge {
    display: inline-block;
    background: rgba(245, 158, 11, 0.2);
    color: #FBBF24;
    font-size: 0.7rem;
    font-weight: 800;
    letter-spacing: 1.5px;
    padding: 5px 12px;
    border-radius: 999px;
    border: 1px solid rgba(245, 158, 11, 0.4);
    margin-bottom: 14px;
    position: relative;
    z-index: 1;
}
.ma-title {
    font-size: 2rem;
    font-weight: 900;
    color: #FFFFFF;
    letter-spacing: -1px;
    line-height: 1.15;
    margin-bottom: 12px;
    position: relative;
    z-index: 1;
}
.ma-desc {
    font-size: 0.95rem;
    color: #C4B5FD;
    line-height: 1.6;
    max-width: 720px;
    position: relative;
    z-index: 1;
}
.ma-desc strong { color: #FBBF24; }

/* Roadmap Card */
.ma-roadmap {
    position: relative;
    background: linear-gradient(135deg, #FFFFFF 0%, #F5F3FF 100%);
    border: 1px solid rgba(196, 181, 253, 0.5);
    border-radius: 14px;
    padding: 20px 22px;
    box-shadow: 0 6px 20px rgba(139, 92, 246, 0.08);
    margin-bottom: 14px;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    overflow: hidden;
}
.ma-roadmap::before {
    content: '';
    position: absolute;
    top: 0; left: 0; bottom: 0;
    width: 4px;
    background: linear-gradient(180deg, #8B5CF6 0%, #EC4899 100%);
}
.ma-roadmap:hover {
    transform: translateY(-2px);
    box-shadow: 0 16px 32px rgba(139, 92, 246, 0.18);
    border-color: rgba(139, 92, 246, 0.6);
}
.ma-roadmap-icon {
    font-size: 1.6rem;
    margin-bottom: 8px;
    display: block;
}
.ma-roadmap-title {
    font-size: 1rem;
    font-weight: 800;
    color: #1E1B4B;
    letter-spacing: -0.3px;
    margin-bottom: 6px;
}
.ma-roadmap-desc {
    font-size: 0.85rem;
    color: #64748B;
    line-height: 1.5;
}
.ma-roadmap-phase {
    display: inline-block;
    background: #F5F3FF;
    color: #6D28D9;
    font-size: 0.68rem;
    font-weight: 800;
    letter-spacing: 0.8px;
    padding: 3px 8px;
    border-radius: 6px;
    margin-top: 10px;
}
</style>
"""


def _inject_css():
    st.markdown(GLASS_CSS, unsafe_allow_html=True)


# ==================== MAIN ====================
def render(ds, scope) -> None:
    _inject_css()

    st.title("🤖 Multi-Agent Factory Collaboration")

    # Banner
    html = (
        f'<div class="ma-banner">'
        f'<div class="ma-badge">⏳ COMING SOON — TAHAP 5</div>'
        f'<div class="ma-title">Fitur ini belum tersedia</div>'
        f'<div class="ma-desc">'
        f'Sesuai <strong>BRD bagian 8 (Kejujuran Klaim)</strong> dan roadmap Tahap 5, '
        f'orkestrasi multi-agen akan dibangun pada Tahap 5. '
        f'Tahap 1 hanya menyediakan lapisan analitik read-only. '
        f'<strong>Tidak ada agen AI yang berkoordinasi atau mengeksekusi tindakan.</strong>'
        f'</div>'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)

    # Roadmap
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

    c1, c2 = st.columns(2)
    for i, (icon, title, desc, phase) in enumerate(roadmap):
        html = (
            f'<div class="ma-roadmap">'
            f'<span class="ma-roadmap-icon">{icon}</span>'
            f'<div class="ma-roadmap-title">{title}</div>'
            f'<div class="ma-roadmap-desc">{desc}</div>'
            f'<div class="ma-roadmap-phase">{phase}</div>'
            f'</div>'
        )
        target = c1 if i % 2 == 0 else c2
        with target:
            st.markdown(html, unsafe_allow_html=True)

    st.markdown("---")
    st.info(
        "💡 **Kenapa belum tersedia?** Sesuai prinsip BRD: *'Jangan klaim fitur "
        "yang belum ada.'* Decidiq memilih transparan tentang roadmap daripada "
        "menampilkan fitur palsu. Fase 5 akan dibangun setelah fondasi data "
        "(Fase 1), intelijen analitik (Fase 2), dan memory (Fase 3) matang."
    )