"""What-If Simulator — simulasi skenario berdasarkan parameter user."""
from dataclasses import dataclass


@dataclass
class Scenario:
    yield_pct: float
    scrap_pct: float
    resin_price_pct: float
    volume_pct: float


@dataclass
class SimulationResult:
    output_kg: float
    cogm: float
    cost_per_kg: float
    savings_annual: float
    baseline_cost_per_kg: float
    baseline_cogm: float


def simulate(baseline_output_kg, baseline_cogm, material_cost_share, scenario):
    """Simulasi cepat berdasarkan baseline pabrik."""
    if baseline_output_kg <= 0 or baseline_cogm <= 0:
        return SimulationResult(0, 0, 0, 0, 0, baseline_cogm)

    new_output = baseline_output_kg * (1 + scenario.volume_pct / 100.0)

    new_cogm = baseline_cogm * (1 + (scenario.resin_price_pct / 100.0) * material_cost_share)

    variable_share = material_cost_share
    fixed_share = 1 - variable_share
    if new_output > 0:
        new_cogm = new_cogm * (variable_share * (new_output / baseline_output_kg) + fixed_share)

    yield_base = 97.5
    yield_factor = scenario.yield_pct / yield_base if yield_base else 1.0
    if yield_factor > 0:
        new_cogm = new_cogm / yield_factor

    baseline_cpk = baseline_cogm / baseline_output_kg if baseline_output_kg > 0 else 0
    new_cpk = new_cogm / new_output if new_output > 0 else 0

    monthly_savings = (baseline_cpk - new_cpk) * new_output
    annual_savings = monthly_savings * 12

    return SimulationResult(
        output_kg=new_output,
        cogm=new_cogm,
        cost_per_kg=new_cpk,
        savings_annual=annual_savings,
        baseline_cost_per_kg=baseline_cpk,
        baseline_cogm=baseline_cogm,
    )