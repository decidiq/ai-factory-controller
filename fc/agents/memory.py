"""Agent Memory — persistent run history + context recall.

Berbeda dari fc/intel/memory.py (decision analytics user),
modul ini menyimpan riwayat eksekusi agent untuk:
1. Recall konteks percakapan sebelumnya
2. Konsistensi rekomendasi antar run
3. Audit trail agent
"""
import json
import os
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

DB_PATH = os.path.join("data", "agent_memory.db")


# ==================== SCHEMA ====================

_SCHEMA = """
CREATE TABLE IF NOT EXISTS agent_runs (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp    TEXT NOT NULL,
    agent        TEXT NOT NULL,
    task         TEXT NOT NULL,
    content      TEXT NOT NULL,
    confidence   INTEGER DEFAULT 0,
    duration_ms  INTEGER DEFAULT 0,
    source_tools TEXT,
    scope_json   TEXT,
    session_id   TEXT,
    error        TEXT
);
CREATE INDEX IF NOT EXISTS idx_agent_runs_ts      ON agent_runs(timestamp);
CREATE INDEX IF NOT EXISTS idx_agent_runs_agent   ON agent_runs(agent);
CREATE INDEX IF NOT EXISTS idx_agent_runs_session ON agent_runs(session_id);
"""


def _conn() -> sqlite3.Connection:
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(_SCHEMA)
    return conn


# ==================== DATACLASS ====================

@dataclass
class RunRecord:
    id: int
    timestamp: str
    agent: str
    task: str
    content: str
    confidence: int
    duration_ms: int
    source_tools: List[str]
    session_id: Optional[str]
    error: Optional[str]

    def age_hours(self) -> float:
        try:
            ts = datetime.fromisoformat(self.timestamp)
            return (datetime.now() - ts).total_seconds() / 3600
        except Exception:
            return 999.0


# ==================== WRITE ====================

