"""Recommendation Engine — saran aksi konkret dengan impact Rp (BRD 8).

Mengubah alert menjadi rekomendasi bertindak:
  * Prioritas berdasarkan dampak Rp
  * Langkah-langkah konkret (bukan saran umum)
  * Estimasi hemat tahunan / cash recovery
  * Tingkat keyakinan (confidence 0-100%)
  * Sumber data pendukung untuk audit trail
"""
from dataclasses import dataclass
from typing import List, Optional

from ..config import Targets
from .alert_impact import AlertImpact, compute_alerts
from .predictive import predict_slow_moving, predict_stockout

# ==================== KONSTANTA ====================

# Asumsi harga material rata-rata (Rp/Kg) — dipakai saat detail tidak tersedia
DEFAULT_MATERIAL_PRICE = 15_000

# Estimasi downtime stock-out (hari) — konservatif untuk pabrik menengah
ASSUMED_STOCKOUT_DOWNTIME_DAYS = 2

# Margin kotor yang hilang saat produksi terhenti (20%)
LOST_MARGIN_PCT = 0.20

# Recovery rate likuidasi dead stock (70% dari nilai buku)
DEAD_STOCK_RECOVERY_PCT = 0.70


# ==================== DATACLASS ====================

@dataclass
class Recommendation:
    priority: int                 # 1 = paling tinggi (di-reindex setelah sort)
    severity: str                 # high | medium | info
    title: str
    context: str
    steps: List[str]
    monthly_rp: float
    annual_rp: float
    confidence_pct: int           # 0-100
    category: str                 # yield | scrap | oee | cost | inventory
    data_source: str = ""

    @property
    def is_one_time(self) -> bool:
        """True kalau cash recovery (bukan hemat rutin)."""
        return self.annual_rp == 0 and self.monthly_rp > 0


# ==================== HELPER ====================

def _confidence_from_data(prod_rows: int, has_alert: bool = True) -> int:
    """Confidence berdasarkan jumlah data historis."""
    base = 50
    if prod_rows > 500:
        base += 30
    elif prod_rows > 200:
        base += 20
    elif prod_rows > 50:
        base += 10
    if has_alert:
        base += 5
    return min(base, 95)


def _kpi_value(kpi) -> float:
    """Ambil value KPI, return 0 kalau tidak tersedia."""
    return float(kpi.value) if kpi and kpi.available else 0.0


# ==================== REKOMENDASI PER KATEGORI ====================

def _rec_yield(alert: AlertImpact, summary, prod_rows: int, targets) -> Optional[Recommendation]:
    if "Yield" not in alert.title:
        return None

    y_val = _kpi_value(summary.yield_pct)
    target = targets.yield_min            # <-- dari Settings
    gap = target - y_val

    return Recommendation(
        priority=1,
        severity="high",
        title=f"Naikkan Yield dari {y_val:.2f}% ke target {target:.1f}%",
        context=(
            f"Yield saat ini {y_val:.2f}% — gap {gap:.2f} poin persentase. "
            f"Setiap 1 poin yield = hemat material signifikan."
        ),
        steps=[
            "Audit kalibrasi 3 mesin dengan yield terendah",
            f"Perketat QC input material (target Yield ≥ {target:.1f}%)",
            "Review SOP operator shift 2 & 3",
            "Jadwalkan preventive maintenance bulanan untuk semua mesin",
        ],
        monthly_rp=alert.monthly_rp,
        annual_rp=alert.annual_rp,
        confidence_pct=_confidence_from_data(prod_rows, has_alert=True),
        category="yield",
        data_source="Sheet Production → kolom Output_Kg & Input_Kg",
    )


