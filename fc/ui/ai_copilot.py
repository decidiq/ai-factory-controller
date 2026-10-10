"""AI Copilot — Hybrid AI (keyword + LLM eksternal) dengan source badge."""
import hashlib

import streamlit as st

from ..intel.llm_provider import get_provider
from ..kpi import Scope, summarize
from ..pipeline import Dataset


# ==================== CONTEXT BUILDER ====================

def _build_context(ds: Dataset, scope: Scope) -> str:
    """Build KPI context ringkas untuk dikirim ke LLM."""
    try:
        s = summarize(ds, scope)
        parts = ["=== KPI UTAMA ==="]

        if s.output_kg.available:
            parts.append(f"Total Output: {s.output_kg.value:,.0f} Kg")
        if s.yield_pct.available:
            parts.append(f"Yield: {s.yield_pct.value:.2f}%")
        if s.scrap_pct.available:
            parts.append(f"Scrap: {s.scrap_pct.value:.2f}%")
        if s.oee.oee.available:
            parts.append(f"OEE: {s.oee.oee.value:.2f}%")
        if s.cogm.available:
            parts.append(f"COGM: Rp {s.cogm.value:,.0f}")
        if s.cost_per_kg.available:
            parts.append(f"Cost/Kg: Rp {s.cost_per_kg.value:,.0f}")

        if s.breakdown:
            parts.append("\n=== KOMPONEN BIAYA ===")
            for k, v in s.breakdown.items():
                parts.append(f"  - {k}: Rp {v:,.0f}")

        plants = ds.plants()
        if plants:
            parts.append(f"\n=== PLANT AKTIF ===\n  {', '.join(plants)}")

        lines = ds.lines()
        if lines:
            parts.append(f"\n=== LINE AKTIF ===\n  {', '.join(lines[:10])}")

        return "\n".join(parts)
    except Exception as e:
        return f"Data tidak tersedia: {e}"


# ==================== LLM CACHE ====================

def _ask_llm_cached(provider, question: str, context: str, history: list) -> str:
    """Cache hasil LLM per pertanyaan+context."""
    key_raw = f"{provider.name}|{question}|{context[:500]}"
    key = hashlib.md5(key_raw.encode()).hexdigest()
    cache = st.session_state.setdefault("_llm_cache", {})
    if key in cache:
        return cache[key]
    try:
        answer = provider.ask(question, context, history=history)
        cache[key] = answer
        return answer
    except Exception as e:
        raise RuntimeError(str(e))


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

