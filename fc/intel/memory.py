"""Institutional Memory Engine — belajar dari keputusan user (BRD 8, Fase 3)."""
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List

from .. import db


@dataclass
class DecisionStats:
    total: int = 0
    approved: int = 0
    rejected: int = 0
    total_impact_rp: float = 0.0
    top_categories: List[tuple] = field(default_factory=list)
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


def _parse_impact(notes: str) -> float:
    if not notes:
        return 0.0
    import re
    matches = re.findall(r"Rp\s*([\d.,]+)", notes)
    if not matches:
        return 0.0
    max_val = 0.0
    for m in matches:
        clean = m.replace(".", "").replace(",", ".")
        try:
            val = float(clean)
            if val > max_val:
                max_val = val
        except ValueError:
            pass
    return max_val


def _categorize_title(title: str) -> str:
    t = title.lower()
    if "yield" in t: return "yield"
    if "scrap" in t: return "scrap"
    if "oee" in t: return "oee"
    if "cost" in t or "biaya" in t: return "cost"
    if "utilitas" in t or "listrik" in t: return "utility"
    if "material" in t or "resin" in t or "stok" in t: return "inventory"
    if "dead stock" in t or "likuidasi" in t: return "dead_stock"
    if "supplier" in t: return "supplier"
    return "other"


def _extract_keywords(text: str, min_len: int = 4) -> List[str]:
    stop = {"yang","dari","untuk","dengan","pada","akan","ini","itu",
            "tidak","atau","juga","sudah","bisa","dapat","adalah","oleh",
            "saja","agar","kita","anda","saya"}
    words = text.lower().split()
    return [w.strip(".,;:!?()[]{}\"'") for w in words
            if len(w) >= min_len and w not in stop]


def compute_stats(limit: int = 500) -> DecisionStats:
    try:
        rows = db.get_decisions(limit=limit)
    except Exception:
        return DecisionStats()
    if not rows:
        return DecisionStats()
    stats = DecisionStats(total=len(rows))
    cat_counter = Counter()
    kw_counter = Counter()
    for r in rows:
        decision = str(r.get("decision", "")).lower()
        title = str(r.get("recommendation", ""))
        notes = str(r.get("notes", ""))
        if "approve" in decision:
            stats.approved += 1
            stats.total_impact_rp += _parse_impact(notes)
        elif "reject" in decision:
            stats.rejected += 1
        cat_counter[_categorize_title(title)] += 1
        for kw in _extract_keywords(title):
            kw_counter[kw] += 1
    stats.top_categories = cat_counter.most_common(5)
    stats.top_keywords = kw_counter.most_common(10)
    return stats


def generate_insights(stats: DecisionStats, min_decisions: int = 3) -> List[MemoryInsight]:
    insights: List[MemoryInsight] = []
    if stats.total < min_decisions:
        remaining = min_decisions - stats.total
        insights.append(MemoryInsight(
            title="Belum Cukup Data", icon="📊",
            description=f"Butuh minimal {min_decisions} keputusan untuk analisis pola. "
                        f"Anda baru membuat {stats.total} keputusan. "
                        f"Setujui/tolak {remaining} rekomendasi lagi untuk unlock insights.",
        ))
        return insights
    ar = stats.acceptance_rate
    if ar >= 80:
        insights.append(MemoryInsight(
            title="Anda Cenderung Setuju", icon="✅",
            description=f"Anda menyetujui {ar:.0f}% dari rekomendasi. "
                        f"Ini menandakan sistem sudah cukup relevan dengan kebutuhan Anda.",
            metric=f"{stats.approved}/{stats.total} approved",
        ))
    elif ar <= 30:
        insights.append(MemoryInsight(
            title="Banyak Rekomendasi Ditolak", icon="⚠️",
            description=f"Anda menolak {100-ar:.0f}% dari rekomendasi. "
                        f"Pertimbangkan untuk update target di Settings.",
            metric=f"{stats.rejected}/{stats.total} rejected",
        ))
    else:
        insights.append(MemoryInsight(
            title="Pola Seimbang", icon="⚖️",
            description=f"Acceptance rate Anda {ar:.0f}% — seimbang antara setuju dan tolak.",
            metric=f"{stats.approved} approved / {stats.rejected} rejected",
        ))
    if stats.total_impact_rp > 0:
        if stats.total_impact_rp >= 1_000_000_000:
            impact_str = f"Rp {stats.total_impact_rp/1_000_000_000:.2f} M"
        elif stats.total_impact_rp >= 1_000_000:
            impact_str = f"Rp {stats.total_impact_rp/1_000_000:.1f} jt"
        else:
            impact_str = f"Rp {stats.total_impact_rp:,.0f}"
        insights.append(MemoryInsight(
            title="Total Potensi Hemat dari Keputusan Anda", icon="💰",
            description=f"Anda sudah menyetujui {stats.approved} rekomendasi dengan total "
                        f"potensi penghematan **{impact_str}**.",
            metric=impact_str,
        ))
    if stats.top_categories:
        top_cat, count = stats.top_categories[0]
        pct = count / stats.total * 100
        cat_label = {"yield": "Yield", "scrap": "Scrap", "oee": "OEE",
                     "cost": "Biaya", "utility": "Utilitas",
                     "inventory": "Inventory", "dead_stock": "Dead Stock",
                     "supplier": "Supplier", "other": "Lainnya"}.get(top_cat, top_cat.title())
        insights.append(MemoryInsight(
            title=f"Fokus Utama: {cat_label}", icon="🎯",
            description=f"Rekomendasi terkait **{cat_label}** paling sering muncul "
                        f"({pct:.0f}% dari total).",
            metric=f"{count} rekomendasi",
        ))
    return insights


def update_outcome(decision_id: int, days: int, outcome: str) -> bool:
    if days not in (30, 60, 90):
        raise ValueError(f"days harus 30/60/90, got {days}")
    column = f"outcome_{days}d"
    try:
        with db.get_conn() as conn:
            conn.execute(f"UPDATE decisions SET {column} = ? WHERE id = ?",
                         (outcome, decision_id))
        return True
    except Exception:
        return False


def get_all_decisions_with_outcome(limit: int = 100) -> List[Dict]:
    try:
        return db.get_decisions(limit=limit)
    except Exception:
        return []


def compute_weekly_trend(weeks: int = 8) -> List[Dict]:
    try:
        all_decisions = db.get_decisions(limit=1000)
    except Exception:
        return []
    if not all_decisions:
        return []
    now = datetime.now()
    buckets = defaultdict(lambda: {"approved": 0, "rejected": 0})
    for d in all_decisions:
        try:
            ts = datetime.fromisoformat(d.get("timestamp", ""))
        except (ValueError, TypeError):
            continue
        weeks_ago = (now - ts).days // 7
        if weeks_ago >= weeks:
            continue
        key = f"M-{weeks_ago}" if weeks_ago > 0 else "This Week"
        decision = str(d.get("decision", "")).lower()
        if "approve" in decision:
            buckets[key]["approved"] += 1
        elif "reject" in decision:
            buckets[key]["rejected"] += 1
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
