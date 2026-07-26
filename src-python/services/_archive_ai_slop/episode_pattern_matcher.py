"""
Episode Pattern Matcher: Learning from Successful Historical Episodes

Analyzes training data to identify market episodes where strategies performed well,
then matches current market conditions against these successful patterns to discover
symbols with similar characteristics.
"""

import logging
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import numpy as np

from services.database import get_database
from services.data_manager import get_data_manager
from services.brain import get_engine

logger = logging.getLogger("EpisodePatternMatcher")

@dataclass
class MarketEpisode:
    """Represents a market episode with its characteristics."""
    symbol: str
    start_time: float
    end_time: float
    entry_price: float
    exit_price: float
    pnl: float
    pnl_pct: float
    volatility: float
    avg_volume: float
    volume_trend: float  # -1 to 1 (decreasing to increasing)
    signal_strength: float  # Average z-score magnitude during episode
    regime: str  # Active, Stagnant, Crash/Panic
    momentum: float  # Price momentum during episode
    market_correlation: float = 0.0 # New: Correlation with market leader (BTC)
    global_regime: str = "Unknown" # New: Regime of market leader
    win: bool = False # Whether this was a winning trade

@dataclass
class EpisodePattern:
    """A pattern extracted from successful episodes."""
    pattern_id: str
    volatility_range: Tuple[float, float]  # (min, max)
    volume_range: Tuple[float, float]
    signal_strength_range: Tuple[float, float]
    regime: str
    momentum_range: Tuple[float, float]
    market_correlation_range: Tuple[float, float] = (-1.0, 1.0) # New: Correlation with leader
    global_regime_allowance: List[str] = field(default_factory=lambda: ["Any"]) # New: Allowed global regimes
    success_rate: float = 0.0  # How often this pattern leads to wins
    avg_pnl_pct: float = 0.0  # Average PnL when this pattern appears
    sample_count: int = 0  # Number of episodes matching this pattern

