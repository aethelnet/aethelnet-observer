<template>
  <div class="lgnn-container-white light-theme" :class="{'dream-mode-active': isDreaming}" @wheel.stop @mousedown.stop="onBackgroundMouseDown" @touchstart.stop="onBackgroundMouseDown" @mousemove="onMouseMove" @mouseup="onMouseUp" @touchmove="onMouseMove" @touchend="onMouseUp">
    <div id="a11y-announcer" class="sr-only" aria-live="polite"></div>
    
    <LgnnTopNav 
      :identity-nodes="nodes.filter(n => n.source_tag === 'identity' || n.id.startsWith('identity_'))"
      :global-active-persona-id="globalActivePersonaId"
      :show-autonomous="showAutonomous"
      :min-confidence="minConfidence"
      :is-grid-mode="isGridMode"
      :show-help-overlay="false"
      @update:showAutonomous="showAutonomous = $event"
      @update:minConfidence="minConfidence = $event"
      @recenter="recenterCanvas"
      @add-mask="spawnNewMask"
      @edit-mask="editMask"
      @remove-mask="removeMask"
      @toggle-grid="toggleGridMode"
      @toggle-assets="showToolbox = !showToolbox"
      @toggle-spiders="spawnApp('Spider')"
      @toggle-eco="toggleEcoMode"
      :is-eco-mode="isEcoMode"
    />

    <LgnnToolbox 
      v-if="showToolbox"
      :custom-blueprints="customBlueprints"
      :sorted-manual-nodes="sortedManualNodes"
      :mic-active="micActive"
      :gyro-active="gyroActive"
      :gps-active="gpsActive"
      @spawn-app="spawnApp"
      @spawn-custom="spawnCustom"
      @delete-blueprint="deleteCustomBlueprint"
      @focus-node="focusNode"
      @toggle-sensor="toggleSensor"
      @toggle-forge="showForgeWorkbench = true"
      @toggle-diary="showDiary = !showDiary"
      @toggle-logs="systemLogsRef?.toggleOpen()"
      @close="showToolbox = false"
    />

    <GalaxyView 
      v-if="isGalaxyMode"
      :nodes="nodes" 
      :links="links" 
      :transform="globalTransform" 
      :is-galaxy-mode="isGalaxyMode"
      @node-click="selectNode"
    />

    <div 
      class="canvas-area" 
      ref="canvasContainer"
      role="application"
      tabindex="0"
      aria-label="Synaptic Node Network Visualization. Use arrow keys to navigate nodes, Enter to expand."
      @dragover.prevent
      @drop.prevent="onDropCanvas"
      :style="{ transform: `translate(${parallaxX}px, ${parallaxY}px)` }"
    >
      <canvas ref="webglCanvas" class="webgl-background-canvas"></canvas>
      
      <!-- WebGL Particle Tooltip -->
      <div v-if="hoveredParticle" class="webgl-tooltip" :style="{ left: hoveredParticlePos.x + 15 + 'px', top: hoveredParticlePos.y + 15 + 'px' }">
        <div class="tooltip-title">{{ hoveredParticle.label || hoveredParticle.id }}</div>
        <div class="tooltip-type">Type: {{ hoveredParticle.source_tag || hoveredParticle.node_type }}</div>
        <div class="tooltip-content" v-if="hoveredParticle.content">{{ hoveredParticle.content.substring(0, 60) }}...</div>
        <div class="tooltip-hint">Click to pluck</div>
      </div>
      
      <!-- Subgraph Breadcrumbs -->
      <div v-if="currentParentId" style="position: absolute; bottom: 24px; left: 50%; transform: translateX(-50%); z-index: 2000; font-family: var(--font-family-mono); font-size: 14px; background: var(--color-bg-panel); padding: 8px 16px; border: 1px solid var(--border-color); color: var(--color-text-main); border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.5);">
        <span @click="leaveSubgraph" style="cursor: pointer; color: var(--color-accent); font-weight: bold;">[ <-- BACK ]</span>
        <span style="margin-left: 8px;">Inside Subgraph: {{ currentParentId }}</span>
      </div>
      
      <!-- Persistent Canvas Navigation Controls -->
      <div class="canvas-nav-controls">
        <button class="nav-btn" @click.stop="zoomIn" title="Zoom In">＋</button>
        <button class="nav-btn" @click.stop="recenterCanvas" title="Reset View">◎</button>
        <button class="nav-btn" @click.stop="zoomOut" title="Zoom Out">－</button>
      </div>
      
      <!-- When Space is held, we add an invisible overlay to intercept all pointer events and allow panning anywhere -->
      <div v-if="isSpacePressed" class="space-pan-overlay"></div>
      
      <SynapticLinks
        :projected-links="projectedLinks"
        :fast-link-source="fastLinkSource"
        :fast-link-current="fastLinkCurrent"
        :show-autonomous="showAutonomous"
        :show3D="false"
        :min-confidence="minConfidence"
        @delete-link="deleteLink"
        @open-edge-editor="edge => activeEdge = edge"
      />

      <div
        v-for="node in domNodes"
        v-show="true"
        :key="node.id"
        class="concept-node"
        :data-node-id="node.id"
        :class="{ 
          'is-dragged': node.isDragged, 
          'is-selected': node.isSelected,
          'autonomous-node': !node.isManual,
          'is-expanded': node.isExpanded
        }"
        :style="{
          zIndex: Math.floor(1000 + (node.z || 0)),
          pointerEvents: isSpacePressed ? 'none' : 'auto'
        }"
        @mousedown.stop="startDrag($event, node)"
        @touchstart.stop="startDrag($event, node)"
        @dblclick.stop="activeConsoleNode = node"
      >
        <Transition name="node-expand" mode="out-in">
          <template v-if="node.isExpanded">
            <component 
              :is="resolveNodeComponent(node)" 
              :node="node" 
              :globalNodes="nodes"
              :globalLinks="links"
              @update="updateNodeAndConsole"
              @spawn-link="startFastLink($event, node)"
              @unpin="unpinNode(node)"
              @edit="startEdit(node)"
              @toggle-expand="toggleExpand(node)"
              @execute="executeMacro(node)"
              @save-edit="saveEdit(node)"
              @delete="deleteNode(node)"
              @enter="enterSubgraph(node)"
              @refresh="fetchGraphData"
            />
          </template>
          <template v-else>
            <div class="node-content fast-mode">
              <div class="node-label">{{ node.label || (node.id ? node.id.substring(0,8) : 'Unknown') }}</div>
              <div class="node-text">{{ (node.content || node.text_content || '').substring(0, 60) }}...</div>
              <div class="metrics-bar">
                <span class="metric">TAG: {{ node.source_tag }}</span>
              </div>
              <div class="fast-actions">
                <button @click.stop="toggleExpand(node)" class="expand-btn">EXPAND</button>
              </div>
            </div>
          </template>
        </Transition>
      </div>

      <!-- Node Console Overlay -->
      <NodeConsoleOverlay 
        v-if="activeConsoleNode" 
        :node="activeConsoleNode" 
        :allNodes="nodes"
        @close="activeConsoleNode = null" 
        @update-node="updateNodeAndConsole" 
      />
      
      <!-- Box Selection Overlay -->
      <div 
        v-if="isBoxSelecting"
        class="selection-box-overlay"
        :style="{
          left: Math.min(boxStart.x, boxCurrent.x) + 'px',
          top: Math.min(boxStart.y, boxCurrent.y) + 'px',
          width: Math.abs(boxCurrent.x - boxStart.x) + 'px',
          height: Math.abs(boxCurrent.y - boxStart.y) + 'px'
        }"
      ></div>

      <!-- Merge & Evolve Button -->
      <!-- Multi Node Selection -->
      <div 
        v-if="selectedNodes.length > 1"
        class="floating-action-bar"
        style="position: absolute; bottom: 80px; left: 50%; transform: translateX(-50%); z-index: 2000; display: flex; gap: 8px; background: var(--color-bg-panel); padding: 8px 16px; border: 1px solid var(--border-color); border-radius: 20px; box-shadow: var(--shadow-glass);"
      >
        <span style="color: var(--color-text-muted); font-size: 12px; align-self: center; font-weight: bold; margin-right: 8px;">
          {{ selectedNodes.length }} NODES SELECTED
        </span>
        <button 
          @click="mergeSelectedNodes"
          style="background: #E03C31; color: #FFF; border: none; padding: 6px 12px; border-radius: 4px; font-weight: 900; cursor: pointer; text-transform: uppercase; font-size: 12px; letter-spacing: 0.5px;"
        >
          MERGE & EVOLVE
        </button>
      </div>

      <!-- Single Node Context Menu -->
      <div 
        v-if="selectedNodes.length === 1"
        class="floating-action-bar single-action-bar"
        style="position: absolute; bottom: 80px; left: 50%; transform: translateX(-50%); z-index: 2000; display: flex; gap: 8px; background: var(--color-bg-panel); padding: 6px 12px; border: 1px solid var(--border-color); border-radius: 20px; box-shadow: var(--shadow-glass);"
      >
        <button 
          @click="toggleExpand(selectedNodes[0])"
          style="background: transparent; color: #FFF; border: 1px solid #FFF; padding: 4px 12px; border-radius: 4px; font-weight: 900; cursor: pointer; text-transform: uppercase; font-size: 11px; letter-spacing: 0.5px; transition: all 0.2s;"
          onmouseover="this.style.background='#FFF'; this.style.color='#000';"
          onmouseout="this.style.background='transparent'; this.style.color='#FFF';"
        >
          {{ selectedNodes[0].isExpanded ? 'COLLAPSE' : 'EXPAND' }}
        </button>
        <button 
          @click="spawnOmniDecoder(selectedNodes[0])"
          style="background: transparent; color: #00FF41; border: 1px solid #00FF41; padding: 4px 12px; border-radius: 4px; font-weight: 900; cursor: pointer; text-transform: uppercase; font-size: 11px; letter-spacing: 0.5px; transition: all 0.2s;"
          onmouseover="this.style.background='#00FF41'; this.style.color='#000';"
          onmouseout="this.style.background='transparent'; this.style.color='#00FF41';"
        >
          OMNI DECODE
        </button>
        <button 
          v-if="hasAppUI(selectedNodes[0])"
          @click="activeAppNode = selectedNodes[0]"
          style="background: transparent; color: #FF9800; border: 1px solid #FF9800; padding: 4px 12px; border-radius: 4px; font-weight: 900; cursor: pointer; text-transform: uppercase; font-size: 11px; letter-spacing: 0.5px; transition: all 0.2s;"
          onmouseover="this.style.background='#FF9800'; this.style.color='#000';"
          onmouseout="this.style.background='transparent'; this.style.color='#FF9800';"
        >
          OPEN APP
        </button>
        <button 
          @click="enterSubgraph(selectedNodes[0])"
          style="background: transparent; color: #00BCD4; border: 1px solid #00BCD4; padding: 4px 12px; border-radius: 4px; font-weight: 900; cursor: pointer; text-transform: uppercase; font-size: 11px; letter-spacing: 0.5px; transition: all 0.2s;"
          onmouseover="this.style.background='#00BCD4'; this.style.color='#000';"
          onmouseout="this.style.background='transparent'; this.style.color='#00BCD4';"
          title="Turn this node into a subgraph and dive into its contents"
        >
          DIVE IN
        </button>
        <!-- Contextual Help Button -->
        <button 
          @click="spawnContextualGuide(selectedNodes[0])"
          style="background: transparent; color: #E03C31; border: 1px solid #E03C31; padding: 4px 12px; border-radius: 4px; font-weight: 900; cursor: pointer; text-transform: uppercase; font-size: 11px; letter-spacing: 0.5px; transition: all 0.2s;"
          onmouseover="this.style.background='#E03C31'; this.style.color='#FFF';"
          onmouseout="this.style.background='transparent'; this.style.color='#E03C31';"
          title="Spawn an interactive tutorial specifically for this node type"
        >
          [?] GUIDE
        </button>
      </div>
    </div>

    <!-- Injection Stream (Terminal) -->
    <div class="injection-stream">
      <div class="stream-prompt">> AETHELNET_INJECT //</div>
      <input 
        type="text" 
        v-model="seedInput" 
        @keydown.enter="injectSeed"
        placeholder="Type a reality anchor or concept to seed the LGNN..."
        class="stream-input"
      />
      <button class="inject-btn" @click="injectSeed" :disabled="!seedInput.trim()">INJECT</button>
    </div>
    <!-- The Forge OS Builder Overlay -->
    <ForgeWorkbench 
      v-if="showForgeWorkbench"
      @close="showForgeWorkbench = false"
      @blueprint-forged="onBlueprintForged"
    />

    <!-- App Window Fullscreen Overlay -->
    <AppWindowOverlay
      v-if="activeAppNode"
      :node="activeAppNode"
      :resolvedComponent="resolveNodeComponent(activeAppNode)"
      :globalNodes="nodes"
      :globalLinks="links"
      @close="activeAppNode = null"
      @update="saveEdit"
      @app-message="handleAppMessage"
      @refresh="fetchGraphData"
    />

    <!-- Subgraph Breadcrumb -->
    <div v-if="currentParentId" class="subgraph-breadcrumb">
      <button class="breadcrumb-back-btn" @click="leaveSubgraph">← DIVE OUT</button>
      <span class="breadcrumb-path">DIMENSION: {{ currentParentId }}</span>
    </div>

    <!-- THE DIARY -->
    <TomRiddleDiary v-if="showDiary" @node-spawned="fetchGraphData" />

    <!-- SYSTEM LOGS HUD -->
    <SystemLogsHUD ref="systemLogsRef" />

    <!-- EDGE EDITOR -->
    <EdgeEditorModal 
      v-if="activeEdge" 
      :link="activeEdge" 
      @close="activeEdge = null"
      @save="updateLinkWeight"
      @sever="deleteLink"
    />

    <!-- Timeline HUD (Time-Machine) -->
    <TimelineHUD @checkout-complete="fetchGraphData" />

    <!-- GNN Parameters Tuning Panel -->
    <GnnTuningHUD 
      v-model:decay="lgnnDecay" 
      v-model:resonance="lgnnResonance" 
      @change="sendParams" 
    />

    <!-- Command Palette (Ctrl+K) -->
    <CommandPalette
      :is-open="showCommandPalette"
      @close="showCommandPalette = false"
      @command="handleCommand"
    />

    <!-- REM Sleep Overlay -->
    <div v-if="isRemSleep" class="rem-sleep-overlay">
      <div class="rem-text">THE GRAPH IS SLEEPING... (SYNAPTIC PRUNING ACTIVE)</div>
    </div>
    
    <!-- Dream Log Toast -->
    <div v-if="dreamLog" class="dream-log-toast">
      {{ dreamLog }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, shallowRef, watch, onMounted, onUnmounted, computed, nextTick, defineAsyncComponent, triggerRef } from 'vue'
