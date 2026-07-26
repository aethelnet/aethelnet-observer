"""
System Metrics Tracker
Tracks uptime and error counts for dashboard reporting
"""
import time
import logging
from typing import Optional

logger = logging.getLogger("SystemMetrics")

class SystemMetrics:
    """Tracks system-level metrics like uptime and error counts"""
    _instance: Optional['SystemMetrics'] = None
    _start_time: Optional[float] = None
    _error_count: int = 0
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SystemMetrics, cls).__new__(cls)
        return cls._instance
    
    @classmethod
    def record_startup(cls):
        """Record system startup time"""
        cls._start_time = time.time()
        logger.info(f"[SystemMetrics] Startup time recorded: {cls._start_time}")
    
    @classmethod
    def get_uptime_seconds(cls) -> int:
        """Get system uptime in seconds"""
        if cls._start_time is None:
            return 0
        return int(time.time() - cls._start_time)
    
    @classmethod
    def increment_error_count(cls):
        """Increment error counter"""
        cls._error_count += 1
        logger.debug(f"[SystemMetrics] Error count incremented to {cls._error_count}")
    
    @classmethod
    def get_error_count(cls) -> int:
        """Get current error count"""
        return cls._error_count
    
    @classmethod
    def reset_error_count(cls):
        """Reset error counter (for testing/debugging)"""
        cls._error_count = 0
        logger.info("[SystemMetrics] Error count reset")

    @classmethod
    def get_report(cls) -> dict:
        """Returns a snapshot of system health for UI display"""
        import psutil
        uptime_sec = cls.get_uptime_seconds()
        
        # Format uptime string (H:M:S)
        h = uptime_sec // 3600
        m = (uptime_sec % 3600) // 60
        s = uptime_sec % 60
        uptime_str = f"{h:02d}:{m:02d}:{s:02d}"
        
        try:
            mem = psutil.virtual_memory()
            mem_pct = mem.percent
        except:
            mem_pct = 0.0

        return {
            "uptime": uptime_str,
            "error_count": cls._error_count,
            "mem_pct": mem_pct,
            "loop_latency": 0.001 # Placeholder for future high-freq tracking
        }

class ErrorCounterHandler(logging.Handler):
    """Logging handler that increments error count on ERROR/CRITICAL messages"""
    
    def emit(self, record):
        """Increment error count for ERROR and CRITICAL level messages"""
        if record.levelno >= logging.ERROR:
            SystemMetrics.increment_error_count()

def get_system_metrics() -> SystemMetrics:
    """Get the global SystemMetrics instance"""
    return SystemMetrics()

