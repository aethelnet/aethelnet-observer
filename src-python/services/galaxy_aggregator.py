import asyncio
import logging
import time
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger("GalaxyAggregator")

class GalaxyEvent:
    def __init__(self, id: str, label: str, targets: List[str], color: str, tier: int = 3, intensity: float = 0.5, ttl: int = 10):
        self.id = id
        self.label = label
        self.targets = targets
        self.color = color
        self.tier = tier
        self.intensity = intensity
        self.ttl = ttl  # Seconds
        self.created_at = time.time()

    def to_dict(self):
        return {
            "id": self.id,
            "label": self.label,
            "targets": self.targets,
            "color": self.color,
            "tier": self.tier,
            "intensity": self.intensity,
            "expires_at": self.created_at + self.ttl,
            "type": "event"
        }

class GalaxyAggregator:
    def __init__(self):
        self.active_events: Dict[str, GalaxyEvent] = {}
        self.last_update = 0
        self.last_topology_broadcast = 0
        self.update_interval = 1.0 
        self.topology_interval = 20.0 # Topology updates less frequently

    def add_event(self, event: GalaxyEvent):
        self.active_events[event.id] = event

    async def get_topology(self) -> Dict[str, Any]:
        """
        Compiles the full "Ant Colony" with dynamic properties driven by the Physics Library.
        """
        from services.data_manager import get_data_manager
        from services.leaderboard_service import get_leaderboard_service
        from config.settings import get_settings
        from incubator.physics import HydroFractalEngine
        from services.universe import get_universe_manager
        import pandas_ta as ta
        
        dm = get_data_manager()
        leaderboard = get_leaderboard_service()
        settings = get_settings()
        um = get_universe_manager()
        hfe = HydroFractalEngine() # Use for global metric processing
        
        # 0. THE FLOTILLA (Infrastructure Layer)
        nodes = [
            {"id": "MOTHERSHIP", "label": "LOCAL (MOTHERSHIP)", "type": "infrastructure", "tier": 0, "color": "#10b981", "baseRadius": 30, "currentRadius": 35, "group": "flotilla"}, # Green (Local)
            {"id": "ORACLE", "label": "ORACLE (DREAMER)", "type": "infrastructure", "tier": 1, "color": "#06b6d4", "baseRadius": 20, "currentRadius": 20, "group": "flotilla"}, # Cyan (Oracle)
            {"id": "HETZNER", "label": "HETZNER (SCOUT)", "type": "infrastructure", "tier": 1, "color": "#8b5cf6", "baseRadius": 20, "currentRadius": 20, "group": "flotilla"}, # Purple (Hetzner)
            {"id": "GCP", "label": "GCP (MUSCLE)", "type": "infrastructure", "tier": 1, "color": "#475569", "baseRadius": 20, "currentRadius": 20, "group": "flotilla"}, # Slate (Sleeping)
        ]
        
        links = [
            {"source": "ORACLE", "target": "MOTHERSHIP", "weight": 2},
            {"source": "HETZNER", "target": "MOTHERSHIP", "weight": 2},
            {"source": "GCP", "target": "MOTHERSHIP", "weight": 0.5}, # Weak link when offline
        ]

        # 1. CORE HUBS
        nodes.extend([
            {"id": "SINGULARITY", "label": "THE ORIGIN", "type": "singularity", "tier": -1, "color": "#000000", "baseRadius": 60, "currentRadius": 60},
            {"id": "CRYPTO", "label": "CRYPTO HUB", "type": "market", "tier": 0, "color": "#10b981", "baseRadius": 40, "currentRadius": 40},
            {"id": "FOREX", "label": "FOREX HUB", "type": "market", "tier": 0, "color": "#3b82f6", "baseRadius": 40, "currentRadius": 40},
            {"id": "STOCKS", "label": "EQUITY HUB", "type": "market", "tier": 0, "color": "#ec4899", "baseRadius": 40, "currentRadius": 40},
        ])
        
        links.extend([
            {"source": "SINGULARITY", "target": "CRYPTO"},
            {"source": "SINGULARITY", "target": "FOREX"},
            {"source": "SINGULARITY", "target": "STOCKS"},
        ])
        
        # 2. SECTORS (T1)
        taxonomy = settings.UNIVERSE_TAXONOMY.get("SECTORS", {})
        for sector, members in taxonomy.items():
            nodes.append({"id": sector, "label": sector, "type": "calculation", "tier": 1, "color": "#64748b", "baseRadius": 25, "currentRadius": 25})
            market = "CRYPTO"
            if sector in ["MACRO", "COMMODITY"]: market = "FOREX"
            elif sector in ["TECH", "BLUECHIP"]: market = "STOCKS"
            links.append({"source": market, "target": sector})

        # 3. THE ANTS (T2 - Symbols & Traders)
        symbols = dm.get_available_symbols()
        
        for sym in symbols:
            # Species Coloring
            color = "#10b981" if not any(x in sym for x in ["=", "^", "."]) else "#3b82f6"
            
            # 3.1 DYNAMIC PHYSICS & TECHS
            p_data = um.price_data.get(sym, [])
            v_data = um.volume_data.get(sym, [])
            
            base_r = 14
            curr_r = 14
            tech_data = {
                "rsi": 50,
                "drift": 0.0,
                "volatility": 0.0,
                "sentiment": "Neutral"
            }
            
            if len(p_data) >= 20:
                try:
                    # 1. Basic Physics
                    analysis = hfe.analyze_turbulence(p_data, v_data)
                    turb = analysis.get("turbulence", 0)
                    curr_r = base_r * (1.0 + min(1.5, turb * 5.0))
                    tech_data.update(analysis)
                    
                    # 2. Advanced Technicals (Need ~50 points for reliable RSI)
                    if len(p_data) >= 50:
                        df = pd.DataFrame({"close": p_data})
                        rsi_series = ta.rsi(df["close"], length=14)
                        if rsi_series is not None and not rsi_series.empty:
                            tech_data["rsi"] = float(rsi_series.iloc[-1])
                            
                        # 24-tick Drift (Momentum)
                        tech_data["drift"] = float((p_data[-1] - p_data[-24]) / p_data[-24] * 100) if len(p_data) >= 24 else 0.0
                        
                        # Sentiment Logic
                        if tech_data["rsi"] > 70: tech_data["sentiment"] = "Overbought"
                        elif tech_data["rsi"] < 30: tech_data["sentiment"] = "Oversold"
                        elif tech_data["drift"] > 2.0: tech_data["sentiment"] = "Bullish"
                        elif tech_data["drift"] < -2.0: tech_data["sentiment"] = "Bearish"
                        elif tech_data["drift"] > 0: tech_data["sentiment"] = "Slightly Bullish"
                        else: tech_data["sentiment"] = "Slightly Bearish"

                except Exception as e:
                    logger.warning(f"Technical calculation error for {sym}: {e}")

            # Identify Parent Sector
            parent = "CRYPTO" if color == "#10b981" else "STOCKS"
            for sector, members in taxonomy.items():
                if any(sym.startswith(m) for m in members):
                    parent = sector
                    break

            nodes.append({
                "id": sym, "label": sym, "type": "symbol", "tier": 2, 
                "color": color, "baseRadius": base_r, "currentRadius": curr_r, 
                "group": "market", "data": tech_data
            })
            links.append({"source": parent, "target": sym})

        # 4. RIVAL ANTS (T2 - Competitors)
        try:
            traders = await leaderboard.get_top_traders(limit=12)
            for t in traders:
                nodes.append({
                    "id": t['id'], "label": t['id'], "type": "trader", "tier": 2, 
                    "color": "#f59e0b", "baseRadius": 12, "currentRadius": 12, "group": "event",
                    "data": {"pnl": t.get('pnl', 0)}
                })
                links.append({"source": "SINGULARITY", "target": t['id']})
        except: pass
        
        # 5. GLOBAL PHYSICS STATE (Regime-based constants)
        from analysis.market_regime import analyze_universe
        # Mock metrics_df for analyze_universe
        metrics_df = pd.DataFrame([{"symbol": n['id'], "volatility": n.get('data', {}).get('turbulence', 0)} for n in nodes if n['type'] == 'symbol'])
        regime_config = {"gravity": 0.05, "friction": 0.9, "repulsion": 350, "regime": "Neutral"}
        if not metrics_df.empty:
            from config.settings import get_settings
            layers = {"core": ["BTCUSDT", "ETHUSDT"]}
            regime_config = analyze_universe(layers, metrics_df).get("physics", regime_config)

        return {
            "nodes": nodes, 
            "links": links, 
            "physics_config": regime_config
        }

    async def poll_intelligence(self):
        while True:
            try:
                now = time.time()
                self._cleanup_expired(now)
                
                # Check for events...
                await self._check_price_volatility()
                await self._check_news_stream()
                await self._check_strategy_pivot()

                # Broadcast Resonance (1Hz)
                if now - self.last_update > self.update_interval:
                    await self._broadcast_resonance()
                    self.last_update = now

                # Broadcast Topology (0.05Hz - Every 20s)
                if now - self.last_topology_broadcast > self.topology_interval:
                    topo = await self.get_topology()
                    await self._broadcast_topology(topo)
                    self.last_topology_broadcast = now

            except Exception as e:
                logger.error(f"Galaxy Aggregator Error: {e}")
            await asyncio.sleep(self.update_interval)

    async def _broadcast_topology(self, topo: Dict[str, Any]):
        from routers.stream import get_frontend_manager
        manager = get_frontend_manager()
        payload = {"type": "GALAXY_TOPOLOGY", "topology": topo}
        import json
        await manager.broadcast(json.dumps(payload))

    def _cleanup_expired(self, now: float):
        expired = [eid for eid, ev in self.active_events.items() if now > ev.created_at + ev.ttl]
        for eid in expired:
            del self.active_events[eid]

    async def _check_price_volatility(self):
        from services.data_manager import get_data_manager
        from config.settings import get_trading_symbols, get_settings
        dm = get_data_manager()
        settings = get_settings()
        symbols = get_trading_symbols(settings)[:10]
        
        for symbol in symbols:
            price = dm.get_latest_price(symbol)
            if not price: continue
            
            # Simulated activity spike for resonance
            id = f"PRICE_SURGE_{symbol}"
            if id not in self.active_events:
                self.add_event(GalaxyEvent(
                    id=id, label=f"{symbol} ACTIVITY", targets=[symbol],
                    color="#10b981", tier=2, intensity=0.6, ttl=15
                ))

    async def _check_news_stream(self):
        try:
            from services.enhanced_news_aggregator import get_enhanced_news_aggregator
            agg = get_enhanced_news_aggregator()
            news_items = await agg.get_relevant_news(limit=1)
            for item in news_items:
                id = f"NEWS_{item.get('id', hash(item.get('title')))}"
                if id not in self.active_events:
                    self.add_event(GalaxyEvent(
                        id=id, label=item.get('title', '')[:20], 
                        targets=["SINGULARITY"], color="#8b5cf6", tier=3, intensity=0.9, ttl=60
                    ))
        except: pass

    async def _check_strategy_pivot(self):
        pass

    async def _broadcast_resonance(self):
        from routers.stream import get_frontend_manager
        manager = get_frontend_manager()
        if not manager.active_connections: return
        payload = {"type": "GALAXY_RESONANCE", "events": [ev.to_dict() for ev in self.active_events.values()]}
        import json
        await manager.broadcast(json.dumps(payload))

_aggregator = None

def get_galaxy_aggregator():
    global _aggregator
    if _aggregator is None:
        _aggregator = GalaxyAggregator()
    return _aggregator
