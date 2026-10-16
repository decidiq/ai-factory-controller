"""Pipeline data: konektor -> validasi -> Dataset siap pakai."""
from dataclasses import dataclass
from datetime import date
from typing import Dict, List, Optional
import pandas as pd

from .connectors.base import DataConnector, DataSourceError
from .schema import COST_SHEETS, SHEETS
from .validation import Issue, ValidationReport, validate_sheet


RISK_TEXT_MAP = {"high": 3, "tinggi": 3, "medium": 2, "sedang": 2, "low": 1, "rendah": 1}

# Kolom breakdown Standard_Cost
STD_RP_PER_KG_COLS = (
    "Standard_Labor_Rp_per_Kg",
    "Standard_Utility_Rp_per_Kg",
    "Standard_Depreciation_Rp_per_Kg",
    "Standard_Maintenance_Rp_per_Kg",
)


def _map_risk_level(series: Optional[pd.Series]) -> pd.Series:
    if series is None or series.empty:
        return pd.Series(dtype="Int64")
    txt = series.astype(str).str.strip().str.lower()
    return txt.map(RISK_TEXT_MAP).astype("Int64")


@dataclass
class Dataset:
    report: ValidationReport
    production: Optional[pd.DataFrame] = None
    costs: Optional[pd.DataFrame] = None
    raw_material: Optional[pd.DataFrame] = None
    standard_cost: Optional[pd.DataFrame] = None
    budget: Optional[pd.DataFrame] = None
    inventory: Optional[pd.DataFrame] = None
    risk: Optional[pd.DataFrame] = None
    config: Optional[pd.DataFrame] = None
    production_kpi: Optional[pd.DataFrame] = None
    is_demo: bool = False

    @property
    def ok(self) -> bool:
        return (not self.report.blocking) and self.production is not None and self.costs is not None

    def plants(self) -> List[str]:
        for df in (self.production, self.costs, self.raw_material,
                   self.standard_cost, self.budget, self.inventory, self.risk):
            if df is not None and "Plant" in df.columns:
                vals = [str(v) for v in df["Plant"].dropna().unique() if str(v).strip()]
                if vals:
                    return sorted(set(vals))
        return []

    def lines(self, plant: Optional[str] = None) -> List[str]:
        for df in (self.production, self.costs):
            if df is not None and "Line" in df.columns:
                sub = df
                if plant and "Plant" in sub.columns:
                    sub = sub[sub["Plant"] == plant]
                vals = [str(v) for v in sub["Line"].dropna().unique() if str(v).strip()]
                if vals:
                    return sorted(set(vals))
        return []

    def date_span(self) -> Optional[tuple]:
        dates = []
        for df in (self.production, self.costs, self.raw_material,
                   self.standard_cost, self.budget, self.inventory, self.risk):
            if df is None:
                continue
            for col in ("Period", "Date", "Month"):
                if col in df.columns:
                    parsed = pd.to_datetime(df[col], errors="coerce").dropna()
                    if not parsed.empty:
                        dates.extend(parsed.tolist())
        if dates:
            return min(dates).date(), max(dates).date()
        return None


def _derive_input_kg(production, raw_material):
    if production is None:
        return None
    has = "Input_Kg" in production.columns and production["Input_Kg"].notna().any()
    if has or raw_material is None or raw_material.empty:
        return production
    if not {"Date", "Machine", "Qty_Kg"} <= set(raw_material.columns):
        return production
    derived = (raw_material.groupby(["Date", "Machine"], dropna=True)["Qty_Kg"]
               .sum().reset_index().rename(columns={"Qty_Kg": "Input_Kg"}))
    base = production.drop(columns=["Input_Kg"], errors="ignore")
    return base.merge(derived, on=["Date", "Machine"], how="left")


def _normalize_risk(risk):
    if risk is None or risk.empty:
        return risk
    risk = risk.copy()
    if ("Probability_Val" not in risk.columns) or risk["Probability_Val"].isna().any():
        if "Probability" in risk.columns:
            risk["Probability_Val"] = _map_risk_level(risk["Probability"])
    if ("Impact_Val" not in risk.columns) or risk["Impact_Val"].isna().any():
        if "Impact" in risk.columns:
            risk["Impact_Val"] = _map_risk_level(risk["Impact"])
    return risk


