"""
Lightweight in-memory cache manager for performance optimization.
Used for expensive API calls like wallet reconciliation.
"""

import asyncio
import time
import logging
from typing import Optional, Dict, Any, Callable
from datetime import datetime, timezone

logger = logging.getLogger("CacheManager")


class CacheEntry:
    """Single cache entry with TTL support."""
    
    def __init__(self, data: Any, ttl_seconds: int):
        self.data = data
        self.timestamp = time.time()
        self.ttl = ttl_seconds
    
    def is_valid(self) -> bool:
        """Check if cache entry is still valid."""
        return (time.time() - self.timestamp) < self.ttl
    
    def age(self) -> float:
        """Return age of cache entry in seconds."""
        return time.time() - self.timestamp


class CacheManager:
    """
    In-memory cache with TTL support and background refresh.
    Thread-safe for async operations.
    """
    
    def __init__(self):
        self._cache: Dict[str, CacheEntry] = {}
        self._locks: Dict[str, asyncio.Lock] = {}
        self._refresh_tasks: Dict[str, asyncio.Task] = {}
    
    def _get_lock(self, key: str) -> asyncio.Lock:
        """Get or create lock for a specific cache key."""
        if key not in self._locks:
            self._locks[key] = asyncio.Lock()
        return self._locks[key]
    
    async def get(self, key: str) -> Optional[Any]:
        """Get cached value if valid, None otherwise."""
        if key not in self._cache:
            return None
        
        entry = self._cache[key]
        if not entry.is_valid():
            logger.debug(f"[CACHE] {key} expired (age: {entry.age():.1f}s)")
            del self._cache[key]
            return None
        
        logger.debug(f"[CACHE] {key} HIT (age: {entry.age():.1f}s)")
        return entry.data
    
    async def set(self, key: str, value: Any, ttl_seconds: int = 30):
        """Set cache value with TTL."""
        async with self._get_lock(key):
            self._cache[key] = CacheEntry(value, ttl_seconds)
            logger.debug(f"[CACHE] {key} SET (TTL: {ttl_seconds}s)")
    
    async def get_or_compute(
        self, 
        key: str, 
        compute_func: Callable, 
        ttl_seconds: int = 30,
        background_refresh: bool = False
    ) -> Any:
        """
        Get cached value or compute if missing/expired.
        
        Args:
            key: Cache key
            compute_func: Async function to compute value
            ttl_seconds: Cache TTL
            background_refresh: If True, return stale data and refresh in background
        
        Returns:
            Cached or computed value
        """
        # Try to get from cache
        cached = await self.get(key)
        if cached is not None:
            return cached
        
        # Check if stale data exists (for background refresh mode)
        if background_refresh and key in self._cache:
            stale_entry = self._cache[key]
            logger.info(f"[CACHE] {key} STALE (age: {stale_entry.age():.1f}s), returning old data and refreshing in background")
            
            # Start background refresh if not already running
            if key not in self._refresh_tasks or self._refresh_tasks[key].done():
                self._refresh_tasks[key] = asyncio.create_task(
                    self._background_refresh(key, compute_func, ttl_seconds)
                )
            
            return stale_entry.data
        
        # Compute value (with lock to prevent thundering herd)
        async with self._get_lock(key):
            # Double-check after acquiring lock
            cached = await self.get(key)
            if cached is not None:
                return cached
            
            logger.info(f"[CACHE] {key} MISS, computing...")
            start = time.time()
            
            try:
                value = await compute_func()
                elapsed = time.time() - start
                logger.info(f"[CACHE] {key} COMPUTED in {elapsed:.2f}s")
                
                await self.set(key, value, ttl_seconds)
                return value
            except Exception as e:
                logger.error(f"[CACHE] {key} COMPUTE FAILED: {e}")
                # Return stale data if available
                if key in self._cache:
                    logger.warning(f"[CACHE] {key} returning STALE data due to error")
                    return self._cache[key].data
                raise
    
    async def _background_refresh(self, key: str, compute_func: Callable, ttl_seconds: int):
        """Refresh cache in background."""
        try:
            logger.debug(f"[CACHE] {key} background refresh started")
            value = await compute_func()
            await self.set(key, value, ttl_seconds)
            logger.info(f"[CACHE] {key} background refresh complete")
        except Exception as e:
            logger.error(f"[CACHE] {key} background refresh failed: {e}")
    
    async def invalidate(self, key: str):
        """Invalidate cache entry."""
        if key in self._cache:
            del self._cache[key]
            logger.info(f"[CACHE] {key} INVALIDATED")
    
    async def clear(self):
        """Clear all cache entries."""
        self._cache.clear()
        logger.info("[CACHE] ALL CLEARED")
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total = len(self._cache)
        valid = sum(1 for entry in self._cache.values() if entry.is_valid())
        expired = total - valid
        
        entries = {}
        for key, entry in self._cache.items():
            entries[key] = {
                "age_seconds": entry.age(),
                "ttl_seconds": entry.ttl,
                "valid": entry.is_valid(),
                "size_bytes": len(str(entry.data))  # Rough estimate
            }
        
        return {
            "total_entries": total,
            "valid_entries": valid,
            "expired_entries": expired,
            "entries": entries
        }


# Singleton instance
_cache_manager: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """Get or create global cache manager instance."""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager





