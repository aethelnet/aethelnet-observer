<template>
  <div class="node-details" :class="{ expanded: isExpanded }">
    <div class="details-header">
      <!-- Title & Type -->
      <div class="header-main">
          <h3>{{ node.id }}</h3>
          <span class="node-type">{{ t(`nodes.types.${node.type}`) }}</span>
      </div>

      <!-- Actions -->
      <div class="header-actions">
        <button class="expand-btn" @click="toggleExpand" :title="isExpanded ? t('ui.actions.collapse') : t('ui.actions.expand')">
          <svg v-if="!isExpanded" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M15 3h6v6M9 21H3v-6M21 3l-7 7M3 21l7-7"/></svg>
          <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M4 14h6v6M14 4h6v6M10 14l-7 7M21 3l-7 7"/></svg>
        </button>
        
        <PinButton 
            :itemId="node.id"
            :itemType="node.type"
            :itemLabel="node.label || node.id"
            :itemMetadata="{ color: node.color, sentiment: node.data?.sentiment, price: node.data?.price }"
            size="sm"
            :showLabel="false"
        />
        
        <button class="close-btn" @click="$emit('close')" :title="t('ui.actions.close')">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><path d="M18 6L6 18M6 6l12 12"/></svg>
        </button>
      </div>
    </div>

    <!-- Status / Sentiment -->
    <div class="node-status" :style="{ color: node.color }">
      {{ node.data?.sentiment || 'NEUTRAL' }}
    </div>
    
    <div class="node-body">
      <!-- TLDR Section (New) -->
      <div class="tldr-section">
          <p>{{ tldrText }}</p>
      </div>

      <!-- Stats Grid -->
      <div class="stat-grid">
        <div class="stat-item" :title="t('nodes.details.rsi')">
          <span class="label">RSI(14)</span>
          <span class="value" :style="{ color: getRSIColor(node.data?.rsi) }">{{ node.data?.rsi?.toFixed(1) || '--' }}</span>
        </div>
        <div class="stat-item" :title="t('nodes.details.drift')">
          <span class="label">DRIFT</span>
          <span class="value" :class="getSignClass(node.data?.drift, 0)">{{ node.data?.drift?.toFixed(2) || '0.00' }}%</span>
        </div>
        <div class="stat-item" :title="t('nodes.details.turbulence')">
          <span class="label">TURBULENCE</span>
          <span class="value">{{ ((node.data?.turbulence || 0) * 100).toFixed(1) }}%</span>
        </div>
        <div class="stat-item">
          <span class="label">TIER</span>
          <span class="value">{{ node.tier }}</span>
        </div>
      </div>
      
      <!-- Connection Summary -->
      <div class="connections-section" v-if="connections.length > 0 && !isExpanded">
        <div class="section-label">{{ t('ui.connections.title') }} ({{ connections.length }})</div>
        <div class="connection-list">
          <div v-for="conn in connections.slice(0, 5)" :key="conn.id" class="connection-item" @click="$emit('select', conn.id)">
            <span class="conn-dot" :style="{ background: conn.color }"></span>
            <span class="conn-label">{{ conn.label || conn.id }}</span>
            <span class="conn-sentiment" v-if="conn.sentiment">{{ conn.sentiment }}</span>
          </div>
          <div v-if="connections.length > 5" class="more-connections">
            {{ t('ui.connections.more', { count: connections.length - 5 }) }}
          </div>
        </div>
      </div>

      <!-- INFINITE WORKBENCH (Andersrum) -->
      <div class="workbench-section" v-if="isExpanded">
        <div class="section-label">Local Workbench: {{ node.id }}</div>
        <div class="workbench-container">
          <InfiniteCanvasView @implode="toggleExpand" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from '../composables/useI18n'
import PinButton from './PinButton.vue'
import InfiniteCanvasView from '../views/InfiniteCanvasView.vue'

const props = defineProps<{
    node: any
    connections: any[]
}>()

const emit = defineEmits(['close', 'select'])
const { t } = useI18n()

const isExpanded = ref(false)

const tldrText = computed(() => {
    return t(`nodes.tldr.${props.node.type}`, {
        name: props.node.label || props.node.id,
        price: formatCurrency(props.node.data?.price),
        market: props.node.data?.market || 'Global',
        confidence: ((props.node.data?.confidence || 0) * 100).toFixed(0)
    })
})


