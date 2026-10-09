"""Generate dummy data untuk testing Decidiq — 2 Plant."""
import random
from datetime import date, timedelta

import pandas as pd

random.seed(42)

# ==================== CONFIG ====================
PLANTS = ["Plant A (Cikarang)", "Plant B (Karawang)"]
LINES = ["Line 1", "Line 2", "Line 3", "Line 4"]
MACHINES_PER_LINE = 2

PRODUCTS = [
    "Product A", "Product B", "Product C", "Product D",
    "Product E", "Product F", "Product G", "Product H",
    "Product I", "Product J", "Product K", "Product L",
]

MATERIALS = [
    ("Resin PP",      15000, 0.65),
    ("Resin PE",      14000, 0.62),
    ("Resin ABS",     18000, 0.68),
    ("Resin PVC",     16000, 0.60),
    ("Pigment Red",   25000, 0.05),
    ("Pigment Blue",  27000, 0.04),
    ("Pigment Yellow",24000, 0.04),
    ("Additive A",    30000, 0.02),
    ("Additive B",    32000, 0.02),
    ("Additive C",    28000, 0.015),
    ("Regrind",        5000, 0.01),
    ("Solvent",       22000, 0.01),
    ("Lubricant",     35000, 0.005),
    ("Stabilizer",    40000, 0.005),
    ("Filler",         8000, 0.03),
]

BUDGET_CATEGORIES = [
    ("Material",    2890000000, 0.05),
    ("Labor",        556000000, 0.02),
    ("Utility",      435000000, 0.06),
    ("Maintenance",  234000000, 0.08),
    ("Packaging",    380000000, 0.04),
    ("Depreciation", 280000000, 0.01),
]

RISKS = [
    ("Kenaikan harga material", "Open", 3, 3),
    ("Mesin rusak", "Mitigation", 2, 3),
    ("Scrap tinggi", "Open", 3, 2),
    ("Keterlambatan pemasok", "Open", 2, 3),
    ("Lonjakan biaya utilitas", "Controlled", 2, 2),
    ("Kehilangan tenaga kerja ahli", "Mitigation", 2, 3),
    ("Kegagalan sistem IT", "Open", 2, 3),
    ("Kontaminasi produk", "Controlled", 1, 3),
    ("Fluktuasi kurs", "Open", 3, 2),
    ("Bencana alam", "Mitigation", 1, 3),
]

CONFIG = [
    ("Target_Yield", 98),
    ("Target_Scrap", 2),
    ("Target_OEE", 85),
    ("Max_Cost_per_Kg", 12500),
    ("Utility_Share_Max", 15),
    ("Slow_Moving_Days", 45),
    ("Variance_Tolerance_Pct", 5),
]

START_DATE = date(2026, 1, 1)
END_DATE = date(2026, 10, 8)


def generate_production():
    print("📊 Generating Production...")
    rows = []
    current = START_DATE

    machine_products = {}
    for plant in PLANTS:
        for line in LINES:
            for m_idx in range(MACHINES_PER_LINE):
                machine = f"M-{(LINES.index(line) * MACHINES_PER_LINE) + m_idx + 1:02d}"
                key = (plant, line, machine)
                machine_products[key] = random.choice(PRODUCTS)

    plant_factor = {PLANTS[0]: 1.02, PLANTS[1]: 0.98}

    while current <= END_DATE:
        day_of_year = current.timetuple().tm_yday
        seasonal = 1.0 + 0.08 * (day_of_year / 365)

        for plant in PLANTS:
            for line in LINES:
                for m_idx in range(MACHINES_PER_LINE):
                    machine = f"M-{(LINES.index(line) * MACHINES_PER_LINE) + m_idx + 1:02d}"
                    product = machine_products[(plant, line, machine)]

                    planned = 480
                    if random.random() < 0.05:
                        downtime = random.randint(60, 120)
                    else:
                        downtime = random.randint(10, 50)

                    ideal_rate = round(random.uniform(2.3, 2.9), 2)
                    base_output = random.uniform(950, 1150) * plant_factor[plant] * seasonal

                    if random.random() < 0.04:
                        yield_pct = random.uniform(0.92, 0.95)
                    else:
                        yield_pct = random.uniform(0.96, 0.985)

                    output = base_output * (1 - downtime / planned * 0.3)
                    input_kg = output / yield_pct
                    scrap_kg = input_kg - output

                    rows.append({
                        "Date": current.strftime("%Y-%m-%d"),
                        "Plant": plant,
                        "Line": line,
                        "Machine": machine,
                        "Product": product,
                        "Input_Kg": round(input_kg, 1),
                        "Output_Kg": round(output, 1),
                        "Scrap_Kg": round(scrap_kg, 1),
                        "Planned_Time_Min": planned,
                        "Downtime_Min": downtime,
                        "Ideal_Rate_Kg_per_Min": ideal_rate,
                    })
        current += timedelta(days=1)

    df = pd.DataFrame(rows)
    print(f"   ✅ {len(df):,} baris production")
    return df


def generate_raw_material():
    print("📊 Generating Raw_Material...")
    rows = []

    periods = []
    current = START_DATE.replace(day=1)
    while current <= END_DATE:
        periods.append(current.strftime("%Y-%m"))
        if current.month == 12:
            current = current.replace(year=current.year + 1, month=1)
        else:
            current = current.replace(month=current.month + 1)

    for period in periods:
        month_idx = periods.index(period)
        seasonal = 1.0 + 0.08 * (month_idx / len(periods))

        for plant in PLANTS:
            plant_factor = 1.02 if "A" in plant else 0.98

            for material, base_price, share in MATERIALS:
                total_volume = 200000 * seasonal * plant_factor
                qty = total_volume * share * random.uniform(0.9, 1.1)

                price_variation = random.uniform(0.9, 1.1)
                cost = qty * base_price * price_variation

                rows.append({
                    "Material": material,
                    "Cost": round(cost, 0),
                    "Qty_Kg": round(qty, 0),
                    "Plant": plant,
                    "Period": period,
                })

    df = pd.DataFrame(rows)
    print(f"   ✅ {len(df):,} baris raw_material")
    return df


