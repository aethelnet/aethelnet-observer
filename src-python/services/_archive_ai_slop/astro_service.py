"""
Astrological Data Service
=========================
Fetches Moon Phase, Solar Activity, and Day-of-Year for training Gen2 Neural Network.
"If there's a correlation, ML will find it."

Data Sources:
- Moon Phase: Calculated using ephem/skyfield (local computation)
- Solar Activity: NOAA SWPC API (Kp Index, Sunspot Number)
- Day of Year: Simple datetime calculation
"""

import math
import logging
import time
from datetime import datetime, timezone
from typing import Dict, Optional

logger = logging.getLogger("AstroService")

# --- MOON PHASE CALCULATION ---
# Using a simple astronomical algorithm (no external library needed)
# Based on Conway's algorithm for lunar phase

def get_moon_phase(dt: Optional[datetime] = None) -> float:
    """
    Calculate moon phase as a value from 0 to 1.
    0.0 = New Moon
    0.5 = Full Moon
    1.0 = New Moon (next cycle)
    
    Uses the synodic month (29.53 days) and a known new moon reference.
    """
    if dt is None:
        dt = datetime.now(timezone.utc)
    
    # Reference: Known New Moon (Jan 6, 2000 at 18:14 UTC)
    reference_new_moon = datetime(2000, 1, 6, 18, 14, 0, tzinfo=timezone.utc)
    
    # Synodic month in days
    synodic_month = 29.53058867
    
    # Ensure dt is timezone aware (UTC) to match reference
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
        
    # Days since reference
    days_since = (dt - reference_new_moon).total_seconds() / 86400.0
    
    # Current position in lunar cycle (0 to 1)
    phase = (days_since % synodic_month) / synodic_month
    
    return phase


def get_moon_phase_name(phase: float) -> str:
    """Convert numeric phase to human-readable name."""
    if phase < 0.0625:
        return "New Moon"
    elif phase < 0.1875:
        return "Waxing Crescent"
    elif phase < 0.3125:
        return "First Quarter"
    elif phase < 0.4375:
        return "Waxing Gibbous"
    elif phase < 0.5625:
        return "Full Moon"
    elif phase < 0.6875:
        return "Waning Gibbous"
    elif phase < 0.8125:
        return "Last Quarter"
    elif phase < 0.9375:
        return "Waning Crescent"
    else:
        return "New Moon"


# --- SOLAR ACTIVITY ---
# NOAA Space Weather Prediction Center provides Kp and Sunspot data

_solar_cache = {"timestamp": 0, "data": None}
SOLAR_CACHE_TTL = 3600  # 1 hour cache

