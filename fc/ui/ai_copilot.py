"""AI Copilot dasar - berbasis kata kunci (BRD 8) — Premium UI."""
import streamlit as st

from ..kpi import Scope, summarize
from ..pipeline import Dataset


# ==================== CSS ====================
GLASS_CSS = """
<style>
.ai-banner {
    background: linear-gradient(135deg, #0F172A 0%, #1E1B4B 60%, #4C1D95 100%);
    border-radius: 16px;
    padding: 24px 30px;
    color: white;
    box-shadow: 0 12px 32px rgba(30, 27, 75, 0.25);
    border: 1px solid rgba(139, 92, 246, 0.3);
    margin-bottom: 20px;
    position: relative;
    overflow: hidden;
}
.ai-banner::before {
    content: '';
    position: absolute;
    top: -80px; right: -80px;
    width: 260px; height: 260px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(139, 92, 246, 0.35) 0%, transparent 70%);
    pointer-events: none;
}
.ai-banner-label {
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 1.5px;
    color: #A78BFA;
    text-transform: uppercase;
    margin-bottom: 8px;
    position: relative;
    z-index: 1;
}
.ai-banner-title {
    font-size: 1.6rem;
    font-weight: 900;
    color: #FFFFFF;
    letter-spacing: -0.6px;
    line-height: 1.15;
    margin-bottom: 8px;
    position: relative;
    z-index: 1;
}
.ai-banner-desc {
    font-size: 0.9rem;
    color: #C4B5FD;
    line-height: 1.5;
    max-width: 700px;
    position: relative;
    z-index: 1;
}
.ai-banner-desc strong { color: #FBBF24; }

.ai-hint-card {
    background: #FFFFFF;
    border: 1px solid #E9D5FF;
    border-radius: 12px;
    padding: 14px 18px;
    margin-bottom: 10px;
    box-shadow: 0 2px 6px rgba(139, 92, 246, 0.05);
    display: flex;
    align-items: start;
    gap: 12px;
}
.ai-hint-icon {
    font-size: 1.4rem;
    flex-shrink: 0;
    line-height: 1;
}
.ai-hint-title {
    font-size: 0.9rem;
    font-weight: 700;
    color: #1E1B4B;
    margin-bottom: 3px;
}
.ai-hint-desc {
    font-size: 0.8rem;
    color: #64748B;
    line-height: 1.45;
}
</style>
"""


def _inject_css():
    st.markdown(GLASS_CSS, unsafe_allow_html=True)


