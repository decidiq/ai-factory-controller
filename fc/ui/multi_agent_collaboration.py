"""Multi-Agent Collaboration — Fase 5C (FUNGSIONAL).

Beberapa agent bekerja bareng untuk 1 task kompleks:
- Pilih mode Auto (executive pilih agent) atau Manual (user pilih)
- Jalankan setiap agent
- Executive sintesis jawaban mereka
- Lihat breakdown per-agent + konsensus
"""
from datetime import datetime

import streamlit as st

from fc.agents import (
    list_agents,
    CollaborativeOrchestrator,
    agent_memory,
)


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
    background: radial-gradient(circle, rgba(164, 137, 255, 0.28) 0%, transparent 70%);
}
.mac-hero-badge {
    display: inline-block;
    background: rgba(164, 137, 255, 0.18);
    color: #c4aaff;
    font-size: 0.66rem;
    font-weight: 800;
    letter-spacing: 0.12em;
    padding: 5px 12px;
    border-radius: 999px;
    border: 1px solid rgba(164, 137, 255, 0.5);
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
.mac-hero-sub strong { color: #c4aaff; }

.mac-synth {
    background: linear-gradient(145deg, #232651, #1a1d3d);
    border: 1px solid #4a4180;
    border-left: 4px solid #a489ff;
    border-radius: 14px;
    padding: 22px 26px;
    margin-bottom: 20px;
    box-shadow: 0 9px 30px rgba(6, 9, 23, 0.35);
}
.mac-synth-label {
    color: #c4aaff;
    font-size: 0.66rem;
    font-weight: 800;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-bottom: 8px;
}

.mac-meta {
    background: #1b1e3e;
    border: 1px solid #343858;
    border-left: 4px solid #a489ff;
    border-radius: 10px;
    padding: 12px 16px;
    margin-top: 14px;
    font-size: 0.8rem;
    color: #99a2c9;
}
.mac-meta strong { color: #f7d578; }
.mac-meta .tool-pill {
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


QUICK_PROMPTS = [
    "Bagaimana kondisi pabrik minggu ini?",
    "Apa 3 isu paling prioritas saat ini?",
    "Analisis lengkap: produksi, stok, dan biaya",
]


def _is_demo_mode() -> bool:
    try:
        if st.secrets.get("DEMO_MODE", False):
            return True
        try:
            host = st.context.headers.get("Host", "")
            if ".streamlit.app" in host:
                return True
        except Exception:
            pass
    except Exception:
        pass
    return False


def _inject_css():
    st.markdown(CSS, unsafe_allow_html=True)


def _ensure_state():
    if "_collab_history" not in st.session_state:
        st.session_state["_collab_history"] = []
    if "_collab_task_input" not in st.session_state:
        st.session_state["_collab_task_input"] = ""
    if "_session_id" not in st.session_state:
        import uuid
        st.session_state["_session_id"] = str(uuid.uuid4())[:8]


def _render_header():
    html = (
        '<div class="mac-hero">'
        '<div class="mac-hero-badge">🤝 FASE 5C — KOLABORASI AKTIF</div>'
        '<div class="mac-hero-title">Multi-Agent Collaboration</div>'
        '<div class="mac-hero-sub">'
        'Beberapa agent bekerja <strong>bersama</strong> untuk 1 task kompleks. '
        'Setiap agent memberi perspektif dari domainnya, lalu '
        '<strong>Executive Advisor</strong> menyintesis konsensus dan prioritas.'
        '</div></div>'
    )
    st.markdown(html, unsafe_allow_html=True)

    if _is_demo_mode():
        st.info(
            "🔒 **Mode Demo** — sintesis AI dinonaktifkan. "
            "Setiap agent tetap menampilkan data mentah dari tools."
        )


def _render_sidebar():
    st.sidebar.markdown("### 🤝 Mode Kolaborasi")
    mode = st.sidebar.radio(
        "Mode",
        ["auto", "manual"],
        format_func=lambda x: {
            "auto": "🪄 Auto — Executive pilih agent",
            "manual": "🎯 Manual — Saya pilih agent",
        }[x],
        key="_collab_mode",
    )

    selected = []
    if mode == "manual":
        agents = list_agents()
        options = {a["name"]: f"{a['role']}" for a in agents}
        selected = st.sidebar.multiselect(
            "Pilih agent (2-4 disarankan)",
            options=list(options.keys()),
            default=["production", "inventory", "cost"],
            format_func=lambda x: options.get(x, x),
            key="_collab_selected",
        )

    st.sidebar.caption(
        "💡 Auto: keyword task → pilih agent yang relevan. "
        "Manual: kontrol penuh."
    )
    return mode, selected


def _render_prompts():
    st.markdown("**💡 Quick prompts**")
    cols = st.columns(len(QUICK_PROMPTS))
    for i, p in enumerate(QUICK_PROMPTS):
        with cols[i]:
            if st.button(p, key=f"_collab_prompt_{i}", use_container_width=True):
                st.session_state["_collab_task_input"] = p
                st.rerun()


def _render_synthesis(synth: str, synth_error):
    if not synth and not synth_error:
        return
    html = (
        '<div class="mac-synth">'
        '<div class="mac-synth-label">🧠 Sintesis Executive Advisor</div>'
        '</div>'
    )
    st.markdown(html, unsafe_allow_html=True)
    if synth_error:
        st.warning(f"⚠️ Sintesis gagal: {synth_error}")
    if synth:
        st.markdown(synth)


def _render_agent_results(result):
    st.markdown("### 🎯 Perspektif per Agent")
    if not result.agent_results:
        st.info("Tidak ada agent yang dijalankan.")
        return

    for name, r in result.agent_results.items():
        status = "✅" if r.ok else "❌"
        confidence = f"{r.confidence}%" if r.confidence else "—"
        title = f"{status} **{name}** · confidence {confidence} · {r.duration_ms} ms"
        with st.expander(title, expanded=False):
            if r.error and "Mode Demo" not in r.error:
                st.warning(f"⚠️ {r.error}")
            st.markdown(r.content)

            tools_html = " ".join(
                f'<span class="tool-pill">{t}</span>' for t in r.source_tools
            ) or '<em style="color:#666">(tidak ada tool)</em>'
            st.markdown(
                f'<div class="mac-meta">'
                f'<strong>Tools:</strong> {tools_html}'
                f'</div>',
                unsafe_allow_html=True,
            )

            with st.expander("🔍 Lihat data mentah"):
                for tool_name, payload in r.data.items():
                    ok = payload.get("ok")
                    s = "✅" if ok else "❌"
                    st.markdown(f"**{s} `{tool_name}`**")
                    if ok:
                        st.code(payload.get("text", ""), language="text")
                    else:
                        st.error(payload.get("error", "unknown error"))


def _render_meta(result):
    agents_html = " ".join(
        f'<span class="tool-pill">{a}</span>' for a in result.agents_run
    )
    meta = (
        f'<div class="mac-meta">'
        f'<strong>Mode:</strong> {result.mode} &nbsp;·&nbsp; '
        f'<strong>Agents:</strong> {agents_html} &nbsp;·&nbsp; '
        f'<strong>Avg Confidence:</strong> {result.avg_confidence}% &nbsp;·&nbsp; '
        f'<strong>Total Durasi:</strong> {result.total_duration_ms} ms'
        f'</div>'
    )
    st.markdown(meta, unsafe_allow_html=True)


def _render_history():
    hist = st.session_state["_collab_history"]
    if not hist:
        return
    with st.expander(f"📚 Riwayat Kolaborasi ({len(hist)} run)"):
        for h in reversed(hist[-10:]):
            st.markdown(
                f"**{h['time']}** — mode `{h['mode']}` — "
                f"agents `{', '.join(h['agents'])}` — "
                f"avg conf {h['confidence']}% — {h['duration_ms']} ms"
            )
            st.caption(h["task"])
            st.markdown("---")


def render(ds, scope) -> None:
    _inject_css()
    _ensure_state()
    _render_header()

    mode, selected = _render_sidebar()
    _render_prompts()

    st.markdown("---")
    st.markdown("**✍️ Tugas / Pertanyaan Kompleks**")
    st.text_area(
        "Tugas",
        placeholder="Contoh: Bagaimana kondisi pabrik minggu ini?",
        label_visibility="collapsed",
        height=90,
        key="_collab_task_input",
    )

    c1, c2 = st.columns([1, 4])
    with c1:
        run_btn = st.button("🤝 Kolaborasi", type="primary", use_container_width=True)
    with c2:
        if st.button("🗑️ Bersihkan history", use_container_width=True):
            st.session_state["_collab_history"] = []
            st.rerun()

    task = st.session_state.get("_collab_task_input", "")

    if run_btn and task.strip():
        if mode == "manual" and len(selected) < 2:
            st.error("Pilih minimal 2 agent untuk mode manual.")
            return

        with st.spinner("Menjalankan beberapa agent…"):
            try:
                orch = CollaborativeOrchestrator()
                result = orch.run(
                    task, ds, scope,
                    agents=selected if mode == "manual" else None,
                    mode=mode,
                )
            except Exception as exc:
                st.error(f"❌ Gagal menjalankan kolaborasi: `{exc}`")
                return

        st.session_state["_collab_history"].append({
            "time": datetime.now().strftime("%H:%M:%S"),
            "task": task,
            "mode": mode,
            "agents": result.agents_run,
            "confidence": result.avg_confidence,
            "duration_ms": result.total_duration_ms,
        })

        _render_meta(result)
        _render_synthesis(result.synthesis, result.synthesis_error)
        _render_agent_results(result)

    _render_history()