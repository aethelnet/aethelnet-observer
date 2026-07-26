"""
Event Hydra - Multi-Source Economic Calendar Aggregator
Fetches events from multiple providers, calculates consensus, and prepares ML training data.
"""
import asyncio
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from difflib import SequenceMatcher
import statistics
import time

logger = logging.getLogger("EventHydra")


class EventHydra:
    """
    The Hydra Pattern for Economic Events.
    Aggregates data from multiple calendar providers to:
    1. Calculate consensus forecasts
    2. Detect forecast divergence (disagreement)
    3. Compute surprise values (actual vs consensus)
    """
    
    def __init__(self):
        self._cache: List[Dict] = []
        self._last_fetch = 0
        self._cache_ttl = 3600  # 1 hour
        
        # Provider registry
        self._providers = {}
        self._register_providers()
        
    def _register_providers(self):
        """Register available calendar providers."""
        try:
            from services.economic_calendar import get_economic_calendar
            self._providers['forexfactory'] = get_economic_calendar()
            logger.info("[HYDRA] Registered: ForexFactory")
        except Exception as e:
            logger.warning(f"[HYDRA] ForexFactory unavailable: {e}")
            
        try:
            from services.investing_calendar import get_investing_calendar
            self._providers['investing'] = get_investing_calendar()
            logger.info("[HYDRA] Registered: Investing.com")
        except Exception as e:
            logger.warning(f"[HYDRA] Investing.com unavailable: {e}")
    
    def _similarity(self, a: str, b: str) -> float:
        """Calculate string similarity ratio (0-1)."""
        return SequenceMatcher(None, a.lower(), b.lower()).ratio()
    
    def _normalize_title(self, title: str) -> str:
        """Normalize event title for matching."""
        # Remove common variations
        normalized = title.lower().strip()
        normalized = normalized.replace('m/m', 'mom')
        normalized = normalized.replace('y/y', 'yoy')
        normalized = normalized.replace('q/q', 'qoq')
        normalized = normalized.replace('-', ' ')
        normalized = ' '.join(normalized.split())  # Normalize whitespace
        return normalized
    
    def _events_match(self, e1: Dict, e2: Dict) -> bool:
        """Check if two events are the same event from different providers."""
        # Same country
        if e1.get('country', '').upper() != e2.get('country', '').upper():
            return False
            
        # Same date (within 1 day tolerance for timezone differences)
        try:
            ts1 = e1.get('timestamp', 0)
            ts2 = e2.get('timestamp', 0)
            if abs(ts1 - ts2) > 86400 * 2:  # More than 2 days apart
                return False
        except:
            pass
        
        # Similar title
        title1 = self._normalize_title(e1.get('title', ''))
        title2 = self._normalize_title(e2.get('title', ''))
        
        if self._similarity(title1, title2) > 0.7:
            return True
            
        # Check for key words match
        words1 = set(title1.split())
        words2 = set(title2.split())
        common = words1 & words2
        
        # If at least 2 significant words match
        significant_words = {w for w in common if len(w) > 3}
        if len(significant_words) >= 2:
            return True
            
        return False
    
    async def fetch_all(self) -> List[Dict]:
        """Fetch events from all registered providers."""
        now = time.time()
        
        if now - self._last_fetch < self._cache_ttl and self._cache:
            return self._cache
            
        all_events = {}  # provider -> events list
        
        # Fetch from all providers in parallel
        tasks = []
        provider_names = []
        
        for name, provider in self._providers.items():
            provider_names.append(name)
            if hasattr(provider, 'get_upcoming_events'):
                tasks.append(provider.get_upcoming_events(limit=100))
            elif hasattr(provider, 'get_events'):
                tasks.append(provider.get_events(limit=100))
            else:
                tasks.append(asyncio.coroutine(lambda: [])())
                
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for name, result in zip(provider_names, results):
            if isinstance(result, Exception):
                logger.warning(f"[HYDRA] Provider {name} failed: {result}")
                all_events[name] = []
            else:
                all_events[name] = result
                logger.info(f"[HYDRA] {name}: {len(result)} events")
                
        # Merge and calculate consensus
        merged = self._merge_events(all_events)
        self._cache = merged
        self._last_fetch = now
        
        return merged
    
    def _merge_events(self, provider_events: Dict[str, List[Dict]]) -> List[Dict]:
        """
        Merge events from multiple providers.
        Match similar events and calculate consensus.
        """
        merged = []
        seen_events = []  # Track matched events to avoid duplicates
        
        # Use ForexFactory as primary source (most structured)
        primary = provider_events.get('forexfactory', [])
        secondary_all = []
        for name, events in provider_events.items():
            if name != 'forexfactory':
                for e in events:
                    e['_source'] = name
                secondary_all.extend(events)
        
        for event in primary:
            event['_source'] = 'forexfactory'
            
            # Find matches in secondary sources
            matches = [event]
            for sec_event in secondary_all:
                if sec_event in seen_events:
                    continue
                if self._events_match(event, sec_event):
                    matches.append(sec_event)
                    seen_events.append(sec_event)
            
            # Calculate consensus
            merged_event = self._calculate_consensus(matches)
            merged.append(merged_event)
            
        # Add any unmatched secondary events
        for sec_event in secondary_all:
            if sec_event not in seen_events:
                # Single source event
                sec_event['consensus_forecast'] = sec_event.get('forecast')
                sec_event['forecast_divergence'] = 0.0
                sec_event['source_count'] = 1
                sec_event['sources'] = [sec_event.get('_source', 'unknown')]
                merged.append(sec_event)
                
        # Sort by timestamp
        merged.sort(key=lambda x: x.get('timestamp', 0))
        
        return merged
    
    def _calculate_consensus(self, matches: List[Dict]) -> Dict:
        """
        Calculate consensus values from matched events.
        Returns a single merged event with consensus metrics.
        """
        if len(matches) == 1:
            event = matches[0].copy()
            event['consensus_forecast'] = event.get('forecast')
            event['forecast_divergence'] = 0.0
            event['source_count'] = 1
            event['sources'] = [event.get('_source', 'unknown')]
            return event
            
        # Use first match as base (primary source)
        merged = matches[0].copy()
        
        # Collect forecasts from all sources
        forecasts = []
        actuals = []
        sources = []
        
        for m in matches:
            source = m.get('_source', 'unknown')
            sources.append(source)
            
            # Parse forecast
            forecast_val = self._parse_value(m.get('forecast', ''))
            if forecast_val is not None:
                forecasts.append({'source': source, 'value': forecast_val})
                
            # Parse actual
            actual_val = self._parse_value(m.get('actual', ''))
            if actual_val is not None:
                actuals.append(actual_val)
        
        # Calculate consensus forecast (average)
        if forecasts:
            values = [f['value'] for f in forecasts]
            merged['consensus_forecast'] = statistics.mean(values)
            
            # Calculate divergence (std deviation)
            if len(values) > 1:
                merged['forecast_divergence'] = statistics.stdev(values)
            else:
                merged['forecast_divergence'] = 0.0
                
            # Store per-source forecasts
            merged['forecast_ff'] = next((f['value'] for f in forecasts if f['source'] == 'forexfactory'), None)
            merged['forecast_inv'] = next((f['value'] for f in forecasts if f['source'] == 'investing'), None)
        else:
            merged['consensus_forecast'] = None
            merged['forecast_divergence'] = 0.0
            
        # Calculate surprise (actual - consensus)
        if actuals and merged.get('consensus_forecast') is not None:
            actual = actuals[0]  # Use first available actual
            merged['surprise'] = actual - merged['consensus_forecast']
        else:
            merged['surprise'] = None
            
        merged['source_count'] = len(matches)
        merged['sources'] = sources
        
        return merged
    
    def _parse_value(self, value_str: str) -> Optional[float]:
        """Parse economic value string to float."""
        if not value_str or value_str.strip() in ['N/A', '', '-', '...']:
            return None
            
        value_str = value_str.strip().upper()
        multiplier = 1.0
        
        if value_str.endswith('%'):
            value_str = value_str[:-1]
        elif value_str.endswith('K'):
            value_str = value_str[:-1]
            multiplier = 1000
        elif value_str.endswith('M'):
            value_str = value_str[:-1]
            multiplier = 1_000_000
        elif value_str.endswith('B'):
            value_str = value_str[:-1]
            multiplier = 1_000_000_000
            
        try:
            return float(value_str.replace(',', '')) * multiplier
        except ValueError:
            return None
    
    async def get_recent_impacts(self, window_hours: int = 24) -> List[Dict]:
        """
        Get events with actual values released in the last N hours.
        Useful for real-time ML feature injection.
        """
        events = await self.fetch_all()
        now = time.time()
        cutoff = now - (window_hours * 3600)
        
        recent = []
        for e in events:
            ts = e.get('timestamp', 0)
            if ts < cutoff or ts > now:
                continue
            if e.get('actual') and e.get('surprise') is not None:
                recent.append(e)
                
        return recent
    
    async def get_upcoming_high_impact(self, hours: int = 24) -> List[Dict]:
        """Get high-impact events in the next N hours."""
        events = await self.fetch_all()
        now = time.time()
        cutoff = now + (hours * 3600)
        
        upcoming = []
        for e in events:
            ts = e.get('timestamp', 0)
            if ts < now or ts > cutoff:
                continue
            if e.get('impact', '').lower() in ['high', 'medium']:
                upcoming.append(e)
                
        return upcoming
    
    def get_event_bias(self, country: str) -> Dict[str, float]:
        """
        Calculate directional bias for a currency based on recent event surprises.
        Returns: {'bias': -1 to 1, 'confidence': 0 to 1}
        """
        if not self._cache:
            return {'bias': 0.0, 'confidence': 0.0}
            
        now = time.time()
        window = 24 * 3600  # Last 24 hours
        
        surprises = []
        for e in self._cache:
            if e.get('country', '').upper() != country.upper():
                continue
            ts = e.get('timestamp', 0)
            if ts < now - window or ts > now:
                continue
            if e.get('surprise') is not None:
                # Weight by impact
                weight = 1.0
                impact = e.get('impact', '').lower()
                if impact == 'high':
                    weight = 3.0
                elif impact == 'medium':
                    weight = 2.0
                surprises.append({'value': e['surprise'], 'weight': weight})
        
        if not surprises:
            return {'bias': 0.0, 'confidence': 0.0}
            
        # Calculate weighted average surprise
        total_weight = sum(s['weight'] for s in surprises)
        weighted_sum = sum(s['value'] * s['weight'] for s in surprises)
        avg_surprise = weighted_sum / total_weight
        
        # Normalize to -1 to 1 range (assuming typical surprise is ±1%)
        bias = max(-1.0, min(1.0, avg_surprise))
        
        # Confidence based on number of events and their impact
        confidence = min(1.0, total_weight / 5.0)
        
        return {'bias': bias, 'confidence': confidence}


# Singleton
_hydra_instance = None

def get_event_hydra():
    global _hydra_instance
    if _hydra_instance is None:
        _hydra_instance = EventHydra()
    return _hydra_instance


# CLI Test
if __name__ == "__main__":
    import asyncio
    
    async def test():
        hydra = get_event_hydra()
        events = await hydra.fetch_all()
        
        print(f"\n=== EVENT HYDRA: {len(events)} Events ===\n")
        
        for e in events[:10]:
            sources = e.get('source_count', 1)
            div = e.get('forecast_divergence', 0)
            print(f"[{e.get('country', '??')}] {e.get('title', 'Unknown')}")
            print(f"    Forecast: {e.get('forecast')} | Consensus: {e.get('consensus_forecast')}")
            print(f"    Divergence: {div:.3f} | Sources: {sources}")
            print(f"    Actual: {e.get('actual', '-')} | Surprise: {e.get('surprise', '-')}")
            print()
            
    asyncio.run(test())
