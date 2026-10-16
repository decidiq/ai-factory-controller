"""Fase 5 — AI Factory OS: Multi-Agent Foundation."""
from .base import BaseAgent, AgentResult
from .tools import TOOLS, call_tool, list_tools
from .registry import AGENTS, get_agent, list_agents
from .orchestrator import (
    route,
    run_agent,
    run_orchestrated,
    route_explain,
)

__all__ = [
    "BaseAgent",
    "AgentResult",
    "TOOLS",
    "call_tool",
    "list_tools",
    "AGENTS",
    "get_agent",
    "list_agents",
    "route",
    "run_agent",
    "run_orchestrated",
    "route_explain",
]