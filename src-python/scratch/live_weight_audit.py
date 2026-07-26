import sys
import os
import asyncio

# Add project root
sys.path.append(os.getcwd())

from services.layer_tracker import get_layer_tracker

async def check_live_weights():
    print("--- 🕵️ FORENSIC AUDIT: LIVE COUNCIL WEIGHTS ---")
    tracker = get_layer_tracker()
    
    # Check weights for current market conditions (approx)
    weights = tracker.get_dynamic_weights(current_z=0.0, current_volatility=0.02, current_entropy=0.5)
    
    print("\nLive Weights in Council:")
    for layer, weight in sorted(weights.items(), key=lambda x: x[1], reverse=True):
        print(f"  {layer:<25}: {weight:.4f}")
        
    total = sum(weights.values())
    print(f"\nTotal Sum: {total:.4f}")
    
    if total == 0:
        print("\n⚠️ WARNING: Council is SILENT. All weights are zero!")
    elif max(weights.values()) < 0.20:
        print(f"\nℹ️ INFO: No specialist dominates yet. Max is {max(weights.values()):.4f}")

if __name__ == "__main__":
    asyncio.run(check_live_weights())