async def fetch_solar_activity() -> Dict[str, float]:
    """
    Fetch current solar activity from NOAA SWPC.
    Returns: {kp_index: 0-9, sunspot_number: 0-300+}
    
    Falls back to neutral values if API fails.
    """
    import aiohttp
    
    now = time.time()
    if _solar_cache["data"] and (now - _solar_cache["timestamp"]) < SOLAR_CACHE_TTL:
        return _solar_cache["data"]
    
    try:
        # NOAA Planetary K-index
        kp_url = "https://services.swpc.noaa.gov/json/planetary_k_index_1m.json"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(kp_url, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data:
                        # Get latest Kp value
                        latest = data[-1]
                        kp_value = float(latest.get("kp_index", 3.0))
                        
                        result = {
                            "kp_index": kp_value,
                            "kp_normalized": kp_value / 9.0,  # Normalize to 0-1
                            "sunspot_number": 100.0,  # Placeholder (separate API)
                            "sunspot_normalized": 0.33  # Placeholder
                        }
                        
                        _solar_cache["timestamp"] = now
                        _solar_cache["data"] = result
                        
                        logger.info(f"[ASTRO] Solar Activity fetched: Kp={kp_value}")
                        return result
    except Exception as e:
        logger.warning(f"[ASTRO] Solar fetch failed: {e}")
    
    # Fallback to neutral values
    return {
        "kp_index": 3.0,
        "kp_normalized": 0.33,
        "sunspot_number": 100.0,
        "sunspot_normalized": 0.33
    }


def get_solar_activity_sync() -> Dict[str, float]:
    """Synchronous version using cached data or defaults."""
    if _solar_cache["data"]:
        return _solar_cache["data"]
    return {
        "kp_index": 3.0,
        "kp_normalized": 0.33,
        "sunspot_number": 100.0,
        "sunspot_normalized": 0.33
    }


# --- DAY OF YEAR (Seasonality) ---

def get_day_of_year(dt: Optional[datetime] = None) -> float:
    """
    Get day of year normalized to 0-1.
    Useful for capturing seasonality (January Effect, Tax Season, etc.)
    """
    if dt is None:
        dt = datetime.now(timezone.utc)
    
    day_of_year = dt.timetuple().tm_yday
    days_in_year = 366 if (dt.year % 4 == 0 and (dt.year % 100 != 0 or dt.year % 400 == 0)) else 365
    
    return day_of_year / days_in_year


def get_hour_of_day(dt: Optional[datetime] = None) -> float:
    """
    Get hour of day normalized to 0-1.
    Useful for capturing intraday patterns (market opens, closes, etc.)
    """
    if dt is None:
        dt = datetime.now(timezone.utc)
    
    return (dt.hour + dt.minute / 60.0) / 24.0


def get_day_of_week(dt: Optional[datetime] = None) -> float:
    """
    Get day of week normalized to 0-1.
    0 = Monday, 1 = Sunday (approx)
    """
    if dt is None:
        dt = datetime.now(timezone.utc)
    
    return dt.weekday() / 6.0


# --- AGGREGATED ASTRO PACKET ---

async def get_astro_packet(dt: Optional[datetime] = None) -> Dict[str, float]:
    """
    Get all astrological/temporal features in one packet.
    Ready for training ingestion.
    """
    if dt is None:
        dt = datetime.now(timezone.utc)
    
    moon = get_moon_phase(dt)
    solar = await fetch_solar_activity()
    day_of_year = get_day_of_year(dt)
    hour_of_day = get_hour_of_day(dt)
    day_of_week = get_day_of_week(dt)
    
    # Lunar illumination (0 at new moon, 1 at full moon, 0 at next new moon)
    # Use cosine of phase to get illumination curve
    illumination = (1 - math.cos(moon * 2 * math.pi)) / 2
    
    return {
        "moon_phase": moon,
        "moon_illumination": illumination,
        "moon_name": get_moon_phase_name(moon),
        "kp_index": solar["kp_normalized"],
        "sunspot": solar["sunspot_normalized"],
        "day_of_year": day_of_year,
        "hour_of_day": hour_of_day,
        "day_of_week": day_of_week
    }


def get_astro_packet_sync(dt: Optional[datetime] = None) -> Dict[str, float]:
    """
    Synchronous version (uses cached solar data).
    Use this in non-async contexts like training data preparation.
    """
    if dt is None:
        dt = datetime.now(timezone.utc)
    
    moon = get_moon_phase(dt)
    solar = get_solar_activity_sync()
    day_of_year = get_day_of_year(dt)
    hour_of_day = get_hour_of_day(dt)
    day_of_week = get_day_of_week(dt)
    
    illumination = (1 - math.cos(moon * 2 * math.pi)) / 2
    
    return {
        "moon_phase": moon,
        "moon_illumination": illumination,
        "kp_index": solar["kp_normalized"],
        "sunspot": solar["sunspot_normalized"],
        "day_of_year": day_of_year,
        "hour_of_day": hour_of_day,
        "day_of_week": day_of_week
    }


# --- SINGLETON ---
_astro_service_instance = None

def get_astro_service():
    """Get singleton instance (for future stateful caching)."""
    global _astro_service_instance
    if _astro_service_instance is None:
        _astro_service_instance = AstroService()
    return _astro_service_instance


class AstroService:
    """Wrapper class for potential future extensions."""
    
    def __init__(self):
        self.last_update = 0
        
    async def get_packet(self, dt: Optional[datetime] = None) -> Dict[str, float]:
        return await get_astro_packet(dt)
    
    def get_packet_sync(self, dt: Optional[datetime] = None) -> Dict[str, float]:
        return get_astro_packet_sync(dt)