import * as d3 from 'd3'
import { graphConnect, sugiyama } from 'd3-dag'

import LgnnTopNav from '../components/LgnnTopNav.vue'
import LgnnToolbox from '../components/LgnnToolbox.vue'
import ForgeWorkbench from '../components/ForgeWorkbench.vue'
import AppWindowOverlay from '../components/AppWindowOverlay.vue'
import CommandPalette from '../components/CommandPalette.vue'
import SynapticLinks from '../components/SynapticLinks.vue'
import TimelineHUD from '../components/TimelineHUD.vue'
import GnnTuningHUD from '../components/GnnTuningHUD.vue'
import SystemLogsHUD from '../components/SystemLogsHUD.vue'
import TomRiddleDiary from './TomRiddleDiary.vue'
import EdgeEditorModal from '../components/EdgeEditorModal.vue'
import { engineSettings } from '../utils/engineSettings'
import { forceLennardJones, forceEntanglement, forceHawkingRadiation } from '../utils/quantumPhysics'
import { useLgnnWebsocket } from '../composables/useLgnnWebsocket'

// Nodes
import HtmlNode from '../components/nodes/HtmlNode.vue'
import LuaNode from '../components/nodes/LuaNode.vue'
import ApiGatewayNode from '../components/nodes/ApiGatewayNode.vue'
import VitalsNode from '../components/nodes/VitalsNode.vue'
import { ThreeGraphRenderer } from '../shared/ThreeGraphRenderer'
import GalaxyView from '../components/GalaxyView.vue'
import VaultNode from '../components/nodes/VaultNode.vue'
import AudioNode from '../components/nodes/AudioNode.vue'
import NodeConsoleOverlay from '../components/NodeConsoleOverlay.vue'
import IdentityNode from '../components/nodes/IdentityNode.vue'
import SubgraphNode from '../components/nodes/SubgraphNode.vue'
import WebhookNode from '../components/nodes/WebhookNode.vue'
import PersonaNode from '../components/nodes/PersonaNode.vue'
import GuideNode from '@/components/nodes/GuideNode.vue'
import CustomNode from '@/components/nodes/CustomNode.vue'
import LgnnChatNode from '@/components/nodes/LgnnChatNode.vue'
import PinnedSummary from '@/components/PinnedSummary.vue'
import ModularSynthNode from '../components/nodes/ModularSynthNode.vue'
import SpiderNode from '../components/nodes/SpiderNode.vue'
import ObjDecoderNode from '../components/nodes/ObjDecoderNode.vue'
import OmniDecoderNode from '../components/nodes/OmniDecoderNode.vue'
import PatternMatcherNode from '../components/nodes/PatternMatcherNode.vue'
import AuraStreamNode from '../components/nodes/AuraStreamNode.vue'
import PrismaNode from '../components/nodes/PrismaNode.vue'
import FusionReactorNode from '../components/nodes/FusionReactorNode.vue'
import RepulsorNode from '../components/nodes/RepulsorNode.vue'
import GravitonNode from '../components/nodes/GravitonNode.vue'
import EntropyChamberNode from '../components/nodes/EntropyChamberNode.vue'
import IncubatorNode from '../components/nodes/IncubatorNode.vue'
import ChronosphereNode from '../components/nodes/ChronosphereNode.vue'

const emit = defineEmits(['open3d'])
import { API_BASE } from '../shared/api.js'

const apps = {
  Orderbook: defineAsyncComponent(() => import('./OrderbookView.vue')),
  Observer: defineAsyncComponent(() => import('./AethelnetObserverView.vue')),
  SelfHub: defineAsyncComponent(() => import('./SelfHubView.vue')),
  Script: defineAsyncComponent(() => import('./ScriptView.vue')),

  MacroVision: defineAsyncComponent(() => import('./Observer3DView.vue'))
}
// Quick fixes for undefined template properties from interrupted edits
const selectedNodes = computed(() => nodes.value.filter(n => (n as any).isSelected))
const customBlueprints = ref([])
const sortedManualNodes = ref([])


const isEcoMode = ref(false)

const showGnnTuning = ref(false)
const lgnnDecay = ref(0.05)
const lgnnResonance = ref(0.75)
const showDiary = ref(false)
const systemLogsRef = ref<any>(null)

const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
const wsUrl = `${wsProtocol}//${window.location.host}/ws`
const { ws, sendJson } = useLgnnWebsocket(
  wsUrl,
  fetchGraphData,
  () => !!activeDragNode,
  () => false
)

function sendParams() {
  sendJson({
    type: 'update_params',
    decay_rate: lgnnDecay.value,
    resonance_threshold: lgnnResonance.value
  })
}

const micActive = ref(false)
const gyroActive = ref(false)
const gpsActive = ref(false)
const toolboxPosition = ref({ x: 0, y: 0 })
const parallaxX = ref(0)
const parallaxY = ref(0)
const activeConsoleNode = ref<any | null>(null)
const activeEdge = ref<any | null>(null)
const showToolbox = ref(false)
const showCommandPalette = ref(false)
const isGalaxyMode = ref(false)
const searchQuery = ref('')
const activeAppNode = ref<any>(null)
const currentParentId = ref<string | null>(null)

// Spacebar Super Key logic
const isSpacePressed = ref(false)
let spaceKeyDownTime = 0

const webglCanvas = ref<HTMLCanvasElement | null>(null)
let threeRenderer: ThreeGraphRenderer | null = null

const hoveredParticle = ref<any>(null)
const hoveredParticlePos = ref({ x: 0, y: 0 })

function onMouseMove(e: MouseEvent | TouchEvent) {
  let clientX, clientY
  if (window.TouchEvent && e instanceof TouchEvent) {
    clientX = e.touches[0].clientX
    clientY = e.touches[0].clientY
  } else {
    clientX = (e as MouseEvent).clientX
    clientY = (e as MouseEvent).clientY
  }
  
  if (threeRenderer) {
    // Custom 2D hit testing since WebGL InstancedMesh exact-pixel raycasting is too hard to hit
    const { x: tx, y: ty, k } = globalTransform
    
    let hitNode = null
    let minDist = 25 // 25px hover radius!
    
    for (let i = 0; i < visibleNodes.value.length; i++) {
      const n = visibleNodes.value[i]
      if (n.isManual) continue // DOM nodes handle their own hovers
      
      const px = tx + (n.x || 0) * k
      const py = ty + (n.y || 0) * k
      
      const dx = clientX - px
      const dy = clientY - py
      const dist = Math.sqrt(dx*dx + dy*dy)
      
      if (dist < minDist) {
        minDist = dist
        hitNode = n
      }
    }
    
    if (hitNode) {
      hoveredParticle.value = hitNode
      hoveredParticlePos.value = { x: clientX, y: clientY }
    } else {
      hoveredParticle.value = null
    }
  }
}

function onMouseUp(e: MouseEvent | TouchEvent) {
  // handled in startDrag or specific events
}

function toggleGridMode() {
  isGridMode.value = !isGridMode.value
  if (isGridMode.value) {
    applyGridLayout()
    setTimeout(() => {
      recenterCanvas()
    }, 100)
  } else {
    // Release grid layout
    nodes.value.forEach(node => {
      delete node.fx
      delete node.fy
    })
    simulation.alpha(1).restart()
  }
}

function toggleEcoMode() {
  isEcoMode.value = !isEcoMode.value
  if (isEcoMode.value) {
    if (simulation) simulation.stop()
    if (backgroundAudio) backgroundAudio.pause()
    if (threeRenderer) threeRenderer.pause() // we need to add pause() to ThreeGraphRenderer
  } else {
    if (simulation) simulation.restart()
    if (backgroundAudio) backgroundAudio.play()
    if (threeRenderer) threeRenderer.resume()
  }
}

function applyGridLayout() {
  const adj = new Map()
  nodes.value.forEach(n => adj.set(n.id, []))
  
  links.value.forEach(e => {
    const sourceId = typeof e.source === 'object' ? e.source.id : e.source
    const targetId = typeof e.target === 'object' ? e.target.id : e.target
    if (adj.has(sourceId) && adj.has(targetId)) {
      adj.get(sourceId).push(targetId)
    }
  })
  
  const acyclicEdges: string[][] = []
  const visited = new Set<string>()
  const recStack = new Set<string>()
  
  function dfs(u: string) {
    visited.add(u)
    recStack.add(u)
    
    for (const v of adj.get(u) || []) {
      if (!visited.has(v)) {
        acyclicEdges.push([u, v])
        dfs(v)
      } else if (!recStack.has(v)) {
        acyclicEdges.push([u, v])
      }
    }
    recStack.delete(u)
  }
  
  nodes.value.forEach(n => {
    if (!visited.has(n.id)) dfs(n.id)
  })
  
  if (acyclicEdges.length === 0) {
    // No edges at all: arrange in a wide circle instead of a stiff grid
    const radius = Math.max(300, nodes.value.length * 40)
    const centerX = 0
    const centerY = 0
    nodes.value.forEach((node, i) => {
      const angle = (i / nodes.value.length) * Math.PI * 2
      node.fx = centerX + Math.cos(angle) * radius
      node.fy = centerY + Math.sin(angle) * radius
      node.x = node.fx
      node.y = node.fy
    })
    return
  }
  
  try {
    const createDag = graphConnect()
    const dag = createDag(acyclicEdges)
    const layout = sugiyama()
    layout(dag)
    
    let minX = Infinity, maxX = -Infinity
    let minY = Infinity, maxY = -Infinity
    
    for (const node of dag.nodes()) {
      if (node.x < minX) minX = node.x
      if (node.x > maxX) maxX = node.x
      if (node.y < minY) minY = node.y
      if (node.y > maxY) maxY = node.y
    }
    
    const scaleX = 200
    const scaleY = 150
    const centerX = (minX + maxX) / 2 || 0
    const centerY = (minY + maxY) / 2 || 0
    
    const positionedIds = new Set<string>()
    for (const dNode of dag.nodes()) {
      const id = dNode.data
      const vNode = nodes.value.find(n => n.id === id)
      if (vNode) {
        vNode.fx = (dNode.x - centerX) * scaleX
        vNode.fy = (dNode.y - centerY) * scaleY
        vNode.x = vNode.fx
        vNode.y = vNode.fy
        positionedIds.add(id)
      }
    }
    
    let unplacedIdx = 0
    nodes.value.forEach(node => {
      if (!positionedIds.has(node.id)) {
        node.fx = (maxX > -Infinity ? ((maxX - centerX) * scaleX + 250) : 0) + (unplacedIdx % 3) * 200
        node.fy = (unplacedIdx * 100)
        node.x = node.fx
        node.y = node.fy
        unplacedIdx++
      }
    })
    
  } catch (err) {
    console.error("DAG Layout failed:", err)
  }
}

function updateNodeAndConsole(node: any, newMeta: any, newContent?: string) {
  if (newMeta !== undefined) node.meta_data = JSON.stringify(newMeta)
  if (newContent !== undefined) node.content = newContent
  updateNode(node, {})
}

function deleteCustomBlueprint(bp: any) {}
function focusNode(node: any) {}
function toggleSensor(sensor: string) {
  if (sensor === 'mic') micActive.value = !micActive.value
  if (sensor === 'gyro') gyroActive.value = !gyroActive.value
  if (sensor === 'gps') gpsActive.value = !gpsActive.value
}
async function mergeSelectedNodes() {
  const ids = selectedNodes.value.map((n: any) => n.id)
  if (ids.length < 2) return
  
  try {
    const url = API_BASE ? `${API_BASE}/lgnn/macro/compress` : '/api/lgnn/macro/compress';
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ node_ids: ids })
    })
    const data = await res.json()
    if (data.status === 'success') {
      console.log('Macro Created:', data.new_node_id)
      nodes.value.forEach((n: any) => n.isSelected = false)
      await fetchGraphData()
    } else {
      console.error(data.message)
    }
  } catch (err) {
    console.error('Compression failed:', err)
  }
}

