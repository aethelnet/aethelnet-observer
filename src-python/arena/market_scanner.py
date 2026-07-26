"""
Market Opportunity Scanner
Scans markets to find opportunities where the current strategy performs best.
Uses strategy metadata to match optimal conditions (volatility, regime, signals).
"""

import sqlite3
import pandas as pd
import numpy as np
import os
import sys
import logging
from typing import Dict, Any, List, Optional

# Add project root to path
sys.path.append(os.getcwd())

from arena.strategy_verifier import load_metadata, calculate_atr

logger = logging.getLogger("MarketScanner")


class MarketScanner:
    """
    Scans markets to find opportunities matching strategy's optimal regime.
    """
    
    def __init__(self):
        self.last_scan_time = 0.0
        self.scan_interval = 300.0  # 5 minutes
    
    def calculate_strategy_fit_score(
        self,
        symbol: str,
        price: float,
        volume: float,
        z_score: float,
        volatility: float,
        strategy_metadata: Optional[Dict[str, Any]]
    ) -> float:
        """
        Calculate how well a market matches the strategy's optimal conditions.
        
        Args:
            symbol: Trading symbol
            price: Current price
            volume: Current volume
            z_score: Market z-score (signal strength)
            volatility: Current volatility (ATR normalized)
            strategy_metadata: Strategy metadata with optimal_regime info
        
        Returns:
            Fit score (0-1, higher = better match)
        """
        if not strategy_metadata:
            # No metadata - use default scoring
            return 0.5
        
        optimal_regime = strategy_metadata.get('optimal_regime', 'normal')
        regime_perf = strategy_metadata.get('regime_performance', {})
        
        score = 0.0
        
        # 1. Volatility matching (40% weight)
        if optimal_regime == 'high_volatility':
            # Prefer high volatility
            vol_score = min(volatility / 0.05, 1.0)  # Normalize to 5% max
            score += vol_score * 0.4
        elif optimal_regime == 'low_volatility':
            # Prefer low volatility
            vol_score = 1.0 - min(volatility / 0.02, 1.0)  # Invert, normalize to 2% max
            score += vol_score * 0.4
        else:
            # Normal/crash - moderate volatility preferred
            vol_score = 1.0 - abs(volatility - 0.015) / 0.015  # Peak at 1.5%
            score += max(vol_score, 0.0) * 0.4
        
        # 2. Signal strength (30% weight)
        # Strong signals (high |z_score|) are generally better
        signal_score = min(abs(z_score) / 3.0, 1.0)  # Normalize to |z| = 3
        score += signal_score * 0.3
        
        # 3. Regime match (20% weight)
        # Check if current conditions match optimal regime
        current_regime = self._detect_current_regime(volatility, z_score)
        if current_regime == optimal_regime:
            score += 0.2
        elif self._are_regimes_compatible(current_regime, optimal_regime):
            score += 0.1
        
        # 4. Volume (10% weight) - ensure liquidity
        # Normalize volume (assuming $100M+ is excellent)
        vol_score = min(volume / 100_000_000.0, 1.0)
        score += vol_score * 0.1
        
        return min(score, 1.0)
    
    def _detect_current_regime(self, volatility: float, z_score: float) -> str:
        """
        Detect current market regime from volatility and z-score.
        
        Returns:
            Regime name: 'normal', 'crash', 'high_volatility', 'low_volatility'
        """
        # Crash: extreme negative z-score
        if z_score < -2.5:
            return 'crash'
        
        # High volatility: ATR > 2%
        if volatility > 0.02:
            return 'high_volatility'
        
        # Low volatility: ATR < 1%
        if volatility < 0.01:
            return 'low_volatility'
        
        # Normal otherwise
        return 'normal'
    
    def _are_regimes_compatible(self, current: str, optimal: str) -> bool:
        """
        Check if current regime is compatible with optimal regime.
        """
        # High volatility is compatible with crash (both volatile)
        if current == 'crash' and optimal == 'high_volatility':
            return True
        if current == 'high_volatility' and optimal == 'crash':
            return True
        
        # Normal and low volatility are somewhat compatible
        if current == 'normal' and optimal == 'low_volatility':
            return True
        if current == 'low_volatility' and optimal == 'normal':
            return True
        
        return False
    
    async def scan_opportunities(
        self,
        symbols: List[str],
        market_data: Dict[str, Dict[str, Any]],
        strategy_metadata: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Scan for trading opportunities matching strategy's optimal conditions.
        
        Args:
            symbols: List of symbols to scan
            market_data: Dict mapping symbol to {price, volume, z_score, volatility}
            strategy_metadata: Current strategy's metadata
        
        Returns:
            List of opportunities sorted by fit score (highest first)
        """
        opportunities = []
        
        for symbol in symbols:
            if symbol not in market_data:
                continue
            
            data = market_data[symbol]
            price = data.get('price', 0.0)
            volume = data.get('volume', 0.0)
            z_score = data.get('z_score', 0.0)
            volatility = data.get('volatility', 0.0)
            
            if price <= 0 or volume <= 0:
                continue
            
            # Calculate fit score
            fit_score = self.calculate_strategy_fit_score(
                symbol, price, volume, z_score, volatility, strategy_metadata
            )
            
            if fit_score > 0.5:  # Only report good matches
                opportunities.append({
                    'symbol': symbol,
                    'fit_score': fit_score,
                    'price': price,
                    'volume': volume,
                    'z_score': z_score,
                    'volatility': volatility,
                    'regime': self._detect_current_regime(volatility, z_score)
                })
        
        # Sort by fit score (highest first)
        opportunities.sort(key=lambda x: x['fit_score'], reverse=True)
        
        return opportunities
    
    def should_scan(self) -> bool:
        """
        Check if enough time has passed since last scan.
        """
        import time
        now = time.time()
        if now - self.last_scan_time >= self.scan_interval:
            self.last_scan_time = now
            return True
        return False


def get_market_scanner() -> MarketScanner:
    """Get singleton MarketScanner instance."""
    global _scanner_instance
    if '_scanner_instance' not in globals():
        _scanner_instance = MarketScanner()
    return _scanner_instance


def calculate_z_score(prices: pd.Series, window: int = 20) -> pd.Series:
    """Calculate z-score of price changes."""
    pct = prices.pct_change()
    roll_std = pct.rolling(window).std()
    z_scores = (pct / roll_std).fillna(0)
    return z_scores


def detect_regime(df: pd.DataFrame) -> str:
    """
    Detect current market regime based on volatility and price action.
    
    Args:
        df: DataFrame with OHLCV data
    
    Returns:
        Regime name: 'normal', 'crash', 'high_volatility', 'low_volatility'
    """
    if df.empty or len(df) < 20:
        return 'normal'
    
    # Calculate ATR
    atr_pct = calculate_atr(df)
    current_atr = atr_pct.iloc[-1] if len(atr_pct) > 0 else 0.0
    
    # Calculate recent price change
    closes = df['close']
    recent_pct = closes.pct_change().iloc[-1] if len(closes) > 1 else 0.0
    
    # Detect regime
    if recent_pct < -0.10:  # >10% drop
        return 'crash'
    elif current_atr > 2.0:  # High volatility
        return 'high_volatility'
    elif current_atr < 1.0:  # Low volatility
        return 'low_volatility'
    else:
        return 'normal'


def calculate_strategy_fit_score(
    symbol: str,
    strategy_metadata: Dict[str, Any],
    df: pd.DataFrame
) -> float:
    """
    Calculate how well the current market conditions match the strategy's optimal regime.
    
    Args:
        symbol: Trading symbol
        strategy_metadata: Strategy metadata with optimal_regime info
        df: DataFrame with recent market data
    
    Returns:
        Fit score (0-1, higher = better match)
    """
    if df.empty or len(df) < 20:
        return 0.0
    
    if not strategy_metadata:
        return 0.5
    
    optimal_regime = strategy_metadata.get('optimal_regime', 'normal')
    current_regime = detect_regime(df)
    
    # Base score: regime match
    regime_match = 1.0 if current_regime == optimal_regime else 0.3
    
    # Volatility match (if strategy prefers high/low vol)
    atr_pct = calculate_atr(df)
    current_atr = atr_pct.iloc[-1] if len(atr_pct) > 0 else 0.0
    
    volatility_score = 1.0
    if optimal_regime == 'high_volatility' and current_atr < 2.0:
        volatility_score = current_atr / 2.0  # Partial match
    elif optimal_regime == 'low_volatility' and current_atr > 1.0:
        volatility_score = max(0.0, 1.0 - (current_atr - 1.0))  # Penalty for high vol
    
    # Signal strength (z-score)
    closes = df['close']
    z_scores = calculate_z_score(closes)
    current_z = abs(z_scores.iloc[-1]) if len(z_scores) > 0 else 0.0
    
    # Higher z-score is better for most strategies (indicates movement)
    signal_score = min(1.0, current_z / 2.0)  # Normalize to 0-1
    
    # Composite score
    fit_score = (regime_match * 0.5) + (volatility_score * 0.3) + (signal_score * 0.2)
    
    return fit_score


def scan_opportunities(
    strategy_checkpoint: str,
    symbols: Optional[List[str]] = None,
    limit: int = 1000
) -> List[Dict[str, Any]]:
    """
    Scan markets for opportunities matching the strategy's optimal regime.
    
    Args:
        strategy_checkpoint: Path to checkpoint file (or checkpoint name)
        symbols: List of symbols to scan (if None, uses Tier 1 from universe)
        limit: Number of candles to load per symbol
    
    Returns:
        List of opportunities sorted by fit score (descending)
    """
    # Load strategy metadata
    checkpoint_path = strategy_checkpoint
    if not os.path.isabs(checkpoint_path):
        # Try to find in checkpoints directory
        checkpoints_dir = os.path.join(os.getcwd(), "checkpoints", "auto")
        full_path = os.path.join(checkpoints_dir, checkpoint_path)
        if not os.path.exists(full_path):
            full_path = os.path.join(os.getcwd(), "checkpoints", checkpoint_path)
        checkpoint_path = full_path
    
    metadata = load_metadata(checkpoint_path)
    if not metadata:
        logger.warning(f"No metadata found for {checkpoint_path}")
        return []
    
    optimal_regime = metadata.get('optimal_regime', 'normal')
    logger.info(f"Scanning for {optimal_regime} regime opportunities...")
    
    # Get symbols to scan
    if symbols is None:
        # Default to common Tier 1 symbols (can be expanded)
        symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'ADAUSDT',
                   'XRPUSDT', 'DOGEUSDT', 'DOTUSDT', 'MATICUSDT', 'AVAXUSDT']
    
    opportunities = []
    
    # Connect to database
    try:
        conn = sqlite3.connect('market_data.db')
        
        for symbol in symbols:
            try:
                # Load recent data for symbol
                query = f"""
                    SELECT open, high, low, close, volume, timestamp 
                    FROM ohlcv 
                    WHERE symbol = ? 
                    ORDER BY timestamp DESC 
                    LIMIT {limit}
                """
                df = pd.read_sql(query, conn, params=(symbol,))
                
                if df.empty:
                    continue
                
                # Sort ascending (oldest first)
                df = df.sort_values('timestamp').reset_index(drop=True)
                
                # Calculate fit score
                fit_score = calculate_strategy_fit_score(symbol, metadata, df)
                
                # Get current regime
                current_regime = detect_regime(df)
                
                # Calculate signal strength
                closes = df['close']
                z_scores = calculate_z_score(closes)
                current_z = z_scores.iloc[-1] if len(z_scores) > 0 else 0.0
                
                # Calculate ATR
                atr_pct = calculate_atr(df)
                current_atr = atr_pct.iloc[-1] if len(atr_pct) > 0 else 0.0
                
                opportunities.append({
                    'symbol': symbol,
                    'fit_score': round(fit_score, 3),
                    'current_regime': current_regime,
                    'optimal_regime': optimal_regime,
                    'z_score': round(current_z, 3),
                    'atr_pct': round(current_atr, 2),
                    'match': current_regime == optimal_regime
                })
                
            except Exception as e:
                logger.warning(f"Error scanning {symbol}: {e}")
                continue
        
        conn.close()
        
    except Exception as e:
        logger.error(f"Database error: {e}")
        return []
    
    # Sort by fit score (descending)
    opportunities.sort(key=lambda x: x['fit_score'], reverse=True)
    
    return opportunities


def scan_and_log_opportunities(
    strategy_checkpoint: str,
    min_fit_score: float = 0.5
) -> List[Dict[str, Any]]:
    """
    Scan opportunities and log results.
    Called periodically by LiveStrategyManager.
    
    Args:
        strategy_checkpoint: Path to checkpoint file
        min_fit_score: Minimum fit score to report
    
    Returns:
        List of filtered opportunities
    """
    opportunities = scan_opportunities(strategy_checkpoint)
    
    # Filter by minimum fit score
    filtered = [opp for opp in opportunities if opp['fit_score'] >= min_fit_score]
    
    if filtered:
        # Group by regime
        by_regime = {}
        for opp in filtered:
            regime = opp['current_regime']
            if regime not in by_regime:
                by_regime[regime] = []
            by_regime[regime].append(opp['symbol'])
        
        # Log summary
        for regime, symbols in by_regime.items():
            logger.info(f"Found {len(symbols)} {regime} opportunities: {', '.join(symbols)}")
            print(f"[SCANNER] Found {len(symbols)} {regime} opportunities: {', '.join(symbols)}")
    
    return filtered
