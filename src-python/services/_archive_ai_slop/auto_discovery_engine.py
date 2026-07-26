"""
Auto-Discovery Engine: Finding Markets to Farm

Automatically discovers and trades symbols where strategies perform well.
Scans Tier 1 symbols from universe calibration, monitors signals and regimes,
and allocates funds from a dedicated auto-discovery pool.

Reuses existing infrastructure:
- WebSocketManager.get_latest_buffer() - Already streams all symbols
- BrainEngine signals - Already generated per symbol
- UniverseManager - Already tracks regimes
- OmniRouter - Already handles execution
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field

from config import get_settings
from services.wallet import get_wallet
from services.websocket_manager import get_websocket_manager
from services.brain import get_engine
from services.universe import get_universe_manager
from services.data_manager import get_data_manager
from services.episode_pattern_matcher import get_episode_pattern_matcher
from services.binance_market_info import get_binance_market_info
from brokers.router import OmniRouter

logger = logging.getLogger("AutoDiscovery")

@dataclass
class DiscoveredSymbol:
    """Represents a symbol discovered and being traded by auto-discovery."""
    symbol: str
    discovery_time: float
    strategy_fit_score: float
    allocated_budget: float
    entry_price: Optional[float] = None
    entry_time: Optional[float] = None
    current_price: Optional[float] = None
    unrealized_pnl: float = 0.0
    total_trades: int = 0
    winning_trades: int = 0
    cumulative_pnl: float = 0.0
    status: str = "active"  # active, removed, promoted

class AutoDiscoveryEngine:
    """
    Automatically discovers and trades symbols where strategies excel.
    
    Works by:
    1. Scanning Tier 1 symbols from universe calibration
    2. Monitoring signals and regimes via existing data streams
    3. Calculating "strategy fit" scores
    4. Allocating budget from auto-discovery pool
    5. Trading discovered symbols separately from whitelist
    """
    # Class-level defaults to remove magic numbers from method bodies.
    # These may be overridden by self.settings where appropriate.
    MAX_ZSCORE: float = 5.0
    VOLUME_THRESHOLD_HIGH: float = 500000.0
    VOLUME_THRESHOLD_MED: float = 100000.0

    def __init__(self):
        self.settings = get_settings()
        self.discovered_symbols: Dict[str, DiscoveredSymbol] = {}
        self.closed_trades: List[Dict[str, Any]] = []
        self.is_running = False
        self._task: Optional[asyncio.Task] = None
        self.last_discovery_time = 0.0
        self.last_rebalance_time = 0.0
        self.whitelist_symbols: Set[str] = set()
        
        # Initialize whitelist symbols
        try:
            from config.settings import get_trading_symbols
            self.whitelist_symbols = set(get_trading_symbols(self.settings))
        except Exception:
            pass
        
        # Initialize episode pattern matcher and update patterns on startup
        try:
            pattern_matcher = get_episode_pattern_matcher()
            # Update patterns in background (don't block startup)
            import asyncio
            asyncio.create_task(pattern_matcher.update_patterns(force=True))
        except Exception as e:
            logger.debug(f"[AUTO-DISCOVERY] Could not initialize pattern matcher: {e}")
        
        logger.info("[AUTO-DISCOVERY] Engine initialized")
    
    async def calculate_strategy_fit_score(self, symbol: str, price: float, volume: float) -> float:
        """
        Calculate how well a symbol fits our trading strategies.
        
        Combines:
        - Signal strength (z-score magnitude)
        - Regime (Active vs Stagnant)
        - Volume trends (increasing activity)
        - Liquidity (Tier 1 = high liquidity)
        """
        score = 0.0
        
        try:
            # 1. Signal Strength (40% weight)
            brain_engine = get_engine()
            signal = 0.0
            
            # Get latest signal for this specific symbol
            if hasattr(brain_engine, 'z_score_history') and brain_engine.z_score_history:
                if hasattr(brain_engine, 'symbol_history') and brain_engine.symbol_history:
                    # Find the last z-score for this symbol
                    for i in range(len(brain_engine.symbol_history) - 1, -1, -1):
                        if brain_engine.symbol_history[i] == symbol and i < len(brain_engine.z_score_history):
                            signal = abs(brain_engine.z_score_history[i])
                            break
                else:
                    # Fallback: use latest z-score if no symbol history
                    signal = abs(brain_engine.z_score_history[-1]) if brain_engine.z_score_history else 0.0
            
            # Normalize signal to 0-1 range (use class-configurable MAX_ZSCORE)
            try:
                max_z = getattr(self, "MAX_ZSCORE", 5.0)
                signal_score = min(1.0, signal / max_z) if signal > 0 else 0.0
            except Exception:
                signal_score = min(1.0, signal / 5.0) if signal > 0 else 0.0
            score += signal_score * 0.25  # Reduced from 0.3 for sentiment
            
            # 2. Regime Detection (25% weight)
            # Use volatility and momentum from universe calibration
            regime_score = 0.5  # Default neutral
            
            try:
                # Get calibration metrics for this symbol
                dm = get_data_manager()
                calibration = await dm.calibrate_universe(lookback_days=2)
                metrics_df = calibration.get("metrics")
                
                if metrics_df is not None and not metrics_df.empty:
                    symbol_metrics = metrics_df[metrics_df['symbol'] == symbol]
                    if not symbol_metrics.empty:
                        row = symbol_metrics.iloc[0]
                        volatility = row.get('volatility', 0.0)
                        momentum = row.get('momentum', 0.0) if 'momentum' in row else 0.0
                        
                        # Active regime = higher volatility (2-5%) = better for trading
                        if volatility > 5.0:
                            regime_score = 0.9  # Crash/Panic - high opportunity but risky
                        elif volatility > 1.5:
                            regime_score = 0.8  # Active - ideal for trading
                        elif volatility > 1.0:
                            regime_score = 0.6  # Moderate activity
                        else:
                            regime_score = 0.4  # Stagnant - less opportunity
                        
                        # Boost score if momentum is strong (trending)
                        if abs(momentum) > 50:
                            regime_score = min(1.0, regime_score + 0.1)
            except Exception:
                # Fallback: use volume as proxy
                if volume > 0:
                    volume_normalized = min(1.0, volume / 1000000.0)
                    regime_score = 0.3 + (volume_normalized * 0.7)
            
            score += regime_score * 0.2  # Reduced from 0.25 for sentiment
            
            # 3. Volume Trend (15% weight)
            # Check if volume is increasing (would need history, simplified for now)
            volume_trend = 0.5  # Default neutral
            # In a full implementation, we'd track volume history per symbol
            # For MVP, assume high volume = positive trend (use class-level thresholds)
            try:
                if volume > getattr(self, "VOLUME_THRESHOLD_HIGH", 500000.0):
                    volume_trend = 0.8
                elif volume > getattr(self, "VOLUME_THRESHOLD_MED", 100000.0):
                    volume_trend = 0.6
            except Exception:
                if volume > 500000:
                    volume_trend = 0.8
                elif volume > 100000:
                    volume_trend = 0.6

            score += volume_trend * 0.15  # Reduced from 0.2
            
            # 4. Liquidity Score (10% weight)
            # Tier 1 symbols already have high liquidity
            liquidity_score = 1.0  # All candidates are Tier 1
            score += liquidity_score * 0.1
            
            # 5. Episode Pattern Matching (20% weight) - NEW!
            # Match current market conditions against successful historical episodes
            pattern_match_score = 0.0
            try:
                pattern_matcher = get_episode_pattern_matcher()
                
                # Get current market conditions
                current_volatility = volatility if 'volatility' in locals() else 0.0
                current_momentum = momentum if 'momentum' in locals() else 0.0
                current_regime = "Crash/Panic" if current_volatility > 5.0 else ("Active" if current_volatility > 1.5 else "Stagnant")
                
                # --- GLOBAL CONTEXT PREP (Auto-Discovery) ---
                global_ctx = {"regime": "Unknown", "correlation": 0.0}
                try:
                    leader = "BTCUSDC" 
                    if symbol == "BTCUSDC": leader = "ETHUSDC"
                    
                    if hasattr(brain_engine, 'states'):
                         l_state = brain_engine.states.get(leader)
                         s_state = brain_engine.states.get(symbol)
                         
                         if l_state:
                             l_vol = l_state.get('volatility', 0.0)
                             if l_vol > 5.0: global_ctx['regime'] = "Crash/Panic"
                             elif l_vol > 1.5: global_ctx['regime'] = "Active"
                             else: global_ctx['regime'] = "Stagnant"
                             
                             if s_state:
                                 l_prices = l_state.get('price_history', [])
                                 s_prices = s_state.get('price_history', [])
                                 if len(l_prices) > 10 and len(s_prices) > 10:
                                     try:
                                         import numpy as np
                                         min_len = min(len(l_prices), len(s_prices))
                                         lp = l_prices[-min_len:]
                                         sp = s_prices[-min_len:]
                                         corr = np.corrcoef(lp, sp)[0, 1]
                                         if not np.isnan(corr):
                                             global_ctx['correlation'] = float(corr)
                                     except:
                                         pass
                except Exception:
                    pass

                # Match against learned patterns
                pattern_match_score = pattern_matcher.match_pattern(
                    symbol=symbol,
                    volatility=current_volatility,
                    volume=volume,
                    signal_strength=signal,
                    regime=current_regime,
                    momentum=current_momentum,
                    global_context=global_ctx
                )
                
                # Boost score if pattern matches (this is learned from successful trades)
                score += pattern_match_score * 0.15
                
                # 6. Sentiment Score (15% weight) - HYPE METRIC
                sentiment_score = 0.5 # Neutral fallback
                try:
                    from services.news_correlation import get_news_correlation
                    news_engine = get_news_correlation()
                    if hasattr(news_engine, "get_sentiment"):
                        sentiment = await news_engine.get_sentiment(symbol)
                        if sentiment:
                            # Normalize from [-1, 1] to [0, 1]
                            sentiment_score = (sentiment.score + 1.0) / 2.0
                            logger.debug(f"[AUTO-DISCOVERY] {symbol} Sentiment Alpha: {sentiment_score:.2f}")
                except Exception as e:
                    logger.debug(f"[AUTO-DISCOVERY] Failed to fetch sentiment for {symbol}: {e}")
                
                score += sentiment_score * 0.15
                
            except Exception as e:
                logger.debug(f"[AUTO-DISCOVERY] Error in pattern matching for {symbol}: {e}")
                # If pattern matching fails, don't penalize - just skip it
                # Pattern matching is optional enhancement
            
        except Exception as e:
            logger.debug(f"[AUTO-DISCOVERY] Error calculating fit score for {symbol}: {e}")
        
        return score
    
    async def discovery_loop(self):
        """
        Main discovery loop that runs periodically to find new symbols.
        """
        discovery_interval = self.settings.AUTO_DISCOVERY_DISCOVERY_INTERVAL_MINUTES * 60
        
        logger.info(f"[AUTO-DISCOVERY] Starting discovery loop (interval: {self.settings.AUTO_DISCOVERY_DISCOVERY_INTERVAL_MINUTES} minutes)")
        
        while self.is_running:
            try:
                current_time = time.time()
                
                # Run discovery scan
                if current_time - self.last_discovery_time >= discovery_interval:
                    await self.scan_and_discover()
                    self.last_discovery_time = current_time
                
                # Daily rebalance
                rebalance_interval = self.settings.AUTO_DISCOVERY_REBALANCE_HOURS * 3600
                if current_time - self.last_rebalance_time >= rebalance_interval:
                    await self.rebalance_discoveries()
                    self.last_rebalance_time = current_time
                    
                    # Update episode patterns during rebalance (learn from new trades)
                    try:
                        pattern_matcher = get_episode_pattern_matcher()
                        await pattern_matcher.update_patterns(force=False)
                    except Exception as e:
                        logger.debug(f"[AUTO-DISCOVERY] Error updating patterns: {e}")
                
                # Wait before next iteration
                await asyncio.sleep(60)  # Check every minute
                
            except asyncio.CancelledError:
                logger.info("[AUTO-DISCOVERY] Discovery loop cancelled")
                break
            except Exception as e:
                logger.error(f"[AUTO-DISCOVERY] Error in discovery loop: {e}", exc_info=True)
                await asyncio.sleep(60)
    
    async def scan_and_discover(self):
        """Scan Tier 1 symbols and discover new trading opportunities."""
        if not self.settings.AUTO_DISCOVERY_ENABLED:
            return
        
        try:
            # Get Tier 1 symbols from universe calibration
            dm = get_data_manager()
            calibration = await dm.calibrate_universe(lookback_days=2)
            tier_1_symbols = calibration.get("core", [])
            
            # Filter out whitelist symbols and already discovered symbols
            candidates = [
                s for s in tier_1_symbols 
                if s.upper() not in self.whitelist_symbols 
                and s.upper() not in self.discovered_symbols
            ]
            
            if not candidates:
                logger.debug("[AUTO-DISCOVERY] No new candidates found")
                return
            
            # Get current market data from WebSocket buffer
            ws_manager = get_websocket_manager()
            buffer = ws_manager.get_latest_buffer()
            
            # Calculate strategy fit scores for candidates
            scored_candidates = []
            for symbol in candidates:
                symbol_upper = symbol.upper()
                if symbol_upper in buffer:
                    price_data = buffer[symbol_upper]
                    price = float(price_data.get('c', 0))  # Close price
                    volume = float(price_data.get('v', 0))  # Volume
                    
                    if price > 0:
                        score = await self.calculate_strategy_fit_score(symbol_upper, price, volume)
                        scored_candidates.append((symbol_upper, score, price, volume))
            
            # Sort by score (highest first)
            scored_candidates.sort(key=lambda x: x[1], reverse=True)
            
            # Filter to candidates meeting minimum signal threshold
            qualified_candidates = [
                (symbol, score, price, volume) 
                for symbol, score, price, volume in scored_candidates
                if score >= self.settings.AUTO_DISCOVERY_MIN_SIGNAL
            ]

            # Notify Bot of Opportunities
            try:
                from services.bot.core import get_telegram_bot
                bot = get_telegram_bot()
                if bot:
                    for sym, score, prc, _ in qualified_candidates:
                        await bot.check_opportunity_alerts({
                            "symbol": sym, 
                            "score": round(score, 2), 
                            "signal": "STRONG BUY", 
                            "price": prc
                        })
            except Exception:
                pass
            
            if not qualified_candidates:
                logger.debug("[AUTO-DISCOVERY] No candidates meet minimum signal threshold")
                return
            
            # Calculate how many we can afford
            wallet = get_wallet()
            auto_balance = wallet.get_auto_discovery_balance()
            
            # Get minimum notional for all candidates (use highest to be safe)
            market_info = get_binance_market_info()
            router = OmniRouter()
            max_min_notional = 10.0  # Default
            
            for symbol, _, _, _ in qualified_candidates[:5]:  # Check first 5
                broker = router._route(symbol)
                min_notional = await market_info.get_min_notional(symbol, broker)
                max_min_notional = max(max_min_notional, min_notional)
            
            min_allocation = max_min_notional * 1.2
            max_affordable = await self.calculate_affordable_symbol_count(auto_balance, min_allocation)
            available_slots = min(max_affordable, self.settings.AUTO_DISCOVERY_MAX_SYMBOLS) - len(self.discovered_symbols)
            
            if available_slots <= 0:
                logger.debug(f"[AUTO-DISCOVERY] No available slots (have {len(self.discovered_symbols)}, max {max_affordable})")
                return
            
            # Allocate using score-weighted method if we have enough funds
            await self.allocate_with_score_weighting(qualified_candidates[:available_slots], auto_balance)
            
        except Exception as e:
            logger.error(f"[AUTO-DISCOVERY] Error in scan_and_discover: {e}", exc_info=True)
    
    async def allocate_with_score_weighting(self, candidates: List[tuple], available_balance: float):
        """
        Allocate budget to candidates using score-weighted distribution.
        
        When funds allow, higher-scoring symbols get more budget.
        Falls back to equal allocation if score weighting would violate minimums.
        
        Args:
            candidates: List of (symbol, score, price, volume) tuples
            available_balance: Total available balance for allocation
        """
        if not candidates:
            return
        
        try:
            market_info = get_binance_market_info()
            router = OmniRouter()
            
            # Get min notional for each candidate
            candidate_minimums = {}
            total_score = 0.0
            
            for symbol, score, _, _ in candidates:
                broker = router._route(symbol)
                min_notional = await market_info.get_min_notional(symbol, broker)
                min_allocation = min_notional * 1.2
                candidate_minimums[symbol] = min_allocation
                total_score += score
            
            if total_score == 0:
                # Fallback to equal allocation
                allocation_per_symbol = available_balance / len(candidates)
                for symbol, score, price, _ in candidates:
                    if allocation_per_symbol >= candidate_minimums.get(symbol, 10.0):
                        await self._allocate_single_symbol(symbol, score, price, allocation_per_symbol)
                return
            
            # Try score-weighted allocation
            weighted_allocations = {}
            for symbol, score, _, _ in candidates:
                weight = score / total_score
                allocation = available_balance * weight
                weighted_allocations[symbol] = allocation
            
            # Check if all allocations meet minimums
            all_meet_minimum = all(
                weighted_allocations.get(symbol, 0) >= candidate_minimums.get(symbol, 10.0)
                for symbol, _, _, _ in candidates
            )
            
            if all_meet_minimum:
                # Use score-weighted allocation
                for symbol, score, price, _ in candidates:
                    allocation = weighted_allocations[symbol]
                    await self._allocate_single_symbol(symbol, score, price, allocation)
                logger.info(f"[AUTO-DISCOVERY] Used score-weighted allocation for {len(candidates)} symbols")
            else:
                # Fall back to equal allocation
                allocation_per_symbol = available_balance / len(candidates)
                for symbol, score, price, _ in candidates:
                    if allocation_per_symbol >= candidate_minimums.get(symbol, 10.0):
                        await self._allocate_single_symbol(symbol, score, price, allocation_per_symbol)
                logger.info(f"[AUTO-DISCOVERY] Used equal allocation (score-weighted would violate minimums)")
                
        except Exception as e:
            logger.error(f"[AUTO-DISCOVERY] Error in score-weighted allocation: {e}", exc_info=True)
            # Fallback to simple equal allocation
            allocation_per_symbol = available_balance / len(candidates)
            for symbol, score, price, _ in candidates:
                await self._allocate_single_symbol(symbol, score, price, allocation_per_symbol)
    
    async def _allocate_single_symbol(self, symbol: str, strategy_fit_score: float, current_price: float, allocation: float):
        """Helper method to allocate a single symbol with given allocation amount."""
        try:
            # Validate allocation meets minimum
            market_info = get_binance_market_info()
            router = OmniRouter()
            broker = router._route(symbol)
            min_notional = await market_info.get_min_notional(symbol, broker)
            min_allocation = min_notional * 1.2
            
            if allocation < min_allocation:
                logger.warning(
                    f"[AUTO-DISCOVERY] Allocation too small for {symbol} | "
                    f"allocation=${allocation:.2f} | min_required=${min_allocation:.2f}"
                )
                return
            
            # Create discovered symbol record
            discovered = DiscoveredSymbol(
                symbol=symbol,
                discovery_time=time.time(),
                strategy_fit_score=strategy_fit_score,
                allocated_budget=allocation,
                current_price=current_price
            )
            
            self.discovered_symbols[symbol] = discovered
            
            # --- SWARM SUGGEST FEATURE ---
            # Broadcast the suggestion to the UI via telemetry
            try:
                from services.websocket_manager import get_websocket_manager
                ws_manager = get_websocket_manager()
                
                broker_name = broker.name if hasattr(broker, 'name') else str(broker.__class__.__name__)
                if 'Hyperliquid' in broker_name:
                    broker_label = 'Hyperliquid'
                elif 'Alpaca' in broker_name:
                    broker_label = 'Alpaca'
                elif 'Binance' in broker_name:
                    broker_label = 'Binance'
                else:
                    broker_label = broker_name

                suggestion_payload = {
                    "type": "AUTO_DISCOVERY_SUGGESTION",
                    "symbol": symbol,
                    "score": float(strategy_fit_score),
                    "broker": broker_label,
                    "price": current_price,
                    "timestamp": time.time(),
                    "message": f"🧠 Swarm suggests: {symbol} on {broker_label} (Z-Score: {strategy_fit_score:.2f})"
                }
                asyncio.create_task(ws_manager.broadcast("SWARM_SUGGESTION", suggestion_payload))
            except Exception as e:
                logger.debug(f"[AUTO-DISCOVERY] Failed to broadcast suggestion: {e}")
            
            logger.info(
                f"[AUTO-DISCOVERY] 🎯 Discovered {symbol} | "
                f"Score: {strategy_fit_score:.2f} | "
                f"Allocation: ${allocation:.2f} | "
                f"Min Notional: ${min_notional:.2f} | "
                f"Price: ${current_price:.2f}"
            )
            
        except Exception as e:
            logger.error(f"[AUTO-DISCOVERY] Error allocating single symbol {symbol}: {e}", exc_info=True)
    
    async def calculate_affordable_symbol_count(self, available_balance: float, min_notional_per_symbol: float) -> int:
        """
        Calculate how many symbols can be afforded based on available balance.
        
        Args:
            available_balance: Total available balance in auto-discovery pool
            min_notional_per_symbol: Minimum notional required per symbol (with buffer)
        
        Returns:
            Maximum number of symbols that can be afforded
        """
        if min_notional_per_symbol <= 0:
            return self.settings.AUTO_DISCOVERY_MAX_SYMBOLS
        
        max_affordable = int(available_balance / min_notional_per_symbol)
        configured_max = self.settings.AUTO_DISCOVERY_MAX_SYMBOLS
        
        # Use the smaller of: what we can afford or configured maximum
        return min(max_affordable, configured_max)
    
    async def validate_position_size(self, symbol: str, position_value: float) -> bool:
        """
        Validate that position size meets Binance minimum notional requirements.
        
        Args:
            symbol: Trading symbol
            position_value: Position value in quote currency
        
        Returns:
            True if position size is valid, False otherwise
        """
        try:
            market_info = get_binance_market_info()
            
            # Get broker to pass to market info service
            router = OmniRouter()
            broker = router._route(symbol)
            
            min_notional = await market_info.get_min_notional(symbol, broker)
            
            # Add 10% buffer to ensure we're safely above minimum
            min_with_buffer = min_notional * 1.1
            
            if position_value < min_with_buffer:
                logger.warning(
                    f"[AUTO-DISCOVERY] Position size too small for {symbol} | "
                    f"position=${position_value:.2f} | min_required=${min_with_buffer:.2f} | "
                    f"min_notional=${min_notional:.2f}"
                )
                return False
            
            return True
            
        except Exception as e:
            logger.debug(f"[AUTO-DISCOVERY] Error validating position size for {symbol}: {e}")
            # On error, allow the trade (fail-safe)
            return True
    
    async def allocate_to_symbol(self, symbol: str, strategy_fit_score: float, current_price: float):
        """
        Allocate budget to a newly discovered symbol with smart resource management.
        
        Uses actual Binance minimum notional requirements and adapts to available funds.
        This is a convenience method for single-symbol allocation.
        For batch allocation with score weighting, use allocate_with_score_weighting().
        """
        try:
            wallet = get_wallet()
            auto_balance = wallet.get_auto_discovery_balance()
            
            # Get actual Binance minimum notional for this symbol
            market_info = get_binance_market_info()
            router = OmniRouter()
            broker = router._route(symbol)
            min_notional = await market_info.get_min_notional(symbol, broker)
            
            # Add 20% buffer above minimum to ensure we can trade comfortably
            min_allocation = min_notional * 1.2
            
            # Check if we have enough for even one symbol
            if auto_balance < min_allocation:
                logger.warning(
                    f"[AUTO-DISCOVERY] Insufficient total balance for {symbol} | "
                    f"available=${auto_balance:.2f} | required=${min_allocation:.2f} | "
                    f"min_notional=${min_notional:.2f}"
                )
                return
            
            # Calculate how many symbols we can afford
            max_affordable = await self.calculate_affordable_symbol_count(auto_balance, min_allocation)
            
            if max_affordable == 0:
                logger.warning(
                    f"[AUTO-DISCOVERY] Cannot afford any symbols | "
                    f"available=${auto_balance:.2f} | min_per_symbol=${min_allocation:.2f}"
                )
                return
            
            # Calculate allocation per symbol (equal split for single symbol allocation)
            allocation_per_symbol = auto_balance / max_affordable
            
            # Ensure allocation meets minimum
            if allocation_per_symbol < min_allocation:
                # Reduce symbol count to meet minimum
                max_affordable = int(auto_balance / min_allocation)
                if max_affordable == 0:
                    logger.warning(
                        f"[AUTO-DISCOVERY] Cannot afford {symbol} after recalculating | "
                        f"available=${auto_balance:.2f} | min_required=${min_allocation:.2f}"
                    )
                    return
                allocation_per_symbol = auto_balance / max_affordable
            
            # Use helper method for consistency
            await self._allocate_single_symbol(symbol, strategy_fit_score, current_price, allocation_per_symbol)
            
        except Exception as e:
            logger.error(f"[AUTO-DISCOVERY] Error allocating to {symbol}: {e}", exc_info=True)
    
    async def rebalance_discoveries(self):
        """Rebalance discovered symbols - remove underperformers, add new ones."""
        logger.info("[AUTO-DISCOVERY] Running daily rebalance...")
        
        # Remove symbols with poor performance
        to_remove = []
        for symbol, discovered in self.discovered_symbols.items():
            if discovered.status != "active":
                continue
            
            # Check performance metrics
            if discovered.total_trades >= 5:  # Need minimum trades for evaluation
                win_rate = discovered.winning_trades / discovered.total_trades if discovered.total_trades > 0 else 0.0
                
                # Remove if poor performance
                if win_rate < 0.3 or discovered.cumulative_pnl < -10.0:
                    to_remove.append(symbol)
                    logger.info(f"[AUTO-DISCOVERY] Removing {symbol} (win_rate={win_rate:.1%}, pnl=${discovered.cumulative_pnl:.2f})")
        
        # Remove underperformers
        for symbol in to_remove:
            discovered = self.discovered_symbols.pop(symbol, None)
            if discovered:
                discovered.status = "removed"
        
        # Scan for new discoveries
        await self.scan_and_discover()
    
    def get_active_symbols(self) -> List[str]:
        """Get list of currently active discovered symbols."""
        return [
            symbol for symbol, discovered in self.discovered_symbols.items()
            if discovered.status == "active"
        ]
    
    async def process_tick(self, symbol: str, price: float, signal: float):
        """
        Process a market tick for a discovered symbol.
        This is called from the trading service loop.
        """
        if symbol not in self.discovered_symbols:
            return
        
        discovered = self.discovered_symbols[symbol]
        discovered.current_price = price
        
        # Update unrealized PnL if we have a position
        if discovered.entry_price and discovered.entry_time:
            if discovered.entry_price > 0:
                # Calculate unrealized PnL (simplified - assumes LONG position)
                price_change = (price - discovered.entry_price) / discovered.entry_price
                position_value = discovered.allocated_budget
                discovered.unrealized_pnl = price_change * position_value
        
        # Check if we should enter a position
        if not discovered.entry_time and abs(signal) >= self.settings.AUTO_DISCOVERY_MIN_SIGNAL:
            await self.enter_position(symbol, price, signal)
        
        # Check if we should exit a position
        elif discovered.entry_time:
            await self.check_exit(symbol, price, signal)
    
    async def enter_position(self, symbol: str, price: float, signal: float):
        """
        Enter a position in a discovered symbol with position size validation.
        
        Validates that position size meets Binance minimum notional requirements
        before placing the order to prevent failed trades.
        """
        try:
            discovered = self.discovered_symbols.get(symbol)
            if not discovered or discovered.entry_time:
                return  # Already in position or not discovered
            
            # Calculate position size from allocated budget
            position_value = discovered.allocated_budget * 0.8  # Use 80% of allocation
            quantity = position_value / price if price > 0 else 0.0
            
            if quantity <= 0:
                return
            
            # Validate position size meets Binance minimum notional
            is_valid = await self.validate_position_size(symbol, position_value)
            if not is_valid:
                logger.warning(
                    f"[AUTO-DISCOVERY] Skipping entry for {symbol} - position size too small | "
                    f"position_value=${position_value:.2f}"
                )
                return
            
            # Check if we have enough balance
            wallet = get_wallet()
            auto_balance = wallet.get_auto_discovery_balance()
            
            if position_value > auto_balance:
                logger.warning(
                    f"[AUTO-DISCOVERY] Insufficient balance for {symbol} entry | "
                    f"needed=${position_value:.2f} | available=${auto_balance:.2f}"
                )
                return
            
            # Place order via router
            router = OmniRouter()
            side = "BUY" if signal > 0 else "SELL"
            
            if self.settings.EXECUTION_ENABLED:
                order_result = await router.place_order(symbol, side, "MARKET", quantity, price)
                if order_result:
                    discovered.entry_price = price
                    discovered.entry_time = time.time()
                    logger.info(
                        f"[AUTO-DISCOVERY] [OK] Entered {side} {symbol} @ ${price:.2f} | "
                        f"qty={quantity:.8f} | value=${position_value:.2f}"
                    )
            else:
                # Simulation mode
                discovered.entry_price = price
                discovered.entry_time = time.time()
                logger.info(
                    f"[AUTO-DISCOVERY] 🔮 SIMULATION: Would enter {side} {symbol} @ ${price:.2f} | "
                    f"qty={quantity:.8f} | value=${position_value:.2f}"
                )
            
        except Exception as e:
            logger.error(f"[AUTO-DISCOVERY] Error entering position for {symbol}: {e}", exc_info=True)
    
    async def check_exit(self, symbol: str, price: float, signal: float):
        """Check if we should exit a position in a discovered symbol."""
        try:
            discovered = self.discovered_symbols.get(symbol)
            if not discovered or not discovered.entry_time:
                return
            
            entry_price = discovered.entry_price
            entry_time = discovered.entry_time
            hold_time = time.time() - entry_time
            
            # Minimum hold time (same as main trading)
            min_hold_time = getattr(self.settings, 'MIN_HOLD_TIME', 90)
            if hold_time < min_hold_time:
                return  # Too soon to exit
            
            # Exit conditions
            should_exit = False
            exit_reason = ""
            
            # 1. Signal reversal
            if entry_price and entry_price > 0:
                # Check if signal reversed (simplified - assumes LONG)
                if signal < -self.settings.AUTO_DISCOVERY_MIN_SIGNAL:
                    should_exit = True
                    exit_reason = "signal_reversal"
            
            # 2. Profit target
            profit_target = getattr(self.settings, 'PROFIT_TARGET', 0.016)
            if entry_price and entry_price > 0:
                profit_pct = (price - entry_price) / entry_price
                if profit_pct >= profit_target:
                    should_exit = True
                    exit_reason = "profit_target"
            
            # 3. Stop loss
            stop_loss = getattr(self.settings, 'STOP_LOSS', 0.012)
            if entry_price and entry_price > 0:
                loss_pct = (entry_price - price) / entry_price
                if loss_pct >= stop_loss:
                    should_exit = True
                    exit_reason = "stop_loss"
            
            if should_exit:
                await self.exit_position(symbol, price, exit_reason)
            
        except Exception as e:
            logger.error(f"[AUTO-DISCOVERY] Error checking exit for {symbol}: {e}", exc_info=True)
    
    async def exit_position(self, symbol: str, price: float, reason: str):
        """Exit a position in a discovered symbol."""
        try:
            discovered = self.discovered_symbols.get(symbol)
            if not discovered or not discovered.entry_time:
                return
            
            entry_price = discovered.entry_price
            entry_time = discovered.entry_time
            hold_time = time.time() - entry_time
            
            # Calculate PnL
            if entry_price and entry_price > 0:
                price_change = (price - entry_price) / entry_price
                position_value = discovered.allocated_budget * 0.8
                pnl = price_change * position_value
                
                # Update stats
                discovered.cumulative_pnl += pnl
                discovered.total_trades += 1
                if pnl > 0:
                    discovered.winning_trades += 1
                
                # Record trade
                trade = {
                    'symbol': symbol,
                    'entry_price': entry_price,
                    'exit_price': price,
                    'pnl': pnl,
                    'hold_time': hold_time,
                    'reason': reason,
                    'timestamp': time.time()
                }
                self.closed_trades.append(trade)
                
                # Place exit order
                router = OmniRouter()
                # Calculate quantity (same as entry)
                position_value = discovered.allocated_budget * 0.8
                quantity = position_value / entry_price if entry_price > 0 else 0.0
                
                if self.settings.EXECUTION_ENABLED and quantity > 0:
                    order_result = await router.place_order(symbol, "SELL", "MARKET", quantity, price)
                    if order_result:
                        logger.info(f"[AUTO-DISCOVERY] [OK] Exited {symbol} @ ${price:.2f} | PnL: ${pnl:.2f} | Reason: {reason}")
                else:
                    logger.info(f"[AUTO-DISCOVERY] 🔮 SIMULATION: Would exit {symbol} @ ${price:.2f} | PnL: ${pnl:.2f} | Reason: {reason}")
                
                # Reset position
                discovered.entry_price = None
                discovered.entry_time = None
                discovered.unrealized_pnl = 0.0
            
        except Exception as e:
            logger.error(f"[AUTO-DISCOVERY] Error exiting position for {symbol}: {e}", exc_info=True)
    
    def get_global_opportunities(self) -> List[Dict[str, Any]]:
        """
        Get global opportunities from discovered symbols.
        
        Returns a list of opportunity dictionaries with symbol and strategy_fit_score.
        This method is used by the predictions API to get fit scores for symbols.
        """
        opportunities = []
        for symbol, discovered in self.discovered_symbols.items():
            if discovered.status == "active":
                opportunities.append({
                    'symbol': symbol,
                    'strategy_fit_score': discovered.strategy_fit_score,
                    'allocated_budget': discovered.allocated_budget,
                    'current_price': discovered.current_price,
                    'total_trades': discovered.total_trades,
                    'win_rate': discovered.winning_trades / discovered.total_trades if discovered.total_trades > 0 else 0.0,
                    'cumulative_pnl': discovered.cumulative_pnl,
                    'discovery_time': discovered.discovery_time
                })
        return opportunities
    
    def get_stats(self) -> Dict[str, Any]:
        """Get auto-discovery engine statistics."""
        total_pnl = sum(d.cumulative_pnl for d in self.discovered_symbols.values())
        total_trades = sum(d.total_trades for d in self.discovered_symbols.values())
        winning_trades = sum(d.winning_trades for d in self.discovered_symbols.values())
        win_rate = winning_trades / total_trades if total_trades > 0 else 0.0
        
        return {
            'discovered_symbols': len(self.discovered_symbols),
            'active_symbols': len([d for d in self.discovered_symbols.values() if d.status == "active"]),
            'total_pnl': total_pnl,
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'win_rate': win_rate,
            'symbols': {
                symbol: {
                    'strategy_fit_score': d.strategy_fit_score,
                    'allocated_budget': d.allocated_budget,
                    'total_trades': d.total_trades,
                    'win_rate': d.winning_trades / d.total_trades if d.total_trades > 0 else 0.0,
                    'cumulative_pnl': d.cumulative_pnl,
                    'status': d.status,
                    'discovery_time': datetime.fromtimestamp(d.discovery_time).isoformat() if d.discovery_time else None
                }
                for symbol, d in self.discovered_symbols.items()
            },
            'closed_trades': self.closed_trades[-20:]  # Last 20 trades
        }
    
    def get_internal_state(self) -> Dict[str, Any]:
        """Return a serializable snapshot of internal engine state for debugging."""
        try:
            return {
                "is_running": self.is_running,
                "discovered_symbols": list(self.discovered_symbols.keys()),
                "closed_trades_count": len(self.closed_trades),
                "last_discovery_time": self.last_discovery_time,
                "last_rebalance_time": self.last_rebalance_time,
                "whitelist_symbols_count": len(self.whitelist_symbols) if self.whitelist_symbols is not None else 0,
                "settings": {
                    "AUTO_DISCOVERY_ENABLED": getattr(self.settings, "AUTO_DISCOVERY_ENABLED", False),
                    "AUTO_DISCOVERY_MIN_SIGNAL": getattr(self.settings, "AUTO_DISCOVERY_MIN_SIGNAL", 0.7),
                    "AUTO_DISCOVERY_MAX_SYMBOLS": getattr(self.settings, "AUTO_DISCOVERY_MAX_SYMBOLS", 5),
                },
                "stats": self.get_stats()
            }
        except Exception as e:
            logger.debug(f"[AUTO-DISCOVERY] Error building internal state: {e}")
            return {"error": str(e)}

    def start(self):
        """Start the auto-discovery engine."""
        if not self.settings.AUTO_DISCOVERY_ENABLED:
            logger.info("[AUTO-DISCOVERY] Auto-discovery disabled in settings")
            return
        
        if self.is_running:
            logger.warning("[AUTO-DISCOVERY] Already running")
            return
        
        self.is_running = True
        self._task = asyncio.create_task(self.discovery_loop(), name="auto_discovery_engine")
        logger.info("[AUTO-DISCOVERY] Started discovery engine")
    
    def stop(self):
        """Stop the auto-discovery engine."""
        if not self.is_running:
            return
        
        self.is_running = False
        if self._task:
            self._task.cancel()
        logger.info("[AUTO-DISCOVERY] Stopped discovery engine")

# Singleton instance
_auto_discovery_instance: Optional[AutoDiscoveryEngine] = None

def get_auto_discovery_engine() -> AutoDiscoveryEngine:
    """Get or create the singleton AutoDiscoveryEngine instance."""
    global _auto_discovery_instance
    if _auto_discovery_instance is None:
        _auto_discovery_instance = AutoDiscoveryEngine()
    return _auto_discovery_instance

