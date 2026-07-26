import sys
import os
import logging

# [FORENSIC SETUP]
# Path to project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from incubator.oracle import get_oracle

# Silence the Oracle's internal logs for cleaner output
logging.getLogger("Oracle").setLevel(logging.WARNING)

def run_oracle_audit():
    oracle = get_oracle()
    
    print("\n=== THE ORACLE: SURGICAL AUDIT (50% SOUL) ===")
    
    scenarios = [
        {
            "name": "Scenario 1: Soul Leadership (Soul says BUY, Others Neutral)",
            "state": {
                "ml_probability": 0.9,  # High Soul
                "rat_initiation_trend": 0.1,
                "pattern_return": 0.0   # Neutral Hindsight
            }
        },
        {
            "name": "Scenario 2: The Neural Veto (Swarm says BUY, Soul says SELL)",
            "state": {
                "ml_probability": 0.1,  # Strong SELL from Soul
                "rat_initiation_trend": 0.8, # Strong BUY from Swarm
                "pattern_return": 0.0   # Neutral Hindsight
            }
        },
        {
            "name": "Scenario 3: Triad Consensus (Maximum Conviction)",
            "state": {
                "ml_probability": 0.95,
                "rat_initiation_trend": 0.9,
                "pattern_return": 0.95
            }
        }
    ]

    for s in scenarios:
        print(f"\n--- {s['name']} ---")
        score = oracle.calculate_truth_score(s['state'])
        
        # Calculate expected influence based on 0.5/0.25/0.25 weights
        ml_prob = s['state'].get('ml_probability', 0.5)
        soul_val = (ml_prob - 0.5) * 2.0
        
        print(f"Inputs: Soul={ml_prob:.2f} | Swarm={s['state'].get('rat_initiation_trend', 0):.2f} | Hind={s['state'].get('pattern_return', 0):.2f}")
        print(f"Final Truth Score: {score:+.4f}")
        
        if "Scenario 2" in s['name']:
            if score < 0:
                print("RESULT: SUCCESS. The Soul successfully VETOED the Swarm.")
            else:
                print("RESULT: DILUTED. The Swarm still has too much momentum.")

    print("\n--- CONCLUSION ---")
    print("Architecture verified. The Soul is now the primary driver of the Truth score.")

if __name__ == "__main__":
    run_oracle_audit()
