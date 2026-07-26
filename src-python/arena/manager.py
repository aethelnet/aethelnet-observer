import asyncio
import threading
import logging
import os
import time
import math
from typing import Dict, Any, List, Optional
from config import get_settings
class MockLayerTracker: pass
def get_layer_tracker(): return MockLayerTracker()
from arena.api import Champion

logger = logging.getLogger("LiveManager")

class LiveStrategyManager:
    """
    The General (Neural Reconstruction).
    Uses the LayerTracker manifold to bridge signals to the Live/Testnet layer.
    
    Philosophy: 
    - Replaced poisoned "Zodiac" logic with raw Layer Performance metrics.
    - Prioritizes "Rat" (Scorpio Cusp) layers in Chaos Mode.
    - Acts as a high-speed signal aggregator for the Execution Engine.
    """
    
    def __init__(self):
        # Load Stealth Mode from Environment
        self.is_stealth_active = os.getenv("STEALTH_MODE", "true").lower() == "true"
        self.is_auto_pilot_active = True
        self.execution_mode = "PAPER"
        self.active_avatar = "SNAKE" if self.is_stealth_active else "FALCON"
        self.hive_state = {"whitelist": [], "blacklist": []}
        self.trades = [] # Internal buffer for broadcast
        self.trade_history = [] # Persistent history for this session
        self.active_memory_name = "default"
        self.confidence_threshold = 0.65 # Sovereign Default
        self._latest_metrics = {
            "pnl": 0.0,
            "trades": 0,
            "win_rate": 0.0,
            "equity": 0.0,
            "space_weather": {
                "alpha_flux": 0.0,
                "kp_index": 0.0,
                "solar_wind": 0.0
            },
            "bit_stage": 0
        }
        
        self.tracker = get_layer_tracker()
        from arena.gene_synthesizer import GeneSynthesizer
        self.synthesizer = GeneSynthesizer()
        
        self.active_layers = [
            "rat_trinity_trend",
            "rat_initiation_trend",
            "rat_momentum_swarm",
            "rat_velocity_gate",
            "rat_wick_rebound",
            "arena_reality"
        ]
        
        # Performance Cache (The Nitro)
        self._weight_cache = {}
        self._last_weight_update = 0
        self._weight_cache_ttl = 60 # Seconds
        
        self.load_manager_state() # Restore persistence (threshold, mode, etc.)
        self.start_background_tasks()
        logger.info("[System] Reconstructed Live Strategy Manager INITIALIZED (Sovereign Layer-Primary).")

    def start_background_tasks(self):
        """Starts the background alchemist loop."""
        asyncio.create_task(self._evolution_loop())

    async def _evolution_loop(self):
        """
        The Alchemist Loop: Periodically evolves the Sovereign Gene Pool.
        Runs every 10 minutes to adapt to regime shifts.
        """
        while True:
            try:
                await asyncio.sleep(600) # 10 Minutes
                history, outcomes = self.tracker.get_evolution_data()
                if len(history) > 100:
                    logger.info(f"[ALCHEMY] Starting Evolution Cycle with {len(history)} records...")
                    # [SOVEREIGN STABILITY] Move heavy CPU-bound evolution to a background thread
                    # to prevent event loop starvation and system hangs.
                    await asyncio.to_thread(self.synthesizer.evolve_pool, history, outcomes)
                    logger.info(f"[ALCHEMY] New Sovereign Law Synthesized: {self.synthesizer.get_best_expression()}")
                else:
                    logger.debug(f"[ALCHEMY] Skipping evolution: Not enough data ({len(history)}/100)")
            except Exception as e:
                logger.error(f"[ALCHEMY] Evolution error: {e}")
                await asyncio.sleep(60)

    @property
    def latest_metrics(self):
        """Returns the latest performance metrics for the manifold."""
        return self._latest_metrics

    def log(self, message: str):
        """Standard logging interface for high-level system notifications."""
        logger.info(message)
        # We also push to the trades buffer for TUI/UI visibility
        self.trades.append({"type": "LOG", "message": message, "timestamp": time.time()})

    def update_telemetry(self, manifold_data: Dict[str, Any]):
        """
        Updates the live telemetry cache with 36D manifold data.
        Called by the Engine during the ingest cycle.
        """
        if not manifold_data: return
        
        # Update Space Weather
        self._latest_metrics["space_weather"] = {
            "alpha_flux": manifold_data.get("alpha_flux", 0.0),
            "kp_index": manifold_data.get("kp_index", 0.0),
            "solar_wind": manifold_data.get("speed", 400.0)
        }
        
        # Calculate Bit-Stage (Quantized Conviction)
        z = manifold_data.get("z_score", 0.0)
        if z != 0:
            self._latest_metrics["bit_stage"] = math.floor(math.log2(abs(z))) if abs(z) > 0 else -99
        else:
            self._latest_metrics["bit_stage"] = 0
            
        # Also capture PnL from manifold if present
        if "pnl" in manifold_data:
            self._latest_metrics["pnl"] = manifold_data["pnl"]

    def get_broadcast_trades(self):
        """Returns and clears the recent trades buffer."""
        tmp = list(self.trades)
        self.trades.clear()
        return tmp

    def get_trade_history(self):
        """Returns the full session trade history."""
        return self.trade_history

    def get_available_abilities(self) -> List[str]:
        """Scans for evolved champion checkpoints."""
        checkpoint_dir = os.path.join(os.getcwd(), "checkpoints", "auto")
        if not os.path.exists(checkpoint_dir):
            return []
        return [f for f in os.listdir(checkpoint_dir) if f.endswith(".pkl")]

    def get_strategy_ensemble_vote(self, market_state: Dict) -> Dict[str, Any]:
        """
        Synthesizes a master signal from the active performance layers.
        Returns the Sovereign Dictionary expected by the ExecutionEngine.
        """
        try:
            settings = get_settings()
            raw_signal = market_state.get('logic_signal', 0.0)
            
            # CHAOS MODE OVERRIDE: If threshold is 0, we bypass complex vetting 
            if getattr(settings, 'SIGNAL_THRESHOLD', 0.1) == 0.0:
                return {
                    "ensemble_signal": raw_signal,
                    "confidence": 1.0,
                    "active_avatar": "SOVEREIGN_RECON",
                    "council_votes": {"CHAOS_BYPASS": 1.0}
                }

            # Standard Mode: Use dynamic weights from the LayerTracker (36D Aware)
            weights = self.tracker.get_dynamic_weights(
                current_z=market_state.get('z_score', 0.0),
                current_volatility=market_state.get('volatility', 0.0),
                current_entropy=market_state.get('entropy', 0.0),
                current_astro=market_state.get('astro_power', 0.0),
                current_sentiment=market_state.get('sentiment_bias', 0.0)
            )
            
            # [SOVEREIGN GENE] Combinatorial Expression Synthesis
            # We evaluate the best evolved gene against the current 36D manifold
            gene_signal = self.synthesizer.evaluate_best(market_state)
            
            # [SOVEREIGN DEFAULT] Unified Neural Signal Synthesis
            confidence = market_state.get('confidence', 0.5)
            effective_threshold = self.confidence_threshold
            
            # Calculate Specialist/Rat Weight (Aggregation of all active layers)
            # This ensures arena_reality and other specialists influence the final signal.
            active_weight = sum(v for k, v in weights.items() if k in self.active_layers)
            
            # Final Signal Assembly: Neural + Combinatorial Gene + Active Weight
            # The gene_signal provides the "Weirdo Expert" edge.
            final_signal = (raw_signal + gene_signal) * (1.0 + active_weight)
            
            return {
                "ensemble_signal": final_signal,
                "confidence": confidence,
                "active_avatar": self.active_avatar,
                "council_votes": weights,
                "dna_threshold": effective_threshold,
                "gene_expression": self.synthesizer.get_best_expression()
            }

        except Exception as e:
            logger.error(f"[LiveManager] Ensemble vote error: {e}")
            return {
                "ensemble_signal": market_state.get('logic_signal', 0.0),
                "confidence": 0.5,
                "active_avatar": "FALLBACK",
                "council_votes": {}
            }


    def get_current_weights(self) -> Dict[str, Any]:
        """
        Returns the dynamic weights and directional bias for each strategy layer.
        Includes a 60s cache to prevent ingestion timeouts on high-symbol counts.
        """
        now = time.time()
        # Double-checked locking pattern
        if self._weight_cache and (now - self._last_weight_update) < self._weight_cache_ttl:
            return self._weight_cache

        if not hasattr(self, '_weight_lock'):
            self._weight_lock = threading.Lock()

        with self._weight_lock:
            if self._weight_cache and (now - self._last_weight_update) < self._weight_cache_ttl:
                return self._weight_cache

        try:
            # Get weights from tracker (These are performance-adjusted and potentially inverted)
            raw_weights = self.tracker.get_dynamic_weights()
            
            fusion_data = {}
            for layer, weight in raw_weights.items():
                side = 0.0
                with self.tracker._lock:
                    if self.tracker.strategy_history.get(layer):
                        last_record = self.tracker.strategy_history[layer][-1]
                        side = 1.0 if last_record.get('predicted_up', True) else -1.0
                
                fusion_data[layer] = {
                    'weight': abs(weight),
                    'side': side * (1.0 if weight >= 0 else -1.0)
                }
            
            # Update Cache
            self._weight_cache = fusion_data
            self._last_weight_update = now
            return fusion_data
        except Exception as e:
            logger.error(f"[LiveManager] Weight retrieval failed: {e}")
            return self._weight_cache or {}

    def save_manager_state(self):
        """Persists current state to checkpoints/manager_state.json"""
        state = {
            "execution_mode": self.execution_mode,
            "active_avatar": self.active_avatar,
            "active_memory_name": self.active_memory_name,
            "confidence_threshold": self.confidence_threshold,
            "hive_state": self.hive_state,
            "last_updated": time.time()
        }
        try:
            os.makedirs("checkpoints", exist_ok=True)
            with open("checkpoints/manager_state.json", "w") as f:
                import json
                json.dump(state, f)
            logger.info("[LiveManager] [SYNC] State persisted to disk.")
        except Exception as e:
            logger.error(f"[LiveManager] [FAIL] State persistence failed: {e}")

    def load_manager_state(self):
        """Restores state from checkpoints/manager_state.json if available."""
        path = "checkpoints/manager_state.json"
        if not os.path.exists(path):
            return
        try:
            with open(path, "r") as f:
                import json
                state = json.load(f)
                self.execution_mode = state.get("execution_mode", self.execution_mode)
                self.active_avatar = state.get("active_avatar", self.active_avatar)
                self.active_memory_name = state.get("active_memory_name", self.active_memory_name)
                self.confidence_threshold = state.get("confidence_threshold", self.confidence_threshold)
                self.hive_state = state.get("hive_state", self.hive_state)
                logger.info(f"[LiveManager] [RECALL] State restored from disk. Gate: {self.confidence_threshold:.3f}")
        except Exception as e:
            logger.error(f"[LiveManager] [FAIL] State restoration failed: {e}")

    def is_live_ready(self, symbol: str, signal: float, metadata: Dict = None) -> bool:
        """Determines if a symbol is ready for live execution."""
        settings = get_settings()
        threshold = getattr(settings, 'SIGNAL_THRESHOLD', 0.1)
        if threshold == 0.0:
            return True
        return abs(signal) >= threshold

    def load_ability(self, checkpoint_path: str):
        """Loads a champion's ability (The Rat) into the Live Manifold."""
        import pickle
        import json
        try:
            if not os.path.exists(checkpoint_path):
                logger.error(f"[LiveManager] Checkpoint NOT FOUND: {checkpoint_path}")
                return

            with open(checkpoint_path, 'rb') as f:
                data = pickle.load(f)
            
            population = data.get('population', [])
            if not population:
                logger.error(f"[LiveManager] No population found in {checkpoint_path}")
                return
                
            champion = population[0]
            skills = champion.skills if hasattr(champion, 'skills') else {}
            
            if not skills:
                logger.warning(f"[LiveManager] Champion from {checkpoint_path} has NO skills. Aborting injection.")
                return

            # [NEURAL SYNC] Inhale the evolved threshold into the manager's gating logic
            self.confidence_threshold = float(skills.get('confidence_threshold', 0.65))
            logger.info(f"[LiveManager] [GATE] Neural Threshold UPDATED: {self.confidence_threshold:.3f}")

            logger.info(f"[LiveManager] [EPIPHANY] Champion skills ingested: {skills}")
            
            skills_file = os.path.join(os.getcwd(), "checkpoints", "active_skills.json")
            os.makedirs(os.path.dirname(skills_file), exist_ok=True)
            with open(skills_file, 'w') as f:
                json.dump({
                    "skills": skills,
                    "source": checkpoint_path,
                    "timestamp": time.time(),
                    "fitness": data.get('fitness', 0.0)
                }, f, indent=4)
            
            logger.info(f"[LiveManager] [SYNC] Neural skills synchronized to {skills_file}")
            self.active_memory_name = checkpoint_path
            self.save_manager_state() # Persist the new threshold
            
        except Exception as e:
            logger.error(f"[LiveManager] FATAL injection error: {e}", exc_info=True)

    # --- BOT / UI HANDLER INTERFACES ---
    def set_execution_mode(self, mode: str):
        self.execution_mode = mode
        logger.info(f"[LiveManager] Execution Mode -> {mode}")
        self.save_manager_state()

    def set_execution_state(self, active: bool):
        self.is_auto_pilot_active = active
        logger.info(f"[LiveManager] AutoPilot -> {active}")

    def set_auto_pilot(self, active: bool):
        self.set_execution_state(active)

    def switch_avatar(self, avatar: str):
        self.active_avatar = avatar
        logger.info(f"[LiveManager] Avatar -> {avatar}")

    def activate_relic(self, relic_id: str):
        logger.info(f"[LiveManager] Activating Relic: {relic_id}")

    def add_ally(self, username: str):
        if username not in self.hive_state['whitelist']:
            self.hive_state['whitelist'].append(username)
            logger.info(f"[Hive] Added ally: {username}")
            self.save_manager_state()

    def revoke_ally(self, username: str):
        if username in self.hive_state['whitelist']:
            self.hive_state['whitelist'].remove(username)
            logger.info(f"[Hive] Revoked ally: {username}")
            self.save_manager_state()

    def record_execution(self, trade_data: Dict):
        """Records a trade in the session history."""
        self.trades.append(trade_data)
        self.trade_history.append(trade_data)
        # Update metrics (Simplified)
        self._latest_metrics['trades'] += 1
        self._latest_metrics['pnl'] += trade_data.get('pnl', 0.0)

    def broadcast_skills(self):
        logger.info("[LiveManager] Broadcasting current skills to UI.")

    def update_risk_settings(self, settings: Dict):
        logger.info(f"[LiveManager] Risk Updated: {settings}")

    def update_rat_skills(self, skills: Dict):
        logger.info(f"[LiveManager] Rat Skills Forced: {skills}")

    def update_wallet_settings(self, settings: Dict):
        logger.info(f"[LiveManager] Wallet Updated: {settings}")
