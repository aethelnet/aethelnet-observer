
import os
import json
import tempfile
import logging

logger = logging.getLogger("AuraticUtils")

def atomic_write(filepath, data, mode='w', encoding='utf-8'):
    """
    Writes data to a temporary file first, then renames it to the target file.
    This ensures that the target file is never left in a corrupted state
    if the process crashes during write.
    
    Args:
        filepath (str): Target file path.
        data (str or dict): Content to write. If dict, assumes JSON.
        mode (str): File mode ('w' or 'wb').
        encoding (str): Encoding for text mode.
    """
    dir_name = os.path.dirname(os.path.abspath(filepath))
    base_name = os.path.basename(filepath)
    
    # Create temp file in the same directory to ensure atomic move
    # (os.rename is only atomic on the same filesystem)
    tmp_fd, tmp_path = tempfile.mkstemp(prefix=f".{base_name}.tmp-", dir=dir_name)
    
    try:
        with os.fdopen(tmp_fd, mode, encoding=encoding if 'b' not in mode else None) as f:
            if isinstance(data, dict) or isinstance(data, list):
                json.dump(data, f, indent=4)
            else:
                f.write(data)
                
            # Force flush to disk
            f.flush()
            os.fsync(f.fileno())
            
        # Atomic replacement
        os.replace(tmp_path, filepath)
        # logger.debug(f"[ATOMIC] Saved {filepath}")
        
    except Exception as e:
        logger.error(f"[ATOMIC] Write Failed for {filepath}: {e}")
        # Clean up temp file
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise e


# Context-manager wrapper for atomic_write (compatibility with code using context-manager style)
def atomic_write_ctx(filepath, mode='w', encoding='utf-8', make_dirs=True):
    """
    Context manager wrapper delegating to core.failsafe.atomic_write to provide
    the context-manager style API for atomic writes.

    Usage:
        with atomic_write_ctx("file.txt") as f:
            f.write("data")
    """
    try:
        from core.failsafe import atomic_write as _failsafe_atomic_write
        return _failsafe_atomic_write(filepath, mode=mode, encoding=encoding, make_dirs=make_dirs)
    except Exception:
        # If import fails, raise to surface the issue immediately
        raise
