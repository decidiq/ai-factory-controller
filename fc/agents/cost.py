"""CostAgent — variance COGM, cost per kg, efisiensi biaya."""
from typing import Any, Dict

from .base import BaseAgent
from .tools import call_tool


class CostAgent(BaseAgent):
    name = "cost"
    role = "Cost Controller"
    description = "Analisis biaya, variance COGM, cost per kg"
    tools_allowed = ("kpi_summary", "cost_variance", "recommendations")

    system_prompt = (
        "Anda adalah **Cost Controller** di pabrik manufaktur.\n"
        "Fokus: COGM, cost per kg, variance material/labor/utility, "
        "efisiensi biaya.\n\n"
        "ATURAN:\n"
        "1. Bahasa Indonesia profesional.\n"
        "2. HANYA pakai angka dari DATA KONTEKS. Sebutkan Rp kalau ada.\n"
        "3. Format:\n"
        "   **Ringkasan Biaya** (1-2 kalimat + COGM)\n"
        "   **Pendorong Biaya** (bullet dengan Rp)\n"
        "   **Peluang Penghematan** (bullet dengan estimasi Rp)\n"
        "4. Maksimal 200 kata.\n"
    )

    def build_context(self, ds, scope, **_) -> Dict[str, Any]:
        return {
            "kpi_summary": call_tool("kpi_summary", ds, scope),
            "cost_variance": call_tool("cost_variance", ds, scope),
            "recommendations": call_tool("recommendations", ds, scope),
        }