<template>
  <div class="graviton-node" @mousedown.stop>
    <div class="gravity-waves" :class="{ active: isPulling }">
      <div class="wave w1"></div>
      <div class="wave w2"></div>
      <div class="wave w3"></div>
    </div>
    
    <div class="header">
      <div class="icon"><i class="fas fa-magnet"></i></div>
      <div class="title-wrap">
        <div class="title">GRAVITON</div>
        <div class="subtitle">Concept Attractor</div>
      </div>
    </div>
    
    <div class="content">
      <div class="input-group">
        <label>Gravitational Center (Topic/Tag)</label>
        <input type="text" v-model="topic" placeholder="e.g. Neural Networks..." />
      </div>
      
      <div class="controls">
        <button class="pull-btn" @click="pullConcepts" :disabled="isPulling || !topic">
          <span v-if="isPulling">Generating Singularity...</span>
          <span v-else>Engage Gravity Well</span>
        </button>
      </div>

      <div class="pulled-nodes" v-if="pulled.length > 0">
        <div class="pulled-title">Caught in Orbit:</div>
        <div class="orbit-item" v-for="(item, i) in pulled" :key="i">
          {{ item }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const props = defineProps<{ node: any }>()
const topic = ref('')
const isPulling = ref(false)
const pulled = ref<string[]>([])

async function pullConcepts() {
  if (!topic.value) return
  isPulling.value = true
  pulled.value = []
  
  await new Promise(r => setTimeout(r, 2500))
  
  pulled.value = [
    `Concept: Evolution of ${topic.value}`,
    `Paper: Core mechanics of ${topic.value}`,
    `Critique: The limitations of ${topic.value}`
  ]
  isPulling.value = false
}
</script>

<style scoped>
.graviton-node {
  background: rgba(10, 0, 20, 0.95);
  border: 1px solid rgba(138, 43, 226, 0.5);
  border-radius: 50% 50% 12px 12px;
  width: 280px;
  color: #fff;
  font-family: 'Inter', sans-serif;
  box-shadow: 0 0 30px rgba(138, 43, 226, 0.2);
  position: relative;
  overflow: hidden;
  padding-top: 20px;
}

.gravity-waves {
  position: absolute;
  top: -50px; left: 50%;
  transform: translateX(-50%);
  width: 1px; height: 1px;
  z-index: 0;
  pointer-events: none;
}

.wave {
  position: absolute;
  top: 50%; left: 50%;
  transform: translate(-50%, -50%);
  border-radius: 50%;
  border: 1px solid rgba(138, 43, 226, 0.5);
  opacity: 0;
}

.gravity-waves.active .wave {
  animation: ripple 2s infinite cubic-bezier(0.1, 0.8, 0.3, 1);
}
.gravity-waves.active .w1 { animation-delay: 0s; }
.gravity-waves.active .w2 { animation-delay: 0.6s; }
.gravity-waves.active .w3 { animation-delay: 1.2s; }

@keyframes ripple {
  0% { width: 0px; height: 0px; opacity: 1; border-width: 4px; }
  100% { width: 300px; height: 300px; opacity: 0; border-width: 1px; }
}

.header {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 10px;
}

.icon {
  font-size: 28px;
  color: #8a2be2;
  text-shadow: 0 0 15px #8a2be2;
  margin-bottom: 8px;
}

.title { font-weight: 900; letter-spacing: 3px; font-size: 14px; color: #d4a5ff; text-align: center; }
.subtitle { font-size: 9px; color: #888; text-transform: uppercase; letter-spacing: 2px; text-align: center; }

.content {
  position: relative;
  z-index: 1;
  background: rgba(0, 0, 0, 0.6);
  padding: 16px;
  border-top: 1px solid rgba(138, 43, 226, 0.3);
}

.input-group label { display: block; font-size: 10px; color: #d4a5ff; margin-bottom: 6px; text-transform: uppercase; }
.input-group input { width: 100%; background: rgba(0,0,0,0.5); border: 1px solid #8a2be2; border-radius: 4px; color: #fff; padding: 8px; font-size: 12px; }

.controls { margin-top: 16px; }
.pull-btn {
  width: 100%; background: rgba(138, 43, 226, 0.2); border: 1px solid #8a2be2; color: #d4a5ff;
  padding: 10px; border-radius: 4px; font-weight: bold; cursor: pointer; transition: all 0.2s;
  text-transform: uppercase; letter-spacing: 1px;
}
.pull-btn:hover:not(:disabled) { background: #8a2be2; color: #fff; box-shadow: 0 0 15px #8a2be2; }
.pull-btn:disabled { opacity: 0.5; }

.pulled-nodes { margin-top: 16px; border-top: 1px dashed rgba(138, 43, 226, 0.3); padding-top: 12px; }
.pulled-title { font-size: 10px; color: #888; margin-bottom: 8px; text-transform: uppercase; }
.orbit-item {
  background: rgba(138, 43, 226, 0.1); border-left: 2px solid #8a2be2;
  padding: 8px; margin-bottom: 6px; font-size: 11px; border-radius: 0 4px 4px 0;
  animation: slideIn 0.3s ease-out;
}
@keyframes slideIn { from { transform: translateX(-10px); opacity: 0; } to { transform: translateX(0); opacity: 1; } }
</style>
