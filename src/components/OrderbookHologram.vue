<template>
  <div class="hologram-container" v-if="active">
    <div class="holo-core">
      <div class="holo-title">54D ORDER FLOW MATRIX</div>
      
      <div class="holo-matrix">
        <div class="ask-layer">
          <div v-for="i in 5" :key="'ask'+i" class="book-row ask" :style="{ width: `${40 + Math.random() * 60}%`, opacity: 1 - (i * 0.15) }">
            <span class="price">{{ (8.543 + (6-i)*0.01).toFixed(3) }}</span>
            <span class="vol">{{ Math.floor(Math.random() * 500) + 100 }}</span>
          </div>
        </div>
        
        <div class="spread-indicator">
          <span>SPREAD: 0.002</span>
          <div class="pulse-line"></div>
        </div>
        
        <div class="bid-layer">
          <div v-for="i in 5" :key="'bid'+i" class="book-row bid" :style="{ width: `${40 + Math.random() * 60}%`, opacity: 1 - (i * 0.15) }">
            <span class="price">{{ (8.540 - i*0.01).toFixed(3) }}</span>
            <span class="vol">{{ Math.floor(Math.random() * 500) + 100 }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';

const active = ref(true);

// Mock dynamic updates
onMounted(() => {
  setInterval(() => {
    // Just force a re-render/update if we wanted reactive data
  }, 500);
});
</script>

<style scoped>
.hologram-container {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%) perspective(1000px) rotateX(45deg) rotateZ(-15deg);
  width: 600px;
  height: 800px;
  pointer-events: none;
  z-index: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.holo-core {
  background: radial-gradient(circle at center, rgba(16, 185, 129, 0.05) 0%, transparent 70%);
  border: 1px solid rgba(16, 185, 129, 0.2);
  border-radius: 50%;
  width: 100%;
  height: 100%;
  box-shadow: 0 0 100px rgba(16, 185, 129, 0.1) inset, 0 0 50px rgba(16, 185, 129, 0.2);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  animation: float 6s infinite ease-in-out;
}

@keyframes float {
  0%, 100% { transform: translateY(0px) rotateZ(0deg); }
  50% { transform: translateY(-20px) rotateZ(2deg); }
}

.holo-title {
  color: #10b981;
  font-family: monospace;
  font-size: 1.5rem;
  letter-spacing: 4px;
  text-shadow: 0 0 10px #10b981;
  margin-bottom: 40px;
  opacity: 0.8;
}

.holo-matrix {
  width: 80%;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.book-row {
  display: flex;
  justify-content: space-between;
  padding: 8px 16px;
  font-family: monospace;
  font-size: 1.2rem;
  border-radius: 4px;
  transition: width 0.3s ease;
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
.vol { opacity: 0.8; }

.spread-indicator {
  text-align: center;
  color: #e2e8f0;
  font-family: monospace;
  font-size: 1rem;
  padding: 20px 0;
  position: relative;
}

.pulse-line {
  position: absolute;
  top: 50%;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.5), transparent);
  box-shadow: 0 0 10px rgba(255,255,255,0.8);
  animation: scan 2s infinite linear;
}

@keyframes scan {
  0% { opacity: 0; transform: scaleX(0); }
  50% { opacity: 1; transform: scaleX(1); }
  100% { opacity: 0; transform: scaleX(0); }
}
</style>
