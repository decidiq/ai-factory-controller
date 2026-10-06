"""Inventory Analysis - data-driven (BRD 6)."""
import streamlit as st

from ..config import targets_from_config
from ..kpi import Scope, inventory_table
from ..pipeline import Dataset


def render(ds: Dataset, scope: Scope) -> None:
    st.title("📦 Inventory Analysis")

    inv = ds.inventory
    if inv is None or inv.empty:
        st.warning("Data Inventory tidak tersedia (sheet 'Inventory').")
        st.info("Sesuai BRD 5.5: tidak ada data pengganti yang ditampilkan.")
        return

    if not {"Material", "Stock_Kg", "Monthly_Usage"} <= set(inv.columns):
        st.error("Sheet Inventory harus punya kolom: Material, Stock_Kg, Monthly_Usage.")
        return

    targets = targets_from_config(ds.config)
    tbl = inventory_table(inv)

    total_kg = float(tbl["Stock_Kg"].sum())
    slow = int((tbl["Status"] == "Slow Moving").sum())
    dead = int((tbl["Status"] == "Dead Stock").sum())

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Jenis Material", f"{len(tbl)}")
    c2.metric("Total Stok", f"{total_kg:,.0f} Kg")
    c3.metric("Slow Moving", f"{slow}", help=f"> {targets.slow_moving_days} hari")
    c4.metric("Dead Stock", f"{dead}")

    st.subheader("Detail Inventory")
    st.dataframe(tbl, use_container_width=True, hide_index=True)