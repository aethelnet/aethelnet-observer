"""
Telemetry service for logging brain state and trading performance for analysis and debugging.
Writes JSON Lines to backend/data/*.jsonl. Designed to be lightweight and best-effort so it does
not block or crash the main trading loop.
"""

import json
import os
from datetime import datetime

class TelemetryService:
    """
    Simple telemetry service for logging brain state during training.
    """
    def __init__(self):
        self.log_file = "backend/data/telemetry.jsonl"
        os.makedirs("backend/data", exist_ok=True)
        
    def log(self, episode_id, step, brain_state):
        """
        Log brain state for analysis.
        
        Args:
            episode_id: Training episode ID
            step: Step within episode
            brain_state: Dict containing brain state info
        """
        try:
            entry = {
                'timestamp': datetime.now().isoformat(),
                'episode_id': episode_id,
                'step': step,
                'brain_state': brain_state
            }
            
            with open(self.log_file, 'a') as f:
                f.write(json.dumps(entry) + '\n')
                
        except Exception as e:
            print(f"[Telemetry] Failed to log: {e}")

class BrainTelemetry:
    """
    High-frequency logging for the engine's internal state (for visualizations such as "Galaxy View").
    Collects frames into an in-memory buffer and periodically flushes to disk to minimize IO overhead.
    """
    def __init__(self, log_file="backend/data/brain_telemetry.jsonl"):
        self.log_file = log_file
        self.buffer = []
        self.last_flush = 0
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        
    def log(self, episode_id, tick, brain_state):
        """
        Logs a single frame of brain state.
        """
        import time
        entry = {
            'episode_id': episode_id,
            'tick': tick,
            'timestamp': time.time(),
            'state': brain_state
        }
        self.buffer.append(json.dumps(entry))
        
        # Flush every 100 entries or 1 second
        if len(self.buffer) > 100 or (time.time() - self.last_flush) > 1.0:
            self.flush()
            
    def flush(self):
        if not self.buffer: 
            return
        print(f"TELEMETRY FLUSH: {len(self.buffer)} items")
        
        try:
            import time
            with open(self.log_file, 'a') as f:
                f.write('\n'.join(self.buffer) + '\n')
                f.flush()
                os.fsync(f.fileno())
            self.buffer = []
            self.last_flush = time.time()
        except Exception as e:
            print(f"Telemetry Error: {e}")

# Global instances
telemetry = TelemetryService()
brain_telemetry = BrainTelemetry()
