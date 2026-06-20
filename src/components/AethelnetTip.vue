<template>
  <div v-if="isVisible && showTips" class="aethelnet-tip" :class="{ 'dismissed': dismissed }">
    <div class="tip-header">
      <span class="tip-icon"><i class="fas fa-lightbulb"></i></span>
      <span class="tip-title">Aethelnet Tip</span>
      <button class="close-btn" @click="dismiss">
        <i class="fas fa-times"></i>
      </button>
    </div>
    <div class="tip-content">
      <slot></slot>
    </div>
    <div class="tip-footer">
      <label class="toggle-tips">
        <input type="checkbox" v-model="showTips" @change="savePreference">
        <span>Show contextual tips</span>
      </label>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'

const props = defineProps<{
  id: string
}>()

const isVisible = ref(true)
const dismissed = ref(false)
const showTips = ref(true)

onMounted(() => {
  // Load global tip preference
  const savedGlobal = localStorage.getItem('aethelnet_show_tips')
  if (savedGlobal === 'false') {
    showTips.value = false
  }

  // Load specific tip dismissal
  const dismissedTips = JSON.parse(localStorage.getItem('aethelnet_dismissed_tips') || '{}')
  if (dismissedTips[props.id]) {
    isVisible.value = false
  }
})

function dismiss() {
  dismissed.value = true
  setTimeout(() => {
    isVisible.value = false
    const dismissedTips = JSON.parse(localStorage.getItem('aethelnet_dismissed_tips') || '{}')
    dismissedTips[props.id] = true
    localStorage.setItem('aethelnet_dismissed_tips', JSON.stringify(dismissedTips))
  }, 300)
}

function savePreference() {
  localStorage.setItem('aethelnet_show_tips', showTips.value.toString())
}

// Watch for global preference changes across components
window.addEventListener('storage', (e) => {
  if (e.key === 'aethelnet_show_tips') {
    showTips.value = e.newValue !== 'false'
  }
})
</script>

<style scoped>
.aethelnet-tip {
  background: rgba(26, 26, 26, 0.95);
  border: 1px solid var(--color-border);
  border-left: 3px solid var(--color-primary);
  border-radius: 4px;
  padding: 12px;
  margin: 12px 0;
  font-family: 'IBM Plex Mono', monospace;
  font-size: 11px;
  color: var(--color-text);
  box-shadow: 0 4px 12px rgba(0,0,0,0.5);
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.aethelnet-tip.dismissed {
  opacity: 0;
  transform: translateX(20px);
  pointer-events: none;
}

.tip-header {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
  color: var(--color-primary);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.tip-icon {
  margin-right: 8px;
}

.tip-title {
  flex: 1;
}

.close-btn {
  background: none;
  border: none;
  color: var(--color-text-muted);
  cursor: pointer;
  padding: 4px;
  transition: color 0.2s;
}

.close-btn:hover {
  color: var(--color-danger);
}

.tip-content {
  line-height: 1.5;
  margin-bottom: 12px;
  color: #DDD;
}

.tip-footer {
  border-top: 1px solid rgba(255,255,255,0.1);
  padding-top: 8px;
  display: flex;
  justify-content: flex-end;
}

.toggle-tips {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 10px;
  color: var(--color-text-muted);
  cursor: pointer;
}

.toggle-tips input {
  accent-color: var(--color-primary);
}
</style>
