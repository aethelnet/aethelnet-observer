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
    </div>
    
    <div class="hud">
      <div class="hud-stat">NODES: {{ graphData.nodes.length }}</div>
      <div class="hud-stat">LINKS: {{ graphData.links.length }}</div>
      <div class="hud-stat blink">LIVE DATA STREAM</div>
      <div v-if="errorMessage" style="color: #E03C31; margin-top: 10px;">ERR: {{ errorMessage }}</div>
      <div v-if="debugInfo" style="color: #F2C12E; margin-top: 10px;">DBG: {{ debugInfo }}</div>
      <div class="hud-stat blink" style="cursor: pointer; pointer-events: auto; margin-top: 15px; color: #00FF41; border: 1px solid #00FF41; padding: 5px;" @click="injectTestNodes">[ INJECT DECODER TEST ]</div>
      <div class="hud-stat blink" style="cursor: pointer; pointer-events: auto; margin-top: 10px; color: #F2C12E; border: 1px solid #F2C12E; padding: 5px;" @click="toggleMode">[ TOGGLE MATRIX (PCA) ]</div>
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
          <div class="content-text">{{ selectedNode.content || selectedNode.text_content || selectedNode.name || 'No semantic data available.' }}</div>
        </div>
        <div style="margin-top: 15px; display: flex; gap: 10px;">
          <button class="brutal-btn" @click="quarantineSelected" v-if="selectedNode.node_type !== 'quarantined'">[ QUARANTINE ]</button>
          <button class="brutal-btn" @click="nukeSelected">[ NUKE ]</button>
        </div>
        
        <div style="margin-top: 20px; border-top: 2px solid #111; padding-top: 20px;">
          <DeepDecoderView :inputs="{ 'focus': { node: selectedNode, value: selectedNode.text_content || selectedNode.name } }" style="height: 400px;" />
        </div>
      </div>
    </div>

    <div ref="graphContainer" class="graph-3d-wrapper"></div>
    
    <!-- THE DIARY -->
    <TomRiddleDiary @node-spawned="fetchData" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import ForceGraph3D from '3d-force-graph'
