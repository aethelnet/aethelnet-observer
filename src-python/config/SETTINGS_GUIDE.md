# Settings Configuration Guide

## Overview
This guide categorizes all settings by importance and explains what's safe to modify vs what should be left alone.

**Key Principle**: Settings in `.env` override defaults in `settings.py`. If a setting isn't in `.env`, the default value is used.

## Security Warnings

**CRITICAL**: The following security issues were identified in the system vitals review:

1. **ADMIN_TOKEN Default Value**: The default `"auratic_alpha_99"` is insecure for production
   - **Action Required**: Set `ADMIN_TOKEN` in `.env` file for production
   - **Validation**: System will refuse to start in production mode without a custom ADMIN_TOKEN
   - See [System Vitals Review](../../docs/system_vitals_review.md) for details

2. **Telemetry/Phone-Home Code**: Beta Rat telemetry sends data externally
   - **Action Required**: Disable or gate behind explicit opt-in flag
   - **Status**: Being addressed in system vitals fixes

---

## 🔴 CRITICAL - Required for Live Trading

These settings MUST be configured correctly for live trading:

### API Keys (Required)
```bash
# For TESTNET (safe testing):
BINANCE_TESTNET_API_KEY=your_testnet_key_here
BINANCE_TESTNET_SECRET_KEY=your_testnet_secret_here

# For LIVE TRADING (real money):
BINANCE_API_KEY=your_live_key_here
BINANCE_SECRET_KEY=your_live_secret_here
```

### Trading Mode Control (Required)
```bash
# Set to false for LIVE TRADING (real money!)
BINANCE_TESTNET=true

# Must match BINANCE_TESTNET:
# - "testnet" = safe testing
# - "production" = live trading (real money!)
ENV_MODE=testnet

# Enable/disable actual trade execution
EXECUTION_ENABLED=true
```

**⚠️ WARNING**: Setting `BINANCE_TESTNET=false` and `ENV_MODE=production` enables REAL MONEY trading!

---

## 🟡 IMPORTANT - Core Trading Settings

These affect trading behavior and should be understood before modifying:

### Oracle System (Primary Decision Maker)
```bash
# Use Oracle for trading decisions (synthesizes multiple signals)
# Default: true (recommended)
ORACLE_ENABLED=true

# Legacy mode: use preset threshold/persistence instead of Oracle
# Default: false (Oracle is primary)
USE_PRESET_FILTERS=false
```

**Oracle** synthesizes signals from:
- Logic (Physics/Z-Score): 40% weight
- ML Models: 30% weight
- Pattern Matching: 20% weight
- Sentiment: 10% weight

Output: Truth Score (-1.0 to +1.0) used for trading decisions.

### Position Sizing & Risk Management (Always Active)
```bash
# Max position size as % of account (0.05 = 5%)
MAX_POSITION_SIZE=0.05

# Minimum hold time in seconds (prevents whipsaw)
MIN_HOLD_TIME=45

# Daily loss limit in USD (stops trading if exceeded)
MAX_DAILY_LOSS=500.0

# Per-trade stop loss percentage (0.012 = 1.2%)
STOP_LOSS=0.012

# Per-trade profit target percentage (0.016 = 1.6%)
PROFIT_TARGET=0.016
```

### Legacy Preset Filters (Only if USE_PRESET_FILTERS=true)
```bash
# Signal strength threshold (0.1-1.0, lower = more trades)
# Only used if USE_PRESET_FILTERS=true
SIGNAL_THRESHOLD=0.65

# Require N confirming signals before trading
# Only used if USE_PRESET_FILTERS=true
SIGNAL_PERSISTENCE=2
```

**Note**: Preset filters are legacy. Oracle is the recommended approach.

### Symbol Selection
```bash
# Comma-separated list of trading pairs
SYMBOLS_WHITELIST=BTCUSDT,ETHUSDT,SOLUSDT,ADAUSDT,DOTUSDT,LINKUSDT,AVAXUSDT,MATICUSDT
```

---

## Oracle Migration Guide

### Migrating from Presets to Oracle

