import time
import random
from .market import Market, MarketEra
from .traders.simple import TitForTatTrader, RiskAverseTrader
from .traders.expert import HFTTrader, ChaosTrader

class Arena:
    def __init__(self):
        self.market = Market()
        self.traders = []
        self.tick_count = 0
        
    def register_trader(self, trader):
        self.traders.append(trader)
        
    def setup_default_arena(self):
        """
        Populate arena with a mix of traders.
        """
        self.traders = []
        # 3 Simple Traders
        self.register_trader(TitForTatTrader("Alice"))
        self.register_trader(TitForTatTrader("Bob"))
        self.register_trader(RiskAverseTrader("Carol"))
        
        # 2 Expert Traders
        self.register_trader(HFTTrader("QuantX"))
        self.register_trader(ChaosTrader("Joker"))
        
    def run(self, ticks=1000):
        print(f"--- STARTING ARENA SIMULATION ({ticks} ticks) ---")
        
        for i in range(ticks):
            self.tick_count += 1
            
            # 1. Era Control (Director)
            if i == 200:
                print(">>> ERA CHANGE: BOOM")
                self.market.set_era(MarketEra.BOOM)
            elif i == 500:
                print(">>> ERA CHANGE: CRASH")
                self.market.set_era(MarketEra.CRASH)
            elif i == 700:
                print(">>> ERA CHANGE: CHAOS")
                self.market.set_era(MarketEra.CHAOS)
            elif i == 900:
                print(">>> ERA CHANGE: STAGNATION")
                self.market.set_era(MarketEra.STAGNATION)
                
            # 2. Get Market State
            state = self.market.get_state()
            current_price = state['price']
            
            # 3. Collect Orders
            orders = []
            for trader in self.traders:
                if trader.is_bankrupt: continue
                
                try:
                    decision = trader.decide(state)
                    if decision['side'] != 'hold':
                        # Execute logic (simplified, immediate fill)
                        # In real matching engine, this is complex.
                        # Here we just log the intent and let market process impact.
                        orders.append({
                            'side': decision['side'], 
                            'size': decision['size'],
                            'trader': trader
                        })
                        
                        # Update Trader Portfolio (Assuming fill at current price for simplicity)
                        # Realistically, fill price would be post-impact.
                        # We'll update portfolio AFTER market step to use new price?
                        # No, let's assume fill at 'current' price but market moves for 'next' tick.
                        trader.execute_trade(decision['side'], decision['size'], current_price)
                        
                except Exception as e:
                    print(f"Trader {trader.name} crashed: {e}")
            
            # 4. Evolve Market
            market_step = self.market.step(orders)
            new_price = market_step['price']
            
            # 5. Update PnL
            for trader in self.traders:
                trader.update_portfolio(new_price)
                
            # Logging
            if i % 100 == 0:
                print(f"Tick {i}: Price {new_price:.2f} | Era {state['era'].value}")
                
        self.report_results()
        
    def report_results(self):
        print("\n--- SIMULATION RESULTS ---")
        print(f"Final Price: {self.market.price:.2f}")
        
        # Rank Traders
        ranked = sorted(self.traders, key=lambda t: t.pnl_history[-1], reverse=True)
        
        print(f"{'RANK':<5} {'NAME':<15} {'BALANCE':<12} {'INVENTORY':<10} {'PnL':<10}")
        print("-" * 60)
        
        for i, t in enumerate(ranked):
            pnl = t.pnl_history[-1]
            status = " (BANKRUPT)" if t.is_bankrupt else ""
            print(f"{i+1:<5} {t.name:<15} {t.balance:<12.2f} {t.inventory:<10.2f} {pnl:<10.2f}{status}")

if __name__ == "__main__":
    arena = Arena()
    arena.setup_default_arena()
    arena.run(1000)