async function spawnOmniDecoder(targetNode: any) {
  try {
    const url = API_BASE ? `${API_BASE}/lgnn/node` : '/api/lgnn/node';
    const decoderId = 'omni_decoder_' + Date.now();
    
    // Spawn Decoder Node
    await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        id: decoderId,
        text_content: "",
        node_type: "standard",
        source_tag: "omni_decoder",
        meta_data: JSON.stringify({
          target_id: targetNode.id,
          mode: "TEXT"
        }),
        is_grounded: true,
        confidence: 1.0,
        parent_id: currentParentId.value || 'root'
      })
    });
    
    // Create connection from target to decoder
    const edgeUrl = API_BASE ? `${API_BASE}/lgnn/edge` : '/api/lgnn/edge';
    await fetch(edgeUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        source: targetNode.id,
        target: decoderId,
        weight: 1.0,
        is_manual: true
      })
    });

    targetNode.isSelected = false;
    await fetchGraphData();
  } catch (err) {
    console.error('Failed to spawn omni decoder:', err)
  }
}

async function updateNode(node: any, options: any = {}) {
  try {
    const url = API_BASE ? `${API_BASE}/lgnn/node` : '/api/lgnn/node';
    await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        id: node.id,
        text_content: node.content || node.label || '',
        meta_data: node.meta_data || "{}",
        source_tag: node.source_tag || "manual",
        connections: [],
        parent_id: node.parent_id || currentParentId.value || 'root'
      })
    })
    await fetchGraphData()
  } catch(e) {
    console.error("Failed to update node", e)
  }
}

function spawnNewMask() {
  const newId = `identity_${Date.now()}`
  const newNode = {
    id: newId,
    label: `NEW MASK`,
    source_tag: 'identity',
    x: Math.random() * 800 - 400,
    y: Math.random() * 600 - 300,
    text_content: 'Identity configuration...',
    meta_data: JSON.stringify({ system_prompt: 'You are an observer.' }),
    isManual: true,
    activation: 1.0,
    confidence: 1.0
  }
  nodes.value.push(newNode as any)
  triggerRef(nodes)
  globalActivePersonaId.value = newId
  updateNode(newNode)
  activeConsoleNode.value = newNode
}

function editMask(id: string) {
  const node = nodes.value.find((n: any) => n.id === id)
  if (node) {
    activeConsoleNode.value = node
  }
}

async function removeMask(id: string) {
  if (confirm('Delete this mask?')) {
    nodes.value = nodes.value.filter((n: any) => n.id !== id)
    if (globalActivePersonaId.value === id) {
      globalActivePersonaId.value = ''
    }
    // Delete from backend
    try {
      await fetch(`/api/lgnn/node/${id}`, { method: 'DELETE' })
    } catch (err) {
      console.error(err)
    }
  }
}

function loadCustomBlueprints() {
  try {
    const saved = localStorage.getItem('aethelnet_blueprints')
    if (saved) {
      customBlueprints.value = JSON.parse(saved)
    }
  } catch(e) {
    console.error("Failed to load custom blueprints", e)
  }
}

const isAudioPlaying = ref(false)
const isDreaming = ref(false)
const isTyping = ref(false)
const showForgeWorkbench = ref(false)

function onBlueprintForged(bp: any) {
  loadCustomBlueprints()
  showToolbox.value = true
}

function handleAppMessage(msg: any) {
  const payload = msg.data
  if (!payload || !payload.action) return
  
  if (payload.action === 'SPAWN_NODE') {
    // Send request to backend
    const tempId = 'app_spawn_' + Date.now()
    const url = API_BASE ? `${API_BASE}/lgnn/node` : '/api/lgnn/node'
    fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        id: tempId,
        text_content: payload.content || 'Spawned by App',
        source_tag: payload.source_tag || 'custom',
        connections: [msg.nodeId], // Connect to the app that spawned it
        parent_id: currentParentId.value || 'root',
        node_type: 'standard'
      })
    }).then(res => {
      if (res.ok) {
        fetchGraphData().then(() => refreshSimulation())
      }
    })
  } else if (payload.action === 'EVOLVE') {
    const url = API_BASE ? `${API_BASE}/lgnn/market/spawn_app` : '/api/lgnn/market/spawn_app'
    fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id: msg.nodeId, iterations: payload.iterations || 1 })
    }).then(res => {
      if (res.ok) fetchGraphData()
    })
  } else if (payload.action === 'CLOSE_WINDOW') {
    if (activeAppNode.value && activeAppNode.value.id === msg.nodeId) {
      activeAppNode.value = null;
    }
  } else if (payload.action === 'SET_DECAY') {
    if (payload.value !== undefined) {
      lgnnDecay.value = parseFloat(payload.value);
      sendParams();
    }
  } else if (payload.action === 'SET_RESONANCE') {
    if (payload.value !== undefined) {
      lgnnResonance.value = parseFloat(payload.value);
      sendParams();
    }
  }
}

function handleCommand(item: any) {
  if (item.type === 'node') {
    // Focus the node
    const n = nodes.value.find((nd: any) => nd.id === item.id)
    if (n) {
      selectedNodeIds.value.clear()
      selectedNodeIds.value.add(n.id)
      nodes.value.forEach((nd: any) => nd.isSelected = (nd.id === n.id))
      // In a real D3 app we would transition the zoom transform here
    }
  } else if (item.type === 'app') {
    // Download/Spawn the community app from market
    spawnCustom(item.node.meta_data)
  } else if (item.type === 'command') {
    const cmd = item.value
    if (cmd.startsWith('spawn-')) {
      const appType = cmd.replace('spawn-', '')
      if (appType === 'spider') {
        spawnApp('Spider')
      } else if (appType === 'anomaly') {
        // Create a custom Gravity Well node instantly
        const id = `manual_anomaly_${Date.now()}`
        const newNode: Node = {
          id: id,
          label: 'GRAVITY ANOMALY',
          content: 'Sucking in untagged low-confidence ideas...',
          source_tag: 'manual',
          parent_id: currentParentId.value || 'root',
          x: (window.innerWidth / 2 - globalTransform.x) / globalTransform.k,
          y: (window.innerHeight / 2 - globalTransform.y) / globalTransform.k,
          z: 0,
          isExpanded: true,
          node_type: 'gravity_well',
          meta_data: { gravity_strength: 1.5, is_anomaly: true }
        }
        nodes.value.push(newNode)
        updateNode(newNode, {})
        refreshSimulation()
      } else if (appType === 'app') {
        spawnApp(item.payload)
      } else {
        const appMap: Record<string, string> = {
          'identity': 'Identity',
          'aurastream': 'AuraStream',
          'html': 'Html',
          'render': 'Render',
          'vault': 'Vault',
          'subgraph': 'Subgraph',
          'audio': 'Audio',
          'omni': 'OmniDecoder',
          'vitals': 'Vitals'
        }
        const mapped = appMap[appType] || appType
        spawnApp(mapped)
      }
    } else if (cmd === 'fresh-canvas') {
      spawnApp('Subgraph').then((newId) => {
        if (newId) {
          const newNode = nodes.value.find((n: any) => n.id === newId)
          if (newNode) enterSubgraph(newNode)
        }
      })
    } else if (cmd === 'toggle-diary') {
      showDiary.value = !showDiary.value
    } else if (cmd === 'toggle-logs') {
      systemLogsRef.value?.toggleOpen()
    } else if (cmd === 'clear-graph') {
      nodes.value = []
      links.value = []
    } else if (cmd === 'load-blueprint') {
      isGalaxyMode.value = true
      // We assume /api/blueprint or /naas/blueprint? 
      // Since aethelnet-node is running on port 8000, we'll hit its endpoint
      const API_BASE = window.API_BASE || 'http://localhost:8000/api'
      fetch(`${API_BASE}/system_apps/blueprint`) // or wherever we mounted it
        .then(res => res.json())
        .then(data => {
          if (data && data.nodes) {
            const bpNodes = data.nodes.map((n: any) => ({
              id: n.id,
              label: n.name || n.id,
              type: n.type || 'file',
              x: (Math.random() - 0.5) * 5000,
              y: (Math.random() - 0.5) * 5000,
              z: (Math.random() - 0.5) * 5000,
              color: n.type === 'file' ? '#00BCD4' : (n.type === 'function' ? '#4CAF50' : '#FF9800')
            }))
            const bpEdges = data.edges.map((e: any) => ({
              source: e.source,
              target: e.target,
              type: e.type || 'import'
            }))
            nodes.value = bpNodes
            links.value = bpEdges
            triggerRef(nodes)
            triggerRef(links)
          }
        })
        .catch(err => console.error("Failed to load blueprint", err))
    }
  }
}


async function spawnCustom(bp: any) {
  const tempId = 'custom_' + Date.now()
  const newNode = {
    id: tempId,
    text_content: bp.script || '# Custom App Node',
    node_type: 'macro',
    is_grounded: true,
    confidence: 1.0,
    source_tag: 'custom',
    connections: [],
    parent_id: currentParentId.value || 'root',
    meta_data: JSON.stringify({
      blueprint: bp,
      state: {}
    })
  }

  try {
    const url = API_BASE ? `${API_BASE}/lgnn/node` : '/api/lgnn/node';
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(newNode)
    })
    
    if (response.ok) {
      await fetchGraphData()
      const spawned = nodes.value.find((n: any) => n.id === tempId)
      if (spawned) {
        spawned.x = (window.innerWidth / 2 - globalTransform.x) / globalTransform.k
        spawned.y = (window.innerHeight / 2 - globalTransform.y) / globalTransform.k
        spawned.fx = spawned.x
        spawned.fy = spawned.y
        spawned.isExpanded = true
        triggerRef(nodes)
        refreshSimulation()
      }
    }
  } catch (err) {
    console.error("Failed to spawn custom app:", err)
  }
  showToolbox.value = false
}

let backgroundAudio: HTMLAudioElement | null = null

const toggleAudio = () => {
  if (isAudioPlaying.value) {
    if (backgroundAudio) {
      backgroundAudio.pause()
    }
    isAudioPlaying.value = false
  } else {
    // We add a timestamp query param to bust cache and get the latest dream
    const timestamp = new Date().getTime()
    backgroundAudio = new Audio(`${API_BASE}/lgnn/audio/latest?t=${timestamp}`)
    backgroundAudio.loop = true
    backgroundAudio.volume = 0.5
    backgroundAudio.play().catch(e => console.error("Audio playback failed. Please interact with the page first.", e))
    isAudioPlaying.value = true
  }
}

function saveExpandedState() {
  const expandedIds = nodes.value.filter(n => n.isExpanded).map(n => n.id)
  localStorage.setItem('aethelnet_expanded_nodes', JSON.stringify(expandedIds))
}

function toggleExpand(node: Node) {
  node.isExpanded = !node.isExpanded
  saveExpandedState()
}

function getAppType(node: Node): string | null {
  const content = node.content || ''
  const label = node.label || ''
  const match = (content + ' ' + label).match(/APP:(\w+)/)
  if (match && apps[match[1] as keyof typeof apps]) {
    return match[1]
  }
  return null
}

function resolveNodeComponent(node: Node) {
  if (node.source_tag === 'aurastream') return AuraStreamNode
  if (node.source_tag === 'prisma') return PrismaNode
  if (node.source_tag === 'fusion') return FusionReactorNode
  if (node.source_tag === 'repulsor') return RepulsorNode
  if (node.source_tag === 'graviton') return GravitonNode
  if (node.source_tag === 'entropy') return EntropyChamberNode
  if (node.source_tag === 'incubator') return IncubatorNode
  if (node.source_tag === 'chronosphere') return ChronosphereNode
  if (node.source_tag === 'omni_decoder') return OmniDecoderNode
  if (node.source_tag?.toLowerCase() === 'academy' || node.source_tag?.toLowerCase() === 'pattern_matcher') return PatternMatcherNode
  if (node.source_tag === 'obj_decoder') return ObjDecoderNode
  if (node.source_tag === 'spider') return SpiderNode
  if (node.source_tag === 'audio') return AudioNode
  if (node.source_tag === 'vault') return VaultNode
  if (node.source_tag === 'webhook') return WebhookNode
  if (node.source_tag === 'api_gateway') return ApiGatewayNode
  if (node.source_tag === 'subgraph' || node.id === 'COMMUNITY_FORUM') return SubgraphNode
  if (node.source_tag === 'synth') return ModularSynthNode
  if (node.source_tag === 'lua') return LuaNode
  if (node.source_tag === 'vitals') return VitalsNode
  if (node.source_tag === 'identity') return IdentityNode
  if (node.source_tag === 'lgnn_chat') return LgnnChatNode
  if (node.source_tag === 'custom' || node.source_tag === 'custom_app' || node.label?.startsWith('APP:')) return CustomNode
  if (node.id === 'AETHEL_DOCS') return GuideNode
  if (node.source_tag === 'persona' || node.id.startsWith('persona_')) return PersonaNode
  return HtmlNode
}

