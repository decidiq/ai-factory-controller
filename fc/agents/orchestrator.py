"""Orchestrator — routing task ke agent yang tepat."""
from typing import Optional
import re

from .base import AgentResult
from .registry import get_agent


ROUTING_RULES = [
    ("inventory", [
        r"\bstok\b", r"\bstock\b", r"\binventor", r"\bmaterial\b",
        r"\breorder\b", r"\bdead stock\b", r"\bslow moving\b",
        r"\bstock[- ]?out\b", r"\bgudang\b",
    ]),
    ("maintenance", [
        r"\bmaintenance\b", r"\bmesin\b", r"\bdown(t)?ime\b",
        r"\bpreventive\b", r"\bservis\b", r"\bperbaikan\b",
        r"\bkerusakan\b", r"\bmtbf\b", r"\bmtbr\b",
    ]),
    ("quality", [
        r"\bkualitas\b", r"\bquality\b", r"\bscrap\b", r"\bdefect\b",
        r"\breject\b", r"\bcacat\b", r"\bqc\b", r"\byield\b",
    ]),
    ("risk", [
        r"\brisiko\b", r"\brisk\b", r"\bmitigasi\b", r"\bancaman\b",
        r"\bprobabilitas\b", r"\bdampak\b", r"\bregister\b",
    ]),
    ("cost", [
        r"\bbiaya\b", r"\bcost\b", r"\bcogm\b", r"\bhemat\b",
        r"\bvariance\b", r"\banggaran\b", r"\bbudget\b",
        r"\brp\b", r"\bmargin\b", r"\befisiensi\b",
    ]),
    ("production", [
        r"\bproduksi\b", r"\boutput\b", r"\boee\b", r"\bforecast\b",
        r"\banomali\b", r"\bline\b", r"\bthroughput\b",
    ]),
    ("executive", [
        r"\bringkas", r"\bbriefing\b", r"\bexecutive\b", r"\bdirektur\b",
        r"\bstrategi\b", r"\boverall\b", r"\bkeseluruhan\b",
        r"\bkeputusan\b", r"\bprioritas\b",
    ]),
]


def route(task: str) -> str:
    """Tentukan nama agent dari task string. Default: executive."""
    t = task.lower()
    for agent_name, patterns in ROUTING_RULES:
        for pat in patterns:
            if re.search(pat, t):
                return agent_name
    return "executive"


def run_agent(name: str, task: str, ds, scope, **kwargs) -> AgentResult:
    """Run single agent by name."""
    agent = get_agent(name)
    return agent.run(task, ds, scope, **kwargs)


def run_orchestrated(task: str, ds, scope,
                     force_agent: Optional[str] = None,
                     **kwargs) -> AgentResult:
    """Auto-route task ke agent yang tepat, lalu run."""
    name = force_agent or route(task)
    return run_agent(name, task, ds, scope, **kwargs)


def route_explain(task: str) -> dict:
    """Untuk debugging/UI: jelaskan kenapa task di-route ke agent tertentu."""
    name = route(task)
    t = task.lower()
    matched = []
    for agent_name, patterns in ROUTING_RULES:
        if agent_name != name:
            continue
        for pat in patterns:
            if re.search(pat, t):
                matched.append(pat)
    return {
        "agent": name,
        "matched_keywords": matched,
        "fallback": not matched,
    }