<template>
  <div class="holo-frame" :style="{ '--frame-color': color, width: width + 'px' }">
    <div class="holo-header" @mousedown="onHeaderMouseDown">
      <div class="holo-icon"><slot name="icon">❖</slot></div>
      <div class="holo-title">{{ title }}</div>
      <div class="holo-actions">
        <button class="holo-btn" @click.stop="$emit('action-primary')" title="Options">
          <slot name="action-primary-icon">⚙</slot>
        </button>
        <button class="holo-btn" @click.stop="$emit('collapse')" title="Collapse">_</button>
      </div>
    </div>
    <div class="holo-body">
      <slot></slot>
    </div>
    <div class="holo-footer" v-if="$slots.footer">
      <slot name="footer"></slot>
    </div>
  </div>
</template>

<script setup lang="ts">
const props = defineProps({
  title: { type: String, default: 'UNKNOWN APP' },
  color: { type: String, default: '#00d4ff' },
  width: { type: Number, default: 320 }
})

const emit = defineEmits(['collapse', 'action-primary'])

function onHeaderMouseDown(e: MouseEvent) {
  // Let the event bubble up to LgnnView.vue startDrag handler
  // so the window can be dragged by the header
}
</script>

<style scoped>
.holo-frame {
  background: rgba(10, 15, 20, 0.85);
  backdrop-filter: blur(12px);
  border: 1px solid var(--frame-color);
  border-radius: 8px;
  box-shadow: 0 4px 30px rgba(0, 0, 0, 0.5), inset 0 0 20px rgba(0, 212, 255, 0.05);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  font-family: var(--font-family-mono);
  color: var(--color-text-main);
  transition: box-shadow 0.3s ease;
}

.holo-frame:hover {
  box-shadow: 0 8px 40px rgba(0, 0, 0, 0.7), 0 0 15px var(--frame-color);
}

.holo-header {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  background: linear-gradient(90deg, rgba(255,255,255,0.05), transparent);
  border-bottom: 1px solid rgba(255,255,255,0.1);
  cursor: grab;
}

.holo-header:active {
  cursor: grabbing;
}

.holo-icon {
  color: var(--frame-color);
  margin-right: 8px;
  font-size: 14px;
}

.holo-title {
  flex: 1;
  font-size: 12px;
  font-weight: 900;
  letter-spacing: 1px;
  color: #fff;
  text-transform: uppercase;
  user-select: none;
}

.holo-actions {
  display: flex;
  gap: 4px;
}

.holo-btn {
  background: transparent;
  border: none;
  color: #888;
  cursor: pointer;
  font-size: 12px;
  padding: 4px;
  transition: color 0.2s;
}

.holo-btn:hover {
  color: #fff;
}

.holo-body {
  padding: 12px;
  flex: 1;
  overflow-y: auto;
  max-height: 500px;
}

.holo-body::-webkit-scrollbar {
  width: 4px;
}
.holo-body::-webkit-scrollbar-thumb {
  background: var(--frame-color);
  border-radius: 4px;
}

.holo-footer {
  padding: 8px 12px;
  border-top: 1px solid rgba(255,255,255,0.1);
  background: rgba(0,0,0,0.2);
  font-size: 10px;
  color: #666;
}
</style>
