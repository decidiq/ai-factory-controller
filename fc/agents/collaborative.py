"""Collaborative Orchestrator — beberapa agent kerja bareng untuk 1 task.

Berbeda dari `orchestrator.py` (1 task → 1 agent), modul ini:
- Pilih otomatis/manual 2-4 agent
- Jalankan setiap agent secara berurutan
- Executive sintesis jawaban mereka
- Deteksi konsensus & kontradiksi
"""
import re
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from fc.intel.llm_provider import get_provider, LLMProvider
from .base import AgentResult, _is_demo_mode
from .registry import get_agent


@dataclass
class CollaborativeResult:
    task: str
    mode: str                       # "auto" | "manual"
    agent_results: Dict[str, AgentResult] = field(default_factory=dict)
    synthesis: str = ""
    synthesis_error: Optional[str] = None
    total_duration_ms: int = 0
    avg_confidence: int = 0
    agents_run: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return any(r.ok for r in self.agent_results.values())


class CollaborativeOrchestrator:
    """Orkestrasi beberapa agent untuk 1 task kompleks."""

    DEFAULT_AGENTS = ("production", "inventory", "cost")

    def __init__(self, llm: Optional[LLMProvider] = None):
        self.llm = llm or get_provider()

    # ============ Pilih agent ============
    def pick_agents(self, task: str, max_agents: int = 4) -> List[str]:
        """Auto-pilih agent berdasarkan keyword matching.

        Logika:
        - Executive keyword / tidak ada match → cross-domain
          (production + inventory + cost + executive)
        - 1 agent match sempit → tambah executive untuk sintesis
        - Multi-agent match → ambil sampai max_agents
        """
        from .orchestrator import ROUTING_RULES
        t = task.lower()

        matched: List[str] = []
        has_executive_kw = False
        for agent_name, patterns in ROUTING_RULES:
            for pat in patterns:
                if re.search(pat, t):
                    if agent_name == "executive":
                        has_executive_kw = True
                    else:
                        matched.append(agent_name)
                    break

        # Task broad/executive ATAU tidak ada match → cross-domain
        if not matched or has_executive_kw:
            return ["production", "inventory", "cost", "executive"][:max_agents]

        # Task sempit (1 agent) → tambah executive untuk sintesis
        if len(matched) == 1:
            return (matched + ["executive"])[:max_agents]

        # Multi-agent match → ambil sampai max
        return matched[:max_agents]

    # ============ Main run ============
    def run(
        self,
        task: str,
        ds,
        scope,
        agents: Optional[List[str]] = None,
        mode: str = "auto",
    ) -> CollaborativeResult:
        t0 = time.time()

        if mode == "auto" or not agents:
            agent_names = self.pick_agents(task)
        else:
            agent_names = list(agents)

        # Jalankan setiap agent secara berurutan
        results: Dict[str, AgentResult] = {}
        for name in agent_names:
            try:
                a = get_agent(name)
                results[name] = a.run(task, ds, scope)
            except Exception as e:
                results[name] = AgentResult(
                    agent=name,
                    content=f"❌ Gagal menjalankan `{name}`: `{e}`",
                    error=str(e),
                )

        # Sintesis oleh executive (kalau LLM tersedia & bukan demo mode)
        synthesis = ""
        synth_err = None
        if not _is_demo_mode() and self.llm and self.llm.is_available():
            try:
                synthesis = self._synthesize(task, results)
            except Exception as e:
                synth_err = str(e)

        # Agregat confidence
        confs = [r.confidence for r in results.values() if r.confidence > 0]
        avg_conf = int(sum(confs) / len(confs)) if confs else 0

        return CollaborativeResult(
            task=task,
            mode=mode,
            agent_results=results,
            synthesis=synthesis,
            synthesis_error=synth_err,
            total_duration_ms=int((time.time() - t0) * 1000),
            avg_confidence=avg_conf,
            agents_run=agent_names,
        )

    # ============ Sintesis ============
    def _synthesize(self, task: str, results: Dict[str, AgentResult]) -> str:
        """Executive sintesis jawaban dari beberapa agent."""
        parts = []
        for name, r in results.items():
            parts.append(f"=== {name.upper()} ===")
            parts.append(r.content)
            parts.append("")
        ctx = "\n".join(parts)

        question = (
            f"TASK USER: {task}\n\n"
            "Beberapa agent sudah menganalisis data. Sintesis jawaban mereka "
            "menjadi briefing eksekutif yang padat dan actionable.\n\n"
            "FORMAT WAJIB:\n"
            "**Konsensus** — 1-2 kalimat ringkas kondisi keseluruhan\n"
            "**3 Prioritas Utama** — bullet lintas-agent dengan angka\n"
            "**Kontradiksi / Perbedaan Pandangan** — bullet (atau 'Tidak ada')\n"
            "**Rekomendasi Keputusan** — bullet actionable untuk pimpinan\n\n"
            "ATURAN:\n"
            "- Bahasa Indonesia profesional.\n"
            "- HANYA pakai angka dari data agent di atas.\n"
            "- Maksimal 250 kata.\n"
            "- Sebut agent mana yang berkontribusi untuk setiap poin."
        )

        return self.llm.ask(question=question, context=ctx)