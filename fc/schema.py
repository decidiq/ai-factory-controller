"""Kamus data (BRD bagian 5.4)."""
from dataclasses import dataclass
from typing import Optional, Tuple

REQUIRED, KPI, OPTIONAL = "required", "kpi", "optional"


@dataclass(frozen=True)
class Column:
    name: str
    kind: str
    level: str = REQUIRED
    unit: str = ""
    aliases: Tuple[str, ...] = ()
    feeds: str = ""
    min: Optional[float] = 0
    max: Optional[float] = None


@dataclass(frozen=True)
class Sheet:
    name: str
    columns: Tuple[Column, ...]
    core: bool = True
    module: str = ""


def text(name, level=REQUIRED, **kw):
    return Column(name, "text", level, **kw)


def num(name, level=REQUIRED, unit="", **kw):
    return Column(name, "number", level, unit=unit, **kw)


_DIMS = (
    Column("Date", "date", OPTIONAL, feeds="Dipakai turunkan Period harian"),
    text("Plant", OPTIONAL, feeds="Biaya per Plant"),
    text("Period", OPTIONAL, feeds="Biaya per periode (YYYY-MM)"),
)


SHEETS: Tuple[Sheet, ...] = (
    Sheet("Raw_Material", (
        text("Material"),
        num("Cost", unit="Rp",
            aliases=("Total_Cost_Rp", "Cost_Rp", "Total_Cost")),
        num("Qty_Kg", unit="Kg",
            aliases=("Quantity_Kg", "Quantity")),
    ) + _DIMS, module="COGM, Pareto, Input_Kg turunan"),

    Sheet("Packaging", (
        num("Cost", unit="Rp",
            aliases=("Total_Cost_Rp", "Cost_Rp", "Total_Cost")),
        num("Qty", OPTIONAL, unit="pcs",
            aliases=("Quantity", "Qty_Pcs")),
    ) + _DIMS, module="COGM"),

    Sheet("Direct_Labor", (
        num("Cost", unit="Rp",
            aliases=("Total_Cost_Rp", "Cost_Rp", "Total_Cost")),
    ) + _DIMS, module="COGM"),

    Sheet("Utility", (
        num("Electricity_Cost", unit="Rp",
            aliases=("Cost", "Total_Cost_Rp", "Cost_Rp", "Total_Cost")),
    ) + _DIMS, module="COGM"),

    Sheet("Maintenance", (
        num("Cost", unit="Rp",
            aliases=("Maintenance", "Total_Cost_Rp", "Cost_Rp", "Total_Cost")),
    ) + _DIMS, module="COGM"),

    Sheet("Depreciation", (
        num("Monthly_Dep", unit="Rp/bulan",
            aliases=("Cost", "Total_Cost_Rp", "Cost_Rp",
                     "Depreciation_Cost_Rp", "Total_Cost")),
    ) + _DIMS, module="COGM"),

    # === Standard Cost (input user per Product + Plant) ===
    # Basis per element:
    #   Material   : Qty (Kg) x Price (Rp/Kg)
    #   Packaging  : Qty (pcs) x Price (Rp/pcs)
    #   Labor      : Rp/Kg
    #   Utility    : Rp/Kg
    #   Depreciation : Rp/Kg  (fixed, tapi dialokasikan per Kg)
    #   Maintenance : Rp/Kg
    Sheet("Standard_Cost", (
        text("Product"),
        # Material
        num("Standard_Material_Qty_Kg", unit="Kg",
            aliases=("Material_Qty_Kg", "Std_Material_Qty")),
        num("Standard_Material_Price_Rp", unit="Rp/Kg",
            aliases=("Material_Price_Rp", "Std_Material_Price")),
        num("Standard_Material_Cost_Rp", OPTIONAL, unit="Rp",
            aliases=("Material_Cost_Rp", "Std_Material_Cost")),
        # Packaging
        num("Standard_Packaging_Qty", unit="pcs",
            aliases=("Packaging_Qty", "Std_Packaging_Qty")),
        num("Standard_Packaging_Price_Rp", unit="Rp/pcs",
            aliases=("Packaging_Price_Rp", "Std_Packaging_Price")),
        num("Standard_Packaging_Cost_Rp", OPTIONAL, unit="Rp",
            aliases=("Packaging_Cost_Rp", "Std_Packaging_Cost")),
        # Rp/Kg elements
        num("Standard_Labor_Rp_per_Kg", unit="Rp/Kg",
            aliases=("Labor_Rp_per_Kg", "Standard_Labor_Rp")),
        num("Standard_Utility_Rp_per_Kg", unit="Rp/Kg",
            aliases=("Utility_Rp_per_Kg", "Standard_Utility_Rp")),
        num("Standard_Depreciation_Rp_per_Kg", unit="Rp/Kg",
            aliases=("Depreciation_Rp_per_Kg", "Standard_Depreciation_Rp")),
        num("Standard_Maintenance_Rp_per_Kg", unit="Rp/Kg",
            aliases=("Maintenance_Rp_per_Kg", "Standard_Maintenance_Rp")),
        # Total
        num("Standard_Unit_Cost_Rp", OPTIONAL, unit="Rp/Kg",
            aliases=("Unit_Cost_Rp", "Unit_Cost")),
        num("Standard_Total_Rp", OPTIONAL, unit="Rp",
            aliases=("Total_Rp", "Total")),
        # Output standard (untuk hitung Total Rp dari Rp/Kg)
        num("Standard_Output_Kg", OPTIONAL, unit="Kg",
            aliases=("Output_Kg_Standard", "Std_Output_Kg")),
    ) + _DIMS, core=False, module="Standard vs Actual Variance"),

    Sheet("Production", (
        Column("Date", "date"),
        text("Line", OPTIONAL, feeds="Filter Line"),
        text("Machine"),
        num("Output_Kg", unit="Kg"),
        text("Plant", OPTIONAL, feeds="Filter Plant"),
        text("Product", OPTIONAL, feeds="Filter Product"),
        num("Input_Kg", KPI, "Kg", feeds="Yield, Scrap"),
        num("Scrap_Kg", KPI, "Kg", feeds="Scrap, OEE Quality"),
        num("Planned_Time_Min", KPI, "Menit", feeds="OEE Availability"),
        num("Downtime_Min", KPI, "Menit", feeds="OEE Availability"),
        num("Ideal_Rate_Kg_per_Min", KPI, "Kg/menit", feeds="OEE Performance"),
    ), module="Produksi, Yield, Scrap, OEE, Cost/Kg"),

    Sheet("Production_KPI", (
        Column("Date", "date"),
        num("Yield_%", KPI, "%", feeds="Yield dilaporkan"),
        num("Scrap_%", KPI, "%", feeds="Scrap dilaporkan"),
        num("OEE_%", KPI, "%", feeds="OEE dilaporkan"),
    ), core=False, module="KPI dilaporkan (cadangan)"),

    Sheet("Config", (
        text("Parameter"),
        num("Value"),
    ), core=False, module="Target KPI dari Config"),

    Sheet("Budget", (
        text("Category"),
        num("Budget", unit="Rp", aliases=("Budget_Rp",)),
        num("Actual", KPI, "Rp", aliases=("Actual_Rp",)),
        Column("Period", "text", OPTIONAL, aliases=("Month",),
               feeds="Periode budget (YYYY-MM)"),
    ), core=False, module="Manufacturing Variance"),

    Sheet("Inventory", (
        text("Material"),
        num("Stock_Kg", unit="Kg"),
        num("Monthly_Usage", unit="Kg/bulan"),
    ), core=False, module="Inventory Analysis"),

    Sheet("Risk_Register", (
        text("Risk"),
        text("Status", OPTIONAL),
        text("Probability", OPTIONAL),
        text("Impact", OPTIONAL),
        Column("Probability_Val", "int", OPTIONAL, unit="skala 1-3", min=1, max=3),
        Column("Impact_Val", "int", OPTIONAL, unit="skala 1-3", min=1, max=3),
    ), core=False, module="Risk Register"),
)

SHEET_BY_NAME = {s.name: s for s in SHEETS}

COST_SHEETS = (
    ("Raw_Material", "Cost", "Material"),
    ("Packaging", "Cost", "Packaging"),
    ("Direct_Labor", "Cost", "Labor"),
    ("Utility", "Electricity_Cost", "Utility"),
    ("Maintenance", "Cost", "Maintenance"),
    ("Depreciation", "Monthly_Dep", "Depreciation"),
)