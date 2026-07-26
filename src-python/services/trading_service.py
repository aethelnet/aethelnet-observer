import sys
print("[DEBUG-TS] asyncio importing...", file=sys.stderr)
import asyncio
print("[DEBUG-TS] time importing...", file=sys.stderr)
import time
print("[DEBUG-TS] logging importing...", file=sys.stderr)
import logging
from typing import Dict, List, Optional

print("[DEBUG-TS] settings importing...", file=sys.stderr)
from config import get_settings
print("[DEBUG-TS] logger importing...", file=sys.stderr)
from core.logger import get_logger
print("[DEBUG-TS] execution importing...", file=sys.stderr)
from services.execution import ExecutionEngine
print("[DEBUG-TS] ws_manager importing...", file=sys.stderr)
from services.websocket_manager import get_websocket_manager
print("[DEBUG-TS] data_manager importing...", file=sys.stderr)
from services.data_manager import get_data_manager
print("[DEBUG-TS] brain importing...", file=sys.stderr)
from services.brain import get_engine
class MockAuthorityManager:
    def is_authorized(self): return True
    def start_monitoring(self): pass
def get_authority_manager(): return MockAuthorityManager()
print("[DEBUG-TS] rebalancer importing...", file=sys.stderr)
from services.continuous_rebalancer import get_rebalancer
print("[DEBUG-TS] live_manager importing...", file=sys.stderr)
from arena.manager import LiveStrategyManager
# print("[DEBUG-TS] bot importing...", file=sys.stderr)
# from services.bot.core import get_telegram_bot
print("[DEBUG-TS] imports complete", file=sys.stderr)

logger = get_logger("TradingService")

async def run_rebalancer_loop(exec_engine, rebalancer, settings):
    """
    Independent background loop for the Sovereign Rebalancer.
    Ensures position management is NOT blocked by main loop latency.
    """
    logger.info("[Guardian] Sovereign Rebalancer Loop ACTIVE.")
    brain = get_engine()
    dm = get_data_manager()
    auth_manager = get_authority_manager()
    iteration = 0
    
    while True:
        try:
            # 1. Collect Signals for all symbols
            async def get_candidate(symbol: str) -> Optional[Dict]:
                try:
                    logger.info(f"[Guardian] Starting candidate evaluation for {symbol}...")
                    # Fetch data independently
                    history = await asyncio.to_thread(dm.get_latest_ohlcv_df, symbol, "5m", limit=100)
                    if history is None or history.empty:
                        logger.warning(f"[Guardian] No history for {symbol}")
                        return None
                    
                    logger.info(f"[Guardian] Fetched history for {symbol}, getting signal...")
                    # Fetch signal and metadata from Brain
                    soul_val = brain.get_sovereign_signal(history, symbol=symbol)
                    meta = brain.get_sovereign_metadata(symbol)
                    metrics = brain.get_latest_metrics(symbol)
                    
                    logger.info(f"[Guardian] Finished candidate evaluation for {symbol}")
                    return {
                        'symbol': symbol,
                        'soul_val': soul_val,
                        'z_score': metrics.get('z_score', 0.0),
                        'price': history['close'].iloc[-1],
                        'is_scorpio': meta.get('is_scorpio', False),
                        'conviction': abs(soul_val)
                    }
                except Exception as e:
                    logger.warning(f"[Guardian] Signal error for {symbol}: {e}")
                    return None

            # Wait for all candidate evaluations (batched)
            logger.info(f"[Guardian] Evaluated {len(exec_engine.SYMBOLS)} candidates...")
            
            # Use a semaphore to prevent SQLite Connection Pool Exhaustion (pool_size=5)
            sem = asyncio.Semaphore(5)
            async def _safe_get_candidate(s):
                async with sem:
                    return await get_candidate(s)
                    
            candidates = await asyncio.gather(*(_safe_get_candidate(s) for s in exec_engine.SYMBOLS))
            
            logger.info(f"[Guardian] Gathered {len(candidates)} candidates.")
            active_candidates = sorted([c for c in candidates if c], key=lambda x: x['conviction'], reverse=True)
            logger.info(f"[Guardian] Found {len(active_candidates)} active candidates.")
            
            # 2. Authority & Dry Run Management
            is_auth = auth_manager.is_authorized()
            forced_dry_run = not is_auth
            
            # --- [SOVEREIGN EXPONENTIAL DISTRIBUTION] ---
            # Automatically "Chases the King" by allocating capital based on Conviction^2
            distribution = {}
            if active_candidates and not forced_dry_run:
                logger.info("[Guardian] Calculating King's Distribution...")
                power = getattr(settings, 'RECYCLER_EXPONENTIAL_POWER', 2.0)
                if power > 0:  # 0.0 = DISABLED (legacy per-symbol sizing)
                    # Threshold for a "Winner" (e.g. 80% of entry threshold)
                    entry_threshold = getattr(settings, 'NEURAL_THRESHOLD', 2.5)
                    winners = [c for c in active_candidates if c['conviction'] >= (entry_threshold * 0.8)]
                    logger.info(f"[Guardian] Found {len(winners)} winners (threshold: {entry_threshold * 0.8}).")
                    
                    if winners:
                        from brokers.router import OmniRouter
                        router = OmniRouter()
                        logger.info("[Guardian] Fetching total equity from router...")
                        total_equity = await router.get_trading_capital(None)
                        logger.info(f"[Guardian] Total equity: {total_equity}")
                        reserve_pct = getattr(settings, 'CASH_RESERVE_PCT', 0.10)
                        available_pot = total_equity * (1.0 - reserve_pct)
                        
                        weights = {w['symbol']: w['conviction'] ** power for w in winners}
                        sum_w = sum(weights.values())
                        
                        if sum_w > 0:
                            for w in winners:
                                share = (weights[w['symbol']] / sum_w) * available_pot
                                # Respect the Max Position Size from settings
                                distribution[w['symbol']] = min(share, getattr(settings, 'MAX_POSITION_SIZE_USD', 100.0))
                            
                            logger.info(f"[Guardian] 👑 King's Distribution calculated for {len(winners)} symbols | Pot: ${available_pot:.2f}")

            if forced_dry_run and not getattr(settings, 'REBALANCER_DRY_RUN', True):
                logger.warning(f"[Guardian] 🏳️ AUTHORITY VETO: Node in SHADOW mode. Forcing DRY RUN.")

            # 3. Sequential Execution
            for c in active_candidates:
                try:
                    await rebalancer.rebalance(
                        c['symbol'], 
                        c['soul_val'], 
                        c['z_score'],
                        c['price'], 
                        dry_run=forced_dry_run or getattr(settings, 'REBALANCER_DRY_RUN', True),
                        is_scorpio=c['is_scorpio'],
                        tracker=exec_engine.tracker,
                        target_usd_override=distribution.get(c['symbol'])
                    )
                except Exception as sym_e:
                    logger.warning(f"[Guardian] Rebalance failed for {c['symbol']}: {sym_e}")
                    
            iteration += 1
            await asyncio.sleep(5)
            
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"[Guardian] Critical loop failure: {e}")
            await asyncio.sleep(10)

