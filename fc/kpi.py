"""Mesin KPI - rumus resmi BRD bagian 6.

Aturan utama:
  * Fungsi murni (input DataFrame -> hasil), tanpa Streamlit, mudah diuji.
  * KPI yang tidak bisa dihitung berstatus 'unavailable' dengan alasan jelas;
    TIDAK PERNAH 0 atau angka tebakan.
  * Biaya dan produksi dihitung pada cakupan (plant/line/periode) yang sama; bila
    data biaya tidak punya dimensi yang dibutuhkan, Cost/Kg dinyatakan tidak tersedia
    (BRD 5.5 - konsistensi filter).
"""
from dataclasses import dataclass, field
from datetime import date
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from .config import SCORE_BANDS, SCORE_PENALTY, TARGETS
from .pipeline import Dataset
from .schema import COST_SHEETS

CATEGORIES = [c for _, _, c in COST_SHEETS]


# ---------- tipe hasil ----------
@dataclass(frozen=True)
class KPI:
    value: Optional[float] = None
    status: str = "unavailable"      # ok | estimate | unavailable
    note: str = ""

    @property
    def available(self) -> bool:
        return self.value is not None


def _ok(v: float, note: str = "") -> KPI:
    return KPI(float(v), "ok", note)


def _est(v: float, note: str) -> KPI:
    return KPI(float(v), "estimate", note)


def _na(note: str) -> KPI:
    return KPI(None, "unavailable", note)


@dataclass(frozen=True)
class Scope:
    plant: Optional[str] = None
    line: Optional[str] = None
    start: Optional[date] = None
    end: Optional[date] = None


@dataclass(frozen=True)
class OEEResult:
    oee: KPI
    availability: KPI
    performance: KPI
    quality: KPI


@dataclass(frozen=True)
class ScoreResult:
    score: Optional[int]
    category: str
    reasons: Tuple[str, ...] = ()
    note: str = ""


@dataclass
class Summary:
    output_kg: KPI
    cogm: KPI
    breakdown: Dict[str, float]
    cost_per_kg: KPI
    yield_pct: KPI
    scrap_pct: KPI
    oee: OEEResult
    score: ScoreResult
    alerts: List[str] = field(default_factory=list)
    production_rows: int = 0


# ---------- cakupan ----------
def scope_production(prod: pd.DataFrame, scope: Scope) -> pd.DataFrame:
    p = prod
    if scope.plant and "Plant" in p.columns:
        p = p[p["Plant"].eq(scope.plant).fillna(False)]
    if scope.line:
        p = p[p["Line"].eq(scope.line).fillna(False)]
    if scope.start:
        p = p[p["Date"] >= pd.Timestamp(scope.start)]
    if scope.end:
        p = p[p["Date"] <= pd.Timestamp(scope.end)]
    return p


def period_filtered(prod_full: pd.DataFrame, scope: Scope) -> bool:
    if not scope.start and not scope.end:
        return False
    lo, hi = prod_full["Date"].min().date(), prod_full["Date"].max().date()
    return bool((scope.start and scope.start > lo) or (scope.end and scope.end < hi))


