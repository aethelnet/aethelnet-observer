<template>
  <div class="orderbook-node" @mousedown.stop @touchstart.stop>
    <div class="node-header">
      <h3>54D ORDER FLOW</h3>
      <span class="status-pulse"></span>
    </div>
    
    <div class="book-container">
      <div class="ask-layer">
        <div v-for="(ask, idx) in asks.slice(0, 5)" :key="'ask'+idx" class="book-row ask" :style="{ width: `${40 + Math.random() * 60}%` }">
          <span class="price">{{ parseFloat(ask[0]).toFixed(2) }}</span>
          <span class="vol">{{ parseFloat(ask[1]).toFixed(4) }}</span>
        </div>
        <div v-if="asks.length === 0" class="book-row ask" style="width: 100%; opacity: 0.5;">
          <span>Waiting for stream...</span>
        </div>
      </div>
      
      <div class="spread-indicator">
        <span>SPREAD</span>
      </div>
      
      <div class="bid-layer">
        <div v-for="(bid, idx) in bids.slice(0, 5)" :key="'bid'+idx" class="book-row bid" :style="{ width: `${40 + Math.random() * 60}%` }">
          <span class="price">{{ parseFloat(bid[0]).toFixed(2) }}</span>
          <span class="vol">{{ parseFloat(bid[1]).toFixed(4) }}</span>
        </div>
        <div v-if="bids.length === 0" class="book-row bid" style="width: 100%; opacity: 0.5;">
          <span>Waiting for stream...</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { defineProps } from 'vue';

const props = defineProps({
  bids: { type: Array, default: () => [] },
  asks: { type: Array, default: () => [] }
});
</script>

<style scoped>
.orderbook-node {
  width: 100%;
  padding: 15px;
  background: rgba(10, 15, 20, 0.85);
  border-radius: 12px;
  border: 1px solid rgba(16, 185, 129, 0.4);
  box-shadow: 0 4px 20px rgba(0,0,0,0.5), inset 0 0 15px rgba(16, 185, 129, 0.1);
  backdrop-filter: blur(10px);
}
.node-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  color: #10b981;
}
.node-header h3 {
  margin: 0;
  font-family: monospace;
  font-size: 1rem;
  letter-spacing: 1px;
}
.status-pulse {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: #10b981;
  box-shadow: 0 0 10px #10b981;
  animation: pulse 1s infinite;
}
@keyframes pulse {
  0% { opacity: 0.5; }
  50% { opacity: 1; }
  100% { opacity: 0.5; }
}
.book-container {
  display: flex;
  flex-direction: column;
  gap: 5px;
}
.book-row {
  display: flex;
  justify-content: space-between;
  padding: 4px 8px;
  font-family: monospace;
  font-size: 0.9rem;
  border-radius: 2px;
}
.ask {
  background: linear-gradient(90deg, rgba(239, 68, 68, 0.2) 0%, transparent 100%);
  color: #ef4444;
  border-left: 2px solid #ef4444;
}
.bid {
  background: linear-gradient(90deg, rgba(16, 185, 129, 0.2) 0%, transparent 100%);
  color: #10b981;
  border-left: 2px solid #10b981;
}
.price { font-weight: bold; }
.vol { opacity: 0.8; font-size: 0.8rem; }
.spread-indicator {
  text-align: center;
  color: #94a3b8;
  font-family: monospace;
  font-size: 0.75rem;
  padding: 6px 0;
  border-top: 1px dashed rgba(255,255,255,0.1);
  border-bottom: 1px dashed rgba(255,255,255,0.1);
  margin: 6px 0;
  letter-spacing: 2px;
}
</style>
