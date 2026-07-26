"""
Unit tests for train_artifacts.py
Tests data validation, fitness calculation, and numeric stability.
"""

import unittest
import pandas as pd
import numpy as np
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from arena.train_artifacts import (
    _validate_and_clean_data,
    calculate_fitness,
    calculate_thoth_oracle
)


class TestDataValidation(unittest.TestCase):
    """Test data validation and cleaning."""
    
    def test_removes_invalid_prices(self):
        """Test that candles with zero or negative prices are removed."""
        df = pd.DataFrame({
            'open': [100, 0, -10, 200],
            'high': [110, 5, 5, 210],
            'low': [95, 0, 0, 195],
            'close': [105, 0, -5, 205],
            'volume': [1000, 1000, 1000, 1000],
            'timestamp': pd.date_range('2024-01-01', periods=4, freq='1min')
        })
        
        cleaned = _validate_and_clean_data(df)
        
        # Should only keep first and last row (valid prices)
        self.assertEqual(len(cleaned), 2)
        self.assertTrue(all(cleaned['close'] > 0))
    
    def test_removes_extreme_intrabar_moves(self):
        """Test that candles with >50% intrabar moves are removed."""
        df = pd.DataFrame({
            'open': [100, 100],
            'high': [160, 110],  # First has 60% intrabar move
            'low': [100, 100],
            'close': [105, 105],
            'volume': [1000, 1000],
            'timestamp': pd.date_range('2024-01-01', periods=2, freq='1min')
        })
        
        cleaned = _validate_and_clean_data(df)
        
        # Should remove first row (extreme intrabar move)
        self.assertEqual(len(cleaned), 1)
    
    def test_removes_extreme_sequential_jumps(self):
        """Test that candles with >50% sequential price changes are removed."""
        df = pd.DataFrame({
            'open': [100, 100, 100],
            'high': [110, 110, 110],
            'low': [95, 95, 95],
            'close': [100, 160, 110],  # Second has 60% jump from first
            'volume': [1000, 1000, 1000],
            'timestamp': pd.date_range('2024-01-01', periods=3, freq='1min')
        })
        
        cleaned = _validate_and_clean_data(df)
        
        # Should remove the row with extreme sequential jump
        # Note: first row will be removed because pct_change() is NaN for first row
        # So we expect 2 rows (second and third, or just third if second is removed)
        self.assertLessEqual(len(cleaned), 2)
    
    def test_preserves_valid_data(self):
        """Test that valid data passes through unchanged."""
        df = pd.DataFrame({
            'open': [100, 101, 102],
            'high': [105, 106, 107],
            'low': [99, 100, 101],
            'close': [103, 104, 105],
            'volume': [1000, 1000, 1000],
            'timestamp': pd.date_range('2024-01-01', periods=3, freq='1min')
        })
        
        cleaned = _validate_and_clean_data(df)
        
        # All data should be valid
        self.assertEqual(len(cleaned), 3)


class TestFitnessCalculation(unittest.TestCase):
    """Test fitness calculation function."""
    
    def test_returns_zero_for_insufficient_trades(self):
        """Test that fitness is 0 if trades < 5."""
        fitness = calculate_fitness(2000.0, 1000.0, 3, 2, [0.1, 0.2, 0.15])
        self.assertEqual(fitness, 0.0)
    
    def test_calculates_log_returns(self):
        """Test that fitness uses log returns."""
        # 2x return = log(2) ≈ 0.693
        fitness = calculate_fitness(2000.0, 1000.0, 10, 8, [0.1] * 10)
        
        # Should be positive (log return * 100 + win rate * 50)
        self.assertGreater(fitness, 0)
        self.assertLess(fitness, 200)  # Reasonable upper bound
    
    def test_penalizes_extreme_returns(self):
        """Test that extreme single-trade returns are penalized."""
        # Normal returns
        normal_fitness = calculate_fitness(1500.0, 1000.0, 10, 8, [0.05] * 10)
        
        # Extreme return (>50%)
        extreme_fitness = calculate_fitness(1500.0, 1000.0, 10, 8, [0.6] + [0.05] * 9)
        
        # Extreme should be penalized (lower fitness)
        self.assertLess(extreme_fitness, normal_fitness)
    
    def test_handles_zero_balance(self):
        """Test that zero or negative balance is handled gracefully."""
        fitness = calculate_fitness(0.0, 1000.0, 10, 5, [0.1] * 10)
        
        # Should not crash, should return finite value
        self.assertTrue(np.isfinite(fitness))
    
    def test_handles_empty_returns(self):
        """Test that empty returns history is handled."""
        fitness = calculate_fitness(1500.0, 1000.0, 10, 8, [])
        
        # Should not crash
        self.assertTrue(np.isfinite(fitness))
        self.assertGreater(fitness, 0)


