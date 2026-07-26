<template>
  <div class="observer-mode" :class="{ 'sanctuary-active': isSanctuaryActive }" ref="containerRef">
    <div class="starfield-brutal"></div>
    <div class="hud">
      <h2>OBSERVER</h2>
      <p>STATUS: <span :style="{ color: isConnected ? '#00FF00' : '#FF0000' }">{{ isConnected ? 'CONNECTED' : 'DISCONNECTED' }}</span></p>
      <p>CONSENSUS: {{ consensusScore.toFixed(1) }}%</p>
      <p>SWARM SIZE: {{ swarmSize }}</p>
      <p>AETHEL REWARDS: {{ aethelRewards.toFixed(4) }} $AETHEL</p>
      
      <div style="margin-top: 15px; margin-bottom: 5px;">LIQUID MANIFOLD VISCOSITY (TAU: {{ avgTau.toFixed(3) }})</div>
      <div class="manifold-bar">
         <div class="manifold-fill" :style="{ width: `${avgChaos * 100}%` }"></div>
      </div>
      <div style="display: flex; gap: 10px; margin-top: 15px;">
        <button @click="spawnCloudWorker" class="brutal-btn-small" style="flex: 1;">SPAWN WORKER</button>
        <button @click="injectChaos" class="brutal-btn-small" style="flex: 1; border-color: #E03C31; color: #E03C31;">INJECT CHAOS</button>
      </div>
    </div>
    
    <div v-if="godModeMessage" class="god-mode-banner">
      <h2>🧬 OUROBOROS INJECTION SUCCESS</h2>
      <p>{{ godModeMessage }}</p>
    </div>
    
    <div v-if="cellDivisionMessage" class="god-mode-banner" style="background: rgba(242, 193, 46, 0.9); color: #000; top: 120px; border-color: #000;">
      <h2>🚨 ELASTIC SWARMING TRIGGERED</h2>
      <p>{{ cellDivisionMessage }}</p>
    </div>

    <div v-if="isSanctuaryActive" class="sanctuary-banner">
      <h2>🛡️ TYPHOON SANCTUARY ACTIVE</h2>
      <p>MARKET CHAOS CRITICAL (> 0.8) • HALTING TRADING • SHIELDING CAPITAL</p>
    </div>

    <div v-if="focusedNode" class="subgraph-overlay">
      <div class="subgraph-panel">
        <h3>TACTICAL SUBGRAPH</h3>
        <p><strong>NODE:</strong> {{ focusedNode.name }}</p>
        <p><strong>ID:</strong> {{ focusedNode.id }}</p>
        <p><strong>TELEMETRY:</strong> {{ focusedNode.topic }}</p>
        <div style="margin-bottom: 10px; display: flex; align-items: center; gap: 10px; font-family: 'Space Mono', monospace;">
          <strong>TOPIC SUBSCRIPTION:</strong>
          <input type="text" v-model="draftSpecialization" style="background: transparent; color: #fff; border: 1px solid #555; padding: 4px; width: 120px;" placeholder="NONE" />
          <button @click="saveSpecialization" class="brutal-btn-small" style="padding: 4px 8px; font-size: 10px;">[ SAVE ]</button>
        </div>
        <p><strong>STATUS:</strong> {{ focusedNode.syncing ? 'PROCESSING TENSOR (HOT)' : 'IDLE / LISTENING' }}</p>
        <p><strong>DISTANCE:</strong> {{ focusedNode.distance.toFixed(0) }} AU</p>
        <div class="tensor-matrix">
           <div>[ {{ (Math.random()).toFixed(2) }} ]</div>
           <div>[ {{ (Math.random()).toFixed(2) }} ]</div>
           <div>[ {{ (Math.random()).toFixed(2) }} ]</div>
           <div>[ {{ (Math.random()).toFixed(2) }} ]</div>
        </div>
        <button v-if="focusedNodeId !== 'local_compute'" @click="decommissionNode" class="brutal-btn" style="margin-bottom: 10px; background: transparent; border-color: #E03C31; color: #E03C31;">[ DECOMMISSION NODE ]</button>
        <button v-else disabled class="brutal-btn" style="margin-bottom: 10px; background: transparent; border-color: #555; color: #555; cursor: not-allowed;">[ CORE NODE: PROTECTED ]</button>
        <button @click="focusedNodeId = null" class="brutal-btn">CLOSE SUBGRAPH</button>
      </div>
    </div>
    <svg class="radar" width="100%" height="100%" viewBox="0 0 600 600" preserveAspectRatio="xMidYMid meet">
      <g transform="translate(300, 300)">
        <!-- Radar Circles -->
        <circle r="80" class="radar-ring" />
        <circle r="180" class="radar-ring" />
        <circle r="280" class="radar-ring" />

        <!-- Typhoon Shield -->
        <g v-if="isSanctuaryActive" class="typhoon-shield">
          <polygon points="0,-160 138,-80 138,80 0,160 -138,80 -138,-80" class="shield-hexagon" />
          <circle r="160" class="shield-pulse" />
        </g>
        
        <!-- Local Node -->
        <circle r="12" class="local-node" />
        <text y="-25" class="node-label local">PRIME</text>
        
        <!-- Peer Nodes -->
        <g v-for="(peer, i) in peers" :key="peer.id" 
           @click="focusedNodeId = peer.id"
           :style="{ transform: `rotate(${peer.angle}deg) translate(${peer.distance}px, 0)`, cursor: 'pointer' }">
          <!-- Invisible Hitbox for easier clicking -->
          <circle r="40" fill="transparent" pointer-events="all" />
          <circle :r="peer.radius" class="peer-node" :class="{ 'is-syncing': peer.syncing }" />
          <line x1="0" y1="0" :x2="-peer.distance" y2="0" class="peer-link" :class="{ 'is-syncing': peer.syncing }" />
          <text y="-15" :style="{ transform: `rotate(${-peer.angle}deg)` }" class="node-label">{{ peer.name }}</text>
          <text y="15" :style="{ transform: `rotate(${-peer.angle}deg)` }" class="node-sublabel">{{ peer.topic }}</text>
        </g>
      </g>
    </svg>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, watch } from 'vue'

