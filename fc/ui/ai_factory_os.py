"""AI Factory OS — Multi-Agent Dashboard (Fase 5).

Ganti placeholder 'COMING SOON' jadi dashboard fungsional:
- Pilih agent (auto-route atau manual)
- Ketik task / pakai quick prompts
- Lihat hasil: narasi + confidence + tools used + duration
- Toggle raw data dari tools
- History per session

Demo mode: LLM off di cloud, banner informatif ditampilkan.
"""
from datetime import datetime

import streamlit as st

from fc.agents import list_agents, run_orchestrated
from fc.agents import memory as agent_memory
from fc.agents import hitl
from fc.ui.auth import get_current_role, get_allowed_agents


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
        "Bagaimana OEE bulan ini?",
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
    "maintenance": [
        "Bagaimana kondisi mesin minggu ini?",
        "Mesin mana yang perlu preventive?",
        "Analisis downtime produksi",
    ],
    "quality": [
        "Bagaimana kualitas produk minggu ini?",
        "Produk mana yang scrap-nya tinggi?",
        "Analisis yield dan defect",
    ],
    "risk": [
        "Apa risiko terbesar saat ini?",
        "Bagaimana mitigasi risiko material?",
        "Prioritas risiko minggu ini",
    ],
    "auto": [
        "Ringkas kondisi pabrik minggu ini",
        "Material apa yang berisiko stock-out?",
        "Berapa COGM bulan ini?",
    ],
}


def _is_demo_mode() -> bool:
    """Cek apakah app di cloud/demo mode."""
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
    if "_agents_history" not in st.session_state:
        st.session_state["_agents_history"] = []
    if "_agents_task_input" not in st.session_state:
        st.session_state["_agents_task_input"] = ""
    if "_session_id" not in st.session_state:
        import uuid
        st.session_state["_session_id"] = str(uuid.uuid4())[:8]


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

    if _is_demo_mode():
        st.info(
            "🔒 **Mode Demo** — narasi AI dinonaktifkan demi keamanan. "
            "Semua data dan tools tetap berfungsi penuh; jawaban LLM diganti "
            "dengan tampilan data mentah. Untuk narasi AI penuh, jalankan "
            "aplikasi secara lokal."
        )


def _render_sidebar():
    st.sidebar.markdown("### 🤖 Pilih Agent")
    
    # Ambil role & filter agent sesuai izin
    role = get_current_role()
    allowed_agent_names = get_allowed_agents(role)
    
    all_agents = list_agents()
    # Hanya tampilkan agent yang diizinkan
    agents = [a for a in all_agents if a["name"] in allowed_agent_names]
    
    # Susun opsi
    options = []
    if "auto" in allowed_agent_names:
        options.append("auto")
    options.extend([a["name"] for a in agents])

    # Label tampilan
    labels = {"auto": "🪄 Auto (orchestrator)"}
    for a in agents:
        labels[a["name"]] = f"• {a['role']}"

    if not options:
        st.sidebar.warning("Role Anda tidak memiliki akses ke agent apapun.")
        return "auto"

    # Set default pilihan jika belum ada atau tidak valid
    if "_agents_choice" not in st.session_state or st.session_state["_agents_choice"] not in options:
        st.session_state["_agents_choice"] = options[0]

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
            
    # Tampilkan info role di sidebar
    st.sidebar.caption(f"🔒 Akses: **{role}**")
    
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

    if result.error and "Mode Demo" not in result.error:
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


