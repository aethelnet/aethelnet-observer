from fastapi import APIRouter, HTTPException, Depends
import os
import json
import httpx
from pydantic import BaseModel
from typing import Dict, Any
from routers.auth import get_current_user

router = APIRouter(prefix="/api/prophitquant", tags=["ProphitQuant"], dependencies=[Depends(get_current_user)])

# We use the wallet address from the environment
def get_hyperliquid_address():
    return os.getenv("HYPERLIQUID_WALLET_ADDRESS")

@router.get("/dashboard")
async def get_dashboard_data():
    """
    Fetches real-time PnL and active positions from Hyperliquid directly,
    and merges it with the local performance.json (if available).
    """
    address = get_hyperliquid_address()
    if not address:
        raise HTTPException(status_code=500, detail="HYPERLIQUID_WALLET_ADDRESS not set in .env")

    # 1. Fetch real-time clearinghouse state from Hyperliquid Mainnet
    hyperliquid_data = {}
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.hyperliquid.xyz/info",
                json={"type": "clearinghouseState", "user": address},
                timeout=10.0
            )
            if response.status_code == 200:
                hyperliquid_data = response.json()
    except Exception as e:
        print(f"Error fetching from Hyperliquid: {e}")

    # 2. Fetch local performance stats from performance.json (maintained by Sovereign Rebalancer)
    local_performance = {}
    perf_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "performance.json")
    if os.path.exists(perf_path):
        try:
            with open(perf_path, "r") as f:
                local_performance = json.load(f)
        except Exception as e:
            print(f"Error reading performance.json: {e}")

    # Extract relevant fields for the frontend
    margin_summary = hyperliquid_data.get("marginSummary", {})
    asset_positions = hyperliquid_data.get("assetPositions", [])
    
    positions = []
    for pos in asset_positions:
        pos_data = pos.get("position", {})
        positions.append({
            "coin": pos_data.get("coin"),
            "size": pos_data.get("szi"),
            "entry_price": pos_data.get("entryPx"),
            "leverage": pos_data.get("leverage", {}).get("value"),
            "unrealized_pnl": pos_data.get("unrealizedPnl"),
            "return_on_equity": pos_data.get("roePnl"),
            "liquidation_price": pos_data.get("liquidationPx")
        })

    return {
        "status": "online",
        "wallet": address,
        "live_equity": margin_summary.get("accountValue", "0.0"),
        "total_margin_used": margin_summary.get("totalMarginUsed", "0.0"),
        "positions": positions,
        "local_stats": {
            "total_trades": local_performance.get("total_trades", 0),
            "winning_trades": local_performance.get("winning_trades", 0),
            "peak_equity": local_performance.get("peak_equity", 0.0),
            "bot_pnl": local_performance.get("total_pnl", 0.0)
        }
    }