**Default Behavior** (Recommended):
- `ORACLE_ENABLED=true` (default)
- `USE_PRESET_FILTERS=false` (default)
- Oracle synthesizes all signals and makes trading decisions

**Legacy Mode** (Fallback):
- `ORACLE_ENABLED=false` OR `USE_PRESET_FILTERS=true`
- Uses preset threshold and persistence checks
- Same behavior as before Oracle integration

**Migration Steps**:
1. Ensure `ORACLE_ENABLED=true` in settings (default)
2. Ensure `USE_PRESET_FILTERS=false` in settings (default)
3. Restart backend
4. Monitor Oracle truth scores in logs: `[ORACLE] {symbol}: truth_score={score:.3f}`
5. Compare performance: Oracle vs previous preset-based trading

**Rollback** (if needed):
- Set `USE_PRESET_FILTERS=true` to revert to preset-based trading
- System will use threshold/persistence checks instead of Oracle

---

## 🟢 OPTIONAL - Can Be Commented Out

These have safe defaults and can be left unset or commented out:

### System Performance (Safe Defaults)
```bash
# PHYSICS_WINDOW_SIZE=20000  # Data window size
# BROADCAST_INTERVAL=0.05     # Update rate (20Hz)
```

### Trading Style (Safe Defaults)
```bash
# TRADE_FREQUENCY=HIGH              # HIGH/MEDIUM/LOW
# RISK_TOLERANCE=AGGRESSIVE         # CONSERVATIVE/MODERATE/AGGRESSIVE
# PROFIT_TARGET=0.02                # 2% profit target
# STOP_LOSS=0.01                    # 1% stop loss
# TRAILING_STOP=true                # Enable trailing stops
# SCALPING_MODE=true                 # Enable rapid trading
```

### Shadow Engine (Optional Feature)
```bash
# SHADOW_ENGINE_ENABLED=true        # Parallel shadow trading
# SHADOW_MIN_HOLD_TIME=10
# SHADOW_SIGNAL_THRESHOLD=0.5       # Uses Oracle if ORACLE_ENABLED=true
# SHADOW_POSITION_SIZE=0.04
# SHADOW_MAX_POSITIONS=3
```

**Note**: Shadow Engine now supports Oracle-based decisions (if `ORACLE_ENABLED=true`). Falls back to preset threshold if Oracle is disabled.

### Validation Settings (For Testing)
```bash
# VALIDATION_MIN_TRADES=75
# VALIDATION_MIN_WIN_RATE=0.45
# VALIDATION_MAX_DRAWDOWN=0.08
# VALIDATION_TARGET_HOURS=3.0
```

### Universe Engine (Auto-configured)
```bash
# UNIVERSE_MODE=alpha
# API_URL=http://localhost:8000
# UNIVERSE_REFRESH_INTERVAL=3600
```

### Brain Engine (Physics Analysis - Auto-configured)
```bash
# BRAIN_ENGINE_ENABLED=true
# PHYSICS_MASS=1.0
# PHYSICS_DRAG_COEFFICIENT=0.1
# PHYSICS_SPRING_CONSTANT=0.5
# PHYSICS_DAMPING_RATIO=0.7
# BRAIN_CALCULATION_INTERVAL=0.1
```

### Monitoring & Notifications (Optional)
```bash
# SENTINEL_ENABLED=true             # System health monitoring
# SENTINEL_CHECK_INTERVAL=30
# SENTINEL_ALERT_THRESHOLD=0.05
# SENTINEL_AUTO_STOP=true

# ARENA_ENABLED=true                # Competition tracking
# RIVAL_NAME=Pied_Piper
# USER_TEAM_NAME=The_Prophit_Team
# ARENA_UPDATE_INTERVAL=60

# DISCORD_WEBHOOK_URL=              # Optional notifications
# NOTIFICATION_EMAIL=
```