# ---------- biaya ----------
def cogm_for_scope(costs: pd.DataFrame, prod_full: pd.DataFrame, scope: Scope,
                   wip_begin: float = 0.0, wip_end: float = 0.0) -> Tuple[KPI, Dict[str, float]]:
    """COGM = Material + Kemasan + Tenaga Kerja + Utilitas + Pemeliharaan + Penyusutan
    (+ WIP awal - WIP akhir bila tersedia)."""
    notes: List[str] = []
    c = costs
    if scope.line:
        return _na("Biaya tidak dapat dipisahkan per Line (data biaya belum memiliki dimensi Line)."), {}
    if scope.plant:
        if c["Plant"].isna().all():
            return _na("Biaya per Plant tidak tersedia: sheet biaya belum memiliki kolom Plant."), {}
        unalloc = int(c["Plant"].isna().sum())
        c = c[c["Plant"].eq(scope.plant).fillna(False)]
        if unalloc:
            notes.append(f"{unalloc} baris biaya tanpa Plant tidak dihitung.")
    if period_filtered(prod_full, scope):
        if c["Period"].isna().all():
            return _na("Biaya per periode tidak tersedia: sheet biaya belum memiliki kolom Period (YYYY-MM)."), {}
        lo = (scope.start or prod_full["Date"].min().date()).strftime("%Y-%m")
        hi = (scope.end or prod_full["Date"].max().date()).strftime("%Y-%m")
        c = c[(c["Period"] >= lo) & (c["Period"] <= hi)]
        notes.append("Biaya dialokasikan per bulan penuh.")
    if c.empty:
        return _na("Tidak ada data biaya untuk filter terpilih."), {}
    by_cat = c.groupby("Category")["Cost"].sum()
    breakdown = {cat: float(by_cat.get(cat, 0.0)) for cat in CATEGORIES}
    total = sum(breakdown.values()) + wip_begin - wip_end
    return _ok(total, " ".join(notes)), breakdown


def cost_per_kg(cogm: KPI, output_kg: float) -> KPI:
    if not cogm.available:
        return _na(cogm.note)
    if output_kg <= 0:
        return _na("Output produksi 0 Kg pada filter terpilih.")
    return _ok(cogm.value / output_kg, cogm.note)


# ---------- yield, scrap, OEE ----------
def yield_kpi(prod: pd.DataFrame) -> KPI:
    """Yield = Output baik / Input bahan baku x 100%."""
    if "Input_Kg" not in prod.columns:
        return _na("Kolom Input_Kg tidak ada pada sheet Production.")
    m = prod["Input_Kg"].notna()
    if not m.any():
        return _na("Input_Kg kosong pada filter terpilih.")
    inp = float(prod.loc[m, "Input_Kg"].sum())
    out = float(prod.loc[m, "Output_Kg"].sum())
    if inp <= 0:
        return _na("Total Input_Kg 0.")
    note = f"{int((~m).sum())} baris tanpa Input_Kg tidak dihitung." if (~m).any() else ""
    return _ok(out / inp * 100, note)


def scrap_kpi(prod: pd.DataFrame, yield_k: KPI) -> KPI:
    """Scrap = Scrap_Kg / Input x 100%; bila Scrap_Kg tidak ada: 100% - Yield (estimasi)."""
    if {"Scrap_Kg", "Input_Kg"} <= set(prod.columns):
        m = prod["Scrap_Kg"].notna() & prod["Input_Kg"].notna()
        if m.any():
            inp = float(prod.loc[m, "Input_Kg"].sum())
            if inp > 0:
                return _ok(float(prod.loc[m, "Scrap_Kg"].sum()) / inp * 100)
    if yield_k.available:
        return _est(max(0.0, 100.0 - yield_k.value),
                    "Estimasi = 100% - Yield (Scrap_Kg tidak tersedia); mencakup semua loss, bukan hanya scrap.")
    return _na("Scrap tidak dapat dihitung: butuh kolom Scrap_Kg dan Input_Kg, atau Input_Kg untuk estimasi.")


