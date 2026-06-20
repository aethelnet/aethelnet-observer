<template>
  <div class="macro-vision-container">
    <div class="overlay-header">
      <h1 class="glitch" data-text="MACRO VISION 3D">MACRO VISION 3D</h1>
      
      <!-- SNIPER SEARCH -->
      <div class="search-box">
        <input 
          v-model="searchQuery" 
          @input="applySearch"
          type="text" 
          class="brutal-input" 
          placeholder="[ FOCUS NODE... ]" 
        />
      </div>

      <button class="brutal-btn" @click="$emit('close')">[ RETURN TO 2D ]</button>
    </div>
    
    <div class="hud">
      <div class="hud-stat">NODES: {{ graphData.nodes.length }}</div>
      <div class="hud-stat">LINKS: {{ graphData.links.length }}</div>
      <div class="hud-stat blink">LIVE DATA STREAM</div>
      <div v-if="errorMessage" style="color: #E03C31; margin-top: 10px;">ERR: {{ errorMessage }}</div>
      <div v-if="debugInfo" style="color: #F2C12E; margin-top: 10px;">DBG: {{ debugInfo }}</div>
    </div>

    <!-- NODE DETAILS PANEL -->
    <div v-if="selectedNode" class="node-panel">
      <div class="panel-header">
        <span class="panel-title">{{ selectedNode.node_type === 'macro' ? 'MACRO PRISM' : (selectedNode.isManual ? 'SEED NODE' : 'SPIDER NODE') }}</span>
        <button class="icon-btn" @click="selectedNode = null">[X]</button>
      </div>
      <div class="panel-body">
        <div class="data-row"><strong>ID:</strong> <span>{{ selectedNode.id }}</span></div>
        <div class="data-row"><strong>CONFIDENCE:</strong> <span>{{ (selectedNode.val).toFixed(2) }}</span></div>
        <div class="data-row"><strong>ENTROPY:</strong> <span>{{ (selectedNode.entropy || 0).toFixed(2) }}</span></div>
        <div class="node-content-box">
          <div class="content-label">EXTRACTED KNOWLEDGE:</div>
          <div class="content-text">{{ selectedNode.text_content || selectedNode.name || 'No semantic data available.' }}</div>
        </div>
      </div>
    </div>

    <div ref="graphContainer" class="graph-3d-wrapper"></div>
    
    <!-- THE DIARY -->
    <TomRiddleDiary @node-spawned="fetchData" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, markRaw } from 'vue'
import ForceGraph3D from '3d-force-graph'
import { UnrealBloomPass } from 'three/examples/jsm/postprocessing/UnrealBloomPass.js'
import * as THREE from 'three'
import { API_BASE } from '../shared/api.js'
import TomRiddleDiary from './TomRiddleDiary.vue'

defineEmits(['close'])

const graphContainer = ref<HTMLDivElement | null>(null)
let graph: any = null
let interval: any = null

const graphData = ref({ nodes: [], links: [] })
const errorMessage = ref('')
const debugInfo = ref('')
const selectedNode = ref<any>(null)
const searchQuery = ref('')