import { UnrealBloomPass } from 'three/examples/jsm/postprocessing/UnrealBloomPass.js'
import * as THREE from 'three'
import SpriteText from 'three-spritetext'
import { API_BASE } from '../shared/api.js'
import TomRiddleDiary from './TomRiddleDiary.vue'
import DeepDecoderView from './DeepDecoderView.vue'

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
      .enableNodeDrag(true)
      .linkDirectionalParticles(2)
      .linkDirectionalParticleWidth(1.5)
      .linkDirectionalParticleSpeed((d: any) => (d as any).weight * 0.01)
      .nodeVal((n: any) => {
        const node = n as any;
        if (node.node_type === 'GitRepo') return 20;
        if (node.node_type === 'GitFile') return 2;
        return (node.confidence || 0.5) * 5;
      })
      .nodeColor((n: any) => {
        const node = n as any;
        const q = searchQuery.value.toLowerCase();
        
        // Is it part of the search focus?
        let isFocused = true;
        if (q) {
          const textMatch = (node.name || '').toLowerCase().includes(q) || (node.text_content || '').toLowerCase().includes(q);
          isFocused = textMatch;
        }

        if (!isFocused) return 'rgba(17, 17, 17, 0.1)'; // Ghosted out
        
        if (node.node_type === 'pca_node') {
          // Color based on height (z) to give it a 3D matrix depth effect
          const zNorm = Math.min(1, Math.max(0, (node.fz + 100) / 200)); 
          // From Dark Blue to Neon Cyan to Matrix Green
          return zNorm > 0.6 ? '#00FF41' : (zNorm > 0.3 ? '#00FFFF' : '#0B3B60');
        }
        
        if (node.node_type === 'quarantined') return '#FF3366'; // Dead Zone (Red)
        if (node.node_type === 'macro') return '#F2C12E'; // Operator/Prism
        if (node.node_type === 'GitRepo') return '#111111'; // Magenta giant star
        if (node.node_type === 'GitFile') return '#555555'; // BlueViolet for files
        if (node.node_type === 'zk_proof_verified') return '#32D74B'; // Guardian Shield
        if (node.node_type === 'bounty_node') return '#F2C12E'; // Yellow Target
        if (node.node_type === 'hunter_spider') return '#FF4500'; // Orange Hunter
        if (node.isManual) return '#005096'; // Seed
        return '#00FF41'; // Spider (vibrant green)
      })
      .nodeThreeObjectExtend(true)
      .nodeThreeObject((n: any) => {
        const node = n as any;
        const q = searchQuery.value.toLowerCase();
        
        let isFocused = false;
        if (q) {
          isFocused = (node.name || '').toLowerCase().includes(q) || (node.text_content || '').toLowerCase().includes(q);
        }
        const shouldShowLabel = isFocused || node.node_type === 'GitRepo' || node.node_type === 'macro' || node.isManual;
        let sprite = null;
        if (shouldShowLabel) {
          sprite = new SpriteText(node.name || node.id);
          sprite.color = '#111111';
          sprite.textHeight = node.node_type === 'GitRepo' ? 12 : 4;
          sprite.backgroundColor = 'rgba(255, 255, 255, 0.9)';
          sprite.padding = 2;
          sprite.borderRadius = 0;
          sprite.position.y = node.node_type === 'GitRepo' ? 30 : 10;
        }

        let mesh = null;

        // PCA Node (Matrix Glow)
        if (node.node_type === 'pca_node') {
            const geometry = new THREE.IcosahedronGeometry(Math.random() * 2 + 2, 0);
            const zNorm = Math.min(1, Math.max(0, (node.fz + 100) / 200)); 
            const colorHex = zNorm > 0.6 ? 0x00FF41 : (zNorm > 0.3 ? 0x00FFFF : 0x0B3B60);
            const material = new THREE.MeshBasicMaterial({ color: colorHex, wireframe: true, transparent: true, opacity: 0.9 });
            mesh = new THREE.Mesh(geometry, material);
            node.__pcaMesh = mesh;
        }
        // Bounty Target Geometry
        else if (node.node_type === 'bounty_node') {
            const geometry = new THREE.TorusGeometry(5, 1, 16, 100);
            const material = new THREE.MeshBasicMaterial({ color: 0xF2C12E, wireframe: true, transparent: true, opacity: 0.9 });
            mesh = new THREE.Mesh(geometry, material);
            
            const s = new SpriteText("BOUNTY_TARGET");
            s.color = '#F2C12E'; s.textHeight = 4; s.position.y = 10;
            mesh.add(s);
            node.__bountyMesh = mesh;
        }
        // Hunter Spider Geometry
        else if (node.node_type === 'hunter_spider') {
            const geometry = new THREE.TetrahedronGeometry(4, 0); // Sharp pointy pyramid
            const material = new THREE.MeshBasicMaterial({ color: 0xFF4500, wireframe: true, transparent: true, opacity: 0.9 });
            mesh = new THREE.Mesh(geometry, material);
            
            const s = new SpriteText("HUNTER_SPIDER");
            s.color = '#FF4500'; s.textHeight = 3; s.position.y = 8;
            mesh.add(s);
            node.__hunterMesh = mesh;
        }
        // Spider Glitch Geometry
        else if (node.source_tag && String(node.source_tag).includes('Spider')) {
            const geometry = new THREE.IcosahedronGeometry(Math.random() * 2 + 3, 0); // Spiky
            const material = new THREE.MeshBasicMaterial({ color: 0x00ffff, wireframe: true, transparent: true, opacity: 0.8 });
            mesh = new THREE.Mesh(geometry, material);
            
            const labelStr = String(node.source_tag).replace('_Spider', '').toUpperCase();
            const s = new SpriteText("SPIDER_" + labelStr);
            s.color = '#00ffff'; s.textHeight = 3; s.position.y = 8;
            mesh.add(s);
            node.__spiderMesh = mesh; // Store reference for animation
        }
        // Guardian Shield Geometry
        else if (node.node_type === 'zk_proof_verified') {
            const geometry = new THREE.OctahedronGeometry(Math.random() * 1.5 + 4, 0);
            const material = new THREE.MeshBasicMaterial({ color: 0x32D74B, wireframe: true, transparent: true, opacity: 0.9 });
            mesh = new THREE.Mesh(geometry, material);
            
            const s = new SpriteText("GUARDIAN_NODE");
            s.color = '#32D74B'; s.textHeight = 4; s.position.y = 10;
            mesh.add(s);
            node.__guardianMesh = mesh;
        }
        // Quarantined Dead Zone
        else if (node.node_type === 'quarantined') {
            const geometry = new THREE.BoxGeometry(4, 4, 4);
            const material = new THREE.MeshBasicMaterial({ color: 0xE03C31, wireframe: false, transparent: true, opacity: 0.5 });
            mesh = new THREE.Mesh(geometry, material);
            
            const s = new SpriteText("QUARANTINED");
            s.color = '#E03C31'; s.textHeight = 3; s.position.y = 8;
            mesh.add(s);
        }
        // Axiom Anchor (Shielded from Liquid Mutations)
        else if (node.is_shielded) {
            const geometry = new THREE.DodecahedronGeometry(6, 0);
            const material = new THREE.MeshBasicMaterial({ color: 0xFFFFFF, wireframe: true, transparent: true, opacity: 0.9 });
            mesh = new THREE.Mesh(geometry, material);
            
            const s = new SpriteText("AXIOM ANCHOR");
            s.color = '#FFFFFF'; s.textHeight = 4; s.position.y = 10;
            mesh.add(s);
            node.__axiomMesh = mesh;
        }
        // Default Nodes (Matrix Style Wireframe Spheres)
        else {
            const size = (node.confidence || 0.5) * 5;
            const geometry = new THREE.IcosahedronGeometry(size, 1);
            let colorHex = 0x00FF41; // Default green
            if (node.node_type === 'macro') colorHex = 0xF2C12E;
            if (node.isManual) colorHex = 0x005096;
            const material = new THREE.MeshBasicMaterial({ color: colorHex, wireframe: true, transparent: true, opacity: 0.6 });
            mesh = new THREE.Mesh(geometry, material);
            node.__defaultMesh = mesh;
        }

        if (sprite) {
            mesh.add(sprite);
        }
        return mesh;
      })
      .nodeRelSize(4)
      .linkWidth((d: any) => {
        const q = searchQuery.value.toLowerCase();
        if (q) return 0.5; // Dim all links when searching
        return (d as any).weight * 1.5;
      })
      .linkColor((link: any) => {
        const q = searchQuery.value.toLowerCase();
        if (q) return 'rgba(17, 17, 17, 0.05)'; // Ghost links
        
        // Sever links from/to quarantined nodes
        if (link.source.node_type === 'quarantined' || link.target.node_type === 'quarantined') {
           return 'rgba(255, 51, 102, 0.3)'; // Severed toxic links (faint red)
        }
        
        if (link.source.node_type === 'pca_node' || link.target.node_type === 'pca_node' || (link.source.id && link.source.id.startsWith('neuron_'))) {
           return 'rgba(0, 255, 65, 0.2)'; // Matrix Green links
        }
        
        return 'rgba(17, 17, 17, 0.2)'; // Dark links
      })
      .onNodeClick((node: any) => {
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
      
      // 🌌 1. RESTORED BLOOM EFFECTS FOR MATRIX CYBERPUNK FEEL
      const bloomPass = new UnrealBloomPass(new THREE.Vector2(window.innerWidth, window.innerHeight), 1.5, 0.4, 0.85);
      bloomPass.threshold = 0.1;
      bloomPass.strength = 1.2;
      bloomPass.radius = 0.5;
      graph.postProcessingComposer().addPass(bloomPass);

      // 🌌 2. BLACK HOLE GRAVITY LOGIC
      // Pull all nodes gently towards the center [0,0,0], but let them repel each other strongly
      graph.d3Force('charge').strength(-200); // Stronger repulsion so they don't clump
      graph.d3Force('center', null); // Remove default center force
      // Custom gravity well pulling to center
      import('d3').then((d3: any) => {
        graph.d3Force('gravity', d3.forceRadial(10, 0, 0).strength(0.05));
      }).catch(() => console.warn('d3 optional import failed for gravity'));
    } catch (e) {
      console.error("Failed to initialize 3D graph:", e);
    }

    await fetchData()
    let interval = setInterval(fetchData, 2000) // Poll every 2s

    // Create the global function to allow manual injection
    window._injectDecoderTest = () => {
      const b64Node = { id: 'TEST_B64', label: 'Base64 Intel', node_type: 'intel', confidence: 0.99, value: 'QWV0aGVsbmV0IEludGVsOiBDb21wcm9taXNlZA==' };
      const walletNode = { id: 'TEST_WALLET', label: 'Treasury Wallet', node_type: 'wallet', confidence: 1.0, value: '0x1234567890123456789012345678901234567890' };
      const jwtNode = { id: 'TEST_JWT', label: 'Auth Token', node_type: 'token', confidence: 0.85, value: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1bml0LTczNCIsIm5hbWUiOiJBdXJhdGljIFByaW1lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c' };
      
      const currentNodes = graph.graphData().nodes;
      graph.graphData({
        nodes: [...currentNodes, b64Node, walletNode, jwtNode],
        links: graph.graphData().links
      });
      // also push to localNodes so that it persists the next 2s before poll?
      // actually, just stop polling temporarily so they don't disappear
      clearInterval(interval);
      console.log("Injected test nodes and paused polling.");
    };

    // Animation Loop (Glitch Effect & Shield Pulse)
    const animateMeshes = () => {
      if (graph) {
         const { nodes } = graph.graphData();
         nodes.forEach((n: any) => {
            if (n.__spiderMesh) {
                // Wild glitch rotation
                n.__spiderMesh.rotation.x += Math.random() * 0.2;
                n.__spiderMesh.rotation.y += Math.random() * 0.2;
                
                // Pulsate scale
                const scale = 1 + Math.sin(Date.now() * 0.02) * 0.3 + (Math.random() * 0.2);
                n.__spiderMesh.scale.set(scale, scale, scale);
                
                // Glitch color intensity flash
                if (Math.random() > 0.95) {
                   n.__spiderMesh.material.color.setHex(0xff00ff); // Magenta flash
                } else if (Math.random() > 0.9) {
                   n.__spiderMesh.material.color.setHex(0xffffff); // White flash
                } else {
                   n.__spiderMesh.material.color.setHex(0x00ffff); // Cyan default
                }
            }
            
            if (n.__guardianMesh) {
                n.__guardianMesh.rotation.y += 0.02;
                const scale = 1 + Math.sin(Date.now() * 0.005) * 0.05;
                n.__guardianMesh.scale.set(scale, scale, scale);
            }
            
            if (n.__bountyMesh) {
                n.__bountyMesh.rotation.z += 0.05;
                const scale = 1 + Math.sin(Date.now() * 0.005) * 0.2;
                n.__bountyMesh.scale.set(scale, scale, scale);
            }
            
            if (n.__hunterMesh) {
                n.__hunterMesh.rotation.x += 0.3;
                n.__hunterMesh.rotation.y += 0.3;
            }

            if (n.__pcaMesh) {
                n.__pcaMesh.rotation.x += 0.01;
                n.__pcaMesh.rotation.y += 0.02;
            }

            if (n.__defaultMesh) {
                n.__defaultMesh.rotation.x += 0.005;
                n.__defaultMesh.rotation.y += 0.01;
            }
         });
      }
      requestAnimationFrame(animateMeshes);
    };
    animateMeshes();
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
    graph.nodeColor(graph.nodeColor());
    graph.linkColor(graph.linkColor());
    graph.linkWidth(graph.linkWidth());
  }
}

