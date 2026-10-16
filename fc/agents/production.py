"""ProductionAgent — KPI produksi, forecast, anomali."""
from typing import Any, Dict

from .base import BaseAgent
from .tools import call_tool


class ProductionAgent(BaseAgent):
    name = "production"
    role = "Production Planner"
    description = "Analisis KPI produksi, forecast output, deteksi anomali"
    tools_allowed = ("kpi_summary", "forecast_output", "detect_anomalies")

    system_prompt = (
        "Anda adalah **Production Planner** di pabrik manufaktur.\n"
        "Fokus: yield, scrap, OEE, throughput, forecast, anomali.\n\n"
        "ATURAN:\n"
        "1. Bahasa Indonesia profesional, ringkas.\n"
        "2. HANYA pakai angka dari DATA KONTEKS — jangan mengarang.\n"
        "3. Format output:\n"
        "   **Ringkasan** (1-2 kalimat)\n"
        "   **Temuan Kunci** (3-5 bullet)\n"
        "   **Rekomendasi** (2-3 bullet, prioritas aksi)\n"
        "4. Maksimal 200 kata.\n"
    )

    def build_context(self, ds, scope, periods: int = 7, **_) -> Dict[str, Any]:
        return {
            "kpi_summary": call_tool("kpi_summary", ds, scope),
            "forecast_output": call_tool("forecast_output", ds, scope, periods=periods),
            "detect_anomalies": call_tool("detect_anomalies", ds, scope),
        }