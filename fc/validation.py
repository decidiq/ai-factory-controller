"""Validasi data sesuai BRD bagian 5.5.

Prinsip: data yang tidak valid DITOLAK dan DILAPORKAN, tidak pernah diganti
dengan angka karangan. Setiap baris yang ditolak tercatat beserta nomor baris
Excel-nya (baris 1 = header).
"""
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Dict, List, Optional, Tuple

import pandas as pd

from .schema import KPI, OPTIONAL, REQUIRED, Sheet

MIN_VALID_YEAR = 2000


@dataclass
class Issue:
    severity: str            # error | warning | info
    sheet: str
    column: str
    message: str
    rows: Tuple[int, ...] = ()   # nomor baris Excel
    blocking: bool = False


@dataclass
class SheetReport:
    sheet: str
    found: bool
    rows_in: int = 0
    rows_ok: int = 0
    rows_rejected: int = 0


@dataclass
class ValidationReport:
    source_label: str = ""
    loaded_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    issues: List[Issue] = field(default_factory=list)
    sheets: Dict[str, SheetReport] = field(default_factory=dict)

    @property
    def blocking(self) -> bool:
        return any(i.blocking for i in self.issues)

    @property
    def rows_rejected(self) -> int:
        return sum(s.rows_rejected for s in self.sheets.values())

    def by_severity(self, severity: str) -> List[Issue]:
        return [i for i in self.issues if i.severity == severity]

    def to_frame(self) -> pd.DataFrame:
        rows = [{
            "Tingkat": i.severity, "Sheet": i.sheet, "Kolom": i.column,
            "Pesan": i.message, "Baris Excel": _fmt_rows(i.rows),
        } for i in self.issues]
        return pd.DataFrame(rows, columns=["Tingkat", "Sheet", "Kolom", "Pesan", "Baris Excel"])

    def summary_frame(self) -> pd.DataFrame:
        rows = [{
            "Sheet": s.sheet,
            "Ditemukan": "Ya" if s.found else "Tidak",
            "Baris dibaca": s.rows_in, "Baris diterima": s.rows_ok, "Baris ditolak": s.rows_rejected,
        } for s in self.sheets.values()]
        return pd.DataFrame(rows)


def _fmt_rows(rows, limit: int = 8) -> str:
    rows = sorted(set(int(r) for r in rows))
    if not rows:
        return ""
    txt = ", ".join(str(r) for r in rows[:limit])
    return txt + (f" (+{len(rows) - limit} lainnya)" if len(rows) > limit else "")


def _excel_rows(index) -> Tuple[int, ...]:
    return tuple(int(i) + 2 for i in index)  # index 0 = baris Excel 2 (baris 1 = header)


def _canonicalize(raw: pd.DataFrame, sheet: Sheet) -> pd.DataFrame:
    df = raw.copy()
    df.columns = [str(c).strip() for c in df.columns]
    for col in sheet.columns:
        if col.name not in df.columns:
            for alias in col.aliases:
                if alias in df.columns:
                    df = df.rename(columns={alias: col.name})
                    break
    keep = [c.name for c in sheet.columns if c.name in df.columns]
    return df[keep]


def _to_date(s: pd.Series) -> pd.Series:
    if pd.api.types.is_datetime64_any_dtype(s):
        return s
    if pd.api.types.is_numeric_dtype(s):  # serial tanggal Excel
        return pd.to_datetime(s, unit="D", origin="1899-12-30", errors="coerce")
    return pd.to_datetime(s, errors="coerce", format="mixed")


