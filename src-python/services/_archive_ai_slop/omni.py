
import json
import os
import logging
import random
from typing import Dict, Any

logger = logging.getLogger("AuraticOmni")

class OmniMind:
    """
    The Omni (Phase 30).
    The Self-Rewriting Intelligence.
    """
    def __init__(self, config_dir="backend/config"):
        self.config_dir = config_dir
        self.active = True
        
    def evolve_config(self, strategy_name: str, current_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Takes current config, mutates it, and saves it.
        Returns new config.
        """
        if not self.active: return current_config
        
        logger.info(f"[OMNI] 🧬 Evolving DNA for {strategy_name}...")
        
        new_config = current_config.copy()
        
        # Mutation Logic (Generic)
        for key, val in new_config.items():
            if isinstance(val, float):
                # 10% Mutation
                mutation = random.uniform(0.9, 1.1)
                new_config[key] = val * mutation
            elif isinstance(val, int) and not isinstance(val, bool):
                # Integer Mutation
                change = random.choice([-1, 0, 1])
                new_config[key] = max(1, val + change)
                
        # Persist
        self._save_config(strategy_name, new_config)
        return new_config

    def _save_config(self, name: str, config: Dict[str, Any]):
        try:
            path = os.path.join(self.config_dir, f"{name}_evolved.json")
            with open(path, 'w') as f:
                json.dump(config, f, indent=4)
            logger.info(f"[OMNI] 💾 Config Saved: {path}")
        except Exception as e:
            logger.error(f"[OMNI] Failed to save config: {e}")

_omni_instance = None
def get_omni():
    global _omni_instance
    if _omni_instance is None:
        _omni_instance = OmniMind()
    return _omni_instance
