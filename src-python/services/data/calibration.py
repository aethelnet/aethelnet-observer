
import logging
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List

logger = logging.getLogger("Data.Calibration")

class UniverseCalibrator:
    def __init__(self, data_manager):
        self.dm = data_manager

    def calibrate(self, lookback_days: int = 2):
        """
        Calibrate the universe: Update symbol registry, volatility tags, and active status.
        Uses DataManager access for DB operations.
        """
        logger.info(f"Starting Universe Calibration (Lookback: {lookback_days}d)...")
        try:
            # Re-fetch registry from Binance/Yahoo first
            self.dm.update_symbol_registry()
            
            with self.dm.get_db() as session:
                from services.data.schema import SymbolRegistry, OHLCV
                
                # Get all symbols
                symbols = session.query(SymbolRegistry).all()
                total = len(symbols)
                logger.info(f"Analyzing {total} symbols for volatility/volume...")
                
                updates = 0
                cutoff = datetime.utcnow() - timedelta(days=lookback_days)
                
                for sym_obj in symbols:
                    sym = sym_obj.symbol
                    # Get recent data
                    candles = session.query(OHLCV).filter(
                        OHLCV.symbol == sym,
                        OHLCV.interval == '1h',
                        OHLCV.timestamp >= cutoff
                    ).order_by(OHLCV.timestamp.asc()).all()
                    
                    if not candles:
                        sym_obj.status = 'INACTIVE'
                        continue
                        
                    # Calculate Metrics
                    df = pd.DataFrame([{
                        'close': c.close,
                        'volume': c.volume, 
                        'high': c.high,
                        'low': c.low
                    } for c in candles])
                    
                    if len(df) < 5:
                        continue
                        
                    # Volatility (ATR-like or StdDev)
                    df['tr'] = df['high'] - df['low']
                    avg_tr = df['tr'].mean()
                    mean_price = df['close'].mean()
                    volatility_pct = (avg_tr / mean_price * 100) if mean_price else 0
                    
                    # Volume
                    avg_vol = df['volume'].mean() * mean_price # Dollar volume approx
                    
                    # Classification
                    status = 'ACTIVE'
                    category = sym_obj.category or 'UNKNOWN'
                    
                    # Sector Logic (Simplified)
                    if 'USDT' in sym:
                         if avg_vol > 1_000_000: category = 'MAJOR'
                         elif volatility_pct > 5.0: category = 'VOLATILE'
                    
                    sym_obj.status = status
                    # We usually don't overwrite sector if already set manually, but here we can tag
                    
                    updates += 1
                
                session.commit()
                logger.info(f"Calibration Complete. Updated {updates}/{total} symbols.")
                
        except Exception as e:
            logger.error(f"Calibration Failed: {e}")
