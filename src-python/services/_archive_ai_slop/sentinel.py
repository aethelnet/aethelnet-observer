
import asyncio
import logging
import os
import gc
import psutil
import time

logger = logging.getLogger("Sentinel")

class Sentinel:
    """
    The Sentinel (System Health Monitor).
    Prevents Silent Death by monitoring Memory/CPU and Heartbeats.
    """
    def __init__(self, threshold_mb=1024):
        self.pid = os.getpid()
        self.process = psutil.Process(self.pid)
        self.threshold_mb = threshold_mb
        self.is_running = False
        self._last_heartbeat = time.time()
        
    async def start(self):
        """Starts the background monitoring loop."""
        self.is_running = True
        logger.info(f"[SENTINEL] 🛡️ Watchdog Active. PID: {self.pid}")
        try:
            while self.is_running:
                await self._check_vitals()
                await asyncio.sleep(5) # Check every 5 seconds
        except asyncio.CancelledError:
            logger.info("[SENTINEL] Stopping...")
            
    async def _check_vitals(self):
        """Monitors system resources."""
        try:
            # 1. Memory Check
            mem_info = self.process.memory_info()
            rss_mb = mem_info.rss / 1024 / 1024
            
            # 2. CPU Check
            cpu_percent = self.process.cpu_percent(interval=None)
            
            # Log Status (Heartbeat)
            # Log every 60 seconds roughly? Or always?
            # Let's log if significant change or period
            
            # OOM Prevention
            if rss_mb > self.threshold_mb:
                logger.warning(f"[SENTINEL] [WARN] HIGH MEMORY USAGE ({rss_mb:.1f} MB). Triggering Cleanup...")
                gc.collect()
                # Re-check
                mem_info_after = self.process.memory_info()
                rss_mb_after = mem_info_after.rss / 1024 / 1024
                logger.info(f"[SENTINEL] 🧹 Cleanup Complete. RAM: {rss_mb:.1f} MB -> {rss_mb_after:.1f} MB")
                
                if rss_mb_after > self.threshold_mb * 1.5:
                     logger.critical(f"[SENTINEL] 🚨 CRITICAL MEMORY LEAK. RECOMMENDING RESTART.")
            
            # Broadcasting Vitals (Optional, can be added to /ws/stream if needed)
            # For now, just Log.
            # logger.info(f"[SENTINEL] Vitals - CPU: {cpu_percent}% | RAM: {rss_mb:.1f} MB")
            
        except Exception as e:
            logger.error(f"[SENTINEL] Error checking vitals: {e}")

    def stop(self):
        self.is_running = False

def get_sentinel():
    return Sentinel()
