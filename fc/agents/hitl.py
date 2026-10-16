"""Human-in-the-Loop — approve/reject rekomendasi agent.

Wrapper tipis di atas fc.db.log_decision + fc.db.get_decisions.
Setiap keputusan user tercatat di tabel `decisions` (Fase 3),
otomatis feed ke Institutional Memory.
"""
from typing import Dict, List, Optional

from fc import db


VALID_DECISIONS = ("approve", "reject", "noted")


def save_decision(
    recommendation: str,
    decision: str,
    notes: str = "",
    user: str = "system",
    agent: str = "",
    confidence: int = 0,
    extra_tags: Optional[List[str]] = None,
) -> int:
    """Simpan keputusan user ke DB. Return row id (atau -1 kalau gagal).

    Args:
        recommendation: Teks rekomendasi / task / hasil agent
        decision:       "approve" | "reject" | "noted"
        notes:          Catatan opsional dari user
        user:           Nama user (dari session)
        agent:          Nama agent yang menghasilkan (mis. "maintenance")
        confidence:     Confidence score 0-100 (opsional)
        extra_tags:     Tag tambahan (mis. ["phase5c", "synthesis"])

    Format recommendation yang disimpan:
        📌 [agent] <recommendation>
        [Confidence: XX%] [Tags: a, b] [Notes: ...]
    """
    if decision not in VALID_DECISIONS:
        raise ValueError(f"decision harus salah satu dari {VALID_DECISIONS}")

    # Susun string recommendation yang kaya metadata
    parts = []
    if agent:
        parts.append(f"[{agent}]")
    parts.append(recommendation.strip())

    meta_parts = []
    if confidence:
        meta_parts.append(f"Confidence: {confidence}%")
    if extra_tags:
        meta_parts.append(f"Tags: {', '.join(extra_tags)}")

    full_rec = " ".join(parts)
    if meta_parts:
        full_rec += " | " + " | ".join(meta_parts)

    try:
        return db.log_decision(
            recommendation=full_rec,
            decision=decision,
            user=user,
            notes=notes.strip(),
        )
    except Exception:
        return -1


def recent_decisions(limit: int = 20, user: Optional[str] = None) -> List[Dict]:
    """Ambil keputusan terbaru, filter opsional by user."""
    try:
        rows = db.get_decisions(limit=limit)
    except Exception:
        return []
    if user:
        rows = [r for r in rows if r.get("user") == user]
    return rows


def decision_summary(limit: int = 200) -> Dict[str, int]:
    """Ringkasan jumlah approve / reject / noted."""
    try:
        rows = db.get_decisions(limit=limit)
    except Exception:
        return {"approve": 0, "reject": 0, "noted": 0, "total": 0}

    counts = {"approve": 0, "reject": 0, "noted": 0}
    for r in rows:
        d = str(r.get("decision", "")).lower()
        if d in counts:
            counts[d] += 1
    counts["total"] = sum(counts.values())
    return counts


def get_current_user() -> str:
    """Ambil username dari session state Streamlit. Fallback: 'system'."""
    try:
        import streamlit as st
        user = st.session_state.get("_user") or st.session_state.get("user")
        if isinstance(user, dict):
            user = user.get("username") or user.get("name")
        if user:
            return str(user)
    except Exception:
        pass
    return "system"