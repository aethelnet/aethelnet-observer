<template>
  <div class="entropy-chamber-node">
    <div class="chaos-particles" v-if="isDecaying">
      <div class="p" v-for="n in 20" :key="n" :style="getParticleStyle()"></div>
    </div>
    
    <div class="header">
      <div class="icon"><i class="fas fa-radiation"></i></div>
      <div class="title-wrap">
        <div class="title">ENTROPY CHAMBER</div>
        <div class="subtitle">Concept Decay Engine</div>
      </div>
    </div>
    
    <div class="content">
      <div class="input-block">
        <label>Solid Concept (Target)</label>
        <textarea v-model="concept" placeholder="Paste a rigid or boring idea here to break it down..."></textarea>
      </div>

      <button class="decay-btn" @click="triggerDecay" :disabled="isDecaying || !concept">
        <span v-if="isDecaying">Shattering Coherence...</span>
        <span v-else>Induce Entropy</span>
      </button>

      <div class="fragments" v-if="fragments.length > 0">
        <div class="fragments-label">Decayed Fragments:</div>
        <div class="fragment" v-for="(f, i) in fragments" :key="i">
          <span class="frag-icon">✺</span> {{ f }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const props = defineProps<{ node: any }>()
const concept = ref('')
const isDecaying = ref(false)
const fragments = ref<string[]>([])

function getParticleStyle() {
  const x = Math.random() * 100;
  const y = Math.random() * 100;
  const delay = Math.random() * 0.5;
  const dur = 0.5 + Math.random() * 1;
  return `left: ${x}%; top: ${y}%; animation-delay: ${delay}s; animation-duration: ${dur}s;`;
}

async function triggerDecay() {
  if (!concept.value) return
  isDecaying.value = true
  fragments.value = []
  
  // Real logic would go here
  
  fragments.value = [
    "What if the exact opposite is true?",
    "How does this look on a microscopic scale?",
    "Remove the core assumption: what's left?",
    "Inject pure randomness into the process."
  ]
  isDecaying.value = false
}
</script>

<style scoped>
.entropy-chamber-node {
  background: rgba(15, 0, 5, 0.95);
  border: 1px solid rgba(255, 0, 80, 0.5);
  border-radius: 4px 4px 20px 20px;
  width: 310px;
  color: #fff;
  font-family: 'Inter', sans-serif;
  box-shadow: 0 0 25px rgba(255, 0, 80, 0.15);
  position: relative;
  overflow: hidden;
}

.chaos-particles {
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  pointer-events: none;
  z-index: 0;
  background: radial-gradient(circle at center, rgba(255, 0, 80, 0.2) 0%, transparent 70%);
}

.p {
  position: absolute;
  width: 4px; height: 4px;
  background: #ff0050;
  border-radius: 50%;
  opacity: 0;
  animation: spark linear infinite;
}

@keyframes spark {
  0% { transform: scale(1) translate(0, 0); opacity: 1; }
  100% { transform: scale(0) translate(calc(-50px + 100px * var(--rx)), calc(-50px + 100px * var(--ry))); opacity: 0; }
}

.header {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  padding: 12px 16px;
  background: linear-gradient(90deg, rgba(255,0,80,0.3) 0%, transparent 100%);
  border-bottom: 1px solid rgba(255, 0, 80, 0.3);
}

.icon { font-size: 20px; color: #ff0050; margin-right: 12px; animation: jitter 2s infinite; }
@keyframes jitter { 0%, 100% { transform: translate(0,0); } 50% { transform: translate(1px, -1px); } }

.title { font-weight: 900; letter-spacing: 2px; font-size: 14px; color: #ff6b96; }
.subtitle { font-size: 10px; color: #aaa; text-transform: uppercase; }

.content { position: relative; z-index: 1; padding: 16px; }

.input-block label { display: block; font-size: 10px; color: #ff6b96; margin-bottom: 6px; text-transform: uppercase; }
.input-block textarea { width: 100%; height: 60px; background: rgba(0,0,0,0.6); border: 1px solid #ff0050; border-radius: 4px; color: #fff; padding: 8px; font-size: 12px; resize: none; }

.decay-btn {
  width: 100%; margin-top: 12px; background: rgba(255, 0, 80, 0.2); border: 1px solid #ff0050; color: #fff;
  padding: 10px; border-radius: 4px; font-weight: bold; cursor: pointer; transition: all 0.2s; text-transform: uppercase; letter-spacing: 2px;
}
.decay-btn:hover:not(:disabled) { background: #ff0050; box-shadow: 0 0 20px rgba(255, 0, 80, 0.6); }
.decay-btn:disabled { opacity: 0.5; cursor: wait; }

.fragments { margin-top: 16px; }
.fragments-label { font-size: 10px; color: #ff6b96; margin-bottom: 8px; text-transform: uppercase; border-bottom: 1px dashed rgba(255, 0, 80, 0.3); padding-bottom: 4px;}
.fragment { background: rgba(255, 255, 255, 0.05); padding: 8px; font-size: 11px; border-radius: 4px; margin-bottom: 6px; display: flex; align-items: flex-start; }
.frag-icon { color: #ff0050; margin-right: 8px; font-size: 10px; margin-top: 2px;}
</style>
