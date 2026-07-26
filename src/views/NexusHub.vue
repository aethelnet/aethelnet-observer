<template>
  <div class="nexus-container">
    <div class="nexus-wrapper">
      <header class="nexus-header">
        <h1 class="glitch" data-text="THE NEXUS">THE NEXUS</h1>
        <p class="subtitle">SECURE PUBLIC DROP-POINT // NO LOGS // ZERO TRACE</p>
      </header>

      <div class="drop-zone">
        <label class="brutal-label">[ INJECT PAYLOAD ]</label>
        <textarea 
          v-model="payload" 
          class="brutal-textarea" 
          placeholder="PASTE INTEL, LEAKED DOCS, OR EXPLOIT TRACES HERE..."
          :disabled="isInjecting"
        ></textarea>
        
        <div class="actions">
          <button class="brutal-btn" @click="injectData" :disabled="isInjecting || !payload.trim()">
            {{ isInjecting ? 'ENCRYPTING...' : '▲ TRANSMIT TO AETHELNET' }}
          </button>
        </div>
        
        <div v-if="statusMessage" class="status-msg" :class="statusType">
          {{ statusMessage }}
        </div>
      </div>
      
      <div class="info-block">
        <h3>SYSTEM PROTOCOL</h3>
        <p>Data dropped here is immediately encrypted and thrown into the LGNN Dark Pool. Unit 734 Spiders will validate and extract actionable intelligence automatically.</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { API_BASE } from '../shared/api.js'

const payload = ref('')
const isInjecting = ref(false)
const statusMessage = ref('')
const statusType = ref('')

const injectData = async () => {
  if (!payload.value.trim()) return
  
  isInjecting.value = true
  statusMessage.value = ''
  
  try {
    const url = API_BASE ? `${API_BASE}/lgnn/universal_ingest` : '/api/lgnn/universal_ingest'
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        bot_name: 'Nexus_WebUI',
        observation: payload.value,
        confidence: 1.0,
        context_tags: ['nexus_drop', 'manual_intel'],
        node_prefix: 'NEXUS_'
      })
    })
    
    if (!res.ok) throw new Error('Transmission rejected by proxy.')
    
    statusMessage.value = '[ TRANSMISSION SUCCESS. SPIDERS DISPATCHED. ]'
    statusType.value = 'success'
    payload.value = '' // clear
    
  } catch (err) {
    statusMessage.value = `[ ERR: ${err.message} ]`
    statusType.value = 'error'
  } finally {
    isInjecting.value = false
    
    setTimeout(() => {
      statusMessage.value = ''
    }, 5000)
  }
}
</script>

<style scoped>
.nexus-container {
  height: 100%;
  width: 100%;
  background: #FFFFFF;
  color: #111111;
  display: flex;
  justify-content: center;
  align-items: center;
  font-family: 'JetBrains Mono', monospace;
  overflow: auto;
}

.nexus-wrapper {
  width: 100%;
  max-width: 800px;
  padding: 40px;
}

.nexus-header {
  margin-bottom: 60px;
  border-bottom: 4px solid #111111;
  padding-bottom: 20px;
}

.nexus-header h1 {
  font-size: 64px;
  font-weight: 900;
  letter-spacing: -2px;
  margin: 0;
  line-height: 1;
}

.subtitle {
  font-size: 14px;
  font-weight: bold;
  letter-spacing: 2px;
  color: #666666;
  margin-top: 10px;
}

.drop-zone {
  display: flex;
  flex-direction: column;
  gap: 20px;
  margin-bottom: 60px;
}

.brutal-label {
  font-weight: bold;
  font-size: 18px;
}

.brutal-textarea {
  width: 100%;
  height: 250px;
  background: #F8F8F8;
  border: 4px solid #111111;
  padding: 20px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 16px;
  resize: vertical;
  color: #111111;
}

.brutal-textarea:focus {
  outline: none;
  background: #FFFFFF;
  box-shadow: 8px 8px 0px #111111;
}

.actions {
  display: flex;
  justify-content: flex-end;
}

.brutal-btn {
  background: #111111;
  color: #FFFFFF;
  border: 4px solid #111111;
  padding: 15px 30px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 18px;
  font-weight: 900;
  cursor: pointer;
  box-shadow: 6px 6px 0px rgba(17,17,17,0.2);
  transition: all 0.1s;
}

.brutal-btn:hover:not(:disabled) {
  background: #FFFFFF;
  color: #111111;
  box-shadow: 6px 6px 0px #111111;
  transform: translate(-2px, -2px);
}

.brutal-btn:disabled {
  background: #EAEAEA;
  color: #666666;
  border-color: #AAAAAA;
  cursor: not-allowed;
  box-shadow: none;
}

.status-msg {
  padding: 20px;
  border: 4px solid #111111;
  font-weight: bold;
  font-size: 16px;
  text-align: center;
}

.status-msg.success {
  background: #32D74B;
  color: #111111;
  border-color: #111111;
  box-shadow: 4px 4px 0px #111111;
}

.status-msg.error {
  background: #FF3366;
  color: #111111;
  border-color: #111111;
  box-shadow: 4px 4px 0px #111111;
}

.info-block {
  border-left: 4px solid #111111;
  padding-left: 20px;
  color: #333333;
}

.info-block h3 {
  margin: 0 0 10px 0;
  font-weight: 900;
}

.info-block p {
  margin: 0;
  line-height: 1.5;
}

/* Glitch animation */
.glitch {
  position: relative;
  color: #111111;
}
.glitch::before, .glitch::after {
  content: attr(data-text);
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: #FFFFFF;
}
.glitch::before {
  left: 2px;
  text-shadow: -2px 0 #FF3366;
  clip: rect(24px, 550px, 90px, 0);
  animation: glitch-anim 3s infinite linear alternate-reverse;
}
.glitch::after {
  left: -2px;
  text-shadow: -2px 0 #32D74B;
  clip: rect(85px, 550px, 140px, 0);
  animation: glitch-anim 2.5s infinite linear alternate-reverse;
}
@keyframes glitch-anim {
  0% { clip: rect(10px, 9999px, 85px, 0); }
  20% { clip: rect(32px, 9999px, 11px, 0); }
  40% { clip: rect(78px, 9999px, 56px, 0); }
  60% { clip: rect(21px, 9999px, 98px, 0); }
  80% { clip: rect(90px, 9999px, 12px, 0); }
  100% { clip: rect(44px, 9999px, 33px, 0); }
}
</style>
