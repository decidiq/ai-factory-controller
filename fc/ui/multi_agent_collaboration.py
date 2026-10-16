"""Multi-Agent Collaboration — COMING SOON di Fase 5C (DARK).

Berbeda dari AI Factory OS (Fase 5A) yang fokus 1 agent per task,
halaman ini akan menampilkan kolaborasi beberapa agent sekaligus
untuk menyelesaikan task kompleks.
"""
import streamlit as st


CSS = """
<style>
.mac-hero {
    background: linear-gradient(110deg, #1a1f4a 0%, #2d2a5e 45%, #1e1b47 100%);
    border-radius: 18px;
    padding: 28px 32px;
    color: #fff;
    border: 1px solid #4a4180;
    margin-bottom: 22px;
    position: relative;
    overflow: hidden;
}
.mac-hero::before {
    content: '';
    position: absolute;
    top: -60px; right: -60px;
    width: 220px; height: 220px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(247, 213, 120, 0.28) 0%, transparent 70%);
}
.mac-hero-badge {
    display: inline-block;
    background: rgba(247, 213, 120, 0.18);
    color: #f7d578;
    font-size: 0.66rem;
    font-weight: 800;
    letter-spacing: 0.12em;
    padding: 5px 12px;
    border-radius: 999px;
    border: 1px solid rgba(247, 213, 120, 0.5);
    margin-bottom: 12px;
    position: relative;
    z-index: 1;
}
.mac-hero-title {
    font-size: 1.7rem;
    font-weight: 800;
    letter-spacing: -0.03em;
    margin-bottom: 8px;
    position: relative;
    z-index: 1;
}
.mac-hero-sub {
    font-size: 0.9rem;
    color: #c9cdf0;
    max-width: 720px;
    line-height: 1.55;
    position: relative;
    z-index: 1;
}
.mac-hero-sub strong { color: #f7d578; }

.mac-card {
    background: linear-gradient(145deg, #1a1d3d, #151933);
    border: 1px solid #343858;
    border-radius: 14px;
    padding: 20px 22px;
    margin-bottom: 14px;
    position: relative;
    overflow: hidden;
    transition: transform 0.2s ease, border-color 0.2s ease;
}
.mac-card:hover {
    transform: translateY(-2px);
    border-color: #8c79d7;
}
.mac-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; bottom: 0;
    width: 4px;
    background: linear-gradient(180deg, #a489ff 0%, #71d5e9 100%);
}
.mac-card-icon {
    font-size: 1.6rem;
    display: block;
    margin-bottom: 8px;
}
.mac-card-title {
    font-size: 0.95rem;
    font-weight: 800;
    color: #f5f6ff;
    letter-spacing: -0.02em;
    margin-bottom: 6px;
}
.mac-card-desc {
    font-size: 0.82rem;
    color: #adb6d5;
    line-height: 1.5;
}
.mac-card-phase {
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

.mac-compare {
    background: #1b1e3e;
    border: 1px solid #343858;
    border-left: 4px solid #7adcff;
    border-radius: 10px;
    padding: 16px 20px;
    margin: 20px 0;
}
.mac-compare-title {
    color: #7adcff;
    font-size: 0.72rem;
    font-weight: 800;
    letter-spacing: 0.1em;
    margin-bottom: 10px;
    text-transform: uppercase;
}
.mac-compare-row {
    color: #dce0f4;
    font-size: 0.85rem;
    line-height: 1.6;
    padding: 4px 0;
}
.mac-compare-row strong { color: #f7d578; }
</style>
"""


