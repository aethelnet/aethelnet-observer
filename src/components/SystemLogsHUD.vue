<template>
  <div class="logs-hud" :class="{ open: isOpen, fullscreen: isFullscreen }">
    <!-- Sliding Toggle Tab (shows when drawer is closed) -->
    <div v-if="!isOpen" class="logs-tab" @click="toggleOpen" title="Open Live Console logs (Shortcut: Backtick ` or Ctrl+L)">
      <div class="tab-pulse"></div>
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <polyline points="4 17 10 11 4 5"></polyline>
        <line x1="12" y1="19" x2="20" y2="19"></line>
      </svg>
      <span>CONSOLE LOGS</span>
    </div>

    <!-- Main Terminal Container -->
    <div class="terminal-drawer">
      <!-- Header Deck -->
      <div class="terminal-header">
        <div class="header-left">
          <div class="terminal-badge">
            <span class="pulse-dot" :class="{ inactive: isPaused }"></span>
            <span class="badge-text">SYSTEM LOGS TELEMETRY</span>
          </div>
          <!-- Editable Backend URL Input -->
          <div class="backend-url-deck">
            <span class="url-label">API BASE:</span>
            <input 
              v-model="backendUrlInput" 
              @change="saveBackendUrl" 
              type="text" 
              class="backend-url-input" 
              placeholder="http://127.0.0.1:8000/api"
              title="Press Enter to save and re-bind frontend API client"
            />
          </div>
          <span class="source-tag" v-if="logSource">Source: {{ logSource }}</span>
        </div>
        <div class="header-right">
          <!-- Text Filter -->
          <div class="search-box">
            <input 
              v-model="searchQuery" 
              type="text" 
              placeholder="Filter logs (e.g. BTC, order)..." 
              aria-label="Filter logs"
            />
            <span v-if="searchQuery" class="clear-search" @click="searchQuery = ''">✕</span>
          </div>

          <!-- Controls -->
          <button class="icon-btn" @click="toggleFullscreen" :title="isFullscreen ? 'Exit Fullscreen' : 'Fullscreen HUD'">
            <svg v-if="!isFullscreen" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M15 3h6v6M9 21H3v-6M21 3l-7 7M3 21l7-7"/>
            </svg>
            <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M4 14h6v6M20 10h-6V4M14 10l7-7M10 14l-7 7"/>
            </svg>
          </button>
          
          <button class="icon-btn" @click="copyToClipboard" title="Copy logs to clipboard">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
              <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
            </svg>
          </button>

          <button class="icon-btn btn-close" @click="toggleOpen" title="Close Logs HUD (Shortcut: Backtick `)">
            ✕
          </button>
        </div>
      </div>

      <!-- Quick Filter Bar -->
      <div class="filter-bar">
        <div class="level-filters">
          <button :class="{ active: activeLevel === 'all' }" @click="activeLevel = 'all'">ALL</button>
          <button :class="{ active: activeLevel === 'info' }" @click="activeLevel = 'info'">INFO</button>
          <button :class="{ active: activeLevel === 'warn' }" @click="activeLevel = 'warn'">WARN</button>
          <button :class="{ active: activeLevel === 'error' }" @click="activeLevel = 'error'">ERROR</button>
          <button :class="{ active: activeLevel === 'trades' }" class="trades-btn" @click="activeLevel = 'trades'">⚔️ TRADES</button>
        </div>

        <div class="stream-controls">
          <label for="polling-interval">Interval:</label>
          <select id="polling-interval" v-model="pollRate" class="interval-select">
            <option :value="0">PAUSED</option>
            <option :value="1000">1s</option>
            <option :value="2000">2s</option>
            <option :value="5000">5s</option>
          </select>
          <button class="clear-btn" @click="clearLogsView">Clear View</button>
        </div>
      </div>

      <!-- Logs Monitor Screen -->
      <div class="terminal-screen" ref="screenRef" @scroll="handleScroll">
        <div v-if="filteredLogs.length === 0" class="empty-state">
          <p v-if="isLoading">Establishing telemetry link...</p>
          <p v-else-if="searchQuery || activeLevel !== 'all'">No logs matching filters found</p>
          <p v-else>Telemetry online. Waiting for incoming log packets...</p>
        </div>
        <div v-else class="logs-container">
          <div 
            v-for="(log, idx) in filteredLogs" 
            :key="idx" 
            class="log-line" 
            :class="getLogClass(log)"
          >
            <span class="line-num">{{ idx + 1 }}</span>
            <span class="line-content">{{ log }}</span>
          </div>
        </div>
      </div>

      <!-- Footer Bar -->
      <div class="terminal-footer">
        <span class="footer-left">Telemetry Status: <strong :class="isPaused ? 'paused' : 'live'">{{ isPaused ? 'PAUSED' : 'LIVE STREAMING' }}</strong></span>
        <span class="footer-right">Total Lines: {{ logs.length }} | Shown: {{ filteredLogs.length }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import { fetchRecentLogs } from '../shared/api.js'

const isOpen = ref(false)
const isFullscreen = ref(false)
const logs = ref<string[]>([])
const logSource = ref<string>('')
const searchQuery = ref('')
const activeLevel = ref<'all' | 'info' | 'warn' | 'error' | 'trades'>('all')
const pollRate = ref(2000) // Default 2s
const isLoading = ref(false)
const screenRef = ref<HTMLElement | null>(null)
const userScrolledUp = ref(false)

// Dynamic backend URL configuration
const backendUrlInput = ref('')

const isPaused = computed(() => pollRate.value === 0)

// Periodical fetch setup
let pollInterval: number | null = null

async function loadLogs() {
  if (isLoading.value) return
  isLoading.value = true
  try {
    const res = await fetchRecentLogs(250) // Read 250 lines for a deep scroll history
    if (res && res.ok) {
      logs.value = res.logs || []
      logSource.value = res.source || ''
      
      // Auto-scroll to bottom if user is not actively reviewing old logs
      if (!userScrolledUp.value) {
        scrollToBottom()
      }
    }
  } catch (err) {
    console.error('[LogsHUD] Failed to stream logs:', err)
  } finally {
    isLoading.value = false
  }
}

function startPolling() {
  stopPolling()
  if (pollRate.value > 0) {
    pollInterval = window.setInterval(loadLogs, pollRate.value)
  }
}

function stopPolling() {
  if (pollInterval) {
    clearInterval(pollInterval)
    pollInterval = null
  }
}

// Watch polling changes
watch(pollRate, () => {
  startPolling()
})

// Open/Close HUD
function toggleOpen() {
  isOpen.value = !isOpen.value
  if (isOpen.value) {
    loadLogs()
    startPolling()
    // Let animation complete before scrolling to bottom
    setTimeout(scrollToBottom, 300)
  } else {
    stopPolling()
  }
}

// Fullscreen HUD
function toggleFullscreen() {
  isFullscreen.value = !isFullscreen.value
  setTimeout(scrollToBottom, 50)
}

// Filter logic
const filteredLogs = computed(() => {
  return logs.value.filter(log => {
    // 1. Text Search Filter
    if (searchQuery.value && !log.toLowerCase().includes(searchQuery.value.toLowerCase())) {
      return false
    }

    // 2. Level Categorizer
    const logLower = log.toLowerCase()
    if (activeLevel.value === 'info') {
      return logLower.includes('info') || (!logLower.includes('warning') && !logLower.includes('error') && !logLower.includes('exception'))
    } else if (activeLevel.value === 'warn') {
      return logLower.includes('warning') || logLower.includes('warn')
    } else if (activeLevel.value === 'error') {
      return logLower.includes('error') || logLower.includes('exception') || logLower.includes('failed')
    } else if (activeLevel.value === 'trades') {
      return logLower.includes('trade') || logLower.includes('order') || logLower.includes('pnl') || logLower.includes('position') || logLower.includes('[force-')
    }

    return true
  })
})

// Scroll behavior
function handleScroll() {
  if (!screenRef.value) return
  const { scrollTop, scrollHeight, clientHeight } = screenRef.value
  // If the user scrolls up by more than 40px from bottom, lock auto-scroll
  const distanceFromBottom = scrollHeight - scrollTop - clientHeight
  userScrolledUp.value = distanceFromBottom > 40
}

function scrollToBottom() {
  nextTick(() => {
    if (screenRef.value) {
      screenRef.value.scrollTop = screenRef.value.scrollHeight
    }
  })
}

// styling logs line coloring
function getLogClass(log: string): string {
  const lower = log.toLowerCase()
  if (lower.includes('error') || lower.includes('exception') || lower.includes('failed') || lower.includes('critical')) {
    return 'log-error'
  }
  if (lower.includes('warning') || lower.includes('warn') || lower.includes('override')) {
    return 'log-warn'
  }
  if (lower.includes('success') || lower.includes('filled') || lower.includes('[force-trade] success')) {
    return 'log-success'
  }
  if (lower.includes('[force-trade]') || lower.includes('[force-close]') || lower.includes('placing')) {
    return 'log-execution'
  }
  return 'log-info'
}

// Copy to clipboard
function copyToClipboard() {
  const content = filteredLogs.value.join('\n')
  navigator.clipboard.writeText(content).then(() => {
    alert('Logs copied to clipboard!')
  }).catch(err => {
    console.error('Failed to copy logs:', err)
  })
}

// Clear display locally
function clearLogsView() {
  logs.value = []
}

// Global Key Listening (Backtick key ` or Ctrl+L)
function handleKeydown(e: KeyboardEvent) {
  // Backtick (`) key toggles HUD
  if (e.key === '`') {
    e.preventDefault()
    toggleOpen()
  }
  // Ctrl+L toggles HUD
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'l') {
    e.preventDefault()
    toggleOpen()
  }
}

