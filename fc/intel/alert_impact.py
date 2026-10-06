"""Alert Impact Engine — hitung estimasi dampak Rp dari setiap alert.

Setiap alert KPI (Yield, Scrap, OEE, Cost/Kg, Utility) dikonversi
menjadi estimasi kerugian bulanan & tahunan, sehingga manajemen
tahu prioritas berdasarkan DUIT, bukan feeling.
"""
from dataclasses import dataclass
from typing import List

from ..config import Targets


@dataclass
class AlertImpact:
    severity: str       # "high" | "medium" | "info"
    title: str
    message: str
    monthly_rp: float
    annual_rp: float
    fix_hint: str = ""


def _avg_material_price(summary) -> float:
    """Rata-rata harga material Rp/Kg dari data."""
    mat_cost = summary.breakdown.get("Material", 0)
    if summary.yield_pct.available and summary.yield_pct.value > 0:
        input_kg = summary.output_kg.value / (summary.yield_pct.value / 100)
    else:
        input_kg = summary.output_kg.value
    return mat_cost / input_kg if input_kg > 0 else 0


def compute_alerts(summary, targets: Targets) -> List[AlertImpact]:
    """Hitung semua alert dengan dampak finansial."""
    alerts: List[AlertImpact] = []

    if not summary.production_rows:
        return alerts

    output = summary.output_kg.value if summary.output_kg.available else 0
    cogm = summary.cogm.value if summary.cogm.available else 0
    cpk = summary.cost_per_kg.value if summary.cost_per_kg.available else 0
    avg_mat_price = _avg_material_price(summary)

    # 1. YIELD
    y = summary.yield_pct
    if y.available and y.value < targets.yield_min and y.value > 0:
        gap_pp = targets.yield_min - y.value
        input_current = output / (y.value / 100)
        input_target = output / (targets.yield_min / 100)
        input_saved = input_current - input_target
        monthly = input_saved * avg_mat_price
        alerts.append(AlertImpact(
            severity="high",
            title=f"Yield {y.value:.2f}% di bawah target {targets.yield_min:g}%",
            message=f"Gap {gap_pp:.2f} poin persentase",
            monthly_rp=monthly,
            annual_rp=monthly * 12,
            fix_hint="Tingkatkan kualitas input & cek kalibrasi mesin",
        ))

    # 2. SCRAP
    s = summary.scrap_pct
    if s.available and s.value > targets.scrap_max:
        excess_pp = s.value - targets.scrap_max
        input_current = (output / (y.value / 100)
                         if y.available and y.value > 0 else output)
        scrap_excess_kg = input_current * (excess_pp / 100)
        monthly = scrap_excess_kg * avg_mat_price
        alerts.append(AlertImpact(
            severity="high",
            title=f"Scrap {s.value:.2f}% melewati batas {targets.scrap_max:g}%",
            message=f"Kelebihan {excess_pp:.2f} poin persentase",
            monthly_rp=monthly,
            annual_rp=monthly * 12,
            fix_hint="Audit mesin kritis, ganti nozzle rutin",
        ))

    # 3. OEE
    o = summary.oee.oee
    if o.available and o.value < targets.oee_min:
        gap_pct = (targets.oee_min - o.value) / 100
        fixed_share = 0.4  # porsi fixed cost terhadap COGM (depreciation + maintenance + sebagian labor)
        monthly = cogm * fixed_share * gap_pct
        alerts.append(AlertImpact(
            severity="medium",
            title=f"OEE {o.value:.2f}% di bawah target {targets.oee_min:g}%",
            message=f"Gap {(targets.oee_min - o.value):.2f} poin persentase",
            monthly_rp=monthly,
            annual_rp=monthly * 12,
            fix_hint="Kurangi downtime, percepat preventive maintenance",
        ))

    # 4. COST/KG OVER MAX
    if cpk > 0 and targets.max_cost_per_kg > 0 and cpk > targets.max_cost_per_kg:
        overage_per_kg = cpk - targets.max_cost_per_kg
        monthly = overage_per_kg * output
        alerts.append(AlertImpact(
            severity="high",
            title=f"Cost/Kg Rp {cpk:,.0f} > batas Rp {targets.max_cost_per_kg:,.0f}",
            message=f"Overage Rp {overage_per_kg:,.0f}/Kg",
            monthly_rp=monthly,
            annual_rp=monthly * 12,
            fix_hint="Review supplier, negosiasi harga material",
        ))

    # 5. UTILITY SHARE
    if cogm > 0:
        util = summary.breakdown.get("Utility", 0)
        share_pct = util / cogm * 100
        if share_pct > targets.utility_share_max:
            excess_pct = share_pct - targets.utility_share_max
            monthly = cogm * (excess_pct / 100)
            alerts.append(AlertImpact(
                severity="info",
                title=f"Biaya utilitas {share_pct:.1f}% dari COGM",
                message=f"Melewati batas {targets.utility_share_max:g}%",
                monthly_rp=monthly,
                annual_rp=monthly * 12,
                fix_hint="Optimasi beban listrik, cek kebocoran",
            ))

    # Sort: yang dampaknya paling besar di atas
    alerts.sort(key=lambda a: abs(a.annual_rp), reverse=True)
    return alerts