onMounted(async () => {
  if (graphContainer.value) {
    try {
      const GraphConstructor = typeof ForceGraph3D === 'function' ? ForceGraph3D : (ForceGraph3D as any).default || (window as any).ForceGraph3D;
      
      graph = GraphConstructor()(graphContainer.value)
        .backgroundColor('rgba(0,0,0,0)')
      .nodeLabel('label')
      .nodeAutoColorBy('node_type')
      .linkDirectionalParticles(2)
      .linkDirectionalParticleWidth(1.5)
      .linkDirectionalParticleSpeed(d => (d as any).weight * 0.01)
      .nodeVal(n => ((n as any).confidence || 0.5) * 5)
      .nodeColor(n => {
        const node = n as any;
        const q = searchQuery.value.toLowerCase();
        
        // Is it part of the search focus?
        let isFocused = true;
        if (q) {
          const textMatch = (node.name || '').toLowerCase().includes(q) || (node.text_content || '').toLowerCase().includes(q);
          isFocused = textMatch;
        }

        if (!isFocused) return 'rgba(30, 30, 30, 0.2)'; // Ghosted out
        
        if (node.node_type === 'macro') return '#E03C31'; // Operator/Prism
        if (node.isManual) return '#00FF41'; // Seed
        return '#005096'; // Spider
      })
      .nodeRelSize(4)
      .linkWidth(d => {
        const q = searchQuery.value.toLowerCase();
        if (q) return 0.5; // Dim all links when searching
        return (d as any).weight * 1.5;
      })
      .linkColor(link => {
        const q = searchQuery.value.toLowerCase();
        if (q) return 'rgba(255, 255, 255, 0.02)'; // Ghost links
        return 'rgba(255, 255, 255, 0.2)';
      })
      .onNodeClick(node => {
        // Set selected node for the UI panel
        selectedNode.value = node;
        
        // Aim at node from outside it
        const distance = 40;
        const distRatio = 1 + distance/Math.hypot((node as any).x, (node as any).y, (node as any).z);
        graph.cameraPosition(
          { x: (node as any).x * distRatio, y: (node as any).y * distRatio, z: (node as any).z * distRatio }, // new position
          node, // lookAt ({ x, y, z })
          3000  // ms transition duration
        );
      });
      
      // 🌌 1. ADD BLOOM EFFECTS (NEON GLOW)
      const bloomPass = new UnrealBloomPass(
        new THREE.Vector2(window.innerWidth, window.innerHeight),
        2.5,  // strength
        0.5,  // radius
        0.1   // threshold
      );
      graph.postProcessingComposer().addPass(bloomPass);

      // 🌌 2. BLACK HOLE GRAVITY LOGIC
      // Pull all nodes gently towards the center [0,0,0], but let them repel each other strongly
      graph.d3Force('charge').strength(-200); // Stronger repulsion so they don't clump
      graph.d3Force('center', null); // Remove default center force
      // Custom gravity well pulling to center
      import('d3').then(d3 => {
        graph.d3Force('gravity', d3.forceRadial(10, 0, 0, 0).strength(0.05));
      }).catch(e => console.warn('d3 optional import failed for gravity'));
    } catch (e) {
      console.error("Failed to initialize 3D graph:", e);
    }

    await fetchData()
    interval = setInterval(fetchData, 2000) // Poll every 2s
  }
})

onUnmounted(() => {
  if (interval) clearInterval(interval)
  if (graph) {
    // Cleanup if necessary
    graph._destructor && graph._destructor()
  }
})

// Search filter handler to force re-evaluation of node colors
function applySearch() {
  if (graph) {
    // This forces the graph to re-evaluate colors based on the new searchQuery
    graph.nodeColor(graph.nodeColor());
    graph.linkColor(graph.linkColor());
    graph.linkWidth(graph.linkWidth());
  }
}

async function fetchData() {
  try {
    const url = API_BASE ? `${API_BASE}/lgnn/graph` : '/api/lgnn/graph'
    debugInfo.value = `Fetching: ${url}`
    const res = await fetch(url)
    if (!res.ok) {
      errorMessage.value = `HTTP ${res.status}: ${res.statusText}`
      return
    }
    const data = await res.json()
    debugInfo.value = `Got ${data?.nodes?.length || 0} nodes from backend.`
    
    if (!data || !data.nodes) {
      errorMessage.value = "data.nodes is undefined"
      return
    }
      // Prevent layout resets: only update if the number of nodes or links has actually changed!
    if (graph) {
      const currentData = graph.graphData();
      const currentNodesCount = currentData.nodes.length;
      const currentLinksCount = currentData.links.length;
      
      if (data.nodes.length !== currentNodesCount || data.links.length !== currentLinksCount) {
        // Map to 3D Force Graph format
        const nodes = data.nodes.map((n: any) => {
          // Preserve existing coordinates to prevent violent jumping
          const existingNode = currentData.nodes.find((cn: any) => cn.id === n.id);
          return {
            ...n,
            id: n.id,
            name: n.label,
            val: n.confidence || 1,
            text_content: n.text_content,
            node_type: n.node_type,
            entropy: n.entropy,
            isManual: n.isManual,
            ...(existingNode ? { x: existingNode.x, y: existingNode.y, z: existingNode.z, vx: existingNode.vx, vy: existingNode.vy, vz: existingNode.vz } : {})
          };
        });
        
        const links = data.links.map((e: any) => ({
          source: e.source,
          target: e.target,
          weight: e.weight
        }));
        
        graphData.value = { nodes, links };
        graph.graphData({ nodes, links });
      }
    } else {
        // Initial load
        const nodes = data.nodes.map((n: any) => ({ ...n, id: n.id, name: n.label, val: n.confidence || 1 }));
        const links = data.links.map((e: any) => ({ source: e.source, target: e.target, weight: e.weight }));
        graphData.value = { nodes, links };
    }
    
    errorMessage.value = ''
  } catch (e: any) {
    console.error("Failed fetching 3D graph data", e)
    errorMessage.value = e.message || String(e)
  }
}
</script>

