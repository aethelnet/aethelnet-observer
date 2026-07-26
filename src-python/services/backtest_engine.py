import pandas as pd
import numpy as np
import time
from typing import Dict, Any, List

class BacktestEngine:
    """
    The Academy.
    Simulates the past to predict the future.
    """
    def __init__(self, strategy_class, initial_balance=10000.0):
        self.strategy_class = strategy_class
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.position = 0.0 # Size
        self.entry_price = 0.0
        self.trades = []
        self.equity_curve = []
        
    async def run(self, data: pd.DataFrame):
        """
        Executes the Time Machine.
        data: DataFrame with ['time', 'open', 'high', 'low', 'close', 'volume']
        """
        print(f"[ACADEMY] 🏛️ Class in session. Simulating {len(data)} candles...")
        
        # Instantiate fresh avatar
        avatar = self.strategy_class()
        
        # Simulation Loop
        for index, row in data.iterrows():
            price = float(row['close'])
            # Construct tick data
            tick = {
                'symbol': 'BTCUSDT', 
                'price': price,
                'volume': float(row['volume']),
                'timestamp': row['time'] if 'time' in row else index
            }
            
            # 1. Analyze
            try:
                signal = await avatar.analyze(tick)
            except Exception as e:
                # Strategies might fail on cold start logic, ignore
                signal = None
            
            # 2. Execute
            if signal:
                self._execute_sim(signal, price, index)
            
            # 3. Mark to Market
            equity = self.balance + (self.position * price)
            self.equity_curve.append(equity)
            
        print(f"[ACADEMY] 🎓 Simulation Complete. Trade Count: {len(self.trades)}")
        return self._generate_report()

    def _execute_sim(self, signal, price, timestamp):
        # Simplified Execution Logic
        # BUY
        if signal == "BUY" and self.position == 0:
            # Full Send (Simplistic)
            size = (self.balance * 0.99) / price # 99% to leave room for fees
            cost = size * price
            self.balance -= cost
            self.position = size
            self.entry_price = price
            self.trades.append({"side": "BUY", "price": price, "ts": timestamp})
            
        # SELL
        elif signal == "SELL" and self.position > 0:
            revenue = self.position * price
            self.balance += revenue
            pnl = (price - self.entry_price) * self.position
            self.position = 0
            self.trades.append({"side": "SELL", "price": price, "ts": timestamp, "pnl": pnl})

    def _generate_report(self):
        # Calculate final equity including open positions
        # Assuming last known price is required? 
        # But we don't have it easily here unless we store it.
        # Let's verify if 'equity_curve' has the last value.
        final_equity = self.equity_curve[-1] if self.equity_curve else self.balance
        
        return {
            "initial_balance": self.initial_balance,
            "final_balance": final_equity,
            "pnl": final_equity - self.initial_balance,
            "total_trades": len(self.trades),
            "win_rate": 0.0 # TODO
        }
