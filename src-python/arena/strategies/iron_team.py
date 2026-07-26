from arena.team import TeamStrategy
from arena.strategies.rat import TheRat
from arena.strategies.ox import TheOx

class TheIronTeam(TeamStrategy):
    """
    Phase 3: Mastery of the Ox.
    
    The Rat rides The Ox (Rhino).
    - Ox: Provides the "Thick Skin" (DCA / Holding).
    - Rat: "The Free Ride".
    
    Synergy:
    - The Ox holds the bag (Beta).
    - The Rat trades around the Core Position (Alpha).
    - If Ox is underwater (Drawdown), Rat works twice as hard to lower the cost basis.
    """
    
    def __init__(self):
        rider = TheRat()
        mount = TheOx() 
        
        super().__init__(
            rider=rider, 
            mount=mount, 
            name="The Iron Team (Rat + Ox)"
        )
        
    def _synergize(self, mount: float, rider: float) -> float:
        """
        Logic: The Free Ride (Cost Basis Reduction).
        """
        # 1. The Ox (Mount) sets the Core Position (Trend)
        # It usually outputs 0.1 (Hold) or 1.0 (DCA Buy).
        
        # 2. The Rat (Rider) hunts for Volatility.
        
        # Synergy:
        # If the Ox is buying (1.0), and the Rat sees a dip (1.0), we GO BIG.
        if mount > 0.5 and rider > 0.5:
            return 1.5 # Super Conviction
            
        # If the Ox is Neutral/Holding (0.0 - 0.1)
        # The Rat must PAY THE RENT.
        # We amplify the Rat's scalping power to offset the carry cost.
        if abs(rider) > 0.0:
            return mount + (rider * 1.5)
            
        return mount
