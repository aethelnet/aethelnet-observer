
import os
import pickle
import logging
from typing import Dict, Any

logger = logging.getLogger("RivalArk")

class RivalManager:
    """
    The Pied Piper (Der Rattenfänger).
    A Shadow Manager that runs a perfect, unencumbered version of the Strategy.
    Acts as the Benchmark (The Villain) and the Source for the Sonar.
    """
    def __init__(self):
        self.avatar = None # The Villain (TheRat instance)
        self.name = "The Pied Piper"
        self.signal_history = [] # For Sonar
        
        # Load the Artifact
        self.load_imposter()

    def load_imposter(self):
        try:
            # We look for the Hyperbolic Time Chamber artifact
            repo_root = os.getcwd() # Assumes running from root
            path = os.path.join(repo_root, "checkpoints", "rat_the_hyperbolic_chk.pkl")
            
            if not os.path.exists(path):
                logger.warning(f"[RIVAL] Manifestation Failed. Artifact not found: {path}")
                return

            with open(path, 'rb') as f:
                data = pickle.load(f)
                population = data.get('population', [])
                if population:
                    champion = population[0] # Best Genome
                    
                    # Summon the Rat
                    from arena.strategies.rat import TheRat
                    self.avatar = TheRat()
                    
                    # Inject Skills (Perfect Copy)
                    if hasattr(champion, 'skills'):
                        self.avatar.skills.update(champion.skills)
                        
                    logger.info(f"[RIVAL] 🐀 The Pied Piper has entered Hamelin. Skills: {self.avatar.skills}")
                else:
                    logger.warning("[RIVAL] Artifact Corrupted (Empty Population).")
                    
        except Exception as e:
            logger.error(f"[RIVAL] Failed to summon the Imposter: {e}")

    def on_tick(self, market_state: Dict[str, Any]) -> float:
        """
        Executes the Shadow Logic.
        Returns: Signal (-1.0 to 1.0)
        """
        if not self.avatar: return 0.0
        
        try:
            signal = self.avatar.on_tick(market_state)
            
            # Store signal for Sonar (Butterfly Effect)
            self.signal_history.append({
                'timestamp': market_state.get('timestamp', 0),
                'signal': signal,
                'price': market_state.get('price', 0)
            })
            
            # Keep history short (100 ticks)
            if len(self.signal_history) > 100:
                self.signal_history.pop(0)
                
            return signal
        except Exception as e:
            logger.error(f"[RIVAL] Execution Error: {e}")
            return 0.0
