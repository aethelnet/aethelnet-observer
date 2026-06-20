<template>
  <div class="toolbox" :style="toolboxStyle" role="dialog" aria-label="Asset Browser" aria-modal="false">
    <div class="toolbox-top" @mousedown="startDrag" style="cursor: grab;" aria-hidden="true">
      <div class="toolbox-header">ASSET BROWSER</div>
      <button class="close-btn" @click="$emit('close')" aria-label="Close Asset Browser">×</button>
    </div>
    
    <div class="toolbox-tabs" role="tablist" aria-label="Toolbox Categories">
      <button class="tab-btn" role="tab" :aria-selected="activeTab === 'tools'" :class="{ active: activeTab === 'tools' }" @click="activeTab = 'tools'">TOOLS</button>
      <button class="tab-btn" role="tab" :aria-selected="activeTab === 'market'" :class="{ active: activeTab === 'market' }" @click="activeTab = 'market'">MARKET</button>
      <button class="tab-btn" role="tab" :aria-selected="activeTab === 'graph'" :class="{ active: activeTab === 'graph' }" @click="activeTab = 'graph'">GRAPH</button>
    </div>
    
    <div class="toolbox-scroll" role="tabpanel" :aria-label="activeTab + ' options'">
      <!-- TAB: TOOLS -->
      <template v-if="activeTab === 'tools'">
        <div class="category-group">
          <div class="category-title" style="color: #00d4ff;">PATTERN MATCHER</div>
          <button class="tool-btn" @click="$emit('spawn-app', 'PatternMatcher')">
            <span class="btn-icon">[🦂]</span> Pattern Matcher
          </button>
        </div>

        <div class="category-group">
          <div class="category-title">1. PRIMITIVES</div>
          <button class="tool-btn" @click="$emit('spawn-app', 'Text')">
            <span class="btn-icon">T</span> Text Block
          </button>
          <button class="tool-btn" @click="$emit('spawn-app', 'Script')">
            <span class="btn-icon">&lt;/&gt;</span> Python Script
          </button>
          <button class="tool-btn" @click="$emit('spawn-app', 'Render')">
            <span class="btn-icon">&lt;&gt;</span> Render / HTML
          </button>
          <button class="tool-btn" @click="$emit('spawn-app', 'Vault')">
            <span class="btn-icon">V</span> Vault
          </button>
        </div>

        <div class="category-group">
          <div class="category-title">2. EDGE SENSORS</div>
          <button class="tool-btn" @click="$emit('spawn-app', 'Spider')">
            <span class="btn-icon">[*]</span> Spider (Crawler)
          </button>
          <button class="tool-btn" @click="$emit('spawn-app', 'Webhook')">
            <span class="btn-icon">W</span> Webhook
          </button>
          <button :class="['tool-btn', 'sensor-btn', {'active': micActive}]" @click="$emit('toggle-sensor', 'mic')">
            <span class="status-dot"></span> Acoustic Input
          </button>
          <button :class="['tool-btn', 'sensor-btn', {'active': gyroActive}]" @click="$emit('toggle-sensor', 'gyro')">
            <span class="status-dot"></span> Kinematic Data
          </button>
          <button :class="['tool-btn', 'sensor-btn', {'active': gpsActive}]" @click="$emit('toggle-sensor', 'gps')">
            <span class="status-dot"></span> Spatial Location
          </button>
        </div>

        <div class="category-group">
          <div class="category-title">3. DECODERS & AI</div>
          <button class="tool-btn" @click="$emit('spawn-app', 'OmniDecoder')">
            <span class="btn-icon">[O]</span> Omni Decoder
          </button>
          <button class="tool-btn" @click="$emit('spawn-app', 'ObjDecoder')">
            <span class="btn-icon">[T]</span> Tensor Topology
          </button>
          <button class="tool-btn" @click="$emit('spawn-app', 'AuraStream')">
            <span class="btn-icon">[~]</span> AuraStream
          </button>
        </div>

        <div class="category-group">
          <div class="category-title">4. KNOWLEDGE ENGINEERING</div>
          <button class="tool-btn" @click="$emit('spawn-app', 'Prisma')">
            <span class="btn-icon">PR</span> Prisma (Research Commenter)
          </button>
          <button class="tool-btn" @click="$emit('spawn-app', 'Repulsor')">
            <span class="btn-icon">RP</span> Repulsor (Noise Filter)
          </button>
          <button class="tool-btn" @click="$emit('spawn-app', 'Graviton')">
            <span class="btn-icon">GR</span> Graviton (Attraktor)
          </button>
          <button class="tool-btn" @click="$emit('spawn-app', 'EntropyChamber')">
            <span class="btn-icon">EN</span> Entropie-Kammer
          </button>
          <button class="tool-btn" @click="$emit('spawn-app', 'Incubator')">
            <span class="btn-icon">IN</span> Inkubator
          </button>
          <button class="tool-btn" @click="$emit('spawn-app', 'Chronosphere')">
            <span class="btn-icon">CH</span> Chronosphäre
          </button>
          <button class="tool-btn" @click="$emit('spawn-app', 'Fusion')">
            <span class="btn-icon">FU</span> Fusions-Reaktor
          </button>
        </div>

        <div class="category-group">
          <div class="category-title">5. SYSTEM & META</div>
          <button class="tool-btn" @click="$emit('toggle-forge')" style="color: #E03C31;">
            <span class="btn-icon">F</span> The Forge (OS Builder)
          </button>
          <button class="tool-btn" @click="$emit('toggle-diary')" style="color: #FF5722;">
            <span class="btn-icon">D</span> The Diary (Logs)
          </button>
          <button class="tool-btn" @click="$emit('spawn-anomaly')">
            <span class="btn-icon">O</span> Anomaly
          </button>
        </div>
      </template>

      <!-- TAB: MARKET -->
      <template v-if="activeTab === 'market'">
        <div class="market-search">
          <span class="search-icon">[*]</span>
          <input 
            v-model="marketSearchQuery" 
            placeholder="Search Aethelnet Store..." 
            class="market-search-input"
          />
        </div>
        


        <template v-if="Object.keys(groupedCustomBlueprints).length > 0">
          <div v-for="(bps, category) in groupedCustomBlueprints" :key="category" class="category-group">
            <div class="category-title">{{ category }}</div>
            <div v-for="(bp, index) in bps" :key="bp.id || bp.name + index" style="position: relative; display: flex; flex-direction: column; gap: 4px; margin-bottom: 8px;">
              <div style="display: flex; align-items: center; gap: 4px;">
                <button class="tool-btn" @click="$emit('spawn-custom', bp)" :style="{ color: bp.color || 'var(--color-text-main)', flex: 1 }">
                  <span class="btn-icon">B</span> {{ bp.name.replace('APP:', '') }}
                </button>
                <button class="delete-bp-btn" @click.stop="$emit('delete-blueprint', bp.id || bp.name)" title="Archive Blueprint">
                  [X]
                </button>
              </div>
              <div class="peer-review-widget" style="display: flex; align-items: center; gap: 8px; padding-left: 28px; font-size: 10px; color: var(--color-text-muted);">
                <span>RATING:</span>
                <input type="range" min="-1" max="1" step="1" v-model.number="bp.rating" @change="saveRating(bp)" style="width: 60px;" />
                <span :style="{color: bp.rating > 0 ? '#32d74b' : bp.rating < 0 ? '#ff453a' : 'inherit'}">
                  {{ bp.rating > 0 ? 'TRUSTED' : bp.rating < 0 ? 'FLAGGED' : 'NEUTRAL' }}
                </span>
              </div>
            </div>
          </div>
        </template>
        <div class="category-group" v-if="filteredSystemApps.length === 0 && Object.keys(groupedCustomBlueprints).length === 0 && marketResults.length === 0" style="font-size: 10px; color: var(--color-text-muted); font-style: italic;">
          No matching apps or blueprints found.
        </div>

        <!-- GLOBAL MARKETPLACE -->
        <div class="category-group" v-if="marketResults.length > 0">
          <div class="category-title">AETHELNET GLOBAL MARKET</div>
          <div v-for="bp in marketResults" :key="bp.id" style="position: relative; display: flex; flex-direction: column; gap: 4px; margin-bottom: 8px;">
            <div style="display: flex; align-items: center; gap: 4px;">
              <button class="tool-btn" @click="$emit('spawn-custom', { name: bp.title, content: bp.description, is_blueprint: true })" style="color: #00FF41; flex: 1; text-align: left;">
                <span class="btn-icon" style="animation: pulse 2s infinite;">🌐</span> {{ bp.title }}
              </button>
            </div>
            <div style="font-size: 9px; color: var(--color-text-muted); padding-left: 28px; line-height: 1.3;">
               {{ bp.description }}<br>
               <span style="color: #F2C12E">{{ bp.author }}</span> | Downloads: {{ bp.downloads }}
            </div>
          </div>
        </div>
      </template>

      <!-- TAB: GRAPH -->
      <template v-if="activeTab === 'graph'">
        <div class="category-group">
          <div class="category-title">ACTIVE NODES ({{ sortedManualNodes.length }})</div>
          <div class="nodes-list">
            <div v-for="node in sortedManualNodes" :key="node.id" class="node-list-item" @click="$emit('focus-node', node.id)">
              <div class="node-indicator" :style="{ backgroundColor: node.color || 'var(--color-accent)' }"></div>
              <div class="node-label">{{ node.label || node.id }}</div>
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { defineProps, defineEmits, ref, onUnmounted, computed, watch } from 'vue'

