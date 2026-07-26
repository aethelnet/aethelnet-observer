import logging
import time
from typing import Dict
from brokers.router import OmniRouter

logger = logging.getLogger("LiquidityManager")

class LiquidityManager:
    """
    Manages portfolio allocation suggestions and liquidity health checks.

    Monitors aggregated balances across brokers and suggests rebalancing actions.
    This component currently emits suggestions (no automated transfers).
    """
    def __init__(self):
        self.target_allocation = {
            'crypto': 0.7, # 70% Growth
            'stocks': 0.3  # 30% Stability
        }
        self.rebalance_threshold = 0.05 # 5% Drift triggers action
        self.last_check = 0
        
    async def run_check(self, router: OmniRouter):
        """
        Periodic heartbeat to check liquidity health.
        """
        now = time.time()
        if now - self.last_check < 60: # Check every 1 min
            return
            
        self.last_check = now
        
        # 1. Fetch Balances
        crypto_bal = 0.0
        stock_bal = 0.0
        
        # Crypto (Binance Spot + Futures)
        if 'binance_spot' in router.brokers:
            crypto_bal += await router.brokers['binance_spot'].get_balance('USDT')
        if 'binance_future' in router.brokers:
            crypto_bal += await router.brokers['binance_future'].get_balance('USDT')
            
        # Stocks (Alpaca)    
        if 'alpaca' in router.brokers:
            stock_bal = await router.brokers['alpaca'].get_balance('USD')
            
        total = crypto_bal + stock_bal
        if total == 0: return

        # 2. Check Drift
        crypto_pct = crypto_bal / total
        stock_pct = stock_bal / total
        
        diff = crypto_pct - self.target_allocation['crypto']
        
        if abs(diff) > self.rebalance_threshold:
            logger.info("⚖️ LIQUIDITY IMBALANCE DETECTED ⚖️")
            logger.info(f"Current: {crypto_pct*100:.1f}% Crypto / {stock_pct*100:.1f}% Stocks")
            logger.info(f"Target:  {self.target_allocation['crypto']*100:.1f}% Crypto / {self.target_allocation['stocks']*100:.1f}% Stocks")
            
            amount_to_move = abs(diff) * total
            
            if diff > 0:
                # Crypto Overweight -> Move to Stocks
                logger.info(f"👉 SUGGESTION: Withdraw ${amount_to_move:.2f} from Binance -> Deposit to Alpaca")
            else:
                # Stocks Overweight -> Move to Crypto
                logger.info(f"👉 SUGGESTION: Withdraw ${amount_to_move:.2f} from Alpaca -> Deposit to Binance")
                
            # Note: Automatic ACH transfers are Phase 50 (Banking Integration).
            # For PAPER mode, we could virtually move it.
            
    def set_allocation(self, crypto_pct: float):
        self.target_allocation['crypto'] = crypto_pct
        self.target_allocation['stocks'] = 1.0 - crypto_pct
        logger.info(f"[TREASURY] Allocation Target Updated: {crypto_pct*100}% Crypto")

# Global Instance
liquidity_manager = LiquidityManager()
def get_liquidity_manager():
    return liquidity_manager
