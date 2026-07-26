
from typing import Dict, Any, Optional
import time

from arena.api import IStrategy

class TheUserSeedStrategy(IStrategy):
    """
    The User Seed.
    Represents the User's Direct Will injected into the Arena.
    
    Modes:
    1. IDLE: Observes silently.
    2. DIRECTIVE: Executes user overrides with extreme prejudice.
    3. AUTONOMOUS: (Optional) Replicates user's trading style.
    """
    @property
    def class_type(self) -> str:
        return "UserSeed"

    @property
    def name(self) -> str:
        return "The User Seed"

    def __init__(self):
        self.active_directive: Optional[Dict] = None
        self.directive_expiry = 0
        
    def handle_directive(self, directive: Dict):
        """
        Ingest a command from the Cockpit.
        directive: { type, price, reason, score, action, ... }
        """
        # Parse Directive
        # If it's a "Target Line" (Price), we hold it until hit or manual cancel.
        # If it's a "Zone", we might trade inside it.
        
        # For simplicity V1: treat it as a temporary override signal.
        # directive might look like: { price: 95000, reason: "Resistance", ... }
        
        self.active_directive = directive
        self.directive_expiry = time.time() + 3600 # 1 Hour Expiry?
        
        print(f"[{self.name}] Acknowledged Directive: {directive}")

    def on_tick(self, market_state: Dict[str, Any]) -> float:
        """
        Returns signal -1.0 (Sell) to 1.0 (Buy).
        """
        # 1. Check Directive
        if self.active_directive:
            # Check Expiry
            if time.time() > self.directive_expiry:
                self.active_directive = None
                return 0.0
            
            # Logic: If Directive is a "Target", do we go TOWARDS it or FADE it?
            # User intent is vague in "Click to add line".
            # Usually: 
            #  - Click above price = Target (Long) OR Resistance (Short)?
            #  - Let's assume for now: Click = MAGNET (Target).
            
            d_price = self.active_directive.get('price')
            if d_price:
                current_price = market_state.get('price')
                
                # If we are close, maybe we stop?
                if abs(current_price - d_price) / d_price < 0.001:
                    # Hit target -> Clear directive
                    self.active_directive = None
                    return 0.0
                
                if d_price > current_price:
                    return 1.0 # Pull UP to target
                else:
                    return -1.0 # Pull DOWN to target
                    
        return 0.0 # Silent otherwise


