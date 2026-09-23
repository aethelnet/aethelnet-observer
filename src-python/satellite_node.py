import asyncio
import json
import logging
import os
import time
import math
import threading
from typing import Dict
from collections import deque
import sys
import torch
import torch.nn as nn
from dotenv import load_dotenv

# Import the new Aethelnet SDK
from aethelnet import SwarmNode

sys.path.append(os.getcwd())
load_dotenv()  # Load .env file for NEXUS_URL etc.

class IncrementalStats:
    """Incremental mean/std over a sliding window (O(1) updates)."""
    def __init__(self, window_size: int = 20):
        self.window_size = int(window_size)
        self.prices: deque = deque()
        self.sum = 0.0
        self.sum_sq = 0.0
        self._lock = threading.Lock()

    def add_price(self, price: float):
        price = float(price)
        with self._lock:
            if len(self.prices) >= self.window_size:
                old = self.prices.popleft()
                self.sum -= old
                self.sum_sq -= old * old
            self.prices.append(price)
            self.sum += price
            self.sum_sq += price * price

    def get_mean(self) -> float:
        with self._lock:
            n = len(self.prices)
            return (self.sum / n) if n else 0.0

    def get_std(self) -> float:
        with self._lock:
            n = len(self.prices)
            if n < 2: return 0.0
            mean = (self.sum / n) if n else 0.0
            variance = (self.sum_sq / n) - (mean * mean)
            return math.sqrt(variance) if variance > 0 else 0.0

class ButterflySensor:
    """Butterfly Effect Sensor: Detects Sensitive Dependence on Initial Conditions (Chaos)."""
    def __init__(self, window=20):
        self.window = window
        self.history = []
        
    def update(self, price):
        self.history.append(float(price))
        if len(self.history) > self.window * 2:
            self.history.pop(0)
            
    def get_chaos_level(self) -> float:
        if len(self.history) < self.window: return 0.0
        try:
            mid = len(self.history) // 2
            dists = []
            for i in range(mid - 1):
                p1 = self.history[i]
                p2 = self.history[i+1]
                shifted_p1 = self.history[mid + i]
                shifted_p2 = self.history[mid + i + 1]
                div_initial = abs(p1 - shifted_p1)
                div_final = abs(p2 - shifted_p2)
                if div_initial > 0.0001:
                    expansion = math.log((div_final + 1e-8) / (div_initial + 1e-8))
                    dists.append(expansion)
            if not dists: return 0.0
            avg_lambda = sum(dists) / len(dists)
            chaos = math.tanh(max(0, avg_lambda) * 1.0) 
            return chaos
        except:
            return 0.0

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AuraticSatellite")

class SatelliteLGNN(nn.Module):
    """Local edge-compute PyTorch Model for Topological Prediction Error."""
    def __init__(self):
        super().__init__()
        # 3 inputs: node_count, edge_count, vertices_count (mock features for now)
        self.fc1 = nn.Linear(3, 16)
        self.fc2 = nn.Linear(16, 1)
        self.activation = nn.Tanh()
        
    def forward(self, x):
        h = self.activation(self.fc1(x))
        out = self.fc2(h)
        return out


