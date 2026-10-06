"""Data contoh untuk MODE DEMO (BRD 5.5: data contoh hanya boleh muncul pada mode demo
yang ditandai jelas). Tidak pernah dipakai otomatis sebagai pengganti data asli."""
from datetime import date, timedelta
from typing import Dict, Optional

import numpy as np
import pandas as pd

PLANTS = {
    "Plant A (Cikarang)": {"Line 1": ["M-01", "M-02"], "Line 2": ["M-03", "M-04"]},
    "Plant B (Karawang)": {"Line 3": ["M-05", "M-06"]},
}
_MATERIALS = [("Resin PP", .35), ("Resin PE", .25), ("Pigment", .15), ("Additive", .12), ("Regrind", .08), ("Solvent", .05)]


def make_demo_frames(days: int = 60, today: Optional[date] = None, seed: int = 7) -> Dict[str, pd.DataFrame]:
    rng = np.random.default_rng(seed)
    end = (today or date.today()) - timedelta(days=1)
    dates = pd.date_range(end=pd.Timestamp(end), periods=days, freq="D")

    machine_rate = {m: round(float(rng.uniform(2.4, 2.8)), 2)
                    for lines in PLANTS.values() for ms in lines.values() for m in ms}
    rows = []
    for d in dates:
        for plant, lines in PLANTS.items():
            for line, machines in lines.items():
                for m in machines:
                    planned = 480
                    down = int(rng.integers(20, 51))
                    ideal = machine_rate[m]
                    total = (planned - down) * ideal * float(rng.uniform(0.90, 0.97))
                    scrap = total * float(rng.uniform(0.015, 0.03))
                    rows.append({
                        "Date": d, "Plant": plant, "Line": line, "Machine": m,
                        "Output_Kg": round(total - scrap, 1),
                        "Input_Kg": round(total + float(rng.uniform(0, 6)), 1),
                        "Scrap_Kg": round(scrap, 1),
                        "Planned_Time_Min": planned, "Downtime_Min": down,
                        "Ideal_Rate_Kg_per_Min": ideal,
                    })
    production = pd.DataFrame(rows)

    production["Period"] = production["Date"].dt.strftime("%Y-%m")
    monthly = production.groupby(["Plant", "Period"])["Output_Kg"].sum().reset_index()

    raw, pack, labor, util, maint, dep = [], [], [], [], [], []
    for _, r in monthly.iterrows():
        total = r["Output_Kg"] * 12_000 * float(rng.uniform(0.95, 1.05))
        dim = {"Plant": r["Plant"], "Period": r["Period"]}
        for name, w in _MATERIALS:
            cost = total * 0.60 * w
            raw.append({"Material": name, "Cost": round(cost), "Qty_Kg": round(cost / 15_000), **dim})
        pack.append({"Cost": round(total * 0.08), **dim})
        labor.append({"Cost": round(total * 0.12), **dim})
        util.append({"Electricity_Cost": round(total * 0.09), **dim})
        maint.append({"Cost": round(total * 0.05), **dim})
        dep.append({"Monthly_Dep": round(total * 0.06), **dim})
    production = production.drop(columns="Period")

    cost_total = {
        "Material": sum(x["Cost"] for x in raw), "Labor": sum(x["Cost"] for x in labor),
        "Utility": sum(x["Electricity_Cost"] for x in util), "Maintenance": sum(x["Cost"] for x in maint),
    }
    budget = pd.DataFrame([{"Category": k, "Budget": round(v * float(rng.uniform(0.95, 1.08))), "Actual": v}
                           for k, v in cost_total.items()])
    inventory = pd.DataFrame({
        "Material": ["Resin PP", "Resin PE", "Pigment", "Additive", "Regrind", "Solvent"],
        "Stock_Kg": [42_000, 18_000, 9_000, 6_500, 3_000, 1_200],
        "Monthly_Usage": [30_000, 22_000, 4_000, 5_800, 0, 900],
    })
    risk = pd.DataFrame({
        "Risk": ["Kenaikan harga material", "Mesin rusak", "Scrap tinggi", "Lonjakan biaya utilitas", "Keterlambatan pemasok"],
        "Status": ["Open", "Mitigation", "Open", "Controlled", "Open"],
        "Probability_Val": [3, 2, 3, 2, 2], "Impact_Val": [3, 3, 2, 2, 3],
    })
    return {
        "Raw_Material": pd.DataFrame(raw), "Packaging": pd.DataFrame(pack), "Direct_Labor": pd.DataFrame(labor),
        "Utility": pd.DataFrame(util), "Maintenance": pd.DataFrame(maint), "Depreciation": pd.DataFrame(dep),
        "Production": production, "Budget": budget, "Inventory": inventory, "Risk_Register": risk,
    }


def write_demo_excel(path: str, **kw) -> str:
    with pd.ExcelWriter(path) as xw:
        for name, df in make_demo_frames(**kw).items():
            df.to_excel(xw, sheet_name=name, index=False)
    return path
