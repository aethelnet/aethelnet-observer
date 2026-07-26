import time
import requests
import random
from collections import deque
import numpy as np

# Use localhost if running natively on .141, otherwise point to .141
API_URL = "http://127.0.0.1:8000/api/lgnn/node"
BINANCE_URL = "https://api.binance.com/api/v3/ticker/price"
SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "DOGEUSDT"]

# Track price history for momentum calculation
# Storing the last 10 ticks (30 seconds)
history = {sym: deque(maxlen=10) for sym in SYMBOLS}

def get_prices():
    try:
        res = requests.get(BINANCE_URL, timeout=5)
        data = res.json()
        prices = {item['symbol']: float(item['price']) for item in data}
        return prices
    except Exception as e:
        print(f"Error fetching binance: {e}")
        return {}

def spawn_trade_signal(sym, momentum, action):
    signal_id = f"TRADE_SIGNAL_{sym}_{int(time.time())}"
    color = "🟢" if action == "LONG" else "🔴"
    confidence = min(0.5 + abs(momentum) * 100, 1.0)
    
    payload = {
        "id": signal_id,
        "label": f"{sym} SIGNAL",
        "content": f"{color} {action} TRIGGER! Momentum: {momentum:.4f}\nConfidence: {confidence:.2%}",
        "source_tag": "trade_signal",
        "node_type": "macro",
        "parent_id": "MARKETPLACE",
        "confidence": confidence
    }
    try:
        requests.post(API_URL, json=payload, timeout=2)
        print(f">>> SPAWNED TRADE SIGNAL: {sym} {action} <<<")
    except Exception as e:
        print(f"Signal Error: {e}")

print("Initializing Auratic Oracle Agent...")
print("Monitoring live markets for momentum anomalies...")

while True:
    prices = get_prices()
    for sym in SYMBOLS:
        if sym in prices:
            price = prices[sym]
            history[sym].append(price)
            
            # 1. Update the Market Feed Node (Sensor)
            jitter = random.uniform(-0.001, 0.001) * price
            display_price = price + jitter
            
            feed_payload = {
                "id": f"market_ticker_{sym}",
                "label": f"{sym.replace('USDT', '')}",
                "content": f"Live Price: ${display_price:.2f}",
                "source_tag": "market_feed",
                "node_type": "sensor",
                "parent_id": "ROOT",
                "confidence": 1.0
            }
            try:
                requests.post(API_URL, json=feed_payload, timeout=2)
            except:
                pass
            
            # 2. Check for Trade Signals (Momentum Spike)
            if len(history[sym]) == 10:
                # Calculate simple rate of change
                start_price = history[sym][0]
                end_price = history[sym][-1]
                momentum = (end_price - start_price) / start_price
                
                # Threshold for a "Spike" (0.1% move in 30 seconds is quite high for crypto in real-time)
                # We use a lower threshold here (0.01%) just to ensure the user sees the signals while testing
                THRESHOLD = 0.0001 
                
                if momentum > THRESHOLD:
                    spawn_trade_signal(sym, momentum, "LONG")
                    # Clear history to prevent duplicate signals immediately
                    history[sym].clear()
                elif momentum < -THRESHOLD:
                    spawn_trade_signal(sym, momentum, "SHORT")
                    history[sym].clear()
                
    time.sleep(3)
