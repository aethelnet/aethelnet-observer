import logging
import asyncio
from typing import Dict, List, Optional
from services.watchtower import get_watchtower

logger = logging.getLogger("HiveMind")

class HiveMind:
    """
    The Hive Mind (Phase 50).
    A Governance Layer that enforces Consensus before Execution.
    No single entity can authorized a trade. It requires a weighted vote.
    """
    def __init__(self):
        self.watchtower = get_watchtower()
        
        # Governance Configuration (Tunable)
        # Governance Configuration (Tunable)
        # OPTIMIZED DEFAULTS (Phase 90 "Golden Weights")
        self.governance_params = {
            "ratification_threshold": 2.0, # Result of Genetic Optimization
            "fracture_tolerance": 100.0, 
            "max_risk_score": 0.8,
            "weight_strategist": 1.0,
            "weight_watchtower": 1.0, # Equalized
            "weight_treasurer": 1.0   # Equalized
        }
        
        # Current State
        self.active_proposals = []
        self.council_log = [] # History of votes

    @property
    def weights(self):
        return {
            "STRATEGIST": self.governance_params.get("weight_strategist", 1.0),
            "WATCHTOWER": self.governance_params.get("weight_watchtower", 2.0),
            "TREASURER": self.governance_params.get("weight_treasurer", 3.0)
        }
        


    async def cast_vote(self, proposal: Dict) -> Dict:
        """
        Gathers votes from all Council Members.
        Returns the Vote Result.
        """
        symbol = proposal.get('symbol')
        side = proposal.get('side')
        price = proposal.get('price', 0)
        
        votes = []
        total_score = 0.0
        
        # 1. The Strategist (Implicitly votes YES if they proposed it)
        votes.append({"member": "STRATEGIST", "vote": "YES", "weight": self.weights["STRATEGIST"], "reason": "Signal Generated"})
        total_score += self.weights["STRATEGIST"]
        
        # 2. The Watchtower (Hydra)
        # Checks for Fracture (Reality Check)
        try:
            fracture_data = self.watchtower.compare(symbol, price)
            fracture_index = fracture_data.get('fracture_index', 0.0)
            
            tolerance = self.governance_params.get('fracture_tolerance', 1.0)
            
            if fracture_index < tolerance: 
                votes.append({"member": "WATCHTOWER", "vote": "YES", "weight": self.weights["WATCHTOWER"], "reason": f"Reality Intact ({fracture_index:.2f}%)"})
                total_score += self.weights["WATCHTOWER"]
            else:
                # VETO: Negative Weight
                votes.append({"member": "WATCHTOWER", "vote": "NO", "weight": -self.weights["WATCHTOWER"], "reason": f"REALITY FRACTURE ({fracture_index:.2f}%)"})
                total_score -= self.weights["WATCHTOWER"]
        except Exception as e:
            logger.error(f"[HIVE] Watchtower Unreachable: {e}")
            # FAILSAFE: If Reality cannot be verified, we assumed it is Broken.
            votes.append({"member": "WATCHTOWER", "vote": "NO", "weight": -self.weights["WATCHTOWER"], "reason": "HYDRA OFFLINE (Unsafe)"})
            total_score -= self.weights["WATCHTOWER"]
            
        # 3. The Treasurer (Risk)
        # For now, simple check: Do we have open slots? (Simplistic)
        # Future: Check Max Drawdown, Exposure, etc.
        # Assuming YES for Phase 50 initial implementation unless 'force_risk_veto' flag is passed
        if proposal.get('force_risk_veto'):
            votes.append({"member": "TREASURER", "vote": "NO", "weight": -self.weights["TREASURER"], "reason": "Risk Limit Exceeded"})
            total_score -= self.weights["TREASURER"]
        else:
            votes.append({"member": "TREASURER", "vote": "YES", "weight": self.weights["TREASURER"], "reason": "Funds Available"})
            total_score += self.weights["TREASURER"]
            
        # Verdict
        threshold = self.governance_params.get('ratification_threshold', 2.5)
        ratified = total_score >= threshold
        
        result = {
            "id": proposal.get("id"),
            "symbol": symbol,
            "side": side,
            "score": total_score,
            "ratified": ratified,
            "votes": votes,
            "timestamp": proposal.get("timestamp")
        }
        
        # Log it
        self.council_log.append(result)
        # Keep log size manageable
        if len(self.council_log) > 50:
            self.council_log.pop(0)
            
        return result

    async def propose(self, signal: Dict) -> bool:
        """
        Submit a signal for ratification.
        Returns True if Ratified, False if Vetoed.
        """
        logger.info(f"HiveMind Proposal Received: {signal['symbol']} {signal['side']}")
        
        # Create Proposal ID
        import uuid
        signal['id'] = str(uuid.uuid4())[:8]
        
        # Cast Votes
        vote_result = await self.cast_vote(signal)
        
        if vote_result['ratified']:
            logger.info(f"[OK] RATIFIED: {signal['symbol']} Score: {vote_result['score']}")
            return True
        else:
            logger.warning(f"❌ VETOED: {signal['symbol']} Score: {vote_result['score']}")
            return False

# Singleton
_hive = None
def get_hive_mind():
    global _hive
    if _hive is None:
        _hive = HiveMind()
    return _hive
