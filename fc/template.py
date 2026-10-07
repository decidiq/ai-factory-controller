"""Generator template Excel untuk customer Decidiq."""
from io import BytesIO

import pandas as pd


def generate_template() -> bytes:
    """Generate template Excel dengan semua sheet yang dibutuhkan.

    Return: bytes siap di-download.
    """
    buf = BytesIO()

    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        # === 1. Production ===
        prod = pd.DataFrame({
            "Date": ["2026-01-01", "2026-01-01", "2026-01-02"],
            "Plant": ["Plant A", "Plant A", "Plant B"],
            "Line": ["Line 1", "Line 2", "Line 3"],
            "Machine": ["M-01", "M-03", "M-05"],
            "Product": ["Product X", "Product Y", "Product X"],
            "Input_Kg": [1000.0, 1100.0, 1050.0],
            "Output_Kg": [975.0, 1075.0, 1025.0],
            "Scrap_Kg": [25.0, 25.0, 25.0],
            "Planned_Time_Min": [480, 480, 480],
            "Downtime_Min": [30, 40, 25],
            "Ideal_Rate_Kg_per_Min": [2.5, 2.6, 2.55],
        })
        prod.to_excel(writer, sheet_name="Production", index=False)

        # === 2. Raw_Material ===
        rm = pd.DataFrame({
            "Material": ["Resin PP", "Resin PE", "Pigment"],
            "Cost": [300_000_000, 200_000_000, 100_000_000],
            "Qty_Kg": [20_000, 14_000, 8_500],
            "Plant": ["Plant A", "Plant A", "Plant A"],
            "Period": ["2026-01", "2026-01", "2026-01"],
        })
        rm.to_excel(writer, sheet_name="Raw_Material", index=False)

        # === 3. Packaging ===
        pk = pd.DataFrame({
            "Cost": [115_000_000],
            "Plant": ["Plant A"],
            "Period": ["2026-01"],
        })
        pk.to_excel(writer, sheet_name="Packaging", index=False)

        # === 4. Direct_Labor ===
        dl = pd.DataFrame({
            "Cost": [172_000_000],
            "Plant": ["Plant A"],
            "Period": ["2026-01"],
        })
        dl.to_excel(writer, sheet_name="Direct_Labor", index=False)

        # === 5. Utility ===
        ut = pd.DataFrame({
            "Electricity_Cost": [129_000_000],
            "Plant": ["Plant A"],
            "Period": ["2026-01"],
        })
        ut.to_excel(writer, sheet_name="Utility", index=False)

        # === 6. Maintenance ===
        mt = pd.DataFrame({
            "Cost": [72_000_000],
            "Plant": ["Plant A"],
            "Period": ["2026-01"],
        })
        mt.to_excel(writer, sheet_name="Maintenance", index=False)

        # === 7. Depreciation ===
        dp = pd.DataFrame({
            "Monthly_Dep": [86_000_000],
            "Plant": ["Plant A"],
            "Period": ["2026-01"],
        })
        dp.to_excel(writer, sheet_name="Depreciation", index=False)

        # === 8. Budget ===
        bd = pd.DataFrame({
            "Category": ["Material", "Labor", "Utility", "Maintenance"],
            "Budget": [2_889_000_000, 556_000_000, 435_000_000, 234_000_000],
            "Actual": [2_780_000_000, 556_000_000, 417_000_000, 232_000_000],
        })
        bd.to_excel(writer, sheet_name="Budget", index=False)

        # === 9. Inventory ===
        inv = pd.DataFrame({
            "Material": ["Resin PP", "Resin PE", "Pigment", "Additive", "Regrind", "Solvent"],
            "Stock_Kg": [42_000, 18_000, 9_000, 6_500, 3_000, 1_200],
            "Monthly_Usage": [30_000, 22_000, 4_000, 5_800, 0, 900],
        })
        inv.to_excel(writer, sheet_name="Inventory", index=False)

        # === 10. Risk_Register ===
        rk = pd.DataFrame({
            "Risk": [
                "Kenaikan harga material",
                "Mesin rusak",
                "Scrap tinggi",
                "Keterlambatan pemasok",
            ],
            "Status": ["Open", "Mitigation", "Open", "Open"],
            "Probability_Val": [3, 2, 3, 2],
            "Impact_Val": [3, 3, 2, 3],
        })
        rk.to_excel(writer, sheet_name="Risk_Register", index=False)

        # === 11. Config (opsional) ===
        cfg = pd.DataFrame({
            "Parameter": ["Target_Yield", "Target_Scrap", "Target_OEE",
                          "Max_Cost_per_Kg", "Utility_Share_Max"],
            "Value": [98.0, 2.0, 85.0, 12_500.0, 15.0],
        })
        cfg.to_excel(writer, sheet_name="Config", index=False)

    buf.seek(0)
    return buf.read()