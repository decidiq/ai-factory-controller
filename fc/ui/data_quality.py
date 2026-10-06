"""Halaman Kualitas Data - laporan validasi (BRD 5.5) dan kamus data (BRD 5.4)."""
import pandas as pd
import streamlit as st

from ..pipeline import Dataset
from ..schema import SHEETS

_LEVEL = {"required": "Wajib", "kpi": "Untuk KPI", "optional": "Opsional"}


def render_issues(ds: Dataset) -> None:
    rep = ds.report
    st.markdown("#### Ringkasan per sheet")
    st.dataframe(rep.summary_frame(), use_container_width=True, hide_index=True)
    st.markdown("#### Temuan validasi")
    frame = rep.to_frame()
    if frame.empty:
        st.success("Tidak ada temuan. Seluruh data lolos validasi.")
    else:
        st.dataframe(frame, use_container_width=True, hide_index=True)


def render_blocking(ds: Dataset) -> None:
    st.error("Data tidak dapat dipakai. Tidak ada angka yang ditampilkan sampai masalah berikut diperbaiki "
             "(sistem tidak memakai data pengganti).")
    render_issues(ds)


def render(ds: Dataset) -> None:
    st.title("🧪 Kualitas Data")
    st.caption(f"Sumber: {ds.report.source_label} · Dibaca: {ds.report.loaded_at}")
    render_issues(ds)
    st.markdown("---")
    st.markdown("#### Kamus data")
    st.caption("Struktur kolom yang diharapkan. Kolom 'Untuk KPI' tidak memblokir pembacaan, "
               "tetapi KPI terkait akan tampil 'Data tidak tersedia' bila kolom tidak ada.")
    rows = [{"Sheet": sh.name, "Kolom": c.name, "Tipe": c.kind, "Satuan": c.unit,
             "Level": _LEVEL[c.level], "Dipakai untuk": c.feeds or sh.module}
            for sh in SHEETS for c in sh.columns]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
