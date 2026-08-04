# Aethelnet Observer

The **Aethelnet Observer** is the active telemetry dashboard, visualizer, and satellite execution layer for the Aethelnet LGNN Swarm.

While the core physics engine (Liquid Graph Neural Networks) resides in `aethelnet-core` and the master prime node in `auratic-systems-prime`, the Observer acts as the decentralized eye of the swarm. It connects to the network via the `aethelnet-sdk` and provides real-time insights into the topological state of the graph.

## Architecture

The Observer serves two primary functions:
1. **Satellite Node (Python):** Located in `src-python/`, the satellite node utilizes the Aethelnet SDK (`SwarmNode`) to connect to the P2P mesh. It processes incoming ticks, evaluates chaotic divergence (Butterfly Sensors), and executes trade orders via decentralized brokers (Binance, Alpaca, Hyperliquid).
2. **Telemetry Dashboard (Frontend):** A high-performance WebGL / Vue 3 interface that visualizes the network state, including the CodeSpider Blueprint Engine, rendering complex topologies as a 3D WebGL Galaxy.

## Getting Started

### 1. Python Satellite Node
The satellite node actively listens to the swarm and provides execution capabilities.
```bash
cd src-python
pip install -r requirements.txt
# Ensure aethelnet-sdk is installed
python main.py
```

### 2. Web Interface
The frontend provides the visual canvas for the network state.
```bash
npm install
npm run dev
```

## Galaxy Blueprint View
The Observer includes the massive **CodeSpider Blueprint Engine**.
You can open the Command Palette (`Cmd+K` or `/`) and type **"Load System Blueprint"** to instantly render the backend node's 181,000+ file/function dependencies as a 3D WebGL Galaxy using Three.js.

## Documentation
Extensive architectural evaluations, API mappings, and design system decisions are located in the `docs/` directory.

---
*Built by the Aethelnet Team. Open Source. Decentralized. Sovereign.*
