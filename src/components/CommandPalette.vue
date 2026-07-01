<template>
  <Transition name="fade">
    <div v-if="isOpen" class="palette-overlay" @click.self="close">
      <div class="palette-container">
        <div class="palette-input-wrapper">
          <span class="palette-icon">[ CMD ]</span>
          <input
            ref="inputRef"
            v-model="searchQuery"
            type="text"
            placeholder="Type a command or view..."
            @keydown.down="moveDown"
            @keydown.up="moveUp"
            @keydown.enter="executeCurrent"
            @keydown.esc="close"
          />
        </div>
        
        <div v-if="filteredResults.length > 0" class="palette-results">
          <div
            v-for="(item, index) in filteredResults"
            :key="item.id || index"
            class="palette-item"
            :class="{ active: index === activeIndex, ['item-type-' + item.type]: true }"
            @mouseenter="activeIndex = index"
            @click="executeItem(item)"
          >
            <span class="item-icon" :style="{ color: item.color || '#EEE' }">{{ item.icon || '[?]' }}</span>
            <div class="item-info">
              <span class="item-label" :style="{ color: item.color || '#EEE' }">{{ item.label }}</span>
              <span class="item-desc">{{ item.description }}</span>
            </div>
            <span v-if="item.shortcut" class="item-shortcut">{{ item.shortcut }}</span>
            <span v-else-if="item.type" class="item-type-badge">{{ item.type.toUpperCase() }}</span>
          </div>
        </div>
        <div v-else class="palette-no-results">
          <div style="margin-bottom: 8px;">No local matches found for "{{ searchQuery }}"</div>
          <button class="spider-btn" @click="executeSpiderSearch">
            [*] DEPLOY SPIDER TO SEARCH NETWORK
          </button>
        </div>
        
        <div class="palette-footer">
          <span><kbd>↑↓</kbd> to navigate</span>
          <span><kbd>↵</kbd> to execute</span>
          <span><kbd>esc</kbd> to close</span>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted, onBeforeUnmount } from 'vue'

const props = defineProps<{
  isOpen: boolean,
  nodes?: any[]
}>()

const emit = defineEmits(['close', 'navigate', 'command'])

const searchQuery = ref('')
const activeIndex = ref(0)
const inputRef = ref<HTMLInputElement | null>(null)
const marketResults = ref<any[]>([])
let searchTimeout: any = null

