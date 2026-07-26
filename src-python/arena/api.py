from abc import ABC, abstractmethod
import pandas as pd
from typing import Dict, Any, List, Optional
import numpy as np

# --- THE JOYFUL API ---

class IStrategy(ABC):
    """
    The Base Card.
    To create a new strategy, just inherit from this and implement 2 methods.
    """
    
    def __init__(self, skills: Dict[str, Any] = None):
        """
        Stats / Build.
        skills: Hyperparameters (e.g. {'lookback': 20, 'aggression': 1.5})
        """
        self.skills = skills if skills else self.default_skills()

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of your Strategy (e.g. 'The Rogue')"""
        pass
        
    @property
    @abstractmethod
    def class_type(self) -> str:
        """Archetype: 'Tank', 'Rogue', 'Alchemist', or 'Custom'"""
        pass

    def default_skills(self) -> Dict[str, Any]:
        """Define your base stats here."""
        return {}

    def crossover(self, other: 'IStrategy') -> 'IStrategy':
        """
        Uniform Crossover: coin flip per gene.
        Creates a child with genes randomly picked from self or other.
        """
        child_skills = {}
        for key in self.skills:
            if key in other.skills and isinstance(self.skills[key], (int, float)) and not isinstance(self.skills[key], bool):
                child_skills[key] = self.skills[key] if np.random.random() < 0.5 else other.skills[key]
            else:
                child_skills[key] = self.skills[key]
        return self.__class__(skills=child_skills)

    def evolve(self, mutation_rate: float = 0.1) -> 'IStrategy':
        """
        Respawn Mechanic.
        Returns a NEW instance of this strategy with mutated skills.
        """
        new_skills = self.skills.copy()
        
        for key, val in new_skills.items():
            # Numeric mutation
            if isinstance(val, (int, float)) and not isinstance(val, bool):
                if np.random.random() < mutation_rate:
                    # Mutate by +/- 20%
                    change = np.random.uniform(0.8, 1.2)
                    try:
                        new_skills[key] = val * change
                    except Exception as e:
                        print(f"Mutation Failed for {key}: {e}")
                    
                    # Round ints back to ints
                    if isinstance(val, int):
                        new_skills[key] = int(round(new_skills[key]))
        
        # Return new instance
        return self.__class__(skills=new_skills)

    @abstractmethod
    def on_tick(self, market_state: Dict[str, Any]) -> float:
        """
        The Brain.
        Input: market_state (price, volume, indicators...)
        Output: Signal (-1.0 to 1.0)
                -1.0 = Max Short
                 0.0 = Cash / Neutral
                 1.0 = Max Long
        
        This is where you have fun!
        """
        pass

    def on_gladiator_death(self):
        """Optional: Called if your strategy blows up in the Gauntlet."""
        print(f"Strategy {self.name} died.")

class IGameMode(ABC):
    """
    The Arena.
    To create a new scenario, inherit from this.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the Mode (e.g., 'The Great War')"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Flavor text explaining the scenario."""
        pass

    @abstractmethod
    def generate_scenario(self) -> pd.DataFrame:
        """
        Returns the data for this mode.
        Can be Historical (Replay) or Synthetic (Procedural).
        Returns a DataFrame with [timestamp, open, high, low, close, volume]
        """
        pass

    def apply_handicap(self, signal: float, lag_ms: int = 0) -> float:
        """Optional: Mutate the signal (add lag, slippage) for Hard Mode."""
        return signal

class Champion:
    """
    A persistent container for an evolved strategy's DNA.
    Used for cross-process serialization (Pickle) to ensure Type survival.
    """
    def __init__(self, skills: Dict[str, Any]):
        self.skills = skills
