"""Auto-Narrative Report Engine — generate narasi dari data (BRD 8).

Menghasilkan teks Bahasa Indonesia natural dari KPI, alert, dan tren.
Tanpa LLM — berbasis template + rule-based logic.

Output:
  - Ringkasan Eksekutif (paragraf)
  - Poin Pencapaian, Perhatian, Kritis
  - Rekomendasi prioritas
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from ..config import Targets
from .alert_impact import compute_alerts
from .recommend import generate_recommendations
from .period_compare import available_periods, compare_periods


# ==================== THRESHOLD KONFIGURASI ====================
# Ubah angka di sini untuk mengatur sensitivitas kategori "Kritis".
# Semakin KECIL angkanya, semakin SENSITIF (semakin mudah masuk Kritis).

CRITICAL_THRESHOLDS = {
    "yield_gap_pp": 0.3,      # Gap Yield ≥ 0.3 pp → Kritis (default lama: 1.0)
    "scrap_excess_pp": 0.15,  # Kelebihan Scrap ≥ 0.15 pp → Kritis (default lama: 1.0)
    "oee_gap_pp": 0.5,        # Gap OEE ≥ 0.5 pp → Kritis (default lama: 3.0)
}


@dataclass
class NarrativeSection:
    title: str
    icon: str
    items: List[str] = field(default_factory=list)


@dataclass
class NarrativeReport:
    headline: str
    executive_summary: str
    achievements: NarrativeSection
    warnings: NarrativeSection
    criticals: NarrativeSection
    recommendations: NarrativeSection
    closing: str


# ==================== HELPER ====================

def _fmt_rp(v: float) -> str:
    """Format Rupiah ringkas: Rp 4,63 M / Rp 174,2 jt / Rp 12.005."""
    if abs(v) >= 1_000_000_000:
        return f"Rp {v / 1_000_000_000:.2f} M"
    if abs(v) >= 1_000_000:
        return f"Rp {v / 1_000_000:.1f} jt"
    return f"Rp {v:,.0f}"


def _kpi_status(yield_v, scrap_v, oee_v, targets: Targets) -> dict:
    """Tentukan status setiap KPI."""
    return {
        "yield": "ok" if yield_v and yield_v >= targets.yield_min else "below",
        "scrap": "ok" if scrap_v and scrap_v <= targets.scrap_max else "above",
        "oee": "ok" if oee_v and oee_v >= targets.oee_min else "below",
    }


# ==================== NARRATIVE ENGINE ====================

def _build_headline(s, targets: Targets) -> str:
    """Kalimat pembuka — status keseluruhan."""
    score = s.score.score if s.score.score is not None else 0

    if score >= 90:
        return "✅ Kinerja pabrik dalam kondisi **excellent**. Semua KPI utama di atas target."
    elif score >= 80:
        return "🟢 Kinerja pabrik **baik**. Ada beberapa area minor yang bisa dioptimalkan."
    elif score >= 70:
        return "🟡 Kinerja pabrik **perlu perbaikan**. Beberapa KPI utama di bawah target."
    else:
        return "🔴 Kinerja pabrik **kritis**. Perlu tindakan segera pada beberapa area."


def _build_executive_summary(s, targets: Targets, n_alerts: int) -> str:
    """Paragraf ringkasan eksekutif 3-5 kalimat."""
    parts = []

    if s.output_kg.available and s.cogm.available:
        output = s.output_kg.value
        cogm = s.cogm.value
        cpk = s.cost_per_kg.value if s.cost_per_kg.available else 0
        parts.append(
            f"Bulan ini pabrik memproduksi **{output:,.0f} Kg** output baik "
            f"dengan total COGM **{_fmt_rp(cogm)}** "
            f"(Cost/Kg **{_fmt_rp(cpk)}**)."
        )

    status = _kpi_status(
        s.yield_pct.value if s.yield_pct.available else None,
        s.scrap_pct.value if s.scrap_pct.available else None,
        s.oee.oee.value if s.oee.oee.available else None,
        targets,
    )
    issues = []
    if status["yield"] == "below":
        issues.append("Yield di bawah target")
    if status["scrap"] == "above":
        issues.append("Scrap melewati batas")
    if status["oee"] == "below":
        issues.append("OEE di bawah target")

    if issues:
        parts.append(f"Namun {'; '.join(issues).lower()}.")
    else:
        parts.append("Semua KPI operasional utama berhasil mencapai target.")

    if n_alerts > 0:
        parts.append(
            f"Terdapat **{n_alerts} peringatan aktif** yang membutuhkan perhatian manajemen."
        )
    else:
        parts.append("Tidak ada peringatan aktif — operasional berjalan stabil.")

    if s.score.score is not None:
        parts.append(f"Controller Score: **{s.score.score}/100** ({s.score.category}).")

    return " ".join(parts)


def _build_achievements(s, targets: Targets) -> NarrativeSection:
    """Poin pencapaian."""
    sec = NarrativeSection(title="Pencapaian", icon="🟢")

    if s.output_kg.available:
        sec.items.append(f"Output stabil di {s.output_kg.value:,.0f} Kg")

    if s.yield_pct.available and s.yield_pct.value >= targets.yield_min:
        sec.items.append(f"Yield {s.yield_pct.value:.2f}% mencapai target {targets.yield_min:g}%")

    if s.scrap_pct.available and s.scrap_pct.value <= targets.scrap_max:
        sec.items.append(f"Scrap {s.scrap_pct.value:.2f}% dalam batas {targets.scrap_max:g}%")

    if s.oee.oee.available and s.oee.oee.value >= targets.oee_min:
        sec.items.append(f"OEE {s.oee.oee.value:.2f}% mencapai target {targets.oee_min:g}%")

    if s.cost_per_kg.available and targets.max_cost_per_kg > 0:
        if s.cost_per_kg.value <= targets.max_cost_per_kg:
            sec.items.append(
                f"Cost/Kg {_fmt_rp(s.cost_per_kg.value)} dalam batas "
                f"{_fmt_rp(targets.max_cost_per_kg)}"
            )

    if not sec.items:
        sec.items.append("Belum ada pencapaian signifikan bulan ini.")

    return sec


def _build_warnings(s, targets: Targets) -> NarrativeSection:
    """Poin perhatian (tidak kritis) — gap di bawah threshold Kritis."""
    sec = NarrativeSection(title="Perhatian", icon="🟡")

    thr_yield = CRITICAL_THRESHOLDS["yield_gap_pp"]
    thr_scrap = CRITICAL_THRESHOLDS["scrap_excess_pp"]

    # Yield: masuk warning kalau gap di bawah threshold kritis
    if s.yield_pct.available and s.yield_pct.value < targets.yield_min:
        gap = targets.yield_min - s.yield_pct.value
        if gap < thr_yield:
            sec.items.append(
                f"Yield {s.yield_pct.value:.2f}% — gap {gap:.2f} pp dari target"
            )

    # Scrap: masuk warning kalau excess di bawah threshold kritis
    if s.scrap_pct.available and s.scrap_pct.value > targets.scrap_max:
        excess = s.scrap_pct.value - targets.scrap_max
        if excess < thr_scrap:
            sec.items.append(
                f"Scrap {s.scrap_pct.value:.2f}% — kelebihan {excess:.2f} pp"
            )

    # Cost/Kg mendekati batas
    if s.cost_per_kg.available and targets.max_cost_per_kg > 0:
        cpk = s.cost_per_kg.value
        if targets.max_cost_per_kg * 0.9 <= cpk <= targets.max_cost_per_kg:
            sec.items.append(
                f"Cost/Kg {_fmt_rp(cpk)} mendekati batas {_fmt_rp(targets.max_cost_per_kg)}"
            )

    if not sec.items:
        sec.items.append("Tidak ada perhatian khusus bulan ini.")

    return sec


def _build_criticals(s, targets: Targets) -> NarrativeSection:
    """Poin kritis (butuh tindakan segera).

    Threshold diambil dari CRITICAL_THRESHOLDS (bisa di-tune).
    """
    sec = NarrativeSection(title="Kritis", icon="🔴")

    thr_yield = CRITICAL_THRESHOLDS["yield_gap_pp"]
    thr_scrap = CRITICAL_THRESHOLDS["scrap_excess_pp"]
    thr_oee = CRITICAL_THRESHOLDS["oee_gap_pp"]

    # Yield
    if s.yield_pct.available and s.yield_pct.value < targets.yield_min:
        gap = targets.yield_min - s.yield_pct.value
        if gap >= thr_yield:
            sec.items.append(
                f"Yield {s.yield_pct.value:.2f}% — gap {gap:.2f} pp dari target "
                f"(threshold {thr_yield:.2f} pp)"
            )

    # Scrap
    if s.scrap_pct.available and s.scrap_pct.value > targets.scrap_max:
        excess = s.scrap_pct.value - targets.scrap_max
        if excess >= thr_scrap:
            sec.items.append(
                f"Scrap {s.scrap_pct.value:.2f}% — kelebihan {excess:.2f} pp "
                f"(threshold {thr_scrap:.2f} pp)"
            )

    # OEE
    if s.oee.oee.available and s.oee.oee.value < targets.oee_min:
        gap = targets.oee_min - s.oee.oee.value
        if gap >= thr_oee:
            sec.items.append(
                f"OEE {s.oee.oee.value:.2f}% — gap {gap:.2f} pp "
                f"(threshold {thr_oee:.2f} pp)"
            )

    # Cost/Kg lewat batas
    if s.cost_per_kg.available and targets.max_cost_per_kg > 0:
        if s.cost_per_kg.value > targets.max_cost_per_kg:
            sec.items.append(
                f"Cost/Kg {_fmt_rp(s.cost_per_kg.value)} — "
                f"melewati batas {_fmt_rp(targets.max_cost_per_kg)}"
            )

    if not sec.items:
        sec.items.append("Tidak ada masalah kritis. ✅")

    return sec


def _build_recommendations_section(ds, s, targets: Targets) -> NarrativeSection:
    """Poin rekomendasi aksi — ambil top 3."""
    sec = NarrativeSection(title="Rekomendasi Aksi Prioritas", icon="💡")

    try:
        recs = generate_recommendations(ds, s, targets)
    except Exception:
        recs = []

    if not recs:
        sec.items.append("Tidak ada rekomendasi saat ini.")
        return sec

    for i, r in enumerate(recs[:3], 1):
        impact = _fmt_rp(r.annual_rp) if r.annual_rp > 0 else _fmt_rp(r.monthly_rp)
        suffix = "/tahun" if r.annual_rp > 0 else " (one-time)"
        sec.items.append(f"{r.title} → hemat {impact}{suffix}")

    return sec


def _build_closing(s, targets: Targets, n_alerts: int) -> str:
    """Kalimat penutup."""
    if n_alerts == 0:
        return (
            "Secara keseluruhan, operasional pabrik berjalan sesuai target. "
            "Pertahankan konsistensi dan lanjutkan monitoring rutin."
        )

    total_impact = 0
    if s.cogm.available:
        total_impact = s.cogm.value * 0.02

    return (
        f"Dengan mengeksekusi rekomendasi prioritas di atas, "
        f"potensi penghematan dapat mencapai **{_fmt_rp(total_impact)}/tahun**. "
        f"Rekomendasi sudah diperingkat berdasarkan dampak finansial — "
        f"fokus pada 2-3 aksi teratas untuk hasil maksimal."
    )


# ==================== MAIN FUNCTION ====================

def generate_narrative(ds, summary, targets: Targets) -> NarrativeReport:
    """Generate laporan naratif lengkap."""
    try:
        alerts = compute_alerts(summary, targets)
    except Exception:
        alerts = []

    return NarrativeReport(
        headline=_build_headline(summary, targets),
        executive_summary=_build_executive_summary(summary, targets, len(alerts)),
        achievements=_build_achievements(summary, targets),
        warnings=_build_warnings(summary, targets),
        criticals=_build_criticals(summary, targets),
        recommendations=_build_recommendations_section(ds, summary, targets),
        closing=_build_closing(summary, targets, len(alerts)),
    )