const commands = [
  { id: 'cmd-fresh', label: 'Fresh Canvas', description: 'Dive into a brand new empty dimension', icon: '[+]', type: 'command', value: 'fresh-canvas', shortcut: '↵' },
  { id: 'cmd-subgraph', label: 'Spawn Subgraph', description: 'Create a new nested subgraph dimension', icon: '[SUB]', type: 'command', value: 'spawn-subgraph' },
  { id: 'cmd-diary', label: 'Toggle Diary', description: 'Open/Close the System Diary', icon: '[D]', type: 'command', value: 'toggle-diary', shortcut: 'Ctrl+Shift+D' },
  { id: 'cmd-identity', label: 'Spawn Identity', description: 'Create a new Persona Identity Node', icon: '[ID]', type: 'command', value: 'spawn-identity' },
  { id: 'cmd-aurastream', label: 'Spawn AuraStream', description: 'Open the P2P communication stream', icon: '[~]', type: 'command', value: 'spawn-aurastream' },
  { id: 'cmd-html', label: 'Spawn HTML Node', description: 'Create an interactive HTML canvas', icon: '[<>]', type: 'command', value: 'spawn-html' },
  { id: 'cmd-spider', label: 'Spawn Spider', description: 'Create a network spider node', icon: '[*]', type: 'command', value: 'spawn-spider' },
  { id: 'cmd-render', label: 'Spawn UI Render', description: 'Create a UI rendering node', icon: '[UI]', type: 'command', value: 'spawn-render' },
  { id: 'cmd-vault', label: 'Spawn Vault', description: 'Create a secure credential storage node', icon: '[V]', type: 'command', value: 'spawn-vault' },
  { id: 'cmd-evolve', label: 'Evolve Command', description: 'Mutate a node via the Network', icon: '[NET]', type: 'command', value: 'spawn-evolve' },
  { id: 'cmd-anomaly', label: 'Spawn Anomaly', description: 'Create a gravitational anomaly', icon: '[O]', type: 'command', value: 'spawn-anomaly' },
  { id: 'cmd-pattern-matcher', label: 'Spawn Pattern Matcher', description: 'Episode Pattern Matcher', icon: '[🦂]', type: 'command', value: 'spawn-app', payload: 'PatternMatcher' },
  { id: 'cmd-prisma', label: 'Spawn Prisma', description: 'Research Commenter Node', icon: '[PR]', type: 'command', value: 'spawn-app', payload: 'Prisma' },
  { id: 'cmd-fusion', label: 'Spawn Fusion Reactor', description: 'Concept Synthesis Engine', icon: '[FU]', type: 'command', value: 'spawn-app', payload: 'Fusion' },
  { id: 'cmd-repulsor', label: 'Spawn Repulsor', description: 'Noise Filter Shield', icon: '[RP]', type: 'command', value: 'spawn-app', payload: 'Repulsor' },
  { id: 'cmd-graviton', label: 'Spawn Graviton', description: 'Concept Attractor', icon: '[GR]', type: 'command', value: 'spawn-app', payload: 'Graviton' },
  { id: 'cmd-entropy', label: 'Spawn Entropy Chamber', description: 'Concept Decay Engine', icon: '[EN]', type: 'command', value: 'spawn-app', payload: 'EntropyChamber' },
  { id: 'cmd-incubator', label: 'Spawn Incubator', description: 'Concept Greenhouse', icon: '[IN]', type: 'command', value: 'spawn-app', payload: 'Incubator' },
  { id: 'cmd-chronosphere', label: 'Spawn Chronosphere', description: 'Predictive Extrapolation', icon: '[CH]', type: 'command', value: 'spawn-app', payload: 'Chronosphere' },
  { id: 'cmd-blueprint', label: 'Load System Blueprint', description: 'Fetch and visualize the CodeSpider architecture', icon: '[BP]', type: 'command', value: 'load-blueprint' },
  { id: 'cmd-clear', label: 'Clear Graph', description: 'Reset the local graph visualization', icon: '[X]', type: 'command', value: 'clear-graph' },
]

const filteredResults = computed(() => {
  const query = searchQuery.value.toLowerCase()
  let results: any[] = []

  // 1. Static Commands
  if (!query) {
    results = [...commands]
  } else {
    results = commands.filter(c => 
      c.label.toLowerCase().includes(query) || 
      c.description.toLowerCase().includes(query)
    )
  }

  // 2. Local Nodes
  if (query && props.nodes) {
    const localNodes = props.nodes
      .filter(n => n.text_content?.toLowerCase().includes(query) || (n.meta_data && typeof n.meta_data === 'string' && n.meta_data.toLowerCase().includes(query)))
      .slice(0, 5)
      .map(n => ({
        id: n.id,
        label: n.id,
        description: n.text_content?.substring(0, 60) + '...',
        icon: '[N]',
        type: 'node',
        value: 'focus-node',
        color: '#00BCD4',
        node: n
      }))
    results = [...results, ...localNodes]
  }

  // 3. Market / Community Apps
  if (marketResults.value.length > 0) {
    results = [...results, ...marketResults.value]
  }

  return results
})

watch(searchQuery, (newVal) => {
  activeIndex.value = 0
  if (searchTimeout) clearTimeout(searchTimeout)
  
  if (newVal.length > 2) {
    searchTimeout = setTimeout(async () => {
      try {
        const res = await fetch(`/api/lgnn/market/search?q=${encodeURIComponent(newVal)}&limit=5`)
        const data = await res.json()
        let results = []
        if (data.results) {
          results = data.results.map((n: any) => {
            let meta = n.meta_data
            if (typeof meta === 'string') {
              try { meta = JSON.parse(meta) } catch(e) {}
            }
            return {
              id: n.id,
              label: meta?.name || n.id,
              description: meta?.category || 'Community App',
              icon: meta?.icon || '[A]',
              type: 'app',
              value: 'spawn-app',
              color: meta?.color || '#FF9800',
              node: n
            }
          })
        }
        marketResults.value = results;
        
        // Background Spider Fire
        fetch(`/api/spider/crawl?target=${encodeURIComponent(newVal)}`).then(async (spiderRes) => {
          if (spiderRes.ok && newVal === searchQuery.value) {
            const spiderData = await spiderRes.json()
            if (spiderData.cluster && spiderData.cluster.nodes) {
              const sNodes = spiderData.cluster.nodes.map((n:any) => ({
                id: n.id,
                label: n.id,
                description: n.content ? n.content.substring(0, 60) + '...' : 'Live network extraction',
                icon: '[*]',
                type: 'spider-node',
                value: 'focus-node',
                color: '#E03C31',
                node: n
              }))
              // Append live results
              marketResults.value = [...marketResults.value, ...sNodes]
            }
          }
        }).catch(err => console.debug("Spider background check skipped", err))
      } catch (err) {
        console.error("Market search failed", err)
      }
    }, 300)
  } else {
    marketResults.value = []
  }
})

