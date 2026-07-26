import optuna
import json
import os
import numpy as np
import sys
from ..services.brain import ProphitEngine
from .galaxy import MarketGalaxy

def objective(trial):
    # 1. Suggest Hyperparameters
    config = {
        'decay': trial.suggest_float('decay', 0.5, 0.99),
        'base_drag': trial.suggest_float('base_drag', 0.1, 0.9),
        'base_spring': trial.suggest_float('base_spring', 0.0001, 0.05, log=True),
        # Resource-Based Params
        'pca_window': trial.suggest_int('pca_window', 20, 100),
        # GMM is internal to engine, but we could tune it if we exposed it
    }
    
    # 2. Setup Engine & Galaxy
    engine = ProphitEngine()
    # Inject config (hacky since engine usually takes config in compute_projection)
    # We'll pass it during the loop
    
    galaxy = MarketGalaxy()
    
    # 3. Run Simulation (Fast)
    mse_sum = 0.0
    count = 0
    
    # Warmup
    for _ in range(50):
        galaxy.step([])
        state = galaxy.get_state()
        engine.ingest_candle(state['CORE']['time'], state['CORE']['price'], 100)
        
    # Test
    for _ in range(100):
        galaxy.step([])
        state = galaxy.get_state()
        true_price = state['CORE']['price']
        
        # Predict *before* ingesting current
        proj = engine.compute_projection(lookahead=5, config=config)
        
        if proj:
            pred_price = proj['prices'][4] if len(proj['prices']) > 4 else proj['prices'][-1]
            mse_sum += (pred_price - true_price) ** 2
            count += 1
            
        engine.ingest_candle(state['CORE']['time'], true_price, 100)
        
    if count == 0: return float('inf')
    return mse_sum / count

def main():
    print("--- STARTING PREDICTION OPTIMIZATION (OPTUNA) ---")
    study = optuna.create_study(direction='minimize')
    study.optimize(objective, n_trials=100) # Fast run
    
    print("Best params:", study.best_params)
    
    # Save
    os.makedirs('backend/data', exist_ok=True)
    with open('backend/data/best_brain.json', 'w') as f:
        json.dump(study.best_params, f, indent=2)

if __name__ == "__main__":
    main()
