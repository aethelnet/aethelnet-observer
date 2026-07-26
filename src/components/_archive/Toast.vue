<template>
  <TransitionGroup name="toast" tag="div" class="toast-container">
    <div
      v-for="toast in toasts"
      :key="toast.id"
      :class="['toast', `toast-${toast.type}`]"
    >
      <span class="toast-icon">
        <svg v-if="toast.type === 'success'" width="18" height="18" viewBox="0 0 18 18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M15 5L7 13L3 9"/>
        </svg>
        <svg v-else width="18" height="18" viewBox="0 0 18 18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M5 5L13 13M13 5L5 13"/>
        </svg>
      </span>
      <span class="toast-message">{{ toast.message }}</span>
    </div>
  </TransitionGroup>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'

export interface Toast {
  id: number
  type: 'success' | 'error'
  message: string
}

const toasts = ref<Toast[]>([])
let toastIdCounter = 0

function showToast(type: 'success' | 'error', message: string, duration: number = 3000) {
  const id = toastIdCounter++
  const toast: Toast = { id, type, message }
  toasts.value.push(toast)
  
  setTimeout(() => {
    const index = toasts.value.findIndex(t => t.id === id)
    if (index > -1) {
      toasts.value.splice(index, 1)
    }
  }, duration)
}

// Expose function globally for easy access
function setupToastListener() {
  const handleToast = (event: CustomEvent) => {
    const { type, message, duration } = event.detail
    showToast(type, message, duration)
  }
  
  window.addEventListener('toast:show', handleToast as EventListener)
  
  return () => {
    window.removeEventListener('toast:show', handleToast as EventListener)
  }
}

let cleanup: (() => void) | null = null

onMounted(() => {
  cleanup = setupToastListener()
  // Make showToast available globally for convenience
  ;(window as any).showToast = showToast
})

onUnmounted(() => {
  if (cleanup) cleanup()
  delete (window as any).showToast
})

// Export for programmatic use
defineExpose({ showToast })
</script>

<style scoped>
.toast-container {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 10000;
  display: flex;
  flex-direction: column;
  gap: 12px;
  pointer-events: none;
}

.toast {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-radius: 8px;
  background: var(--color-bg-card, rgba(20, 20, 30, 0.95));
  border: 1px solid var(--color-text-muted, rgba(136, 136, 136, 0.2));
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  min-width: 280px;
  max-width: 400px;
  pointer-events: auto;
  animation: slideIn 0.3s ease-out;
}

.toast-success {
  border-color: var(--color-accent, #4ade80);
  background: var(--color-accent-dark, rgba(74, 222, 128, 0.15));
}

.toast-error {
  border-color: var(--color-danger, #f87171);
  background: var(--color-danger-dark, rgba(248, 113, 113, 0.15));
}

.toast-icon {
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.toast-icon svg {
  width: 18px;
  height: 18px;
}

.toast-success .toast-icon {
  color: var(--color-accent, #4ade80);
}

.toast-error .toast-icon {
  color: var(--color-danger, #f87171);
}

.toast-message {
  flex: 1;
  color: var(--color-text, #e8e8e8);
  font-size: 14px;
  line-height: 1.4;
}

@keyframes slideIn {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
}

.toast-enter-from {
  transform: translateX(100%);
  opacity: 0;
}

.toast-leave-to {
  transform: translateX(100%);
  opacity: 0;
}

/* Light mode adjustments */
@media (prefers-color-scheme: light) {
  .toast {
    background: var(--color-bg-card, rgba(255, 255, 255, 0.95));
    border-color: var(--color-text-muted, rgba(107, 114, 128, 0.2));
  }
  
  .toast-message {
    color: var(--color-text, #1a1a1a);
  }
}
</style>

