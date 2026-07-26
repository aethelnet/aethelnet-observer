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

import { useGraphStore } from '../stores/useGraphStore'
import { useAgentStore } from '../stores/agentStore'
import { storeToRefs } from 'pinia'

const graphStore = useGraphStore()
const agentStore = useAgentStore()
const { nodes } = storeToRefs(graphStore)

const props = defineProps<{
  isOpen: boolean
}>()

const emit = defineEmits(['close', 'navigate', 'command'])

const searchQuery = ref('')
const activeIndex = ref(0)
const inputRef = ref<HTMLInputElement | null>(null)
const marketResults = ref<any[]>([])
let searchTimeout: any = null

const commands: any[] = [
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
  { id: 'cmd-blueprint', label: 'Load System Blueprint', description: 'Fetch and visualize the CodeSpider architecture', icon: '[BP]', type: 'command', value: 'load-blueprint' },
  { id: 'cmd-clear', label: 'Clear Graph', description: 'Reset the local graph visualization', icon: '[X]', type: 'command', value: 'clear-graph' },
]

const dynamicCommands = computed(() => {
  const base = [...commands]
  // Add installed agents dynamically
  const installed = agentStore.agents.filter(a => a.installed)
  installed.forEach(agent => {
    base.push({
      id: `cmd-${agent.id}`,
      label: `Spawn ${agent.name}`,
      description: agent.description,
      icon: agent.icon,
      type: 'command',
      value: 'spawn-app',
      payload: agent.id // Backend needs to match this ID
    })
  })
  return base
})

const filteredResults = computed(() => {
  const query = searchQuery.value.toLowerCase()
  let results: any[] = []

  // 1. Static & Dynamic Commands
  if (!query) {
    results = [...dynamicCommands.value]
  } else {
    results = dynamicCommands.value.filter(c => 
      c.label.toLowerCase().includes(query) || 
      c.description.toLowerCase().includes(query)
    )
  }

  // 2. Local Nodes
  if (query && nodes.value) {
    const localNodes = nodes.value
      .filter(n => n.text_content?.toLowerCase().includes(query) || (n.meta_data && typeof n.meta_data === 'string' && n.meta_data.toLowerCase().includes(query)))
      .slice(0, 5)
      .map(n => ({
        id: n.id,
        label: n.id,
        description: n.text_content?.substring(0, 60) + '...',
        icon: '[N]',
        type: 'node',
        value: 'focus-node',
        color: '#000000',
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
  width: 650px;
  max-width: 90vw;
  background: rgba(18, 18, 20, 0.45);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  box-shadow: 0 32px 64px rgba(0, 0, 0, 0.6), 0 0 40px rgba(0, 255, 255, 0.05);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  animation: slideDown 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes slideDown {
  from { transform: translateY(-30px) scale(0.98); opacity: 0; }
  to { transform: translateY(0) scale(1); opacity: 1; }
}

.palette-input-wrapper {
  display: flex;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(255, 255, 255, 0.02);
}

.palette-icon {
  font-size: 20px;
  margin-right: 16px;
  color: #00e5ff;
  text-shadow: 0 0 10px rgba(0, 229, 255, 0.5);
  font-family: 'JetBrains Mono', monospace;
  font-weight: 600;
}

input {
  flex: 1;
  background: transparent;
  border: none;
  color: #fff;
  font-size: 20px;
  outline: none;
  font-family: var(--font-family);
  font-weight: 300;
}
input::placeholder {
  color: rgba(255, 255, 255, 0.3);
}

.palette-results {
  max-height: 450px;
  overflow-y: auto;
  padding: 12px;
}

.palette-item {
  display: flex;
  align-items: center;
  padding: 14px 20px;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
  margin-bottom: 4px;
  border: 1px solid transparent;
}

.palette-item.active,
.palette-item:hover {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: inset 0 0 20px rgba(255, 255, 255, 0.02);
}

.item-icon {
  font-size: 20px;
  margin-right: 16px;
  width: 24px;
  text-align: center;
  opacity: 0.9;
}

.item-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.item-label {
  font-size: 15px;
  font-weight: 500;
  color: #fff;
  letter-spacing: 0.2px;
}

.item-desc {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.5);
}

.item-shortcut, .item-type-badge {
  margin-left: auto;
  font-size: 11px;
  font-family: var(--font-family-mono);
  color: rgba(255, 255, 255, 0.6);
  background: rgba(255, 255, 255, 0.05);
  padding: 4px 8px;
  border-radius: 6px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  letter-spacing: 1px;
}

.palette-no-results {
  padding: 40px;
  text-align: center;
  color: rgba(255, 255, 255, 0.4);
  font-style: italic;
  font-size: 14px;
}

.palette-footer {
  padding: 14px 24px;
  background: rgba(0, 0, 0, 0.2);
  border-top: 1px solid rgba(255, 255, 255, 0.05);
  display: flex;
  gap: 24px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.4);
  font-weight: 500;
}

kbd {
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 4px;
  padding: 2px 6px;
  color: #fff;
  margin: 0 4px;
  box-shadow: 0 2px 0 rgba(0,0,0,0.2);
  font-family: var(--font-family-mono);
}

.fade-enter-active, .fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}
</style>
