"""Generator template Excel untuk customer Decidiq."""
from io import BytesIO

import pandas as pd


def generate_template() -> bytes:
    """Generate template Excel dengan semua sheet yang dibutuhkan."""
    buf = BytesIO()

    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        # === 1. Production ===
        prod = pd.DataFrame({
            "Date": [
                "2026-01-01", "2026-01-01", "2026-01-01",
                "2026-01-01", "2026-01-01", "2026-01-01",
            ],
            "Plant": [
                "Plant A", "Plant A", "Plant A",
                "Plant B", "Plant B", "Plant B",
            ],
            "Line": ["Line 1", "Line 2", "Line 3", "Line 1", "Line 2", "Line 3"],
            "Machine": ["M-01", "M-03", "M-05", "M-02", "M-04", "M-06"],
            "Product": [
                "Resin Pipe 20mm", "Resin Pipe 25mm", "Resin Pipe 32mm",
                "Resin Pipe 20mm", "Resin Pipe 25mm", "Resin Pipe 32mm",
            ],
            "Input_Kg": [1000.0, 1100.0, 1050.0, 980.0, 1020.0, 1150.0],
            "Output_Kg": [975.0, 1075.0, 1025.0, 955.0, 995.0, 1120.0],
            "Scrap_Kg": [25.0, 25.0, 25.0, 25.0, 25.0, 30.0],
            "Planned_Time_Min": [480, 480, 480, 480, 480, 480],
            "Downtime_Min": [30, 40, 25, 35, 28, 42],
            "Ideal_Rate_Kg_per_Min": [2.5, 2.6, 2.55, 2.45, 2.5, 2.6],
        })
        prod.to_excel(writer, sheet_name="Production", index=False)

        # === 2. Raw_Material ===
        rm = pd.DataFrame({
            "Date": [
                "2026-01-01", "2026-01-01", "2026-01-01",
                "2026-01-01", "2026-01-01", "2026-01-01",
            ],
            "Plant": [
                "Plant A", "Plant A", "Plant A",
                "Plant B", "Plant B", "Plant B",
            ],
            "Material": [
                "Resin PP", "Resin PE", "Pigment",
                "Resin PP", "Resin PE", "Pigment",
            ],
            "Quantity_Kg": [
                20000.0, 14000.0, 8500.0,
                18000.0, 13000.0, 8000.0,
            ],
            "Unit_Cost_Rp": [
                15000.0, 14285.7, 11764.7,
                15500.0, 14500.0, 12000.0,
            ],
            "Total_Cost_Rp": [
                300_000_000, 200_000_000, 100_000_000,
                279_000_000, 188_500_000, 96_000_000,
            ],
        })
        rm.to_excel(writer, sheet_name="Raw_Material", index=False)

        # === 3. Packaging ===
        pk = pd.DataFrame({
            "Date": ["2026-01-01", "2026-01-01"],
            "Plant": ["Plant A", "Plant B"],
            "Material": ["Carton Box", "Carton Box"],
            "Quantity": [32300.0, 30500.0],
            "Unit_Cost_Rp": [3560.0, 3600.0],
            "Total_Cost_Rp": [115_000_000, 109_800_000],
        })
        pk.to_excel(writer, sheet_name="Packaging", index=False)

        # === 4. Direct_Labor ===
        dl = pd.DataFrame({
            "Date": ["2026-01-01", "2026-01-01"],
            "Plant": ["Plant A", "Plant B"],
            "Employee_Group": ["Operator", "Operator"],
            "Hours": [5000.0, 4800.0],
            "Hourly_Rate_Rp": [34400.0, 35000.0],
            "Total_Cost_Rp": [172_000_000, 168_000_000],
        })
        dl.to_excel(writer, sheet_name="Direct_Labor", index=False)

        # === 5. Utility ===
        ut = pd.DataFrame({
            "Date": ["2026-01-01", "2026-01-01"],
            "Plant": ["Plant A", "Plant B"],
            "Utility_Type": ["Electricity", "Electricity"],
            "Consumption_Unit": [75000.0, 72000.0],
            "Unit_Rate_Rp": [1720.0, 1750.0],
            "Total_Cost_Rp": [129_000_000, 126_000_000],
        })
        ut.to_excel(writer, sheet_name="Utility", index=False)

        # === 6. Maintenance ===
        mt = pd.DataFrame({
            "Date": ["2026-01-01", "2026-01-01"],
            "Plant": ["Plant A", "Plant B"],
            "Machine": ["M-01", "M-02"],
            "Maintenance_Type": ["Preventive", "Preventive"],
            "Quantity": [1.0, 1.0],
            "Unit_Cost_Rp": [72_000_000.0, 68_000_000.0],
            "Total_Cost_Rp": [72_000_000.0, 68_000_000.0],
        })
        mt.to_excel(writer, sheet_name="Maintenance", index=False)

        # === 7. Depreciation ===
        dp = pd.DataFrame({
            "Date": ["2026-01-01", "2026-01-01"],
            "Plant": ["Plant A", "Plant B"],
            "Asset_Code": ["FA-001", "FA-001"],
            "Asset_Category": ["Production Machine", "Production Machine"],
            "Depreciation_Cost_Rp": [86_000_000.0, 82_000_000.0],
        })
        dp.to_excel(writer, sheet_name="Depreciation", index=False)

        # === 8. Standard_Cost ===
        # Basis per element:
        #   Material     : Qty (Kg)  x Price (Rp/Kg)   -> Material_Cost_Rp
        #   Packaging    : Qty (pcs) x Price (Rp/pcs)  -> Packaging_Cost_Rp
        #   Labor/Utility/Dep/Maint : Rp/Kg
        # Total Rp = Material_Cost + Packaging_Cost
        #          + (Labor+Utility+Dep+Maint) x Output_Kg
        sc = pd.DataFrame({
            "Period": [
                "2026-01", "2026-01", "2026-01",
                "2026-01", "2026-01", "2026-01",
            ],
            "Plant": [
                "Plant A", "Plant A", "Plant A",
                "Plant B", "Plant B", "Plant B",
            ],
            "Product": [
                "Resin Pipe 20mm", "Resin Pipe 25mm", "Resin Pipe 32mm",
                "Resin Pipe 20mm", "Resin Pipe 25mm", "Resin Pipe 32mm",
            ],
            "Standard_Material_Qty_Kg": [
                40000.0, 41000.0, 42000.0,
                38000.0, 39000.0, 40000.0,
            ],
            "Standard_Material_Price_Rp": [
                1500.0, 1520.0, 1540.0,
                1550.0, 1570.0, 1590.0,
            ],
            "Standard_Material_Cost_Rp": [
                60_000_000, 62_320_000, 64_680_000,
                58_900_000, 61_230_000, 63_600_000,
            ],
            "Standard_Packaging_Qty": [
                40000.0, 41000.0, 42000.0,
                38000.0, 39000.0, 40000.0,
            ],
            "Standard_Packaging_Price_Rp": [50.0, 52.0, 54.0, 56.0, 58.0, 60.0],
            "Standard_Packaging_Cost_Rp": [
                2_000_000, 2_132_000, 2_268_000,
                2_128_000, 2_262_000, 2_400_000,
            ],
            "Standard_Labor_Rp_per_Kg":        [300.0, 310.0, 315.0,
                                                320.0, 325.0, 330.0],
            "Standard_Utility_Rp_per_Kg":      [200.0, 205.0, 210.0,
                                                215.0, 220.0, 225.0],
            "Standard_Depreciation_Rp_per_Kg": [150.0, 155.0, 160.0,
                                                165.0, 170.0, 175.0],
            "Standard_Maintenance_Rp_per_Kg":  [300.0, 305.0, 310.0,
                                                315.0, 320.0, 325.0],
            "Standard_Unit_Cost_Rp": [2500.0, 2547.0, 2593.0,
                                      2621.0, 2670.0, 2705.0],
            "Standard_Total_Rp": [
                100_000_000, 104_427_000, 108_906_000,
                 99_598_000, 104_130_000, 108_200_000,
            ],
            "Standard_Output_Kg": [
                40000.0, 41000.0, 42000.0,
                38000.0, 39000.0, 40000.0,
            ],
        })
        sc.to_excel(writer, sheet_name="Standard_Cost", index=False)

        # === 9. Budget ===
        bd = pd.DataFrame({
            "Category": ["Material", "Labor", "Utility", "Maintenance"],
            "Budget": [2_889_000_000, 556_000_000, 435_000_000, 234_000_000],
            "Actual": [2_780_000_000, 556_000_000, 417_000_000, 232_000_000],
        })
        bd.to_excel(writer, sheet_name="Budget", index=False)

        # === 10. Inventory ===
        inv = pd.DataFrame({
            "Material": ["Resin PP", "Resin PE", "Pigment",
                         "Additive", "Regrind", "Solvent"],
            "Stock_Kg": [42_000, 18_000, 9_000, 6_500, 3_000, 1_200],
            "Monthly_Usage": [30_000, 22_000, 4_000, 5_800, 0, 900],
        })
        inv.to_excel(writer, sheet_name="Inventory", index=False)

        # === 11. Risk_Register ===
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

        # === 12. Config ===
        cfg = pd.DataFrame({
            "Parameter": ["Target_Yield", "Target_Scrap", "Target_OEE",
                          "Max_Cost_per_Kg", "Utility_Share_Max"],
            "Value": [98.0, 2.0, 85.0, 12_500.0, 15.0],
        })
        cfg.to_excel(writer, sheet_name="Config", index=False)

    buf.seek(0)
    return buf.read()