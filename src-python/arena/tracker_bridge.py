import os
import pickle
import logging
from typing import Dict, Any

from arena.strategies.phd.minsky_moment import TheMinskyMoment
from arena.strategies.phd.soros_loop import TheSorosLoop
from arena.strategies.phd.liquidity_hole import TheLiquidityHole
from arena.strategies.phd.professor import TheProfessor
from arena.strategies.personal.jade_protocol import TheJadeProtocol
from arena.strategies.personal.alchemic_architect import TheAlchemicArchitect
from arena.strategies.personal.auratic_bridge import TheAuraticBridge
from arena.strategies.personal.fleet_commander import TheFleetCommander
from arena.strategies.personal.sovereign_pilot import TheSovereignPilot
from arena.strategies.personal.echo_weaver import EchoWeaverStrategy
from arena.strategies.personal.reality_arbitrage import TheRealityArbitrage
from arena.strategies.personal.exiled_emperor import TheExiledEmperor
from arena.strategies.personal.seismic_vault import TheSeismicVault
from arena.strategies.personal.typhoon_sanctuary import TheTyphoonSanctuary
from arena.strategies.science.molecular import TheMolecularMind
from arena.strategies.science.stigmergy import TheStigmergy
from arena.strategies.science.kuramoto import TheKuramoto
from arena.strategies.prophit_net import ProphitNetStrategy
from arena.strategies.rat import TheRat
from arena.strategies.turtle import TheTurtle
from arena.strategies.dragon import TheDragon
from arena.strategies.surfer import TheSurfer
from arena.strategies.snake import TheSnake
from arena.strategies.berserker import TheBerserker
from arena.strategies.ox import TheOx
from arena.strategies.goose import TheGooseBull, TheGooseBear

logger = logging.getLogger("ArenaBridge")

# Define the ELITE ROSTER
ROSTER = {
    'arena_minsky': TheMinskyMoment,
    'arena_soros': TheSorosLoop,
    'arena_liquidity': TheLiquidityHole,
    'arena_professor': TheProfessor,
    'arena_jade': TheJadeProtocol,
    'arena_alchemic': TheAlchemicArchitect,
    'arena_bridge': TheAuraticBridge,
    'arena_fleet': TheFleetCommander,
    'arena_sovereign': TheSovereignPilot,
    'arena_echo': EchoWeaverStrategy,
    'arena_reality': TheRealityArbitrage,
    'arena_emperor': TheExiledEmperor,
    'arena_seismic': TheSeismicVault,
    'arena_typhoon': TheTyphoonSanctuary,
    'arena_molecular': TheMolecularMind,
    'arena_stigmergy': TheStigmergy,
    'arena_kuramoto': TheKuramoto,
    'arena_prophit': ProphitNetStrategy,
    'arena_rat': TheRat,
    'arena_turtle': TheTurtle,
    'arena_dragon': TheDragon,
    'arena_surfer': TheSurfer,
    'arena_snake': TheSnake,
    'arena_berserker': TheBerserker,
    'arena_ox': TheOx,
    'arena_goose_bull': TheGooseBull,
    'arena_goose_bear': TheGooseBear
}

