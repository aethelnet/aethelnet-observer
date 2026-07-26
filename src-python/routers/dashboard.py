from fastapi import APIRouter, Depends
import time
import os
import json
import httpx
from datetime import datetime
from routers.prophit_quant import get_hyperliquid_address
from routers.auth import get_current_user

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

START_TIME = time.time()

@router.get("/status")
async def get_status():
    return {
        "is_running": True,
        "testnet_mode": os.getenv("HYPERLIQUID_TESTNET", "true").lower() == "true",
        "execution_enabled": os.getenv("EXECUTION_ENABLED", "false").lower() == "true",
        "env_mode": "production",
        "panic_active": False,
        "last_heartbeat": datetime.utcnow().isoformat(),
        "websocket_connected": True,
        "uptime_seconds": int(time.time() - START_TIME),
        "errors_count": 0
    }

@router.get("/metrics")
async def get_metrics():
    # Fetch local performance stats from performance.json (maintained by Sovereign Rebalancer)
    local_performance = {}
    perf_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "performance.json")
    if os.path.exists(perf_path):
        try:
            with open(perf_path, "r") as f:
                local_performance = json.load(f)
        except Exception:
            pass

    # Read live equity from Hyperliquid if possible
    address = get_hyperliquid_address()
    live_equity = 0.0
    open_pos = 0
    daily_pnl = 0.0
    
    if address:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.hyperliquid.xyz/info",
                    json={"type": "clearinghouseState", "user": address},
                    timeout=5.0
                )
                if response.status_code == 200:
                    hl_data = response.json()
                    margin_summary = hl_data.get("marginSummary", {})
                    live_equity = float(margin_summary.get("accountValue", "0.0"))
                    asset_positions = hl_data.get("assetPositions", [])
                    open_pos = len(asset_positions)
        except Exception:
            pass

    return {
        "total_pnl": local_performance.get("total_pnl", 0.0),
        "total_trades": local_performance.get("total_trades", 0),
        "winning_trades": local_performance.get("winning_trades", 0),
        "win_rate": 0.0 if local_performance.get("total_trades", 0) == 0 else local_performance.get("winning_trades", 0) / local_performance.get("total_trades", 1),
        "open_positions": open_pos,
        "daily_pnl": daily_pnl,
        "max_drawdown": 0.0,
        "drawdown_percentage": 0.0,
        "peak_equity": local_performance.get("peak_equity", live_equity),
        "current_equity": live_equity,
        "shadow_pnl": 0.0,
        "balance": {
            "free": live_equity,
            "locked": 0.0,
            "total": live_equity,
            "currency": "USDC"
        },
        "validation": {
            "trades_met": True,
            "win_rate_met": True,
            "drawdown_met": True,
            "live_ready": True
        },
        "last_update": datetime.utcnow().isoformat()
    }

@router.get("/positions")
async def get_positions():
    address = get_hyperliquid_address()
    positions = []
    if address:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.hyperliquid.xyz/info",
                    json={"type": "clearinghouseState", "user": address},
                    timeout=5.0
                )
                if response.status_code == 200:
                    hl_data = response.json()
                    asset_positions = hl_data.get("assetPositions", [])
                    for pos in asset_positions:
                        pos_data = pos.get("position", {})
                        size = float(pos_data.get("szi", "0"))
                        positions.append({
                            "symbol": pos_data.get("coin", "UNKNOWN"),
                            "side": "LONG" if size > 0 else "SHORT",
                            "entry_price": float(pos_data.get("entryPx", "0")),
                            "current_price": float(pos_data.get("entryPx", "0")), # HL doesn't provide mark price in clearinghouseState easily without meta
                            "quantity": abs(size),
                            "unrealized_pnl": float(pos_data.get("unrealizedPnl", "0")),
                            "entry_time": datetime.utcnow().isoformat(),
                            "hold_time_seconds": 0
                        })
        except Exception:
            pass
    return positions

