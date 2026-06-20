<template>
  <div class="identity-node-container" @mousedown.stop @touchstart.stop>
    <div class="identity-header">
      <div class="header-icon">👁️</div>
      <div class="header-title">MIRROR TERMINAL</div>
      <div class="status-indicator"></div>
    </div>
    
    <div class="identity-body">
      <div class="avatar-ring">
        <div class="avatar-core"></div>
      </div>
      <div class="identity-name">{{ name }}</div>
      <div class="identity-role">Aethelnet Operator</div>
      
      <div class="metrics-grid">
        <div class="metric">
          <span class="m-label">CLEARANCE</span>
          <span class="m-val">LEVEL 9</span>
        </div>
        <div class="metric">
          <span class="m-label">ENTANGLEMENT</span>
          <span class="m-val active">STABLE</span>
        </div>
      </div>
    </div>

    <div class="identity-footer">
      <button class="action-btn" @click.stop="$emit('spawn-persona', node)">
        <span class="btn-icon">+</span> DEPLOY SUB-PERSONA
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  node: any
}>()

const name = computed(() => {
  return props.node.content?.split(':')[2] || 'ROOT IDENTITY'
})
</script>

<style scoped>
.identity-node-container {
  display: flex;
  flex-direction: column;
  width: 280px;
  background: rgba(15, 5, 20, 0.75);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(156, 39, 176, 0.3);
  border-radius: 12px;
  font-family: 'Inter', 'Space Mono', monospace;
  color: #fff;
  box-shadow: 0 15px 35px rgba(0,0,0,0.6), inset 0 0 20px rgba(156, 39, 176, 0.1);
  overflow: hidden;
  transition: all 0.4s cubic-bezier(0.25, 0.8, 0.25, 1);
}

.identity-node-container:hover {
  transform: translateY(-4px);
  box-shadow: 0 20px 45px rgba(0,0,0,0.7), inset 0 0 30px rgba(156, 39, 176, 0.2);
  border-color: rgba(156, 39, 176, 0.6);
}

.identity-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  background: linear-gradient(90deg, rgba(156, 39, 176, 0.2) 0%, transparent 100%);
  border-bottom: 1px solid rgba(255,255,255,0.05);
}

.header-icon {
  font-size: 14px;
}

.header-title {
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 2px;
  color: rgba(255,255,255,0.7);
  flex: 1;
}

.status-indicator {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #00FF41;
  box-shadow: 0 0 8px #00FF41;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% { opacity: 0.5; box-shadow: 0 0 4px #00FF41; }
  50% { opacity: 1; box-shadow: 0 0 12px #00FF41; }
  100% { opacity: 0.5; box-shadow: 0 0 4px #00FF41; }
}

.identity-body {
  padding: 24px 16px;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  background: radial-gradient(circle at center, rgba(156, 39, 176, 0.1) 0%, transparent 70%);
}

.avatar-ring {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  border: 2px solid rgba(156, 39, 176, 0.5);
  padding: 4px;
  margin-bottom: 16px;
  position: relative;
}

.avatar-ring::before {
  content: "";
  position: absolute;
  top: -2px; left: -2px; right: -2px; bottom: -2px;
  border-radius: 50%;
  border: 2px solid transparent;
  border-top-color: #9c27b0;
  animation: spin 3s linear infinite;
}

@keyframes spin {
  100% { transform: rotate(360deg); }
}

.avatar-core {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background: linear-gradient(135deg, #9c27b0, #4a148c);
  box-shadow: inset 0 0 10px rgba(0,0,0,0.5);
}

.identity-name {
  font-size: 16px;
  font-weight: 900;
  letter-spacing: 1px;
  text-transform: uppercase;
  color: #FFF;
  text-shadow: 0 2px 4px rgba(0,0,0,0.5);
}

.identity-role {
  font-size: 10px;
  color: #9c27b0;
  font-family: 'Space Mono', monospace;
  margin-top: 4px;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.metrics-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  width: 100%;
  margin-top: 24px;
}

.metric {
  background: rgba(0,0,0,0.4);
  border: 1px solid rgba(255,255,255,0.05);
  border-radius: 6px;
  padding: 8px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.m-label {
  font-size: 8px;
  color: rgba(255,255,255,0.4);
  letter-spacing: 1px;
}

.m-val {
  font-size: 11px;
  font-weight: 800;
  font-family: 'Space Mono', monospace;
}

.m-val.active {
  color: #00FF41;
  text-shadow: 0 0 5px rgba(0,255,65,0.5);
}

.identity-footer {
  padding: 12px 16px;
  background: rgba(0,0,0,0.3);
  border-top: 1px solid rgba(255,255,255,0.05);
}

.action-btn {
  width: 100%;
  background: rgba(156, 39, 176, 0.1);
  color: #d1c4e9;
  border: 1px solid rgba(156, 39, 176, 0.4);
  border-radius: 6px;
  padding: 10px;
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 1px;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 8px;
}

.action-btn:hover {
  background: rgba(156, 39, 176, 0.3);
  color: #FFF;
  border-color: #9c27b0;
  box-shadow: 0 0 15px rgba(156, 39, 176, 0.4);
}

.btn-icon {
  font-size: 14px;
  font-weight: 900;
}
</style>
