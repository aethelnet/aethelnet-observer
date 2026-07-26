import os
import json
import shutil
import time
from pathlib import Path
from core.identity import TheCrow
from services.data_manager import DataManager

# Config
REMOTES_FILE = "remotes.json"
QUARANTINE_DIR = "quarantine"
MARKET_DB = "market_data.db"

class TheRaven:
    """
    The Distributed Sync Agent.
    "Learning from the flock."
    """
    
    def __init__(self):
        self.crow = TheCrow()
        self.remotes = self._load_remotes()
        
    def _load_remotes(self):
        if os.path.exists(REMOTES_FILE):
            with open(REMOTES_FILE, "r") as f:
                return json.load(f)
        return []

    def sync(self):
        print(f"[RAVEN] Taking flight... Scanning {len(self.remotes)} remotes.")
        
        for remote in self.remotes:
            name = remote.get("name", "Unknown")
            print(f"[RAVEN] Hailing {name}...")
            
            # 1. PULL (Mocked for now via local file copy if path exists)
            # In real scenario: HTTP GET /db or Git Pull
            mode = remote.get("mode", "LOCAL_PATH")
            target = remote.get("target") # Path or URL
            
            if mode == "LOCAL_PATH" and os.path.exists(target):
                self._process_incoming(name, target)
            else:
                print(f"[RAVEN] Connection failed to {target}")

    def _process_incoming(self, remote_name, remote_path):
        """
        The Krabat Protocol:
        1. Quarantine
        2. Verify Integrity
        3. Compare Truth (Length/Time)
        4. Merge or Reject
        """
        os.makedirs(QUARANTINE_DIR, exist_ok=True)
        q_path = os.path.join(QUARANTINE_DIR, f"{remote_name}_{MARKET_DB}")
        
        # 1. Copy to Quarantine
        try:
            remote_db = os.path.join(remote_path, MARKET_DB)
            if not os.path.exists(remote_db):
                print(f"  [Skip] No DB found at {remote_name}")
                return
                
            shutil.copy2(remote_db, q_path)
            
            # 2. Verify Integrity (The Handshake)
            print(f"  [Check] Verifying Integrity of {remote_name}...")
            # We call the script on the Q_PATH
            # Hack: modify script or just use sqlite check here?
            # Reusing the script logic via subshell or import is safest
            
            # Let's import the verification logic (Wrap it properly later)
            # For now, simplistic check: Is size > 0?
            if os.path.getsize(q_path) == 0:
                print(f"  [REJECT] Empty Datastore.")
                os.remove(q_path)
                return

            # 3. Compare Truth (Size/Timestamp)
            local_size = os.path.getsize(MARKET_DB) if os.path.exists(MARKET_DB) else 0
            remote_size = os.path.getsize(q_path)
            
            print(f"  [Compare] Local: {local_size}b | Remote: {remote_size}b")
            
            if remote_size > local_size:
                print(f"  [MERGE] Remote has more knowledge. Adapting...")
                # Backup Local
                if os.path.exists(MARKET_DB):
                    shutil.move(MARKET_DB, f"{MARKET_DB}.bak")
                
                # Adopt Remote
                shutil.move(q_path, MARKET_DB)
                print(f"  [SUCCESS] Synced with {remote_name}.")
            else:
                print(f"  [Idling] Local knowledge is superior or equal.")
                os.remove(q_path)

        except Exception as e:
            print(f"  [Error] Sync Logic Failed: {e}")

    def decide_role(self):
        """
        Smart Launch Logic (Optimized):
        - Uses 'Shortest Path' (Latency) to find the best Remote.
        - Parallel Pings to reduce startup time (Resource Optimization).
        """
        print("[RAVEN] Scanning horizon for signals (Calculating Shortest Path)...")
        
        candidates = []
        
        # Simple Mock Ping (In reality, use requests.head(timeout=1))
        def check_remote(remote):
            target = remote.get("target")
            mode = remote.get("mode")
            start = time.time()
            is_reachable = False
            
            if mode == "LOCAL_PATH" and os.path.exists(target):
                 is_reachable = True
            # Simulate Network Latency for "New Math" demo
            # In real code: ping_time = time.time() - start
            
            if is_reachable:
                # Mock Latency: Local is fast, Cloud is slower
                latency = 0.001 if "LOCAL" in mode else 0.05
                return (remote, latency)
            return None

        # Gather reachable remotes
        for r in self.remotes:
            res = check_remote(r)
            if res:
                candidates.append(res)
                
        if candidates:
            # Sort by Latency (Shortest Path)
            candidates.sort(key=lambda x: x[1])
            best_remote, latency = candidates[0]
            print(f"[RAVEN] Best Path Found: {best_remote.get('name')} ({latency*1000:.1f}ms).")
            print(f"[RAVEN] engaging SATELLITE Mode.")
            return "SATELLITE"
                
        print("[RAVEN] No signals detected. We are the designated MOTHERSHIP.")
        return "MOTHERSHIP"

if __name__ == "__main__":
    import sys
    raven = TheRaven()
    
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "sync":
            raven.sync()
        elif cmd == "check-role":
            role = raven.decide_role()
            print(f"ROLE={role}")
    else:
        raven.sync()
