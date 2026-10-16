"""QualityAgent — scrap, yield, pola defect, root cause."""
from typing import Any, Dict

from .base import BaseAgent
from .tools import call_tool


class QualityAgent(BaseAgent):
    name = "quality"
    role = "Quality Analyst"
    description = "Analisis scrap, yield, pola defect, hipotesis root cause"
    tools_allowed = ("quality_signals", "detect_anomalies", "kpi_summary")

    system_prompt = (
        "Anda adalah **Quality Analyst** di pabrik manufaktur.\n"
        "Fokus: yield, scrap, defect pattern, root cause, konsistensi kualitas.\n\n"
        "ATURAN:\n"
        "1. Bahasa Indonesia profesional.\n"
        "2. HANYA pakai angka dari DATA KONTEKS.\n"
        "3. Format:\n"
        "   **Kualitas Saat Ini** (1-2 kalimat)\n"
        "   **Produk Bermasalah** (bullet dengan scrap Kg)\n"
        "   **Hipotesis Root Cause** (bullet, tidak mengarang data)\n"
        "   **Rekomendasi** (bullet actionable)\n"
        "4. Maksimal 200 kata.\n"
    )

    def build_context(self, ds, scope, **_) -> Dict[str, Any]:
        return {
            "quality_signals": call_tool("quality_signals", ds, scope),
            "detect_anomalies": call_tool("detect_anomalies", ds, scope),
            "kpi_summary": call_tool("kpi_summary", ds, scope),
        }