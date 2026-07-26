<template>
  <div class="telemetry-hud glass-panel">
    <div class="hud-header">
      <div class="blinking-dot"></div>
      <span class="hud-title">SYS_TELEMETRY</span>
    </div>
    
    <div class="metric-row">
      <span class="label">NODES</span>
      <span class="value">{{ telemetry?.lgnn_core?.total_nodes || '...' }}</span>
    </div>
    <div class="metric-row">
      <span class="label">EDGES</span>
      <span class="value">{{ telemetry?.lgnn_core?.total_edges || '...' }}</span>
    </div>
    <div class="metric-row">
      <span class="label">DENSITY</span>
      <span class="value">{{ densityPercent }}%</span>
    </div>
    <div class="metric-row">
      <span class="label">API_BURN</span>
      <span class="value api-cost">${{ telemetry?.lgnn_core?.estimated_api_cost_usd?.toFixed(6) || '0.000000' }}</span>
    </div>
    <div class="metric-row">
      <span class="label">CPU_LOAD</span>
      <span class="value">{{ telemetry?.hardware?.cpu_load_percent || '...' }}%</span>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue';

const telemetry = ref(null);
let interval = null;

const densityPercent = computed(() => {
  if (!telemetry.value?.lgnn_core?.network_density) return '0.00';
  return (telemetry.value.lgnn_core.network_density * 100).toFixed(4);
});

const fetchTelemetry = async () => {
  try {
    const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
    const res = await fetch(`${baseUrl}/telemetry/pulse`);
    if (res.ok) {
      telemetry.value = await res.json();
    }
  } catch (e) {
    console.warn("Telemetry offline or unreachable", e);
  }
};

onMounted(() => {
  fetchTelemetry();
  interval = setInterval(fetchTelemetry, 3000); // 3 seconds matches backend cache TTL
});

onUnmounted(() => {
  if (interval) clearInterval(interval);
});
</script>

<style scoped>
.telemetry-hud {
  position: absolute;
  top: 20px;
  right: 20px;
  width: 220px;
  background: rgba(10, 15, 20, 0.85);
  border: 1px solid rgba(0, 255, 128, 0.3);
  backdrop-filter: blur(10px);
  padding: 15px;
  border-radius: 4px;
  color: #00ff80;
  font-family: 'Courier New', Courier, monospace;
  z-index: 1000;
  box-shadow: 0 0 15px rgba(0, 255, 128, 0.1);
  pointer-events: none; /* Let clicks pass through to the 3D graph */
}

.hud-header {
  display: flex;
  align-items: center;
  margin-bottom: 15px;
  border-bottom: 1px dashed rgba(0, 255, 128, 0.3);
  padding-bottom: 8px;
}

.blinking-dot {
  width: 8px;
  height: 8px;
  background-color: #00ff80;
  border-radius: 50%;
  margin-right: 10px;
  animation: pulse 1.5s infinite;
}

.hud-title {
  font-weight: bold;
  letter-spacing: 1px;
}

.metric-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 13px;
}

.label {
  color: rgba(0, 255, 128, 0.7);
}

.value {
  font-weight: bold;
  text-shadow: 0 0 5px rgba(0, 255, 128, 0.5);
}

.api-cost {
  color: #ff3366;
  text-shadow: 0 0 5px rgba(255, 51, 102, 0.5);
}

@keyframes pulse {
  0% { opacity: 1; box-shadow: 0 0 0 0 rgba(0, 255, 128, 0.7); }
  70% { opacity: 0.3; box-shadow: 0 0 0 6px rgba(0, 255, 128, 0); }
  100% { opacity: 1; box-shadow: 0 0 0 0 rgba(0, 255, 128, 0); }
}
</style>