def _render_memory_panel():
    """Panel memory: stats + tombol clear."""
    st_stats = agent_memory.stats()

    with st.expander(
        f"🧠 Memori Agent — {st_stats['total']} run tersimpan "
        f"(avg confidence {st_stats['avg_confidence']}%)",
        expanded=False,
    ):
        if st_stats["total"] == 0:
            st.caption("Belum ada riwayat. Jalankan agent untuk mulai membangun memori.")
            return

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total run", st_stats["total"])
        with col2:
            st.metric("Rata-rata confidence", f"{st_stats['avg_confidence']}%")
        with col3:
            st.metric("Rata-rata durasi", f"{st_stats['avg_duration_ms']} ms")

        st.markdown("**Distribusi per agent:**")
        for agent_name, n in st_stats["by_agent"]:
            pct = n / st_stats["total"] * 100
            st.markdown(f"- `{agent_name}` — {n} run ({pct:.0f}%)")

        st.markdown("**Aktivitas 14 hari terakhir:**")
        days = st_stats["by_day"]
        if days:
            for day, n in days[:7]:
                bar = "█" * min(30, n)
                st.caption(f"{day}  {bar} {n}")

        st.markdown("---")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🧹 Hapus run >30 hari", use_container_width=True):
                n = agent_memory.clear_old(days=30)
                st.success(f"✅ {n} run dihapus")
                st.rerun()
        with c2:
            if st.button("🗑️ Hapus semua memori", use_container_width=True):
                n = agent_memory.clear_all()
                st.warning(f"⚠️ {n} run dihapus")
                st.rerun()

def _render_approval_panel(result, task: str):
    """Panel approve/reject setelah agent run."""
    st.markdown("### 🤝 Keputusan Anda")
    st.caption(
        "Setiap keputusan tercatat permanen di Institutional Memory (Fase 3). "
        "Sistem akan belajar dari pola keputusan Anda."
    )

    user = hitl.get_current_user()
    st.caption(f"👤 Login sebagai: **{user}**")

    notes = st.text_input(
        "Catatan (opsional)",
        placeholder="mis. Setuju — perlu verifikasi mesin M-04 dulu",
        key=f"_hitl_notes_{result.agent}",
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        approve = st.button(
            "✅ Setujui", type="primary",
            use_container_width=True,
            key=f"_hitl_approve_{result.agent}",
        )
    with c2:
        reject = st.button(
            "❌ Tolak",
            use_container_width=True,
            key=f"_hitl_reject_{result.agent}",
        )
    with c3:
        noted = st.button(
            "📝 Catat saja",
            use_container_width=True,
            key=f"_hitl_noted_{result.agent}",
        )

    decision = None
    if approve:
        decision = "approve"
    elif reject:
        decision = "reject"
    elif noted:
        decision = "noted"

    if decision:
        rid = hitl.save_decision(
            recommendation=task,
            decision=decision,
            notes=notes,
            user=user,
            agent=result.agent,
            confidence=result.confidence,
            extra_tags=["phase5d", "single-agent"],
        )
        if rid > 0:
            icon = {"approve": "✅", "reject": "❌", "noted": "📝"}[decision]
            st.success(
                f"{icon} Keputusan tersimpan (ID #{rid}). "
                f"Institutional Memory akan update otomatis."
            )
        else:
            st.error("❌ Gagal menyimpan keputusan. Cek log database.")


def _render_recent_decisions():
    """Panel kecil: keputusan terakhir dari user."""
    try:
        recent = hitl.recent_decisions(limit=5)
    except Exception:
        return
    if not recent:
        return

    with st.expander(f"🗳️ Keputusan Terakhir ({len(recent)})"):
        for r in recent:
            decision_raw = str(r.get("decision", "")).lower()
            icon = {"approve": "✅", "reject": "❌", "noted": "📝"}.get(decision_raw, "•")
            rec = str(r.get("recommendation", ""))[:100]
            ts = str(r.get("timestamp", ""))[:16]
            user = r.get("user", "?")
            st.caption(f"{icon} **{ts}** · {user} · {rec}…")
            notes = str(r.get("notes", "")).strip()
            if notes:
                st.caption(f"   💬 _{notes}_")


def render(ds, scope) -> None:
    _inject_css()
    _ensure_state()
    _render_header()

    _render_memory_panel()

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

        # Panel approval HITL
        st.markdown("---")
        _render_approval_panel(result, task)

    _render_history()
    _render_recent_decisions()