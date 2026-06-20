# Shadow Engine Settings Fix

**Issue**: Shadow Engine was initializing with hardcoded defaults (0.65 threshold) instead of settings from `.env` (0.5 threshold).

**Date**: 2026-01-01

---

## Problem

The Shadow Engine log showed:
```
🌀 Espresso preset: 10s holds, 0.65 threshold
```

But the settings file (`backend/config/settings.py`) has:
```python
SHADOW_SIGNAL_THRESHOLD: float = 0.5  # Default from settings
```

And the actual loaded settings show:
```
SHADOW_SIGNAL_THRESHOLD: 0.5  ✅ Correct
```

**Root Cause**: `get_shadow_engine()` was being called without passing settings, so it used hardcoded defaults from `ShadowConfig` dataclass:
```python
@dataclass
class ShadowConfig:
    SIGNAL_THRESHOLD: float = 0.65  # ❌ Hardcoded default
```

---

## Solution

**File**: `/var/home/nhrlyn/Projects/Backup/auratic-systems-prime/backend/services/shadow_engine.py`

**Change**: Updated `get_shadow_engine()` to automatically load settings if not provided:

```python
def get_shadow_engine(settings=None) -> ShadowEngine:
    global _shadow_engine
    if _shadow_engine is None:
        # Automatically load settings if not provided
        if settings is None:
            try:
                from backend.config import get_settings
                settings = get_settings()
                logger.debug("Shadow Engine: Loaded settings from config")
            except Exception as e:
                logger.warning(f"Shadow Engine: Could not load settings, using defaults: {e}")
                settings = None
        _shadow_engine = ShadowEngine(settings)
        logger.info("🌀 Shadow Engine ready to assist your trading!")
    return _shadow_engine
```

---

## Current Settings (Verified)

```python
SHADOW_MIN_HOLD_TIME: 10        ✅ Matches expected
SHADOW_SIGNAL_THRESHOLD: 0.5    ✅ Correct (was showing 0.65)
SHADOW_POSITION_SIZE: 0.04      ✅ Correct (was showing 0.05)
SHADOW_MAX_POSITIONS: 3         ✅ Matches expected
```

---

## Expected Behavior After Fix

After restarting the backend, the Shadow Engine should log:
```
🌀 Espresso preset: 10s holds, 0.5 threshold
```

Instead of:
```
🌀 Espresso preset: 10s holds, 0.65 threshold
```

---

## Important Note

**The Shadow Engine is a singleton** - once initialized, it won't reinitialize even if you call `get_shadow_engine()` again. 

**To apply the fix**: **Restart the backend** so the Shadow Engine initializes with the correct settings.

---

## Verification

After restarting, verify the settings are correct:

1. **Check the log** for the initialization message:
   ```
   🌀 Espresso preset: 10s holds, 0.5 threshold
   ```

2. **Check via API** (if available):
   ```bash
   curl http://localhost:8000/api/dashboard/shadow-status
   ```
   Should show `signal_threshold: 0.5` in the config section.

3. **Check via Python**:
   ```python
   from backend.services.shadow_engine import get_shadow_engine
   from backend.config import get_settings
   
   settings = get_settings()
   engine = get_shadow_engine(settings)
   print(f"Threshold: {engine.config.SIGNAL_THRESHOLD}")  # Should be 0.5
   ```

---

## Settings Reference

### Settings File Defaults (`backend/config/settings.py`)
```python
SHADOW_ENGINE_ENABLED: bool = True
SHADOW_MIN_HOLD_TIME: int = 10
SHADOW_SIGNAL_THRESHOLD: float = 0.5
SHADOW_POSITION_SIZE: float = 0.04
SHADOW_MAX_POSITIONS: int = 3
```

### Hardcoded Defaults (Fallback - Only Used If Settings Can't Be Loaded)
```python
@dataclass
class ShadowConfig:
    MIN_HOLD_TIME: int = 10
    SIGNAL_PERSISTENCE: int = 1
    SIGNAL_THRESHOLD: float = 0.65  # ⚠️ Only used as fallback
    POSITION_SIZE: float = 0.05     # ⚠️ Only used as fallback
    MAX_POSITIONS: int = 3
```

---

## Status

✅ **FIXED** - Settings will now be loaded automatically when Shadow Engine initializes.

**Action Required**: Restart the backend to apply the fix.





