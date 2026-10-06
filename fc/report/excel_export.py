"""Ekspor ke Excel — Executive Report multi-sheet."""
from datetime import datetime
from io import BytesIO
from typing import Optional

import pandas as pd

from ..intel.alert_impact import compute_alerts
from ..intel.period_compare import available_periods, compare_periods
from ..kpi import Scope, inventory_table, summarize, variance_table
from ..pipeline import Dataset


def generate_excel(ds: Dataset, scope: Scope, targets=None) -> bytes:
    """Buat file Excel multi-sheet. Return bytes.

    Args:
        ds: Dataset
        scope: Scope filter
        targets: Targets KPI — kalau None pakai DEFAULT dari config
    """
    if targets is None:
        from ..config import TARGETS as DEFAULT_TARGETS
        targets = DEFAULT_TARGETS

    s = summarize(ds, scope)
    buf = BytesIO()

    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        # === Sheet 1: Ringkasan ===
        summary_df = pd.DataFrame([
            {"KPI": "Output (Kg)", "Nilai": s.output_kg.value if s.output_kg.available else None},
            {"KPI": "Yield (%)", "Nilai": s.yield_pct.value if s.yield_pct.available else None},
            {"KPI": "Scrap (%)", "Nilai": s.scrap_pct.value if s.scrap_pct.available else None},
            {"KPI": "OEE (%)", "Nilai": s.oee.oee.value if s.oee.oee.available else None},
            {"KPI": "COGM (Rp)", "Nilai": s.cogm.value if s.cogm.available else None},
            {"KPI": "Cost/Kg (Rp)", "Nilai": s.cost_per_kg.value if s.cost_per_kg.available else None},
            {"KPI": "Controller Score", "Nilai": s.score.score},
            {"KPI": "Kategori", "Nilai": s.score.category},
            {"KPI": "Baris Produksi", "Nilai": s.production_rows},
            {"KPI": "Sumber Data", "Nilai": ds.report.source_label},
            {"KPI": "Dibaca", "Nilai": ds.report.loaded_at},
            {"KPI": "Plant", "Nilai": scope.plant or "Semua"},
            {"KPI": "Line", "Nilai": scope.line or "Semua"},
            {"KPI": "Periode", "Nilai": f"{scope.start} s/d {scope.end}" if scope.start else "Semua"},
            {"KPI": "Target Yield (%)", "Nilai": targets.yield_min},
            {"KPI": "Target Scrap (%)", "Nilai": targets.scrap_max},
            {"KPI": "Target OEE (%)", "Nilai": targets.oee_min},
        ])
        summary_df.to_excel(writer, sheet_name="Ringkasan", index=False)

        # === Sheet 2: Peringatan Aktif ===
        alerts = compute_alerts(s, targets)
        if alerts:
            alerts_df = pd.DataFrame([{
                "Prioritas": i,
                "Severity": a.severity,
                "Judul": a.title,
                "Pesan": a.message,
                "Dampak_Bulanan_Rp": a.monthly_rp,
                "Dampak_Tahunan_Rp": a.annual_rp,
                "Saran": a.fix_hint,
            } for i, a in enumerate(alerts, 1)])
            alerts_df.to_excel(writer, sheet_name="Peringatan", index=False)

        # === Sheet 3: Perbandingan Periode ===
        periods = available_periods(ds)
        if len(periods) >= 2:
            prev, curr = periods[-2], periods[-1]
            comps = compare_periods(ds, prev, curr)
            comp_df = pd.DataFrame([{
                "KPI": c.label,
                prev: c.prev_value,
                curr: c.curr_value,
                "Delta": c.delta,
                "Delta_%": c.delta_pct,
                "Status": ("Membaik" if c.is_improving is True
                           else "Memburuk" if c.is_improving is False
                           else "Stabil"),
            } for c in comps])
            comp_df.to_excel(writer, sheet_name="Perbandingan_Periode", index=False)

        # === Sheet 4: Struktur COGM ===
        if s.breakdown:
            total = sum(s.breakdown.values())
            cogm_df = pd.DataFrame([
                {"Komponen": k, "Nilai_Rp": v, "Porsi_%": (v / total * 100 if total else 0)}
                for k, v in sorted(s.breakdown.items(), key=lambda x: -x[1])
            ])
            cogm_df.to_excel(writer, sheet_name="Struktur_COGM", index=False)

        # === Sheet 5: Variance Biaya ===
        if (ds.budget is not None and not ds.budget.empty
                and {"Category", "Budget", "Actual"} <= set(ds.budget.columns)):
            variance_table(ds.budget).to_excel(
                writer, sheet_name="Variance_Biaya", index=False)

        # === Sheet 6: Inventaris ===
        if ds.inventory is not None and not ds.inventory.empty:
            inventory_table(ds.inventory).to_excel(
                writer, sheet_name="Inventaris", index=False)

        # === Sheet 7: Risk Register ===
        if ds.risk is not None and not ds.risk.empty:
            ds.risk.to_excel(writer, sheet_name="Risk_Register", index=False)

        # === Sheet 8: Data Produksi (sample) ===
        if ds.production is not None and not ds.production.empty:
            ds.production.head(1000).to_excel(
                writer, sheet_name="Produksi_1000", index=False)

    buf.seek(0)
    return buf.read()