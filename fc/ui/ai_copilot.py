"""AI Copilot — Hybrid AI (DARK)."""
import hashlib
import math

import streamlit as st

from ..intel.llm_provider import get_provider
from ..kpi import Scope, summarize
from ..pipeline import Dataset


def _fmt_thousand(v) -> str:
    try:
        if v is None: return "—"
        f = float(v)
        if math.isnan(f) or math.isinf(f): return "—"
        return f"{f:,.0f}".replace(",", ".")
    except (ValueError, TypeError):
        return str(v) if v is not None else "—"


def _build_context(ds: Dataset, scope: Scope) -> str:
    try:
        s = summarize(ds, scope)
        parts = ["=== KPI UTAMA ==="]
        if s.output_kg.available:
            parts.append(f"Total Output: {_fmt_thousand(s.output_kg.value)} Kg")
        if s.yield_pct.available:
            parts.append(f"Yield: {s.yield_pct.value:.2f}%")
        if s.scrap_pct.available:
            parts.append(f"Scrap: {s.scrap_pct.value:.2f}%")
        if s.oee.oee.available:
            parts.append(f"OEE: {s.oee.oee.value:.2f}%")
        if s.cogm.available:
            parts.append(f"COGM: Rp {_fmt_thousand(s.cogm.value)}")
        if s.cost_per_kg.available:
            parts.append(f"Cost/Kg: Rp {_fmt_thousand(s.cost_per_kg.value)}")
        if s.breakdown:
            parts.append("\n=== KOMPONEN BIAYA ===")
            for k, v in s.breakdown.items():
                parts.append(f"  - {k}: Rp {_fmt_thousand(v)}")
        plants = ds.plants()
        if plants:
            parts.append(f"\n=== PLANT AKTIF ===\n  {', '.join(plants)}")
        lines = ds.lines()
        if lines:
            parts.append(f"\n=== LINE AKTIF ===\n  {', '.join(lines[:10])}")
        return "\n".join(parts)
    except Exception as e:
        return f"Data tidak tersedia: {e}"


def _ask_llm_cached(provider, question: str, context: str, history: list) -> str:
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


GLASS_CSS = """
<style>
.ai-banner {
    background: linear-gradient(110deg, #30265e, #211b47 55%, #171b3c);
    border-radius: 16px;
    padding: 24px 30px;
    color: #ffffff;
    box-shadow: 0 9px 30px rgba(6, 9, 23, 0.13);
    border: 1px solid #5e5090;
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
    background: radial-gradient(circle, rgba(164, 137, 255, 0.35) 0%, transparent 70%);
    pointer-events: none;
}
.ai-banner-label {
    font-size: 0.62rem;
    font-weight: 800;
    letter-spacing: 0.12em;
    color: #c9b9f8;
    text-transform: uppercase;
    margin-bottom: 8px;
    position: relative;
    z-index: 1;
}
.ai-banner-title {
    font-size: 1.5rem;
    font-weight: 800;
    color: #ffffff;
    letter-spacing: -0.03em;
    line-height: 1.15;
    margin-bottom: 8px;
    position: relative;
    z-index: 1;
}
.ai-banner-desc {
    font-size: 0.85rem;
    color: #dce0f4;
    line-height: 1.5;
    max-width: 700px;
    position: relative;
    z-index: 1;
}
.ai-banner-desc strong { color: #f7d578; }

.ai-hint-card {
    background: #1b1e3e;
    border: 1px solid #343858;
    border-radius: 12px;
    padding: 14px 18px;
    margin-bottom: 10px;
    box-shadow: 0 9px 30px rgba(6, 9, 23, 0.13);
    display: flex;
    align-items: start;
    gap: 12px;
}
.ai-hint-icon { font-size: 1.4rem; flex-shrink: 0; line-height: 1; }
.ai-hint-title {
    font-size: 0.85rem;
    font-weight: 700;
    color: #f5f6ff;
    margin-bottom: 3px;
}
.ai-hint-desc {
    font-size: 0.78rem;
    color: #adb6d5;
    line-height: 1.45;
}

.src-badge {
    display: inline-block;
    font-size: 0.6rem;
    font-weight: 800;
    letter-spacing: 0.08em;
    padding: 3px 10px;
    border-radius: 999px;
    margin-bottom: 8px;
    text-transform: uppercase;
    border: 1px solid;
}
.src-groq     { background: #172d35; color: #77edb4; border-color: #276956; }
.src-keyword  { background: #242748; color: #71d5e9; border-color: #3c4060; }
.src-fallback { background: #302b30; color: #f7d578; border-color: #756036; }
.src-system   { background: #242748; color: #adb6d5; border-color: #343858; }
</style>
"""


def _inject_css():
    st.markdown(GLASS_CSS, unsafe_allow_html=True)


_SOURCE_META = {
    "groq": ("🟢 GROQ", "src-groq"),
    "keyword": ("🔵 KEYWORD", "src-keyword"),
    "fallback": ("🟠 FALLBACK", "src-fallback"),
    "system": ("⚪ SISTEM", "src-system"),
}


def _render_badge(source: str) -> None:
    if not source:
        return
    label, cls = _SOURCE_META.get(source, _SOURCE_META["system"])
    st.markdown(f'<span class="src-badge {cls}">{label}</span>',
                unsafe_allow_html=True)


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
        f'</div></div>')
    st.markdown(html, unsafe_allow_html=True)