const props = defineProps<{
  customBlueprints: any[];
  sortedManualNodes: any[];
  micActive: boolean;
  gyroActive: boolean;
  gpsActive: boolean;
}>()

const emits = defineEmits([
  'spawn-app',
  'spawn-custom',
  'delete-blueprint',
  'focus-node',
  'toggle-diary',
  'toggle-forge',
  'toggle-sensor',
  'close'
])

const activeTab = ref('tools')

const marketSearchQuery = ref('')

const posX = ref(20)
const posY = ref(20)
let isDragging = false
let dragStartX = 0
let dragStartY = 0

const toolboxStyle = computed(() => {
  return {
    left: posX.value + 'px',
    bottom: posY.value + 'px'
  }
})

function startDrag(e: MouseEvent) {
  isDragging = true
  dragStartX = e.clientX
  dragStartY = e.clientY
  
  window.addEventListener('mousemove', onDrag)
  window.addEventListener('mouseup', stopDrag)
}

function onDrag(e: MouseEvent) {
  if (!isDragging) return
  const dx = e.clientX - dragStartX
  const dy = e.clientY - dragStartY
  
  posX.value += dx
  posY.value -= dy // because bottom is used instead of top
  
  dragStartX = e.clientX
  dragStartY = e.clientY
}

function stopDrag() {
  isDragging = false
  window.removeEventListener('mousemove', onDrag)
  window.removeEventListener('mouseup', stopDrag)
}