def _rec_scrap(alert: AlertImpact, summary, prod_rows: int, targets) -> Optional[Recommendation]:
    if "Scrap" not in alert.title:
        return None

    s_val = _kpi_value(summary.scrap_pct)
    target = targets.scrap_max            # <-- dari Settings
    excess = s_val - target

    return Recommendation(
        priority=2,
        severity="high",
        title=f"Turunkan Scrap dari {s_val:.2f}% ke target {target:.1f}%",
        context=(
            f"Scrap {s_val:.2f}% di atas batas {target:.1f}%. "
            f"Kelebihan {excess:.2f} poin = pemborosan material."
        ),
        steps=[
            "Identifikasi 3 mesin dengan scrap tertinggi (lihat Production Analysis)",
            "Ganti nozzle/dies yang aus (rutin tiap 4 minggu)",
            "Review setting suhu & tekanan proses",
            "Pelatihan operator handling material",
        ],
        monthly_rp=alert.monthly_rp,
        annual_rp=alert.annual_rp,
        confidence_pct=_confidence_from_data(prod_rows, has_alert=True),
        category="scrap",
        data_source="Sheet Production → kolom Scrap_Kg & Input_Kg",
    )


def _rec_oee(alert: AlertImpact, summary, prod_rows: int, targets) -> Optional[Recommendation]:
    if "OEE" not in alert.title:
        return None

    o_val = _kpi_value(summary.oee.oee)
    target = targets.oee_min              # <-- dari Settings
    gap = target - o_val

    return Recommendation(
        priority=3,
        severity="medium",
        title=f"Naikkan OEE dari {o_val:.2f}% ke target {target:.1f}%",
        context=(
            f"OEE {o_val:.2f}% — gap {gap:.2f} poin. "
            f"OEE rendah = fixed cost per unit naik."
        ),
        steps=[
            "Analisis downtime per mesin — identifikasi 3 penyebab utama",
            "Percepat preventive maintenance (3 bulan → 2 bulan)",
            "Tambah buffer stock untuk sparepart kritis",
            "Implementasi quick changeover untuk setup lebih cepat",
        ],
        monthly_rp=alert.monthly_rp,
        annual_rp=alert.annual_rp,
        confidence_pct=max(60, _confidence_from_data(prod_rows) - 10),
        category="oee",
        data_source="Sheet Production → Planned_Time_Min, Downtime_Min, Ideal_Rate",
    )

def _rec_cost(alert: AlertImpact, summary, prod_rows: int) -> Optional[Recommendation]:
    if "Cost/Kg" not in alert.title:
        return None

    return Recommendation(
        priority=2,
        severity="high",
        title="Turunkan Cost/Kg dengan review supplier",
        context=alert.message,
        steps=[
            "Review 3 supplier material terbesar — negosiasi harga",
            "Cari supplier alternatif lokal (potensi hemat 5-10%)",
            "Evaluasi spesifikasi material — ada yang bisa disubstitusi?",
            "Konsolidasi pembelian (bulk discount)",
        ],
        monthly_rp=alert.monthly_rp,
        annual_rp=alert.annual_rp,
        confidence_pct=70,
        category="cost",
        data_source="Sheet Raw_Material + Budget",
    )


def _rec_utility(alert: AlertImpact, summary, prod_rows: int) -> Optional[Recommendation]:
    if "utilitas" not in alert.title.lower():
        return None

    return Recommendation(
        priority=4,
        severity="info",
        title="Optimalkan biaya utilitas",
        context=alert.message,
        steps=[
            "Audit konsumsi listrik per line — cek kebocoran",
            "Jadwalkan beban produksi di jam off-peak (jika tarif berbeda)",
            "Review efisiensi mesin utama (motor, kompresor)",
        ],
        monthly_rp=alert.monthly_rp,
        annual_rp=alert.annual_rp,
        confidence_pct=65,
        category="cost",
        data_source="Sheet Utility → Electricity_Cost",
    )


# ==================== REKOMENDASI DARI INVENTORY ====================