function saveBackendUrl() {
  const url = backendUrlInput.value.trim()
  if (!url) {
    localStorage.removeItem('SOVEREIGN_BACKEND_URL')
  } else {
    localStorage.setItem('SOVEREIGN_BACKEND_URL', url)
  }
  // Soft reload to reinitialize the API client bound to the new location!
  window.location.reload()
}

onMounted(() => {
  // Load current configured backend URL
  backendUrlInput.value = localStorage.getItem('SOVEREIGN_BACKEND_URL') || 'http://127.0.0.1:8000/api'
  
  window.addEventListener('keydown', handleKeydown)
  // If drawer is initialized open, boot polling immediately
  if (isOpen.value) {
    startPolling()
  }
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', handleKeydown)
  stopPolling()
})
</script>

<style scoped>
/* HUD Wrapper */
.logs-hud {
  position: fixed;
  right: 0;
  top: 0;
  bottom: 0;
  width: 480px;
  background: var(--color-bg-panel, rgba(10, 10, 15, 0.95));
  border-left: 1px solid rgba(74, 222, 128, 0.25);
  box-shadow: -10px 0 30px rgba(0, 0, 0, 0.5);
  z-index: 9999;
  transform: translateX(100%);
  transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1), width 0.3s ease;
  display: flex;
  flex-direction: column;
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
}