function triggerFocus(nodeId: string) {
  // implemented via watcher
}

function injectTestNodes() {
  if (window._injectDecoderTest) {
    window._injectDecoderTest();
  }
}

function quarantineSelected() {
  if (selectedNode.value && graph) {
    const id = selectedNode.value.id;
    selectedNode.value.node_type = 'quarantined';
    selectedNode.value.entropy = 1.0;
    
    // Update data locally to bypass full fetch override immediately
    const data = graph.graphData();
    const node = data.nodes.find((n: any) => n.id === id);
    if (node) {
      node.node_type = 'quarantined';
      node.entropy = 1.0;
    }
    
    // Force re-render
    graph.nodeColor(graph.nodeColor());
    graph.linkColor(graph.linkColor());
    
    // Call API
    const url = API_BASE ? `${API_BASE}/lgnn/node/${id}/quarantine` : `/api/lgnn/node/${id}/quarantine`;
    fetch(url, { method: 'POST' }).catch(console.error);
  }
}

function nukeSelected() {
  if (selectedNode.value && graph) {
    const id = selectedNode.value.id;
    const data = graph.graphData();
    const newNodes = data.nodes.filter((n: any) => n.id !== id);
    const newLinks = data.links.filter((l: any) => l.source.id !== id && l.target.id !== id);
    graph.graphData({ nodes: newNodes, links: newLinks });
    graphData.value = { nodes: newNodes, links: newLinks };
    selectedNode.value = null;
    
    // Call API
    const url = API_BASE ? `${API_BASE}/lgnn/node/${id}` : `/api/lgnn/node/${id}`;
    fetch(url, { method: 'DELETE' }).catch(console.error);
  }
}

