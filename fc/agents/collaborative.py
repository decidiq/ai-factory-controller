"""Collaborative Orchestrator — beberapa agent kerja bareng untuk 1 task."""
import re
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Iterator

from fc.intel.llm_provider import get_provider, LLMProvider
from .base import AgentResult, _is_demo_mode
from .registry import get_agent


@dataclass
class CollaborativeResult:
    task: str
    mode: str
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
    DEFAULT_AGENTS = ("production", "inventory", "cost")

    def __init__(self, llm: Optional[LLMProvider] = None):
        self.llm = llm or get_provider()

    def pick_agents(self, task: str, max_agents: int = 4) -> List[str]:
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

        if not matched or has_executive_kw:
            return ["production", "inventory", "cost", "executive"][:max_agents]

        if len(matched) == 1:
            return (matched + ["executive"])[:max_agents]

        return matched[:max_agents]

    def run(self, task: str, ds, scope, agents: Optional[List[str]] = None, mode: str = "auto", skip_synthesis: bool = False) -> CollaborativeResult:
        t0 = time.time()
        if mode == "auto" or not agents:
            agent_names = self.pick_agents(task)
        else:
            agent_names = list(agents)

        results: Dict[str, AgentResult] = {}
        for name in agent_names:
            try:
                a = get_agent(name)
                results[name] = a.run(task, ds, scope)
            except Exception as e:
                results[name] = AgentResult(agent=name, content=f"❌ Gagal menjalankan `{name}`: `{e}`", error=str(e))

        synthesis = ""
        synth_err = None
        # Skip synthesis if requested (untuk streaming di UI)
        if not skip_synthesis and not _is_demo_mode() and self.llm and self.llm.is_available():
            try:
                synthesis = self._synthesize(task, results)
            except Exception as e:
                synth_err = str(e)

        confs = [r.confidence for r in results.values() if r.confidence > 0]
        avg_conf = int(sum(confs) / len(confs)) if confs else 0

        return CollaborativeResult(
            task=task, mode=mode, agent_results=results, synthesis=synthesis,
            synthesis_error=synth_err, total_duration_ms=int((time.time() - t0) * 1000),
            avg_confidence=avg_conf, agents_run=agent_names,
        )

    def _synthesize(self, task: str, results: Dict[str, AgentResult]) -> str:
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

    def stream_synthesis(self, task: str, results: Dict[str, AgentResult]) -> Iterator[str]:
        if _is_demo_mode() or not self.llm or not self.llm.is_available():
            yield "🔒 **Mode Demo** — sintesis AI dinonaktifkan."
            return

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

        try:
            for chunk in self.llm.ask_stream(question=question, context=ctx):
                yield chunk
        except Exception as e:
            yield f"\n\n⚠️ Gagal sintesis: {e}"