watch(() => props.isOpen, (newVal) => {
  if (newVal) {
    searchQuery.value = ''
    activeIndex.value = 0
    nextTick(() => {
      inputRef.value?.focus()
    })
  }
})

function close() {
  emit('close')
}

function moveDown() {
  if (activeIndex.value < filteredResults.value.length - 1) {
    activeIndex.value++
  } else {
    activeIndex.value = 0
  }
}

function moveUp() {
  if (activeIndex.value > 0) {
    activeIndex.value--
  } else {
    activeIndex.value = filteredResults.value.length - 1
  }
}

function executeCurrent() {
  if (filteredResults.value[activeIndex.value]) {
    executeItem(filteredResults.value[activeIndex.value])
  }
}

function executeItem(item: any) {
  emit('command', item)
  close()
}

function executeSpiderSearch() {
  emit('command', {
    type: 'command',
    value: 'spawn-spider',
    payload: searchQuery.value
  })
  close()
}

// Global listener for Ctrl+P
function handleGlobalKeydown(e: KeyboardEvent) {
  // Listener removed, moved to App.vue
}

onMounted(() => {
  window.addEventListener('keydown', handleGlobalKeydown)
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', handleGlobalKeydown)
})
</script>

<style scoped>
.palette-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(8px);
  z-index: 9999;
  display: flex;
  justify-content: center;
  padding-top: 15vh;
}

.palette-container {
  width: 600px;
  max-width: 90vw;
  background: #1a1a1a;
  border: 1px solid #333;
  border-radius: 12px;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.5), 0 0 20px rgba(0, 255, 128, 0.1);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  animation: slideDown 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes slideDown {
  from { transform: translateY(-20px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}

.palette-input-wrapper {
  display: flex;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #333;
  background: #222;
}

.palette-icon {
  font-size: 20px;
  margin-right: 15px;
  filter: drop-shadow(0 0 5px rgba(0, 255, 128, 0.5));
}

input {
  flex: 1;
  background: transparent;
  border: none;
  color: #fff;
  font-size: 18px;
  outline: none;
  font-family: 'Inter', sans-serif;
}

.palette-results {
  max-height: 400px;
  overflow-y: auto;
  padding: 8px;
}

.palette-item {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.1s ease;
  margin-bottom: 2px;
}

.palette-item.active {
  background: rgba(0, 255, 128, 0.1);
  border-left: 3px solid #00ff80;
}

.item-icon {
  font-size: 20px;
  margin-right: 15px;
  width: 24px;
  text-align: center;
}

.item-info {
  display: flex;
  flex-direction: column;
}

.item-label {
  font-size: 15px;
  font-weight: 600;
  color: #eee;
}

.item-desc {
  font-size: 12px;
  color: #888;
}

.item-shortcut {
  margin-left: auto;
  font-size: 11px;
  color: #555;
  background: #111;
  padding: 2px 6px;
  border-radius: 4px;
  border: 1px solid #333;
}

.palette-no-results {
  padding: 30px;
  text-align: center;
  color: #666;
  font-style: italic;
}

.palette-footer {
  padding: 10px 20px;
  background: #111;
  border-top: 1px solid #333;
  display: flex;
  gap: 20px;
  font-size: 11px;
  color: #555;
}

kbd {
  background: #222;
  border: 1px solid #444;
  border-radius: 3px;
  padding: 1px 4px;
  color: #888;
  margin: 0 2px;
}

.fade-enter-active, .fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}
</style>