def _render_quick_prompts():
    st.markdown("##### ⚡ Quick Prompts")
    st.caption("Klik salah satu untuk bertanya langsung.")
    prompts = [("📊 Output", "Berapa total output produksi?"),
               ("🎯 Yield", "Berapa yield saat ini?"),
               ("🗑️ Scrap", "Berapa scrap rate sekarang?"),
               ("⚙️ OEE", "Berapa nilai OEE?"),
               ("💰 COGM", "Berapa total COGM?"),
               ("💵 Cost/Kg", "Berapa cost per kg?")]
    cols = st.columns(6, gap="small")
    for col, (label, full_prompt) in zip(cols, prompts):
        with col:
            if st.button(label, width='stretch', key=f"quick_{label}"):
                st.session_state["_quick_prompt"] = full_prompt
                st.rerun()


def _answer(ds, scope, q):
    s = summarize(ds, scope)

    def _v(kpi, label, fmt="{:,.2f}"):
        return (f"**{label}**: {fmt.format(kpi.value)}" if kpi.available
                else f"**{label}**: data tidak tersedia ({kpi.note})")

    if any(k in q for k in ("output", "produksi")):
        if s.output_kg.available:
            return f"**Total Output**: {_fmt_thousand(s.output_kg.value)} Kg"
    if "yield" in q:
        return _v(s.yield_pct, "Yield", "{:.2f}%")
    if "scrap" in q:
        return _v(s.scrap_pct, "Scrap", "{:.2f}%")
    if "oee" in q:
        return _v(s.oee.oee, "OEE", "{:.2f}%")
    if "cogm" in q or "total biaya" in q:
        if s.cogm.available:
            return f"**COGM**: Rp {_fmt_thousand(s.cogm.value)}"
    if "cost/kg" in q or "cost per kg" in q:
        if s.cost_per_kg.available:
            return f"**Cost/Kg**: Rp {_fmt_thousand(s.cost_per_kg.value)}"
    return ("Maaf, saya tidak punya jawaban untuk itu. Mode dasar hanya menjawab: "
            "output, yield, scrap, OEE, COGM, Cost/Kg. "
            "Aktifkan **Mode AI Lanjutan** untuk pertanyaan bebas.")


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
                f'</div></div>')
            st.markdown(html, unsafe_allow_html=True)


def render(ds: Dataset, scope: Scope) -> None:
    _inject_css()
    st.title("🤖 AI Copilot")
    st.caption("Asisten analitik — Hybrid AI (keyword + LLM eksternal).")
    _render_banner()

    provider = get_provider("groq")
    llm_ready = provider is not None

    if llm_ready:
        use_llm = st.toggle(
            "🧠 Mode AI Lanjutan (Groq)", value=True,
            help="Jika aktif, pertanyaan dikirim ke Groq untuk jawaban lebih natural. "
                 "Jika gagal, otomatis kembali ke mode keyword.")
    else:
        use_llm = False
        st.info("ℹ️ **Mode AI Lanjutan tidak aktif.** "
                "Hubungi admin untuk mengaktifkan (butuh API key Groq atau DeepSeek).")

    if use_llm:
        st.caption(f"🟢 AI Lanjutan aktif · Provider: **{provider.name}**")
    else:
        st.caption("🔵 Mode dasar aktif · Keyword-based (offline)")

    with st.expander("ℹ️ Arti badge di setiap jawaban"):
        st.markdown(
            "- 🟢 **GROQ** — Jawaban dari AI Groq (bahasa natural + analisis)\n"
            "- 🔵 **KEYWORD** — Jawaban dari mode dasar (angka saja)\n"
            "- 🟠 **FALLBACK** — Toggle ON tapi Groq error → balik ke keyword\n"
            "- ⚪ **SISTEM** — Pesan pembuka dari aplikasi")

    if "copilot_messages" not in st.session_state:
        st.session_state.copilot_messages = [{
            "role": "assistant",
            "content": ("Halo! Saya **Decidiq AI Copilot**. "
                        "Tanya apa saja tentang data pabrik Anda — saya akan jawab "
                        "berdasarkan KPI terkini."),
            "source": "system"}]

    _render_quick_prompts()
    st.markdown("---")
    _render_hints()
    st.markdown("---")

    for m in st.session_state.copilot_messages:
        with st.chat_message(m["role"]):
            if m["role"] == "assistant":
                _render_badge(m.get("source", "system"))
            st.markdown(m["content"])

    def _process(question: str):
        st.session_state.copilot_messages.append({"role": "user", "content": question})
        source = "keyword"
        if use_llm and llm_ready:
            with st.spinner("🤖 AI sedang menganalisis..."):
                context = _build_context(ds, scope)
                history = [{"role": m["role"], "content": m["content"]}
                           for m in st.session_state.copilot_messages[-5:]
                           if m["role"] in ("user", "assistant")][:-1]
                try:
                    answer = _ask_llm_cached(provider, question, context, history)
                    source = provider.name
                except Exception as e:
                    answer = f"_(Fallback ke mode dasar: {e})_\n\n" + _answer(ds, scope, question.lower())
                    source = "fallback"
        else:
            answer = _answer(ds, scope, question.lower())
            source = "keyword"
        st.session_state.copilot_messages.append(
            {"role": "assistant", "content": answer, "source": source})

    quick = st.session_state.pop("_quick_prompt", None)
    if quick:
        _process(quick)
        st.rerun()

    prompt = st.chat_input("Tanyakan tentang data produksi...")
    if not prompt:
        return
    with st.chat_message("user"):
        st.markdown(prompt)
    _process(prompt)
    st.rerun()