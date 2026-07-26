from arena.team import TeamStrategy
from arena.strategies.rat import TheRat
from arena.strategies.snake import TheSnake

class TheStealthTeam(TeamStrategy):
    """
    Phase 2: Mastery of the Snake.
    
    The Rat rides The Snake.
    - Snake: Waits for 'The Lunar Crossing' (Trend Reversal/Continuation at key level).
    - Rat: Eager to trade.
    
    Synergy:
    - The Rat is inherently noisy/impatient.
    - The Snake is infinitely patient.
    - The Team only trades when the Rat's "Gap" aligns with the Snake's "Crossing".
    """
    
    def __init__(self):
        rider = TheRat()
        mount = TheSnake() 
        
        super().__init__(
            rider=rider, 
            mount=mount, 
            name="The Stealth Team (Rat + Snake)"
        )
        self.current_position = 0.0 # Memory

    def _synergize(self, mount: float, rider: float) -> float:
        """
        Logic: Snake Strike, Rat Escape.
        """
        # 1. Entry Logic (The Snake)
        # If Snake signals a Crossing (1.0 or -1.0), we obey immediately.
        if abs(mount) > 0.0:
            self.current_position = mount
            return mount

        # 2. Exit/Management Logic (The Rat)
        # If we are holding a position...
        if abs(self.current_position) > 0.0:
            # The Rat looks for exit opportunities (Wicks against us).
            # If we are Long (1.0) and Rat screams Short (-1.0) -> TAKE PROFIT.
            if self.current_position > 0 and rider < -0.5:
                self.current_position = 0.0 # Close
                return 0.0
            
            # If we are Short (-1.0) and Rat screams Long (1.0) -> TAKE PROFIT.
            if self.current_position < 0 and rider > 0.5:
                self.current_position = 0.0 # Close
                return 0.0
                
            # Otherwise, Hold the Line.
            return self.current_position
            
        # 3. Default: Flat
        return 0.0