function saveRating(bp: any) {
  const bList = JSON.parse(localStorage.getItem('aethelnet_blueprints') || '[]')
  const existing = bList.find((b: any) => b.id === bp.id)
  if (existing) {
    existing.rating = bp.rating
    localStorage.setItem('aethelnet_blueprints', JSON.stringify(bList))
  }
}

const marketResults = ref<any[]>([])
let debounceTimer: any
watch(marketSearchQuery, (newVal) => {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(async () => {
    try {
      const API_BASE = (window as any).API_BASE || ''
      const url = API_BASE ? `${API_BASE}/lgnn/market/search?q=${encodeURIComponent(newVal)}` : `/api/lgnn/market/search?q=${encodeURIComponent(newVal)}`
      const res = await fetch(url)
      const data = await res.json()
      if (data.status === 'success') {
        marketResults.value = data.results
      }
    } catch(e) {
      console.error("Market fetch failed", e)
    }
  }, 300)
}, { immediate: true })

const filteredSystemApps = computed(() => {
  if (!marketSearchQuery.value) return systemApps;
  const q = marketSearchQuery.value.toLowerCase();
  return systemApps.filter(app => app.name.toLowerCase().includes(q) || app.id.toLowerCase().includes(q));
})

const groupedCustomBlueprints = computed(() => {
  let bps = props.customBlueprints;
  if (marketSearchQuery.value) {
    const q = marketSearchQuery.value.toLowerCase();
    bps = bps.filter((bp: any) => bp.name.toLowerCase().includes(q));
  }
  
  const groups: Record<string, any[]> = {}
  bps.forEach((bp: any) => {
    const cat = bp.category ? bp.category.toUpperCase() : 'CUSTOM BLUEPRINTS & PEER REVIEW'
    if (!groups[cat]) groups[cat] = []
    groups[cat].push(bp)
  })
  return groups
})

const handleImageUpload = (event: Event) => {
  const target = event.target as HTMLInputElement
  if (target.files && target.files.length > 0) {
    emits('spawn-custom', 'image', target.files[0])
  }
}
</script>

<style scoped>
.toolbox {
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  width: 280px;
  background: var(--color-bg-panel);
  border-right: 1px solid var(--border-color);
  box-shadow: 4px 0 15px rgba(0,0,0,0.5);
  display: flex;
  flex-direction: column;
  z-index: 1500;
}

