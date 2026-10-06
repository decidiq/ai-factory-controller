"""Manufacturing Variance - Budget vs Actual (BRD 6)."""
import plotly.express as px
import streamlit as st

from ..config import targets_from_config
from ..kpi import variance_table
from ..pipeline import Dataset


def render(ds: Dataset, scope) -> None:
    st.title("⚖️ Manufacturing Variance (Budget vs Actual)")

    budget = ds.budget
    if budget is None or budget.empty:
        st.warning("Sheet **Budget** tidak tersedia.")
        return
    if not {"Category", "Budget"} <= set(budget.columns):
        st.error("Sheet Budget harus punya kolom **Category** dan **Budget**.")
        return
    if "Actual" not in budget.columns or budget["Actual"].isna().all():
        st.error("Kolom **Actual** belum ada atau kosong di sheet Budget. "
                 "Sesuai BRD 5.4: Actual perlu diturunkan dari sheet biaya. "
                 "Tidak ada angka pengganti yang ditampilkan.")
        return

    targets = targets_from_config(ds.config)
    tbl = variance_table(budget)

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Budget", f"Rp {tbl['Budget'].sum():,.0f}")
    c2.metric("Total Actual", f"Rp {tbl['Actual'].sum():,.0f}")
    v_total = tbl["Variance"].sum()
    c3.metric("Total Variance", f"Rp {v_total:,.0f}",
              delta=("Over budget" if v_total > 0 else "Under budget"),
              delta_color="inverse")

    st.subheader("Variance per Kategori")
    fig = px.bar(tbl, x="Category", y=["Budget", "Actual"], barmode="group")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Tabel Variance")
    st.dataframe(
        tbl.style.format({
            "Budget": "Rp {:,.0f}", "Actual": "Rp {:,.0f}",
            "Variance": "Rp {:,.0f}", "Variance_Pct": "{:+.2f}%",
            "Utilization_Pct": "{:.2f}%",
        }),
        use_container_width=True,
    )
    st.caption(f"Toleransi variance: ±{targets.variance_tolerance_pct:g}% (BRD 6).")