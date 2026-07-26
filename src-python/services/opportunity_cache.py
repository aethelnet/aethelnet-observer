"""
Opportunity Cache Service
Caches opportunities by ID for efficient lookup.
"""
import logging
from typing import Dict, Optional, Any
from datetime import datetime, timezone
import time

logger = logging.getLogger("OpportunityCache")


class OpportunityCache:
    """
    Caches opportunities by ID with automatic expiration based on opportunity expiry time.
    
    Opportunities are automatically removed when they expire.
    """
    
    def __init__(self):
        # opportunity_id -> {
        #   'opportunity': Dict,
        #   'cached_at': float (timestamp),
        #   'expires_at': float (timestamp)
        # }
        self._cache: Dict[str, Dict[str, Any]] = {}
        # Maximum cache size to prevent memory issues
        self._max_size = 1000
        # Cleanup interval (seconds) - check for expired entries
        self._last_cleanup = time.time()
        self._cleanup_interval = 60  # Clean up every 60 seconds
    
    def cache_opportunity(self, opportunity: Dict[str, Any]) -> None:
        """
        Cache an opportunity by its ID.
        
        Args:
            opportunity: Opportunity dict with 'id' and 'expires_at' fields
        """
        opp_id = opportunity.get('id')
        if not opp_id:
            logger.warning("[OpportunityCache] Cannot cache opportunity without ID")
            return
        
        # Parse expiration time
        expires_at_str = opportunity.get('expires_at')
        if expires_at_str:
            try:
                # Handle ISO format timestamps
                if isinstance(expires_at_str, str):
                    expires_at = datetime.fromisoformat(expires_at_str.replace('Z', '+00:00'))
                    expires_timestamp = expires_at.timestamp()
                else:
                    # Assume it's already a timestamp
                    expires_timestamp = float(expires_at_str)
            except Exception as e:
                logger.warning(f"[OpportunityCache] Could not parse expires_at for {opp_id}: {e}")
                # Default to 1 hour from now if parsing fails
                expires_timestamp = time.time() + 3600
        else:
            # Default to 1 hour from now if no expiration
            expires_timestamp = time.time() + 3600
        
        # Clean up if cache is too large
        if len(self._cache) >= self._max_size:
            self._cleanup_expired()
            # If still too large, remove oldest entries
            if len(self._cache) >= self._max_size:
                sorted_entries = sorted(self._cache.items(), key=lambda x: x[1].get('cached_at', 0))
                entries_to_remove = len(self._cache) - self._max_size + 100  # Remove extra to make room
                for opp_id_to_remove, _ in sorted_entries[:entries_to_remove]:
                    self._cache.pop(opp_id_to_remove, None)
                logger.info(f"[OpportunityCache] Cache full, removed {entries_to_remove} oldest entries")
        
        # Cache the opportunity
        self._cache[opp_id] = {
            'opportunity': opportunity.copy(),
            'cached_at': time.time(),
            'expires_at': expires_timestamp
        }
        
        logger.debug(f"[OpportunityCache] Cached opportunity {opp_id} (expires in {expires_timestamp - time.time():.0f}s)")
    
    def get_opportunity(self, opportunity_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a cached opportunity by ID.
        
        Args:
            opportunity_id: Opportunity ID
        
        Returns:
            Opportunity dict if found and not expired, None otherwise
        """
        # Periodic cleanup
        now = time.time()
        if now - self._last_cleanup > self._cleanup_interval:
            self._cleanup_expired()
            self._last_cleanup = now
        
        cached_entry = self._cache.get(opportunity_id)
        if not cached_entry:
            return None
        
        # Check if expired
        if now >= cached_entry['expires_at']:
            self._cache.pop(opportunity_id, None)
            logger.debug(f"[OpportunityCache] Opportunity {opportunity_id} expired, removed from cache")
            return None
        
        return cached_entry['opportunity']
    
    def _cleanup_expired(self) -> None:
        """Remove expired opportunities from cache."""
        now = time.time()
        expired_ids = [
            opp_id for opp_id, entry in self._cache.items()
            if now >= entry.get('expires_at', 0)
        ]
        
        for opp_id in expired_ids:
            self._cache.pop(opp_id, None)
        
        if expired_ids:
            logger.debug(f"[OpportunityCache] Cleaned up {len(expired_ids)} expired opportunities")
    
    def clear(self) -> None:
        """Clear all cached opportunities."""
        count = len(self._cache)
        self._cache.clear()
        logger.info(f"[OpportunityCache] Cleared {count} cached opportunities")

    def invalidate_for_symbol(self, symbol: str) -> None:
        """
        Invalidate (remove) all cached opportunities for a specific symbol.
        Used when a new conflicting signal is generated (e.g. BUY flips to SELL).
        """
        to_remove = [
            opp_id for opp_id, entry in self._cache.items()
            if entry['opportunity'].get('symbol') == symbol
        ]
        
        for opp_id in to_remove:
            self._cache.pop(opp_id, None)
            
        if to_remove:
            logger.info(f"[OpportunityCache] Invalidated {len(to_remove)} signals for {symbol} due to regime flip.")
    
    def get_all_opportunities(self) -> list:
        """
        Get all valid (non-expired) cached opportunities.
        """
        # Periodic cleanup
        now = time.time()
        if now - self._last_cleanup > self._cleanup_interval:
            self._cleanup_expired()
            self._last_cleanup = now
            
        valid_opps = []
        for opp_id, entry in list(self._cache.items()):
            if now < entry.get('expires_at', 0):
                valid_opps.append(entry['opportunity'])
            else:
                # Lazy expire
                self._cache.pop(opp_id, None)
                
        # --- DEBUG/FAILSAFE: If empty, inject a Persistent Test Signal ---
        if not valid_opps:
            # Empty state allows Pidgin Poetry to trigger
            pass
            
        return valid_opps

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        now = time.time()
        active_count = sum(
            1 for entry in self._cache.values()
            if now < entry.get('expires_at', 0)
        )
        expired_count = len(self._cache) - active_count
        
        return {
            'total_cached': len(self._cache),
            'active': active_count,
            'expired': expired_count,
            'max_size': self._max_size
        }

    def get_top_opportunities(self, limit: int = 5) -> list:
        """
        Get the top N valid opportunities, sorted by confidence/score.
        """
        opps = self.get_all_opportunities()
        
        # Sort key: prioritize 'score', then 'confidence', then recency
        # Assuming opportunity dict has these fields
        def sort_key(opp):
            score = opp.get('score', 0)
            if score is None: score = 0
            
            conf = opp.get('confidence', 0)
            if conf is None: conf = 0
            
            # Timestamp fallback
            ts = opp.get('created_at')
            if isinstance(ts, str):
                try:
                    ts = datetime.fromisoformat(ts.replace('Z', '+00:00')).timestamp()
                except:
                    ts = 0
            elif not isinstance(ts, (int, float)):
                ts = 0
                
            return (float(score), float(conf), ts)
            
        opps.sort(key=sort_key, reverse=True)
        return opps[:limit]
# Singleton instance
_cache_instance: Optional[OpportunityCache] = None


def get_opportunity_cache() -> OpportunityCache:
    """Get or create the singleton OpportunityCache instance."""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = OpportunityCache()
    return _cache_instance