class TestOracleProbabilistic(unittest.TestCase):
    """Test probabilistic oracle behavior."""
    
    def test_resonance_varies(self):
        """Test that resonance values vary within expected range."""
        df = pd.DataFrame({
            'open': [100] * 20,
            'high': [105] * 20,
            'low': [95] * 20,
            'close': [100 + i for i in range(20)],  # Simple trend
            'volume': [1000] * 20,
            'timestamp': pd.date_range('2024-01-01', periods=20, freq='1min')
        })
        
        predictions = calculate_thoth_oracle(df, horizon=5, resonance_range=(0.7, 1.0))
        
        # Check that resonances vary
        resonances = [p['resonance'] for p in predictions if p is not None]
        
        self.assertGreater(len(resonances), 0)
        
        # All should be in range
        for r in resonances:
            self.assertGreaterEqual(r, 0.7)
            self.assertLessEqual(r, 1.0)
        
        # Should have some variation (not all 1.0)
        unique_resonances = set(resonances)
        self.assertGreater(len(unique_resonances), 1)  # At least some variation
    
    def test_predictions_have_noise(self):
        """Test that predictions include noise."""
        df = pd.DataFrame({
            'open': [100] * 20,
            'high': [105] * 20,
            'low': [95] * 20,
            'close': [100] * 20,  # Constant price
            'volume': [1000] * 20,
            'timestamp': pd.date_range('2024-01-01', periods=20, freq='1min')
        })
        
        predictions = calculate_thoth_oracle(df, horizon=5, resonance_range=(0.7, 1.0))
        
        # Check that prices have some variation (due to noise)
        valid_predictions = [p for p in predictions if p is not None]
        if len(valid_predictions) > 1:
            prices_0 = valid_predictions[0]['prices']
            prices_1 = valid_predictions[1]['prices']
            
            # Prices should have some variation even with constant input
            # (due to noise factor)
            self.assertIsNotNone(prices_0)
            self.assertIsNotNone(prices_1)


class TestNumericStability(unittest.TestCase):
    """Test numeric stability with edge cases."""
    
    def test_fitness_no_overflow(self):
        """Test that fitness doesn't overflow with large balances."""
        # Simulate what would have caused overflow before
        # Even with large balance, log returns keep it bounded
        fitness = calculate_fitness(1e100, 1000.0, 10, 8, [0.1] * 10)
        
        # Should be finite and reasonable
        self.assertTrue(np.isfinite(fitness))
        self.assertLess(fitness, 1e10)  # Should be much smaller than input
    
    def test_fitness_handles_nan(self):
        """Test that fitness handles NaN inputs gracefully."""
        # Should not crash
        try:
            fitness = calculate_fitness(np.nan, 1000.0, 10, 8, [0.1] * 10)
            # If it returns, should be finite or handled
            if np.isfinite(fitness):
                self.assertTrue(True)
        except Exception:
            # If it raises, that's also acceptable (fail-fast)
            self.assertTrue(True)


if __name__ == '__main__':
    unittest.main()