def validate_sheet(raw: pd.DataFrame, sheet: Sheet, today: Optional[date] = None
                   ) -> Tuple[Optional[pd.DataFrame], SheetReport, List[Issue]]:
    """Validasi satu sheet. Mengembalikan (data bersih atau None, laporan, daftar issue)."""
    issues: List[Issue] = []
    today_ts = pd.Timestamp(today or date.today())
    df = _canonicalize(raw, sheet)
    n_in = len(df)
    sev_block = "error" if sheet.core else "warning"

    missing_req = [c.name for c in sheet.columns if c.level == REQUIRED and c.name not in df.columns]
    if missing_req:
        issues.append(Issue(sev_block, sheet.name, ", ".join(missing_req),
                            f"Kolom wajib tidak ada: {', '.join(missing_req)}."
                            + ("" if sheet.core else f" Modul {sheet.module} tidak tersedia."),
                            blocking=sheet.core))
        return None, SheetReport(sheet.name, True, n_in, 0, 0), issues
    if n_in == 0:
        issues.append(Issue(sev_block, sheet.name, "", "Sheet kosong (tidak ada baris data).", blocking=sheet.core))
        return None, SheetReport(sheet.name, True, 0, 0, 0), issues

    for c in sheet.columns:
        if c.name not in df.columns and (c.level == KPI or (c.level == OPTIONAL and c.feeds)):
            issues.append(Issue("warning" if c.level == KPI else "info", sheet.name, c.name,
                                f"Kolom {c.name} tidak ada, sehingga {c.feeds or 'fitur terkait'} tidak tersedia."))

    bad = pd.Series(False, index=df.index)

    def reject(mask: pd.Series, col: str, msg: str):
        nonlocal bad
        mask = mask.fillna(False)
        if mask.any():
            issues.append(Issue("error", sheet.name, col, f"{msg} Baris ditolak.", rows=_excel_rows(df.index[mask])))
            bad = bad | mask

    for c in sheet.columns:
        if c.name not in df.columns:
            continue
        s = df[c.name]
        required = c.level == REQUIRED

        if c.kind == "text":
            if c.name == "Period" and pd.api.types.is_datetime64_any_dtype(s):
                s = s.dt.strftime("%Y-%m")
            s = s.astype("string").str.strip()
            s = s.mask(s == "", pd.NA)
            df[c.name] = s
            if required:
                reject(s.isna(), c.name, f"Kolom {c.name} kosong.")
            continue

        if c.kind == "date":
            parsed = _to_date(s)
            unparsable = parsed.isna() & s.notna()
            parsed = parsed.dt.normalize()
            df[c.name] = parsed
            if required:
                reject(parsed.isna() & ~unparsable, c.name, f"Kolom {c.name} kosong.")
                reject(unparsable, c.name, f"Kolom {c.name} bukan tanggal valid.")
            reject(parsed > today_ts, c.name, f"Tanggal di {c.name} berada di masa depan.")
            reject(parsed.dt.year < MIN_VALID_YEAR, c.name, f"Tanggal di {c.name} tidak wajar (sebelum tahun {MIN_VALID_YEAR}).")
            continue

        # number / int
        orig_null = s.isna()
        n = pd.to_numeric(s, errors="coerce")
        unparsable = n.isna() & ~orig_null
        df[c.name] = n
        if required:
            reject(orig_null, c.name, f"Kolom {c.name} kosong.")
            reject(unparsable, c.name, f"Kolom {c.name} bukan angka (periksa format angka, mis. titik/koma ribuan).")
        elif unparsable.any():
            issues.append(Issue("warning", sheet.name, c.name,
                                f"Nilai {c.name} yang bukan angka diperlakukan sebagai kosong.",
                                rows=_excel_rows(df.index[unparsable])))
        if c.min is not None:
            reject(n < c.min, c.name, f"Nilai {c.name} kurang dari {c.min:g}.")
        if c.max is not None:
            reject(n > c.max, c.name, f"Nilai {c.name} lebih dari {c.max:g}.")
        if c.kind == "int":
            reject(n.notna() & (n != n.round()), c.name, f"Nilai {c.name} harus bilangan bulat.")

    if sheet.name == "Production":
        if {"Output_Kg", "Input_Kg"} <= set(df.columns):
            reject(df["Output_Kg"] > df["Input_Kg"], "Output_Kg", "Output_Kg melebihi Input_Kg.")
        if {"Downtime_Min", "Planned_Time_Min"} <= set(df.columns):
            reject(df["Downtime_Min"] > df["Planned_Time_Min"], "Downtime_Min", "Downtime_Min melebihi Planned_Time_Min.")
        keys = [k for k in ("Date", "Plant", "Line", "Machine", "Product") if k in df.columns]
        dup = df.duplicated(subset=keys, keep="first") & ~bad
        reject(dup, ", ".join(keys), "Baris duplikat (kombinasi " + "/".join(keys) + " sudah ada).")

    clean = df.loc[~bad].reset_index(drop=True)
    report = SheetReport(sheet.name, True, n_in, len(clean), int(bad.sum()))
    if len(clean) == 0:
        issues.append(Issue(sev_block, sheet.name, "", "Tidak ada baris valid yang tersisa.", blocking=sheet.core))
        return None, report, issues
    return clean, report, issues
