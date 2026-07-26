import requests
import time

def test_candles():
    end_ms = int(time.time() * 1000)
    start_ms = end_ms - (100 * 60 * 1000) # 100 minutes ago
    payload = {
        "type": "candleSnapshot",
        "req": {
            "coin": "KAS",
            "interval": "1m",
            "startTime": start_ms,
            "endTime": end_ms
        }
    }
    print(f"Payload: {payload}")
    res = requests.post("https://api.hyperliquid.xyz/info", json=payload)
    print(f"Status: {res.status_code}")
    if res.status_code == 200:
        data = res.json()
        print(f"Items: {len(data) if isinstance(data, list) else data}")
    else:
        print(f"Error: {res.text}")

test_candles()