def _normalize_cost_period(df: Optional[pd.DataFrame]) -> Optional[pd.DataFrame]:
    """Normalisasi sheet biaya: derive Period dari Date + agregasi bulanan."""
    if df is None or df.empty:
        return df

    df = df.copy()
    has_date = "Date" in df.columns
    has_period = "Period" in df.columns

    if has_date and not has_period:
        dt = pd.to_datetime(df["Date"], errors="coerce")
        df["Period"] = dt.dt.strftime("%Y-%m")

    if "Period" not in df.columns:
        return df

    if has_date:
        group_cols = ["Period"]
        for col in ("Plant", "Material", "Category"):
            if col in df.columns:
                group_cols.append(col)

        agg_map = {}
        for col in ("Cost", "Electricity_Cost", "Monthly_Dep", "Qty_Kg", "Qty"):
            if col in df.columns:
                agg_map[col] = "sum"

        if agg_map:
            df = df.groupby(group_cols, as_index=False, dropna=False).agg(agg_map)

        df = df.drop(columns=["Date"], errors="ignore")

    return df


def _ensure_standard_cost(df: Optional[pd.DataFrame]) -> Optional[pd.DataFrame]:
    """Lengkapi Standard_Cost:

    - Standard_Material_Cost_Rp = Material_Qty_Kg x Material_Price_Rp
    - Standard_Packaging_Cost_Rp = Packaging_Qty x Packaging_Price_Rp
    - Standard_Unit_Cost_Rp = (Material_Cost + Packaging_Cost) / Output_Kg
                              + Labor + Utility + Dep + Maint (Rp/Kg)
    - Standard_Total_Rp = Material_Cost + Packaging_Cost
                          + (Labor+Utility+Dep+Maint) x Output_Kg
    """
    if df is None or df.empty:
        return df
    df = df.copy()

    # Material cost
    m_qty = pd.to_numeric(df.get("Standard_Material_Qty_Kg"), errors="coerce")
    m_prc = pd.to_numeric(df.get("Standard_Material_Price_Rp"), errors="coerce")
    if m_qty is not None and m_prc is not None:
        calc = m_qty * m_prc
        if "Standard_Material_Cost_Rp" not in df.columns:
            df["Standard_Material_Cost_Rp"] = calc
        else:
            cur = pd.to_numeric(df["Standard_Material_Cost_Rp"], errors="coerce")
            miss = cur.isna() | (cur == 0)
            if miss.any():
                df.loc[miss, "Standard_Material_Cost_Rp"] = calc[miss]

    # Packaging cost
    p_qty = pd.to_numeric(df.get("Standard_Packaging_Qty"), errors="coerce")
    p_prc = pd.to_numeric(df.get("Standard_Packaging_Price_Rp"), errors="coerce")
    if p_qty is not None and p_prc is not None:
        calc = p_qty * p_prc
        if "Standard_Packaging_Cost_Rp" not in df.columns:
            df["Standard_Packaging_Cost_Rp"] = calc
        else:
            cur = pd.to_numeric(df["Standard_Packaging_Cost_Rp"], errors="coerce")
            miss = cur.isna() | (cur == 0)
            if miss.any():
                df.loc[miss, "Standard_Packaging_Cost_Rp"] = calc[miss]

    # Rp/Kg parts
    rp_per_kg = pd.Series(0.0, index=df.index)
    for c in STD_RP_PER_KG_COLS:
        if c in df.columns:
            rp_per_kg = rp_per_kg.add(
                pd.to_numeric(df[c], errors="coerce").fillna(0), fill_value=0
            )

    # Output_Kg standard
    out = pd.to_numeric(df.get("Standard_Output_Kg"), errors="coerce")

    # Unit cost = (Material_Cost + Packaging_Cost)/Output + rp_per_kg
    mat_cost = pd.to_numeric(df.get("Standard_Material_Cost_Rp"), errors="coerce").fillna(0)
    pkg_cost = pd.to_numeric(df.get("Standard_Packaging_Cost_Rp"), errors="coerce").fillna(0)
    per_kg_from_variable = pd.Series(0.0, index=df.index)
    if out is not None:
        mask = out > 0
        per_kg_from_variable.loc[mask] = (mat_cost[mask] + pkg_cost[mask]) / out[mask]

    unit_cost_calc = per_kg_from_variable + rp_per_kg

    if "Standard_Unit_Cost_Rp" not in df.columns:
        df["Standard_Unit_Cost_Rp"] = unit_cost_calc
    else:
        cur = pd.to_numeric(df["Standard_Unit_Cost_Rp"], errors="coerce")
        miss = cur.isna() | (cur == 0)
        if miss.any():
            df.loc[miss, "Standard_Unit_Cost_Rp"] = unit_cost_calc[miss]

    # Total = Material + Packaging + (Labor+Utility+Dep+Maint) x Output
    total_calc = mat_cost + pkg_cost
    if out is not None:
        total_calc = total_calc + rp_per_kg * out.fillna(0)
    if "Standard_Total_Rp" not in df.columns:
        df["Standard_Total_Rp"] = total_calc
    else:
        cur = pd.to_numeric(df["Standard_Total_Rp"], errors="coerce")
        miss = cur.isna() | (cur == 0)
        if miss.any():
            df.loc[miss, "Standard_Total_Rp"] = total_calc[miss]

    return df


