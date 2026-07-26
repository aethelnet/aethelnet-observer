import os
import signal
import sys
import tempfile
import time
import shutil
import logging
from contextlib import contextmanager

logger = logging.getLogger("AuraticFailsafe")

class GracefulKiller:
    """
    Listens for SIGINT/SIGTERM and sets a flag.
    Allows loops to finish their current iteration before dying.
    """
    kill_now = False

    def __init__(self):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, signum, frame):
        logger.warning(f"[FAILSAFE] Signal {signum} received. Initiating Graceful Shutdown...")
        self.kill_now = True

@contextmanager
def atomic_write(filepath, mode='w', encoding='utf-8', make_dirs=True):
    """
    Context manager for atomic file writes.
    Writes to a temp file first, then renames it to the target filepath on success.
    Ensures no partial writes corrupt critical state files.
    
    Usage:
    with atomic_write("config.json") as f:
        json.dump(data, f)
    """
    # Create directory if needed
    if make_dirs:
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        
    # Create temp file in the same directory to ensure atomic rename (os.replace) works
    # across different mount points if necessary (though usually tmp is ensuring this).
    # Actually, os.replace checks for same device. 
    # Best practice: write to .tmp file in same dir.
    
    dir_name = os.path.dirname(os.path.abspath(filepath))
    base_name = os.path.basename(filepath)
    temp_name = f".{base_name}.tmp"
    temp_path = os.path.join(dir_name, temp_name)
    
    f = None
    try:
        # Open the temp file
        if 'b' in mode:
            f = open(temp_path, mode)
        else:
            f = open(temp_path, mode, encoding=encoding)
            
        yield f
        
        # Flush and Sync to disk
        f.flush()
        os.fsync(f.fileno())
        f.close()
        
        # Atomic Rename
        os.replace(temp_path, filepath)
        # logger.debug(f"[FAILSAFE] Atomically saved {filepath}")
        
    except Exception as e:
        logger.error(f"[FAILSAFE] Failed to write {filepath}: {e}")
        if f:
             try:
                 f.close()
             except:
                 pass
        # Cleanup temp
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise e

class PanicSwitch:
    """
    Global Panic Mechanism.
    Checks/Writes a lock file that stops all sensitive operations.
    """
    LOCK_FILE = "GLOBAL_PANIC.lock"
    
    @staticmethod
    def trigger(reason: str = "Unknown"):
        with atomic_write(PanicSwitch.LOCK_FILE) as f:
            f.write(f"PANIC TRIGGERED AT {time.time()}: {reason}")
        logger.critical(f"[FAILSAFE] !!! GLOBAL PANIC TRIGGERED: {reason} !!!")
        
    @staticmethod
    def clear():
        if os.path.exists(PanicSwitch.LOCK_FILE):
            os.remove(PanicSwitch.LOCK_FILE)
        logger.info("[FAILSAFE] Global Panic Cleared. Systems Resuming.")
        
    @staticmethod
    def is_active() -> bool:
        return os.path.exists(PanicSwitch.LOCK_FILE)
