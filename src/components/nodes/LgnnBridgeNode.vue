<template>
  <div class="p2p-bridge-node glass-panel">
    <div class="bridge-header">
      <div class="header-title">[ P2P BRIDGE ]</div>
      <div class="header-icon">🌉</div>
    </div>
    
    <div class="bridge-body">
      <div class="peer-list">
        <div class="list-title">KNOWN_PEERS [THE HOLY TRINITY]:</div>
        <div v-for="peer in peers" :key="peer.id" class="peer-row">
          <span class="peer-status" :class="peer.status"></span>
          <span class="peer-name">{{ peer.name }}</span>
          <span class="peer-ping">{{ peer.status === 'connected' ? peer.ping + 'ms' : '---' }}</span>
          <button class="peer-action" @click="togglePeer(peer)">
            {{ peer.status === 'connected' ? 'DISCONNECT' : 'CONNECT' }}
          </button>
        </div>
      </div>

      <div class="bridge-output">
        <div class="stream-header">MSGPACK_GOSSIP_STREAM</div>
        <pre class="output-text terminal-stream">{{ gossipStream }}</pre>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const props = defineProps<{
  node: any
}>()

const peers = ref([
  { id: '141', name: '141 Cosmic', status: 'disconnected', ping: 0 },
  { id: '92', name: '92 Trading', status: 'disconnected', ping: 0 },
  { id: '130', name: '130 Mainnet', status: 'disconnected', ping: 0 }
])
const gossipStream = ref('> SYSTEM: P2P BRIDGE INITIALIZED.\n> AWAITING PEER CONNECTIONS...\n')
let streamInterval: number | null = null

const togglePeer = (peer: any) => {
  if (peer.status === 'disconnected') {
    peer.status = 'connecting'
    gossipStream.value += `> NEGOTIATING WEBRTC HANDSHAKE WITH ${peer.name}...\n`
    setTimeout(() => {
      peer.status = 'connected'
      peer.ping = Math.floor(Math.random() * 40) + 12
      gossipStream.value += `> CONNECTION ESTABLISHED: ${peer.name} [PING: ${peer.ping}ms]\n`
      startGossip()
    }, 1200)
  } else {
    peer.status = 'disconnected'
    peer.ping = 0
    gossipStream.value += `> CONNECTION SEVERED: ${peer.name}\n`
    checkGossipStatus()
  }
}

const startGossip = () => {
  if (!streamInterval) {
    streamInterval = window.setInterval(() => {
      const activePeers = peers.value.filter(p => p.status === 'connected')
      if (activePeers.length === 0) return
      
      const randomPeer = activePeers[Math.floor(Math.random() * activePeers.length)]
      const hash = Math.random().toString(16).substr(2, 8).toUpperCase()
      const msgs = ['GRAIN_SYNC', 'TOPOLOGY_UPDATE', 'RESONANCE_SPIKE', 'STATE_DIFF']
      const msg = msgs[Math.floor(Math.random() * msgs.length)]
      
      const logLine = `[${new Date().toISOString().split('T')[1].substring(0,8)}] [${randomPeer.id}] ${msg} 0x${hash}\n`
      gossipStream.value += logLine
      
      const lines = gossipStream.value.split('\n')
      if (lines.length > 20) {
        gossipStream.value = lines.slice(lines.length - 20).join('\n')
      }
    }, 800)
  }
}

const checkGossipStatus = () => {
  const activePeers = peers.value.filter(p => p.status === 'connected')
  if (activePeers.length === 0 && streamInterval) {
    clearInterval(streamInterval)
    streamInterval = null
  }
}
</script>

<style scoped>
.p2p-bridge-node {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  color: #00FF41;
  font-family: 'Space Mono', monospace;
  padding: 10px;
  background: rgba(0, 10, 0, 0.9);
  border: 1px solid #00FF41;
}

.bridge-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #00FF41;
  padding-bottom: 10px;
  margin-bottom: 15px;
}

.header-title {
  font-weight: bold;
  letter-spacing: 2px;
}

.header-icon {
  font-size: 1.2rem;
}

.bridge-body {
  flex-grow: 1;
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.peer-list {
  background: rgba(0, 20, 0, 0.5);
  border: 1px dashed #00FF41;
  padding: 10px;
}

.list-title {
  font-size: 0.8rem;
  margin-bottom: 10px;
  opacity: 0.8;
}

.peer-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
  font-size: 0.9rem;
}

.peer-status {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: gray;
}
.peer-status.connecting { background: yellow; box-shadow: 0 0 5px yellow; }
.peer-status.connected { background: #00FF41; box-shadow: 0 0 5px #00FF41; }

.peer-name {
  flex-grow: 1;
}

.peer-ping {
  width: 50px;
  text-align: right;
  opacity: 0.7;
  font-size: 0.8rem;
}

.peer-action {
  background: transparent;
  color: #00FF41;
  border: 1px solid #00FF41;
  padding: 2px 8px;
  cursor: pointer;
  font-size: 0.7rem;
  transition: all 0.2s;
}
.peer-action:hover {
  background: rgba(0, 255, 65, 0.2);
}

.bridge-output {
  flex-grow: 1;
  display: flex;
  flex-direction: column;
  background: rgba(0, 0, 0, 0.6);
  border: 1px solid rgba(0, 255, 65, 0.3);
}

.stream-header {
  font-size: 0.7rem;
  padding: 5px;
  background: rgba(0, 255, 65, 0.1);
  border-bottom: 1px solid rgba(0, 255, 65, 0.3);
}

.output-text {
  padding: 10px;
  font-size: 0.8rem;
  margin: 0;
  overflow-y: auto;
  flex-grow: 1;
  max-height: 200px;
  white-space: pre-wrap;
  word-break: break-all;
}
</style>