def save_run(
    agent: str,
    task: str,
    content: str,
    confidence: int = 0,
    duration_ms: int = 0,
    source_tools: Optional[List[str]] = None,
    scope: Any = None,
    session_id: Optional[str] = None,
    error: Optional[str] = None,
) -> int:
    """Simpan 1 run. Return row id."""
    scope_json = None
    if scope is not None:
        try:
            scope_json = json.dumps(asdict(scope), default=str)
        except Exception:
            scope_json = json.dumps(str(scope))

    try:
        with _conn() as conn:
            cur = conn.execute(
                """INSERT INTO agent_runs
                   (timestamp, agent, task, content, confidence, duration_ms,
                    source_tools, scope_json, session_id, error)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    datetime.now().isoformat(timespec="seconds"),
                    agent, task, content,
                    int(confidence or 0), int(duration_ms or 0),
                    json.dumps(list(source_tools or [])),
                    scope_json, session_id, error,
                ),
            )
            return cur.lastrowid
    except Exception:
        return -1


# ==================== READ ====================

def _row_to_record(row: sqlite3.Row) -> RunRecord:
    try:
        tools = json.loads(row["source_tools"] or "[]")
    except Exception:
        tools = []
    return RunRecord(
        id=row["id"],
        timestamp=row["timestamp"],
        agent=row["agent"],
        task=row["task"],
        content=row["content"],
        confidence=row["confidence"] or 0,
        duration_ms=row["duration_ms"] or 0,
        source_tools=tools,
        session_id=row["session_id"],
        error=row["error"],
    )


def get_recent(
    agent: Optional[str] = None,
    session_id: Optional[str] = None,
    limit: int = 10,
) -> List[RunRecord]:
    """Ambil N run terakhir, filter opsional by agent / session."""
    sql = "SELECT * FROM agent_runs WHERE 1=1"
    params: list = []
    if agent:
        sql += " AND agent = ?"
        params.append(agent)
    if session_id:
        sql += " AND session_id = ?"
        params.append(session_id)
    sql += " ORDER BY id DESC LIMIT ?"
    params.append(limit)

    try:
        with _conn() as conn:
            rows = conn.execute(sql, params).fetchall()
            return [_row_to_record(r) for r in rows]
    except Exception:
        return []


def search_runs(query: str, limit: int = 10) -> List[RunRecord]:
    """Cari run by keyword (LIKE, case-insensitive)."""
    q = f"%{query.lower()}%"
    try:
        with _conn() as conn:
            rows = conn.execute(
                """SELECT * FROM agent_runs
                   WHERE LOWER(task) LIKE ? OR LOWER(content) LIKE ?
                   ORDER BY id DESC LIMIT ?""",
                (q, q, limit),
            ).fetchall()
            return [_row_to_record(r) for r in rows]
    except Exception:
        return []


# ==================== CONTEXT BUILDER ====================

def get_context_for(
    task: str,
    agent: Optional[str] = None,
    max_runs: int = 3,
    max_chars_per_run: int = 300,
) -> str:
    """Siapkan blok teks konteks dari run sebelumnya untuk di-inject ke LLM."""
    keywords = [w for w in task.lower().split() if len(w) >= 5][:3]
    candidates: List[RunRecord] = []
    seen_ids = set()

    for kw in keywords:
        for r in search_runs(kw, limit=max_runs):
            if r.id not in seen_ids:
                candidates.append(r)
                seen_ids.add(r.id)
            if len(candidates) >= max_runs:
                break
        if len(candidates) >= max_runs:
            break

    if not candidates and agent:
        candidates = get_recent(agent=agent, limit=max_runs)

    if not candidates:
        return ""

    lines = ["=== MEMORI PERCAKAPAN SEBELUMNYA ==="]
    for r in candidates:
        age = r.age_hours()
        if age < 1:
            age_str = f"{int(age*60)} menit lalu"
        elif age < 24:
            age_str = f"{int(age)} jam lalu"
        else:
            age_str = f"{int(age/24)} hari lalu"

        content_preview = r.content[:max_chars_per_run].replace("\n", " ").strip()
        lines.append(
            f"[{r.agent} · {age_str}] "
            f"User: {r.task[:120]} → "
            f"Jawaban: {content_preview}..."
        )
    lines.append("=== AKHIR MEMORI ===")
    return "\n".join(lines)


# ==================== MAINTENANCE ====================

def clear_old(days: int = 30) -> int:
    """Hapus run > N hari. Return jumlah row terhapus."""
    cutoff = (datetime.now() - timedelta(days=days)).isoformat(timespec="seconds")
    try:
        with _conn() as conn:
            cur = conn.execute(
                "DELETE FROM agent_runs WHERE timestamp < ?", (cutoff,)
            )
            return cur.rowcount
    except Exception:
        return 0


def clear_all() -> int:
    """Hapus semua run. Return jumlah row terhapus."""
    try:
        with _conn() as conn:
            cur = conn.execute("DELETE FROM agent_runs")
            return cur.rowcount
    except Exception:
        return 0


# ==================== STATS ====================

def stats() -> Dict[str, Any]:
    """Statistik memory: total, per agent, per hari."""
    try:
        with _conn() as conn:
            total = conn.execute("SELECT COUNT(*) FROM agent_runs").fetchone()[0]

            by_agent = conn.execute(
                "SELECT agent, COUNT(*) as n FROM agent_runs "
                "GROUP BY agent ORDER BY n DESC"
            ).fetchall()

            by_day = conn.execute(
                """SELECT SUBSTR(timestamp, 1, 10) as day, COUNT(*) as n
                   FROM agent_runs
                   GROUP BY day ORDER BY day DESC LIMIT 14"""
            ).fetchall()

            avg_conf = conn.execute(
                "SELECT AVG(confidence) FROM agent_runs WHERE confidence > 0"
            ).fetchone()[0] or 0

            avg_ms = conn.execute(
                "SELECT AVG(duration_ms) FROM agent_runs WHERE duration_ms > 0"
            ).fetchone()[0] or 0

            return {
                "total": total,
                "by_agent": [(r["agent"], r["n"]) for r in by_agent],
                "by_day": [(r["day"], r["n"]) for r in by_day],
                "avg_confidence": round(avg_conf, 1),
                "avg_duration_ms": int(avg_ms),
            }
    except Exception as e:
        return {
            "total": 0, "by_agent": [], "by_day": [],
            "avg_confidence": 0, "avg_duration_ms": 0,
            "error": str(e),
        }