### ALPHA/BETA Access Control (Optional)
```bash
# ALPHA_OVERRIDE=true              # Force ALPHA mode (dev/test only - bypasses all checks)
# ADMIN_TOKEN=your_secret_token    # Primary entry method for ALPHA mode (set in .env)
```
**Note:** The system has two modes:
- **ALPHA mode**: Full functionality, no restrictions
- **BETA mode**: Restricted/lobotomized functionality (default if no auth provided)

**Entry methods (priority order):**
1. `ALPHA_OVERRIDE=true` - Highest priority, for dev/test
2. `ADMIN_TOKEN` in .env - Primary automatic entry method
3. ACL whitelist (via `access_control.json`) - For team members

### Development & Debugging
```bash
# DEBUG_MODE=false
# VERBOSE_LOGGING=false
# MOCK_TRADING=false
# PERFORMANCE_TRACKING=true
```

### Legacy/Unused (Can Be Ignored)
```bash
# LEGACY_MODE=false                 # Not used in current code
# OLD_SIGNAL_ENGINE=false           # Not used in current code
# DEPRECATED_RISK_ENGINE=false      # Not used in current code
# HAWK_ENABLED=false                # Arbitrage scanner (disabled)
```

### Other Optional Services
```bash
# ALPACA_API_KEY=                   # Stock trading (optional)
# ALPACA_SECRET_KEY=
# ADMIN_TOKEN=auratic_alpha_99      # ⚠️ CRITICAL: Change this in production!
# 
# SECURITY WARNING: The default value is insecure. For production:
# 1. Set ADMIN_TOKEN in .env file
# 2. Use a strong, random token
# 3. System will refuse to start in production mode without custom ADMIN_TOKEN
```

---

## 📋 Minimal .env for Live Trading

For live trading, you only need these settings:

```bash
# =============================================================================
# CRITICAL: API Keys for Live Trading
# =============================================================================
BINANCE_API_KEY=your_live_key_here
BINANCE_SECRET_KEY=your_live_secret_here

# =============================================================================
# CRITICAL: Trading Mode
# =============================================================================
BINANCE_TESTNET=false
ENV_MODE=production
EXECUTION_ENABLED=true

# =============================================================================
# IMPORTANT: Core Trading Settings
# =============================================================================
MAX_POSITION_SIZE=0.05
MIN_HOLD_TIME=45
SIGNAL_THRESHOLD=0.65
SIGNAL_PERSISTENCE=2
MAX_DAILY_LOSS=500.0
SYMBOLS_WHITELIST=BTCUSDT,ETHUSDT,SOLUSDT
```

Everything else will use safe defaults from `settings.py`.

---

## ✅ Settings Validation Checklist

Before going live, verify:

- [ ] `BINANCE_TESTNET=false` (for live trading)
- [ ] `ENV_MODE=production` (matches BINANCE_TESTNET)
- [ ] `EXECUTION_ENABLED=true` (enables trading)
- [ ] API keys are set and valid
- [ ] `MAX_POSITION_SIZE` is reasonable (0.05 = 5% max)
- [ ] `MAX_DAILY_LOSS` is acceptable
- [ ] `SYMBOLS_WHITELIST` contains valid trading pairs

---

## 🛡️ Safety Recommendations

1. **Start with testnet**: Always test with `BINANCE_TESTNET=true` first
2. **Small position sizes**: Keep `MAX_POSITION_SIZE` low (0.05 = 5%)
3. **Daily loss limit**: Set `MAX_DAILY_LOSS` to a comfortable amount
4. **Monitor closely**: Watch the first few live trades carefully
5. **Emergency stop**: Know how to set `EXECUTION_ENABLED=false` quickly

---

## 🔧 How to Comment Out Settings

In your `.env` file, you can comment out any setting by adding `#` at the start:

```bash
# This setting is commented out and won't be used
# SHADOW_ENGINE_ENABLED=true

# This setting is active
EXECUTION_ENABLED=true
```

If a setting is commented out or missing, the default value from `settings.py` will be used.

---

## 📝 Notes

- All settings have defaults in `backend/config/settings.py`
- Settings in `.env` override defaults
- Missing or commented settings = use default
- The system will log which settings are loaded at startup
- Check logs to verify your configuration

