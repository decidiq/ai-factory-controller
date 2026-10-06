"""Kontrak konektor data (BRD bagian 5.1): hanya-baca, format keluaran standar.

Setiap konektor (Excel, Google Sheets, Odoo, SAP/QAD via ekspor) cukup
mengimplementasikan read_all() yang mengembalikan {nama_sheet: DataFrame}.
Pipeline di atasnya tidak perlu tahu asal datanya.
"""
from typing import Dict, Protocol

import pandas as pd


class DataSourceError(Exception):
    """Sumber data tidak dapat diakses atau dibaca. Pesan ditampilkan apa adanya ke pengguna."""


class DataConnector(Protocol):
    label: str

    def read_all(self) -> Dict[str, pd.DataFrame]:
        """Baca semua sheet yang tersedia. Tidak boleh menulis ke sumber."""
        ...