const containerRef = ref<HTMLElement | null>(null)
const width = ref(600)
const height = ref(400)
const consensusScore = ref(94.2)
const aethelRewards = ref(0.0)
const swarmSize = ref(0)
const isConnected = ref(false)
const focusedNodeId = ref<string | null>(null)
const godModeMessage = ref("")
const cellDivisionMessage = ref("")
const previousSwarmSize = ref(0)
const avgChaos = ref(0.0)
const avgTau = ref(1.0)
const isSanctuaryActive = computed(() => avgChaos.value > 0.8)

interface Peer {
  id: string
  name: string
  topic: string
  subscription: string
  angle: number
  distance: number
  radius: number
  syncing: boolean
}

const injectChaos = () => {
  // Override network chaos to trigger the Sanctuary Mode for 8 seconds
  avgChaos.value = 0.99;
  setTimeout(() => {
    // Let it naturally be overwritten by the next SWARM_UPDATE
    avgChaos.value = 0.5;
  }, 8000);
}

const peers = ref<Peer[]>([])
const draftSpecialization = ref("")

const focusedNode = computed(() => peers.value.find(p => p.id === focusedNodeId.value))

watch(focusedNodeId, (newId) => {
  if (newId) {
    const node = peers.value.find(p => p.id === newId);
    draftSpecialization.value = node?.subscription || "";
  }
})

let simInterval: any;
let resizeObserver: ResizeObserver | null = null;
let ws: WebSocket | null = null;
let myNodeId: string = "";

async function spawnCloudWorker() {
  try {
    const res = await fetch(`http://127.0.0.1:8000/ws/swarm/spawn`, { method: 'POST' });
    if (res.ok) {
      console.log("Cloud Worker Spawned!");
    }
  } catch(e) {
    console.error("Failed to spawn cloud worker:", e);
  }
}

