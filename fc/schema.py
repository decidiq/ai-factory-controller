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


# Dimensi umum di sheet biaya + kolom Date (untuk ERP yang harian)
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