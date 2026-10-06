"""Institutional Memory Engine — belajar dari keputusan user (BRD 8, Fase 3).

Analisis pola keputusan:
  * Acceptance rate (approve vs reject)
  * Kategori rekomendasi yang paling sering disetujui
  * Total nilai penghematan dari keputusan approved
  * Tren keputusan dari waktu ke waktu
  * Insight & rekomendasi untuk keputusan berikutnya

Tanpa LLM — rule-based + statistical analysis.
"""
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from .. import db


# ==================== DATACLASS ====================

@dataclass
class DecisionStats:
    total: int = 0
    approved: int = 0
    rejected: int = 0
    total_impact_rp: float = 0.0
    top_categories: List[tuple] = field(default_factory=list)  # [(category, count), ...]
    top_keywords: List[tuple] = field(default_factory=list)

    @property
    def acceptance_rate(self) -> float:
        if self.total == 0:
            return 0.0
        return self.approved / self.total * 100


@dataclass
class MemoryInsight:
    title: str
    icon: str
    description: str
    metric: str = ""


# ==================== HELPER ====================

def _parse_impact(notes: str) -> float:
    """Ekstrak angka Rp dari notes keputusan.

    Notes format: 'Impact: Rp 174.240.074/tahun, Confidence: 82%'
    """
    if not notes:
        return 0.0

    import re
    # Cari pola "Rp X" atau "Rp X.XXX.XXX"
    matches = re.findall(r"Rp\s*([\d.,]+)", notes)
    if not matches:
        return 0.0

    # Ambil yang terbesar (biasanya impact tahunan)
    max_val = 0.0
    for m in matches:
        # Bersihkan: hapus titik, ganti koma jadi titik
        clean = m.replace(".", "").replace(",", ".")
        try:
            val = float(clean)
            if val > max_val:
                max_val = val
        except ValueError:
            pass
    return max_val


def _categorize_title(title: str) -> str:
    """Kategorikan rekomendasi dari judulnya."""
    title_lower = title.lower()

    if "yield" in title_lower:
        return "yield"
    if "scrap" in title_lower:
        return "scrap"
    if "oee" in title_lower:
        return "oee"
    if "cost" in title_lower or "biaya" in title_lower:
        return "cost"
    if "utilitas" in title_lower or "listrik" in title_lower:
        return "utility"
    if "material" in title_lower or "resin" in title_lower or "stok" in title_lower:
        return "inventory"
    if "dead stock" in title_lower or "likuidasi" in title_lower:
        return "dead_stock"
    if "supplier" in title_lower:
        return "supplier"
    return "other"


def _extract_keywords(text: str, min_len: int = 4) -> List[str]:
    """Ekstrak kata kunci penting dari teks."""
    stop_words = {
        "yang", "dari", "untuk", "dengan", "pada", "akan", "ini",
        "itu", "tidak", "atau", "juga", "sudah", "bisa", "dapat",
        "adalah", "oleh", "saja", "agar", "kita", "anda", "saya",
    }
    words = text.lower().split()
    return [
        w.strip(".,;:!?()[]{}\"'")
        for w in words
        if len(w) >= min_len and w not in stop_words
    ]


# ==================== STATISTICS ====================

def compute_stats(limit: int = 500) -> DecisionStats:
    """Hitung statistik dari semua keputusan."""
    try:
        rows = db.get_decisions(limit=limit)
    except Exception:
        return DecisionStats()

    if not rows:
        return DecisionStats()

    stats = DecisionStats(total=len(rows))

    category_counter = Counter()
    keyword_counter = Counter()

    for r in rows:
        decision = str(r.get("decision", "")).lower()
        title = str(r.get("recommendation", ""))
        notes = str(r.get("notes", ""))

        # Hitung approved/rejected
        if "approve" in decision:
            stats.approved += 1
            # Impact hanya dari yang disetujui
            stats.total_impact_rp += _parse_impact(notes)

        elif "reject" in decision:
            stats.rejected += 1

        # Kategori
        cat = _categorize_title(title)
        category_counter[cat] += 1

        # Keyword
        for kw in _extract_keywords(title):
            keyword_counter[kw] += 1

    stats.top_categories = category_counter.most_common(5)
    stats.top_keywords = keyword_counter.most_common(10)
    return stats


# ==================== INSIGHTS ====================

