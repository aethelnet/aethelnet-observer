import requests

def test_hl():
    res = requests.post("https://api.hyperliquid.xyz/info", json={"type": "meta"})
    data = res.json()
    universe = data.get("universe", [])
    for coin in universe:
        name = coin.get("name")
        if "AS" in name.upper() or "KAS" in name.upper():
            print(f"Found match: {name}")

test_hl()
