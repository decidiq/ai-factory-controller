"""MaintenanceAgent — downtime, prediksi masalah mesin, preventive."""
from typing import Any, Dict

from .base import BaseAgent
from .tools import call_tool


class MaintenanceAgent(BaseAgent):
    name = "maintenance"
    role = "Maintenance Planner"
    description = "Analisis downtime, prediksi masalah mesin, jadwal preventive"
    tools_allowed = ("maintenance_signals", "detect_anomalies", "kpi_summary")

    system_prompt = (
        "Anda adalah **Maintenance Planner** di pabrik manufaktur.\n"
        "Fokus: downtime, OEE availability, prediksi kerusakan mesin, "
        "jadwal preventive maintenance.\n\n"
        "ATURAN:\n"
        "1. Bahasa Indonesia profesional.\n"
        "2. HANYA pakai angka dari DATA KONTEKS.\n"
        "3. Format:\n"
        "   **Status Mesin** (1-2 kalimat)\n"
        "   **Mesin Kritis** (bullet dengan downtime menit)\n"
        "   **Rekomendasi Tindakan** (bullet, spesifik mesin)\n"
        "4. Maksimal 180 kata.\n"
    )

    def build_context(self, ds, scope, **_) -> Dict[str, Any]:
        return {
            "maintenance_signals": call_tool("maintenance_signals", ds, scope),
            "detect_anomalies": call_tool("detect_anomalies", ds, scope),
            "kpi_summary": call_tool("kpi_summary", ds, scope),
        }