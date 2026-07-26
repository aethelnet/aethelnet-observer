from arena.team import TeamStrategy
from arena.strategies.rat import TheRat
from arena.strategies.tank import TheTank
from arena.strategies.alchemist import TheAlchemist
from arena.strategies.turtle import TheTurtle
from arena.strategies.architect import TheArchitect
from arena.strategies.personal.user_seed_strategy import TheUserSeedStrategy

# 1. The Panzer Team (Rat + Tank)
class ThePanzerTeam(TeamStrategy):
    def __init__(self):
        super().__init__(rider=TheRat(), mount=TheTank(), name="The Panzer Team (Rat + Tank)")

    def _synergize(self, mount: float, rider: float, soul_signal: float = 0.0) -> float:
        # Tank is momentum. Rat is mean reversion.
        # Synergy: If Tank is strong (Trending), Rat fades the counter-moves (Buying dips).
        # We align them: If Tank=1.0 (Trend Up) and Rat=1.0 (Dip Buy), we go 2.0 -> 2.2 (Boosted).
        raw_sum = mount + rider
        if abs(raw_sum) > 1.5:
             return raw_sum * 1.1 # SYNERGY OVERCLOCK
        return raw_sum

# 2. The Magnum Opus (Rat + Alchemist)
class TheMagnumOpus(TeamStrategy):
    def __init__(self):
        super().__init__(rider=TheRat(), mount=TheAlchemist(), name="The Magnum Opus (Rat + Alchemist)")
        
    def on_tick(self, market_state):
        # SAFETY PROTOCOL: In Turbulent regimes, we do not trade.
        regime = market_state.get('regime', 'unknown')
        if regime == 'turbulent':
            return 0.0
        return super().on_tick(market_state)

    def _synergize(self, mount: float, rider: float, soul_signal: float = 0.0) -> float:
        # Alchemist is Volatility Arbitrage.
        # If Alchemist sees opportunity (High Vol), Rat should be more aggressive.
        if abs(mount) > 0.5:
            return mount + (rider * 1.2)
        return mount + rider

# 3. The Shell Team (Rat + Turtle)
class TheShellTeam(TeamStrategy):
    def __init__(self):
        super().__init__(rider=TheRat(), mount=TheTurtle(), name="The Shell Team (Rat + Turtle)")

# 4. The Blueprint (Rat + Architect)
class TheBlueprint(TeamStrategy):
    def __init__(self):
        super().__init__(rider=TheRat(), mount=TheArchitect(), name="The Blueprint (Rat + Architect)")
        
    def _synergize(self, mount: float, rider: float, soul_signal: float = 0.0) -> float:
        # Architect trades Levels (Support/Resistance).
        # Rat trades Wicks.
        # Perfect Synergy: If Architect sees Support (0.5) and Rat sees Wick Check (0.5), it's a sniper entry.
        if mount > 0 and rider > 0: return 2.0
        if mount < 0 and rider < 0: return -2.0
        return mount + rider

# 5. The Cosmic Team (Rat + User Seed)
class TheCosmicTeam(TeamStrategy):
    def __init__(self):
        super().__init__(rider=TheRat(), mount=TheUserSeedStrategy(), name="The Cosmic Team (Rat + User Seed)")

# 6. The Prophit Team (Rat + Dragon)
# Originally from Phase 1, now joining the Assembly properly.
from arena.strategies.dragon import TheDragon
class TheProphitTeam(TeamStrategy):
    def __init__(self):
        # Dragon Skills (Grid Width 8%)
        dragon = TheDragon(skills={"grid_width": 0.08})
        super().__init__(rider=TheRat(), mount=dragon, name="The Prophit Team (Rat + Dragon)")

    def _synergize(self, mount: float, rider: float, soul_signal: float = 0.0) -> float:
        # --- SOVEREIGN OVERRIDE ---
        if abs(soul_signal) > 2.5:
            return soul_signal
            
        # Dragon (Grid) + Rat (Sniper)
        # If Dragon is adding inventory (Mean Reversion) and Rat sees panic, we double down.
        if (mount > 0 and rider > 0) or (mount < 0 and rider < 0):
            return (mount + rider) * 1.15 # DRAGONFIRE OVERCLOCK
        return mount + rider