ROADMAP = [
    ("🤝", "Cross-Agent Orchestration",
     "Executive agent memanggil Production, Inventory, dan Cost agent secara paralel, "
     "lalu sintesis jawaban menjadi briefing terpadu.",
     "FASE 5C"),
    ("🔀", "Parallel Execution",
     "Beberapa agent bekerja bersamaan untuk task yang sama — hasil lebih cepat "
     "dan pandangan multi-perspektif.",
     "FASE 5C"),
    ("📊", "Side-by-Side Comparison",
     "Bandingkan rekomendasi 2-3 agent dalam satu tampilan — lihat konsistensi "
     "dan perbedaan pandangan.",
     "FASE 5C"),
    ("🧠", "Shared Memory",
     "Semua agent berbagi memori yang sama — tidak ada konteks yang hilang "
     "antar-agent.",
     "FASE 5C"),
    ("👤", "Human-in-the-Loop",
     "Setiap konsensus agent butuh approval manusia sebelum dieksekusi — "
     "log lengkap ke audit trail.",
     "FASE 5D"),
    ("📱", "Agent-to-Agent Messaging",
     "Agent bisa saling bertanya satu sama lain via LLM, dengan explainability "
     "untuk setiap keputusan.",
     "FASE 5D"),
]


def _inject_css():
    st.markdown(CSS, unsafe_allow_html=True)


def _render_hero():
    html = (
        '<div class="mac-hero">'
        '<div class="mac-hero-badge">⏳ FASE 5C — DALAM PERENCANAAN</div>'
        '<div class="mac-hero-title">Multi-Agent Collaboration</div>'
        '<div class="mac-hero-sub">'
        'Halaman ini akan menampilkan <strong>kolaborasi beberapa agent</strong> untuk '
        'menyelesaikan task kompleks — berbeda dari <strong>AI Factory OS</strong> yang '
        'fokus 1 agent per task. Setiap konsensus tetap butuh approval manusia.'
        '</div></div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def _render_compare():
    html = (
        '<div class="mac-compare">'
        '<div class="mac-compare-title">🔍 Perbedaan dengan AI Factory OS</div>'
        '<div class="mac-compare-row">'
        '<strong>AI Factory OS (Fase 5A)</strong> — 1 agent, 1 task, '
        'lihat narasi + confidence + tools used.'
        '</div>'
        '<div class="mac-compare-row">'
        '<strong>Multi-Agent Collaboration (Fase 5C)</strong> — beberapa agent '
        'bekerja bareng, hasil digabung, cross-check konsistensi antar-agent.'
        '</div>'
        '</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def _render_roadmap():
    st.markdown("### 🗺️ Yang Akan Hadir di Fase 5C")
    st.caption("Rencana fitur kolaborasi multi-agent — belum tersedia saat ini.")

    c1, c2 = st.columns(2, gap="medium")
    for i, (icon, title, desc, phase) in enumerate(ROADMAP):
        html = (
            f'<div class="mac-card">'
            f'<span class="mac-card-icon">{icon}</span>'
            f'<div class="mac-card-title">{title}</div>'
            f'<div class="mac-card-desc">{desc}</div>'
            f'<div class="mac-card-phase">{phase}</div>'
            f'</div>'
        )
        target = c1 if i % 2 == 0 else c2
        with target:
            st.markdown(html, unsafe_allow_html=True)


def render(ds, scope) -> None:
    _inject_css()
    st.title("🤝 Multi-Agent Collaboration")

    _render_hero()
    _render_compare()
    _render_roadmap()

    st.markdown("---")
    st.info(
        "💡 **Kenapa belum tersedia?** Decidiq memilih transparan tentang roadmap "
        "daripada menampilkan fitur palsu. Sesuai prinsip BRD bagian 8 "
        "(Kejujuran Klaim), Fase 5C akan dibangun setelah fondasi "
        "**single-agent** (Fase 5A) stabil dan teruji."
    )

    st.markdown("---")
    st.markdown("**🚀 Sementara itu, coba dulu:**")
    c1, c2 = st.columns([1, 3])
    with c1:
        if st.button("⚡ Buka AI Factory OS", type="primary",
                     use_container_width=True):
            st.session_state["_nav_to"] = "AI Factory OS"
            st.rerun()
    with c2:
        st.caption(
            "AI Factory OS (Fase 5A) sudah aktif — pilih agent, jalankan task, "
            "dan lihat memori agent secara real-time."
        )