def generate_insights(stats: DecisionStats,
                      min_decisions: int = 3) -> List[MemoryInsight]:
    """Buat insight dari statistik keputusan."""
    insights: List[MemoryInsight] = []

    # Belum cukup data
    if stats.total < min_decisions:
        remaining = min_decisions - stats.total
        insights.append(MemoryInsight(
            title="Belum Cukup Data",
            icon="📊",
            description=(
                f"Butuh minimal {min_decisions} keputusan untuk analisis pola. "
                f"Anda baru membuat {stats.total} keputusan. "
                f"Setujui/tolak {remaining} rekomendasi lagi untuk unlock insights."
            ),
        ))
        return insights

    # 1. Acceptance rate
    ar = stats.acceptance_rate
    if ar >= 80:
        insights.append(MemoryInsight(
            title="Anda Cenderung Setuju",
            icon="✅",
            description=(
                f"Anda menyetujui {ar:.0f}% dari rekomendasi. "
                f"Ini menandakan sistem sudah cukup relevan dengan kebutuhan Anda."
            ),
            metric=f"{stats.approved}/{stats.total} approved",
        ))
    elif ar <= 30:
        insights.append(MemoryInsight(
            title="Banyak Rekomendasi Ditolak",
            icon="⚠️",
            description=(
                f"Anda menolak {100-ar:.0f}% dari rekomendasi. "
                f"Pertimbangkan untuk update target di Settings, "
                f"atau mungkin konteks pabrik berbeda dari default."
            ),
            metric=f"{stats.rejected}/{stats.total} rejected",
        ))
    else:
        insights.append(MemoryInsight(
            title="Pola Seimbang",
            icon="⚖️",
            description=(
                f"Acceptance rate Anda {ar:.0f}% — seimbang antara setuju dan tolak. "
                f"Bagus untuk validasi rekomendasi."
            ),
            metric=f"{stats.approved} approved · {stats.rejected} rejected",
        ))

    # 2. Total impact
    if stats.total_impact_rp > 0:
        if stats.total_impact_rp >= 1_000_000_000:
            impact_str = f"Rp {stats.total_impact_rp/1_000_000_000:.2f} M"
        elif stats.total_impact_rp >= 1_000_000:
            impact_str = f"Rp {stats.total_impact_rp/1_000_000:.1f} jt"
        else:
            impact_str = f"Rp {stats.total_impact_rp:,.0f}"

        insights.append(MemoryInsight(
            title="Total Potensi Hemat dari Keputusan Anda",
            icon="💰",
            description=(
                f"Anda sudah menyetujui {stats.approved} rekomendasi dengan total "
                f"potensi penghematan **{impact_str}**. "
                f"Pastikan semua dieksekusi dan diukur hasilnya."
            ),
            metric=impact_str,
        ))

    # 3. Top category
    if stats.top_categories:
        top_cat, count = stats.top_categories[0]
        pct = count / stats.total * 100
        cat_label = {
            "yield": "Yield", "scrap": "Scrap", "oee": "OEE",
            "cost": "Biaya", "utility": "Utilitas",
            "inventory": "Inventory", "dead_stock": "Dead Stock",
            "supplier": "Supplier", "other": "Lainnya",
        }.get(top_cat, top_cat.title())

        insights.append(MemoryInsight(
            title=f"Fokus Utama: {cat_label}",
            icon="🎯",
            description=(
                f"Rekomendasi terkait **{cat_label}** paling sering muncul "
                f"({pct:.0f}% dari total). Ini area yang perlu perhatian utama."
            ),
            metric=f"{count} rekomendasi",
        ))

    # 4. Diversifikasi kategori
    unique_cats = len(stats.top_categories)
    if unique_cats >= 4:
        insights.append(MemoryInsight(
            title="Rekomendasi Terdiversifikasi",
            icon="🌈",
            description=(
                f"Sistem mendeteksi masalah di {unique_cats} kategori berbeda. "
                f"Portofolio perbaikan Anda cukup luas."
            ),
            metric=f"{unique_cats} kategori",
        ))
    elif unique_cats == 1 and stats.total >= 5:
        cat = stats.top_categories[0][0]
        insights.append(MemoryInsight(
            title="Fokus Sempit",
            icon="🔍",
            description=(
                f"Semua rekomendasi Anda fokus di 1 kategori ({cat}). "
                f"Pertimbangkan cek KPI lain — mungkin ada masalah tersembunyi."
            ),
        ))

    return insights


# ==================== OUTCOME TRACKING ====================

def update_outcome(decision_id: int, days: int, outcome: str) -> bool:
    """Update outcome 30/60/90 hari untuk sebuah keputusan.

    Args:
        decision_id: ID keputusan di database
        days: 30 | 60 | 90
        outcome: teks hasil (mis. "Yield naik 1.2 pp")
    """
    if days not in (30, 60, 90):
        raise ValueError(f"days harus 30/60/90, got {days}")

    column = f"outcome_{days}d"

    try:
        with db.get_conn() as conn:
            conn.execute(
                f"UPDATE decisions SET {column} = ? WHERE id = ?",
                (outcome, decision_id),
            )
        return True
    except Exception:
        return False


def get_all_decisions_with_outcome(limit: int = 100) -> List[Dict]:
    """Ambil semua keputusan lengkap dengan outcome."""
    try:
        return db.get_decisions(limit=limit)
    except Exception:
        return []


# ==================== TREND ANALYSIS ====================

def compute_weekly_trend(weeks: int = 8) -> List[Dict]:
    """Hitung tren keputusan per minggu (8 minggu terakhir)."""
    try:
        all_decisions = db.get_decisions(limit=1000)
    except Exception:
        return []

    if not all_decisions:
        return []

    # Group by week
    now = datetime.now()
    buckets: Dict[str, Dict[str, int]] = defaultdict(lambda: {"approved": 0, "rejected": 0})

    for d in all_decisions:
        try:
            ts = datetime.fromisoformat(d.get("timestamp", ""))
        except (ValueError, TypeError):
            continue

        weeks_ago = (now - ts).days // 7
        if weeks_ago >= weeks:
            continue

        week_key = f"M-{weeks_ago}" if weeks_ago > 0 else "This Week"
        decision = str(d.get("decision", "")).lower()

        if "approve" in decision:
            buckets[week_key]["approved"] += 1
        elif "reject" in decision:
            buckets[week_key]["rejected"] += 1

    # Sort by weeks_ago
    result = []
    for i in range(weeks - 1, -1, -1):
        key = f"M-{i}" if i > 0 else "This Week"
        label = f"{i} minggu lalu" if i > 0 else "Minggu ini"
        data = buckets.get(key, {"approved": 0, "rejected": 0})
        result.append({
            "week": label,
            "approved": data["approved"],
            "rejected": data["rejected"],
            "total": data["approved"] + data["rejected"],
        })

    return result