class ArenaBridge:
    def __init__(self):
        self.strategies = {}
        self._initialize_roster()
        # [PARALLELISM] Thread pool for concurrent strategy evaluations
        from concurrent.futures import ThreadPoolExecutor
        self.executor = ThreadPoolExecutor(max_workers=10, thread_name_prefix="ArenaWorker")
        # [LATENCY KILL] Rapid-Cache: {symbol: (last_price, last_vol, signals)}
        self._rapid_cache = {}

    def _initialize_roster(self):
        import glob
        root_dir = os.getcwd()
        for layer_key, strategy_class in ROSTER.items():
            strategy_obj = strategy_class()
            name = strategy_obj.name.replace(" ", "_")
            
            if layer_key == 'arena_prophit':
                # Grab the best ProphitNet auto-checkpoint based on metadata
                search_pattern = os.path.join(root_dir, "checkpoints", "auto", "prophit_omniscient_*.pkl")
                files = glob.glob(search_pattern)
                if files:
                    best_file = None
                    best_score = -float('inf')
                    for f in files:
                        meta_path = f.replace('.pkl', '.metadata.json')
                        score = -float('inf')
                        if os.path.exists(meta_path):
                            import json
                            try:
                                with open(meta_path, 'r') as m:
                                    meta = json.load(m)
                                    score = meta.get('metadata', {}).get('universal_score', -float('inf'))
                            except:
                                pass
                        
                        # Fallback to mtime if score is invalid or tied at 0
                        if score > best_score:
                            best_score = score
                            best_file = f
                        elif score == best_score and best_file is not None:
                            if os.path.getmtime(f) > os.path.getmtime(best_file):
                                best_file = f
                                
                    pkl_path = best_file if best_file else max(files, key=os.path.getmtime)
                else:
                    pkl_path = os.path.join(root_dir, f"checkpoint_{name}.pkl")
            else:
                pkl_path = os.path.join(root_dir, f"checkpoint_{name}.pkl")
            
            try:
                if os.path.exists(pkl_path):
                    with open(pkl_path, 'rb') as f:
                        data = pickle.load(f)
                        if 'best_skills' in data:
                            strategy_obj.skills = data['best_skills']
                        elif 'skills' in data:
                            strategy_obj.skills = data['skills']
                    logger.info(f"[{layer_key}] Picked up genetic memory from {pkl_path}.")
                else:
                    logger.warning(f"[{layer_key}] No genetic memory found. Using default stats.")
            except Exception as e:
                logger.error(f"[{layer_key}] Failed to load genetic memory: {e}")

            self.strategies[layer_key] = strategy_obj
        
        logger.info(f"[ArenaBridge] Successfully materialized {len(self.strategies)} elite strategies in ghost mode.")

    def poll_arena(self, market_state: Dict[str, Any], dataframe=None) -> Dict[str, float]:
        """
        Evaluates the entire elite roster against the current market state.
        Now uses ThreadPoolExecutor for parallel processing and Rapid-Cache to skip redundant ticks.
        """
        symbol = market_state.get('symbol', 'UNKNOWN')
        price = market_state.get('price', 0.0)
        volume = market_state.get('volume', 0.0)
        
        # 0. CHECK RAPID-CACHE
        if symbol in self._rapid_cache:
            last_p, last_v, last_sigs = self._rapid_cache[symbol]
            if last_p == price and last_v == volume:
                return last_sigs # Market hasn't moved, return cached signals
                
        def _evaluate_single(layer_key, strategy_obj, state, df=None):
            try:
                # 1. Prefer Candle-level Analysis if Dataframe is available
                # (Phidia Elite strategies often store core logic in next_candle)
                if df is not None and not df.empty and hasattr(strategy_obj, 'next_candle'):
                    raw_out = strategy_obj.next_candle(df)
                    # If the candle signal is HOLD, try on_tick as a tactical fallback
                    if isinstance(raw_out, dict) and raw_out.get('action') == 'HOLD':
                         raw_out = strategy_obj.on_tick(state)
                else:
                    # 2. Regular Tick-level Signal
                    raw_out = strategy_obj.on_tick(state)
                    
                return layer_key, self._normalize_signal(raw_out)
            except Exception as e:
                logger.debug(f"[{layer_key}] Evaluation failed: {e}")
                return layer_key, 0.0

        # 1. PARALLEL EXECUTION
        futures = []
        for lk, obj in self.strategies.items():
            futures.append(self.executor.submit(_evaluate_single, lk, obj, market_state, dataframe))
            
        signals = {}
        for future in futures:
            try:
                layer_key, sig = future.result()
                signals[layer_key] = sig
            except Exception:
                continue
                
        # 2. UPDATE CACHE
        self._rapid_cache[symbol] = (price, volume, signals)
        
        return signals

    def _normalize_signal(self, raw_out: Any) -> float:
        if isinstance(raw_out, float) or isinstance(raw_out, int):
            return float(raw_out)
        elif isinstance(raw_out, dict):
            action = raw_out.get('action', 'HOLD').upper()
            if action == 'HOLD':
                return 0.0
            
            # Extract confidence if present
            conf = raw_out.get('confidence', 1.0)
            if isinstance(conf, str):
                conf_map = {'HIGH': 1.0, 'MEDIUM': 0.6, 'LOW': 0.3}
                conf = conf_map.get(conf.upper(), 1.0)
                
            if action in ['BUY', 'LONG', 'BUY_LIMIT']:
                return float(conf)
            elif action in ['SELL', 'SHORT', 'SELL_LIMIT']:
                return -float(conf)
        return 0.0

_bridge_instance = None
def get_arena_bridge() -> ArenaBridge:
    global _bridge_instance
    if _bridge_instance is None:
        _bridge_instance = ArenaBridge()
    return _bridge_instance
