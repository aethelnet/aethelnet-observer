
from typing import Dict, List

class Scoreboard:
    """
    The Arena Scoreboard.
    Tracks the Duel between The Prophit Team (User) and The Rival (Pied Piper).
    """
    def __init__(self):
        self.scores = {
            "PROPHIT": {"wins": 0, "losses": 0, "pnl": 0.0},
            "RIVAL": {"wins": 0, "losses": 0, "pnl": 0.0}
        }
        self.match_history = []

    def record_match(self, winner: str, pnl_diff: float):
        """
        winner: 'PROPHIT' or 'RIVAL' or 'DRAW'
        """
        if winner == "PROPHIT":
            self.scores["PROPHIT"]["wins"] += 1
            self.scores["RIVAL"]["losses"] += 1
        elif winner == "RIVAL":
            self.scores["RIVAL"]["wins"] += 1
            self.scores["PROPHIT"]["losses"] += 1
            
        # PnL Tracking (Approximate or Actual?)
        # For now, just track wins
        
        self.match_history.append({
            "winner": winner,
            "diff": pnl_diff,
            "ts": __import__('time').time()
        })

    def get_stats(self):
        return self.scores
