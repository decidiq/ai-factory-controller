"""InventoryAgent — risiko stock-out & slow moving."""
from typing import Any, Dict

from .base import BaseAgent
from .tools import call_tool


class InventoryAgent(BaseAgent):
    name = "inventory"
    role = "Inventory Analyst"
    description = "Analisis stok, prediksi stock-out, deteksi slow moving"
    tools_allowed = ("stockout_risk", "kpi_summary")

    system_prompt = (
        "Anda adalah **Inventory Analyst** di pabrik manufaktur.\n"
        "Fokus: stok material, risiko stock-out, dead stock, working capital.\n\n"
        "ATURAN:\n"
        "1. Bahasa Indonesia profesional.\n"
        "2. HANYA pakai angka dari DATA KONTEKS.\n"
        "3. Format:\n"
        "   **Status** (1-2 kalimat)\n"
        "   **Material Kritis** (bullet dengan hari tersisa)\n"
        "   **Aksi** (reorder / audit / dispose)\n"
        "4. Maksimal 180 kata.\n"
    )

    def build_context(self, ds, scope, **_) -> Dict[str, Any]:
        return {
            "stockout_risk": call_tool("stockout_risk", ds, scope),
            "kpi_summary": call_tool("kpi_summary", ds, scope),
        }