# Going Live - Step-by-Step Guide

## Overview
This guide walks you through the process of configuring and verifying your system for live trading.

---

## Step 1: Understand Settings Structure

**Settings are loaded from:**
1. `.env` file in project root (overrides defaults)
2. `backend/config/settings.py` (defaults if not in .env)

**Key Principle**: If a setting isn't in `.env`, the default from `settings.py` is used. You only need to set what you want to change.

---

## Step 2: Create Minimal .env File

1. Copy the minimal template:
   ```bash
   cp backend/config/env.minimal.example .env
   ```

2. Edit `.env` and fill in:
   - Your Binance API keys (for live trading)
   - Set `BINANCE_TESTNET=false` for live trading
   - Set `ENV_MODE=production` for live trading
   - Adjust position size and risk limits as needed

**See**: `backend/config/env.minimal.example` for the minimal template

---

## Step 3: Validate Settings

Before starting the system, validate your configuration:

```bash
python backend/config/validate_settings.py
```

This will check:
- ✅ API keys are set
- ✅ Trading mode is consistent
- ✅ Risk settings are reasonable
- ⚠️  Warns about high-risk configurations

**Fix any errors before proceeding!**

---

## Step 4: Test with Testnet First (Recommended)

1. Set in `.env`:
   ```bash
   BINANCE_TESTNET=true
   ENV_MODE=testnet
   ```

2. Use testnet API keys:
   ```bash
   BINANCE_TESTNET_API_KEY=your_testnet_key
   BINANCE_TESTNET_SECRET_KEY=your_testnet_secret
   ```

3. Start the system and verify it trades correctly on testnet

4. Monitor for at least a few hours to ensure stability

---

## Step 5: Switch to Live Trading

**⚠️ WARNING: This enables real money trading!**

1. Update `.env`:
   ```bash
   BINANCE_TESTNET=false
   ENV_MODE=production
   ```

2. Use live API keys:
   ```bash
   BINANCE_API_KEY=your_live_key
   BINANCE_SECRET_KEY=your_live_secret
   ```

3. **Double-check**:
   - Position sizes are reasonable (start small!)
   - Daily loss limit is acceptable
   - You understand the risk

4. Validate again:
   ```bash
   python backend/config/validate_settings.py
   ```

5. Start the system:
   ```bash
   python backend/main.py
   ```

---

## Step 6: Verify Live Trading

### Check System Logs

Look for these log messages at startup:
```
[System] ENV_MODE=production | EXECUTION_ENABLED=True
[System] 🧪 TESTNET MODE - Orders will be placed on Binance Testnet
```
**If you see "TESTNET MODE" in live trading, something is wrong!**

### Monitor First Trades

1. Watch the logs for trade execution
2. Verify trades appear in your Binance account
3. Check that position sizes match your settings
4. Monitor for any unexpected behavior

### Emergency Stop

If something goes wrong:
1. Set `EXECUTION_ENABLED=false` in `.env`
2. Restart the system (or use emergency endpoint)
3. Manually close any open positions in Binance

---

## Settings You Can Safely Ignore

These settings have safe defaults and can be left unset:

- All `PHYSICS_*` settings (brain engine auto-configures)
- All `SHADOW_*` settings (optional feature)
- `SENTINEL_*`, `ARENA_*` (monitoring, optional)
- `VALIDATION_*` (for testing only)
- `HAWK_*` (disabled by default)
- `LEGACY_*` (not used)
- `ALPACA_*` (stock trading, optional)
- `DISCORD_WEBHOOK_URL`, `NOTIFICATION_EMAIL` (optional)

**See**: `backend/config/SETTINGS_GUIDE.md` for full details

---

## Quick Reference: Essential Settings

```bash
# Required for live trading:
BINANCE_API_KEY=...
BINANCE_SECRET_KEY=...
BINANCE_TESTNET=false
ENV_MODE=production
EXECUTION_ENABLED=true

# Important (adjust as needed):
MAX_POSITION_SIZE=0.05        # 5% max per trade
MIN_HOLD_TIME=45              # 45 seconds minimum
SIGNAL_THRESHOLD=0.65         # Signal strength
SIGNAL_PERSISTENCE=2          # Confirmations needed
MAX_DAILY_LOSS=500.0          # Daily loss limit
SYMBOLS_WHITELIST=BTCUSDT,... # Trading pairs
```

---

## Troubleshooting

### "Settings not loading"
- Check `.env` file is in project root (same level as `backend/`)
- Verify no syntax errors (no spaces around `=`)
- Check file permissions

### "Still using testnet"
- Verify `BINANCE_TESTNET=false` in `.env`
- Check `ENV_MODE=production` matches
- Restart the system after changes

### "Trades not executing"
- Check `EXECUTION_ENABLED=true`
- Verify API keys are correct
- Check Binance account has sufficient balance
- Review logs for error messages

---

## Safety Checklist

Before going live, verify:

- [ ] Tested on testnet successfully
- [ ] Settings validated (no errors)
- [ ] Position size is reasonable (≤5% recommended)
- [ ] Daily loss limit is acceptable
- [ ] API keys are correct
- [ ] `BINANCE_TESTNET=false` and `ENV_MODE=production`
- [ ] `EXECUTION_ENABLED=true`
- [ ] Monitoring system is ready
- [ ] Know how to stop trading quickly
- [ ] Understand the risks

---

## Need Help?

- **Settings Guide**: `backend/config/SETTINGS_GUIDE.md`
- **Minimal Template**: `backend/config/env.minimal.example`
- **Validation Script**: `python backend/config/validate_settings.py`




