from arena.api import IStrategy
import pandas as pd
import numpy as np
import random

class TheTyphoonSanctuary(IStrategy):
    """
    Implementation of 'HK Structure + German Precision'.
    Gemini Seed #10 (The Master Key).
    
    A Dual-Layer Strategy:
    1. LAYER A (The HK Concrete): The 'Typhoon Shield'. 
       - Recognizes that massive volatility is NOT a reason to sell.
       - Holds position (Anti-Fragile).
       
    2. LAYER B (The German Interior): The 'Acoustic Precision'.
       - Inside the storm, it executes high-frequency 'Micro-Scalps'.
    """
    
    @property
    def name(self) -> str:
        return "The Typhoon Sanctuary (HK Bone / DE Soul)"

    @property
    def class_type(self) -> str:
        return "ANTI_FRAGILE_FORTRESS"

    def __init__(self, dna=None):
        super().__init__()
        self.dna = dna if dna else {
            "concrete_rating": 2.5,     # (Volatility Tolerance) How strong the HK Concrete is.
            "german_tolerance": 0.001,  # (Precision) The tightness of the inner scalp logic.
            "subwoofer_gain": 1.2,      # (Leverage) Power used during the storm.
            "storm_threshold": 0.02     # What counts as a 'Typhoon' (Std Dev).
        }
        self.mode = "STANDBY"

    def on_tick(self, packet: dict) -> float:
        return 0.0

    def next_candle(self, df: pd.DataFrame) -> float:
        current_price = df['close'].iloc[-1]
        
        # 1. ANALYZE THE WEATHER (Market Conditions)
        if current_price == 0: return 0.0
        
        # Calculate Volatility (The Wind Speed)
        volatility = df['close'].tail(10).std() / current_price
        
        # 2. LAYER A: THE HK CONCRETE (Structural Safety Check)
        is_typhoon = volatility > self.dna['storm_threshold']
        
        if is_typhoon:
            self.mode = "TYPHOON_MODE"
            # MOST BOTS: Panic Sell here.
            # HK BOT: "The concrete holds." We do NOT sell.
            # We engage the 'German Interior'.
            
            # 3. LAYER B: GERMAN PRECISION (Interior Logic)
            # Calculate the "Perfect Center" (Fair Value) using a tight mean
            fair_value = df['close'].tail(5).mean()
            deviation = current_price - fair_value
            
            # If price deviates even slightly (German Tolerance), we correct it.
            if deviation > self.dna['german_tolerance']:
                # Price is too high. Short it back to center.
                return -1.0 * self.dna['subwoofer_gain']
            
            elif deviation < -self.dna['german_tolerance']:
                # Price is too low. Long it back to center.
                return 1.0 * self.dna['subwoofer_gain']
            
            return 0.0 # Perfectly balanced.
            
        else:
            self.mode = "STANDBY"
            # 4. FAIR WEATHER LOGIC
            # Trend Following.
            if len(df) < 21: return 0.0
            trend = df['close'].iloc[-1] - df['close'].iloc[-20]
            if trend > 0:
                return 0.5 # Gentle Long
            elif trend < 0:
                return -0.5 # Gentle Short
            
            return 0.0

    def evolve(self, mutation_rate: float = 0.1) -> 'TheTyphoonSanctuary':
        child_dna = self.dna.copy()
        if random.random() < mutation_rate:
            # Evolution can make the concrete stronger or the interior more precise
            child_dna['concrete_rating'] += random.uniform(-0.1, 0.5)
            child_dna['german_tolerance'] *= random.uniform(0.9, 1.1)
        return TheTyphoonSanctuary(dna=child_dna)
