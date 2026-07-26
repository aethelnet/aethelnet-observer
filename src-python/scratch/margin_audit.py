import asyncio
import os
import sys

# Setup Path
project_root = "/var/home/nhrlyn/Projects/auratic-systems-prime"
sys.path.insert(0, project_root)

async def check_margin():
    try:
        from brokers.router import get_omni_router
        router = get_omni_router()
        hl = router.brokers.get('hyperliquid')
        if not hl:
             print("Hyperliquid broker not found.")
             return
             
        # Wait for initialize if needed
        # hl.get_margin_state calls the API
        state = await hl.get_margin_state()
        print(f"\n--- HYPERLIQUID MARGIN STATUS ---")
        print(f"Account Value: ${float(state.get('account_value', 0)):.2f}")
        print(f"Margin Used:   ${float(state.get('margin_used', 0)):.2f}")
        print(f"Available:     ${float(state.get('withdrawable', 0)):.2f}")
        util = float(state.get('margin_used', 0)) / float(state.get('account_value', 1))
        print(f"Utilization:   {util:.1%}")
        print(f"---------------------------------\n")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_margin())
