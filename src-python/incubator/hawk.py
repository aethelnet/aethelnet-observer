import logging
import time
import numpy as np

logger = logging.getLogger("TheHawk")

class ArbitrageScanner:
    """
    The Hawk: Hunts for Latency Arbitrage Opportunities.
    Philosophy: "If the Crowd moves, the Laggard must follow."
    """
    def __init__(self):
        self.min_spread_pct = 0.5 # Minimum profit margin (Net of fees)
        
    def scan_for_laggards(self, snapshot: dict) -> list:
        """
        Analyzes a snapshot of prices from Watchtower.
        Returns a list of actionable opportunities.
        snapshot format: {'binance': 100, 'kraken': 99.5, 'median': 100}
        """
        if not snapshot or 'median' not in snapshot:
            return []
            
        median_price = snapshot['median']
        if median_price == 0: return []
        
        opportunities = []
        
        # We assume Median is "True Price"
        # If Exchange << Median, BUY Exchange
        # If Exchange >> Median, SELL Exchange
        
        for exchange, price in snapshot.items():
            if exchange == 'median' or exchange == 'consensus': continue
            if price <= 0: continue
            
            # Calculate Deviation
            deviation_pct = ((price - median_price) / median_price) * 100
            
            # CASE A: Exchange is LAGGING LOW (Cheap) -> BUY
            # Example: Median 100, Kraken 99. (-1%)
            if deviation_pct < -self.min_spread_pct:
                 opp = {
                     "type": "ARBITRAGE_BUY",
                     "target": exchange,
                     "price": price,
                     "true_value": median_price,
                     "est_profit": abs(deviation_pct)
                 }
                 opportunities.append(opp)
                 
            # CASE B: Exchange is LAGGING HIGH (Expensive) -> SELL
            # Example: Median 100, Kraken 101. (+1%)
            if deviation_pct > self.min_spread_pct:
                 opp = {
                     "type": "ARBITRAGE_SELL",
                     "target": exchange,
                     "price": price,
                     "true_value": median_price,
                     "est_profit": abs(deviation_pct)
                 }
                 opportunities.append(opp)
                 
        return opportunities

# Singleton
_hawk = None
def get_hawk():
    global _hawk
    if _hawk is None:
        _hawk = ArbitrageScanner()
    return _hawk
