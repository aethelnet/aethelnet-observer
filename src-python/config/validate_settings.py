#!/usr/bin/env python3
"""
Settings Validation Script
Validates .env configuration before live trading
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config import get_settings

def validate_settings():
    """Validate settings and print warnings/errors"""
    settings = get_settings()
    
    errors = []
    warnings = []
    info = []
    
    print("=" * 70)
    print("SETTINGS VALIDATION")
    print("=" * 70)
    print()
    
    # =========================================================================
    # CRITICAL CHECKS
    # =========================================================================
    
    # Check API keys
    if settings.BINANCE_TESTNET:
        if not settings.BINANCE_TESTNET_API_KEY or not settings.BINANCE_TESTNET_SECRET_KEY:
            errors.append("❌ TESTNET API keys are missing (required for testnet mode)")
        else:
            info.append("✅ Testnet API keys configured")
    else:
        if not settings.BINANCE_API_KEY or not settings.BINANCE_SECRET_KEY:
            errors.append("❌ LIVE TRADING API keys are missing (required for live trading)")
        else:
            warnings.append("⚠️  LIVE TRADING API keys configured - REAL MONEY MODE!")
    
    # Check trading mode consistency
    if settings.BINANCE_TESTNET and settings.ENV_MODE == "production":
        errors.append("❌ BINANCE_TESTNET=true but ENV_MODE=production (inconsistent)")
    elif not settings.BINANCE_TESTNET and settings.ENV_MODE == "testnet":
        errors.append("❌ BINANCE_TESTNET=false but ENV_MODE=testnet (inconsistent)")
    else:
        mode = "TESTNET" if settings.BINANCE_TESTNET else "LIVE TRADING"
        info.append(f"✅ Trading mode: {mode} (ENV_MODE={settings.ENV_MODE})")
    
    # Check execution enabled
    if not settings.EXECUTION_ENABLED:
        warnings.append("⚠️  EXECUTION_ENABLED=false (trading is disabled)")
    else:
        info.append("✅ Trade execution enabled")
    
    # =========================================================================
    # IMPORTANT CHECKS
    # =========================================================================
    
    # Position size
    if settings.MAX_POSITION_SIZE > 0.1:
        warnings.append(f"⚠️  MAX_POSITION_SIZE={settings.MAX_POSITION_SIZE} (10%+) is high risk")
    elif settings.MAX_POSITION_SIZE < 0.01:
        warnings.append(f"⚠️  MAX_POSITION_SIZE={settings.MAX_POSITION_SIZE} (1%-) is very conservative")
    else:
        info.append(f"✅ Position size: {settings.MAX_POSITION_SIZE*100:.1f}%")
    
    # Signal threshold
    if settings.SIGNAL_THRESHOLD < 0.3:
        warnings.append(f"⚠️  SIGNAL_THRESHOLD={settings.SIGNAL_THRESHOLD} (very low, will trade frequently)")
    elif settings.SIGNAL_THRESHOLD > 0.9:
        warnings.append(f"⚠️  SIGNAL_THRESHOLD={settings.SIGNAL_THRESHOLD} (very high, will trade rarely)")
    else:
        info.append(f"✅ Signal threshold: {settings.SIGNAL_THRESHOLD}")
    
    # Daily loss limit
    if settings.MAX_DAILY_LOSS <= 0:
        errors.append("❌ MAX_DAILY_LOSS must be > 0")
    else:
        info.append(f"✅ Daily loss limit: ${settings.MAX_DAILY_LOSS:.2f}")
    
    # Symbols
    from config.settings import get_trading_symbols
    symbols = get_trading_symbols(settings)
    if symbols:
        info.append(f"✅ Trading {len(symbols)} symbols: {', '.join(symbols[:3])}{'...' if len(symbols) > 3 else ''}")
    else:
        warnings.append("⚠️  No trading symbols configured (will use defaults)")
    
    # =========================================================================
    # OPTIONAL CHECKS
    # =========================================================================
    
    if settings.SHADOW_ENGINE_ENABLED:
        info.append("ℹ️  Shadow engine enabled")
    
    if settings.SENTINEL_ENABLED:
        info.append("ℹ️  Sentinel monitoring enabled")
    
    if settings.ARENA_ENABLED:
        info.append("ℹ️  Arena scoreboard enabled")
    
    # =========================================================================
    # PRINT RESULTS
    # =========================================================================
    
    print("📋 VALIDATION RESULTS:")
    print()
    
    if info:
        print("✅ INFO:")
        for msg in info:
            print(f"   {msg}")
        print()
    
    if warnings:
        print("⚠️  WARNINGS:")
        for msg in warnings:
            print(f"   {msg}")
        print()
    
    if errors:
        print("❌ ERRORS:")
        for msg in errors:
            print(f"   {msg}")
        print()
        print("=" * 70)
        print("❌ VALIDATION FAILED - Fix errors before trading")
        print("=" * 70)
        return False
    
    print("=" * 70)
    if warnings:
        print("⚠️  VALIDATION PASSED WITH WARNINGS - Review warnings above")
    else:
        print("✅ VALIDATION PASSED - Settings look good!")
    print("=" * 70)
    
    # Final safety check for live trading
    if not settings.BINANCE_TESTNET:
        print()
        print("🔴 LIVE TRADING MODE DETECTED")
        print("   - Real money will be used")
        print("   - Verify all settings are correct")
        print("   - Start with small position sizes")
        print("   - Monitor closely")
        print()
    
    return len(errors) == 0

if __name__ == "__main__":
    success = validate_settings()
    sys.exit(0 if success else 1)



