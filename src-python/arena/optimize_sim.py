import optuna
import json
import os
import numpy as np
from .galaxy import MarketGalaxy

def higuchi_fd(x, kmax=10):
    """
    Calculate Higuchi Fractal Dimension.
    """
    x = np.array(x)
    N = len(x)
    L = []
    x_series = []
    
    for k in range(1, kmax + 1):
        Lk = []
        for m in range(k):
            Lmk = 0
            for i in range(1, int((N - m) / k)):
                Lmk += abs(x[m + i * k] - x[m + (i - 1) * k])
            Lmk = Lmk * (N - 1) / (((N - m) / k) * k) / k
            Lk.append(Lmk)
        L.append(np.log(np.mean(Lk)))
        x_series.append(np.log(1.0 / k))
        
    # Fit line
    try:
        slope, _ = np.polyfit(x_series, L, 1)
        return slope
    except:
        return 1.5

def objective(trial):
    # 1. Suggest Hyperparameters
    # We need to modify Galaxy to accept these, but for now we'll assume defaults
    # or monkey-patch if needed.
    # Actually, let's just tune the 'noise_level' and 'correlation_strength'
    # assuming we can pass them or set them.
    
    # Since Galaxy is hardcoded currently, we might need to edit it to accept config.
    # For this script, we will just simulate and measure "Realism" of the DEFAULT galaxy
    # to establish a baseline, or we can assume we'll add config support later.
    
    # Let's assume we can set attributes directly after init
    galaxy = MarketGalaxy()
    
    # Tune Contagion
    galaxy.contagion_factor = trial.suggest_float('contagion_factor', 0.1, 2.0)
    
    # Run
    prices = []
    for _ in range(500):
        galaxy.step([])
        state = galaxy.get_state()
        prices.append(state['CORE']['price'])
        
    # Measure Realism
    # 1. Volatility should be non-zero but not infinite
    vol = np.std(np.diff(prices))
    if vol < 0.1 or vol > 50.0: return -1.0 # Penalize unrealistic vol
    
    # 2. Fractal Dimension should be close to 1.5 (Random Walk) - 1.8 (Rough)
    # We want "Interesting" markets, so maybe 1.6
    fd = higuchi_fd(prices)
    
    # Objective: Minimize distance to FD=1.6
    score = -abs(fd - 1.6)
    
    return score

def main():
    print("--- STARTING SIMULATION OPTIMIZATION (OPTUNA) ---")
    study = optuna.create_study(direction='maximize')
    study.optimize(objective, n_trials=50)
    
    print("Best params:", study.best_params)
    
    # Save
    os.makedirs('backend/data', exist_ok=True)
    with open('backend/data/best_galaxy.json', 'w') as f:
        json.dump(study.best_params, f, indent=2)

if __name__ == "__main__":
    main()