def _rec_stockout_risk(r) -> Recommendation:
    """Buat rekomendasi dari StockOutRisk.

    Estimasi kerugian = output harian × hari downtime × margin kotor hilang.
    Bukan nilai pembelian material (yang akan di-restock tetap).
    """
    urgency_icon = "🔴 Kritis" if r.status == "critical" else "🟡 Peringatan"

    # Estimasi kerugian: jika stock-out, produksi terhenti
    output_per_day = r.daily_usage          # aproksimasi: konsumsi = output
    lost_margin_per_day = output_per_day * DEFAULT_MATERIAL_PRICE * LOST_MARGIN_PCT
    monthly_rp = lost_margin_per_day * ASSUMED_STOCKOUT_DOWNTIME_DAYS

    return Recommendation(
        priority=1 if r.status == "critical" else 3,
        severity="high" if r.status == "critical" else "medium",
        title=f"{urgency_icon} — {r.material} tersisa {r.days_until_empty:.0f} hari",
        context=(
            f"Stok {r.stock_kg:,.0f} Kg, usage {r.monthly_usage:,.0f} Kg/bulan. "
            f"Jika habis, produksi terhenti ~{ASSUMED_STOCKOUT_DOWNTIME_DAYS} hari."
        ),
        steps=[
            f"Hubungi supplier {r.material} — cek lead time terkini",
            f"Percepat PO untuk {r.material} (prioritas)",
            "Siapkan buffer stock minimal 30 hari pemakaian",
            "Cek alternatif supplier cadangan",
        ],
        monthly_rp=monthly_rp,
        annual_rp=monthly_rp * 12,
        confidence_pct=80,
        category="inventory",
        data_source="Sheet Inventory → Stock_Kg & Monthly_Usage",
    )


def _rec_dead_stock(s, stock_kg: float) -> Recommendation:
    """Buat rekomendasi likuidasi dead stock."""
    recovery_rp = stock_kg * DEFAULT_MATERIAL_PRICE * DEAD_STOCK_RECOVERY_PCT

    return Recommendation(
        priority=4,
        severity="info",
        title=f"Likuidasi dead stock: {s.material}",
        context=(
            f"Stok {stock_kg:,.0f} Kg menganggur, tidak ada pemakaian. "
            f"Potensi cash recovery Rp {recovery_rp:,.0f}."
        ),
        steps=[
            f"Hitung ulang valuasi stok {s.material}",
            "Cari pembeli / realokasi ke line lain",
            "Jika tidak laku 30 hari → scrap / liquidate",
        ],
        monthly_rp=recovery_rp,
        annual_rp=0,  # one-time cash recovery
        confidence_pct=75,
        category="inventory",
        data_source="Sheet Inventory → usage = 0",
    )


def _recs_inventory(ds) -> List[Recommendation]:
    """Kumpulkan semua rekomendasi dari data inventory."""
    if ds.inventory is None or ds.inventory.empty:
        return []

    results: List[Recommendation] = []

    # --- Stock-out risk ---
    for r in predict_stockout(ds.inventory):
        if r.status not in ("critical", "warning"):
            continue
        if r.days_until_empty is None or r.days_until_empty > 30:
            continue
        results.append(_rec_stockout_risk(r))
        if len(results) >= 3:  # max 3 stock-out
            break

    # --- Dead stock ---
    dead_count = 0
    for s in predict_slow_moving(ds.inventory):
        if s.risk_level != "dead_stock":
            continue
        try:
            row = ds.inventory[ds.inventory["Material"] == s.material].iloc[0]
            stock = float(row["Stock_Kg"])
        except Exception:
            stock = 0.0
        if stock <= 0:
            continue
        results.append(_rec_dead_stock(s, stock))
        dead_count += 1
        if dead_count >= 2:  # max 2 dead stock
            break

    return results


# ==================== ENTRY POINT ====================

# Urutan fungsi generator — dipanggil sampai ada yang match
_ALERT_GENERATORS = (_rec_yield, _rec_scrap, _rec_oee, _rec_cost, _rec_utility)


def generate_recommendations(ds, summary, targets: Targets) -> List[Recommendation]:
    """Hasilkan semua rekomendasi, diurutkan prioritas & dampak Rp."""
    recs: List[Recommendation] = []

    # 1. Dari alert KPI — pass targets ke generator
    for alert in compute_alerts(summary, targets):
        for gen in _ALERT_GENERATORS:
            rec = gen(alert, summary, summary.production_rows, targets)
            if rec is not None:
                recs.append(rec)
                break

    # 2. Dari inventory
    recs.extend(_recs_inventory(ds))

    # 3. Sort
    recs.sort(key=lambda r: (r.priority, -abs(r.annual_rp or r.monthly_rp)))

    # 4. Re-index
    for i, rec in enumerate(recs, 1):
        rec.priority = i

    return recs