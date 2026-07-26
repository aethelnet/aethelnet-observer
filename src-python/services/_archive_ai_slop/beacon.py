
import asyncio
import socket
import logging
import json
import hmac
import hashlib
import os
import sys
import threading
import time
from core.failsafe import PanicSwitch

logger = logging.getLogger("AuraticBeacon")

UDP_PORT = 50000

class BeaconListener:
    def __init__(self):
        self.active = False
        self.sock = None
        self.thread = None
        self.key = self._load_key()

    def _load_key(self):
        try:
            from config.paths import get_handshake_key_path
            handshake_path = get_handshake_key_path()
            
            if not os.path.exists(handshake_path):
                # Auto-generate key if missing
                import secrets
                new_key = secrets.token_hex(32)
                with open(handshake_path, "w") as f:
                    f.write(new_key)
                logger.info(f"[Beacon] Generated new Handshake Key at {handshake_path}")
                return new_key
                
            with open(handshake_path, "r") as f:
                return f.read().strip()
        except Exception as e:
            logger.error(f"Failed to load/generate handshake key: {e}")
            return None

    def start_background(self):
        """Starts the UDP listener in a daemon thread."""
        if not self.key:
            logger.warning("No Handshake Key found. Remote Shutdown Disabled.")
            return

        self.active = True
        self.thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.thread.start()
        logger.info(f"Beacon Listening on UDP {UDP_PORT} (Remote Override Enabled)")

    def _verify_signature(self, payload_dict, signature):
        """Verifies that the command came from a holder of the Master Key."""
        # Reconstruct payload string exactly as sender did
        curr_payload_str = json.dumps(payload_dict)
        
        expected_sig = hmac.new(
            self.key.encode(),
            curr_payload_str.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected_sig, signature)

    def _listen_loop(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            # SECURITY HARDENING: Bind to localhost ONLY.
            # Prevents exposure to LAN/WiFi. 
            self.sock.bind(("127.0.0.1", UDP_PORT))
        except Exception as e:
            logger.error(f"Failed to bind Beacon port {UDP_PORT}: {e}")
            return

        while self.active:
            try:
                data, addr = self.sock.recvfrom(1024)
                message = json.loads(data.decode('utf-8'))
                
                payload = message.get("payload")
                signature = message.get("sig")
                
                if not payload or not signature:
                    continue
                    
                # 1. Verify Signature
                if self._verify_signature(payload, signature):
                    cmd = payload.get("cmd")
                    ts = payload.get("ts", 0)
                    
                    # 2. Replay Protection (Window of 10 seconds)?
                    # For now, simplistic.
                    if time.time() - ts > 30:
                        logger.warning(f"Ignored Stale Command from {addr}")
                        continue

                    if cmd == "SHUTDOWN":
                        logger.critical(f"[WARN] OVERRIDE SIGNAL RECEIVED FROM {addr}. SELF-DESTRUCT INITIATED.")
                        PanicSwitch.trigger("Remote Override Signal")
                        os._exit(1)
                        
                    elif cmd == "VOTE":
                        # Remote Intelligence Integration
                        strat = payload.get("strat", "Unknown")
                        val = float(payload.get("val", 0.0))
                        self.register_vote(strat, val, addr)

                else:
                    logger.warning(f"Invalid Signature received from {addr}")

            except Exception as e:
                if self.active:
                    logger.error(f"Beacon Error: {e}")

    def register_vote(self, strat: str, val: float, addr):
        """Stores a remote vote with a timestamp."""
        if not hasattr(self, 'remote_votes'): self.remote_votes = {}
        self.remote_votes[strat] = {
            "val": val,
            "ts": time.time(),
            "source": addr[0]
        }
        # logger.info(f"[GRID] 🗳️ Remote Vote from {strat} ({addr[0]}): {val}")

    def get_remote_votes(self) -> dict:
        """Returns valid votes (TTL < 10s)."""
        if not hasattr(self, 'remote_votes'): return {}
        
        now = time.time()
        valid = {}
        for strat, data in self.remote_votes.items():
            if now - data['ts'] < 10: # 10s TTL
                valid[strat] = data['val']
        return valid

    def stop(self):
        self.active = False
        if self.sock:
            self.sock.close()

# Singleton
_beacon = None
def get_beacon():
    global _beacon
    if _beacon is None:
        _beacon = BeaconListener()
    return _beacon
