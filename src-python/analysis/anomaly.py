from typing import List, Dict, Optional
import time
from core.failsafe import PanicSwitch

class AnomalyDetector:
    """
    The Citadel Protocol: Data Integrity & Anti-Manipulation Shield.
    
    Protects the system from:
    1. Flash Crashes (Physics violations)
    2. Time Travel (Future timestamps)
    3. Stale Data (Stasis)
    4. Negative/Zero Prices (Reality breaks)
    """
    
    def __init__(self):
        # Memory of the last processed price for velocity checks
        self.last_prices: Dict[str, float] = {}
        # Timestamps of last update per symbol
        self.last_update_time: Dict[str, float] = {}
        # Server time offset (managed by DataManager usually, but we check relative diffs)
        self.server_offset = 0 
    
    def set_server_offset(self, offset_ms: int):
        self.server_offset = offset_ms

    def check_integrity(self, symbol: str, ticker_data: dict) -> bool:
        """
        Scans incoming data for malicious patterns or corruption.
        Returns True if SAFE, False if MALICIOUS/CORRUPT.
        Triggers PanicSwitch if CRITICAL.
        """
        current_sys_time = time.time() * 1000 # ms
        
        try:
            # 1. Parse Critical Fields
            price = float(ticker_data['c'])
            event_time = int(ticker_data.get('E', current_sys_time)) # Event Time
            
            # --- CHECK 1: REALITY CHECK (Zero/Negative) ---
            if price <= 0:
                self._trigger_security_event(symbol, "ZERO_PRICE_DETECTED", f"Price: {price}", critical=True)
                return False

            # --- CHECK 2: CHRONOS CHECK (Time Travel) ---
            # Allow 2 second drift (network lag + clock skew)
            # If data claims to be > 2s in the future, it's spoofed or clock is broken.
            # We use local time + offset if we had it, but raw comparison serves as sanity check.
            if event_time > current_sys_time + 5000: # 5s buffer
                self._trigger_security_event(symbol, "FUTURE_TIMESTAMP", f"Delta: {event_time - current_sys_time}ms", critical=False)
                return False # Reject data, but don't panic yet (could be NTP sync issue)

            # --- CHECK 3: PHYSICS CHECK (Flash Crash / Teleportation) ---
            last_price = self.last_prices.get(symbol)
            if last_price:
                pct_change = (price - last_price) / last_price
                
                # CRITICAL THRESHOLD: 20% move in single tick/update
                if abs(pct_change) > 0.20:
                    self._trigger_security_event(
                        symbol, 
                        "FLASH_CRASH_DETECTED" if pct_change < 0 else "IMPOSSIBLE_PUMP", 
                        f"Move: {pct_change*100:.2f}% (Price: {last_price} -> {price})", 
                        critical=True
                    )
                    return False
            
            # Update State
            self.last_prices[symbol] = price
            self.last_update_time[symbol] = current_sys_time
            
            return True

        except Exception as e:
            # Malformed Data
            print(f"[Shield] Malformed Data rejected: {e}")
            return False

    def check_stasis(self, current_time_ms: float) -> List[str]:
        """
        Called periodically to check for dead feeds.
        """
        dead_symbols = []
        for sym, last_ts in self.last_update_time.items():
            if current_time_ms - last_ts > 60000: # 60s silence
                dead_symbols.append(sym)
                
        if dead_symbols:
            print(f"[Shield] ⚠️ STASIS DETECTED: {len(dead_symbols)} symbols silent > 60s.")
            # We don't Panic for lag, but we warn.
            
        return dead_symbols

    def _trigger_security_event(self, symbol: str, event_type: str, details: str, critical: bool = False):
        msg = f"[Shield] 🛡️ SECURITY INTERVENTION: {symbol} | {event_type} | {details}"
        print(msg)
        
        if critical:
            print(f"[Shield] 🚨 CRITICAL THREAT. ENGAGING PANIC SWITCH.")
            PanicSwitch.trigger(reason=f"Security: {event_type} on {symbol}")
