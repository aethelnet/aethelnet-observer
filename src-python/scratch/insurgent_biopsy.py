import asyncio
import pandas as pd
import numpy as np
import logging
from services.brain_full import BrainEngine
from services.brain import get_engine
from arena.manager import LiveStrategyManager

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("InsurgentBiopsy")

async def run_biopsy():
    print("\n--- FORENSIC BIOPSY: SOVEREIGN INSURGENT ---")
    
    # 1. Initialize Engines
    brain = BrainEngine()
    manager = LiveStrategyManager()
    
    # 2. Setup Symbols to Test
    symbols = ["DOGEUSDT", "BTCUSDT", "ETHUSDT"]
    
    for symbol in symbols:
        print(f"\n[TARGET: {symbol}]")
        
        # 3. Simulate "Fresh" Market State (Mocking last 100 ticks)
        # In a real biopsy we would fetch from DB, but for speed we generate realistic jitter
        data = pd.DataFrame({
            'close': [0.10 + (i * 0.0001) + (np.random.normal(0, 0.0005)) for i in range(100)],
            'volume': [1000] * 100
        })
        
        # 4. Get Prophet's Base Vision
        soul_val = brain.get_sovereign_signal(data)
        
        # 5. Get Specialist Arena Votes
        state = brain.states.get(symbol, {})
        votes_result = manager.get_strategy_ensemble_vote(state)
        votes = votes_result.get('council_votes', {})
        
        # 6. Calculate Sovereign Insurgent Fusion (The New Code)
        specialist_delta = 0.0
        logic_signal = state.get('logic_signal', 0)
        
        insurgent_report = []
        for strategy, conf in votes.items():
            s_dir = state.get(f'signal_{strategy}', logic_signal)
            contribution = (conf ** 2) * 5.0 * s_dir
            specialist_delta += contribution
            if conf > 0.05:
                insurgent_report.append(f"  > {strategy}: Dom={conf*100:.1f}% | Contrib={contribution:+.3f}")

        # Final Fusion (70/30)
        boosted_soul = (soul_val * 0.7) + (specialist_delta * 0.3)
        
        # Results
        print(f"Prophet Base (70%): {soul_val:+.4f}")
        print(f"Insurgent Delta (30%): {specialist_delta:+.4f}")
        print(f"FINAL FUSION:        {boosted_soul:+.4f}")
        
        if insurgent_report:
            print("Specialist Detail:")
            for line in insurgent_report:
                print(line)
        
        # Analysis
        if abs(boosted_soul) > abs(soul_val):
            print("RESULT: RESONANCE. The specialists are AMPLIFYING the Prophet.")
        elif (boosted_soul * soul_val) < 0:
            print("RESULT: OVERRIDE! The specialists have REVERSED the Prophet's course.")
        else:
            print("RESULT: DAMPENING. The specialists are BRAKING for safety.")

if __name__ == "__main__":
    asyncio.run(run_biopsy())