class EpisodePatternMatcher:
    """
    Analyzes historical trades to find successful market episodes,
    extracts patterns from those episodes, and matches current market
    conditions against these patterns.
    """
    
    
    def __init__(self):
        self.patterns: List[EpisodePattern] = []
        self.last_analysis_time = 0.0
        self.analysis_interval = 3600  # Re-analyze patterns every hour
        self.min_episodes_for_pattern = 1  # Learn from even a single victory (was 3)
        # Minimum PnL% threshold to consider an episode "successful"
        self.min_pnl_pct = 0.1 # Lowered from 0.5% to capture small scalps
        
        # HIPPOCAMPUS LOADING
        self.load_memory()
        
    def load_memory(self):
        """Restore learned patterns from the hippocampus (CLOUD database for persistence)."""
        try:
            import json
            from services.data.schema import LearnedPattern as LearnedPatternModel
            dm = get_data_manager()
            session = dm.CloudSession()
            
            try:
                rows = session.query(LearnedPatternModel).order_by(LearnedPatternModel.success_rate.desc()).all()
                
                loaded_patterns = []
                for r in rows:
                    try:
                        features = json.loads(r.features_range) if r.features_range else {}
                        p = EpisodePattern(
                            pattern_id=r.pattern_id,
                            regime=r.regime or 'Unknown',
                            success_rate=r.success_rate or 0.0,
                            sample_count=r.sample_count or 0,
                            avg_pnl_pct=features.get('avg_pnl_pct', 0.0),
                            volatility_range=tuple(features.get('volatility_range', (0,0))),
                            volume_range=tuple(features.get('volume_range', (0,0))),
                            signal_strength_range=tuple(features.get('signal_strength_range', (0,0))),
                            momentum_range=tuple(features.get('momentum_range', (0,0))),
                            market_correlation_range=tuple(features.get('market_correlation_range', (-1,1))),
                            global_regime_allowance=features.get('global_regime_allowance', ['Any'])
                        )
                        loaded_patterns.append(p)
                    except Exception as e:
                        logger.warning(f"Failed to hydrate pattern {r.pattern_id}: {e}")

                if loaded_patterns:
                    self.patterns = loaded_patterns
                    logger.info(f"[HIPPOCAMPUS] Restored {len(self.patterns)} learned patterns from CLOUD memory.")
                else:
                    logger.info("[HIPPOCAMPUS] Memory is clean. Tabula Rasa.")
            finally:
                session.close()
                
        except Exception as e:
            err_str = str(e).lower()
            if "no such table" in err_str or "does not exist" in err_str:
                logger.debug(f"[HIPPOCAMPUS] Cloud tables not yet created - starting with blank memory")
            else:
                logger.error(f"[HIPPOCAMPUS] Error loading memory: {e}")

    def persist_episodes(self, episodes: List[MarketEpisode]):
        """Store episodes (real or dreams) to CLOUD database for persistence."""
        try:
            import json
            from services.data.schema import MarketEpisode as MarketEpisodeModel
            dm = get_data_manager()
            session = dm.CloudSession()
            
            try:
                count = 0
                for ep in episodes:
                    features = {
                        "volatility": ep.volatility,
                        "regime": ep.regime,
                        "signal_strength": ep.signal_strength,
                        "momentum": ep.momentum,
                        "market_correlation": ep.market_correlation,
                        "global_regime": ep.global_regime,
                        "avg_volume": ep.avg_volume
                    }
                    
                    episode_record = MarketEpisodeModel(
                        symbol=ep.symbol,
                        start_ts=ep.start_time,
                        end_ts=ep.end_time,
                        pnl_pct=ep.pnl_pct,
                        is_theoretical=1 if ep.pnl == 0 else 0,
                        features=json.dumps(features)
                    )
                    session.add(episode_record)
                    count += 1
                
                session.commit()
                logger.info(f"[HIPPOCAMPUS] Persisted {count} episodes to CLOUD DB")
            finally:
                session.close()
        except Exception as e:
            err_str = str(e).lower()
            if "no such table" in err_str:
                logger.debug(f"[HIPPOCAMPUS] Episodes table not yet created - skipping persist")
            else:
                logger.error(f"Error persisting episodes: {e}")

    def persist_patterns(self):
        """Save current learned patterns to CLOUD database (Upsert)."""
        try:
            import json
            from sqlalchemy.dialects.postgresql import insert as pg_insert
            from services.data.schema import LearnedPattern as LearnedPatternModel
            dm = get_data_manager()
            session = dm.CloudSession()
            
            try:
                count = 0
                for p in self.patterns:
                    features = {
                        "volatility_range": p.volatility_range,
                        "volume_range": p.volume_range,
                        "signal_strength_range": p.signal_strength_range,
                        "momentum_range": p.momentum_range,
                        "market_correlation_range": p.market_correlation_range,
                        "global_regime_allowance": p.global_regime_allowance,
                        "avg_pnl_pct": p.avg_pnl_pct
                    }
                    
                    # Check if pattern exists
                    existing = session.query(LearnedPatternModel).filter_by(pattern_id=p.pattern_id).first()
                    
                    if existing:
                        # Update existing
                        existing.regime = p.regime
                        existing.success_rate = p.success_rate
                        existing.sample_count = p.sample_count
                        existing.features_range = json.dumps(features)
                        existing.updated_ts = time.time()
                    else:
                        # Insert new
                        new_pattern = LearnedPatternModel(
                            pattern_id=p.pattern_id,
                            regime=p.regime,
                            success_rate=p.success_rate,
                            sample_count=p.sample_count,
                            features_range=json.dumps(features),
                            updated_ts=time.time()
                        )
                        session.add(new_pattern)
                    count += 1
                
                session.commit()
                logger.info(f"[HIPPOCAMPUS] Persisted {count} patterns to CLOUD memory.")
            finally:
                session.close()
        except Exception as e:
            err_str = str(e).lower()
            if "no such table" in err_str or "does not exist" in err_str:
                logger.debug(f"[HIPPOCAMPUS] Cloud patterns table not yet created - skipping persist")
            else:
                logger.error(f"Error persisting patterns: {e}")

        
    async def analyze_historical_episodes(self, lookback_days: int = 30) -> List[MarketEpisode]:
        """
        Analyze historical trades to extract market episodes.
        Each trade represents an episode with its market conditions.
        """
        try:
            db = get_database()
            
            # Get trades from the last N days
            end_time = time.time()
            start_time = end_time - (lookback_days * 86400)
            
            trades = db.get_trades_between(None, start_time, end_time, limit=10000)
            
            if not trades:
                logger.debug("[EPISODE] No historical trades found")
                return []
            
            episodes = []
            
            # Group trades by symbol and extract episodes
            symbol_trades = {}
            for trade in trades:
                symbol = trade.get('symbol') or trade.get('ticker', 'UNKNOWN')
                if symbol not in symbol_trades:
                    symbol_trades[symbol] = []
                symbol_trades[symbol].append(trade)
            
            # Process each symbol's trades
            for symbol, trade_list in symbol_trades.items():
                # Sort by timestamp
                trade_list.sort(key=lambda t: t.get('ts', 0))
                
                # Extract episodes (each trade is an episode)
                for trade in trade_list:
                    episode = await self._extract_episode_from_trade(symbol, trade, start_time, end_time)
                    if episode:
                        episodes.append(episode)
            
            logger.info(f"[EPISODE] Extracted {len(episodes)} market episodes from {len(trades)} trades")
            return episodes
            
        except Exception as e:
            logger.error(f"[EPISODE] Error analyzing historical episodes: {e}", exc_info=True)
            return []

    async def analyze_theoretical_episodes(self, symbol: str, lookback_days: int = 30) -> List[MarketEpisode]:
        """
        Scans historical data for THEORETICAL trade opportunities.
        This solves the Cold Start problem by learning from "what could have happened".
        """
        try:
            db = get_database()
            dm = get_data_manager()
            
            # 1. Fetch History
            # We need high-res data (1h or 15m) to find precise entry points
            # For simplicity in this engine version, we use 1H candles
            end_time = time.time()
            start_time = end_time - (lookback_days * 86400)
            
            candles = dm.get_data(symbol, "1h", limit=lookback_days*24)
            if not candles or len(candles) < 50:
                logger.debug(f"[DREAMER] Not enough history for {symbol}")
                return []
                
            theoretical_episodes = []
            
            # 2. Re-construct Z-Score History (Simplified)
            # We use a moving window to simulate what the brain would have seen
            # Convert ORM objects to dicts if necessary
            candles = [c.__dict__ if hasattr(c, '__dict__') else c for c in candles]

            prices = [float(c['close']) for c in candles]
            
            window = 20
            for i in range(window, len(prices)-24): # Ensure we have room for outcome
                # Context Window
                window_prices = prices[i-window:i]
                current_price = prices[i]
                
                # Handle timestamp safely (dict or attribute)
                ts_raw = candles[i]['timestamp']
                
                if isinstance(ts_raw, datetime):
                     current_ts = ts_raw.timestamp()
                elif isinstance(ts_raw, str):
                    current_ts = datetime.fromisoformat(ts_raw.replace('Z', '+00:00')).timestamp()
                else: # Assume int or float
                    current_ts = float(ts_raw) / 1000.0 if float(ts_raw) > 3000000000 else float(ts_raw)
                
                mean = np.mean(window_prices)
                std = np.std(window_prices)
                
                if std == 0: continue
                
                z_score = (current_price - mean) / std
                
                # 3. Identify Signals (Theoretical Triggers)
                direction = None
                if z_score > 2.0:
                    direction = "SELL" # Mean Reversion Short
                elif z_score < -2.0:
                    direction = "BUY" # Mean Reversion Long
                    
                if direction:
                    # 4. Simulate Outcome (Active Hold for 6 hours)
                    # Simple strategy: Exit after 6 bars or if profit target hit
                    future_prices = prices[i+1:i+7] 
                    if not future_prices: continue
                    
                    exit_price = future_prices[-1]
                    pnl_pct = 0.0
                    
                    if direction == "BUY":
                        pnl_pct = (exit_price - current_price) / current_price
                    else:
                        pnl_pct = (current_price - exit_price) / current_price
                        
                    pnl_pct *= 100.0 # Convert to %
                    
                    # Only learn from WINNERS (Positive Reinforcement)
                    if pnl_pct > 0.5: # Min threshold
                        # 5. Extract Characteristics
                        # Reuse _get_market_conditions logic but pass static time
                        # Be efficient: pass pre-calced metrics if possible, but helper is async db bound
                        # For now, let's just construct the episode directly if we have data
                        
                        te = MarketEpisode(
                            symbol=symbol,
                            start_time=current_ts,
                            end_time=current_ts + (3600*6),
                            entry_price=current_price,
                            exit_price=exit_price,
                            pnl=0.0, # Virtual
                            pnl_pct=pnl_pct,
                            volatility=(std/mean)*100,
                            avg_volume=0.0, # Skip for speed or fetch from candle
                            volume_trend=0.0,
                            signal_strength=abs(z_score),
                            regime="Active" if ((std/mean)*100) > 1.5 else "Stagnant",
                            momentum=0.0,
                            market_correlation=0.0, # Skip cost
                            global_regime="Unknown",
                            win=True
                        )
                        theoretical_episodes.append(te)
            
            logger.info(f"[DREAMER] Synthesized {len(theoretical_episodes)} successful theoretical episodes for {symbol}")
            
            # MEMORY CONSOLIDATION (Hippocampus Write - Episodes)
            if theoretical_episodes:
                self.persist_episodes(theoretical_episodes)
                
            return theoretical_episodes
            
        except Exception as e:
            logger.error(f"[DREAMER] Theoretical analysis failed for {symbol}: {e}")
            return []
    
    async def _extract_episode_from_trade(self, symbol: str, trade: Dict, start_time: float, end_time: float) -> Optional[MarketEpisode]:
        """Extract market episode characteristics from a trade."""
        try:
            trade_ts = trade.get('ts', time.time())
            action = trade.get('action', '')
            price = float(trade.get('price', 0))
            quantity = float(trade.get('quantity', 0))
            metadata = trade.get('metadata', {})
            
            # Parse metadata if it's a string
            if isinstance(metadata, str):
                try:
                    import json
                    metadata = json.loads(metadata)
                except:
                    metadata = {}
            
            # Get PnL from metadata or calculate from price
            pnl = float(metadata.get('pnl', 0)) if metadata else 0.0
            pnl_pct = float(metadata.get('pnl_pct', 0)) if metadata else 0.0
            
            # If we don't have PnL, try to estimate from entry/exit
            if pnl == 0 and action in ['SELL', 'CLOSE']:
                # Try to find corresponding entry trade
                # For now, use a simple estimate
                pnl_pct = 0.0  # Will be calculated if we have entry/exit
            
            # Get market conditions around this trade time
            # Look at data 1 hour before and after the trade
            episode_start = trade_ts - 3600  # 1 hour before
            episode_end = trade_ts + 3600    # 1 hour after
            
            # Get market data for this period
            dm = get_data_manager()
            market_data = await self._get_market_conditions(symbol, episode_start, episode_end)
            
            # Determine if this was a winning trade
            win = pnl > 0 or pnl_pct > 0
            
            # --- GLOBAL CONTEXT AWARENESS ---
            # Fetch "King" Context (BTCUSDC)
            leader = "BTCUSDC"
            if symbol == "BTCUSDC": leader = "ETHUSDC" # If we are analyzing BTC, compare to ETH? Or just self (1.0)?
            
            global_ctx = await self._get_global_context(episode_start, episode_end, leader_symbol=leader)
            
            # Get symbol prices for correlation
            local_prices = [] # We need to fetch these from _get_market_conditions or do a separate fetch
            # Optimization: _get_market_conditions already fetches them but doesn't return them.
            # Let's trust the matcher to learn correlation if we just pass 0.0 for now, 
            # OR better: refactor _get_market_conditions to return prices.
            # For now, let's do a quick fetch to ensure quality
            sym_ticks = [t for t in get_database().get_history(symbol, limit=1000) if episode_start <= t[0] <= episode_end]
            local_prices = [float(t[1]) for t in sym_ticks if t[1] is not None]
            
            market_corr = self._calculate_correlation(local_prices, global_ctx.get("prices", []))
            global_regime = global_ctx.get("regime", "Unknown")
            
            if symbol == "BTCUSDC": market_corr = 1.0 # Self-correlation
            
            episode = MarketEpisode(
                symbol=symbol,
                start_time=episode_start,
                end_time=episode_end,
                entry_price=price,  # Simplified - ideally we'd track entry separately
                exit_price=price,
                pnl=pnl,
                pnl_pct=pnl_pct,
                volatility=market_data.get('volatility', 0.0),
                avg_volume=market_data.get('avg_volume', 0.0),
                volume_trend=market_data.get('volume_trend', 0.0),
                signal_strength=market_data.get('signal_strength', 0.0),
                regime=market_data.get('regime', 'Unknown'),
                momentum=market_data.get('momentum', 0.0),
                market_correlation=market_corr,
                global_regime=global_regime,
                win=win
            )
            
            return episode
            
        except Exception as e:
            logger.debug(f"[EPISODE] Error extracting episode from trade: {e}")
            return None
    
    async def _get_market_conditions(self, symbol: str, start_time: float, end_time: float) -> Dict[str, Any]:
        """Get market conditions (volatility, volume, signals) for a time period."""
        try:
            db = get_database()
            
            # Get market ticks for this period (use get_history and filter)
            all_ticks = db.get_history(symbol, limit=10000)
            ticks = [t for t in all_ticks if start_time <= t[0] <= end_time]
            
            if not ticks:
                return {
                    'volatility': 0.0,
                    'avg_volume': 0.0,
                    'volume_trend': 0.0,
                    'signal_strength': 0.0,
                    'regime': 'Unknown',
                    'momentum': 0.0
                }
            
            # Ticks are tuples: (timestamp, price, volume, is_buyer_maker)
            prices = [float(t[1]) for t in ticks if len(t) > 1 and t[1] is not None]
            volumes = [float(t[2]) for t in ticks if len(t) > 2 and t[2] is not None]
            
            # Calculate volatility (std of returns)
            volatility = 0.0
            if len(prices) > 1:
                returns = np.diff(prices) / prices[:-1]
                volatility = float(np.std(returns)) * 100  # Convert to percentage
            
            # Average volume
            avg_volume = float(np.mean(volumes)) if volumes else 0.0
            
            # Volume trend (increasing or decreasing)
            volume_trend = 0.0
            if len(volumes) > 1:
                # Simple linear trend
                x = np.arange(len(volumes))
                if np.std(x) > 0:
                    trend = np.polyfit(x, volumes, 1)[0]
                    volume_trend = np.tanh(trend / (avg_volume + 1))  # Normalize to -1 to 1
            
            # Get signals for this period
            signals = db.get_signals_since(symbol, start_time, limit=1000)
            # Filter to period
            signals = [s for s in signals if start_time <= s.get('ts', 0) <= end_time]
            signal_strength = 0.0
            if signals:
                signal_values = [abs(float(s.get('signal_value', 0))) for s in signals]
                signal_strength = float(np.mean(signal_values)) if signal_values else 0.0
            
            # Determine regime from volatility
            if volatility > 5.0:
                regime = "Crash/Panic"
            elif volatility > 1.5:
                regime = "Active"
            else:
                regime = "Stagnant"
            
            # Calculate momentum (price change over period)
            momentum = 0.0
            if len(prices) > 1:
                price_change = (prices[-1] - prices[0]) / prices[0] if prices[0] > 0 else 0.0
                momentum = float(price_change * 100)  # Convert to percentage
            
            return {
                'volatility': volatility,
                'avg_volume': avg_volume,
                'volume_trend': volume_trend,
                'signal_strength': signal_strength,
                'regime': regime,
                'momentum': momentum,
            }
            
        except Exception as e:
            logger.debug(f"[EPISODE] Error getting market conditions: {e}")
            return {
                'volatility': 0.0,
                'avg_volume': 0.0,
                'volume_trend': 0.0,
                'signal_strength': 0.0,
                'regime': 'Unknown',
                'momentum': 0.0
            }
    
    async def _get_global_context(self, start_time: float, end_time: float, leader_symbol: str = "BTCUSDC") -> Dict[str, Any]:
        """
        Get the global market context (Leader Regime & Prices for correlation).
        """
        try:
            db = get_database()
            # Fetch leader ticks
            all_ticks = db.get_history(leader_symbol, limit=10000)
            ticks = [t for t in all_ticks if start_time <= t[0] <= end_time]
            
            prices = [float(t[1]) for t in ticks if len(t) > 1 and t[1] is not None]
            
            # Determine Global Regime (Simplified for historical lookup)
            # ideally we'd look up historical regime directly, but recalculating from volatility is safer for now
            regime = "Unknown"
            if len(prices) > 1:
                returns = np.diff(prices) / prices[:-1]
                volatility = float(np.std(returns)) * 100
                if volatility > 5.0: regime = "Crash/Panic"
                elif volatility > 1.5: regime = "Active"
                else: regime = "Stagnant"
                
            return {
                "prices": prices, # For correlation calc
                "regime": regime
            }
        except Exception:
            return {"prices": [], "regime": "Unknown"}

    def _calculate_correlation(self, prices_a: List[float], prices_b: List[float]) -> float:
        """Calculate Pearson correlation between two price series."""
        try:
            if not prices_a or not prices_b: return 0.0
            
            # Interpolate to matching length if needed (simple resampling)
            len_a, len_b = len(prices_a), len(prices_b)
            if len_a < 2 or len_b < 2: return 0.0
            
            target_len = min(len_a, len_b)
            
            # Resample strictly to min length
            pa = np.array(prices_a)
            pb = np.array(prices_b)
            
            # Use simple truncation for speed (assuming roughly synced timestamps)
            # For rigor, we should align by timestamp, but this is an approximation
            pa = pa[:target_len]
            pb = pb[:target_len]
            
            corr = np.corrcoef(pa, pb)[0, 1]
            if np.isnan(corr): return 0.0
            return float(corr)
        except Exception:
            return 0.0
    
    def extract_patterns(self, episodes: List[MarketEpisode]) -> List[EpisodePattern]:
        """
        Extract patterns from successful episodes.
        Groups episodes by similar characteristics and identifies successful patterns.
        """
        if not episodes:
            return []
        
        # Filter to winning episodes only using configurable threshold
        winning_episodes = [e for e in episodes if e.win and e.pnl_pct > self.min_pnl_pct]
        
        if len(winning_episodes) < self.min_episodes_for_pattern:
            logger.debug(f"[EPISODE] Not enough winning episodes ({len(winning_episodes)}) to extract patterns (min_required={self.min_episodes_for_pattern})")
            return []
        
        patterns = []
        
        # Group episodes by regime first
        regime_groups = {}
        for episode in winning_episodes:
            regime = episode.regime
            if regime not in regime_groups:
                regime_groups[regime] = []
            regime_groups[regime].append(episode)
        
        # Extract patterns for each regime
        pattern_id = 0
        for regime, regime_episodes in regime_groups.items():
            if len(regime_episodes) < self.min_episodes_for_pattern:
                continue
            
            # Calculate ranges for this regime's successful episodes
            volatilities = [e.volatility for e in regime_episodes]
            volumes = [e.avg_volume for e in regime_episodes]
            signals = [e.signal_strength for e in regime_episodes]
            momentums = [e.momentum for e in regime_episodes]
            correlations = [e.market_correlation for e in regime_episodes]
            
            # Determine allowed global regimes (if >80% of wins share a regime, enforce it)
            g_regimes = [e.global_regime for e in regime_episodes]
            from collections import Counter
            common_g = Counter(g_regimes).most_common(1)
            
            allowed_globals = ["Any"]
            if common_g and common_g[0][1] / len(regime_episodes) > 0.8:
                allowed_globals = [common_g[0][0]]
            
            # Create pattern with ranges (use percentiles to avoid outliers)
            pattern = EpisodePattern(
                pattern_id=f"pattern_{pattern_id}",
                volatility_range=(
                    float(np.percentile(volatilities, 10)),  # 10th percentile
                    float(np.percentile(volatilities, 90))       # 90th percentile
                ),
                volume_range=(
                    float(np.percentile(volumes, 10)),
                    float(np.percentile(volumes, 90))
                ),
                signal_strength_range=(
                    float(np.percentile(signals, 10)),
                    float(np.percentile(signals, 90))
                ),
                regime=regime,
                momentum_range=(
                    float(np.percentile(momentums, 10)),
                    float(np.percentile(momentums, 90))
                ),
                market_correlation_range=(
                    float(np.percentile(correlations, 10)),
                    float(np.percentile(correlations, 90))
                ),
                global_regime_allowance=allowed_globals,
                success_rate=1.0,  # All episodes in this group are winners
                avg_pnl_pct=float(np.mean([e.pnl_pct for e in regime_episodes])),
                sample_count=len(regime_episodes)
            )
            
            patterns.append(pattern)
            pattern_id += 1
        
        # Also create cross-regime patterns for high-performing episodes
        # Find episodes with very high PnL (>2%)
        high_pnl_episodes = [e for e in winning_episodes if e.pnl_pct > 2.0]
        if len(high_pnl_episodes) >= self.min_episodes_for_pattern:
            volatilities = [e.volatility for e in high_pnl_episodes]
            volumes = [e.avg_volume for e in high_pnl_episodes]
            signals = [e.signal_strength for e in high_pnl_episodes]
            momentums = [e.momentum for e in high_pnl_episodes]
            correlations = [e.market_correlation for e in high_pnl_episodes]
            
            pattern = EpisodePattern(
                pattern_id=f"pattern_high_pnl_{pattern_id}",
                volatility_range=(
                    float(np.percentile(volatilities, 10)),
                    float(np.percentile(volatilities, 90))
                ),
                volume_range=(
                    float(np.percentile(volumes, 10)),
                    float(np.percentile(volumes, 90))
                ),
                signal_strength_range=(
                    float(np.percentile(signals, 10)),
                    float(np.percentile(signals, 90))
                ),
                regime="Any",  # Cross-regime pattern
                momentum_range=(
                    float(np.percentile(momentums, 10)),
                    float(np.percentile(momentums, 90))
                ),
                market_correlation_range=(
                    float(np.percentile(correlations, 10)),
                    float(np.percentile(correlations, 90))
                ),
                global_regime_allowance=["Any"], # High PnL wins often defy gravity
                success_rate=1.0,
                avg_pnl_pct=float(np.mean([e.pnl_pct for e in high_pnl_episodes])),
                sample_count=len(high_pnl_episodes)
            )
            
            patterns.append(pattern)
        
        logger.info(f"[EPISODE] Extracted {len(patterns)} successful patterns from {len(winning_episodes)} winning episodes")
        return patterns
    
    def match_pattern(self, symbol: str, volatility: float, volume: float, signal_strength: float, 
                     regime: str, momentum: float, global_context: Dict = None) -> float:
        """
        Match current market conditions against learned patterns.
        Returns a score (0-1) indicating how well current conditions match successful patterns.
        global_context: {'regime': str, 'correlation': float}
        """
        if not self.patterns:
            return 0.0
            
        # Defaults if no context
        current_g_regime = global_context.get("regime", "Unknown") if global_context else "Unknown"
        current_corr = global_context.get("correlation", 0.0) if global_context else 0.0
        
        best_match_score = 0.0
        
        for pattern in self.patterns:
            # Check if regime matches (or pattern accepts any regime)
            if pattern.regime != "Any" and pattern.regime != regime:
                continue
            
            # Check Global Regime Compliance
            if "Any" not in pattern.global_regime_allowance:
                 if current_g_regime not in pattern.global_regime_allowance:
                     continue
            
            # Calculate match score for each dimension
            vol_match = self._range_match(volatility, pattern.volatility_range)
            vol_match_vol = self._range_match(volume, pattern.volume_range)
            sig_match = self._range_match(signal_strength, pattern.signal_strength_range)
            mom_match = self._range_match(momentum, pattern.momentum_range)
            
            # New: Correlation Match
            corr_match = self._range_match(current_corr, pattern.market_correlation_range)
            
            # Weighted average (signal strength and correlation are key)
            match_score = (
                vol_match * 0.15 +
                vol_match_vol * 0.15 +
                sig_match * 0.3 +
                mom_match * 0.15 +
                corr_match * 0.25  # Correlation is a strong factor
            )
            
            # Context-Aware Penalty Limiters
            # If the pattern demands a specific global regime and we aren't in it, PUNISH severely.
            # (Allows for 'Any' which was skipped above, but if it was not Any and matched, we are good)
            # However, logic above already skips if not in allowance.
            
            # If Correlation is VERY different (e.g. pattern expects >0.8 and we have -0.9),
            # the _range_match only gives 0. But weighted average might still be 0.75.
            # We need a MULTIPLIER penalty for fundamental regime violations.
            
            # 1. Correlation Polarity Check
            # If pattern expects strong positive (>0.5) and we are negative, kill the score.
            pat_min_corr, pat_max_corr = pattern.market_correlation_range
            if pat_min_corr > 0.5 and current_corr < 0.0:
                match_score *= 0.1 # Severe penalty for polarity mismatch
            elif pat_max_corr < -0.5 and current_corr > 0.0:
                 match_score *= 0.1
            
            # 2. Global Regime Strictness
            # If pattern is built on "Crash/Panic" and we are "Active", reduce confidence
            # (Already filtered by allowance list, but if allowed, check alignment)
            pass 
            
            
            # Boost score by pattern's success rate and sample count
            confidence_boost = pattern.success_rate * min(1.0, pattern.sample_count / 10.0)
            match_score *= confidence_boost
            
            if match_score > best_match_score:
                best_match_score = match_score
        
        return min(1.0, best_match_score)
    
    def _range_match(self, value: float, range_tuple: Tuple[float, float]) -> float:
        """Calculate how well a value matches a range (0-1)."""
        min_val, max_val = range_tuple
        if min_val == max_val:
            return 1.0 if value == min_val else 0.0
        
        if value < min_val or value > max_val:
            # Outside range - calculate distance penalty
            if value < min_val:
                distance = min_val - value
                range_size = max_val - min_val
            else:
                distance = value - max_val
                range_size = max_val - min_val
            
            # Exponential decay based on distance
            penalty = np.exp(-distance / (range_size + 0.1))
            return max(0.0, penalty)
        else:
            # Inside range - perfect match
            return 1.0
    
    async def update_patterns(self, force: bool = False, include_theoretical: bool = False):
        """Update patterns from historical data."""
        current_time = time.time()
        
        if not force and (current_time - self.last_analysis_time) < self.analysis_interval:
            return  # Too soon to re-analyze
        
        logger.info("[EPISODE] Analyzing historical episodes to update patterns...")
        
        # 1. Real Episodes (Trades)
        episodes = await self.analyze_historical_episodes(lookback_days=30)
        
        # 2. Theoretical Episodes (Dreams)
        # Only if forced or explicitly requested (expensive)
        if force or include_theoretical:
             # Scan a few key assets
             targets = ["BTCUSDC", "ETHUSDC", "SOLUSDC", "GC=F"]
             theory_eps = []
             for t in targets:
                 eps = await self.analyze_theoretical_episodes(t, lookback_days=30)
                 theory_eps.extend(eps)
             
             episodes.extend(theory_eps)
        
        if episodes:
            self.patterns = self.extract_patterns(episodes)
            self.last_analysis_time = current_time
            logger.info(f"[EPISODE] Updated patterns: {len(self.patterns)} patterns learned (Real+Theoretical)")
            
            # MEMORY CONSOLIDATION (Hippocampus Write)
            self.persist_patterns()
        else:
            logger.warning("[EPISODE] No episodes found - patterns not updated")
    
    def get_pattern_summary(self) -> Dict[str, Any]:
        """Get summary of learned patterns."""
        return {
            'pattern_count': len(self.patterns),
            'patterns': [
                {
                    'id': p.pattern_id,
                    'regime': p.regime,
                    'success_rate': p.success_rate,
                    'avg_pnl_pct': p.avg_pnl_pct,
                    'sample_count': p.sample_count,
                    'volatility_range': p.volatility_range,
                    'signal_strength_range': p.signal_strength_range
                }
                for p in self.patterns
            ],
            'last_analysis': datetime.fromtimestamp(self.last_analysis_time).isoformat() if self.last_analysis_time > 0 else None
        }

# Singleton instance
_pattern_matcher_instance: Optional[EpisodePatternMatcher] = None

def get_episode_pattern_matcher() -> EpisodePatternMatcher:
    """Get or create the singleton EpisodePatternMatcher instance."""
    global _pattern_matcher_instance
    if _pattern_matcher_instance is None:
        _pattern_matcher_instance = EpisodePatternMatcher()
    return _pattern_matcher_instance