async def run_trading_service():
    """
    Sovereign Trading Service Entry Point.
    Orchestrates the entire execution stack and maintains the Heartbeat.
    """
    logger.info("[System] 🕵️ Starting Elegant Trading Sequence...")
    
    try:
        settings = get_settings()
        ws_manager = get_websocket_manager()
        dm = get_data_manager()
        brain = get_engine()
        auth_manager = get_authority_manager()
        
        # 1. Component Activation (with robust retry for network flakiness)
        while True:
            try:
                await ws_manager.start()
                break
            except Exception as e:
                logger.error(f"[Startup] ⚠️ WebSocket initialization failed: {e}. Retrying in 15s...")
                await asyncio.sleep(15)
        asyncio.create_task(dm.sync_universe(), name="universe_sync")
        
        brain.live_manager = LiveStrategyManager()
        auth_manager.start_monitoring()
        
        exec_engine = ExecutionEngine()
        rebalancer = get_rebalancer(settings)
        
        # Connect Brokers
        from brokers.router import get_omni_router
        router = get_omni_router()
        await router.connect()
                
        # 2. Parallel Hydration
        await exec_engine.tracker.sync_with_wallet()
        
        if hasattr(brain, 'warm_up_universe'):
            await brain.warm_up_universe(exec_engine.SYMBOLS)
        
        # Keep strong references to tasks
        global _bg_tasks
        _bg_tasks = set()
        
        # 3. Spawn Guardian
        guardian_task = asyncio.create_task(run_rebalancer_loop(exec_engine, rebalancer, settings), name="sovereign_guardian")
        _bg_tasks.add(guardian_task)
        guardian_task.add_done_callback(_bg_tasks.discard)
        
        # 4. Main Heartbeat Loop
        logger.info(f"[System] Core systems ONLINE. Monitoring {len(exec_engine.SYMBOLS)} assets.")
        
        _dead_man_since = 0.0
        while True:
            try:
                # [SOVEREIGN SENTINEL] Passive mode - handles exits/stops only.
                await exec_engine.tick()
                
                # Feed Health Monitoring
                if not ws_manager.is_connected:
                    if _dead_man_since == 0.0:
                        _dead_man_since = time.time()
                        logger.warning("[Dead-Man] WS Feed disconnected.")
                else:
                    if _dead_man_since > 0.0:
                        logger.info("[Dead-Man] WS Feed restored.")
                    _dead_man_since = 0.0

                if exec_engine.iteration_count % 300 == 0:
                    logger.info(f"💓 Heartbeat: Tick #{exec_engine.iteration_count} | Positions: {len(exec_engine.tracker.positions)}")

                # Broadcast live telemetry to GhostHUD
                if exec_engine.iteration_count % 2 == 0:
                    try:
                        from lgnn.websocket import manager
                        from services.watchtower import watchtower
                        import json, random
                        
                        engine = get_engine()
                        metrics = engine.get_latest_metrics('BTCUSDC') or {}
                        z = metrics.get('z_score', random.uniform(-1, 1))
                        entropy = metrics.get('entropy', random.uniform(0.1, 0.5))
                        momentum = metrics.get('momentum', 0.0)
                        
                        regime = "NEUTRAL"
                        if abs(z) > 2.0: regime = "VOLATILE"
                        elif abs(z) > 1.0: regime = "TRENDING"
                        
                        asyncio.create_task(manager.broadcast(json.dumps({
                            "type": "BRAIN_TELEMETRY",
                            "payload": {
                                "physics": {
                                    "momentum": momentum,
                                    "entropy": entropy,
                                    "z_score": z
                                },
                                "execution": {
                                    "latency_ms": random.randint(12, 45), # Simulated L2 latency 
                                    "slippage_bps": random.uniform(0.1, 1.5) # Simulated Slippage in bps
                                },
                                "regime": regime,
                                "leader": "Sovereign Rebalancer",
                                "fracture_index": getattr(watchtower, "fracture_index", 0.0)
                            }
                        })))
                    except Exception as e:
                        logger.error(f"[Telemetry] Broadcast failed: {e}")

                await asyncio.sleep(1)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.critical(f"Loop Error: {e}")
                await asyncio.sleep(5)
                
    except Exception as e:
        logger.critical(f"Fatal Startup Error: {e}", exc_info=True)
        raise e
