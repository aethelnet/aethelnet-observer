<template>
  <div 
    class="tooltip-wrapper"
    @mouseenter="showTooltip"
    @mouseleave="hideTooltip"
    @focusin="showTooltip"
    @focusout="hideTooltip"
  >
    <!-- Trigger slot -->
    <slot />
    
    <!-- Tooltip content -->
    <Teleport to="body">
      <Transition name="tooltip-fade">
        <div 
          v-if="isVisible && content"
          class="tooltip-container"
          :class="[`tooltip-${position}`, { 'tooltip-rich': rich }]"
          :style="tooltipStyle"
          role="tooltip"
          :id="tooltipId"
        >
          <div class="tooltip-content">
            <span v-if="icon" class="tooltip-icon">{{ icon }}</span>
            <div class="tooltip-text">
              <strong v-if="title" class="tooltip-title">{{ title }}</strong>
              <p class="tooltip-description">{{ content }}</p>
            </div>
          </div>
          <div class="tooltip-arrow" :class="`arrow-${position}`"></div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue';

// ─────────────────────────────────────────────────────────────────────────────
// Props
// ─────────────────────────────────────────────────────────────────────────────

const props = withDefaults(defineProps<{
  /** Main tooltip text */
  content: string;
  /** Optional title (bold) */
  title?: string;
  /** Optional icon */
  icon?: string;
  /** Position relative to trigger */
  position?: 'top' | 'bottom' | 'left' | 'right';
  /** Rich mode with larger padding and shadow */
  rich?: boolean;
  /** Delay before showing (ms) */
  delay?: number;
  /** Maximum width */
  maxWidth?: number;
}>(), {
  position: 'top',
  rich: false,
  delay: 200,
  maxWidth: 280,
});

// ─────────────────────────────────────────────────────────────────────────────
// State
// ─────────────────────────────────────────────────────────────────────────────

const isVisible = ref(false);
const triggerRect = ref<DOMRect | null>(null);
let showTimeout: ReturnType<typeof setTimeout> | null = null;

const tooltipId = `tooltip-${Math.random().toString(36).slice(2, 9)}`;

// ─────────────────────────────────────────────────────────────────────────────
// Computed
// ─────────────────────────────────────────────────────────────────────────────

const tooltipStyle = computed(() => {
  if (!triggerRect.value) return {};
  
  const rect = triggerRect.value;
  const offset = 10;
  
  let top = 0;
  let left = 0;
  
  switch (props.position) {
    case 'top':
      top = rect.top - offset + window.scrollY;
      left = rect.left + rect.width / 2 + window.scrollX;
      break;
    case 'bottom':
      top = rect.bottom + offset + window.scrollY;
      left = rect.left + rect.width / 2 + window.scrollX;
      break;
    case 'left':
      top = rect.top + rect.height / 2 + window.scrollY;
      left = rect.left - offset + window.scrollX;
      break;
    case 'right':
      top = rect.top + rect.height / 2 + window.scrollY;
      left = rect.right + offset + window.scrollX;
      break;
  }
  
  return {
    top: `${top}px`,
    left: `${left}px`,
    maxWidth: `${props.maxWidth}px`,
  };
});

// ─────────────────────────────────────────────────────────────────────────────
// Methods
// ─────────────────────────────────────────────────────────────────────────────

function showTooltip(event: Event) {
  const target = event.currentTarget as HTMLElement;
  triggerRect.value = target.getBoundingClientRect();
  
  if (showTimeout) clearTimeout(showTimeout);
  
  showTimeout = setTimeout(() => {
    isVisible.value = true;
  }, props.delay);
}

function hideTooltip() {
  if (showTimeout) {
    clearTimeout(showTimeout);
    showTimeout = null;
  }
  isVisible.value = false;
}

// ─────────────────────────────────────────────────────────────────────────────
// Cleanup
// ─────────────────────────────────────────────────────────────────────────────

onUnmounted(() => {
  if (showTimeout) clearTimeout(showTimeout);
});
</script>

<style scoped>
.tooltip-wrapper {
  display: inline-flex;
  position: relative;
}

.tooltip-container {
  position: absolute;
  z-index: 10000;
  pointer-events: none;
}

.tooltip-content {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  background: var(--color-bg-elevated, #1e1e32);
  color: var(--color-text, #fff);
  padding: 8px 12px;
  border-radius: 8px;
  font-size: 0.8rem;
  line-height: 1.4;
  box-shadow: 
    0 4px 16px rgba(0, 0, 0, 0.4),
    0 0 0 1px rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(8px);
}

.tooltip-rich .tooltip-content {
  padding: 12px 16px;
  font-size: 0.85rem;
  box-shadow: 
    0 8px 32px rgba(0, 0, 0, 0.5),
    0 0 0 1px rgba(255, 255, 255, 0.08);
}

.tooltip-icon {
  font-size: 1.1em;
  flex-shrink: 0;
}

.tooltip-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.tooltip-title {
  color: var(--color-accent, #10b981);
  font-size: 0.85em;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.tooltip-description {
  margin: 0;
  color: var(--color-text-secondary, #b0b0c0);
}

/* Positioning transforms */
.tooltip-top {
  transform: translateX(-50%) translateY(-100%);
}

.tooltip-bottom {
  transform: translateX(-50%);
}

.tooltip-left {
  transform: translateX(-100%) translateY(-50%);
}

.tooltip-right {
  transform: translateY(-50%);
}

/* Arrow */
.tooltip-arrow {
  position: absolute;
  width: 0;
  height: 0;
}

.arrow-top {
  bottom: -6px;
  left: 50%;
  transform: translateX(-50%);
  border-left: 6px solid transparent;
  border-right: 6px solid transparent;
  border-top: 6px solid var(--color-bg-elevated, #1e1e32);
}

.arrow-bottom {
  top: -6px;
  left: 50%;
  transform: translateX(-50%);
  border-left: 6px solid transparent;
  border-right: 6px solid transparent;
  border-bottom: 6px solid var(--color-bg-elevated, #1e1e32);
}

.arrow-left {
  right: -6px;
  top: 50%;
  transform: translateY(-50%);
  border-top: 6px solid transparent;
  border-bottom: 6px solid transparent;
  border-left: 6px solid var(--color-bg-elevated, #1e1e32);
}

.arrow-right {
  left: -6px;
  top: 50%;
  transform: translateY(-50%);
  border-top: 6px solid transparent;
  border-bottom: 6px solid transparent;
  border-right: 6px solid var(--color-bg-elevated, #1e1e32);
}

/* Transitions */
.tooltip-fade-enter-active,
.tooltip-fade-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}

.tooltip-fade-enter-from,
.tooltip-fade-leave-to {
  opacity: 0;
}

.tooltip-top.tooltip-fade-enter-from,
.tooltip-top.tooltip-fade-leave-to {
  transform: translateX(-50%) translateY(calc(-100% + 4px));
}

.tooltip-bottom.tooltip-fade-enter-from,
.tooltip-bottom.tooltip-fade-leave-to {
  transform: translateX(-50%) translateY(-4px);
}
</style>