def oee_kpi(prod: pd.DataFrame) -> OEEResult:
    """OEE = Availability x Performance x Quality (dihitung dari total, bukan rata-rata rasio).
    Availability = (Planned - Downtime) / Planned
    Performance  = Output total / (Run time x Ideal rate)
    Quality      = Output baik / Output total   (Output total = Output baik + Scrap)"""
    need = ["Planned_Time_Min", "Downtime_Min", "Ideal_Rate_Kg_per_Min", "Scrap_Kg", "Output_Kg"]
    missing = [c for c in need if c not in prod.columns]
    if missing:
        na = _na(f"OEE tidak tersedia: kolom {', '.join(missing)} tidak ada pada sheet Production.")
        return OEEResult(na, na, na, na)
    d = prod.dropna(subset=need)
    if d.empty:
        na = _na("OEE tidak tersedia: data waktu/scrap kosong pada filter terpilih.")
        return OEEResult(na, na, na, na)
    planned = float(d["Planned_Time_Min"].sum())
    run = d["Planned_Time_Min"] - d["Downtime_Min"]
    ideal_out = float((run * d["Ideal_Rate_Kg_per_Min"]).sum())
    out_good = float(d["Output_Kg"].sum())
    out_total = out_good + float(d["Scrap_Kg"].sum())
    if planned <= 0 or ideal_out <= 0 or out_total <= 0:
        na = _na("OEE tidak dapat dihitung: Planned Time, Ideal Rate, atau Output bernilai 0.")
        return OEEResult(na, na, na, na)
    a, p, q = float(run.sum()) / planned, out_total / ideal_out, out_good / out_total
    dropped = len(prod) - len(d)
    note = f"{dropped} baris dengan data tidak lengkap tidak dihitung." if dropped else ""
    pnote = (note + " " if note else "") + ("Performance > 100%: periksa nilai Ideal_Rate_Kg_per_Min." if p > 1 else "")
    return OEEResult(_ok(a * p * q * 100, pnote.strip()), _ok(a * 100, note),
                     _ok(p * 100, pnote.strip()), _ok(q * 100, note))


# ---------- Controller Score ----------
def controller_score(yield_k: KPI, scrap_k: KPI, oee_k: KPI) -> ScoreResult:
    """Mulai 100; kurangi SCORE_PENALTY untuk tiap KPI di luar target. Bila ada KPI tidak tersedia,
    skor tidak dihitung (tidak ada penilaian parsial yang menyesatkan)."""
    missing = [n for n, k in (("Yield", yield_k), ("Scrap", scrap_k), ("OEE", oee_k)) if not k.available]
    if missing:
        return ScoreResult(None, "Tidak tersedia", (), f"Skor tidak dapat dihitung: {', '.join(missing)} tidak tersedia.")
    score, reasons = 100, []
    if yield_k.value < TARGETS.yield_min:
        score -= SCORE_PENALTY
        reasons.append(f"Yield {yield_k.value:.2f}% di bawah target {TARGETS.yield_min:g}%")
    if scrap_k.value > TARGETS.scrap_max:
        score -= SCORE_PENALTY
        reasons.append(f"Scrap {scrap_k.value:.2f}% di atas batas {TARGETS.scrap_max:g}%")
    if oee_k.value < TARGETS.oee_min:
        score -= SCORE_PENALTY
        reasons.append(f"OEE {oee_k.value:.2f}% di bawah target {TARGETS.oee_min:g}%")
    category = next(name for threshold, name in SCORE_BANDS if score >= threshold)
    note = "Berisi KPI estimasi." if "estimate" in (yield_k.status, scrap_k.status, oee_k.status) else ""
    return ScoreResult(score, category, tuple(reasons), note)


# ---------- ringkasan dashboard ----------
def summarize(ds: Dataset, scope: Scope) -> Summary:
    prod = scope_production(ds.production, scope)
    output = float(prod["Output_Kg"].sum()) if len(prod) else 0.0
    out_kpi = _ok(output) if len(prod) else _na("Tidak ada data produksi pada filter terpilih.")
    cogm, breakdown = cogm_for_scope(ds.costs, ds.production, scope)
    cpk = cost_per_kg(cogm, output) if len(prod) else _na("Tidak ada data produksi pada filter terpilih.")
    if len(prod):
        y = yield_kpi(prod)
        s = scrap_kpi(prod, y)
        o = oee_kpi(prod)
    else:
        n = _na("Tidak ada data produksi pada filter terpilih.")
        y, s, o = n, n, OEEResult(n, n, n, n)
    score = controller_score(y, s, o.oee)
    return Summary(out_kpi, cogm, breakdown, cpk, y, s, o, score,
                   build_alerts(y, s, o.oee, cogm, breakdown), len(prod))