/* ===== SOURCE BADGE ===== */
.src-badge {
    display: inline-block;
    font-size: 0.62rem;
    font-weight: 800;
    letter-spacing: 1px;
    padding: 3px 10px;
    border-radius: 999px;
    margin-bottom: 8px;
    text-transform: uppercase;
    border: 1px solid;
}
.src-groq     { background: #ECFDF5; color: #047857; border-color: #6EE7B7; }
.src-keyword  { background: #EFF6FF; color: #1D4ED8; border-color: #93C5FD; }
.src-fallback { background: #FFFBEB; color: #B45309; border-color: #FCD34D; }
.src-system   { background: #F1F5F9; color: #475569; border-color: #CBD5E1; }
</style>
"""


def _inject_css():
    st.markdown(GLASS_CSS, unsafe_allow_html=True)


# ==================== SOURCE BADGE RENDER ====================

_SOURCE_META = {
    "groq":     ("🟢 GROQ",       "src-groq"),
    "keyword":  ("🔵 KEYWORD",    "src-keyword"),
    "fallback": ("🟠 FALLBACK",   "src-fallback"),
    "system":   ("⚪ SISTEM",     "src-system"),
}


def _render_badge(source: str) -> None:
    """Render badge kecil di atas pesan AI."""
    if not source:
        return
    label, cls = _SOURCE_META.get(source, _SOURCE_META["system"])
    html = f'<span class="src-badge {cls}">{label}</span>'
    st.markdown(html, unsafe_allow_html=True)


# ==================== BANNER ====================
def _render_banner():
    html = (
        f'<div class="ai-banner">'
        f'<div class="ai-banner-label">🤖 AI COPILOT</div>'
        f'<div class="ai-banner-title">Tanya data pabrik dalam bahasa natural</div>'
        f'<div class="ai-banner-desc">'
        f'Mode AI Lanjutan (Groq) aktif → bisa jawab pertanyaan bebas. '
        f'Mode dasar → keyword: <strong>output</strong>, <strong>yield</strong>, '
        f'<strong>scrap</strong>, <strong>oee</strong>, <strong>cogm</strong>, '
        f'<strong>cost/kg</strong>.'
        f'</div>'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


# ==================== QUICK PROMPTS ====================
def _render_quick_prompts():
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
            if st.button(label, use_container_width=True, key=f"quick_{label}"):
                st.session_state["_quick_prompt"] = full_prompt
                st.rerun()


# ==================== ANSWER (KEYWORD MODE) ====================
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

    return ("Maaf, saya tidak punya jawaban untuk itu. Mode dasar hanya menjawab: "
            "output, yield, scrap, OEE, COGM, Cost/Kg. "
            "Aktifkan **Mode AI Lanjutan** untuk pertanyaan bebas.")


# ==================== SIDEBAR HINTS ====================
def _render_hints():
    with st.expander("ℹ️ Contoh pertanyaan untuk Mode AI Lanjutan"):
        hints = [
            ("📊", "Output", "Berapa total output produksi bulan ini?"),
            ("🎯", "Yield", "Kenapa yield turun? Apa penyebabnya?"),
            ("🗑️", "Scrap", "Bagaimana cara menurunkan scrap?"),
            ("⚙️", "OEE", "Apa yang bisa dilakukan untuk naikkan OEE?"),
            ("💰", "COGM", "Komponen biaya apa yang paling besar?"),
            ("💵", "Cost/Kg", "Plant mana yang paling efisien dan kenapa?"),
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
    st.caption("Asisten analitik — Hybrid AI (keyword + LLM eksternal).")

    _render_banner()

    # ===== Toggle mode LLM =====
    provider = get_provider("groq")  # Groq (gratis) — fallback ke DeepSeek
    llm_ready = provider is not None

    if llm_ready:
        use_llm = st.toggle(
            "🧠 Mode AI Lanjutan (Groq)",
            value=True,
            help="Jika aktif, pertanyaan dikirim ke Groq untuk jawaban lebih natural. "
                 "Jika gagal, otomatis kembali ke mode keyword."
        )
    else:
        use_llm = False
        st.info(
            "ℹ️ **Mode AI Lanjutan tidak aktif.** "
            "Hubungi admin untuk mengaktifkan (butuh API key Groq atau DeepSeek)."
        )

    if use_llm:
        st.caption(f"🟢 AI Lanjutan aktif · Provider: **{provider.name}**")
    else:
        st.caption("🔵 Mode dasar aktif · Keyword-based (offline)")

    # ===== Legend badge =====
    with st.expander("ℹ️ Arti badge di setiap jawaban"):
        st.markdown(
            "- 🟢 **GROQ** — Jawaban dari AI Groq (bahasa natural + analisis)\n"
            "- 🔵 **KEYWORD** — Jawaban dari mode dasar (angka saja)\n"
            "- 🟠 **FALLBACK** — Toggle ON tapi Groq error → balik ke keyword\n"
            "- ⚪ **SISTEM** — Pesan pembuka dari aplikasi"
        )

    # ===== Init chat history =====
    if "copilot_messages" not in st.session_state:
        st.session_state.copilot_messages = [{
            "role": "assistant",
            "content": (
                "Halo! Saya **Decidiq AI Copilot**. "
                "Tanya apa saja tentang data pabrik Anda — saya akan jawab berdasarkan KPI terkini."
            ),
            "source": "system",
        }]

    # ===== Quick prompts =====
    _render_quick_prompts()

    st.markdown("---")

    # ===== Hints =====
    _render_hints()

    st.markdown("---")

    # ===== Chat history =====
    for m in st.session_state.copilot_messages:
        with st.chat_message(m["role"]):
            if m["role"] == "assistant":
                _render_badge(m.get("source", "system"))
            st.markdown(m["content"])

    # ===== Helper: proses pertanyaan =====
    def _process(question: str):
        st.session_state.copilot_messages.append(
            {"role": "user", "content": question}
        )

        source = "keyword"  # default

        if use_llm and llm_ready:
            with st.spinner("🤖 AI sedang menganalisis..."):
                context = _build_context(ds, scope)
                history = [
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.copilot_messages[-5:]
                    if m["role"] in ("user", "assistant")
                ][:-1]

                try:
                    answer = _ask_llm_cached(provider, question, context, history)
                    source = provider.name  # "groq" atau "deepseek"
                except Exception as e:
                    # Fallback ke keyword
                    answer = f"_(Fallback ke mode dasar: {e})_\n\n" + _answer(
                        ds, scope, question.lower()
                    )
                    source = "fallback"
        else:
            answer = _answer(ds, scope, question.lower())
            source = "keyword"

        st.session_state.copilot_messages.append(
            {"role": "assistant", "content": answer, "source": source}
        )

    # ===== Handle quick prompt =====
    quick = st.session_state.pop("_quick_prompt", None)
    if quick:
        _process(quick)
        st.rerun()

    # ===== Chat input =====
    prompt = st.chat_input("Tanyakan tentang data produksi...")
    if not prompt:
        return

    with st.chat_message("user"):
        st.markdown(prompt)
    _process(prompt)
    st.rerun()