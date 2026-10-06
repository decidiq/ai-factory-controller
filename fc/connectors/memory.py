"""Konektor dari DataFrame di memori (untuk Mode Demo dan pengujian)."""
from typing import Dict

import pandas as pd


class MemoryConnector:
    def __init__(self, frames: Dict[str, pd.DataFrame], label: str = "Data di memori"):
        self.frames = frames
        self.label = label

    def read_all(self) -> Dict[str, pd.DataFrame]:
        return {k: v.copy() for k, v in self.frames.items()}
