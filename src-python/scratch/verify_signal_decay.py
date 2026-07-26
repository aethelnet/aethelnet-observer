
import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# Mock settings
settings = MagicMock()
settings.SIGNAL_DECAY_EXIT_ENABLED = True
settings.SIGNAL_DECAY_EXIT_PCT = 0.10

def test_signal_decay_logic(entry_signal, current_signal, expected_exit):
    entry_signal_abs = abs(entry_signal)
    current_signal_abs = abs(current_signal)
    threshold_pct = 0.10
    exit_threshold = entry_signal_abs * (1.0 - threshold_pct)
    
    triggered = (entry_signal_abs > 0 and current_signal_abs < exit_threshold)
    
    print(f"Entry: {entry_signal} | Current: {current_signal} | Threshold: {exit_threshold:.2f} | Exit: {triggered} (Expected: {expected_exit})")
    return triggered == expected_exit

# Test cases
print("--- Verifying Signal Decay Logic ---")
success = True
success &= test_signal_decay_logic(2.0, 1.9, False)  # 1.9 > 1.8 (No exit)
success &= test_signal_decay_logic(2.0, 1.7, True)   # 1.7 < 1.8 (Exit)
success &= test_signal_decay_logic(-2.0, -1.9, False) # abs(-1.9) > 1.8 (No exit)
success &= test_signal_decay_logic(-2.0, -1.7, True)  # abs(-1.7) < 1.8 (Exit)
success &= test_signal_decay_logic(2.0, 0.0, True)    # 0 < 1.8 (Exit)

if success:
    print("\n✅ Logic validation PASSED.")
else:
    print("\n❌ Logic validation FAILED.")
