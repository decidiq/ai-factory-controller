"""BaseAgent — abstraksi untuk semua agent di Fase 5.

Prinsip desain:
1. Agent TIDAK boleh mengarang angka — semua data dari tools.
2. Agent adalah READ-ONLY. Tidak ada eksekusi otomatis.
3. Setiap output punya confidence score + source tools (untuk audit).
4. Reuse LLMProvider yang sudah ada (Groq/DeepSeek).
5. Reuse AgentMemory untuk recall & save (Fase 5A).
6. Demo mode: LLM off by design di cloud (Fase 5 — keamanan).
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import time

from fc.intel.llm_provider import get_provider, LLMProvider


def _is_demo_mode() -> bool:
    """Deteksi apakah app jalan di cloud/demo (LLM off by design).

    Prioritas:
    1. Explicit flag: secrets.DEMO_MODE = true
    2. Auto-detect host *.streamlit.app
    """
    try:
        import streamlit as st
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


@dataclass
class AgentResult:
    agent: str
    content: str
    data: Dict[str, Any] = field(default_factory=dict)
    confidence: int = 0
    source_tools: List[str] = field(default_factory=list)
    duration_ms: int = 0
    error: Optional[str] = None

    @property
    def ok(self) -> bool:
        return self.error is None


class BaseAgent(ABC):

    name: str = "base"
    role: str = ""
    description: str = ""
    tools_allowed: tuple = ()
    memory_enabled: bool = True

    system_prompt: str = (
        "Anda adalah agen analitik pabrik manufaktur untuk Decidiq.\n"
        "ATURAN:\n"
        "1. Jawab dalam Bahasa Indonesia profesional.\n"
        "2. HANYA gunakan angka dari DATA KONTEKS — jangan mengarang.\n"
        "3. Kalau data kosong, katakan 'data tidak tersedia'.\n"
        "4. Format: **Ringkasan** (2-3 kalimat) → **Temuan** (bullet) "
        "→ **Rekomendasi** (bullet dengan dampak Rp kalau ada).\n"
        "5. Maksimal 250 kata.\n"
    )

    def __init__(self, llm: Optional[LLMProvider] = None):
        self.llm = llm or get_provider()

    @abstractmethod
    def build_context(self, ds, scope, **kwargs) -> Dict[str, Any]:
        ...

    def build_question(self, task: str, context: Dict[str, Any]) -> str:
        return task

    def estimate_confidence(self, context: Dict[str, Any]) -> int:
        ok_count = sum(1 for v in context.values() if v.get("ok"))
        return min(100, ok_count * 30) if ok_count else 0

    # ========== Main entry ==========
    def run(self, task: str, ds, scope, **kwargs) -> AgentResult:
        t0 = time.time()

        # 1. Ambil context dari tools
        try:
            context = self.build_context(ds, scope, **kwargs)
        except Exception as exc:
            return AgentResult(
                agent=self.name,
                content=f"❌ Gagal ambil konteks: `{exc}`",
                error=str(exc),
                duration_ms=int((time.time() - t0) * 1000),
            )

        source_tools = [k for k, v in context.items() if v.get("ok")]

        # 2. Inject memori (lazy import — hindari circular)
        memory_text = ""
        if self.memory_enabled:
            try:
                from fc.agents.memory import get_context_for
                memory_text = get_context_for(task, agent=self.name)
            except Exception:
                memory_text = ""

        ctx_text = self._context_to_text(context)
        if memory_text:
            ctx_text = memory_text + "\n\n" + ctx_text

        # 3. Demo mode ATAU LLM tidak tersedia → fallback
        demo_mode = _is_demo_mode()
        if demo_mode or not self.llm or not self.llm.is_available():
            if demo_mode:
                msg = ("🔒 **Mode Demo** — narasi AI dinonaktifkan demi keamanan. "
                       "Menampilkan data mentah dari tools.")
            else:
                msg = ("ℹ️ **LLM tidak tersedia** — mode data mentah. "
                       "Set `GROQ_API_KEY` untuk mengaktifkan narasi AI.")
            result = AgentResult(
                agent=self.name,
                content=msg + "\n\n" + self._fallback_markdown(task, context),
                data=context,
                confidence=self.estimate_confidence(context),
                source_tools=source_tools,
                duration_ms=int((time.time() - t0) * 1000),
                error=msg,
            )
            self._save(result, task, scope)
            return result

        # 4. Panggil LLM
        try:
            answer = self.llm.ask(
                question=self.build_question(task, context),
                context=ctx_text,
            )
            result = AgentResult(
                agent=self.name,
                content=answer,
                data=context,
                confidence=self.estimate_confidence(context),
                source_tools=source_tools,
                duration_ms=int((time.time() - t0) * 1000),
            )
        except Exception as exc:
            result = AgentResult(
                agent=self.name,
                content=self._fallback_markdown(task, context)
                        + f"\n\n⚠️ LLM error: `{exc}`",
                data=context,
                confidence=self.estimate_confidence(context),
                source_tools=source_tools,
                duration_ms=int((time.time() - t0) * 1000),
                error=str(exc),
            )

        # 5. Simpan ke memory
        self._save(result, task, scope)
        return result

    # ========== Memory helper ==========
    def _save(self, result: AgentResult, task: str, scope) -> None:
        if not self.memory_enabled:
            return
        session_id = None
        try:
            import streamlit as st
            session_id = st.session_state.get("_session_id")
        except Exception:
            pass
        try:
            from fc.agents.memory import save_run
            save_run(
                agent=result.agent,
                task=task,
                content=result.content,
                confidence=result.confidence,
                duration_ms=result.duration_ms,
                source_tools=result.source_tools,
                scope=scope,
                session_id=session_id,
                error=result.error,
            )
        except Exception:
            pass

    # ========== Helpers ==========
    def _context_to_text(self, context: Dict[str, Any]) -> str:
        lines = []
        for name, res in context.items():
            if not res.get("ok"):
                lines.append(f"[{name}] ERROR: {res.get('error', '?')}")
                continue
            lines.append(f"[{name}]")
            lines.append(res.get("text", "(tidak ada teks)"))
            lines.append("")
        return "\n".join(lines)

    def _fallback_markdown(self, task: str, context: Dict[str, Any]) -> str:
        lines = [f"**{self.role or self.name}**", "", f"Task: {task}", "", "**Data dari tools:**"]
        for name, res in context.items():
            if res.get("ok"):
                lines.append(f"- ✅ `{name}`: {res.get('text', '')[:200]}")
            else:
                lines.append(f"- ❌ `{name}`: {res.get('error', '?')}")
        return "\n".join(lines)