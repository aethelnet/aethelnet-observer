from typing import List, Dict, Any
import pandas as pd

class BoardMember:
    """
    A Glorious Nerd.
    Has a specific bias and personality.
    """
    def __init__(self, name: str, role: str, bias: str):
        self.name = name
        self.role = role
        self.bias = bias # 'safety', 'profit', 'consistency'

    def evaluate(self, candidate_stats: Dict[str, Any]) -> Dict[str, Any]:
        """
        Reviews a Candidate Strategy's stats.
        Returns { 'consent': bool, 'objection': str, 'adjustment': float }
        """
        pnl = candidate_stats.get('PnL', 0) or 0
        win_rate = candidate_stats.get('WinRate', 0) or 0
        
        # 1. The Elder (Risk Manager) - Hates Losing Money
        if self.bias == 'safety':
            if pnl < 0:
                return {'consent': False, 'objection': "Negative Expectancy.", 'adjustment': 0.0}
            if win_rate < 40:
                return {'consent': True, 'objection': "Winrate volatile, reduce size.", 'adjustment': 0.5}
            return {'consent': True, 'objection': None, 'adjustment': 1.0}

        # 2. The Speedrunner (Degen) - Loves Action
        elif self.bias == 'profit':
            if pnl > 5.0:
                 return {'consent': True, 'objection': "Glorious numbers!", 'adjustment': 1.2}
            if pnl < -10.0:
                 return {'consent': False, 'objection': "Trash build.", 'adjustment': 0.0}
            return {'consent': True, 'objection': None, 'adjustment': 1.0}

        # 3. The Lorekeeper (Scientist) - Loves Consistency
        elif self.bias == 'consistency':
            if candidate_stats.get('Class') == 'Tank' and pnl > 0:
                 return {'consent': True, 'objection': "Solid foundation.", 'adjustment': 1.0}
            if pnl < -5 and candidate_stats.get('Class') == 'Rogue':
                 return {'consent': False, 'objection': "Glass cannon shattered.", 'adjustment': 0.0}
            return {'consent': True, 'objection': "Data inconclusive, proceed with caution.", 'adjustment': 0.8}
            
        return {'consent': True, 'objection': None, 'adjustment': 1.0}

class SociocracyEngine:
    """
    The Council Chamber.
    """
    def __init__(self):
        self.board = [
            BoardMember("Old Man Jenkins", "The Elder", "safety"),
            BoardMember("xX_Slayer_Xx", "The Speedrunner", "profit"),
            BoardMember("Archivist Threnody", "The Lorekeeper", "consistency")
        ]

    def hold_meeting(self, gauntlet_results: pd.DataFrame):
        print("\n=== THE COUNCIL IS IN SESSION ===")
        print(f"Agenda: Reviewing {len(gauntlet_results)} Gauntlet Runs.\n")
        
        # Aggregate stats per Fighter
        fighters = gauntlet_results.groupby('Fighter').agg({
            'PnL': 'sum',
            'WinRate': 'mean',
            'Class': 'first'
        }).reset_index()
        
        decisions = []
        
        for _, fighter in fighters.iterrows():
            print(f"--- Reviewing Candidate: {fighter['Fighter']} ({fighter['Class']}) ---")
            print(f"    Stats: PnL {fighter['PnL']:.2f}%, WR {fighter['WinRate']:.1f}%")
            
            # The Round of Consent
            total_adjustment = 1.0
            critical_objection = False
            
            for member in self.board:
                vote = member.evaluate(fighter.to_dict())
                
                if not vote['consent']:
                    print(f"    [OBJECTION] {member.name}: \"{vote['objection']}\"")
                    critical_objection = True
                    break # Veto
                elif vote['objection']:
                     print(f"    [CONCERN] {member.name}: \"{vote['objection']}\" (Adjustment: {vote['adjustment']}x)")
                     total_adjustment *= vote['adjustment']
                else:
                     print(f"    [CONSENT] {member.name}: Nodded silently.")
                     
            if critical_objection:
                print(f"    >> VERDICT: REJECTED.\n")
                decisions.append({'Fighter': fighter['Fighter'], 'Status': 'Rejected', 'Allocation': 0.0})
            else:
                allocation = round(total_adjustment * 100, 1)
                print(f"    >> VERDICT: APPROVED. Allocation: {allocation}%\n")
                decisions.append({'Fighter': fighter['Fighter'], 'Status': 'Approved', 'Allocation': allocation})
                
        return pd.DataFrame(decisions)