const mode = ref('graph') // 'graph' or 'pca'

function toggleMode() {
    mode.value = mode.value === 'graph' ? 'pca' : 'graph'
    if (mode.value === 'pca' && graph) {
        // Clear links for pure point cloud
        graph.graphData({ nodes: [], links: [] })
    }
    fetchData()
}

async function fetchData() {
  try {
    const url = API_BASE ? (mode.value === 'pca' ? `${API_BASE}/lgnn/pca` : `${API_BASE}/lgnn/graph`) : (mode.value === 'pca' ? '/api/lgnn/pca' : '/api/lgnn/graph')
    debugInfo.value = `Fetching: ${url}`
    const res = await fetch(url)
    if (!res.ok) {
      errorMessage.value = `HTTP ${res.status}: ${res.statusText}`
      return
    }
    const data = await res.json()
    
    if (mode.value === 'pca') {
        const points = data.points || []
        const featureNames = ["Volatility Core", "Momentum Oscillator", "Liquidity Gravity", "Orderbook Imbalance", "Whale Tracker", "Retail Sentiment", "Mean Reversion", "Trend Following", "Statistical Arbitrage", "Fractal Dimension", "Alpha Decay", "Gamma Squeeze", "Delta Hedging"];
        const assets = ["BTC", "ETH", "SOL", "SUI", "INJ", "LINK", "CRV"];
        
        const pcaNodes = points.map((p: any, index: number) => {
            const feature = featureNames[index % featureNames.length];
            const asset = assets[(index * 3) % assets.length];
            return {
                id: p.id,
                name: `${feature} [${asset}]`,
                label: `${feature} [${asset}]`,
                node_type: 'pca_node',
                text_content: `Latent dimension mapping: ${feature.toLowerCase()} for ${asset} pairings.\n\nNeural Activation: ${(Math.random() * 100).toFixed(2)}%\nTopological Resonance: ${(Math.random()).toFixed(4)}`,
                fx: p.x * 100,
                fy: p.y * 100,
                fz: p.z * 100,
                val: 1.0
            }
        });
        
        // Generate faint links between closest nodes to create a neural web effect
        const pcaLinks = [];
        for (let i = 0; i < pcaNodes.length; i++) {
            let closest = -1;
            let minDist = Infinity;
            for (let j = 0; j < pcaNodes.length; j++) {
                if (i === j) continue;
                const dx = pcaNodes[i].fx - pcaNodes[j].fx;
                const dy = pcaNodes[i].fy - pcaNodes[j].fy;
                const dz = pcaNodes[i].fz - pcaNodes[j].fz;
                const dist = Math.sqrt(dx*dx + dy*dy + dz*dz);
                if (dist < minDist) {
                    minDist = dist;
                    closest = j;
                }
                // Connect if reasonably close to form clusters
                if (dist < 40 && Math.random() > 0.8) {
                    pcaLinks.push({
                        source: pcaNodes[i].id,
                        target: pcaNodes[j].id,
                        weight: 0.2
                    });
                }
            }
            // Always connect to closest neighbor to prevent isolated islands
            if (closest !== -1) {
                pcaLinks.push({
                    source: pcaNodes[i].id,
                    target: pcaNodes[closest].id,
                    weight: 0.5
                });
            }
        }

        graphData.value = { nodes: pcaNodes, links: pcaLinks }
        if (graph) graph.graphData(graphData.value)
        debugInfo.value = `Rendered ${pcaNodes.length} PCA points (The Matrix).`
        return
    }
    
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
            val: n.size || n.confidence || 10,
            text_content: n.text_content,
            content: n.content,
            value: n.content || n.text_content || n.value,
            node_type: n.node_type || 'default',
            entropy: n.entropy || Math.random(),
            isManual: n.isManual || false,
            source_tag: n.source_tag || 'server',
            tensor: n.tensor || n.embedding || null,
            color: n.color,
            ...(existingNode ? { x: existingNode.x, y: existingNode.y, z: existingNode.z, vx: existingNode.vx, vy: existingNode.vx, vz: existingNode.vz } : {})
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
  color: #111111;
  text-transform: uppercase;
  letter-spacing: 2px;
  margin: 0;
  text-shadow: 2px 2px 0 #FF3366;
}

.brutal-btn {
  pointer-events: auto;
  background: #FFFFFF;
  color: #111111;
  border: 2px solid #111111;
  padding: 8px 16px;
  font-family: 'JetBrains Mono', monospace;
  font-weight: bold;
  font-size: 14px;
  cursor: pointer;
  box-shadow: 4px 4px 0 #111111;
  transition: transform 0.1s;
}

.brutal-btn:active {
  transform: translate(4px, 4px);
  box-shadow: 0 0 0 #111111;
}

.search-box {
  pointer-events: auto;
  margin: 0 20px;
  flex-grow: 1;
  max-width: 400px;
}

.brutal-input {
  width: 100%;
  background: #FFFFFF;
  border: 2px solid #111111;
  color: #111111;
  padding: 8px 16px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 14px;
  outline: none;
  box-shadow: 4px 4px 0 #111111;
}

.brutal-input:focus {
  border-color: #FF3366;
  box-shadow: 4px 4px 0 #FF3366;
}

.brutal-input::placeholder {
  color: rgba(17, 17, 17, 0.4);
}

.hud {
  position: absolute;
  bottom: 20px;
  left: 20px;
  z-index: 10000;
  color: #111111;
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  pointer-events: none;
  background: #FFFFFF;
  padding: 10px;
  border: 2px solid #111111;
  box-shadow: 4px 4px 0 #111111;
}

.hud-stat {
  margin-bottom: 4px;
  font-weight: bold;
}

/* NODE PANEL CSS - WHITE BRUTALISM */
.node-panel {
  position: absolute;
  top: 80px;
  right: 20px;
  width: 500px;
  background: #FFFFFF;
  border: 4px solid #111111;
  color: #111111;
  font-family: 'JetBrains Mono', monospace;
  z-index: 10000;
  box-shadow: 8px 8px 0 rgba(17, 17, 17, 0.2);
  display: flex;
  flex-direction: column;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #F8F8F8;
  padding: 10px 15px;
  border-bottom: 4px solid #111111;
}

.panel-title {
  font-weight: 800;
  color: #111111;
  letter-spacing: 1px;
}

.icon-btn {
  background: none;
  border: none;
  font-family: 'JetBrains Mono', monospace;
  font-weight: bold;
  cursor: pointer;
  color: #111111;
}

.panel-body {
  padding: 15px;
  font-size: 13px;
}

.data-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  border-bottom: 2px dotted #111111;
  padding-bottom: 4px;
}

.data-row strong {
  color: #111111;
  font-weight: 800;
}

.node-content-box {
  margin-top: 15px;
  background: #F8F8F8;
  border: 2px solid #111111;
  padding: 10px;
}

.content-label {
  font-size: 10px;
  color: #FF3366;
  font-weight: bold;
  margin-bottom: 5px;
  text-transform: uppercase;
}

.content-text {
  line-height: 1.5;
  color: #111111;
  word-wrap: break-word;
  max-height: 400px;
  overflow-y: auto;
  white-space: pre-wrap;
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
