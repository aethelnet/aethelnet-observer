<template>
  <div class="p2p-mesh-overlay" :class="{ 'is-online': isOnline }">
    <div class="p2p-header">
      <div class="status-indicator"></div>
      <h3 class="mesh-title">AETHELNET // P2P MESH</h3>
    </div>

    <div class="p2p-body">
      <div class="stat-row">
        <span class="stat-label">STATUS:</span>
        <span class="stat-value" :class="isOnline ? 'text-green' : 'text-red'">
          {{ isOnline ? 'ONLINE (TRACKER SYNCED)' : 'OFFLINE (LOCAL ONLY)' }}
        </span>
      </div>
      
      <div class="stat-row">
        <span class="stat-label">ACTIVE PEERS:</span>
        <span class="stat-value">{{ activePeers.length }}</span>
      </div>

      <div class="stat-row">
        <span class="stat-label">LATEST SYNC (LAMPORT):</span>
        <span class="stat-value">{{ lastSyncTime }}</span>
      </div>

      <div class="mesh-controls">
        <button 
          class="cyber-button" 
          @click="toggleConnection"
          :class="{ 'btn-disconnect': isOnline }"
        >
          {{ isOnline ? 'SEVER CONNECTION' : 'UPLINK TO MESH' }}
        </button>

        <div class="toggle-wrapper" v-if="isOnline">
          <label class="cyber-toggle">
            <input type="checkbox" v-model="publishLocal" />
            <span class="slider"></span>
          </label>
          <span class="toggle-label">GOSSIP LOCAL CONCEPTS (PUBLIC)</span>
        </div>
      </div>
    </div>
    
    <div class="peer-list" v-if="isOnline && activePeers.length > 0">
      <div class="peer-list-title">NEIGHBORS DETECTED:</div>
      <div class="peer-item" v-for="peer in activePeers" :key="peer">
        <span class="peer-ip">[{{ peer }}]</span>
        <span class="peer-pulse">_</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onUnmounted } from 'vue';

const isOnline = ref(false);
const publishLocal = ref(false);
const activePeers = ref([]);
const lastSyncTime = ref('N/A');

let syncInterval = null;

const toggleConnection = async () => {
  if (isOnline.value) {
    // Disconnect
    isOnline.value = false;
    clearInterval(syncInterval);
    activePeers.value = [];
    lastSyncTime.value = 'N/A';
  } else {
    // Connect
    isOnline.value = true;
    publishLocal.value = true;
    lastSyncTime.value = new Date().toLocaleTimeString();
    
    // Simulate first tracker ping
    await pingTracker();
    
    // Start background sync
    syncInterval = setInterval(pingTracker, 5000);
  }
};

const pingTracker = async () => {
  try {
    // In production, this points to 92.5.45.124:8000
    // We use a relative or configured API base URL
    const baseUrl = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';
    
    // 1. Register ourselves
    const regRes = await fetch(`${baseUrl}/p2p/tracker/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        peer_id: `browser_node_${Math.floor(Math.random()*1000)}`,
        peer_address: "web_client" // The backend will see the real IP
      })
    });
    
    // 2. Fetch active peers
    const peerRes = await fetch(`${baseUrl}/p2p/tracker/peers`);
    if (peerRes.ok) {
      const data = await peerRes.json();
      activePeers.value = data.peers;
      lastSyncTime.value = new Date().toLocaleTimeString();
    }
  } catch (err) {
    console.error("[P2P] Tracker ping failed:", err);
  }
};

onUnmounted(() => {
  if (syncInterval) clearInterval(syncInterval);
});
</script>

<style scoped>
.p2p-mesh-overlay {
  position: absolute;
  top: 20px;
  right: 20px;
  width: 320px;
  background: rgba(10, 10, 15, 0.85);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-left: 3px solid #ff3366;
  color: #e0e0e0;
  font-family: 'JetBrains Mono', monospace;
  padding: 15px;
  z-index: 9999;
  box-shadow: 0 10px 30px rgba(0,0,0,0.5);
  transition: all 0.3s ease;
}

.p2p-mesh-overlay.is-online {
  border-left-color: #00ffcc;
  box-shadow: 0 10px 30px rgba(0, 255, 204, 0.1);
}

.p2p-header {
  display: flex;
  align-items: center;
  margin-bottom: 15px;
  border-bottom: 1px solid rgba(255,255,255,0.1);
  padding-bottom: 10px;
}

.status-indicator {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #ff3366;
  margin-right: 10px;
  box-shadow: 0 0 10px #ff3366;
}

.is-online .status-indicator {
  background: #00ffcc;
  box-shadow: 0 0 10px #00ffcc;
  animation: pulse 2s infinite;
}

.mesh-title {
  margin: 0;
  font-size: 0.9rem;
  font-weight: 700;
  letter-spacing: 1px;
}

.stat-row {
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
  margin-bottom: 8px;
}

.stat-label {
  color: #888;
}

.text-green { color: #00ffcc; }
.text-red { color: #ff3366; }

.mesh-controls {
  margin-top: 20px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.cyber-button {
  background: transparent;
  border: 1px solid #00ffcc;
  color: #00ffcc;
  padding: 8px 0;
  font-family: inherit;
  font-size: 0.75rem;
  font-weight: bold;
  cursor: pointer;
  transition: all 0.2s;
}

.cyber-button:hover {
  background: rgba(0, 255, 204, 0.2);
}

.btn-disconnect {
  border-color: #ff3366;
  color: #ff3366;
}

.btn-disconnect:hover {
  background: rgba(255, 51, 102, 0.2);
}

.toggle-wrapper {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 5px;
}

.toggle-label {
  font-size: 0.65rem;
  color: #aaa;
}

.cyber-toggle {
  position: relative;
  display: inline-block;
  width: 34px;
  height: 18px;
}

.cyber-toggle input {
  opacity: 0;
  width: 0;
  height: 0;
}

.slider {
  position: absolute;
  cursor: pointer;
  top: 0; left: 0; right: 0; bottom: 0;
  background-color: rgba(255,255,255,0.1);
  transition: .4s;
  border: 1px solid rgba(255,255,255,0.3);
}

.slider:before {
  position: absolute;
  content: "";
  height: 12px;
  width: 12px;
  left: 2px;
  bottom: 2px;
  background-color: #aaa;
  transition: .4s;
}

input:checked + .slider {
  background-color: rgba(0, 255, 204, 0.2);
  border-color: #00ffcc;
}

input:checked + .slider:before {
  transform: translateX(16px);
  background-color: #00ffcc;
}

.peer-list {
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px dashed rgba(255,255,255,0.1);
  font-size: 0.7rem;
}

.peer-list-title {
  color: #888;
  margin-bottom: 5px;
}

.peer-item {
  color: #00ffcc;
  display: flex;
  justify-content: space-between;
  margin-bottom: 3px;
}

.peer-pulse {
  animation: blink 1s infinite;
}

@keyframes pulse {
  0% { box-shadow: 0 0 5px #00ffcc; }
  50% { box-shadow: 0 0 15px #00ffcc; }
  100% { box-shadow: 0 0 5px #00ffcc; }
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}
</style>
