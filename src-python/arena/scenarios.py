import numpy as np
import math

class Scenario:
    def __init__(self, name, duration=1000):
        self.name = name
        self.duration = duration
        self.volatility_map = np.ones(duration) * 0.01
        self.trend_map = np.zeros(duration)
        self.liquidity_map = np.ones(duration) * 1000.0
        self.physics_inverted_map = np.zeros(duration, dtype=bool) # New: Irrational Physics
        
    def get_conditions(self, t):
        if t >= self.duration: t = self.duration - 1
        return {
            'volatility': self.volatility_map[t],
            'trend': self.trend_map[t],
            'liquidity': self.liquidity_map[t],
            'inverted': self.physics_inverted_map[t]
        }

class ScenarioGenerator:
    @staticmethod
    def great_depression(duration=2000):
        s = Scenario("The Great Depression", duration)
        # Massive crash followed by long stagnation
        # Crash Phase (First 20%)
        crash_len = int(duration * 0.2)
        s.trend_map[:crash_len] = -0.005 # Heavy downward drift
        s.volatility_map[:crash_len] = 0.08 # High vol
        s.liquidity_map[:crash_len] = 500.0 # Low liquidity
        
        # Stagnation Phase
        s.trend_map[crash_len:] = -0.0001 # Slow bleed
        s.volatility_map[crash_len:] = 0.02 # Moderate vol
        s.liquidity_map[crash_len:] = 200.0 # Dried up
        return s

    @staticmethod
    def crypto_winter(duration=2000):
        s = Scenario("Crypto Winter", duration)
        # High Volatility, Sharp Drops, Dead Cat Bounces
        for t in range(duration):
            # Sine wave trend (cycles) but trending down
            s.trend_map[t] = math.sin(t * 0.05) * 0.002 - 0.001
            
            # Volatility spikes randomly
            if np.random.random() < 0.05:
                s.volatility_map[t] = 0.15
            else:
                s.volatility_map[t] = 0.03
                
            s.liquidity_map[t] = 1000.0 + (math.sin(t * 0.01) * 500.0)
        return s
        
    @staticmethod
    def hyperinflation(duration=2000):
        s = Scenario("Hyperinflation", duration)
        # Exponential growth in price (currency devaluation)
        for t in range(duration):
            s.trend_map[t] = 0.001 * math.exp(t * 0.002) # Accelerating
            s.volatility_map[t] = 0.05 + (t * 0.0001) # Vol increases with price
            s.liquidity_map[t] = 10000.0 # High nominal liquidity
        return s

    @staticmethod
    def sideways_chop(duration=2000):
        s = Scenario("Sideways Chop", duration)
        # Pure noise, no trend. The "Meat Grinder" for trend followers.
        s.trend_map[:] = 0.0
        s.volatility_map[:] = 0.02
        # Random liquidity gaps
        noise = np.random.normal(0, 100, duration)
        s.liquidity_map += noise
        return s

    @staticmethod
    def cosmic_storm(duration=2000):
        s = Scenario("Cosmic Storm", duration)
        # "Rain and Lightning from Outer Space"
        # Consistent strong momentum...
        s.trend_map[:] = 0.002 
        
        # ...punctuated by massive, irrational jumps ("Lightning")
        for t in range(duration):
            if np.random.random() < 0.02: # 2% chance of lightning
                # Massive discontinuous jump, direction random
                s.trend_map[t] += np.random.choice([-0.1, 0.1]) 
                s.volatility_map[t] = 0.5 # Extreme volatility
            else:
                s.volatility_map[t] = 0.02
                
        return s

    @staticmethod
    def reality_glitch(duration=2000):
        s = Scenario("Reality Glitch", duration)
        # "Physics core behaving irrationally"
        # Randomly invert the laws of supply and demand
        
        for t in range(duration):
            # Normal market mostly
            s.volatility_map[t] = 0.01
            s.trend_map[t] = 0.0
            
            # Glitch Zones
            if 500 < t < 700 or 1200 < t < 1300:
                s.physics_inverted_map[t] = True
                s.volatility_map[t] = 0.05 # Glitches are shaky
                s.liquidity_map[t] = 100.0 # Liquidity evaporates
                
        return s
