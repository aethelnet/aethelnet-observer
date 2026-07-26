from abc import ABC, abstractmethod
from typing import Dict, Any

class IPlugin(ABC):
    """
    Interface for Auratic Engine Plugins.
    Part of the 'Flux Capacitor' architecture.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    def on_engine_start(self, engine_context: Dict[str, Any]):
        """Called when Long Haul starts."""
        pass

    def on_cycle_start(self, cycle_id: int):
        """Called before a Round Robin cycle begins."""
        pass

    def on_strategy_selected(self, strategy_name: str) -> bool:
        """
        Called before training a strategy. 
        Return False to skip this strategy (Curator logic).
        """
        return True

    def on_generation_complete(self, stats: Dict[str, Any]):
        """Called after a generation or batch is finished."""
        pass

    def get_resource_constraints(self) -> Dict[str, Any]:
        """
        Returns dynamic resource limits (e.g. max_population, sleep_time).
        Used by the Governor.
        """
        return {}
