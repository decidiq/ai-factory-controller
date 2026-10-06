"""Pipeline data: konektor -> validasi -> Dataset siap pakai."""
from dataclasses import dataclass
from datetime import date
from typing import Dict, List, Optional
import pandas as pd

from .connectors.base import DataConnector, DataSourceError
from .schema import COST_SHEETS, SHEETS
from .validation import Issue, ValidationReport, validate_sheet


RISK_TEXT_MAP = {"high": 3, "tinggi": 3, "medium": 2, "sedang": 2, "low": 1, "rendah": 1}


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
                   self.budget, self.inventory, self.risk):
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
                   self.budget, self.inventory, self.risk):
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
    """Turunkan Input_Kg dari Raw_Material.Qty_Kg per Date+Machine bila kosong."""
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
    """Konversi teks High/Medium/Low -> 1-3 bila kolom _Val tidak ada."""
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
        budget=clean.get("Budget"),
        inventory=clean.get("Inventory"),
        risk=risk,
        config=clean.get("Config"),
        production_kpi=clean.get("Production_KPI"),
        is_demo=is_demo,
    )