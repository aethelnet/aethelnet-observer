import asyncio
import json
import logging
import urllib.request
import websockets
import time
from collections import defaultdict
from config import get_settings
from .universe import UniverseManager

# --- DOCUMENTATION REFERENCES ---
# Database Schema:      Market Brain/Backend/Database.md
# Market Behavior:      Market Brain/Concepts/Realistic_Market_Behavior.md
# --------------------------------

logger = logging.getLogger("AuraticMarketData")
settings = get_settings()

from .connection_manager import ConnectionManager

# Top 20 Volatile Assets (Expanded to 50 later)
TOP_ASSETS = [
    "btcusdt", "ethusdt", "solusdt", "bnbusdt", "xrpusdt", 
    "adausdt", "dogeusdt", "shibusdt", "dotusdt", "maticusdt",
    "ltcusdt", "linkusdt", "uniusdt", "atomusdt", "avaxusdt"
]

class MarketDataService:
    def __init__(self, universe_manager: UniverseManager, connection_manager: ConnectionManager):
        self.universe = universe_manager
        self.connection_manager = connection_manager
        # Buffer: List of (symbol, timestamp, price, volume, is_buyer_maker)
        self.tick_buffer = []
        self.running = False
        self.current_symbol = "BTCUSDT"
        self.fetch_task = None
        self.last_tick_time = 0.0

    async def start(self):
        self.running = True
        # 1. Backfill (Active Symbol Only for now to save startup time)
        await self.fetch_historical_data(self.current_symbol)
        # 2. Stream (Firehose)
        asyncio.create_task(self.binance_stream())
        # 3. Process Loop
        asyncio.create_task(self.process_loop())

    async def stop(self):
        self.running = False

    async def binance_stream(self):
        """
        Connect to Binance Futures WebSocket (Combined Stream) and ingest ticks.
        """
        # Construct Combined Stream URL
        streams = [f"{symbol}@aggTrade" for symbol in TOP_ASSETS]
        stream_string = "/".join(streams)
        uri = f"wss://fstream.binance.com/stream?streams={stream_string}"
        
        logger.info(f"Connecting to Firehose: {len(TOP_ASSETS)} assets")

        while self.running:
            try:
                async for websocket in websockets.connect(uri):
                    if not self.running: break
                    logger.info("Connected to Binance Firehose")
                    try:
                        while self.running:
                            msg = await websocket.recv()
                            payload = json.loads(msg)
                            
                            # Combined stream format: {"stream": "...", "data": {...}}
                            if 'data' in payload:
                                data = payload['data']
                                symbol = data['s'] # e.g. BTCUSDT
                                
                                # Extract data
                                price = float(data['p'])
                                volume = float(data['q'])
                                timestamp = data['T']
                                is_buyer_maker = data['m']
                                
                                # Buffer Physics Processing
                                self.tick_buffer.append((symbol, timestamp, price, volume, is_buyer_maker))
                                
                                # Broadcast Fast Tick (Only if it's the active symbol)
                                if symbol == self.current_symbol:
                                    current_time = time.time()
                                    if current_time - self.last_tick_time >= 0.25:
                                        fast_tick = {
                                            "fast_tick": [timestamp / 1000.0, price, volume]
                                        }
                                        await self.connection_manager.broadcast(json.dumps(fast_tick))
                                        self.last_tick_time = current_time
                            
                    except websockets.ConnectionClosed:
                        logger.warning("Binance connection closed, reconnecting...")
                        continue
            except Exception as e:
                logger.error(f"Error in binance_stream: {e}")
                await asyncio.sleep(1)

    async def fetch_historical_data(self, symbol):
        """
        Fetch historical data from Binance to backfill/heal the physics engine.
        """
        # 1. Get latest from DB (in seconds)
        engine = self.universe.get_engine(symbol)
        last_db_ts = engine.db.get_latest_timestamp(symbol)
        
        limit = 1500
        start_time_ms = None
        
        if last_db_ts > 0:
            overlap_start = (last_db_ts - 600) * 1000 
            start_time_ms = int(overlap_start)
            logger.info(f"Healing {symbol} from {start_time_ms}")
        else:
            logger.info(f"Deep backfill for {symbol}")

        base_url = f"https://fapi.binance.com/fapi/v1/klines?symbol={symbol}&interval=1m&limit=1500"
        all_candles = []
        
        try:
            url = base_url
            if start_time_ms:
                url += f"&startTime={start_time_ms}"
                
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, urllib.request.urlopen, url)
            data = json.loads(response.read().decode())
            
            if isinstance(data, list) and len(data) > 0:
                all_candles = data
                engine.ingest_historical_batch(all_candles)
                logger.info(f"Processed {len(all_candles)} candles for {symbol}")
        except Exception as e:
            logger.error(f"Backfill failed for {symbol}: {e}")

    def get_and_clear_buffer(self):
        batch = list(self.tick_buffer)
        self.tick_buffer.clear()
        return batch

    async def process_loop(self):
        """
        Broadcast physics state at 20Hz (50ms).
        """
        while self.running:
            await asyncio.sleep(settings.BROADCAST_INTERVAL)
            
            # Process Buffered Ticks
            batch = self.get_and_clear_buffer()
            if batch:
                # Group by Symbol
                grouped = defaultdict(list)
                for item in batch:
                    sym, ts, p, v, m = item
                    grouped[sym].append((ts, p, v, m))
                
                # Update Engines
                for sym, ticks in grouped.items():
                    engine = self.universe.get_engine(sym)
                    engine.process_batch(ticks)
                
                # Calculate & Broadcast ONLY for Active Symbol
                # (To save bandwidth. The others are updating in background)
                active_engine = self.universe.get_engine(self.current_symbol)
                
                # --- SIMULATION TICK ---
                # If simulation is running, we tick it and inject the result into the engine
                if self.universe.simulation.is_running:
                    # 1. Tick Simulation
                    # Use Volume Intensity from active engine as driver
                    vol_intensity = 0.5 
                    if len(active_engine.volumes) > 0:
                        # Normalize volume roughly
                        vol_intensity = min(1.0, active_engine.volumes[-1] / 1000.0)
                        
                    sim_price = self.universe.simulation.tick(vol_intensity)
                    
                    # 2. Inject into Engine (as a new tick)
                    # We use the simulation clock as timestamp
                    sim_time = self.universe.simulation.clock
                    # Ingest as a "Synthetic" tick
                    active_engine.process_tick(sim_time * 1000, sim_price, 100.0, False)
                
                state = active_engine.calculate_physics()
                if state:
                    await self.connection_manager.broadcast(json.dumps(state))

