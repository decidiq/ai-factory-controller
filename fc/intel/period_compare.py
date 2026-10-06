"""Perbandingan Periode (MoM) — bandingkan KPI antar 2 bulan."""
import calendar
from dataclasses import dataclass
from datetime import date
from typing import Dict, List, Optional

from ..kpi import (KPI, Scope, cogm_for_scope, cost_per_kg, oee_kpi,
                    scrap_kpi, scope_production, yield_kpi)
from ..pipeline import Dataset


def _period_bounds(period_str: str) -> tuple:
    """'2026-08' -> (date(2026,8,1), date(2026,8,31))."""
    y, m = period_str.split("-")
    y, m = int(y), int(m)
    last = calendar.monthrange(y, m)[1]
    return date(y, m, 1), date(y, m, last)


@dataclass
class KPIComparison:
    label: str
    prev_value: Optional[float]
    curr_value: Optional[float]
    fmt: str
    higher_is_better: bool

    @property
    def delta(self) -> Optional[float]:
        if self.prev_value is None or self.curr_value is None:
            return None
        return self.curr_value - self.prev_value

    @property
    def delta_pct(self) -> Optional[float]:
        if self.prev_value in (None, 0) or self.curr_value is None:
            return None
        return (self.curr_value - self.prev_value) / abs(self.prev_value) * 100

    @property
    def is_improving(self) -> Optional[bool]:
        """True jika arah perubahan bagus (naik untuk higher_better, turun untuk lower_better)."""
        if self.delta is None or abs(self.delta) < 1e-9:
            return None
        if self.higher_is_better:
            return self.delta > 0
        return self.delta < 0

    def fmt_value(self, v: Optional[float]) -> str:
        return self.fmt.format(v) if v is not None else "—"

    def fmt_delta(self) -> str:
        if self.delta is None:
            return "—"
        sign = "+" if self.delta >= 0 else "−"
        return f"{sign}{self.fmt.format(abs(self.delta))}"

    def fmt_pct(self) -> str:
        if self.delta_pct is None:
            return ""
        sign = "+" if self.delta_pct >= 0 else "−"
        return f"{sign}{abs(self.delta_pct):.1f}%"


def _kpi_for_period(ds: Dataset, period: str) -> Dict:
    """Hitung KPI untuk periode tertentu (YYYY-MM)."""
    start, end = _period_bounds(period)
    scope = Scope(None, None, start, end)

    prod = scope_production(ds.production, scope)
    output = float(prod["Output_Kg"].sum()) if len(prod) else 0.0

    # Filter costs by Period
    costs = ds.costs
    if (costs is not None and not costs.empty
            and "Period" in costs.columns):
        costs_f = costs[costs["Period"].astype(str) == period]
    else:
        costs_f = costs

    cogm, _ = cogm_for_scope(costs_f, ds.production, scope)
    cpk = cost_per_kg(cogm, output) if output > 0 else KPI(None, "unavailable")

    y = yield_kpi(prod) if len(prod) else KPI(None, "unavailable")
    s = scrap_kpi(prod, y) if len(prod) else KPI(None, "unavailable")
    o = oee_kpi(prod) if len(prod) else None

    return {
        "output": output if len(prod) else None,
        "cogm": cogm.value if cogm.available else None,
        "cost_per_kg": cpk.value if cpk.available else None,
        "yield": y.value if y.available else None,
        "scrap": s.value if s.available else None,
        "oee": o.oee.value if (o and o.oee.available) else None,
    }


def available_periods(ds: Dataset) -> List[str]:
    """Daftar periode unik dari raw_material, urut ascending."""
    if ds.raw_material is None or "Period" not in ds.raw_material.columns:
        return []
    vals = ds.raw_material["Period"].dropna().astype(str).unique()
    return sorted([v for v in vals if v.strip()])


def compare_periods(ds: Dataset, prev: str, curr: str) -> List[KPIComparison]:
    """Bandingkan KPI antara 2 periode."""
    p = _kpi_for_period(ds, prev)
    c = _kpi_for_period(ds, curr)

    return [
        KPIComparison("Output", p["output"], c["output"], "{:,.0f} Kg", True),
        KPIComparison("Yield", p["yield"], c["yield"], "{:.2f}%", True),
        KPIComparison("Scrap", p["scrap"], c["scrap"], "{:.2f}%", False),
        KPIComparison("OEE", p["oee"], c["oee"], "{:.2f}%", True),
        KPIComparison("Cost/Kg", p["cost_per_kg"], c["cost_per_kg"], "Rp {:,.0f}", False),
        KPIComparison("COGM", p["cogm"], c["cogm"], "Rp {:,.0f}", False),
    ]