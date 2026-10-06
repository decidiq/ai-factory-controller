"""Konektor Excel (file lokal, path, atau hasil unggahan)."""
import os
from typing import Dict, Union, BinaryIO

import pandas as pd

from .base import DataSourceError


class ExcelConnector:
    def __init__(self, source: Union[str, BinaryIO], label: str = ""):
        self.source = source
        self.label = label or (os.path.basename(source) if isinstance(source, str) else "Excel (unggahan)")

    def read_all(self) -> Dict[str, pd.DataFrame]:
        if isinstance(self.source, str) and not os.path.exists(self.source):
            raise DataSourceError(f"File tidak ditemukan: {self.source}")
        try:
            return pd.read_excel(self.source, sheet_name=None)
        except Exception as exc:  # file rusak, bukan xlsx, terkunci, dll.
            raise DataSourceError(f"Gagal membaca file Excel: {exc}") from exc
