"""ExecutiveAgent — cross-domain briefing untuk Director / Factory Manager."""
from typing import Any, Dict

from .base import BaseAgent
from .tools import call_tool
from .production import ProductionAgent
from .inventory import InventoryAgent
from .cost import CostAgent


class ExecutiveAgent(BaseAgent):
    name = "executive"
    role = "Executive Advisor"
    description = "Briefing lintas-domain: produksi, inventory, biaya"
    tools_allowed = ("kpi_summary", "recommendations", "stockout_risk")

    system_prompt = (
        "Anda adalah **Executive Advisor** untuk Director / Factory Manager.\n"
        "Tugas: rangkum kondisi pabrik lintas-domain menjadi briefing eksekutif.\n\n"
        "ATURAN:\n"
        "1. Bahasa Indonesia formal-profesional, singkat.\n"
        "2. HANYA pakai angka dari DATA KONTEKS.\n"
        "3. Format:\n"
        "   **Headline** (1 kalimat kondisi keseluruhan)\n"
        "   **3 Isu Prioritas** (bullet, sebut domain + angka)\n"
        "   **Keputusan yang Dibutuhkan** (bullet, actionable)\n"
        "   **Watch List** (bullet, risiko jangka menengah)\n"
        "4. Maksimal 250 kata. Fokus ke keputusan, bukan detail teknis.\n"
    )

    def build_context(self, ds, scope, **_) -> Dict[str, Any]:
        sub_context = {}
        sub_context["kpi_summary"] = call_tool("kpi_summary", ds, scope)
        sub_context["stockout_risk"] = call_tool("stockout_risk", ds, scope)
        sub_context["recommendations"] = call_tool("recommendations", ds, scope)

        try:
            for AgentCls in (ProductionAgent, InventoryAgent, CostAgent):
                agent = AgentCls(llm=self.llm)
                ctx = agent.build_context(ds, scope)
                txt_parts = []
                for k, v in ctx.items():
                    if v.get("ok"):
                        txt_parts.append(f"[{agent.name}.{k}] {v.get('text', '')}")
                if txt_parts:
                    sub_context[f"agent_{agent.name}"] = {
                        "ok": True,
                        "text": "\n".join(txt_parts),
                        "raw": ctx,
                        "error": None,
                    }
        except Exception:
            pass

        return sub_context