def _generate_period_sheet(sheet_name, base_per_plant_month):
    print(f"📊 Generating {sheet_name}...")
    rows = []

    periods = []
    current = START_DATE.replace(day=1)
    while current <= END_DATE:
        periods.append(current.strftime("%Y-%m"))
        if current.month == 12:
            current = current.replace(year=current.year + 1, month=1)
        else:
            current = current.replace(month=current.month + 1)

    for period in periods:
        month_idx = periods.index(period)
        seasonal = 1.0 + 0.05 * (month_idx / len(periods))

        for plant in PLANTS:
            plant_factor = 1.02 if "A" in plant else 0.98
            cost = base_per_plant_month * seasonal * plant_factor
            cost *= random.uniform(0.95, 1.05)

            rows.append({
                "Cost": round(cost, 0),
                "Plant": plant,
                "Period": period,
            })

    return pd.DataFrame(rows)


def generate_packaging():
    return _generate_period_sheet("Packaging", 115000000)


def generate_direct_labor():
    return _generate_period_sheet("Direct_Labor", 172000000)


def generate_utility():
    df = _generate_period_sheet("Utility", 129000000)
    df = df.rename(columns={"Cost": "Electricity_Cost"})
    return df[["Electricity_Cost", "Plant", "Period"]]


def generate_maintenance():
    return _generate_period_sheet("Maintenance", 72000000)


def generate_depreciation():
    df = _generate_period_sheet("Depreciation", 86000000)
    df = df.rename(columns={"Cost": "Monthly_Dep"})
    return df[["Monthly_Dep", "Plant", "Period"]]


def generate_budget():
    print("📊 Generating Budget...")
    rows = []
    for category, budget, tol in BUDGET_CATEGORIES:
        actual = budget * (1 + random.uniform(-tol, tol))
        rows.append({
            "Category": category,
            "Budget": round(budget, 0),
            "Actual": round(actual, 0),
        })
    return pd.DataFrame(rows)


def generate_inventory():
    print("📊 Generating Inventory...")
    rows = []
    for material, _, share in MATERIALS:
        usage = 200000 * share * random.uniform(0.8, 1.2)
        stock = usage * random.uniform(0.5, 2.5)

        if material == "Regrind":
            stock = random.uniform(2000, 5000)
            usage = 0
        elif material == "Filler":
            stock = random.uniform(15000, 25000)
            usage = random.uniform(3000, 6000)

        rows.append({
            "Material": material,
            "Stock_Kg": round(stock, 0),
            "Monthly_Usage": round(usage, 0),
        })
    return pd.DataFrame(rows)


def generate_risk_register():
    print("📊 Generating Risk_Register...")
    rows = []
    for risk, status, prob, impact in RISKS:
        rows.append({
            "Risk": risk,
            "Status": status,
            "Probability_Val": prob,
            "Impact_Val": impact,
        })
    return pd.DataFrame(rows)


def generate_config():
    print("📊 Generating Config...")
    return pd.DataFrame({
        "Parameter": [c[0] for c in CONFIG],
        "Value": [c[1] for c in CONFIG],
    })


def main():
    print("\n🚀 Starting data generation (2 Plants)...\n")

    production = generate_production()
    raw_material = generate_raw_material()
    packaging = generate_packaging()
    direct_labor = generate_direct_labor()
    utility = generate_utility()
    maintenance = generate_maintenance()
    depreciation = generate_depreciation()
    budget = generate_budget()
    inventory = generate_inventory()
    risk_register = generate_risk_register()
    config = generate_config()

    output_file = "sample/decidiq_test_data.xlsx"
    print(f"\n📝 Writing to {output_file}...")

    with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
        production.to_excel(writer, sheet_name="Production", index=False)
        raw_material.to_excel(writer, sheet_name="Raw_Material", index=False)
        packaging.to_excel(writer, sheet_name="Packaging", index=False)
        direct_labor.to_excel(writer, sheet_name="Direct_Labor", index=False)
        utility.to_excel(writer, sheet_name="Utility", index=False)
        maintenance.to_excel(writer, sheet_name="Maintenance", index=False)
        depreciation.to_excel(writer, sheet_name="Depreciation", index=False)
        budget.to_excel(writer, sheet_name="Budget", index=False)
        inventory.to_excel(writer, sheet_name="Inventory", index=False)
        risk_register.to_excel(writer, sheet_name="Risk_Register", index=False)
        config.to_excel(writer, sheet_name="Config", index=False)

    print(f"\n✅ File generated: {output_file}")
    print(f"\n📊 Summary:")
    print(f"   Production:     {len(production):>6,} baris")
    print(f"   Raw_Material:   {len(raw_material):>6,} baris")
    print(f"   Packaging:      {len(packaging):>6,} baris")
    print(f"   Direct_Labor:   {len(direct_labor):>6,} baris")
    print(f"   Utility:        {len(utility):>6,} baris")
    print(f"   Maintenance:    {len(maintenance):>6,} baris")
    print(f"   Depreciation:   {len(depreciation):>6,} baris")
    print(f"   Budget:         {len(budget):>6,} baris")
    print(f"   Inventory:      {len(inventory):>6,} baris")
    print(f"   Risk_Register:  {len(risk_register):>6,} baris")
    print(f"   Config:         {len(config):>6,} baris")


if __name__ == "__main__":
    main()