def build_alerts(y: KPI, s: KPI, o: KPI, cogm: KPI, breakdown: Dict[str, float]) -> List[str]:
    alerts = []
    if y.available and y.value < TARGETS.yield_min:
        alerts.append(f"Yield {y.value:.2f}% di bawah target {TARGETS.yield_min:g}%.")
    if s.available and s.value > TARGETS.scrap_max:
        alerts.append(f"Scrap {s.value:.2f}% melewati batas {TARGETS.scrap_max:g}%.")
    if o.available and o.value < TARGETS.oee_min:
        alerts.append(f"OEE {o.value:.2f}% di bawah target {TARGETS.oee_min:g}%.")
    if cogm.available and cogm.value > 0 and breakdown:
        share = breakdown.get("Utility", 0.0) / cogm.value * 100
        if share > TARGETS.utility_share_max:
            alerts.append(f"Biaya utilitas {share:.1f}% dari COGM, melewati batas {TARGETS.utility_share_max:g}%.")
    return alerts


# ---------- modul lain ----------
def variance_table(budget: pd.DataFrame) -> pd.DataFrame:
    """Variance = Actual - Budget; Utilization = Actual / Budget x 100%."""
    t = budget.copy()
    t["Variance"] = t["Actual"] - t["Budget"]
    b = t["Budget"].replace(0, np.nan)
    t["Variance_Pct"] = t["Variance"] / b * 100
    t["Utilization_Pct"] = t["Actual"] / b * 100
    tol = TARGETS.variance_tolerance_pct
    t["Status"] = np.select([t["Variance_Pct"] > tol, t["Variance_Pct"] < -tol], ["Over Budget", "Under Budget"], "On Budget")
    return t


def inventory_table(inv: pd.DataFrame) -> pd.DataFrame:
    """Days Inventory = Stock_Kg / (Monthly_Usage / 30). Pemakaian 0 dengan stok > 0 = Dead Stock."""
    t = inv.copy()
    daily = t["Monthly_Usage"] / 30.0
    t["Days_Inventory"] = np.where(daily > 0, t["Stock_Kg"] / daily.replace(0, np.nan), np.nan)
    dead = (t["Monthly_Usage"] == 0) & (t["Stock_Kg"] > 0)
    slow = t["Days_Inventory"] > TARGETS.slow_moving_days
    t["Status"] = np.select([dead, slow], ["Dead Stock", "Slow Moving"], "Normal")
    return t


def risk_table(risk: pd.DataFrame) -> pd.DataFrame:
    """Skor risiko = Probability_Val x Impact_Val (1-9). Level: >=6 Tinggi, >=3 Sedang, selain itu Rendah."""
    t = risk.copy()
    t["Score"] = t["Probability_Val"] * t["Impact_Val"]
    t["Level"] = np.select([t["Score"] >= 6, t["Score"] >= 3], ["Tinggi", "Sedang"], "Rendah")
    return t


# ==================== STREAMLIT CACHING WRAPPER ====================
# Setiap halaman panggil summarize() untuk KPI. Tanpa cache, ini dihitung
# ulang setiap ganti menu (30+ detik). Cache bikin instant.

try:
    import streamlit as st

    def _hash_dataset(ds):
        """Hash Dataset berdasarkan label & waktu load."""
        if ds is None:
            return "none"
        try:
            return f"{ds.report.source_label}|{ds.report.loaded_at}"
        except Exception:
            return str(id(ds))

    def _hash_scope(s):
        """Hash Scope berdasarkan filter aktif."""
        if s is None:
            return "none"
        return f"{s.plant}|{s.line}|{s.start}|{s.end}"

    # Simpan versi asli sebelum di-wrap
    _summarize_internal = summarize

    @st.cache_data(show_spinner=False, ttl=3600, hash_funcs={
        Dataset: _hash_dataset,
        Scope: _hash_scope,
    })
    def summarize(ds, scope):  # noqa: F811
        """Versi cached dari summarize()."""
        return _summarize_internal(ds, scope)

except ImportError:
    pass  # Streamlit tidak ada (CLI mode) — pakai versi asli