.logs-hud.open {
  transform: translateX(0);
}

.logs-hud.fullscreen {
  width: 100vw;
  border-left: none;
}

/* Floating Drawer Tab */
:global(body.theme-liquid) .logs-hud {
  background: rgba(255, 255, 255, 0.85);
  border-left: 1px solid rgba(14, 165, 233, 0.25);
  box-shadow: -10px 0 30px rgba(0, 0, 0, 0.05);
  color: #333;
}
:global(body.theme-liquid) .terminal-screen {
  background: rgba(250, 250, 250, 0.9);
}
:global(body.theme-liquid) .terminal-header,
:global(body.theme-liquid) .terminal-footer,
:global(body.theme-liquid) .filter-bar {
  background: rgba(255, 255, 255, 0.9);
  border-color: rgba(0, 0, 0, 0.05);
}
:global(body.theme-liquid) .badge-text {
  color: #333;
}
:global(body.theme-liquid) .log-info {
  color: #475569;
}
:global(body.theme-liquid) .logs-tab {
  background: rgba(255, 255, 255, 0.95);
  border-color: rgba(14, 165, 233, 0.3);
  color: #0ea5e9;
}

.logs-tab {
  position: absolute;
  left: -140px;
  bottom: 24px;
  background: rgba(20, 20, 30, 0.9);
  border: 1px solid rgba(74, 222, 128, 0.3);
  border-right: none;
  padding: 10px 16px;
  border-radius: 8px 0 0 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--color-accent, #4ade80);
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  font-weight: bold;
  letter-spacing: 0.1em;
  box-shadow: -5px 5px 15px rgba(0, 0, 0, 0.3);
  transition: all 0.2s ease;
  backdrop-filter: blur(8px);
}

