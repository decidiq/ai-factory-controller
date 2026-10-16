"""Registry daftar agent yang tersedia."""
from typing import Dict, List, Type

from .base import BaseAgent
from .production import ProductionAgent
from .inventory import InventoryAgent
from .cost import CostAgent
from .executive import ExecutiveAgent


AGENTS: Dict[str, Type[BaseAgent]] = {
    "production": ProductionAgent,
    "inventory": InventoryAgent,
    "cost": CostAgent,
    "executive": ExecutiveAgent,
}


def get_agent(name: str, **kwargs) -> BaseAgent:
    """Factory: instantiate agent by name."""
    cls = AGENTS.get(name)
    if not cls:
        raise ValueError(f"agent '{name}' tidak terdaftar. "
                         f"Pilihan: {list(AGENTS.keys())}")
    return cls(**kwargs)


def list_agents() -> List[Dict[str, str]]:
    """Metadata semua agent untuk UI."""
    out = []
    for name, cls in AGENTS.items():
        out.append({
            "name": name,
            "role": cls.role,
            "description": cls.description,
            "tools": list(cls.tools_allowed),
        })
    return out