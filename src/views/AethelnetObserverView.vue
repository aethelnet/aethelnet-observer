<template>
  <div class="observer-mode" ref="containerRef">
    <div class="starfield-brutal"></div>
    <div class="hud">
      <h2>OBSERVER</h2>
      <p>CONSENSUS: {{ consensusScore.toFixed(1) }}%</p>
      <p>PEERS: {{ peers.length }}</p>
    </div>
    <svg class="radar" width="100%" height="100%" viewBox="0 0 600 600" preserveAspectRatio="xMidYMid meet">
      <g transform="translate(300, 300)">
        <!-- Radar Circles -->
        <circle r="80" class="radar-ring" />
        <circle r="180" class="radar-ring" />
        <circle r="280" class="radar-ring" />
        
        <!-- Local Node -->
        <circle r="12" class="local-node" />
        <text y="-25" class="node-label local">PRIME</text>
        
        <!-- Peer Nodes -->
        <g v-for="(peer, i) in peers" :key="peer.id" 
           :style="{ transform: `rotate(${peer.angle}deg) translate(${peer.distance}px, 0)` }">
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
import { ref, onMounted, onUnmounted } from 'vue'

const containerRef = ref<HTMLElement | null>(null)
const width = ref(600)
const height = ref(400)
const consensusScore = ref(94.2)

interface Peer {
  id: string
  name: string
  topic: string
  angle: number
  distance: number
  radius: number
  syncing: boolean
}

const peers = ref<Peer[]>([])
let simInterval: any;
let resizeObserver: ResizeObserver | null = null;

async function fetchGossip() {
  try {
    const res = await fetch('/aethelnet/graph/public')
    if (!res.ok) return
    const data = await res.json()
    
    const gossipArray = Array.isArray(data) ? data : (data.gossip || []);
    if (gossipArray.length > 0) {
      const newPeers = gossipArray.map((g: any, index: number) => {
        const existing = peers.value.find(p => p.id === g.id)
        return {
          id: g.id,
          name: g.source_peer || `Peer_${index}`,
          topic: g.thought_topic || 'Data',
          angle: existing ? existing.angle : Math.random() * 360,
          distance: existing ? existing.distance : 80 + Math.random() * 150,
          radius: existing ? existing.radius : 8 + Math.random() * 8,
          syncing: true
        }
      })
      peers.value = newPeers
    }
  } catch (err) {
    console.error("Failed to fetch gossip:", err)
  }
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
  
  fetchGossip()
  
  simInterval = setInterval(() => {
    fetchGossip()
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
})
</script>

<style scoped>
.observer-mode {
  width: 100%;
  height: 100%;
  background: #FFF;
  color: #1A1A1A;
  font-family: 'Space Mono', monospace;
  position: relative;
  overflow: hidden;
}

.starfield-brutal {
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  background-image: radial-gradient(#1A1A1A 2px, transparent 2px);
  background-size: 40px 40px;
  opacity: 0.1;
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
</style>
