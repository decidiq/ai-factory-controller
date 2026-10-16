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
from .collaborative import CollaborativeOrchestrator, CollaborativeResult
from . import memory as agent_memory

__all__ = [
    # Core
    "BaseAgent",
    "AgentResult",
    # Tools
    "TOOLS",
    "call_tool",
    "list_tools",
    # Registry
    "AGENTS",
    "get_agent",
    "list_agents",
    # Single-agent orchestrator
    "route",
    "run_agent",
    "run_orchestrated",
    "route_explain",
    # Multi-agent collaboration (Fase 5C)
    "CollaborativeOrchestrator",
    "CollaborativeResult",
    # Memory
    "agent_memory",
]