def load_dataset(connector: DataConnector, is_demo: bool = False,
                 today: Optional[date] = None) -> Dataset:
    report = ValidationReport(source_label=getattr(connector, "label", ""))
    try:
        frames = connector.read_all()
    except DataSourceError as exc:
        report.issues.append(Issue("error", "Sumber data", "", str(exc), blocking=True))
        return Dataset(report=report, is_demo=is_demo)

    clean: Dict[str, pd.DataFrame] = {}
    for sheet in SHEETS:
        raw = frames.get(sheet.name)
        if raw is None:
            continue
        df, srep, issues = validate_sheet(raw, sheet, today)
        report.sheets[sheet.name] = srep
        report.issues.extend(issues)
        if df is not None:
            clean[sheet.name] = df

    if report.blocking:
        return Dataset(report=report, is_demo=is_demo)

    # ==== Normalisasi sheet biaya: harian -> bulanan ====
    for sheet_name, _col, _cat in COST_SHEETS:
        if sheet_name in clean:
            clean[sheet_name] = _normalize_cost_period(clean[sheet_name])

    # Standard_Cost: lengkapi cost & total kalau kosong
    if "Standard_Cost" in clean:
        clean["Standard_Cost"] = _ensure_standard_cost(clean["Standard_Cost"])

    raw_material = clean.get("Raw_Material")
    production = _derive_input_kg(clean.get("Production"), raw_material)
    risk = _normalize_risk(clean.get("Risk_Register"))

    # Cost summary
    parts = []
    for sheet_name, col, category in COST_SHEETS:
        df = clean.get(sheet_name)
        if df is not None and col in df.columns:
            parts.append(pd.DataFrame({
                "Category": category,
                "Cost": df[col].astype(float),
                "Plant": df["Plant"] if "Plant" in df.columns else pd.Series(pd.NA, index=df.index, dtype="string"),
                "Period": df["Period"] if "Period" in df.columns else pd.Series(pd.NA, index=df.index, dtype="string"),
            }))
    costs = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame(
        columns=["Category", "Cost", "Plant", "Period"])

    return Dataset(
        report=report,
        production=production,
        costs=costs,
        raw_material=raw_material,
        standard_cost=clean.get("Standard_Cost"),
        budget=clean.get("Budget"),
        inventory=clean.get("Inventory"),
        risk=risk,
        config=clean.get("Config"),
        production_kpi=clean.get("Production_KPI"),
        is_demo=is_demo,
    )