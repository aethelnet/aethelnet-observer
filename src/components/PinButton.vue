<template>
  <button
    class="pin-button"
    :class="{ 
      'is-pinned': pinned,
      'is-animating': isAnimating 
    }"
    @click="handleClick"
    :title="tooltip"
    :aria-label="pinned ? 'Unpin item' : 'Pin item'"
    :aria-pressed="pinned"
  >
    <span class="pin-icon">
      <svg 
        v-if="pinned" 
        xmlns="http://www.w3.org/2000/svg" 
        viewBox="0 0 24 24" 
        fill="currentColor"
        class="icon-filled"
      >
        <path d="M16 4h-2v.5c0 .55-.45 1-1 1H9c-.55 0-1-.45-1-1V4H6c-.55 0-1 .45-1 1v6.59c0 .27.11.52.29.71l2.79 2.79c.18.18.29.42.29.68V20h5v-4.23c0-.26.11-.52.29-.7l2.79-2.79c.18-.19.29-.44.29-.71V5c0-.55-.45-1-1-1z"/>
      </svg>
      <svg 
        v-else 
        xmlns="http://www.w3.org/2000/svg" 
        viewBox="0 0 24 24" 
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        class="icon-outline"
      >
        <path d="M16 4h-2v.5c0 .55-.45 1-1 1H9c-.55 0-1-.45-1-1V4H6c-.55 0-1 .45-1 1v6.59c0 .27.11.52.29.71l2.79 2.79c.18.18.29.42.29.68V20h5v-4.23c0-.26.11-.52.29-.7l2.79-2.79c.18-.19.29-.44.29-.71V5c0-.55-.45-1-1-1z"/>
      </svg>
    </span>
    <span v-if="showLabel" class="pin-label">
      {{ pinned ? 'Pinned' : 'Pin' }}
    </span>
    
    <!-- Tooltip (custom for enhanced styling) -->
    <span class="pin-tooltip" v-if="showTooltip">
      {{ tooltip }}
    </span>
  </button>
</template>

<script setup lang="ts">
import { ref, computed, toRef } from 'vue';
import { usePinnedItems, type PinnedItem, TOOLTIPS } from '../composables/usePinnedItems';

// ─────────────────────────────────────────────────────────────────────────────
// Props
// ─────────────────────────────────────────────────────────────────────────────

const props = withDefaults(defineProps<{
  /** Unique identifier for this pinnable item */
  itemId: string;
  /** Type of item being pinned */
  itemType: PinnedItem['type'];
  /** Display label for the pinned item */
  itemLabel: string;
  /** Optional metadata to store with the pin */
  itemMetadata?: PinnedItem['metadata'];
  /** Show text label next to icon */
  showLabel?: boolean;
  /** Show custom tooltip on hover */
  showTooltip?: boolean;
  /** Size variant */
  size?: 'sm' | 'md' | 'lg';
}>(), {
  showLabel: false,
  showTooltip: true,
  size: 'md',
});

// ─────────────────────────────────────────────────────────────────────────────
// Emits
// ─────────────────────────────────────────────────────────────────────────────

const emit = defineEmits<{
  (e: 'pinned', item: PinnedItem): void;
  (e: 'unpinned', itemId: string): void;
  (e: 'toggled', isPinned: boolean): void;
}>();

// ─────────────────────────────────────────────────────────────────────────────
// State
// ─────────────────────────────────────────────────────────────────────────────

const { isPinned, toggle, getItem } = usePinnedItems();
const isAnimating = ref(false);

// ─────────────────────────────────────────────────────────────────────────────
// Computed
// ─────────────────────────────────────────────────────────────────────────────

const pinned = computed(() => isPinned(props.itemId));

const tooltip = computed(() => 
  pinned.value 
    ? TOOLTIPS.pinButton.pinned 
    : TOOLTIPS.pinButton.unpinned
);

// ─────────────────────────────────────────────────────────────────────────────
// Methods
// ─────────────────────────────────────────────────────────────────────────────

function handleClick(event: MouseEvent) {
  event.stopPropagation();
  
  // Trigger animation
  isAnimating.value = true;
  setTimeout(() => { isAnimating.value = false; }, 300);
  
  const wasPinned = pinned.value;
  
  const newState = toggle({
    id: props.itemId,
    type: props.itemType,
    label: props.itemLabel,
    metadata: props.itemMetadata,
  });
  
  // Emit events
  emit('toggled', newState);
  
  if (newState) {
    const item = getItem(props.itemId);
    if (item) emit('pinned', item);
  } else {
    emit('unpinned', props.itemId);
  }
}
</script>

<style scoped>
.pin-button {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: var(--color-text-muted, #888);
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
  font-size: 0.875rem;
}

.pin-button:hover {
  background: rgba(255, 255, 255, 0.05);
  color: var(--color-text, #fff);
}

.pin-button:hover .pin-tooltip {
  opacity: 1;
  visibility: visible;
  transform: translateX(-50%) translateY(0);
}

.pin-button.is-pinned {
  color: var(--color-accent, #10b981);
  background: rgba(16, 185, 129, 0.1);
}

.pin-button.is-pinned:hover {
  background: rgba(16, 185, 129, 0.2);
}

.pin-button.is-animating .pin-icon {
  animation: pin-bounce 0.3s ease;
}

@keyframes pin-bounce {
  0% { transform: scale(1); }
  50% { transform: scale(1.3); }
  100% { transform: scale(1); }
}

.pin-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
}

.pin-icon svg {
  width: 100%;
  height: 100%;
}

.icon-filled {
  filter: drop-shadow(0 0 4px currentColor);
}

.pin-label {
  font-weight: 500;
  white-space: nowrap;
}

/* Tooltip */
.pin-tooltip {
  position: absolute;
  bottom: calc(100% + 8px);
  left: 50%;
  transform: translateX(-50%) translateY(4px);
  background: var(--color-bg-elevated, #1a1a2e);
  color: var(--color-text, #fff);
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 0.75rem;
  white-space: nowrap;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  border: 1px solid var(--color-border, #333);
  opacity: 0;
  visibility: hidden;
  transition: all 0.2s ease;
  z-index: 1000;
  pointer-events: none;
}

.pin-tooltip::after {
  content: '';
  position: absolute;
  top: 100%;
  left: 50%;
  transform: translateX(-50%);
  border: 6px solid transparent;
  border-top-color: var(--color-bg-elevated, #1a1a2e);
}

/* Size variants */
.pin-button[data-size="sm"] {
  padding: 4px 8px;
  font-size: 0.75rem;
}

.pin-button[data-size="sm"] .pin-icon {
  width: 14px;
  height: 14px;
}

.pin-button[data-size="lg"] {
  padding: 8px 14px;
  font-size: 1rem;
}

.pin-button[data-size="lg"] .pin-icon {
  width: 22px;
  height: 22px;
}

/* Focus state for accessibility */
.pin-button:focus-visible {
  outline: 2px solid var(--color-accent, #10b981);
  outline-offset: 2px;
}
</style>