.toolbox-top {
  padding: 16px;
  border-bottom: 1px solid var(--border-color);
  background: var(--color-bg-primary);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.toolbox-tabs {
  display: flex;
  border-bottom: 1px solid var(--border-color);
  background: var(--color-bg-primary);
}

.tab-btn {
  flex: 1;
  background: transparent;
  border: none;
  color: var(--color-text-muted);
  font-family: var(--font-family-mono);
  font-size: 10px;
  font-weight: bold;
  padding: 8px 0;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: all 0.2s;
}

.tab-btn:hover {
  color: var(--color-text-main);
}

.tab-btn.active {
  color: var(--color-accent);
  border-bottom: 2px solid var(--color-accent);
}

.toolbox-top {
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-color);
  background: var(--color-bg-primary);
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: grab;
}

.toolbox-top:active {
  cursor: grabbing;
}

.toolbox-header {
  font-family: var(--font-family);
  font-weight: 900;
  font-size: 14px;
  text-transform: uppercase;
  color: var(--color-text-main);
  letter-spacing: 1px;
}

.close-btn {
  background: transparent;
  border: none;
  color: var(--color-text-muted);
  font-size: 16px;
  cursor: pointer;
  padding: 0;
  margin: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  transition: color var(--transition-fast);
}

.close-btn:hover {
  color: var(--color-accent);
}

.toolbox-scroll {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.category-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.category-title {
  font-family: var(--font-family-mono);
  font-size: 10px;
  font-weight: 600;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 4px;
}

.tool-btn {
  background: transparent;
  border: 1px solid var(--border-color);
  color: var(--color-text-main);
  font-family: var(--font-family-mono);
  font-size: 11px;
  padding: 8px 12px;
  cursor: pointer;
  text-align: left;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all var(--transition-fast);
}

.btn-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  background: var(--color-bg-primary);
  border: 1px solid var(--border-color);
  font-weight: 800;
  font-size: 9px;
}

.tool-btn:hover {
  background: var(--color-text-main);
  color: var(--color-bg-primary) !important;
  border-color: var(--color-text-main);
}

.tool-btn:hover .btn-icon {
  border-color: var(--color-bg-primary);
  background: var(--color-text-main);
  color: var(--color-bg-primary);
}

.sensor-btn .status-dot {
  display: inline-block;
  width: 6px;
  height: 6px;
  background: var(--color-text-muted);
  border-radius: 50%;
}

.sensor-btn.active {
  border-color: #32d74b;
  color: #32d74b;
}

.sensor-btn.active .status-dot {
  background: #32d74b;
  box-shadow: 0 0 6px rgba(50, 215, 75, 0.6);
}

.nodes-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.node-list-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  cursor: pointer;
  font-family: var(--font-family-mono);
  font-size: 10px;
  color: var(--color-text-main);
  border: 1px solid transparent;
  transition: all var(--transition-fast);
}

.node-list-item:hover {
  background: var(--color-bg-primary);
  border-color: var(--border-color);
}

.node-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.node-label {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  flex: 1;
}

/* Custom Scrollbar */
.toolbox-scroll::-webkit-scrollbar {
  width: 4px;
}
.toolbox-scroll::-webkit-scrollbar-track {
  background: transparent;
}
.toolbox-scroll::-webkit-scrollbar-thumb {
  background: var(--border-color);
  border-radius: 2px;
}
.toolbox-scroll::-webkit-scrollbar-thumb:hover {
  background: var(--color-text-muted);
}
.market-search {
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--color-bg-primary);
  border: 1px solid var(--border-color);
  padding: 6px 12px;
  margin-bottom: 12px;
}

.search-icon {
  color: var(--color-accent);
  font-weight: bold;
}

.market-search-input {
  flex: 1;
  background: transparent;
  border: none;
  color: var(--color-text-main);
  font-family: var(--font-family-mono);
  font-size: 11px;
  outline: none;
}

.market-search-input::placeholder {
  color: var(--color-text-muted);
}

.delete-bp-btn {
  background: transparent;
  border: 1px solid var(--border-color);
  color: var(--color-text-muted);
  font-family: var(--font-family-mono);
  font-size: 9px;
  font-weight: bold;
  padding: 4px;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.delete-bp-btn:hover {
  background: #E03C31;
  color: #fff;
  border-color: #E03C31;
}
</style>
