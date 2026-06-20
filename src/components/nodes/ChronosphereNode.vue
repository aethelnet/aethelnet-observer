<template>
  <div class="chronosphere-node" @mousedown.stop>
    <div class="time-rings" :class="{ spinning: isExtrapolating }">
      <div class="ring r1"></div>
      <div class="ring r2"></div>
      <div class="ring r3"></div>
    </div>
    
    <div class="header">
      <div class="icon"><i class="fas fa-hourglass-half"></i></div>
      <div class="title-wrap">
        <div class="title">CHRONOSPHERE</div>
        <div class="subtitle">Predictive Extrapolation</div>
      </div>
    </div>
    
    <div class="content">
      <div class="input-block">
        <label>Current Paradigm / Trend</label>
        <input type="text" v-model="trend" placeholder="e.g. AI-driven Social Media..." />
      </div>

      <div class="timeline-dial">
        <label>Extrapolate to:</label>
        <div class="dial-track">
          <input type="range" min="1" max="100" v-model.number="years" />
          <div class="dial-value">+{{ years }} YEARS</div>
        </div>
      </div>

      <button class="extrapolate-btn" @click="extrapolate" :disabled="isExtrapolating || !trend">
        <span v-if="isExtrapolating">Shifting Timelines...</span>
        <span v-else>ACTIVATE CHRONOSPHERE</span>
      </button>

      <div class="prediction-box" v-if="prediction">
        <div class="pred-header">YEAR {{ new Date().getFullYear() + years }} PROJECTION:</div>
        <div class="pred-text">{{ prediction }}</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const props = defineProps<{ node: any }>()
const trend = ref('')
const years = ref(10)
const isExtrapolating = ref(false)
const prediction = ref('')

async function extrapolate() {
  if (!trend.value) return
  isExtrapolating.value = true
  prediction.value = ''
  
  try {
    const url = (window as any).API_BASE ? `${(window as any).API_BASE}/lgnn/chronosphere/extrapolate` : '/api/lgnn/chronosphere/extrapolate'
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        trend: trend.value,
        years: years.value,
        api_provider: localStorage.getItem('auratic_llm_provider') || 'openrouter',
        api_key: localStorage.getItem('auratic_llm_api_key') || '',
        custom_model: localStorage.getItem('auratic_llm_model') || ''
      })
    })
    
    if (!res.ok) throw new Error("Chronosphere malfunction")
    const data = await res.json()
    
    if (data.status === 'success') {
      prediction.value = data.prediction
    } else {
      prediction.value = `[ERROR] Temporal static: ${data.message}`
    }
  } catch (err: any) {
    prediction.value = `[CRITICAL] Connection to chronosphere lost: ${err.message}`
  } finally {
    isExtrapolating.value = false
  }
}
</script>

<style scoped>
.chronosphere-node {
  background: rgba(10, 15, 25, 0.95);
  border: 1px solid rgba(255, 215, 0, 0.4);
  border-radius: 50% 50% 10px 10px;
  width: 320px;
  color: #fff;
  font-family: 'Inter', sans-serif;
  box-shadow: 0 0 40px rgba(255, 215, 0, 0.1);
  position: relative;
  overflow: hidden;
  padding-top: 40px;
}

.time-rings {
  position: absolute;
  top: -60px; left: 50%;
  transform: translateX(-50%);
  width: 140px; height: 140px;
  pointer-events: none;
  z-index: 0;
}

.ring {
  position: absolute;
  top: 50%; left: 50%;
  transform: translate(-50%, -50%) rotateX(60deg) rotateZ(0deg);
  border: 2px solid rgba(255, 215, 0, 0.3);
  border-radius: 50%;
  transition: all 0.5s;
}
.r1 { width: 100%; height: 100%; border-top-color: #ffd700; border-left-color: #ffd700; }
.r2 { width: 75%; height: 75%; border-right-color: #00d4ff; border-bottom-color: #00d4ff; }
.r3 { width: 50%; height: 50%; border-color: rgba(255, 255, 255, 0.5); }

.time-rings.spinning .r1 { animation: spin3D 2s linear infinite; border-width: 3px; border-color: #ffd700; }
.time-rings.spinning .r2 { animation: spin3DRev 1.5s linear infinite; border-width: 3px; border-color: #00d4ff; }
.time-rings.spinning .r3 { animation: spin3D 1s linear infinite; border-color: #fff; box-shadow: 0 0 20px #ffd700; }

@keyframes spin3D { 100% { transform: translate(-50%, -50%) rotateX(60deg) rotateZ(360deg); } }
@keyframes spin3DRev { 100% { transform: translate(-50%, -50%) rotateX(60deg) rotateZ(-360deg); } }

.header { position: relative; z-index: 1; display: flex; flex-direction: column; align-items: center; padding: 10px; }
.icon { font-size: 24px; color: #ffd700; text-shadow: 0 0 10px #ffd700; margin-bottom: 8px; }
.title { font-weight: 900; letter-spacing: 3px; font-size: 16px; background: linear-gradient(90deg, #ffd700, #00d4ff); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; }
.subtitle { font-size: 9px; color: #aaa; text-transform: uppercase; letter-spacing: 2px; }

.content { position: relative; z-index: 1; padding: 16px; background: rgba(0,0,0,0.4); border-top: 1px solid rgba(255, 215, 0, 0.2); }

.input-block label { display: block; font-size: 10px; color: #ffd700; margin-bottom: 6px; text-transform: uppercase; }
.input-block input { width: 100%; background: rgba(0,0,0,0.5); border: 1px solid rgba(255, 215, 0, 0.5); border-radius: 4px; color: #fff; padding: 8px; font-size: 12px; }

.timeline-dial { margin-top: 16px; }
.timeline-dial label { display: block; font-size: 10px; color: #00d4ff; margin-bottom: 6px; text-transform: uppercase; }
.dial-track { display: flex; align-items: center; gap: 10px; }
.dial-track input { flex: 1; accent-color: #ffd700; }
.dial-value { font-size: 14px; font-weight: 900; color: #fff; width: 80px; text-align: right; }

.extrapolate-btn {
  width: 100%; margin-top: 16px; background: transparent; border: 1px solid #ffd700; color: #ffd700;
  padding: 10px; border-radius: 4px; font-weight: bold; cursor: pointer; transition: all 0.2s; text-transform: uppercase; letter-spacing: 2px;
}
.extrapolate-btn:hover:not(:disabled) { background: rgba(255, 215, 0, 0.2); box-shadow: 0 0 20px rgba(255, 215, 0, 0.4); }
.extrapolate-btn:disabled { opacity: 0.5; border-color: #666; color: #888; }

.prediction-box { margin-top: 16px; background: rgba(0, 212, 255, 0.1); border-top: 2px solid #00d4ff; padding: 12px; animation: fadeIn 0.5s; }
.pred-header { font-size: 10px; color: #00d4ff; margin-bottom: 6px; font-weight: bold; letter-spacing: 1px; }
.pred-text { font-size: 12px; color: #eee; line-height: 1.5; font-style: italic; }

@keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
</style>
