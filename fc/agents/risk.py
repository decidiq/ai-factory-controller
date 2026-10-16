"""RiskAgent — risk register + mitigasi risiko operasional."""
from typing import Any, Dict

from .base import BaseAgent
from .tools import call_tool


class RiskAgent(BaseAgent):
    name = "risk"
    role = "Risk Manager"
    description = "Analisis risk register, prioritas risiko, mitigasi"
    tools_allowed = ("risk_register", "recommendations", "stockout_risk", "kpi_summary")

    system_prompt = (
        "Anda adalah **Risk Manager** di pabrik manufaktur.\n"
        "Fokus: risk register, mitigasi, prioritas risiko, dampak potensial.\n\n"
        "ATURAN:\n"
        "1. Bahasa Indonesia profesional.\n"
        "2. HANYA pakai angka dari DATA KONTEKS.\n"
        "3. Format:\n"
        "   **Top Risk** (3 bullet dengan skor P×I)\n"
        "   **Dampak Bila Terjadi** (bullet, kualitatif bila tidak ada data Rp)\n"
        "   **Mitigasi Prioritas** (bullet, actionable)\n"
        "4. Maksimal 200 kata.\n"
    )

    def build_context(self, ds, scope, **_) -> Dict[str, Any]:
        return {
            "risk_register": call_tool("risk_register", ds, scope),
            "stockout_risk": call_tool("stockout_risk", ds, scope),
            "recommendations": call_tool("recommendations", ds, scope),
            "kpi_summary": call_tool("kpi_summary", ds, scope),
        }