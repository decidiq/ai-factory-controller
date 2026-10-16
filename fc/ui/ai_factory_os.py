"""AI Factory OS — Multi-Agent Dashboard (Fase 5).

Ganti placeholder 'COMING SOON' jadi dashboard fungsional:
- Pilih agent (auto-route atau manual)
- Ketik task / pakai quick prompts
- Lihat hasil: narasi + confidence + tools used + duration
- Toggle raw data dari tools
- History per session
"""
from datetime import datetime

import streamlit as st

from fc.agents import list_agents, run_orchestrated


CSS = """
<style>
.os-hero {
    background: linear-gradient(110deg, #1a1f4a 0%, #2d2a5e 45%, #1e1b47 100%);
    border-radius: 18px;
    padding: 28px 32px;
    color: #fff;
    border: 1px solid #4a4180;
    margin-bottom: 22px;
    position: relative;
    overflow: hidden;
}
.os-hero::before {
    content: '';
    position: absolute;
    top: -60px; right: -60px;
    width: 220px; height: 220px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(122, 220, 255, 0.25) 0%, transparent 70%);
}
.os-hero-badge {
    display: inline-block;
    background: rgba(122, 220, 255, 0.18);
    color: #7adcff;
    font-size: 0.66rem;
    font-weight: 800;
    letter-spacing: 0.12em;
    padding: 5px 12px;
    border-radius: 999px;
    border: 1px solid rgba(122, 220, 255, 0.5);
    margin-bottom: 12px;
    position: relative;
    z-index: 1;
}
.os-hero-title {
    font-size: 1.7rem;
    font-weight: 800;
    letter-spacing: -0.03em;
    margin-bottom: 8px;
    position: relative;
    z-index: 1;
}
.os-hero-sub {
    font-size: 0.9rem;
    color: #c9cdf0;
    max-width: 720px;
    line-height: 1.55;
    position: relative;
    z-index: 1;
}
.os-hero-sub strong { color: #7adcff; }

.os-meta {
    background: #1b1e3e;
    border: 1px solid #343858;
    border-left: 4px solid #7adcff;
    border-radius: 10px;
    padding: 12px 16px;
    margin-top: 14px;
    font-size: 0.8rem;
    color: #99a2c9;
}
.os-meta strong { color: #f7d578; }
.os-meta .tool-pill {
    display: inline-block;
    background: #242748;
    color: #c4aaff;
    padding: 2px 8px;
    border-radius: 6px;
    border: 1px solid #343858;
    margin-right: 4px;
    font-size: 0.72rem;
}
</style>
"""


QUICK_PROMPTS = {
    "executive": [
        "Ringkas kondisi pabrik minggu ini",
        "Apa 3 isu paling prioritas?",
        "Keputusan apa yang perlu saya ambil?",
    ],
    "production": [
        "Bagaimana yield dan OEE bulan ini?",
        "Ada anomali di data produksi?",
        "Forecast output 7 hari ke depan",
    ],
    "inventory": [
        "Material apa yang berisiko stock-out?",
        "Ada dead stock yang perlu diaudit?",
        "Status stok material kritis",
    ],
    "cost": [
        "Berapa COGM bulan ini?",
        "Di mana peluang penghematan biaya?",
        "Analisis variance biaya produksi",
    ],
    "auto": [
        "Ringkas kondisi pabrik minggu ini",
        "Material apa yang berisiko stock-out?",
        "Berapa COGM bulan ini?",
    ],
}


def _inject_css():
    st.markdown(CSS, unsafe_allow_html=True)


def _ensure_state():
    if "_agents_history" not in st.session_state:
        st.session_state["_agents_history"] = []
    if "_agents_task_input" not in st.session_state:
        st.session_state["_agents_task_input"] = ""


