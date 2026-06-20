<template>
  <aside class="sidebar">
    <!-- Home Indicator -->
    <div class="sidebar-item" :class="{ active: props.currentView === 'home' }" @click="navigate('home')" title="Sovereign Neural Manifold">
      <div class="sidebar-icon">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path>
          <polyline points="9 22 9 12 15 12 15 22"></polyline>
        </svg>
      </div>
    </div>

    <!-- Self (Hub) Indicator -->
    <div class="sidebar-item" :class="{ active: props.currentView === 'self' }" @click="navigate('self')" title="Self (Reality Anchors)">
      <div class="sidebar-icon">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#c678dd" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="4"></circle>
          <path d="M16 8v5a3 3 0 0 0 6 0v-1a10 10 0 1 0-3.92 7.94"></path>
        </svg>
      </div>
    </div>

    <!-- Deleted Status Indicator -->
    
    <!-- The Lens Indicator -->
    <div class="sidebar-item" :class="{ active: props.currentView === 'aura' }" @click="navigate('aura')" title="The Lens (Observer)">
      <div class="sidebar-icon">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#4FC3F7" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2z"></path>
          <path d="M12 8v4l3 3"></path>
          <circle cx="12" cy="12" r="3" fill="rgba(79, 195, 247, 0.4)"></circle>
        </svg>
      </div>
    </div>

    <!-- Synaptic Canvas (Macro/Micro) Indicator -->
    <div class="sidebar-item" :class="{ active: props.currentView === 'synaptic' }" @click="navigate('synaptic')" title="Synaptic Canvas (Macro/Micro)">
      <div class="sidebar-icon">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <!-- Outer circle for galaxy, inner nodes for maxmsp -->
          <circle cx="12" cy="12" r="10" stroke-dasharray="2 4"/>
          <circle cx="12" cy="12" r="3"/>
          <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41"/>
        </svg>
      </div>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { setupConnectionListener, isWebSocketConnected } from '../shared/websocket.js'

const props = defineProps<{
  currentView?: string
}>()

const isConnected = ref<boolean>(false)

// Simple navigation - just emit event for now
const emit = defineEmits<{
  navigate: [view: string]
}>()

function navigate(view: string) {
  emit('navigate', view)
}

// Check connection status
let connectionUnsub: (() => void) | null = null

onMounted(() => {
  // Check initial connection status
  isConnected.value = isWebSocketConnected()
  
  // Listen for connection changes
  connectionUnsub = setupConnectionListener((connected) => {
    isConnected.value = connected
  })
})

onUnmounted(() => {
  if (connectionUnsub) connectionUnsub()
})
</script>

<style scoped>
.sidebar {
  width: 60px;
  background: var(--color-bg-panel, rgba(20, 20, 30, 0.95));
  border-right: 1px solid var(--color-text-muted, rgba(136, 136, 136, 0.2));
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 12px 0;
  gap: 8px;
  position: fixed;
  left: 0;
  top: 0;
  height: 100vh;
  z-index: 100;
}

.sidebar-item {
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
  border-radius: 8px;
  position: relative;
}

.sidebar-item:hover {
  background: var(--color-accent-dark, rgba(74, 222, 128, 0.15));
}

.sidebar-item.active {
  background: var(--color-accent-dark, rgba(74, 222, 128, 0.2));
}

.sidebar-icon {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  color: var(--color-text-muted, #888);
}

.sidebar-icon svg {
  width: 20px;
  height: 20px;
}

.sidebar-item:hover .sidebar-icon,
.sidebar-item.active .sidebar-icon {
  color: var(--color-accent, #4ade80);
}

.status-dot {
  position: absolute;
  bottom: 4px;
  right: 4px;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  border: 2px solid var(--color-bg-panel, rgba(20, 20, 30, 0.95));
}

.status-dot.connected {
  background: var(--color-accent, #4ade80);
}

.status-dot.disconnected {
  background: var(--color-danger, #f87171);
}

/* Light mode adjustments */
@media (prefers-color-scheme: light) {
  .sidebar {
    background: var(--color-bg-panel, rgba(255, 255, 255, 1));
    border-right-color: var(--color-text-muted, rgba(107, 114, 128, 0.2));
  }
  
  .status-dot {
    border-color: var(--color-bg-panel, rgba(255, 255, 255, 1));
  }
}
</style>

