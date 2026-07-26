from typing import Any, Dict, List, Optional
import math
import random

class OuroborosParameter:
    """
    A tunable parameter exposed to the LGNN for dynamic sweeping and mutation.
    """
    def __init__(self, name: str, min_val: float, max_val: float, default: float, is_int: bool = False):
        self.name = name
        self.min_val = min_val
        self.max_val = max_val
        self.current_value = default
        self.is_int = is_int

    def sweep(self, mutation_rate: float = 0.1) -> float:
        """
        Slightly mutates the parameter. The LGNN calls this to explore new states.
        """
        range_span = self.max_val - self.min_val
        delta = (random.random() * 2 - 1.0) * range_span * mutation_rate
        new_val = self.current_value + delta
        new_val = max(self.min_val, min(self.max_val, new_val))
        
        if self.is_int:
            new_val = round(new_val)
            
        self.current_value = new_val
        return self.current_value

class OuroborosNode:
    """
    Base class for all abstract mathematical/AI filters in the Auratic Swarm.
    Completely data-agnostic: Can process finance, audio, or geodata.
    """
    def __init__(self, node_id: str):
        self.node_id = node_id
        self.parameters: Dict[str, OuroborosParameter] = {}
        self._setup_parameters()
        
    def _setup_parameters(self):
        """Override this to define tunable parameters."""
        pass
        
    def get_parameter(self, name: str) -> Any:
        return self.parameters[name].current_value
        
    def mutate_parameters(self, mutation_rate: float = 0.1):
        """Called by the LGNN to sweep all parameters slightly."""
        for param in self.parameters.values():
            param.sweep(mutation_rate)
            
    def process(self, data_stream: Any) -> Any:
        """
        The core Ouroboros function. Eats data, processes it, returns transformed data.
        Must be overridden by subclasses.
        """
        raise NotImplementedError("OuroborosNode must implement process()")
