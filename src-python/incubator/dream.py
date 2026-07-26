

import logging
import threading
import time
import asyncio
import os
from services.brain import get_engine
# Import the evolution logic
# We assume train_artifacts.py is in arena
from arena.train_artifacts import evolve

logger = logging.getLogger("Dreamer")

class Dreamer:
    """
    The Dreamer Protocol.
    Runs genetic evolution in the background (REM Cycle)
    and hot-swaps the new brain into the live agent.
    """
    def __init__(self, interval_hours=4):
        self.interval = interval_hours * 3600
        self.running = False
        self._thread = None

    def start(self):
        if self.running: return
        self.running = True
        # Daemon thread ensures it dies when main process dies
        self._thread = threading.Thread(target=self._dream_loop, name="DreamerThread", daemon=True)
        self._thread.start()
        logger.info("[Dreamer] [INIT] DMT Drip Initiated. The Rat will evolve every 4 hours.")

    def _dream_loop(self):
        # Initial sleep to allow system to boot fully and stabilize
        time.sleep(120) 

        while self.running:
            try:
                logger.info("[Dreamer] [SLEEP] Entering REM Sleep... (Evolution Started)")
                
                # 1. Run Evolution
                # Returns (path, fitness)
                new_brain_path, fitness = evolve()
                
                if not new_brain_path:
                    logger.warning("[Dreamer] Evolution failed to produce an artifact (Sleeping).")
                    # Do NOT continue here - we want to hit the sleep loop below
                    # pass 
                else:
                    
                # 2. Validation (The Dad Check)
                # Check if fitness is acceptable. 
                # For now, we assume > 1000 (profitable).
                if fitness <= 1000.0:
                    logger.warning(f"[Dreamer] [WARN] Evolution Rejected. Fitness too low (${fitness:.2f}). Keeping old brain.")
                    continue
                
                # 3. Hot-Swap (The Epiphany)
                engine = get_engine()
                if hasattr(engine, 'live_manager') and engine.live_manager:
                    manager = engine.live_manager
                    
                    logger.info(f"[Dreamer] [EPIPHANY] Waking up with new skills (Fitness: ${fitness:.2f}).")
                    
                    # Force reload from the NEW versioned file
                    manager.load_ability(new_brain_path)
                    
                    # Update Manager State to persist this new brain as active
                    manager.active_memory_name = new_brain_path # update memory pointer
                    manager.save_manager_state() # Save pointer atomically
                    
                    # Notify UI
                    manager.log(f"[DREAMER] [UPGRADE] Genetic Upgrade Successful. Version: {os.path.basename(new_brain_path)}")
                else:
                    logger.warning("[Dreamer] Could not find LiveManager to inject skills.")

            except Exception as e:
                logger.error(f"[Dreamer] Nightmare detected: {e}")
            
            # 3. Wait for next cycle
            # We sleep in small chunks to allow clean shutdown
            for _ in range(int(self.interval / 10)):
                if not self.running: break
                time.sleep(10)

    def stop(self):
        self.running = False
        if self._thread:
            self._thread.join(timeout=1.0)