function startEdit(node: Node) {
  node.isEditing = true
}

async function saveEdit(node: Node) {
  node.isEditing = false
  // Save to backend
  if (!node.id.startsWith('temp')) {
    try {
      const url = API_BASE ? `${API_BASE}/lgnn/node` : '/api/lgnn/node';
      await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          id: node.id,
          text_content: node.content || node.label || '',
          source_tag: "manual",
          connections: [],
          parent_id: currentParentId.value || 'root'
        })
      })
    } catch (e) {
      console.error("Failed to save node edit", e)
    }
  }
}

async function executeMacro(node: Node) {
  try {
    node.isProcessing = true; // Optional: Add loading state feedback
    const res = await fetch(`${API_BASE || ''}/lgnn/macro/execute`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        node_id: node.id,
        inputs: node.inputs || {},
        text_content: node.content || node.label || ""
      })
    });
    if (!res.ok) throw new Error(`Execution failed: ${res.statusText}`);
    const data = await res.json();
    console.log("Macro execution result:", data);
    // Optionally trigger a graph refresh so we see the new output nodes
    fetchGraphData();
  } catch (err) {
    console.error("Macro execution error:", err);
  } finally {
    node.isProcessing = false;
  }
}

interface Node {
  id: string
  label?: string
  content?: string
  x: number
  y: number
  z: number
  vx: number
  vy: number
  vz: number
  fx?: number
  fy?: number
  isExpanded: boolean
  isEditing?: boolean
  isDragged?: boolean
  isSelected?: boolean
  isProcessing?: boolean
  isManual?: boolean
  mean_activation?: number
  confidence?: number
  // Visual projection coords
  sx?: number
  sy?: number
  scale?: number
  // Data flow
  inputs?: Record<string, any>
  outputs?: any
  node_type?: string
  meta_data?: any
}


interface Link {
  source: string | Node
  target: string | Node
  weight: number
}

const linkDistance = 150
const collisionRadius = 60

const permanentlyDeletedNodes = new Set<string>()

// The physical bounds constraint logic
const constrainToBounds = (node: Node) => {
  // Infinite canvas: No strict bounds, let nodes drift where they may
}

const canvasContainer = ref<HTMLDivElement | null>(null)

const parentStack = ref<{id: string, label: string, k: number, x: number, y: number}[]>([])

async function enterSubgraph(node: any) {
  // Save current camera state
  parentStack.value.push({ 
    id: currentParentId.value || 'root', 
    label: currentParentId.value ? 'Parent' : 'Root',
    k: globalTransform.k,
    x: globalTransform.x,
    y: globalTransform.y
  })
  currentParentId.value = node.id
  
  // Smoothly zoom and pan to the subgraph node
  if (canvasContainer.value && d3ZoomInstance) {
    const targetK = Math.min(globalTransform.k * 2, 3)
    const targetX = (window.innerWidth / 2) - ((node.x || 0) * targetK)
    const targetY = (window.innerHeight / 2) - ((node.y || 0) * targetK)
    
    d3.select(canvasContainer.value).transition().duration(750).call(
      (d3ZoomInstance as any).transform,
      d3.zoomIdentity.translate(targetX, targetY).scale(targetK)
    ).on('end', () => {
      fetchGraphData()
      refreshSimulation()
    })
  } else {
    fetchGraphData()
    refreshSimulation()
  }
}

async function leaveSubgraph() {
  if (parentStack.value.length > 0) {
    const parent = parentStack.value.pop()
    currentParentId.value = parent?.id === 'root' ? null : (parent?.id || null)
    
    if (canvasContainer.value && parent && d3ZoomInstance) {
      fetchGraphData().then(() => {
        refreshSimulation() // Refresh immediately so parent is visible before zooming out
        d3.select(canvasContainer.value as any).transition().duration(750).call(
          (d3ZoomInstance as any).transform,
          d3.zoomIdentity.translate(parent.x, parent.y).scale(parent.k)
        )
      })
    } else {
      fetchGraphData().then(() => refreshSimulation())
    }
  }
}

const sessionStartTime = Date.now()

function isSessionLocal(id: string) {
  if (!id) return false;
  const parts = id.split('_');
  const lastPart = parts[parts.length - 1];
  if (lastPart && lastPart.length === 13) {
    const ts = parseInt(lastPart, 10);
    if (!isNaN(ts) && ts >= sessionStartTime) {
      return true;
    }
  }
  return false;
}

const visibleNodes = computed(() => {
  const pid = currentParentId.value || 'root'
  return nodes.value.filter(n => {
    const nodeParent = n.parent_id || 'root'
    if (nodeParent !== pid) return false
    
    // Blank Page Mode: Hide stardust unless Galaxy View is enabled
    if (!showAutonomous.value) {
      if (!isSessionLocal(n.id) && !n.isExpanded && !n.isSelected) return false
    }
    
    return true
  })
})

const domNodes = computed(() => {
  return visibleNodes.value.filter(n => n.isExpanded)
})

function refreshSimulation() {
  if (simulation) {
    simulation.nodes(visibleNodes.value)
    
    // Also filter links
    const visibleNodeIds = new Set(visibleNodes.value.map((n: any) => n.id))
    const visibleLinks = links.value.filter((l: any) => {
      const sid = typeof l.source === 'object' ? l.source.id : l.source
      const tid = typeof l.target === 'object' ? l.target.id : l.target
      return visibleNodeIds.has(sid) && visibleNodeIds.has(tid)
    })
    
    simulation.force('link').links(visibleLinks)
    simulation.alpha(1).restart()
    
    if (threeRenderer) {
      threeRenderer.updateData(visibleNodes.value, visibleLinks)
    }
  }
}

const nodes = shallowRef<any[]>([])
const links = ref<Link[]>([])
const projectedLinks = ref<any[]>([])
const seedInput = ref('')
const selectedNodeIds = ref<Set<string>>(new Set())

// FastLink (Synapse wiring) state
const fastLinkSource = ref<Node | null>(null)
const fastLinkCurrent = ref({ x: 0, y: 0 })

function startFastLink(e: MouseEvent | TouchEvent, node: Node) {
  e.preventDefault()
  fastLinkSource.value = node
  updateFastLinkPos(e)
  
  const moveHandler = (ev: MouseEvent | TouchEvent) => updateFastLinkPos(ev)
  
  const upHandler = (ev: MouseEvent | TouchEvent) => {
    window.removeEventListener('mousemove', moveHandler)
    window.removeEventListener('touchmove', moveHandler)
    window.removeEventListener('mouseup', upHandler)
    window.removeEventListener('touchend', upHandler)
    
    const clientX = 'touches' in ev ? ev.changedTouches[0].clientX : (ev as MouseEvent).clientX
    const clientY = 'touches' in ev ? ev.changedTouches[0].clientY : (ev as MouseEvent).clientY
    
    const rect = canvasContainer.value?.getBoundingClientRect()
    if (rect && fastLinkSource.value) {
      const x = clientX - rect.left
      const y = clientY - rect.top
      
      let hitNode: Node | null = null
      for (const n of nodes.value) {
        if (n === fastLinkSource.value) continue
        if (n.sx !== undefined && n.sy !== undefined) {
          const dx = n.sx - x
          const dy = n.sy - y
          // Roughly 100px radius hit box for node center
          if (dx*dx + dy*dy < 10000) {
            hitNode = n
            break
          }
        }
      }
      
      if (hitNode) {
        createLink(fastLinkSource.value.id, hitNode.id)
      }
    }
    fastLinkSource.value = null
  }
  
  window.addEventListener('mousemove', moveHandler)
  window.addEventListener('touchmove', moveHandler)
  window.addEventListener('mouseup', upHandler)
  window.addEventListener('touchend', upHandler)
}

function updateFastLinkPos(e: MouseEvent | TouchEvent) {
  const rect = canvasContainer.value?.getBoundingClientRect()
  if (!rect) return
  const clientX = 'touches' in e ? e.touches[0].clientX : (e as MouseEvent).clientX
  const clientY = 'touches' in e ? e.touches[0].clientY : (e as MouseEvent).clientY
  fastLinkCurrent.value = { x: clientX - rect.left, y: clientY - rect.top }
}

async function createLink(sourceId: string, targetId: string) {
  try {
    const url = API_BASE ? `${API_BASE}/lgnn/link` : '/api/lgnn/link';
    await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ source: sourceId, target: targetId, weight: 1.0 })
    })
    // Ensure it visualizes immediately
    links.value.push({ source: sourceId, target: targetId, weight: 1.0 })
  } catch (e) {
    console.error("Failed to create link", e)
  }
}

// Box selection state
const isBoxSelecting = ref(false)
const boxStart = ref({ x: 0, y: 0 })
const boxCurrent = ref({ x: 0, y: 0 })

// UI state
const showAutonomous = ref(true)
const minConfidence = ref(0.5)
const globalActivePersonaId = ref('')
const transform = ref({ x: 0, y: 0, scale: 1 })
const currentResonance = ref(0)

// REM Sleep Cycle (The Forge / Synaptic Pruning)
const isRemSleep = ref(false)
const dreamLog = ref("")
let remIdleTimer: any = null
const REM_SLEEP_TIMEOUT = 120000 // 2 minutes of idle time

async function triggerRemSleep() {
  if (isRemSleep.value || isDreaming.value) return;
  isRemSleep.value = true;
  
  if (physicsWorker) {
    physicsWorker.postMessage({ type: 'DREAM' }) // Speed up physics slightly to represent processing
  }

  try {
    const url = API_BASE ? `${API_BASE}/lgnn/rem_sleep` : '/api/lgnn/rem_sleep';
    const response = await fetch(url, { method: 'POST' });
    const result = await response.json();
    if (result.status === 'success') {
      dreamLog.value = result.log;
    }
  } catch(e) {
    console.error("REM Sleep interrupted", e);
  }
}

function wakeUp() {
  if (isRemSleep.value) {
    isRemSleep.value = false;
    if (physicsWorker) physicsWorker.postMessage({ type: 'STOP' })
    fetchGraphData(); // Reload pruned graph
    
    // Hide toast after 5 seconds
    setTimeout(() => {
      dreamLog.value = "";
    }, 5000);
  }
  
  clearTimeout(remIdleTimer);
  remIdleTimer = setTimeout(triggerRemSleep, REM_SLEEP_TIMEOUT);
}

onMounted(() => {
  window.addEventListener('mousemove', wakeUp);
  window.addEventListener('keydown', wakeUp);
  window.addEventListener('mousedown', wakeUp);
  window.addEventListener('touchstart', wakeUp);
  remIdleTimer = setTimeout(triggerRemSleep, REM_SLEEP_TIMEOUT);
})

onUnmounted(() => {
  window.removeEventListener('mousemove', wakeUp);
  window.removeEventListener('keydown', wakeUp);
  window.removeEventListener('mousedown', wakeUp);
  window.removeEventListener('touchstart', wakeUp);
  clearTimeout(remIdleTimer);
})

function zoomIn() {
  if (zoomBehavior && canvasContainer.value) {
    const container = d3.select(canvasContainer.value as Element)
    container.transition().duration(300).call((zoomBehavior as any).scaleBy, 1.5)
  }
}

function zoomOut() {
  if (zoomBehavior && canvasContainer.value) {
    const container = d3.select(canvasContainer.value as Element)
    container.transition().duration(300).call((zoomBehavior as any).scaleBy, 0.75)
  }
}

function recenterCanvas() {
  if (d3ZoomInstance && canvasContainer.value) {
    const svg = d3.select(canvasContainer.value)
    svg.transition().duration(500).call(d3ZoomInstance.transform, d3.zoomIdentity)
  }
}

// Cleanup audio on route change
onUnmounted(() => {
  if (backgroundAudio) {
    backgroundAudio.pause()
    backgroundAudio.src = ''
    backgroundAudio = null
  }
})

let simulation: any = null
let physicsWorker: Worker | null = null
let animationFrameId = 0
let width = window.innerWidth
let height = window.innerHeight

let globalTransform = { x: 0, y: 0, k: 1 }

