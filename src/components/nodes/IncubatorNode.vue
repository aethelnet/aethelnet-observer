<template>
  <div class="incubator-node">
    <div class="greenhouse-glass"></div>
    
    <div class="header">
      <div class="icon"><i class="fas fa-leaf"></i></div>
      <div class="title-wrap">
        <div class="title">INCUBATOR</div>
        <div class="subtitle">Concept Greenhouse</div>
      </div>
      <div class="growth-stage">STAGE {{ stage }}</div>
    </div>
    
    <div class="content">
      <div class="seed-input" v-if="stage === 0">
        <label>Plant a Seed (Raw Idea)</label>
        <textarea v-model="seed" placeholder="Plant your roughest, most unpolished thought here..."></textarea>
        <button class="plant-btn" @click="plantSeed" :disabled="!seed">PLANT SEED</button>
      </div>

      <div class="growing-state" v-else>
        <div class="plant-visual">
          <div class="stem" :style="{ height: (stage * 20) + 'px' }"></div>
          <div class="leaves" v-if="stage > 1">
            <div class="leaf left" v-for="n in stage-1" :key="'l'+n" :style="{ bottom: (n*15)+'px' }"></div>
            <div class="leaf right" v-for="n in stage-1" :key="'r'+n" :style="{ bottom: (n*15 + 8)+'px' }"></div>
          </div>
          <div class="flower" v-if="stage === 4">✺</div>
        </div>
        
        <div class="status-box">
          <div class="status-title">Current Synthesis:</div>
          <div class="status-text">{{ currentConcept }}</div>
        </div>

        <button class="harvest-btn" v-if="stage === 4" @click="harvest">HARVEST CONCEPT</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const props = defineProps<{ node: any }>()
const seed = ref('')
const stage = ref(0)
const currentConcept = ref('')

let growthInterval: any;

function plantSeed() {
  if (!seed.value) return
  stage.value = 1
  currentConcept.value = `Seed planted: "${seed.value}". Gathering baseline nutrients...`
  
  growthInterval = setInterval(() => {
    stage.value++
    if (stage.value === 2) currentConcept.value = `Sprouting: Cross-referencing "${seed.value}" with psychological models...`
    else if (stage.value === 3) currentConcept.value = `Maturing: Integrating sociological studies and structural frameworks...`
    else if (stage.value === 4) {
      currentConcept.value = `Fully Bloomed: A comprehensive socio-psychological framework explaining the dynamics of "${seed.value}".`
      clearInterval(growthInterval)
    }
  }, 2000) // Fast growth for demo
}

function harvest() {
  alert('Concept harvested to your clipboard / knowledge base!')
  stage.value = 0
  seed.value = ''
  currentConcept.value = ''
}
</script>

<style scoped>
.incubator-node {
  background: rgba(5, 20, 10, 0.95);
  border: 1px solid rgba(0, 255, 128, 0.4);
  border-radius: 16px 16px 4px 4px;
  width: 290px;
  color: #fff;
  font-family: 'Inter', sans-serif;
  box-shadow: 0 10px 30px rgba(0, 255, 128, 0.1), inset 0 0 40px rgba(0, 255, 128, 0.05);
  position: relative;
  overflow: hidden;
}

.greenhouse-glass {
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  background: linear-gradient(135deg, rgba(255,255,255,0.1) 0%, transparent 40%, rgba(255,255,255,0.05) 100%);
  pointer-events: none;
  z-index: 0;
}

.header {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid rgba(0, 255, 128, 0.2);
  background: rgba(0, 255, 128, 0.1);
}

.icon { font-size: 20px; color: #00ff80; margin-right: 12px; }
.title-wrap { flex: 1; }
.title { font-weight: 900; letter-spacing: 2px; font-size: 14px; color: #b3ffcc; }
.subtitle { font-size: 9px; color: #66cc99; text-transform: uppercase; }
.growth-stage { font-size: 10px; font-weight: bold; background: rgba(0,255,128,0.2); color: #00ff80; padding: 4px 8px; border-radius: 10px; }

.content { position: relative; z-index: 1; padding: 16px; min-height: 150px; }

.seed-input label { display: block; font-size: 10px; color: #00ff80; margin-bottom: 6px; text-transform: uppercase; }
.seed-input textarea { width: 100%; height: 60px; background: rgba(0,0,0,0.5); border: 1px solid #00ff80; border-radius: 4px; color: #fff; padding: 8px; font-size: 12px; resize: none; margin-bottom: 12px; }

.plant-btn, .harvest-btn {
  width: 100%; background: transparent; border: 1px solid #00ff80; color: #00ff80;
  padding: 10px; border-radius: 4px; font-weight: bold; cursor: pointer; transition: all 0.2s; text-transform: uppercase; letter-spacing: 1px;
}
.plant-btn:hover:not(:disabled), .harvest-btn:hover { background: rgba(0, 255, 128, 0.2); box-shadow: 0 0 15px rgba(0, 255, 128, 0.4); }
.plant-btn:disabled { opacity: 0.5; }

.growing-state { display: flex; flex-direction: column; align-items: center; }

.plant-visual { height: 100px; width: 60px; position: relative; border-bottom: 2px solid #5c4033; margin-bottom: 16px; display: flex; justify-content: center; align-items: flex-end; }
.stem { width: 4px; background: #00ff80; border-radius: 4px 4px 0 0; transition: height 1s ease-in-out; position: relative; }
.leaf { position: absolute; width: 12px; height: 6px; background: #00cc66; border-radius: 50% 0 50% 0; animation: growLeaf 0.5s forwards; }
.leaf.left { left: -10px; transform-origin: right bottom; transform: rotate(-30deg); }
.leaf.right { right: -10px; transform-origin: left bottom; border-radius: 0 50% 0 50%; transform: rotate(30deg); }
.flower { position: absolute; top: -15px; left: -10px; font-size: 24px; color: #ff00ff; text-shadow: 0 0 10px #ff00ff; animation: bloom 1s forwards; }

@keyframes growLeaf { from { transform: scale(0); } to { transform: scale(1) rotate(var(--rot, 0deg)); } }
@keyframes bloom { from { transform: scale(0) rotate(-180deg); opacity: 0; } to { transform: scale(1) rotate(0deg); opacity: 1; } }

.status-box { width: 100%; background: rgba(0,0,0,0.6); padding: 10px; border-radius: 6px; border-left: 3px solid #00ff80; margin-bottom: 12px; }
.status-title { font-size: 9px; color: #66cc99; margin-bottom: 4px; text-transform: uppercase; }
.status-text { font-size: 11px; line-height: 1.4; color: #e6ffe6; }
</style>
