import math
import random
import logging
import json
import os
import time
from typing import Dict, Any, List, Optional, Callable

logger = logging.getLogger("GeneSynthesizer")

class SovereignGene:
    """
    A symbolic expression tree for market execution laws.
    Can be mutated, crossed over, and evaluated.
    """
    OPERATORS = ['+', '-', '*', '/', 'tanh', 'abs', 'sin', 'cos', 'min', 'max']
    TERMINALS = [
        'z_score', 'volatility', 'entropy', 'stigmergy', 'physics_confidence',
        'astro_power', 'sentiment_bias', 'specialist_delta', 'ocean_wisdom_score',
        'price_velocity', 'volume_delta', 'kp_index', 'moon_phase'
    ]

    def __init__(self, expression: str = None):
        self.expression = expression or self._generate_random_expression()
        self.fitness = 0.0

    def _generate_random_expression(self, depth: int = 2) -> str:
        """Procedurally generate a random starting law."""
        if depth <= 0:
            return random.choice(self.TERMINALS)
        
        op = random.choice(self.OPERATORS)
        if op in ['tanh', 'abs', 'sin', 'cos']:
            return f"{op}({self._generate_random_expression(depth - 1)})"
        else:
            left = self._generate_random_expression(depth - 1)
            right = self._generate_random_expression(depth - 1)
            return f"({left} {op} {right})"

    def evaluate(self, state: Dict[str, float]) -> float:
        """
        Evaluate the expression safely in the current 36D manifold state.
        """
        # Restricted Sandbox
        safe_dict = {
            "math": math,
            "tanh": math.tanh,
            "abs": abs,
            "sin": math.sin,
            "cos": math.cos,
            "min": min,
            "max": max,
            "sqrt": lambda x: math.sqrt(abs(x))
        }
        safe_dict.update(state)
        
        try:
            # We use a restricted eval for safety
            result = eval(self.expression, {"__builtins__": None}, safe_dict)
            return float(result)
        except Exception:
            return 0.0

    def mutate(self, rate: float = 0.1):
        """Perform symbolic mutation (Scalar drift or Operator flip)."""
        # Simplified: For now, just generate a new branch occasionally
        if random.random() < rate:
            self.expression = self._generate_random_expression(depth=2)

class GeneSynthesizer:
    """
    The Alchemist: 
    Evolves a pool of SovereignGenes to find Niche Experts.
    """
    def __init__(self, pool_size: int = 50):
        self.pool = [SovereignGene() for _ in range(pool_size)]
        self.best_gene: Optional[SovereignGene] = None
        self.load_best_gene()

    def evolve_pool(self, manifold_history: List[Dict[str, float]], outcomes: List[float]):
        """
        Backtests the entire pool against history and selects winners.
        manifold_history: List of 36D states
        outcomes: List of PnL results for those states
        """
        for gene in self.pool:
            score = 0.0
            for i, state in enumerate(manifold_history):
                pred = gene.evaluate(state)
                # Fitness: Alignment with outcome
                # If outcome > 0 (Up) and pred > 0 -> Gain
                score += pred * outcomes[i]
            
            gene.fitness = score
            
        # Selection & Crossover
        self.pool.sort(key=lambda g: g.fitness, reverse=True)
        self.best_gene = self.pool[0]
        
        # Keep top 20%, mutate the rest
        survivors = self.pool[:len(self.pool)//5]
        new_pool = list(survivors)
        while len(new_pool) < len(self.pool):
            parent = random.choice(survivors)
            child = SovereignGene(parent.expression)
            child.mutate()
            new_pool.append(child)
            
        self.pool = new_pool
        self.save_best_gene() # PERSISTENCE: Save the new law to disk
        logger.info(f"[ALCHEMY] Evolution Cycle Complete. Best Fitness: {self.best_gene.fitness:.4f}")

    def save_best_gene(self):
        """Saves the current best law to a persistent JSON file."""
        if not self.best_gene: return
        try:
            path = "checkpoints/sovereign_law.json"
            os.makedirs("checkpoints", exist_ok=True)
            with open(path, "w") as f:
                json.dump({
                    "expression": self.best_gene.expression,
                    "fitness": self.best_gene.fitness,
                    "timestamp": time.time()
                }, f, indent=4)
            logger.debug("[ALCHEMY] Sovereign Law persisted to disk.")
        except Exception as e:
            logger.error(f"[ALCHEMY] Failed to save law: {e}")

    def load_best_gene(self):
        """Restores the best law from disk on startup."""
        try:
            path = "checkpoints/sovereign_law.json"
            if os.path.exists(path):
                with open(path, "r") as f:
                    data = json.load(f)
                    self.best_gene = SovereignGene(data["expression"])
                    self.best_gene.fitness = data.get("fitness", 0.0)
                logger.info(f"[ALCHEMY] Sovereign Law RESTORED: {self.best_gene.expression}")
        except Exception as e:
            logger.error(f"[ALCHEMY] Failed to load law: {e}")

    def evaluate_best(self, state: Dict[str, float]) -> float:
        if not self.best_gene:
            return 0.0
        return self.best_gene.evaluate(state)

    def get_best_expression(self) -> str:
        return self.best_gene.expression if self.best_gene else "z_score"
