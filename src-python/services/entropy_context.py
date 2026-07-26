"""
Context Entropy Synthesizer
===========================
Distilled from legacy agentic bloat (astro_service, spider_geo, etc.).
This module provides pure mathematical functions to extract environmental entropy
(lunar phase, solar flares, temporal seasonality) as normalized floats [0.0, 1.0].

No autonomous agents. No background loops. Just numbers for the Core Loop.
"""

import math
import time
import logging
from datetime import datetime, timezone
from typing import Dict, Optional

logger = logging.getLogger("EntropyContext")

_solar_cache = {"timestamp": 0, "kp_normalized": 0.33}
SOLAR_CACHE_TTL = 3600  # 1 hour

def get_temporal_entropy(dt: Optional[datetime] = None) -> Dict[str, float]:
    """Returns normalized time-based seasonality (0.0 to 1.0)."""
    if dt is None:
        dt = datetime.now(timezone.utc)
    
    days_in_year = 366 if (dt.year % 4 == 0 and (dt.year % 100 != 0 or dt.year % 400 == 0)) else 365
    day_of_year = dt.timetuple().tm_yday / days_in_year
    hour_of_day = (dt.hour + dt.minute / 60.0) / 24.0
    day_of_week = dt.weekday() / 6.0
    
    return {
        "seasonality": day_of_year,
        "intraday": hour_of_day,
        "weekly": day_of_week
    }

def get_lunar_entropy(dt: Optional[datetime] = None) -> float:
    """Returns lunar illumination phase (0.0 = New Moon, 1.0 = Full Moon)."""
    if dt is None:
        dt = datetime.now(timezone.utc)
    
    reference_new_moon = datetime(2000, 1, 6, 18, 14, 0, tzinfo=timezone.utc)
    synodic_month = 29.53058867
    
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
        
    days_since = (dt - reference_new_moon).total_seconds() / 86400.0
    phase = (days_since % synodic_month) / synodic_month
    
    # 0 at new moon, 1 at full moon
    illumination = (1 - math.cos(phase * 2 * math.pi)) / 2
    return illumination

async def get_solar_entropy() -> float:
    """Returns normalized Kp index for solar flare activity [0.0, 1.0]."""
    import aiohttp
    
    now = time.time()
    if (now - _solar_cache["timestamp"]) < SOLAR_CACHE_TTL:
        return _solar_cache["kp_normalized"]
        
    try:
        kp_url = "https://services.swpc.noaa.gov/json/planetary_k_index_1m.json"
        async with aiohttp.ClientSession() as session:
            async with session.get(kp_url, timeout=5) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data:
                        latest = data[-1]
                        kp_value = float(latest.get("kp_index", 3.0))
                        normalized = min(1.0, kp_value / 9.0)
                        
                        _solar_cache["timestamp"] = now
                        _solar_cache["kp_normalized"] = normalized
                        return normalized
    except Exception as e:
        logger.debug(f"Solar entropy fetch failed (ignoring): {e}")
        
    return _solar_cache["kp_normalized"] # Fallback

async def get_total_environmental_context(dt: Optional[datetime] = None) -> Dict[str, float]:
    """
    The unified synthesis vector. 
    Drop this directly into the LGNN or Z-Score calculator.
    """
    temporal = get_temporal_entropy(dt)
    lunar = get_lunar_entropy(dt)
    solar = await get_solar_entropy()
    
    return {
        "ctx_seasonality": temporal["seasonality"],
        "ctx_intraday": temporal["intraday"],
        "ctx_weekly": temporal["weekly"],
        "ctx_lunar": lunar,
        "ctx_solar": solar
    }
