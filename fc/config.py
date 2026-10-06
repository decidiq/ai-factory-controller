"""Konfigurasi target dan ambang KPI (BRD bagian 6)."""
from dataclasses import dataclass, replace
from typing import Optional
import pandas as pd


@dataclass(frozen=True)
class Targets:
    yield_min: float = 98.0
    scrap_max: float = 2.0
    oee_min: float = 85.0
    utility_share_max: float = 15.0
    slow_moving_days: int = 45
    variance_tolerance_pct: float = 5.0
    max_cost_per_kg: float = 0.0


DEFAULT_TARGETS = Targets()

SCORE_PENALTY = 10
SCORE_BANDS = ((90, "Excellent"), (80, "Good"), (70, "Need Improvement"), (0, "Critical"))

DEFAULT_DATA_FILE = "sample/factory_data_demo.xlsx"
DATA_PATH = DEFAULT_DATA_FILE
DEMO_FILE_HINTS = ("demo", "sample", "contoh")

# Backward-compat
TARGETS = DEFAULT_TARGETS

_CONFIG_MAP = {
    "Target_Yield": "yield_min",
    "Target_Scrap": "scrap_max",
    "Target_OEE": "oee_min",
    "Utility_Share_Max": "utility_share_max",
    "Slow_Moving_Days": "slow_moving_days",
    "Variance_Tolerance_Pct": "variance_tolerance_pct",
    "Max_Cost_per_Kg": "max_cost_per_kg",
}


def targets_from_config(config: Optional[pd.DataFrame]) -> Targets:
    """Baca target dari sheet Config (BRD 6.3); fallback ke default."""
    if config is None or getattr(config, "empty", True):
        return DEFAULT_TARGETS
    if not {"Parameter", "Value"} <= set(config.columns):
        return DEFAULT_TARGETS
    cfg = dict(zip(config["Parameter"].astype(str), config["Value"]))
    kwargs = {}
    for param, field in _CONFIG_MAP.items():
        if param in cfg:
            try:
                kwargs[field] = float(cfg[param])
            except (TypeError, ValueError):
                pass
    return replace(DEFAULT_TARGETS, **kwargs)