def _render_header():
    html = (
        '<div class="os-hero">'
        '<div class="os-hero-badge">⚡ FASE 5 — AKTIF</div>'
        '<div class="os-hero-title">AI Factory OS</div>'
        '<div class="os-hero-sub">'
        'Orkestrasi <strong>multi-agent</strong> untuk analisis pabrik. '
        'Semua output <strong>read-only</strong> dan berbasis data aktual. '
        'Setiap keputusan tetap di tangan manusia.'
        '</div></div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def _render_sidebar():
    st.sidebar.markdown("### 🤖 Pilih Agent")
    agents = list_agents()
    options = ["auto"] + [a["name"] for a in agents]
    labels = {"auto": "🪄 Auto (orchestrator)"}
    for a in agents:
        labels[a["name"]] = f"• {a['role']}"

    choice = st.sidebar.radio(
        "Agent",
        options,
        format_func=lambda x: labels.get(x, x),
        key="_agents_choice",
    )

    if choice != "auto":
        meta = next((a for a in agents if a["name"] == choice), None)
        if meta:
            st.sidebar.caption(meta["description"])
            st.sidebar.caption(
                "🔧 Tools: " + ", ".join(f"`{t}`" for t in meta["tools"])
            )
    return choice


def _render_prompts(choice: str):
    prompts = QUICK_PROMPTS.get(choice, QUICK_PROMPTS["auto"])
    st.markdown("**💡 Quick prompts**")
    cols = st.columns(len(prompts))
    for i, p in enumerate(prompts):
        with cols[i]:
            if st.button(p, key=f"_agents_prompt_{i}", use_container_width=True):
                st.session_state["_agents_task_input"] = p
                st.rerun()


def _render_result(result, force_agent: str):
    st.markdown("### 📋 Hasil")

    if force_agent == "auto":
        st.caption(f"🪄 Auto-routed ke agent: `{result.agent}`")

    if result.error:
        st.warning(f"⚠️ {result.error}")

    st.markdown(result.content)

    tools_html = " ".join(
        f'<span class="tool-pill">{t}</span>' for t in result.source_tools
    ) or '<em style="color:#666">(tidak ada tool)</em>'

    meta_html = (
        f'<div class="os-meta">'
        f'<strong>Agent:</strong> {result.agent} &nbsp;·&nbsp; '
        f'<strong>Confidence:</strong> {result.confidence}% &nbsp;·&nbsp; '
        f'<strong>Durasi:</strong> {result.duration_ms} ms &nbsp;·&nbsp; '
        f'<strong>Tools:</strong> {tools_html}'
        f'</div>'
    )
    st.markdown(meta_html, unsafe_allow_html=True)

    with st.expander("🔍 Lihat data mentah dari tools"):
        for tool_name, payload in result.data.items():
            ok = payload.get("ok")
            status = "✅" if ok else "❌"
            st.markdown(f"**{status} `{tool_name}`**")
            if ok:
                st.code(payload.get("text", ""), language="text")
            else:
                st.error(payload.get("error", "unknown error"))


def _render_history():
    hist = st.session_state["_agents_history"]
    if not hist:
        return
    with st.expander(f"📚 Riwayat ({len(hist)} run)"):
        for h in reversed(hist[-10:]):
            st.markdown(
                f"**{h['time']}** — `{h['agent']}` — "
                f"confidence {h['confidence']}% — {h['duration_ms']} ms"
            )
            st.caption(h["task"])
            st.markdown("---")


def render(ds, scope) -> None:
    _inject_css()
    _ensure_state()
    _render_header()

    choice = _render_sidebar()
    _render_prompts(choice)

    st.markdown("---")
    st.markdown("**✍️ Tugas / Pertanyaan**")
    st.text_area(
        "Tugas",
        placeholder="Contoh: Ringkas kondisi pabrik minggu ini…",
        label_visibility="collapsed",
        height=90,
        key="_agents_task_input",
    )

    c1, c2 = st.columns([1, 4])
    with c1:
        run_btn = st.button("🚀 Jalankan", type="primary", use_container_width=True)
    with c2:
        if st.button("🗑️ Bersihkan history", use_container_width=True):
            st.session_state["_agents_history"] = []
            st.rerun()

    task = st.session_state.get("_agents_task_input", "")

    if run_btn and task.strip():
        with st.spinner("Menjalankan agent…"):
            try:
                force = None if choice == "auto" else choice
                result = run_orchestrated(task, ds, scope, force_agent=force)
            except Exception as exc:
                st.error(f"❌ Gagal menjalankan agent: `{exc}`")
                return

        st.session_state["_agents_history"].append({
            "time": datetime.now().strftime("%H:%M:%S"),
            "task": task,
            "agent": result.agent,
            "confidence": result.confidence,
            "duration_ms": result.duration_ms,
        })

        _render_result(result, choice)

    _render_history()