.logs-tab:hover {
  background: rgba(74, 222, 128, 0.1);
  color: #fff;
  border-color: var(--color-accent, #4ade80);
  padding-left: 20px;
}

.tab-pulse {
  width: 6px;
  height: 6px;
  background: var(--color-accent, #4ade80);
  border-radius: 50%;
  animation: tab-glow 1.5s infinite alternate;
}

@keyframes tab-glow {
  0% { transform: scale(0.8); opacity: 0.5; box-shadow: 0 0 0 0 rgba(74, 222, 128, 0.5); }
  100% { transform: scale(1.2); opacity: 1; box-shadow: 0 0 8px 3px rgba(74, 222, 128, 0.8); }
}

/* Main Drawer Inner Container */
.terminal-drawer {
  display: flex;
  flex-direction: column;
  height: 100%;
  width: 100%;
  font-family: 'JetBrains Mono', 'Courier New', monospace;
}

/* Header Deck */
.terminal-header {
  padding: 16px 20px;
  background: rgba(16, 16, 24, 0.8);
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.terminal-badge {
  display: flex;
  align-items: center;
  gap: 8px;
}

.pulse-dot {
  width: 8px;
  height: 8px;
  background: #4ade80;
  border-radius: 50%;
  box-shadow: 0 0 8px #4ade80;
}

.pulse-dot.inactive {
  background: #fbbf24;
  box-shadow: 0 0 8px #fbbf24;
}

.badge-text {
  color: #fff;
  font-size: 13px;
  font-weight: bold;
  letter-spacing: 0.05em;
}

.source-tag {
  font-size: 10px;
  color: #888;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

/* Search Box */
.search-box {
  position: relative;
  display: flex;
  align-items: center;
}

.search-box input {
  background: rgba(0, 0, 0, 0.5);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 4px;
  padding: 6px 28px 6px 12px;
  color: #fff;
  font-size: 11px;
  font-family: inherit;
  width: 160px;
  transition: all 0.2s ease;
}

.search-box input:focus {
  width: 220px;
  border-color: rgba(74, 222, 128, 0.5);
  outline: none;
  box-shadow: 0 0 10px rgba(74, 222, 128, 0.2);
}

.clear-search {
  position: absolute;
  right: 8px;
  color: #888;
  cursor: pointer;
  font-size: 10px;
}

.clear-search:hover {
  color: #fff;
}

/* Icon Buttons */
.icon-btn {
  background: none;
  border: none;
  color: #888;
  cursor: pointer;
  padding: 6px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.icon-btn:hover {
  color: #fff;
  background: rgba(255, 255, 255, 0.08);
}

.btn-close:hover {
  background: rgba(248, 113, 113, 0.2);
  color: #f87171;
}

/* Filter Bar */
.filter-bar {
  padding: 10px 20px;
  background: rgba(20, 20, 30, 0.4);
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
}

.level-filters {
  display: flex;
  gap: 6px;
}

.level-filters button {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 4px;
  color: #888;
  font-size: 10px;
  padding: 4px 8px;
  cursor: pointer;
  font-family: inherit;
  transition: all 0.15s ease;
}

.level-filters button:hover {
  color: #fff;
  background: rgba(255, 255, 255, 0.08);
}

.level-filters button.active {
  background: rgba(74, 222, 128, 0.15);
  border-color: var(--color-accent, #4ade80);
  color: var(--color-accent, #4ade80);
  text-shadow: 0 0 5px rgba(74, 222, 128, 0.5);
}

.level-filters button.trades-btn.active {
  background: rgba(167, 139, 250, 0.15);
  border-color: #a78bfa;
  color: #a78bfa;
  text-shadow: 0 0 5px rgba(167, 139, 250, 0.5);
}

.stream-controls {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 11px;
  color: #888;
}

.interval-select {
  background: rgba(0, 0, 0, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 4px;
  color: #fff;
  padding: 3px 6px;
  font-family: inherit;
  font-size: 11px;
}

.clear-btn {
  background: rgba(248, 113, 113, 0.05);
  border: 1px solid rgba(248, 113, 113, 0.2);
  border-radius: 4px;
  color: #f87171;
  font-size: 10px;
  padding: 4px 8px;
  cursor: pointer;
  font-family: inherit;
}

.clear-btn:hover {
  background: rgba(248, 113, 113, 0.15);
  color: #fff;
}

/* Terminal Screen */
.terminal-screen {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background: #050508;
  display: flex;
  flex-direction: column;
}

.empty-state {
  margin: auto;
  text-align: center;
  color: #555;
  font-size: 12px;
}

.logs-container {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.log-line {
  display: flex;
  font-size: 11px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-all;
}

.line-num {
  width: 32px;
  min-width: 32px;
  color: rgba(255, 255, 255, 0.15);
  user-select: none;
  font-size: 9px;
  padding-top: 2px;
}

.line-content {
  flex: 1;
}

/* Log Colors */
.log-error {
  color: #f87171;
  background: rgba(248, 113, 113, 0.03);
}

.log-warn {
  color: #fbbf24;
  background: rgba(251, 191, 36, 0.03);
}

.log-success {
  color: #4ade80;
  background: rgba(74, 222, 128, 0.03);
  text-shadow: 0 0 2px rgba(74, 222, 128, 0.2);
}

.log-execution {
  color: #a78bfa;
  background: rgba(167, 139, 250, 0.03);
}

.log-info {
  color: #cbd5e1;
}

/* Terminal Footer */
.terminal-footer {
  padding: 10px 20px;
  background: rgba(16, 16, 24, 0.8);
  border-top: 1px solid rgba(255, 255, 255, 0.05);
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 10px;
  color: #666;
}

.footer-left strong.live {
  color: #4ade80;
}

.footer-left strong.paused {
  color: #fbbf24;
}

/* Scrollbar Styling */
.terminal-screen::-webkit-scrollbar {
  width: 8px;
}

.terminal-screen::-webkit-scrollbar-track {
  background: #050508;
}

.terminal-screen::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
}

.terminal-screen::-webkit-scrollbar-thumb:hover {
  background: rgba(74, 222, 128, 0.25);
}

/* Backend URL Configuration Styling */
.backend-url-deck {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 6px;
  background: rgba(0, 0, 0, 0.4);
  border: 1px solid rgba(74, 222, 128, 0.15);
  border-radius: 4px;
  padding: 4px 8px;
}

.url-label {
  font-size: 9px;
  color: rgba(74, 222, 128, 0.7);
  font-weight: bold;
}

.backend-url-input {
  background: none;
  border: none;
  color: #fff;
  font-family: inherit;
  font-size: 10px;
  width: 220px;
  outline: none;
}

.backend-url-input:focus {
  color: var(--color-accent, #4ade80);
  text-shadow: 0 0 5px rgba(74, 222, 128, 0.3);
}
</style>
