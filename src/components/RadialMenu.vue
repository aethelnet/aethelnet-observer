<template>
  <div v-if="visible" class="radial-menu-overlay" @click.stop="close" @contextmenu.prevent="close">
    <div 
      class="radial-menu-center"
      :style="{ left: `${x}px`, top: `${y}px` }"
    >
      <div 
        v-for="(item, index) in items" 
        :key="item.type"
        class="radial-menu-item"
        :style="getItemStyle(index)"
        @click.stop="selectItem(item)"
      >
        <span class="item-label">{{ item.label }}</span>
        <div class="item-icon">
          <i :class="item.icon"></i>
        </div>
      </div>
      
      <div class="radial-center-dot"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps({
  visible: { type: Boolean, default: false },
  x: { type: Number, default: 0 },
  y: { type: Number, default: 0 },
  items: {
    type: Array as () => Array<{ type: string, label: string, icon: string }>,
    default: () => []
  },
  radius: { type: Number, default: 100 }
})

const emit = defineEmits(['select', 'close'])

function getItemStyle(index: number) {
  const total = props.items.length
  // Start from top (-90 degrees)
  const angle = (index / total) * Math.PI * 2 - Math.PI / 2
  
  const tx = Math.cos(angle) * props.radius
  const ty = Math.sin(angle) * props.radius

  return {
    '--tx': `${tx}px`,
    '--ty': `${ty}px`,
    transitionDelay: `${index * 0.03}s` // staggering effect on open
  }
}

function selectItem(item: any) {
  emit('select', item.type)
  close()
}

function close() {
  emit('close')
}
</script>

<style scoped>
.radial-menu-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  z-index: 9999;
  background: rgba(0, 0, 0, 0.2);
  backdrop-filter: blur(2px);
  animation: fadeIn 0.2s ease-out;
}

.radial-menu-center {
  position: absolute;
  width: 0;
  height: 0;
}

.radial-center-dot {
  position: absolute;
  width: 16px;
  height: 16px;
  background: var(--color-accent, #3b82f6);
  border-radius: 50%;
  transform: translate(-50%, -50%);
  box-shadow: 0 0 15px var(--color-accent, #3b82f6);
  animation: pulseDot 2s infinite;
}

.radial-menu-item {
  position: absolute;
  top: 0;
  left: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transform: translate(var(--tx), var(--ty)) translate(-50%, -50%) scale(1);
  transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  animation: popIn 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275) both;
}

.radial-menu-item:hover {
  transform: translate(var(--tx), var(--ty)) translate(-50%, -50%) scale(1.15);
  z-index: 10;
}

.item-icon {
  width: 48px;
  height: 48px;
  background: var(--color-bg-panel, #ffffff);
  border: 1px solid var(--color-border, #e2e8f0);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  color: var(--color-text, #1e293b);
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  transition: all 0.2s;
}

.radial-menu-item:hover .item-icon {
  border-color: var(--color-accent, #3b82f6);
  color: var(--color-accent, #3b82f6);
  box-shadow: 0 6px 16px rgba(59, 130, 246, 0.3);
}

.item-label {
  margin-bottom: 8px;
  background: var(--color-bg-panel, #ffffff);
  color: var(--color-text, #1e293b);
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
  opacity: 0.8;
  transition: all 0.2s;
  pointer-events: none;
  white-space: nowrap;
}

.radial-menu-item:hover .item-label {
  opacity: 1;
  background: var(--color-accent, #3b82f6);
  color: white;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes popIn {
  0% { transform: translate(var(--tx), var(--ty)) translate(-50%, -50%) scale(0.5); opacity: 0; }
  100% { transform: translate(var(--tx), var(--ty)) translate(-50%, -50%) scale(1); opacity: 1; }
}

@keyframes pulseDot {
  0% { transform: translate(-50%, -50%) scale(1); opacity: 0.8; }
  50% { transform: translate(-50%, -50%) scale(1.5); opacity: 0.4; }
  100% { transform: translate(-50%, -50%) scale(1); opacity: 0.8; }
}
</style>
