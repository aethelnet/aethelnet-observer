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
  background: rgba(15, 23, 42, 0.85);
  backdrop-filter: blur(25px) saturate(200%);
  border-radius: 12px;
  border: 1px solid rgba(14, 165, 233, 0.3);
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.7), inset 0 0 20px rgba(14, 165, 233, 0.05);
  position: relative;
  overflow: hidden;
}
.orderbook-node::before {
  content: "";
  position: absolute;
  top: 0; left: 0; width: 100%; height: 100%;
  background-image: linear-gradient(rgba(14, 165, 233, 0.05) 1px, transparent 1px), linear-gradient(90deg, rgba(14, 165, 233, 0.05) 1px, transparent 1px);
  background-size: 20px 20px;
  pointer-events: none;
  opacity: 0.5;
  z-index: 0;
}
.node-header, .book-container {
  position: relative;
  z-index: 2;
}
.node-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  color: #0ea5e9;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  padding-bottom: 12px;
}
.node-header h3 {
  margin: 0;
  font-family: 'Space Mono', monospace;
  font-size: 14px;
  font-weight: 700;
  letter-spacing: 1px;
  color: #f0f9ff;
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
  background: rgba(239, 68, 68, 0.15);
  color: #ef4444;
}
.bid {
  background: rgba(16, 185, 129, 0.15);
  color: #10b981;
}
.price { font-weight: bold; text-shadow: 0 0 5px currentColor; }
.vol { opacity: 0.8; font-size: 0.8rem; color: #f8fafc; }
.spread-indicator {
  text-align: center;
  color: #38bdf8;
  font-family: 'Space Mono', monospace;
  font-size: 16px;
  font-weight: bold;
  text-shadow: 0 0 10px rgba(56, 189, 248, 0.5);
  padding: 8px 0;
  border-top: 1px dashed rgba(255,255,255,0.1);
  border-bottom: 1px dashed rgba(255,255,255,0.1);
  margin: 8px 0;
  background: rgba(0,0,0,0.2);
}
</style>
