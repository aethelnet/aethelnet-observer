import pytest
import pandas as pd
import numpy as np
from arena.strategies.rat import TheRat

def test_rat_unshackled_velocity_guard():
    """Verify that high velocity does not block signals in unshackled mode."""
    rat = TheRat()
    market_state = {
        'z_score': 3.0,
        'velocity': 5.0, # Very high velocity in same direction
        'price': 100.0,
        'trend_strength': 0.0,
        'regime': 'JOY'
    }
    
    # In previous version, this would return 0.0 due to is_suicide = True
    signal = rat.on_tick(market_state)
    assert signal != 0.0
    print(f"Signal with high velocity: {signal}")

def test_rat_unshackled_crash_protocol():
    """Verify that extreme negative trend does not block buy signals."""
    rat = TheRat()
    market_state = {
        'z_score': -3.0,
        'velocity': 0.0,
        'price': 100.0,
        'trend_strength': -1.0, # Extreme crash
        'regime': 'SAD'
    }
    
    # In previous version, this would return 0.0 due to trend < -0.95
    signal = rat.on_tick(market_state)
    assert signal != 0.0
    print(f"Signal during crash: {signal}")

def test_rat_unshackled_regime_block():
    """Verify that choppy regimes do not block momentum signals."""
    from unittest.mock import patch
    rat = TheRat()
    market_state = {
        'z_score': 2.0,
        'velocity': 0.0,
        'price': 100.0,
        'trend_strength': 0.0,
        'regime': 'EQUI' # Choppy regime
    }
    
    # Mock settings.USE_RAT_MEAN_REVERSION = False for momentum mode
    with patch('arena.strategies.rat.get_settings') as mock_settings:
        mock_settings.return_value.USE_RAT_MEAN_REVERSION = False
        signal = rat.on_tick(market_state)
        assert signal > 0 # Should follow momentum (Z=2 > sensitivity)
        
def test_rat_unshackled_clamping():
    """Verify that sensitivity and profit are not clamped."""
    skills = {
        'wick_sensitivity': 10.0, # High
        'profit_target': 0.99     # High
    }
    rat = TheRat(skills=skills)
    eff = rat._get_effective_skills()
    
    # Formula: 0.8 + (10.0 * 0.4) = 4.8. 
    # Clamping was at 5.0, so let's try 20.0
    rat.skills['wick_sensitivity'] = 20.0
    eff = rat._get_effective_skills()
    assert eff['sensitivity'] == 0.8 + (20.0 * 0.4) # Should be 8.8, not clamped to 5.0
    assert eff['profit'] == 0.99 # Not clamped to 0.50