# ==================== BANNER ====================
def _render_banner():
    html = (
        f'<div class="ai-banner">'
        f'<div class="ai-banner-label">🤖 AI COPILOT</div>'
        f'<div class="ai-banner-title">Tanya data pabrik dalam bahasa natural</div>'
        f'<div class="ai-banner-desc">'
        f'Copilot dasar ini menjawab dengan data yang tersedia. '
        f'Coba ketik: <strong>output</strong>, <strong>yield</strong>, '
        f'<strong>scrap</strong>, <strong>oee</strong>, <strong>cogm</strong>, '
        f'atau <strong>cost/kg</strong>.'
        f'</div>'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


# ==================== QUICK PROMPTS ====================
def _render_quick_prompts():
    """Tombol pintas untuk pertanyaan umum."""
    st.markdown("##### ⚡ Quick Prompts")
    st.caption("Klik salah satu untuk bertanya langsung.")

    prompts = [
        ("📊 Output", "Berapa total output produksi?"),
        ("🎯 Yield", "Berapa yield saat ini?"),
        ("🗑️ Scrap", "Berapa scrap rate sekarang?"),
        ("⚙️ OEE", "Berapa nilai OEE?"),
        ("💰 COGM", "Berapa total COGM?"),
        ("💵 Cost/Kg", "Berapa cost per kg?"),
    ]

    cols = st.columns(6)
    for col, (label, full_prompt) in zip(cols, prompts):
        with col:
            if st.button(label, use_container_width=True,
                         key=f"quick_{label}"):
                # Simpan prompt ke session state untuk diproses
                st.session_state["_quick_prompt"] = full_prompt
                st.rerun()


# ==================== ANSWER ====================
def _answer(ds, scope, q):
    s = summarize(ds, scope)

    def _v(kpi, label, fmt="{:,.2f}"):
        return (f"**{label}**: {fmt.format(kpi.value)}" if kpi.available
                else f"**{label}**: data tidak tersedia ({kpi.note})")

    if any(k in q for k in ("output", "produksi")):
        return _v(s.output_kg, "Total Output", "{:,.0f} Kg")
    if "yield" in q:
        return _v(s.yield_pct, "Yield", "{:.2f}%")
    if "scrap" in q:
        return _v(s.scrap_pct, "Scrap", "{:.2f}%")
    if "oee" in q:
        return _v(s.oee.oee, "OEE", "{:.2f}%")
    if "cogm" in q or "total biaya" in q:
        return _v(s.cogm, "COGM", "Rp {:,.0f}")
    if "cost/kg" in q or "cost per kg" in q:
        return _v(s.cost_per_kg, "Cost/Kg", "Rp {:,.0f}")

    return ("Maaf, saya tidak punya jawaban untuk itu. Copilot dasar ini hanya menjawab: "
            "output, yield, scrap, OEE, COGM, Cost/Kg. LLM datang di Tahap 3/5.")


# ==================== SIDEBAR HINTS ====================
def _render_hints():
    with st.expander("ℹ️ Apa yang bisa ditanyakan?"):
        hints = [
            ("📊", "Output", "Total produksi dalam Kg"),
            ("🎯", "Yield", "Persentase yield saat ini"),
            ("🗑️", "Scrap", "Persentase scrap rate"),
            ("⚙️", "OEE", "Overall Equipment Effectiveness"),
            ("💰", "COGM", "Cost of Goods Manufactured (Rp)"),
            ("💵", "Cost/Kg", "Biaya per kilogram produksi"),
        ]
        for icon, title, desc in hints:
            html = (
                f'<div class="ai-hint-card">'
                f'<div class="ai-hint-icon">{icon}</div>'
                f'<div>'
                f'<div class="ai-hint-title">{title}</div>'
                f'<div class="ai-hint-desc">{desc}</div>'
                f'</div>'
                f'</div>'
            )
            st.markdown(html, unsafe_allow_html=True)


# ==================== MAIN ====================
def render(ds: Dataset, scope: Scope) -> None:
    _inject_css()

    st.title("🤖 AI Copilot")
    st.caption(
        "Asisten berbasis kata kunci. Belum memakai LLM (lihat roadmap Tahap 3 & 5)."
    )

    _render_banner()

    # Init chat history
    if "copilot_messages" not in st.session_state:
        st.session_state.copilot_messages = [{
            "role": "assistant",
            "content": (
                "Halo! Saya AI Copilot **dasar**. Saya hanya menjawab dengan data tersedia. "
                "Coba klik salah satu **Quick Prompts** di atas, atau ketik pertanyaan Anda "
                "langsung di kolom bawah."
            ),
        }]

    # Quick prompts
    _render_quick_prompts()

    st.markdown("---")

    # Hints
    _render_hints()

    st.markdown("---")

    # Chat history
    for m in st.session_state.copilot_messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    # Handle quick prompt (dari tombol)
    quick = st.session_state.pop("_quick_prompt", None)
    if quick:
        st.session_state.copilot_messages.append({"role": "user", "content": quick})
        response = _answer(ds, scope, quick.lower())
        st.session_state.copilot_messages.append({"role": "assistant", "content": response})
        st.rerun()

    # Chat input
    prompt = st.chat_input("Tanyakan tentang data produksi...")
    if not prompt:
        return

    st.session_state.copilot_messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    response = _answer(ds, scope, prompt.lower())
    st.session_state.copilot_messages.append({"role": "assistant", "content": response})
    with st.chat_message("assistant"):
        st.markdown(response)