<style scoped>
.macro-vision-container {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: transparent;
  z-index: 5;
  display: flex;
  flex-direction: column;
}

.overlay-header {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  z-index: 10000;
  pointer-events: none;
}

.glitch {
  font-size: 24px;
  font-weight: 900;
  color: #F4F4F0;
  text-transform: uppercase;
  letter-spacing: 2px;
  margin: 0;
  text-shadow: 2px 2px 0 #E03C31, -2px -2px 0 #005096;
}

.brutal-btn {
  pointer-events: auto;
  background: #E03C31;
  color: #FFF;
  border: 2px solid #FFF;
  padding: 8px 16px;
  font-family: 'Space Mono', monospace;
  font-weight: bold;
  font-size: 14px;
  cursor: pointer;
  box-shadow: 4px 4px 0 #FFF;
  transition: transform 0.1s;
}

.brutal-btn:active {
  transform: translate(4px, 4px);
  box-shadow: 0 0 0 #FFF;
}

.search-box {
  pointer-events: auto;
  margin: 0 20px;
  flex-grow: 1;
  max-width: 400px;
}

.brutal-input {
  width: 100%;
  background: rgba(0, 0, 0, 0.6);
  border: 2px solid #005096;
  color: #00FF41;
  padding: 8px 16px;
  font-family: 'Space Mono', monospace;
  font-size: 14px;
  outline: none;
  box-shadow: 4px 4px 0 #005096;
}

.brutal-input:focus {
  border-color: #00FF41;
  box-shadow: 4px 4px 0 #00FF41;
}

.brutal-input::placeholder {
  color: rgba(0, 255, 65, 0.5);
}

.hud {
  position: absolute;
  bottom: 20px;
  left: 20px;
  z-index: 10000;
  color: #00FF41;
  font-family: 'Space Mono', monospace;
  font-size: 12px;
  pointer-events: none;
  background: rgba(0, 0, 0, 0.8);
  padding: 10px;
  border: 1px solid #00FF41;
}

.hud-stat {
  margin-bottom: 4px;
}

/* NODE PANEL CSS */
.node-panel {
  position: absolute;
  top: 80px;
  right: 20px;
  width: 500px;
  background: rgba(10, 10, 10, 0.85);
  border: 1px solid #005096;
  border-left: 4px solid #E03C31;
  color: #F4F4F0;
  font-family: 'Space Mono', monospace;
  z-index: 10000;
  box-shadow: 0 10px 30px rgba(0,0,0,0.8);
  backdrop-filter: blur(5px);
  display: flex;
  flex-direction: column;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: rgba(0, 80, 150, 0.3);
  padding: 10px 15px;
  border-bottom: 1px solid #005096;
}

.panel-title {
  font-weight: bold;
  color: #00FF41;
  letter-spacing: 1px;
}

.panel-body {
  padding: 15px;
  font-size: 13px;
}

.data-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  border-bottom: 1px dotted #333;
  padding-bottom: 4px;
}

.data-row strong {
  color: #888;
}

.node-content-box {
  margin-top: 15px;
  background: rgba(0,0,0,0.5);
  border: 1px solid #333;
  padding: 10px;
}

.content-label {
  font-size: 10px;
  color: #F2C12E;
  margin-bottom: 5px;
  text-transform: uppercase;
}

.content-text {
  line-height: 1.5;
  color: #FFF;
  word-wrap: break-word;
}

.blink {
  animation: blink 1s step-end infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

.graph-3d-wrapper {
  flex: 1;
  width: 100%;
  height: 100%;
  overflow: hidden;
  position: relative;
}
</style>