async function decommissionNode() {
  if (!focusedNodeId.value) return;
  const nodeId = focusedNodeId.value;
  try {
    const res = await fetch(`http://127.0.0.1:8000/ws/swarm/kill/${nodeId}`, { method: 'DELETE' });
    if (res.ok) {
      console.log(`Node ${nodeId} decommissioned.`);
      focusedNodeId.value = null; // Close panel
    }
  } catch(e) {
    console.error("Failed to decommission node:", e);
  }
}

async function saveSpecialization() {
  if (!focusedNodeId.value) return;
  const nodeId = focusedNodeId.value;
  const topic = draftSpecialization.value;
  try {
    const res = await fetch(`http://127.0.0.1:8000/ws/swarm/specialize/${nodeId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ topic })
    });
    if (res.ok) {
      console.log(`Node ${nodeId} specialized to ${topic}`);
    }
  } catch(e) {
    console.error("Failed to set specialization:", e);
  }
}

function connectSwarm() {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  // Fallback to local dev if no backend is specified, assuming Prime runs on 8000
  const wsUrl = `ws://127.0.0.1:8000/ws/swarm`;
  
  ws = new WebSocket(wsUrl);

  ws.onopen = () => {
    isConnected.value = true;
    console.log("[SWARM] Connected to Auratic Prime!");
    myNodeId = "ObserverNode_" + Math.floor(Math.random() * 10000);
    // Handshake
    ws?.send(JSON.stringify({
      type: "JOIN_SWARM",
      node_id: myNodeId,
      capabilities: ["compute", "gossip"]
    }));
  };

  ws.onmessage = (event) => {
    try {
      const msg = JSON.parse(event.data);
      if (msg.type === "WELCOME") {
        console.log(`[SWARM] Welcome received! Node ID: ${msg.node_id}, Swarm Size: ${msg.swarm_size}`);
        swarmSize.value = msg.swarm_size;
      }
      else if (msg.type === "COMPUTE_TENSOR") {
        console.log(`[SWARM] 🧠 Received Tensor compute request: ${msg.tensor_id}`);
        // Simulate heavy math: sum of payload
        const data = msg.data || [];
        const result = data.reduce((a: number, b: number) => a + b, 0);
        
        // Show visual feedback that this node is doing something!
        const existing = peers.value.find(p => p.id === 'local_compute');
        if (existing) {
          existing.syncing = true;
          existing.topic = `TSR: ${msg.tensor_id.substring(0, 8)}`;
        } else {
          peers.value.push({
            id: 'local_compute',
            name: 'COMPUTING...',
            topic: `TSR: ${msg.tensor_id.substring(0, 8)}`,
            subscription: '',
            angle: Math.random() * 360,
            distance: 120,
            radius: 10,
            syncing: true
          });
        }
        
        setTimeout(() => {
          ws?.send(JSON.stringify({
            type: "TENSOR_RESULT",
            tensor_id: msg.tensor_id,
            result: result
          }));
        }, 800); // fake computation time
      }
      else if (msg.type === "TENSOR_ACK") {
        console.log(`[SWARM] 💰 Tensor accepted! Reward: ${msg.reward_aethel}`);
        aethelRewards.value += msg.reward_aethel;
        
        // Turn off syncing visual
        const existing = peers.value.find(p => p.id === 'local_compute');
        if (existing) {
          existing.syncing = false;
          existing.name = 'STANDBY';
        }
      }
      else if (msg.type === "SWARM_UPDATE" && msg.payload && msg.payload.peers) {
         const currentSize = Object.keys(msg.payload.peers).length;
         
         if (currentSize > previousSwarmSize.value && previousSwarmSize.value > 0) {
             cellDivisionMessage.value = `Network Viscosity critical. Swarm autonomously scaled to ${currentSize} nodes.`;
             setTimeout(() => { cellDivisionMessage.value = ""; }, 5000);
         }
         previousSwarmSize.value = currentSize;
         swarmSize.value = currentSize;
         
         // Dynamically render other peers in the Swarm on the radar
         let totalChaos = 0;
         let totalTau = 0;
         let count = 0;
         
         for (const [peerId, pData] of Object.entries(msg.payload.peers)) {
             // Extract metrics
             const chaos = (pData as any).last_chaos || 0;
             const tau = (pData as any).last_tau || 1;
             totalChaos += chaos;
             totalTau += tau;
             count++;

             // Don't duplicate the local node visualization
             if (peerId === myNodeId) continue; 
             
             const zScore = (pData as any).last_z || 0;
             const sub = (pData as any).topic_subscription || "";
             
             let existing = peers.value.find(p => p.id === peerId);
             if (!existing) {
                 peers.value.push({
                     id: peerId,
                     name: peerId.substring(0, 15),
                     topic: 'Z-SCORE: ' + (zScore as number).toFixed(2),
                     subscription: sub,
                     angle: Math.random() * 360,
                     distance: 120 + Math.random() * 140,
                     radius: 8,
                     syncing: false
                 });
             } else {
                 existing.topic = 'Z-SCORE: ' + (zScore as number).toFixed(2);
                 existing.subscription = sub;
                 // Randomly blip to show activity
                 if (Math.random() > 0.7) {
                     existing.syncing = true;
                     setTimeout(() => existing.syncing = false, 500);
                 }
             }
         }
         
         // Cleanup disconnected peers (keep local_compute)
         peers.value = peers.value.filter(p => 
            p.id === 'local_compute' || Object.keys(msg.payload.peers).includes(p.id)
         );
         
         if (count > 0) {
             avgChaos.value = totalChaos / count;
             avgTau.value = totalTau / count;
         }
      }
      else if (msg.type === "FEDERATED_SYNC_ACK") {
        console.log(`[SWARM] 🧬 FedAvg completed for ${msg.topic}. Merged ${msg.nodes_merged} nodes.`);
        godModeMessage.value = `Global Model weights updated with ${msg.nodes_merged} edge gradients for topic: ${msg.topic}`;
        
        // Flash nodes of this topic
        peers.value.forEach(p => {
          if (p.subscription === msg.topic) {
            p.syncing = true;
            setTimeout(() => p.syncing = false, 1500);
          }
        });
        
        setTimeout(() => {
          godModeMessage.value = "";
        }, 3500);
      }
    } catch (e) {
      console.error("[SWARM] Failed to parse message", e);
    }
  };

  ws.onclose = () => {
    isConnected.value = false;
    console.log("[SWARM] Disconnected from Prime. Retrying in 5s...");
    setTimeout(connectSwarm, 5000);
  };
}

onMounted(() => {
  if (containerRef.value) {
    resizeObserver = new ResizeObserver((entries) => {
      for (let entry of entries) {
        width.value = entry.contentRect.width
        height.value = entry.contentRect.height
      }
    })
    resizeObserver.observe(containerRef.value)
  }
  
  connectSwarm();
  
  simInterval = setInterval(() => {
    peers.value.forEach(p => {
      p.syncing = false;
      p.angle += (Math.random() - 0.5) * 5; // Faster rotation for brutalism
    })
    consensusScore.value = 90 + Math.random() * 8;
  }, 2000)
})

onUnmounted(() => {
  if (resizeObserver) resizeObserver.disconnect()
  clearInterval(simInterval)
  if (ws) ws.close()
})
</script>

<style scoped>
.observer-mode {
  position: relative;
  width: 100%;
  height: 100vh;
  background: #FFF;
  color: #1A1A1A;
  overflow: hidden;
  font-family: 'Space Mono', monospace;
  transition: background 1s ease, color 1s ease;
}

.observer-mode.sanctuary-active {
  background: #1a0505; /* Deep red-black bunker feel */
  color: #fff; /* Ensure text is legible on dark background */
}

.observer-mode.sanctuary-active .radar-ring {
  stroke: rgba(255, 60, 60, 0.3);
}

.observer-mode.sanctuary-active .local-node {
  fill: #ff3c3c;
  filter: drop-shadow(0 0 10px #ff3c3c);
}

.observer-mode.sanctuary-active .peer-node {
  fill: #ffa07a;
}

.observer-mode.sanctuary-active .peer-link {
  stroke: rgba(255, 160, 122, 0.4);
}

.observer-mode.sanctuary-active .manifold-fill {
  background: #ff3c3c;
  box-shadow: 0 0 10px #ff3c3c;
}

.sanctuary-banner {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: rgba(255, 60, 60, 0.15);
  border: 2px solid #ff3c3c;
  padding: 30px 40px;
  text-align: center;
  z-index: 100;
  backdrop-filter: blur(10px);
  animation: alarm-pulse 2s infinite alternate;
}

.sanctuary-banner h2 {
  margin: 0 0 10px 0;
  color: #ff3c3c;
  font-size: 32px;
  letter-spacing: 4px;
}

.sanctuary-banner p {
  margin: 0;
  color: #ffcccc;
  font-size: 16px;
  letter-spacing: 2px;
}

.typhoon-shield {
  animation: spin-slow 20s linear infinite;
}

.shield-hexagon {
  fill: rgba(255, 60, 60, 0.1);
  stroke: #ff3c3c;
  stroke-width: 2;
  stroke-dasharray: 10 10;
  animation: dash-scroll 2s linear infinite;
}

.shield-pulse {
  fill: transparent;
  stroke: #ff3c3c;
  stroke-width: 1;
  animation: shield-ping 2s cubic-bezier(0, 0, 0.2, 1) infinite;
}

@keyframes shield-ping {
  0% { transform: scale(0.8); opacity: 1; stroke-width: 3; }
  100% { transform: scale(1.5); opacity: 0; stroke-width: 1; }
}

@keyframes dash-scroll {
  to { stroke-dashoffset: 20; }
}

@keyframes spin-slow {
  to { transform: rotate(360deg); }
}

@keyframes alarm-pulse {
  0% { box-shadow: 0 0 10px rgba(255,60,60,0.2); }
  100% { box-shadow: 0 0 30px rgba(255,60,60,0.6); }
}

.starfield-brutal {
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  background-image: radial-gradient(#1A1A1A 2px, transparent 2px);
  background-size: 40px 40px;
  opacity: 0.1;
  pointer-events: none;
}

.hud {
  position: absolute;
  top: 15px;
  left: 15px;
  z-index: 10;
  border: 2px solid #1A1A1A;
  background: #F2C12E;
  padding: 10px;
  box-shadow: 4px 4px 0px #1A1A1A;
}

.hud h2 {
  font-size: 1.2rem;
  font-weight: 900;
  margin: 0 0 5px 0;
  color: #1A1A1A;
  text-transform: uppercase;
}

.hud p {
  color: #1A1A1A;
  margin: 2px 0;
  font-size: 0.8rem;
  font-weight: 700;
  text-transform: uppercase;
}

.radar-ring {
  fill: none;
  stroke: #1A1A1A;
  stroke-width: 2;
  stroke-dasharray: 8 8;
}

.local-node {
  fill: #E03C31;
  stroke: #1A1A1A;
  stroke-width: 3;
}

.peer-node {
  fill: #F2C12E;
  stroke: #1A1A1A;
  stroke-width: 2;
}

.peer-node.is-syncing {
  fill: #E03C31;
  stroke-width: 4;
}

.peer-link {
  stroke: #1A1A1A;
  stroke-width: 1;
  stroke-dasharray: 4 4;
}

.peer-link.is-syncing {
  stroke: #E03C31;
  stroke-width: 3;
  stroke-dasharray: none;
}

.node-label {
  fill: #1A1A1A;
  font-size: 12px;
  font-weight: 900;
  text-anchor: middle;
  text-transform: uppercase;
}

.node-label.local {
  font-size: 16px;
}

.node-sublabel {
  fill: #666;
  font-size: 10px;
  font-weight: 700;
  text-anchor: middle;
  text-transform: uppercase;
}

/* TACTICAL SUBGRAPH OVERLAY */
.subgraph-overlay {
  position: absolute;
  top: 0; right: 0; bottom: 0;
  width: 400px;
  background: #1A1A1A;
  color: #FFF;
  border-left: 4px solid #F2C12E;
  padding: 20px;
  z-index: 50;
  display: flex;
  flex-direction: column;
}

.subgraph-panel h3 {
  color: #E03C31;
  font-size: 1.5rem;
  font-weight: 900;
  border-bottom: 2px solid #333;
  padding-bottom: 10px;
  margin-top: 0;
}

.subgraph-panel p {
  margin: 10px 0;
  font-size: 0.9rem;
}

.tensor-matrix {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  margin: 20px 0;
  background: #333;
  padding: 10px;
  font-size: 0.8rem;
  color: #F2C12E;
}

.brutal-btn {
  margin-top: auto;
  background: #E03C31;
  color: #1A1A1A;
  border: 2px solid #1A1A1A;
  padding: 15px;
  font-family: 'Space Mono', monospace;
  font-weight: 900;
  font-size: 1.2rem;
  cursor: pointer;
  box-shadow: 4px 4px 0px #000;
  text-transform: uppercase;
  transition: all 0.1s;
}

.brutal-btn:active {
  transform: translate(2px, 2px);
  box-shadow: 2px 2px 0px #000;
}

.brutal-btn:hover {
  background: #FFF;
  color: #000;
}

.brutal-btn-small {
  background: #1A1A1A;
  color: #F2C12E;
  border: 2px solid #1A1A1A;
  padding: 8px;
  font-family: 'Space Mono', monospace;
  font-weight: 700;
  font-size: 0.8rem;
  cursor: pointer;
  box-shadow: 2px 2px 0px #000;
  text-transform: uppercase;
  transition: all 0.1s;
}

.brutal-btn-small:hover {
  background: #E03C31;
  color: #FFF;
}

.brutal-btn-small:active {
  transform: translate(1px, 1px);
  box-shadow: 1px 1px 0px #000;
}

.god-mode-banner {
  position: absolute;
  top: 10%;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(20, 20, 20, 0.95);
  border: 2px solid #ff4400;
  color: #ff4400;
  padding: 20px 40px;
  text-align: center;
  z-index: 100;
  animation: glitch-pulse 0.2s infinite, god-mode-fade 3.5s forwards;
  box-shadow: 0 0 20px #ff4400, inset 0 0 10px #ff4400;
  font-family: 'Space Mono', monospace;
}
.god-mode-banner h2 {
  margin: 0 0 10px 0;
  letter-spacing: 2px;
}
.god-mode-banner p {
  margin: 0;
  font-size: 14px;
}
@keyframes god-mode-fade {
  0% { opacity: 0; transform: translateX(-50%) scale(0.9); }
  10% { opacity: 1; transform: translateX(-50%) scale(1.05); }
  15% { transform: translateX(-50%) scale(1.0); }
  80% { opacity: 1; }
  100% { opacity: 0; transform: translateX(-50%) scale(1.1); }
}

@media (max-width: 600px) {
  .brutal-btn-small:active {
    transform: translate(1px, 1px);
    box-shadow: 1px 1px 0px #000;
  }
}

.manifold-bar {
  width: 100%;
  height: 12px;
  background: #111;
  border: 1px solid #555;
  margin-top: 5px;
  position: relative;
  overflow: hidden;
}

.manifold-fill {
  height: 100%;
  background: linear-gradient(90deg, #F2C12E, #E03C31);
  transition: width 0.3s ease-out;
  box-shadow: 0 0 10px #E03C31;
}
</style>