async function triggerDreamState() {
  if (isDreaming.value) return; // Already dreaming
  if (nodes.value.length === 0) {
    alert("Graph is empty! Add some thoughts first.");
    return;
  }
  
  isDreaming.value = true;
  
  // Pick a random node text to use as the seed
  const randomNode = nodes.value[Math.floor(Math.random() * nodes.value.length)];
  const seedText = randomNode.content || randomNode.label || "The void";

  // Simulate an active pulsing physics state
  const interval = setInterval(() => {
    if (simulation) simulation.alphaTarget(0.3).restart();
  }, 500);

  try {
    const response = await fetch(`${API_BASE}/lgnn/dream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: seedText })
    });
    const result = await response.json();
    
    if (result.status === 'success') {
      // Spawn the new dream thought into the canvas
      const cx = (window.innerWidth / 2 - globalTransform.x) / globalTransform.k;
      const cy = (window.innerHeight / 2 - globalTransform.y) / globalTransform.k;
      
      const newNode: Node = {
        id: `dream_${Date.now()}`,
        label: `PROPHECY: ${result.attractors.join(', ')}`,
        content: result.dream,
        x: cx,
        y: cy,
        z: 0,
        vx: 0,
        vy: 0,
        vz: 0,
        isExpanded: true,
        isManual: true
      };
      
      nodes.value.push(newNode);
      
      // Auto-connect it to the attractors if they exist in the UI
      result.attractors.forEach((attrId: string) => {
        const targetNode = nodes.value.find(n => n.id === attrId || n.label === attrId);
        if (targetNode) {
          links.value.push({
            source: newNode,
            target: targetNode,
            weight: 3.0,
            sx1: 0, sy1: 0, sx2: 0, sy2: 0
          });
        }
      });
      
      if (simulation) {
        simulation.nodes(nodes.value as d3.SimulationNodeDatum[]);
        (simulation.force('link') as any).links(links.value);
        simulation.alpha(1).restart();
      }
    } else {
      console.error("Dream failed:", result);
    }
  } catch (e) {
    console.error("Failed to trigger dream state", e);
  } finally {
    clearInterval(interval);
    isDreaming.value = false;
    if (simulation) simulation.alphaTarget(0);
  }
}
async function fetchGraphData() {
  if (nodes.value.some(n => n.isEditing)) return
  try {
    const pid = encodeURIComponent(currentParentId.value || 'root')
    const url = API_BASE ? `${API_BASE}/lgnn/graph?parent_id=${pid}` : `/api/lgnn/graph?parent_id=${pid}`;
    const res = await fetch(url)
    if (!res.ok) return
    const data = await res.json()
    // Merge new data while preserving physics state
    // Update nodes in-place to preserve D3 physics state and avoid Vue reactivity overhead
    let topologyChanged = false
    const nodeMap = new Map(nodes.value.map(n => [n.id, n]))
    const newNodesMap = new Map(data.nodes.map((n: any) => [n.id, n]))
    
    // Remove nodes that don't belong to current parent, or have been deleted
    const currentPid = currentParentId.value || 'root'
    for (let i = nodes.value.length - 1; i >= 0; i--) {
      const nodeParent = nodes.value[i].parent_id || 'root'
      if (nodeParent !== currentPid || !newNodesMap.has(nodes.value[i].id)) {
        nodes.value.splice(i, 1)
        topologyChanged = true
      }
    }
    
    // Add new nodes or update existing
    data.nodes.forEach((n: any) => {
      if (permanentlyDeletedNodes.has(n.id)) return
      
      const existing = nodeMap.get(n.id)
      if (existing) {
        existing.confidence = n.confidence
        existing.content = n.content || n.text_content || existing.content || ''
        existing.node_type = n.node_type || 'standard'
        existing.meta_data = typeof n.meta_data === 'string' ? JSON.parse(n.meta_data || '{}') : n.meta_data
      } else {
        const manualTags = ['manual', 'custom', 'blueprint', 'identity', 'audio', 'spider', 'webhook', 'vault', 'subgraph', 'internal']
        const isManual = n.id.startsWith('seed_') || n.id.startsWith('wiki_') || n.id.startsWith('manual_') || n.node_type === 'macro' || manualTags.includes(n.source_tag) || n.id.startsWith('OPERATOR') || n.id.startsWith('PRISM')
        
        const savedExpanded = JSON.parse(localStorage.getItem('aethelnet_expanded_nodes') || '[]')
        
        const cx = window.innerWidth / 2
        const cy = window.innerHeight / 2
        const k = globalTransform.k || 1
        const tx = globalTransform.x || 0
        const ty = globalTransform.y || 0
        const logicalCx = (cx - tx) / k
        const logicalCy = (cy - ty) / k
        
        const startX = n.x ?? (logicalCx + (Math.random() * 100 - 50))
        const startY = n.y ?? (logicalCy + (Math.random() * 100 - 50))
        
        nodes.value.push({
          id: n.id,
          label: n.label || n.id,
          content: n.content || n.text_content || '',
          inputs: {},
          isManual,
          isAutonomous: n.source_tag === 'spider',
          source_tag: n.source_tag,
          parent_id: n.parent_id || 'root',
          x: startX,
          y: startY,
          z: isManual ? 0 : (Math.random() * 200 - 100),
          isExpanded: savedExpanded.includes(n.id),
          isDragged: false,
          isSelected: false,
          isEditing: false,
          scale: 1,
          node_type: n.node_type || 'standard',
          meta_data: typeof n.meta_data === 'string' ? JSON.parse(n.meta_data || '{}') : n.meta_data
        })
        topologyChanged = true
      }
    })
    
    if (topologyChanged) {
      triggerRef(nodes)
    }
    
    // We update links if they changed
    // Use a Set to deduplicate links based on source and target IDs
    const existingEdges = new Set()
    const backendLinks = data.links.map((l: any) => {
        const srcId = typeof l.source === 'string' ? l.source : l.source.id
        const tgtId = typeof l.target === 'string' ? l.target : l.target.id
        existingEdges.add(srcId + '->' + tgtId)
        return {
          source: nodes.value.find(n => n.id === l.source) || l.source,
          target: nodes.value.find(n => n.id === l.target) || l.target,
          weight: l.weight || 1
        }
    })
    
    // Add local edges that aren't in the backend
    const localLinks = manualLocalEdges.value.filter(l => {
      const srcId = typeof l.source === 'string' ? l.source : (l.source as Node).id
      const tgtId = typeof l.target === 'string' ? l.target : (l.target as Node).id
      
      const hasSrc = nodes.value.some(n => n.id === srcId)
      const hasTgt = nodes.value.some(n => n.id === tgtId)
      
      return hasSrc && hasTgt && !existingEdges.has(srcId + '->' + tgtId)
    }).map(l => {
      const srcId = typeof l.source === 'string' ? l.source : (l.source as Node).id
      const tgtId = typeof l.target === 'string' ? l.target : (l.target as Node).id
      return {
        source: nodes.value.find(n => n.id === srcId) as Node,
        target: nodes.value.find(n => n.id === tgtId) as Node,
        weight: 1
      }
    })
    
    links.value = [...backendLinks, ...localLinks]
    
    if (!physicsWorker) {
      physicsWorker = new Worker(new URL('../workers/physics.worker.ts', import.meta.url), { type: 'module' })
      physicsWorker.onmessage = (e) => {
        if (e.data.type === 'TICK') {
          const positions = e.data.payload
          const nodeMap = new Map(nodes.value.map(n => [n.id, n]))
          for (const p of positions) {
            const node = nodeMap.get(p.id)
            if (node && !node.isDragged) { // don't override dragged position
              node.x = p.x
              node.y = p.y
              node.vx = p.vx
              node.vy = p.vy
            }
          }
          nodes.value.forEach(constrainToBounds)
          updateProjection()
        }
      }
      
      // Setup the mock simulation proxy to intercept all legacy d3 calls
      simulation = {
        alpha: (v: number) => {
          if (v > 0) physicsWorker?.postMessage({ type: 'DREAM' })
          return simulation
        },
        alphaTarget: (v: number) => {
          if (v > 0) physicsWorker?.postMessage({ type: 'DREAM' })
          else physicsWorker?.postMessage({ type: 'STOP' })
          return simulation
        },
        restart: () => {
          physicsWorker?.postMessage({ type: 'DREAM' })
          return simulation
        },
        stop: () => {
          physicsWorker?.postMessage({ type: 'STOP' })
          return simulation
        },
        nodes: (n: any) => simulation,
        force: (name: string, f?: any) => {
          if (f === undefined) return { links: () => {} }
          return simulation
        },
        alphaDecay: (v: number) => simulation,
        on: (event: string, cb: any) => simulation
      }
    }
    
    // Create a copy of links for the worker
    const d3Links = links.value.map(l => ({ 
      source: (l.source as Node).id ?? l.source, 
      target: (l.target as Node).id ?? l.target, 
      weight: l.weight 
    }))
    
    if (isGridMode.value) {
      applyGridLayout()
    } else {
      // Send data to worker instead of local simulation
      physicsWorker.postMessage({
        type: 'UPDATE',
        payload: {
          nodes: JSON.parse(JSON.stringify(nodes.value)), // strip reactivity
          links: d3Links,
          engineSettings,
          linkDistance
        }
      })
    }
      
    if (topologyChanged) {
      triggerRef(nodes)
      if (threeRenderer) {
        const visibleNodeIds = new Set(visibleNodes.value.map(n => n.id))
        const visibleLinks = links.value.filter(l => {
          const sid = typeof l.source === 'object' ? l.source.id : l.source
          const tid = typeof l.target === 'object' ? l.target.id : l.target
          return visibleNodeIds.has(sid) && visibleNodeIds.has(tid)
        })
        threeRenderer.updateData(visibleNodes.value, visibleLinks)
      }
    }
      
    updateProjection()
  } catch (err) {
    console.error("Failed to fetch graph data", err)
  }
}

async function saveGraphPhysics() {
  try {
    const url = API_BASE ? `${API_BASE}/lgnn/graph?parent_id=${encodeURIComponent(currentParentId.value || 'root')}` : `/api/lgnn/graph?parent_id=${encodeURIComponent(currentParentId.value || 'root')}`;
    await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        nodes: nodes.value.map(n => ({
          id: n.id,
          x: n.x,
          y: n.y,
          fx: n.fx,
          fy: n.fy
        }))
      })
    })
  } catch (err) {
    console.error("Failed to save graph physics", err)
  }
}

function updateProjection() {
  const { x: tx, y: ty, k } = globalTransform
  
  // Only update coordinates
  domNodes.value.forEach(node => {
    const perspective = 800 / (800 + (node.z || 0))
    node.scale = k * perspective
    node.sx = tx + (node.x || 0) * k
    node.sy = ty + (node.y || 0) * k
  })
  
  // Directly update DOM to avoid Vue Virtual DOM lag
  if (canvasContainer.value) {
    const els = canvasContainer.value.querySelectorAll('.concept-node')
    els.forEach(el => {
      const id = el.getAttribute('data-node-id')
      if (id) {
        const node = domNodes.value.find(n => n.id === id)
        if (node) {
          (el as HTMLElement).style.transform = `translate(calc(${node.sx}px - 50%), calc(${node.sy}px - 50%)) scale(${node.scale || 1})`
        }
      }
    })
  }

  // Update synaptic links
  const newProjectedLinks = []
  for (const link of links.value) {
    const s = typeof link.source === 'string' ? nodes.value.find(n => n.id === link.source) : link.source
    const t = typeof link.target === 'string' ? nodes.value.find(n => n.id === link.target) : link.target
    if (s && t && (s.isExpanded || t.isExpanded)) {
      const sx1 = tx + (s.x || 0) * k
      const sy1 = ty + (s.y || 0) * k
      const sx2 = tx + (t.x || 0) * k
      const sy2 = ty + (t.y || 0) * k
      newProjectedLinks.push({
        ...link,
        source: s,
        target: t,
        sx1, sy1, sx2, sy2
      })
    }
  }
  projectedLinks.value = newProjectedLinks
  
  if (threeRenderer) {
    threeRenderer.globalTransform = globalTransform
  }
}

function propagateDataFlow() {
  // Clear inputs before propagating new ones
  nodes.value.forEach(n => {
    n.inputs = {}
  })

  links.value.forEach(link => {
    const source = typeof link.source === 'string' ? nodes.value.find(n => n.id === link.source) : link.source as Node
    const target = typeof link.target === 'string' ? nodes.value.find(n => n.id === link.target) : link.target as Node
    
    if (source && target) {
      const outputVal = source.outputs !== undefined ? source.outputs : source.content
      if (outputVal !== undefined) {
        if (!target.inputs) target.inputs = {}
        const key = source.label || source.id
        target.inputs[key] = outputVal
      }
    }
  })
}

let d3ZoomInstance: any = null
let zoomBehavior: any = null

function setupZoomAndPan() {
  const svg = d3.select(canvasContainer.value)
  zoomBehavior = d3.zoom<HTMLDivElement, unknown>()
    .scaleExtent([0.1, 4])
    .filter((e) => {
      // Don't pan on shift+drag (used for box select)
      if (e.type === 'mousedown' && e.shiftKey) return false
      // Only pan if Spacebar is pressed, OR if the event target is the background
      if (e.type === 'mousedown' && !isSpacePressed.value) {
        if (e.target && e.target.closest) {
           if (e.target.closest('.concept-node') || 
               e.target.closest('.app-window-overlay') || 
               e.target.closest('.toolbox') ||
               e.target.closest('.floating-action-bar')) {
             return false
           }
        }
      }
      return true
    })
    .on("zoom", (e) => {
      globalTransform = e.transform
      localStorage.setItem('aethelnet_canvas_transform', JSON.stringify({ x: e.transform.x, y: e.transform.y, k: e.transform.k }))
      updateProjection()
    })
  
  // Always bind the zoom behavior first
  svg.call(zoomBehavior as any)
  d3ZoomInstance = zoomBehavior

  // Load saved transform
  const savedTransform = localStorage.getItem('aethelnet_canvas_transform')
  if (savedTransform) {
    try {
      const { x, y, k } = JSON.parse(savedTransform)
      svg.call(d3ZoomInstance.transform as any, d3.zoomIdentity.translate(x, y).scale(k))
    } catch(e) {}
  }
  
  svg.on("dblclick.zoom", null)
}

// Node Interactions
let activeDragNode: Node | null = null

function unpinNode(node: Node) {
  node.fx = null
  node.fy = null
  if (simulation) {
    simulation.alphaTarget(0.3).restart()
    setTimeout(() => simulation.alphaTarget(0), 1000)
  }
  saveGraphPhysics() // Save the 'null' state to the backend
}

let connectingSource: Node | null = null

function startDrag(event: MouseEvent | TouchEvent, node: Node) {
  // Shift + Click logic for manual connecting
  const isShift = 'shiftKey' in event && event.shiftKey
  const isCtrl = 'metaKey' in event && (event.metaKey || event.ctrlKey)
  
  if (isShift) {
    // Prevent text selection while shift-clicking
    if (event.cancelable) event.preventDefault()
    
    if (!connectingSource) {
      connectingSource = node
      node.isDragged = true 
    } else {
      if (connectingSource.id !== node.id) {
        createManualEdge(connectingSource.id, node.id)
      }
      connectingSource.isDragged = false
      connectingSource = null
    }
    return
  }

  // Node Selection Logic
  if (isCtrl) {
    if (selectedNodeIds.value.has(node.id)) {
      selectedNodeIds.value.delete(node.id)
      node.isSelected = false
    } else {
      selectedNodeIds.value.add(node.id)
      node.isSelected = true
    }
  } else {
    if (!selectedNodeIds.value.has(node.id)) {
      selectedNodeIds.value.clear()
      nodes.value.forEach(n => n.isSelected = false)
      selectedNodeIds.value.add(node.id)
      node.isSelected = true
    }
  }

  activeDragNode = node
  node.isDragged = true
  
  if (simulation) {
    simulation.alphaTarget(0.3).restart()
  }
  
  const initialClientX = 'touches' in event ? event.touches[0].clientX : (event as MouseEvent).clientX
  const initialClientY = 'touches' in event ? event.touches[0].clientY : (event as MouseEvent).clientY
  const rect = canvasContainer.value?.getBoundingClientRect()
  const offsetX = rect ? rect.left : 0
  const offsetY = rect ? rect.top : 0
  const { x: tx, y: ty, k } = globalTransform
  
  const initialMouseX = (initialClientX - offsetX - tx) / k
  const initialMouseY = (initialClientY - offsetY - ty) / k
  const dragOffsetX = (node.x || 0) - initialMouseX
  const dragOffsetY = (node.y || 0) - initialMouseY
  
  const moveHandler = (e: MouseEvent | TouchEvent) => {
    if (!activeDragNode) return
    const clientX = 'touches' in e ? e.touches[0].clientX : e.clientX
    const clientY = 'touches' in e ? e.touches[0].clientY : e.clientY
    
    // Reverse the projection to find raw x/y
    const currentMouseX = (clientX - offsetX - tx) / k
    const currentMouseY = (clientY - offsetY - ty) / k
    
    // Set both the fixed coordinates and current coordinates so the simulation knows
    activeDragNode.fx = currentMouseX + dragOffsetX
    activeDragNode.fy = currentMouseY + dragOffsetY
    activeDragNode.x = activeDragNode.fx
    activeDragNode.y = activeDragNode.fy
    
    if (physicsWorker) {
      physicsWorker.postMessage({
        type: 'DRAG',
        payload: {
          id: activeDragNode.id,
          fx: activeDragNode.fx,
          fy: activeDragNode.fy
        }
      })
    }
    
    // We already keep the simulation hot from startDrag, no need to restart on every move
    // which causes massive lag on large graphs.
    updateProjection()
  }
  
  const endHandler = () => {
    if (activeDragNode) {
      activeDragNode.isDragged = false
      if (physicsWorker) {
        physicsWorker.postMessage({
          type: 'DRAG',
          payload: {
            id: activeDragNode.id,
            fx: null,
            fy: null
          }
        })
      }
      activeDragNode = null
      if (simulation) {
        simulation.alphaTarget(0)
      }
      saveGraphPhysics()
    }
    window.removeEventListener('mousemove', moveHandler)
    window.removeEventListener('touchmove', moveHandler)
    window.removeEventListener('mouseup', endHandler)
    window.removeEventListener('touchend', endHandler)
  }
  
  window.addEventListener('mousemove', moveHandler, { passive: false })
  window.addEventListener('touchmove', moveHandler, { passive: false })
  window.addEventListener('mouseup', endHandler)
  window.addEventListener('touchend', endHandler)
}

function onBackgroundMouseDown(e: MouseEvent) {
  let clientX = e.clientX
  let clientY = e.clientY
  
  if ((e as any).touches && (e as any).touches.length > 0) {
    clientX = (e as any).touches[0].clientX
    clientY = (e as any).touches[0].clientY
  }
  
  let hitNode = null
  
  if (threeRenderer) {
    const rect = canvasContainer.value?.getBoundingClientRect()
    if (rect) {
      const clickX = clientX - rect.left
      const clickY = clientY - rect.top
      hitNode = threeRenderer.raycastHover(clickX, clickY)
    }
    
    if (hitNode && !hitNode.isManual) {
      hitNode.isExpanded = true
      hitNode.isManual = true
      triggerRef(nodes)
      startDrag(e, hitNode)
      return // We clicked a WebGL node!
    }
  }

  // If clicking on the background (not a node), clear selection
  if (!e.shiftKey) {
    selectedNodeIds.value.clear()
    nodes.value.forEach(n => n.isSelected = false)
    return
  }
  
  // Shift + Drag for Box Selection
  isBoxSelecting.value = true
  const rect = canvasContainer.value?.getBoundingClientRect()
  const offsetX = rect ? rect.left : 0
  const offsetY = rect ? rect.top : 0
  
  boxStart.value = { x: e.clientX - offsetX, y: e.clientY - offsetY }
  boxCurrent.value = { ...boxStart.value }
  
  const moveHandler = (moveEvt: MouseEvent) => {
    boxCurrent.value = { x: moveEvt.clientX - offsetX, y: moveEvt.clientY - offsetY }
  }
  
  const upHandler = () => {
    isBoxSelecting.value = false
    
    // Calculate selection bounds
    const minX = Math.min(boxStart.value.x, boxCurrent.value.x)
    const maxX = Math.max(boxStart.value.x, boxCurrent.value.x)
    const minY = Math.min(boxStart.value.y, boxCurrent.value.y)
    const maxY = Math.max(boxStart.value.y, boxCurrent.value.y)
    
    // Find nodes inside
    selectedNodeIds.value.clear()
    nodes.value.forEach(node => {
      if (node.sx === undefined || node.sy === undefined) return
      if (node.sx >= minX && node.sx <= maxX && node.sy >= minY && node.sy <= maxY) {
        selectedNodeIds.value.add(node.id)
        node.isSelected = true
      } else {
        node.isSelected = false
      }
    })
    
    window.removeEventListener('mousemove', moveHandler)
    window.removeEventListener('mouseup', upHandler)
  }
  
  window.addEventListener('mousemove', moveHandler)
  window.addEventListener('mouseup', upHandler)
}

function hasAppUI(node: any) {
  if (!node) return false
  
  if (node.source_tag) {
    const tag = node.source_tag.toLowerCase()
    if (tag === 'html' || tag === 'render_html' || tag === 'render' || tag === 'app') {
      return true
    }
  }
  
  let meta = node.meta_data
  if (typeof meta === 'string') {
    try { meta = JSON.parse(meta) } catch(e) { return false }
  }
  return meta && meta.ui_template && meta.ui_template.trim().length > 0
}

async function injectSeed() {
  const text = seedInput.value.trim()
  if (!text) return
  
  const tempId = 'seed_' + Date.now()
  try {
    const url = API_BASE ? `${API_BASE}/lgnn/node` : '/api/lgnn/node';
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        id: tempId,
        text_content: text,
        source_tag: "injection",
        connections: [],
        parent_id: currentParentId.value || 'root'
      })
    })
    
    if (!response.ok) {
        console.error("Injection failed HTTP status:", response.status)
        return
    }
    
    seedInput.value = ''
    await fetchGraphData()
  } catch (err) {
    console.error("Injection failed:", err)
  }
}

const manualLocalEdges = ref<Link[]>([])

async function createManualEdge(sourceId: string, targetId: string) {
  try {
    const url = API_BASE ? `${API_BASE}/lgnn/edge` : '/api/lgnn/edge';
    await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        source: sourceId,
        target: targetId,
        weight: 1.0
      })
    })
    
    // Update locally immediately
    const sourceNode = nodes.value.find(n => n.id === sourceId)
    const targetNode = nodes.value.find(n => n.id === targetId)
    
    if (sourceNode && targetNode) {
      const edgeExists = links.value.some(l => 
        ((l.source as Node).id || l.source) === sourceId && ((l.target as Node).id || l.target) === targetId
      )
      
      if (!edgeExists) {
        const newEdge: Link = { source: sourceNode, target: targetNode, weight: 1.0, tags: [] }
        manualLocalEdges.value.push(newEdge)
        links.value.push(newEdge)
        
        if (simulation) {
          const d3Links = links.value.map(l => ({ 
            source: (l.source as Node).id ?? l.source, 
            target: (l.target as Node).id ?? l.target, 
            weight: l.weight 
          }))
          simulation.force("link", d3.forceLink(d3Links).id((d: any) => d.id).distance(linkDistance))
          simulation.alpha(0.3).restart()
        }
        updateProjection()
      }
    }
  } catch (err) {
    console.error("Failed to create manual edge", err)
  }
}

async function deleteLink(link: any) {
  const sourceId = link.source.id ?? link.source
  const targetId = link.target.id ?? link.target
  
  // Filter locally
  manualLocalEdges.value = manualLocalEdges.value.filter(l => {
    const sId = (l.source as Node).id ?? l.source
    const tId = (l.target as Node).id ?? l.target
    return !(sId === sourceId && tId === targetId) && !(sId === targetId && tId === sourceId)
  })
  
  links.value = links.value.filter(l => {
    const sId = (l.source as Node).id ?? l.source
    const tId = (l.target as Node).id ?? l.target
    return !(sId === sourceId && tId === targetId) && !(sId === targetId && tId === sourceId)
  })
  
  if (simulation) {
    const d3Links = links.value.map(l => ({ 
      source: (l.source as Node).id ?? l.source, 
      target: (l.target as Node).id ?? l.target, 
      weight: l.weight 
    }))
    simulation.force("link", d3.forceLink(d3Links).id((d: any) => d.id).distance(linkDistance))
    simulation.alphaTarget(0.3).restart()
    setTimeout(() => simulation.alphaTarget(0), 1000)
  }
  updateProjection()
  
  const url = API_BASE ? `${API_BASE}/lgnn/edge/${sourceId}/${targetId}` : `/api/lgnn/edge/${sourceId}/${targetId}`
  fetch(url, { method: 'DELETE' }).catch(e => console.error(e))
}

async function updateLinkWeight({ link, weight }: { link: any, weight: number }) {
  link.weight = weight
  
  // Update local edge if it exists
  const sourceId = link.source.id ?? link.source
  const targetId = link.target.id ?? link.target
  const localMatch = manualLocalEdges.value.find(l => {
    const sId = (l.source as Node).id ?? l.source
    const tId = (l.target as Node).id ?? l.target
    return (sId === sourceId && tId === targetId) || (sId === targetId && tId === sourceId)
  })
  if (localMatch) {
    localMatch.weight = weight
  }

  // Update physics
  if (simulation) {
    const d3Links = links.value.map(l => ({ 
      source: (l.source as Node).id ?? l.source, 
      target: (l.target as Node).id ?? l.target, 
      weight: l.weight 
    }))
    simulation.force("link", d3.forceLink(d3Links).id((d: any) => d.id).distance(linkDistance))
    simulation.alphaTarget(0.3).restart()
    setTimeout(() => simulation.alphaTarget(0), 1000)
  }
  updateProjection()

  // Network call
  const url = API_BASE ? `${API_BASE}/lgnn/edge/${encodeURIComponent(sourceId)}/${encodeURIComponent(targetId)}` : `/api/lgnn/edge/${encodeURIComponent(sourceId)}/${encodeURIComponent(targetId)}`
  try {
    await fetch(url, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ weight })
    })
  } catch (e) {
    console.error("Failed to update edge weight", e)
  }
}

async function spawnContextualGuide(targetNode: any) {
  if (!targetNode) return
  
  const id = 'pattern_matcher_' + Date.now()
  const payload = {
    id,
    text_content: targetNode.source_tag || targetNode.id,
    source_tag: 'pattern_matcher',
    x: targetNode.x + 300,
    y: targetNode.y,
    connections: []
  }

  try {
    await fetch(`${API_BASE}/lgnn/node`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
    
    // Automatically connect the guide to the target node
    await fetch(`${API_BASE}/lgnn/edge`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        source: id,
        target: targetNode.id,
        weight: 1.0,
        tags: ['tutorial']
      })
    })

    // Graph will refresh on its own
  } catch (e) {
    console.error("Failed to spawn guide:", e)
  }
}

async function spawnApp(appName: string) {
  if (appName === 'MacroVision') {
    emit('open3d')
    return
  }
  
  if (appName === 'Operator' || appName === 'Prism') {
    try {
      const url = API_BASE ? `${API_BASE}/lgnn/node` : '/api/lgnn/node';
      const nodeTypeInfo = appName === 'Operator' 
        ? {
            id: 'OPERATOR_' + Date.now(),
            text_content: "",
            meta_data: JSON.stringify({
              inputs: [{name: "DATA_IN", type: "string"}],
              outputs: [{name: "COMPUTE_OUT", type: "tensor"}]
            })
          }
        : {
            id: 'PRISM_' + Date.now(),
            text_content: "",
            meta_data: JSON.stringify({
              inputs: [{name: "COMPUTE_IN", type: "tensor"}],
              outputs: [{name: "MATERIALIZED", type: "any"}]
            })
          };

      await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          id: nodeTypeInfo.id,
          text_content: nodeTypeInfo.text_content,
          node_type: "macro",
          is_grounded: true,
          confidence: 1.0,
          meta_data: nodeTypeInfo.meta_data,
          source_tag: "manual",
          connections: []
        })
      })
      await fetchGraphData()
      // Make sure newly spawned nodes start expanded
      const spawned = nodes.value.find(n => n.id === nodeTypeInfo.id)
      if (spawned) {
        spawned.isExpanded = true
        saveExpandedState()
        triggerRef(nodes)
        refreshSimulation()
      }
      return
    } catch (err) {
      console.error("Spawn macro failed:", err)
    }
  }

  const content = appName === 'Text' ? 'New thought...' : (appName === 'LgnnChat' ? 'LGNN Bridge Session' : `APP:${appName}`)
  const tempId = 'manual_' + Date.now()
  let sourceTag = 'manual'
  if (appName === 'Spider') sourceTag = 'spider'
  else if (appName === 'ApiGateway') sourceTag = 'api_gateway'
  else if (appName === 'Audio') sourceTag = 'audio'
  else if (appName === 'Synth') sourceTag = 'synth'
  else if (appName === 'Lua') sourceTag = 'lua'
  else if (appName === 'Vitals') sourceTag = 'vitals'
  else if (appName === 'Vault') sourceTag = 'vault'
  else if (appName === 'Webhook') sourceTag = 'webhook'
  else if (appName === 'ObjDecoder') sourceTag = 'obj_decoder'
  else if (appName === 'OmniDecoder') sourceTag = 'omni_decoder'
  else if (appName === 'AuraStream') sourceTag = 'aurastream'
  else if (appName === 'Prisma') sourceTag = 'prisma'
  else if (appName === 'Fusion') sourceTag = 'fusion'
  else if (appName === 'Repulsor') sourceTag = 'repulsor'
  else if (appName === 'Graviton') sourceTag = 'graviton'
  else if (appName === 'EntropyChamber') sourceTag = 'entropy'
  else if (appName === 'Incubator') sourceTag = 'incubator'
  else if (appName === 'Chronosphere') sourceTag = 'chronosphere'
  else if (appName === 'Subgraph') sourceTag = 'subgraph'
  else if (appName === 'Kreativfabrik') sourceTag = 'kreativfabrik'
  else if (appName === 'PatternMatcher') sourceTag = 'pattern_matcher'
  else if (appName === 'Html') sourceTag = 'html'
  else if (appName === 'LgnnChat') sourceTag = 'lgnn_chat'
  else if (appName === 'Render') sourceTag = 'render'
  else if (appName === 'Identity') sourceTag = 'identity'
  else if (appName === 'LgnnChat') sourceTag = 'lgnn_chat'
  
  try {
    const url = API_BASE ? `${API_BASE}/lgnn/node` : '/api/lgnn/node';
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        id: tempId,
        text_content: content,
        source_tag: sourceTag,
        connections: [],
        parent_id: currentParentId.value || 'root'
      })
    })
    if (response.ok) {
      await fetchGraphData()
      const spawned = nodes.value.find((n: any) => n.id === tempId)
      if (spawned) {
        spawned.x = (window.innerWidth / 2 - globalTransform.x) / globalTransform.k
        spawned.y = (window.innerHeight / 2 - globalTransform.y) / globalTransform.k
        spawned.isExpanded = true
        spawned.isManual = true
        triggerRef(nodes)
        refreshSimulation()
      }
      return tempId
    }
  } catch (err) {
    console.error("Spawn failed:", err)
  }
  return null
}

async function onDropCanvas(event: DragEvent) {
  const dataStr = event.dataTransfer?.getData('application/json')
  if (!dataStr) return
  
  try {
    const data = JSON.parse(dataStr)
    if (data.type === 'checkpoint' && data.hash) {
      // Spawn checkpoint as a subgraph node
      const url = API_BASE ? `${API_BASE}/lgnn/snapshot/spawn_as_subgraph` : '/api/lgnn/snapshot/spawn_as_subgraph'
      const res = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          commit_hash: data.hash,
          target_parent_id: currentParentId.value || 'root'
        })
      })
      if (res.ok) {
        // Wait briefly for DB to be queried, then refresh
        setTimeout(fetchGraphData, 500)
      }
    }
  } catch (err) {
    console.error("Drop failed:", err)
  }
}

function handleResize() {
  if (canvasContainer.value) {
    width = canvasContainer.value.clientWidth
    height = canvasContainer.value.clientHeight
  }
}

let pollInterval: any = null

onMounted(() => {
  loadCustomBlueprints();
  handleResize()
  window.addEventListener('resize', handleResize)
  setupZoomAndPan()
  fetchGraphData()
  
  if (webglCanvas.value) {
    // Pass links.value initially, we'll update to visibleLinks during fetchGraphData
    threeRenderer = new ThreeGraphRenderer(webglCanvas.value, visibleNodes.value, links.value, globalTransform)
    
    // When a user clicks a WebGL dot, we upgrade it to a fully interactive DOM node!
    threeRenderer.onClick = (node: any) => {
      node.isExpanded = true
      node.isManual = true // This forces it into domNodes computed property
      
      selectedNodeIds.value.clear()
      selectedNodeIds.value.add(node.id)
      
      triggerRef(nodes)
      
      // Optionally zoom/pan to it
      activeDragNode = node
      
      // Only open AppWindowOverlay if it explicitly is an app window
      try {
        const meta = typeof node.meta_data === 'string' ? JSON.parse(node.meta_data) : (node.meta_data || {})
        if (meta.ui_template || node.label?.startsWith('APP:')) {
          activeAppNode.value = node
        }
      } catch (e) {}
    }
  }
  
  // Keyboard listeners for canvas actions
  window.addEventListener('keydown', handleKeyDown)
  window.addEventListener('keyup', handleKeyUp)
  
  // Ctrl+K Listener
  window.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
      e.preventDefault()
      showCommandPalette.value = true
    }
  })
  
  // Poll backend for graph updates periodically (only if websocket is not open)
  pollInterval = setInterval(() => {
    if (!activeDragNode && (!ws.value || ws.value.readyState !== WebSocket.OPEN)) {
      fetchGraphData()
    }
    propagateDataFlow()
  }, 3000) 
})

watch(visibleNodes, (newNodes) => {
  if (threeRenderer) {
    threeRenderer.updateData(newNodes, threeRenderer.links)
  }
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  window.removeEventListener('keydown', handleKeyDown)
  window.removeEventListener('keyup', handleKeyUp)
  if (animationFrameId) cancelAnimationFrame(animationFrameId)
  if (simulation) simulation.stop()
  if (pollInterval) clearInterval(pollInterval)
  if (threeRenderer) {
    threeRenderer.dispose()
  }
})

function handleKeyDown(e: KeyboardEvent) {
  // Ignore if typing in an input
  if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return
  
  if (e.code === 'Space' && !e.repeat) {
    isSpacePressed.value = true
    spaceKeyDownTime = Date.now()
    e.preventDefault() // Prevent scrolling down
  }
  
  if (e.key === 't' || e.key === 'T') {
    showToolbox.value = !showToolbox.value
  }
  
  if (e.key === 'Escape') {
    selectedNodeIds.value.clear()
    nodes.value.forEach(n => n.isSelected = false)
    showCommandPalette.value = false
  }
  
  if (e.key === 'Delete' || e.key === 'Backspace') {
    if (selectedNodeIds.value.size > 0) {
      deleteSelectedNodes()
    }
  }
  
  // Arrow key navigation for nodes
  if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(e.key)) {
    e.preventDefault()
    
    let currentSelected: any = null
    if (selectedNodeIds.value.size > 0) {
      const id = Array.from(selectedNodeIds.value)[0]
      currentSelected = visibleNodes.value.find(n => n.id === id)
    }
    
    if (!currentSelected && visibleNodes.value.length > 0) {
      // Select the first node closest to center if none is selected
      const cx = 0, cy = 0
      let closest = visibleNodes.value[0]
      let minDist = Infinity
      visibleNodes.value.forEach(n => {
        const d = (n.x||0)*(n.x||0) + (n.y||0)*(n.y||0)
        if (d < minDist) { minDist = d; closest = n }
      })
      selectedNodeIds.value.clear()
      selectedNodeIds.value.add(closest.id)
      closest.isSelected = true
      return
    }
    
    if (currentSelected) {
      const cx = currentSelected.x || 0
      const cy = currentSelected.y || 0
      
      let bestMatch = null
      let bestScore = Infinity
      
      visibleNodes.value.forEach(n => {
        if (n.id === currentSelected.id) return
        
        const nx = n.x || 0
        const ny = n.y || 0
        const dx = nx - cx
        const dy = ny - cy
        
        let isValidDirection = false
        if (e.key === 'ArrowRight' && dx > Math.abs(dy)) isValidDirection = true
        if (e.key === 'ArrowLeft' && -dx > Math.abs(dy)) isValidDirection = true
        if (e.key === 'ArrowDown' && dy > Math.abs(dx)) isValidDirection = true
        if (e.key === 'ArrowUp' && -dy > Math.abs(dx)) isValidDirection = true
        
        if (isValidDirection) {
          const dist = Math.sqrt(dx*dx + dy*dy)
          if (dist < bestScore) {
            bestScore = dist
            bestMatch = n
          }
        }
      })
      
      if (bestMatch) {
        selectedNodeIds.value.clear()
        nodes.value.forEach(n => n.isSelected = false)
        selectedNodeIds.value.add((bestMatch as any).id)
        ;(bestMatch as any).isSelected = true
        
        // Announce to screen reader
        const announcer = document.getElementById('a11y-announcer')
        if (announcer) {
          announcer.textContent = `Selected node ${(bestMatch as any).label || (bestMatch as any).id}`
        }
      }
    }
  }
  
  // Enter key to expand/collapse selected node
  if (e.key === 'Enter') {
    if (selectedNodeIds.value.size === 1) {
      const id = Array.from(selectedNodeIds.value)[0]
      const currentSelected = visibleNodes.value.find(n => n.id === id)
      if (currentSelected) {
        currentSelected.isExpanded = !currentSelected.isExpanded
        if (currentSelected.isExpanded) currentSelected.isManual = true
        triggerRef(nodes)
        e.preventDefault()
      }
    }
  }
}

function handleKeyUp(e: KeyboardEvent) {
  if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return

  if (e.code === 'Space') {
    isSpacePressed.value = false
    const duration = Date.now() - spaceKeyDownTime
    // If it was a quick tap, toggle the command palette (our "Super" drawer)
    if (duration < 300) {
      showCommandPalette.value = !showCommandPalette.value
    }
  }
}

async function deleteSelectedNodes() {
  const idsToDelete = Array.from(selectedNodeIds.value)
  // Optimistically remove from frontend
  nodes.value = nodes.value.filter(n => !selectedNodeIds.value.has(n.id))
  links.value = links.value.filter(l => {
    const sId = typeof l.source === 'string' ? l.source : (l.source as Node).id
    const tId = typeof l.target === 'string' ? l.target : (l.target as Node).id
    return !selectedNodeIds.value.has(sId) && !selectedNodeIds.value.has(tId)
  })
  
  selectedNodeIds.value.clear()
  updateProjection()
  
  for (const id of idsToDelete) {
    permanentlyDeletedNodes.add(id)
    try {
      const url = API_BASE ? `${API_BASE}/lgnn/node/${encodeURIComponent(id)}` : `/api/lgnn/node/${encodeURIComponent(id)}`
      await fetch(url, { method: 'DELETE' })
    } catch (e) { console.error(e) }
  }
  
  await fetchGraphData()
}

</script>

<style scoped>
/* Dream State Trance Mode */
.dream-mode-active {
  background-color: #0d0d0d !important;
  transition: background-color 2s ease-in-out;
}

.dream-mode-active * {
  color: #F4F4F0 !important;
  border-color: #F4F4F0 !important;
}

.dream-mode-active .base-link {
  stroke: #4CAF50 !important;
  opacity: 0.8 !important;
  filter: drop-shadow(0 0 8px #4CAF50);
}

.dream-mode-active .concept-node {
  background: rgba(0, 0, 0, 0.8) !important;
  box-shadow: 0 0 20px #4CAF50 !important;
}

.dream-btn {
  background: transparent;
  color: #1A1A1A;
  border: 2px solid #1A1A1A;
}

.dream-btn.is-dreaming {
  background: #4CAF50 !important;
  color: #fff !important;
  border-color: #4CAF50 !important;
  animation: pulse-trance 1.5s infinite alternate;
}

@keyframes pulse-trance {
  0% { transform: scale(1); box-shadow: 0 0 10px #4CAF50; }
  100% { transform: scale(1.05); box-shadow: 0 0 30px #4CAF50; }
}

.webgl-background-canvas {
  position: absolute;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  z-index: 0;
  pointer-events: none;
}

.webgl-tooltip {
  position: fixed;
  background: rgba(10, 10, 15, 0.85);
  border: 1px solid var(--color-accent);
  border-radius: 8px;
  padding: 12px;
  pointer-events: none;
  z-index: 10000;
}

.subgraph-breadcrumb {
  position: absolute;
  top: 80px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 16px;
  background: rgba(10, 10, 15, 0.8);
  border: 1px solid var(--color-accent);
  border-radius: 20px;
  padding: 8px 16px;
  z-index: 50;
  backdrop-filter: blur(10px);
  box-shadow: 0 4px 20px rgba(0, 243, 255, 0.15);
}

.breadcrumb-back-btn {
  background: transparent;
  color: var(--color-accent);
  border: 1px solid var(--color-accent);
  padding: 4px 12px;
  border-radius: 12px;
  font-family: var(--font-family-mono);
  font-size: 11px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.breadcrumb-back-btn:hover {
  background: var(--color-accent);
  color: var(--color-bg-primary);
}

.breadcrumb-path {
  font-family: var(--font-family-mono);
  color: var(--color-text-main);
  font-size: 13px;
  font-weight: bold;
}

.tooltip-title {
  font-weight: bold;
  color: var(--color-accent);
  margin-bottom: 4px;
}
.tooltip-type {
  font-size: 11px;
  color: #888;
  text-transform: uppercase;
  margin-bottom: 6px;
}
.tooltip-content {
  font-size: 12px;
  color: #ccc;
  margin-bottom: 6px;
}
.tooltip-hint {
  font-size: 10px;
  color: var(--color-accent);
  opacity: 0.7;
  font-style: italic;
}

.canvas-nav-controls {
  position: absolute;
  bottom: 24px;
  right: 24px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  z-index: 2000;
  background: var(--color-bg-panel);
  padding: 8px;
  border-radius: 8px;
  border: 1px solid var(--border-color);
  box-shadow: 0 4px 15px rgba(0,0,0,0.4);
}

.nav-btn {
  background: transparent;
  border: none;
  color: var(--color-text-main);
  font-size: 18px;
  width: 32px;
  height: 32px;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.nav-btn:hover {
  background: var(--color-accent);
  color: #fff;
}

.space-pan-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 9998;
  cursor: grab;
}
.space-pan-overlay:active {
  cursor: grabbing;
}

.lgnn-container-white {
  width: 100%;
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--color-bg-primary);
  color: var(--color-text-main);
  overflow: hidden;
  position: relative;
  font-family: 'Inter', -apple-system, sans-serif;
  box-sizing: border-box;
}

.header {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  padding: 32px 30px;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  z-index: 10;
  pointer-events: none;
}

.header-left, .header-right {
  pointer-events: auto;
}

h2 {
  font-size: 1.6rem;
  font-weight: 800;
  letter-spacing: -1px;
  margin: 0 0 8px 0;
  color: var(--color-accent);
  text-transform: uppercase;
}

.status-badge {
  font-size: 0.75rem;
  padding: 4px 10px;
  background: var(--color-text-main);
  border: 2px solid var(--border-color);
  color: var(--color-bg-primary);
  border-radius: 0;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.toolbox {
  position: absolute;
  top: 80px;
  left: 20px;
  width: 220px;
  background: var(--color-bg-primary);
  border: 2px solid var(--border-color);
  box-shadow: var(--shadow-node);
  display: flex;
  flex-direction: column;
  padding: 12px;
  z-index: 100;
}

.toolbox-header {
  font-weight: 900;
  font-size: 14px;
  text-transform: uppercase;
  margin-bottom: 12px;
  border-bottom: 2px solid var(--border-color);
  padding-bottom: 4px;
}

.tool-btn {
  background: transparent;
  border: 2px solid var(--border-color);
  color: var(--color-text-main);
  font-family: 'Inter', monospace;
  font-weight: 800;
  font-size: 12px;
  padding: 8px;
  margin-bottom: 8px;
  cursor: pointer;
  text-transform: uppercase;
  transition: all 0.1s ease;
  box-shadow: 2px 2px 0px var(--border-color);
}

.tool-btn:hover {
  transform: translate(-2px, -2px);
  box-shadow: 4px 4px 0px var(--border-color);
}

.tool-btn:active {
  transform: translate(2px, 2px);
  box-shadow: 0px 0px 0px var(--border-color);
}

.toolbox-divider {
  height: 2px;
  background: var(--border-color);
  margin: 8px 0;
}

.canvas-area {
  flex: 1;
  position: relative;
  overflow: hidden;
  cursor: crosshair;
  user-select: none;
}

.canvas-area:active {
  cursor: grabbing;
}

.links-layer {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.synapse-link {
  stroke: var(--border-color);
  stroke-opacity: 1.0;
  stroke-linecap: square;
}

.concept-node {
  position: absolute;
  top: 0;
  left: 0;
  will-change: transform;
  min-width: 180px;
  max-width: 280px;
  background: var(--color-bg-glass);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  box-shadow: var(--shadow-glass);
  padding: 16px 20px;
  cursor: grab;
  user-select: none;
  transform-origin: center center;
  color: var(--color-text-main);
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.concept-node.is-expanded {
  min-width: 600px;
  min-height: 400px;
  max-width: 800px;
  z-index: 3000 !important;
  cursor: default;
}

.node-content {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.node-text {
  font-size: 12px;
  line-height: 1.4;
  color: #333;
  margin-top: 4px;
}

.concept-node:hover {
  background: var(--color-accent-active);
  z-index: 2000 !important;
}

.concept-node.autonomous-node {
  background: rgba(26, 26, 26, 0.9);
  border: 2px dashed #F2C12E;
  box-shadow: 4px 4px 0px rgba(242, 193, 46, 0.3);
  color: #00FF41;
  opacity: 0.9;
}

.concept-node.autonomous-node .node-label {
  color: #F2C12E;
}

.concept-node.autonomous-node .node-text {
  color: #00FF41;
  font-family: 'Space Mono', monospace;
}

.concept-node.autonomous-node:hover {
  background: #1A1A1A;
  border-style: solid;
  opacity: 1;
  z-index: 2000 !important;
}

.concept-node.is-dragged {
  cursor: grabbing;
  box-shadow: 8px 8px 0px #1A1A1A;
  border-color: var(--color-accent);
  background: var(--color-bg-primary);
}

.concept-node.is-selected {
  border-color: var(--color-accent-active);
  box-shadow: 4px 4px 0px var(--color-accent-active);
}

.selection-box-overlay {
  position: absolute;
  background: rgba(224, 60, 49, 0.1);
  border: 1px dashed var(--color-accent);
  pointer-events: none;
  z-index: 9999;
}

.node-content {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.node-label {
  font-family: var(--font-family);
  font-weight: 800;
  font-size: 1.05rem;
  line-height: 1.3;
  color: var(--color-text-main);
  text-transform: uppercase;
  word-wrap: break-word;
}

.metrics-bar {
  display: flex;
  gap: 8px;
  font-size: 0.7rem;
  color: var(--color-text-main);
  flex-wrap: wrap;
}

.metric {
  background: transparent;
  border: 2px solid var(--border-color);
  padding: 4px 8px;
  border-radius: 0;
  font-weight: 800;
  color: var(--color-text-main);
}

.fast-mode {
  padding: 12px;
  background: var(--color-bg-primary);
  border: 1px solid var(--border-color);
  box-shadow: 2px 2px 0px rgba(0,0,0,0.5);
  min-width: 180px;
  max-width: 250px;
}

.fast-actions {
  margin-top: 8px;
  display: flex;
  justify-content: flex-end;
}

.expand-btn {
  background: transparent;
  border: 1px dashed var(--color-text-main);
  color: var(--color-text-main);
  padding: 2px 8px;
  font-size: 10px;
  font-weight: 900;
  cursor: pointer;
  text-transform: uppercase;
}

.expand-btn:hover {
  background: var(--color-text-main);
  color: var(--color-bg-primary);
}

.node-expand-enter-active,
.node-expand-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
}

.node-expand-enter-from,
.node-expand-leave-to {
  opacity: 0;
  transform: scale(0.95);
}

/* Injection Stream (Glassmorphism) */
.injection-stream {
  position: absolute;
  box-shadow: 0 -8px 0px rgba(26, 26, 26, 0.1);
}

.stream-prompt {
  font-family: 'Space Mono', monospace;
  color: var(--color-text-main);
  font-size: 1.1rem;
  font-weight: 900;
  white-space: nowrap;
}

.stream-input {
  flex: 1;
  background: #FFF;
  border: 2px solid var(--border-color);
  color: var(--color-text-main);
  font-family: 'Space Mono', monospace;
  font-size: 1.1rem;
  font-weight: 600;
  padding: 12px 16px;
  outline: none;
  box-shadow: 4px 4px 0px var(--color-text-main);
}

.stream-input:focus {
  box-shadow: 8px 8px 0px var(--color-text-main);
  transform: translate(-4px, -4px);
}

.stream-input::placeholder {
  color: #999;
  font-weight: 400;
}

.audio-toggle-btn {
  background: var(--color-bg-primary);
  border: 2px solid var(--border-color);
  color: var(--color-text-main);
  padding: 8px 16px;
  border-radius: 0;
  font-family: 'Courier New', Courier, monospace;
  font-weight: 800;
  font-size: 0.85rem;
  cursor: pointer;
  margin-right: 12px;
  box-shadow: var(--shadow-node);
}

.audio-toggle-btn:hover {
  background: var(--color-accent-hover);
  color: var(--color-bg-primary);
}

.audio-toggle-btn.active {
  background: var(--color-accent);
  color: var(--color-bg-primary);
}

.inject-btn {
  background: var(--color-text-main);
  border: 2px solid var(--border-color);
  color: var(--color-bg-primary);
  padding: 12px 24px;
  border-radius: 0;
  font-family: 'Space Mono', monospace;
  font-weight: 900;
  font-size: 1.1rem;
  cursor: pointer;
  box-shadow: 4px 4px 0px var(--color-bg-primary);
  transition: all 0.1s;
}

.inject-btn:hover:not(:disabled) {
  background: var(--color-accent);
  box-shadow: 6px 6px 0px #FFF;
  transform: translate(-2px, -2px);
}

.inject-btn:active:not(:disabled) {
  box-shadow: 0px 0px 0px #FFF;
  transform: translate(4px, 4px);
}

.inject-btn:disabled {
  background: #CCC;
  border-color: #999;
  color: #666;
  cursor: not-allowed;
}

.node-textarea {
  width: 100%;
  min-height: 80px;
  background: #FFF;
  border: 2px solid var(--border-color);
  color: var(--color-text-main);
  font-family: 'Space Mono', monospace;
  font-size: 12px;
  padding: 8px;
  resize: vertical;
  outline: none;
  box-shadow: inset 2px 2px 0px rgba(0,0,0,0.1);
}

.node-textarea.expanded {
  height: 100%;
  min-height: 200px;
  font-size: 14px;
}
.synapse-link {
  stroke: #1A1A1A;
  stroke-dasharray: 4 4;
  animation: dash 1s linear infinite;
}

@keyframes dash {
  to {
    stroke-dashoffset: -8;
  }
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border-width: 0;
}

/* Removed inline gnn-tuning-hud styles */

.cyber-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 12px;
  height: 12px;
  background: var(--color-accent);
  border-radius: 50%;
  cursor: pointer;
  box-shadow: 0 0 8px var(--color-accent);
}

/* REM Sleep UI */
.rem-sleep-overlay {
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(10, 5, 20, 0.7);
  backdrop-filter: blur(8px);
  z-index: 1500;
  display: flex;
  justify-content: center;
  align-items: center;
  pointer-events: none;
  animation: breathe 4s infinite alternate ease-in-out;
}

@keyframes breathe {
  0% { opacity: 0.8; }
  100% { opacity: 1; }
}

.rem-text {
  color: #a855f7;
  font-family: var(--font-family-mono);
  font-size: 24px;
  letter-spacing: 4px;
  text-shadow: 0 0 20px rgba(168, 85, 247, 0.8);
}

.dream-log-toast {
  position: absolute;
  top: 80px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(20, 20, 25, 0.9);
  border: 1px solid #a855f7;
  color: #fff;
  padding: 12px 24px;
  border-radius: 8px;
  font-family: var(--font-family-mono);
  font-size: 14px;
  z-index: 3000;
  box-shadow: 0 0 30px rgba(168, 85, 247, 0.4);
  animation: slideDownFade 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275) forwards;
}

@keyframes slideDownFade {
  0% { top: 40px; opacity: 0; }
  100% { top: 80px; opacity: 1; }
}

</style>
