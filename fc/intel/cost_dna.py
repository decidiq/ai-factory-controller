"""Cost DNA Engine — variance decomposition & waterfall."""
from dataclasses import dataclass
from typing import Dict, Optional

import numpy as np
import pandas as pd


@dataclass
class VarianceDecomposition:
    price: float = 0.0
    volume: float = 0.0
    mix: float = 0.0
    efficiency: float = 0.0
    other: float = 0.0

    @property
    def total(self) -> float:
        return self.price + self.volume + self.mix + self.efficiency + self.other

    def as_dict(self) -> Dict[str, float]:
        return {
            "Harga Material": self.price,
            "Volume Produksi": self.volume,
            "Mix Produk": self.mix,
            "Efisiensi (Yield/Scrap)": self.efficiency,
            "Lainnya": self.other,
        }


def decompose_variance(current, previous, scope_plant=None):
    if current is None or current.empty or previous is None or previous.empty:
        return VarianceDecomposition()

    if scope_plant and "Plant" in current.columns:
        current = current[current["Plant"] == scope_plant]
        previous = previous[previous["Plant"] == scope_plant]

    def agg(df):
        if df.empty or not {"Material", "Qty_Kg", "Cost"} <= set(df.columns):
            return pd.DataFrame(columns=["Material", "Qty", "Cost", "Price"])
        g = df.groupby("Material", as_index=False).agg(
            Qty=("Qty_Kg", "sum"),
            Cost=("Cost", "sum"),
        )
        g["Price"] = g["Cost"] / g["Qty"].replace(0, np.nan)
        return g

    cur = agg(current)
    prev = agg(previous)

    if cur.empty or prev.empty:
        return VarianceDecomposition()

    m = prev.merge(cur, on="Material", how="outer",
                   suffixes=("_prev", "_cur")).fillna(0)

    m["price_var"] = (m["Price_cur"] - m["Price_prev"]) * m["Qty_cur"]
    m["volume_var"] = (m["Qty_cur"] - m["Qty_prev"]) * m["Price_prev"]

    qty_cur_total = m["Qty_cur"].sum()
    qty_prev_total = m["Qty_prev"].sum()
    if qty_cur_total > 0 and qty_prev_total > 0:
        share_cur = m["Qty_cur"] / qty_cur_total
        share_prev = m["Qty_prev"] / qty_prev_total
        m["mix_var"] = (share_cur - share_prev) * qty_cur_total * m["Price_prev"]
    else:
        m["mix_var"] = 0.0

    cogm_cur = m["Cost_cur"].sum()
    cogm_prev = m["Cost_prev"].sum()
    delta = cogm_cur - cogm_prev

    price = float(m["price_var"].sum())
    volume = float(m["volume_var"].sum())
    mix = float(m["mix_var"].sum())
    efficiency = float(delta - price - volume - mix)

    return VarianceDecomposition(price=price, volume=volume, mix=mix,
                                 efficiency=efficiency, other=0.0)


def waterfall_cogm(breakdown):
    if not breakdown:
        return pd.DataFrame(columns=["Category", "Cost"])
    df = pd.DataFrame(list(breakdown.items()), columns=["Category", "Cost"])
    df = df[df["Cost"] > 0].sort_values("Cost", ascending=False)
    return df.reset_index(drop=True)