function toggleExpand() {
    isExpanded.value = !isExpanded.value
}

function getRSIColor(rsi: any) {
  if (rsi === undefined || rsi === null) return '#94a3b8' 
  if (rsi > 70) return '#ef4444' 
  if (rsi < 30) return '#10b981' 
  return '#1e293b'
}

function getSignClass(val: any, baseline: number) {
  if (val === undefined || val === null) return ''
  return val > baseline ? 'bullish' : 'bearish'
}

function formatCurrency(val: any) {
    if (!val) return '0.00'
    return val.toFixed(2)
}
</script>

<style scoped>
.node-details {
  position: absolute; right: 20px; top: 80px; width: 280px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(0,0,0,0.1);
  border-radius: 12px;
  box-shadow: 0 10px 30px rgba(0,0,0,0.1);
  padding: 16px;
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
  color: #0f172a;
  z-index: 20;
}
.node-details.expanded {
  width: 900px;
  height: 600px;
  display: flex;
  flex-direction: column;
}

.node-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.details-header {
  display: flex; justify-content: space-between; align-items: flex-start;
  margin-bottom: 8px;
}
.header-main { display: flex; flex-direction: column; gap: 2px; }
.header-main h3 { margin: 0; font-size: 16px; font-weight: 700; letter-spacing: -0.02em; }
.node-type { font-size: 10px; text-transform: uppercase; color: #64748b; font-weight: 600; letter-spacing: 0.05em; }

.header-actions { display: flex; gap: 6px; align-items: center; }
.expand-btn, .close-btn {
  background: none; border: none; cursor: pointer; padding: 4px;
  color: #94a3b8; transition: color 0.2s;
  display: flex; align-items: center; justify-content: center;
  border-radius: 4px;
}
.expand-btn:hover, .close-btn:hover { color: #0f172a; background: #f1f5f9; }

.node-status {
  font-size: 11px; font-weight: 700; letter-spacing: 0.05em;
  margin-bottom: 16px; display: inline-block;
  padding: 2px 6px; background: #f1f5f9; border-radius: 4px;
}

.tldr-section {
    font-size: 13px; line-height: 1.5; color: #334155;
    margin-bottom: 16px; border-left: 2px solid #cbd5e1; padding-left: 10px;
}

.stat-grid {
  display: grid; grid-template-columns: 1fr 1fr; gap: 8px;
  margin-bottom: 16px;
}
.stat-item {
  background: #f8fafc; padding: 8px; border-radius: 6px;
  display: flex; flex-direction: column; gap: 2px;
}
.stat-item .label { font-size: 9px; color: #64748b; font-weight: 600; text-transform: uppercase; }
.stat-item .value { font-size: 13px; font-weight: 600; color: #0f172a; font-variant-numeric: tabular-nums; }
.stat-item .value.bullish { color: #10b981; }
.stat-item .value.bearish { color: #ef4444; }

.connections-section {
    border-top: 1px solid #e2e8f0; padding-top: 12px;
}
.section-label { font-size: 10px; font-weight: 700; color: #94a3b8; margin-bottom: 8px; text-transform: uppercase; }
.connection-list { display: flex; flex-direction: column; gap: 4px; }
.connection-item {
    display: flex; align-items: center; gap: 8px;
    padding: 6px; border-radius: 4px; cursor: pointer;
    transition: background 0.1s;
}
.connection-item:hover { background: #f1f5f9; }
.conn-dot { width: 6px; height: 6px; border-radius: 50%; opacity: 0.8; }
.conn-label { font-size: 12px; font-weight: 500; flex: 1; }
.conn-sentiment { font-size: 9px; font-weight: 600; color: #64748b; }
.more-connections { font-size: 10px; color: #94a3b8; text-align: center; margin-top: 4px; font-weight: 500; }

.workbench-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  border-top: 1px solid #e2e8f0;
  padding-top: 12px;
  margin-top: 12px;
  min-height: 0;
}
.workbench-container {
  flex: 1;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid #e2e8f0;
  position: relative;
  background: #0f1015; /* Dark background for the workbench */
}
</style>
