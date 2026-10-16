"""BaseAgent — abstraksi untuk semua agent di Fase 5.

Prinsip desain:
1. Agent TIDAK boleh mengarang angka — semua data dari tools.
2. Agent adalah READ-ONLY. Tidak ada eksekusi otomatis.
3. Setiap output punya confidence score + source tools (untuk audit).
4. Reuse LLMProvider yang sudah ada (Groq/DeepSeek).
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import time

from fc.intel.llm_provider import get_provider, LLMProvider


@dataclass
class AgentResult:
    """Hasil dari satu agent run."""
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
    """Abstract base untuk semua agent."""

    name: str = "base"
    role: str = ""
    description: str = ""
    tools_allowed: tuple = ()

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

    # ========== Wajib di-override ==========
    @abstractmethod
    def build_context(self, ds, scope, **kwargs) -> Dict[str, Any]:
        """Kumpulkan data dari tools → dict siap kirim ke LLM.

        Return: {"tool_name": {"ok": bool, "text": str, ...}, ...}
        """
        ...

    # ========== Opsional override ==========
    def build_question(self, task: str, context: Dict[str, Any]) -> str:
        """Default: pakai task langsung."""
        return task

    def estimate_confidence(self, context: Dict[str, Any]) -> int:
        """Default: 100 kalau ada minimal 1 tool success, else 0."""
        ok_count = sum(1 for v in context.values() if v.get("ok"))
        return min(100, ok_count * 30) if ok_count else 0

    # ========== Main entry ==========
    def run(self, task: str, ds, scope, **kwargs) -> AgentResult:
        t0 = time.time()
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
        ctx_text = self._context_to_text(context)

        if not self.llm or not self.llm.is_available():
            return AgentResult(
                agent=self.name,
                content=self._fallback_markdown(task, context),
                data=context,
                confidence=self.estimate_confidence(context),
                source_tools=source_tools,
                duration_ms=int((time.time() - t0) * 1000),
                error="LLM tidak tersedia — menampilkan data mentah",
            )

        try:
            answer = self.llm.ask(
                question=self.build_question(task, context),
                context=ctx_text,
            )
            return AgentResult(
                agent=self.name,
                content=answer,
                data=context,
                confidence=self.estimate_confidence(context),
                source_tools=source_tools,
                duration_ms=int((time.time() - t0) * 1000),
            )
        except Exception as exc:
            return AgentResult(
                agent=self.name,
                content=self._fallback_markdown(task, context)
                        + f"\n\n⚠️ LLM error: `{exc}`",
                data=context,
                confidence=self.estimate_confidence(context),
                source_tools=source_tools,
                duration_ms=int((time.time() - t0) * 1000),
                error=str(exc),
            )

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