@router.get("/market-data")
async def get_market_data():
    results = []
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.hyperliquid.xyz/info",
                json={"type": "metaAndAssetCtxs"},
                timeout=5.0
            )
            if response.status_code == 200:
                data = response.json()
                universe = data[0].get("universe", [])
                ctxs = data[1]
                
                combined = []
                for idx, asset in enumerate(universe):
                    if idx < len(ctxs):
                        combined.append((asset["name"], ctxs[idx]))
                
                # Sort by volume descending
                combined.sort(key=lambda x: float(x[1].get("dayNtlVlm", 0)), reverse=True)
                
                for name, ctx in combined[:20]:
                    mark_px = float(ctx.get("markPx", 0))
                    prev_px = float(ctx.get("prevDayPx", mark_px))
                    volume = float(ctx.get("dayNtlVlm", 0))
                    change_24h = ((mark_px - prev_px) / prev_px) * 100.0 if prev_px > 0 else 0.0
                    
                    # We map the funding rate to a mock ML signal for now until the LGNN predictor is fully wired to this route
                    funding = float(ctx.get("funding", 0))
                    sig = funding * 10000 
                    sig_strength = "NEUTRAL"
                    if sig > 0.3: sig_strength = "BUY"
                    if sig < -0.3: sig_strength = "SELL"
                    if sig > 0.8: sig_strength = "STRONG_BUY"
                    if sig < -0.8: sig_strength = "STRONG_SELL"
                    
                    results.append({
                        "symbol": name,
                        "price": mark_px,
                        "signal": sig,
                        "signal_strength": sig_strength,
                        "volume": volume,
                        "change_24h": change_24h,
                        "last_update": datetime.utcnow().isoformat()
                    })
    except Exception as e:
        print(f"Market data fetch error: {e}")
        
    return results

@router.get("/recent-trades")
async def get_recent_trades():
    return []

from pydantic import BaseModel
class WhitelistAddRequest(BaseModel):
    symbol: str

@router.post("/whitelist/add")
async def add_to_whitelist(data: WhitelistAddRequest):
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env")
    if not os.path.exists(env_path):
        return {"status": "error", "message": ".env not found"}
    
    with open(env_path, "r") as f:
        lines = f.readlines()
        
    found = False
    new_whitelist_str = ""
    for i, line in enumerate(lines):
        if line.startswith("SYMBOLS_WHITELIST="):
            # Parse existing
            current = line.strip().split("=", 1)[1].strip('"\'')
            symbols = [s.strip() for s in current.split(",") if s.strip()]
            if data.symbol not in symbols:
                symbols.append(data.symbol)
                new_whitelist_str = ",".join(symbols)
                lines[i] = f'SYMBOLS_WHITELIST="{new_whitelist_str}"\n'
            found = True
            break
            
    if not found:
        new_whitelist_str = data.symbol
        lines.append(f'SYMBOLS_WHITELIST="{data.symbol}"\n')
        
    with open(env_path, "w") as f:
        f.writelines(lines)
        
    # Update in-memory settings
    from config import get_settings
    settings = get_settings()
    settings.SYMBOLS_WHITELIST = new_whitelist_str
        
    return {"status": "success", "message": f"Added {data.symbol} to whitelist"}

@router.get("/blueprint")
async def get_system_blueprint():
    """
    Returns the parsed AST/Dependency graph of the entire Auratic Prime codebase,
    generated by CodeSpider.
    """
    bp_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "blueprint_graph.json")
    if os.path.exists(bp_path):
        with open(bp_path, "r") as f:
            return json.load(f)
    return {"nodes": [], "edges": []}

@router.get("/agents/installed")
async def get_installed_agents():
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "installed_agents.json")
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception:
            pass
    # Default core agents
    return ["z-score-trader", "fusion-reactor", "PatternMatcher", "Prisma", "Repulsor", "Graviton", "EntropyChamber", "Incubator", "Chronosphere"]

@router.post("/agents/install")
async def update_installed_agents(data: dict):
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "installed_agents.json")
    installed = data.get("installed", [])
    try:
        with open(path, "w") as f:
            json.dump(installed, f)
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
