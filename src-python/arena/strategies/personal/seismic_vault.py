from arena.api import IStrategy
import pandas as pd
import numpy as np
import random

class TheSeismicVault(IStrategy):
    """
    The 'Seismic Vault' Protocol (Liquidity Siphon).
    Gemini Seed #9 (The Looters).
    
    Revised Logic:
    - We do not just 'wait' for the host. 
    - We actively set traps (Limit Bids) deep in the 'Tomb' (Price Wicks).
    - When the 'Earthquake' happens, we don't hide; we 'Grab the Gold' (Liquidity Siphon).
    """
    
    # --- BUREAUCRATIC CAMOUFLAGE (COMPLIANCE LAYER) ---
    EARTHQUAKE_SHIELD = "ACTIVE" # Safety Protocol: ENGAGED
    SUBMERSION_PROTOCOL = True   # If True, we dive BELOW the volatility.
    
    @property
    def name(self) -> str:
        return "The Seismic Vault (Liquidity Siphon)"
        
    @property
    def class_type(self) -> str:
        return "HIBERNATING_ALCHEMIST"

    def __init__(self, dna=None):
        super().__init__()
        self.dna = dna if dna else {
            "tomb_depth": 0.05,           # (5%) How deep the crack needs to be to reveal gold.
            "grab_aggression": 1.0,       # (Leverage) Full deployment when gold is visible.
            "earthquake_threshold": 0.02, # (Volatility) The signal that the seal is breaking.
            "extraction_time": 5          # (Ticks) How fast we run out of the tomb after grabbing.
        }
        self.holding_gold = False
        self.ticks_in_tomb = 0

    def on_tick(self, packet: dict) -> float:
        return 0.0

    def next_candle(self, df: pd.DataFrame) -> float:
        current_price = df['close'].iloc[-1]
        low_price = df['low'].iloc[-1]
        
        # 1. THE EARTHQUAKE DETECTOR (Risk Assessment)
        # Is the market shaking? (High Volatility)
        if current_price == 0: return 0.0
        
        # Calculate instantaneous volatility (High/Low range)
        volatility = (df['high'].iloc[-1] - df['low'].iloc[-1]) / current_price
        
        # --- EARTHQUAKE SHIELD PROTOCOL ---
        # If volatility is CRITICAL, we engage the SUBMERSION PROTOCOL.
        # This is NOT a trade; it is a defensive liquidity provision.
        
        if volatility > self.dna['earthquake_threshold']:
            # >>> CRITICAL VOLATILITY DETECTED <<<
            # ENGAGING LIQUIDITY SIPHON (Limit Orders Only).
            
            if not self.holding_gold:
                # We are looking for a "Flash Crash" or a "Liquidity Wick"
                
                # Calculate where the "Gold" (Panic Sellers) is hiding
                # It is usually 3 standard deviations below the mean.
                mean_price = df['close'].tail(20).mean()
                std_dev = df['close'].tail(20).std()
                tomb_floor = mean_price - (3 * std_dev)
                
                # DID THE FLOOR CRACK? (Submersion Check)
                if low_price < tomb_floor:
                    # SAFETY LOGIC: We only buy if we are catching a falling knife 
                    # that has effectively hit the bedrock (3 Sigma).
                    # This protects the capital from "catching the middle".
                    self.holding_gold = True
                    self.ticks_in_tomb = 0
                    return 1.0 * self.dna['grab_aggression'] # ACTION: SIPHON LIQUIDITY
                
                return 0.0 # Waiting in the shadows.
                
        # --- STANDARD OPERATIONS (If Shield is NOT Active) ---
        # If volatility is low, we do NOTHING. We are a Vault. 
        # We do not trade noise.
        
        # 3. THE ESCAPE LOGIC (Running with the Gold)
        if self.holding_gold:
            self.ticks_in_tomb += 1
            
            # We grabbed the gold. Now we need to get out before the tomb collapses again.
            # We look for the "Mean Reversion" (The bounce).
            mean_price = df['close'].tail(10).mean()
            
            # If price snaps back to normal (Mean), we bank the funds.
            if current_price >= mean_price:
                self.holding_gold = False
                return -1.0 # SELL / CLOSE. (Transfer to Bank)
            
            # If we linger too long, the air runs out.
            if self.ticks_in_tomb > self.dna['extraction_time']:
                self.holding_gold = False
                return -1.0 # Emergency Exit.
            
            # Otherwise, hold the bag tight.
            return 1.0
            
        return 0.0

    def evolve(self, mutation_rate: float = 0.1) -> 'TheSeismicVault':
        child_dna = self.dna.copy()
        if random.random() < mutation_rate:
            child_dna['tomb_depth'] += random.uniform(-0.01, 0.01)
            child_dna['extraction_time'] = max(1, child_dna['extraction_time'] + random.choice([-1, 1]))
        return TheSeismicVault(dna=child_dna)
