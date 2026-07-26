import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import random
import time

app = FastAPI()

# Enable CORS just in case
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# A pool of fun, cyberpunk-esque node names for our swarm
NODE_NAMES = [
    "Neuromancer_01", "Wintermute_Core", "Kusanagi_Ghost", "Turing_Police_99",
    "Aethel_Drone_Alpha", "Lenovo_2015_Hero", "Basement_Server_X", "Void_Walker_2",
    "Neon_Samurai", "Swarm_Node_77", "Null_Pointer_Sec", "Zero_Day_Prophet"
]

TOPICS = [
    "Market_Sentiment", "Orderbook_Imbalance", "Whale_Tracker", "Liquid_Core_Sync",
    "Volatility_Spike", "Dark_Pool_Anomaly", "Arbitrage_Scan", "Loss_Landscape_Calc"
]

@app.get("/aethelnet/graph/public")
def get_public_graph():
    # Simulate an active, breathing swarm network (between 4 and 12 nodes online)
    active_nodes_count = random.randint(4, 12)
    
    gossip_data = []
    selected_names = random.sample(NODE_NAMES, active_nodes_count)
    
    for i in range(active_nodes_count):
        gossip_data.append({
            "id": f"node_{i}_{int(time.time())}",
            "source_peer": selected_names[i],
            "thought_topic": random.choice(TOPICS)
        })
        
    return {"gossip": gossip_data}

if __name__ == "__main__":
    print("🚀 Mock Swarm Backend starting on port 1421...")
    print("📡 Emitting simulated peer gossip for Aethelnet Observer...")
    uvicorn.run(app, host="127.0.0.1", port=1421)