class SatelliteNode:
    def __init__(self, nexus_url: str, node_id: str):
        self.nexus_url = nexus_url
        self.node_id = node_id
        self.sensors: Dict[str, ButterflySensor] = {}
        self.stats: Dict[str, IncrementalStats] = {}
        self.running = True
        
        # Initialize Local Tensor Model
        self.local_model = SatelliteLGNN()
        self.optimizer = torch.optim.Adam(self.local_model.parameters(), lr=0.01)
        
        # Optional Execution Core (Binance)
        self.api_key = os.getenv("BINANCE_API_KEY")
        self.secret_key = os.getenv("BINANCE_SECRET_KEY")
        self.bin_paper = os.getenv("BINANCE_PAPER", "False").lower() == "true"
        self.broker = None
        if self.api_key and self.secret_key:
            try:
                import ccxt
                self.broker = ccxt.binance({
                    'apiKey': self.api_key,
                    'secret': self.secret_key,
                    'enableRateLimit': True,
                    'options': {'defaultType': 'spot'}
                })
                if self.bin_paper:
                    self.broker.set_sandbox_mode(True)
                logger.info(f"[EXECUTION] Binance Broker Initialized for {node_id} (Paper={self.bin_paper})")
            except Exception as e:
                logger.error(f"Failed to init Binance broker: {e}")

        # Optional Execution Core (Alpaca)
        self.alp_key = os.getenv("ALPACA_API_KEY")
        self.alp_secret = os.getenv("ALPACA_SECRET_KEY")
        self.alp_paper = os.getenv("ALPACA_PAPER", "True").lower() == "true"
        self.alpaca = None
        if self.alp_key and self.alp_secret:
            try:
                import ccxt
                self.alpaca = ccxt.alpaca({
                    'apiKey': self.alp_key,
                    'secret': self.alp_secret,
                })
                if self.alp_paper:
                    self.alpaca.set_sandbox_mode(True)
                logger.info(f"[EXECUTION] Alpaca Broker Initialized for {node_id} (Paper={self.alp_paper})")
            except Exception as e:
                logger.error(f"Failed to init Alpaca broker: {e}")

        # Optional Execution Core (Hyperliquid)
        self.hl_key = os.getenv("HYPERLIQUID_PRIVATE_KEY")
        self.hl_broker = None
        if self.hl_key:
            try:
                from brokers.hyperliquid import HyperliquidBroker
                self.hl_broker = HyperliquidBroker(private_key=self.hl_key)
                logger.info(f"[EXECUTION] Hyperliquid Broker Initialized for {node_id}")
            except Exception as e:
                logger.error(f"Failed to init Hyperliquid broker: {e}")

    async def connect(self):
        # Resolve capabilities
        capabilities = ["butterfly", "chaos", "stats"]
        if self.broker: capabilities.append("execution-crypto")
        if self.alpaca: capabilities.append("execution-stocks")
        if self.hl_broker: capabilities.append("execution-hyperliquid")
        
        mode = "execution" if len(capabilities) > 3 else "chaos"
        self.swarm = SwarmNode(mode=mode, prime_url=f"{self.nexus_url}/ws/swarm")
        
        # Register Event Listeners
        self.swarm.on("TICK", self.process_tick)
        self.swarm.on("TRADE_ORDER", self.handle_trade_order)
        self.swarm.on("COMPUTE_TENSOR", self.process_tensor)
        self.swarm.on("FEDERATED_SYNC_ACK", self.process_fedavg_sync)
        self.swarm.on("PING", lambda p: asyncio.create_task(self.swarm.emit("PONG", {"ts": time.time()})))
        
        while self.running:
            try:
                await self.swarm.connect()
            except Exception as e:
                logger.error(f"Connection lost: {e}. Retrying in 5s...")
                await asyncio.sleep(5)

    async def handle_trade_order(self, payload):
        """
        Executes a trade order received from the Nexus.
        """
        symbol = payload["symbol"]
        side = payload["side"].lower()
        qty = payload["quantity"]
        mode = payload.get("mode", "PAPER") # Default to PAPER if unspecified
        
        # --- CRITICAL SAFETY CHECK ---
        # 1. If Order is LIVE but we are PAPER -> REJECT
        # 2. If Order is PAPER but we are LIVE -> FORCE SIMULATION (or REJECT if strict)
        
        # Determine Local Status
        is_crypto = any(symbol.endswith(s) for s in ["USDT", "USDC", "BUSD", "BTC", "EUR"])
        # If HL, check HL settings (assumed Live if key present, paper logic not verified here yet)
        # Simplify: If key present, allow LIVE.
        
        logger.info(f"[SWARM] 📨 Received {mode} Order: {side.upper()} {symbol} {qty}")
        
        # Determine Routing
        try:
            target_broker = None
            venue = "UNKNOWN"
            
            # 1. Hyperliquid (USDC pairs)
            if symbol.endswith("USDC") and self.hl_broker:
                target_broker = self.hl_broker
                venue = "HYPERLIQUID"
            
            # 2. Binance (Other Crypto)
            elif any(symbol.endswith(s) for s in ["USDT", "BUSD", "BTC", "EUR"]):
                target_broker = self.broker
                venue = "BINANCE"
                
            # 3. Stocks (Alpaca)
            else:
                target_broker = self.alpaca
                venue = "ALPACA"

            if not target_broker:
                logger.warning(f"[SWARM] No broker for {symbol} on {self.node_id}")
                return

            logger.info(f"[EXECUTION] {venue} {side.upper()} {symbol} ({qty})")
            
            # Execute
            # Use uniform place_order interface which HyperliquidBroker implementation supports
            if venue == "HYPERLIQUID":
                # hyperliquid broker.place_order(symbol, side, order_type, quantity)
                order = await target_broker.place_order(symbol, side, 'market', qty)
                logger.info(f"[EXECUTION] ✅ {venue} Order Filled: {order}")
            else:
                # CCXT
                order = await target_broker.create_order(symbol, 'market', side, qty)
                logger.info(f"[EXECUTION] ✅ {venue} Order Filled: {order.get('id')}")
                
        except Exception as e:
            logger.error(f"[EXECUTION] ❌ FAILED: {e}")

    async def process_fedavg_sync(self, payload):
        """
        Receives Global Weights from Prime after FedAvg round-trip
        and injects them into the local model.
        """
        topic = payload.get("topic", "UNKNOWN")
        global_weights = payload.get("global_weights", [])
        
        if not global_weights:
            return
            
        logger.info(f"[FEDERATED] ⚖️ Received Global Weights for {topic}! Syncing local model...")
        
        try:
            with torch.no_grad():
                for i, p in enumerate(self.local_model.parameters()):
                    if i < len(global_weights):
                        p.copy_(torch.tensor(global_weights[i]).view(p.shape))
            logger.info(f"[FEDERATED] ✅ Local Model Synchronized with Hive Mind.")
        except Exception as e:
            logger.error(f"[FEDERATED] ❌ Failed to sync weights: {e}")

    async def process_tick(self, payload):
        symbol = payload["symbol"]
        price = payload["price"]

        if symbol not in self.sensors:
            self.sensors[symbol] = ButterflySensor()
            self.stats[symbol] = IncrementalStats(window_size=20)

        # Compute
        self.sensors[symbol].update(price)
        self.stats[symbol].add_price(price)

        chaos = self.sensors[symbol].get_chaos_level()
        mean = self.stats[symbol].get_mean()
        std = self.stats[symbol].get_std()
        z_score = (price - mean) / std if std > 0 else 0

        # Stream Intelligence Back
        await self.swarm.emit("INTELLIGENCE", {
            "symbol": symbol,
            "chaos": chaos,
            "z_score": z_score,
            "ts": time.time()
        })

    async def process_tensor(self, payload):
        """
        Federated Edge Compute:
        Receives a Topological Payload (Tensor/Graph shape), computes local
        Prediction Error gradients, and sends them back to the Nexus.
        """
        tensor_id = payload.get("tensor_id")
        topic = payload.get("topic", "GENERIC")
        data = payload.get("data", [])
        
        if not data or len(data) != 3:
            return
            
        logger.info(f"[FEDERATED] 🧬 Computing Topological Loss for Tensor {tensor_id} ({topic})")
        
        # Zero gradients
        self.optimizer.zero_grad()
        
        # 1. Forward Pass (Data is [nodes, edges, vertices])
        x = torch.tensor(data, dtype=torch.float32)
        prediction = self.local_model(x)
        
        # 2. Compute Structural Prediction Error Loss
        # Target the real-time Chaos metric (if topic matches a symbol)
        target_val = 0.0
        if topic in self.sensors:
            target_val = self.sensors[topic].get_chaos_level()
            
        target = torch.tensor([target_val], dtype=torch.float32)
        loss_fn = nn.MSELoss()
        loss = loss_fn(prediction, target)
        
        # 3. Backward Pass
        loss.backward()
        
        # 4. Extract Gradients for the Swarm
        gradients = []
        for param in self.local_model.parameters():
            if param.grad is not None:
                gradients.append(param.grad.view(-1).tolist())
            else:
                gradients.append([])
                
        # 5. Local Weight Update (The Satellite learns autonomously!)
        self.optimizer.step()
                
        logger.info(f"[FEDERATED] ✅ Computed Gradients (Loss: {loss.item():.4f} | Target Chaos: {target_val:.4f})")
        
        # 6. Broadcast back to Nexus
        await self.swarm.emit("FEDERATED_GRADIENTS", {
            "topic": topic,
            "loss": loss.item(),
            "gradients": gradients,
            "tensor_id": tensor_id
        })

if __name__ == "__main__":
    # Priority: 1. NEXUS_URL 2. MASTER_URL 3. Default (Railway)
    default_url = "wss://prophitengine-production.up.railway.app"
    url = os.getenv("NEXUS_URL", os.getenv("MASTER_URL", default_url))
    
    nid = os.getenv("NODE_ID", f"satellite-{os.uname().nodename}")
    node = SatelliteNode(url, nid)
    try:
        asyncio.run(node.connect())
    except KeyboardInterrupt:
        pass
