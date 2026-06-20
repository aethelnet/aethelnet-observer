<template>
  <div class="aura-stream-node">
    <!-- HUD Header -->
    <div class="hud">
      <div class="aethel-metric">
        <span class="label">Aura Resonance</span>
        <span class="value">{{ computedResonance.toFixed(2) }} Ӕ</span>
      </div>
      <button 
        class="zen-btn audio-btn" 
        :class="{ 'active': audioActive }"
        @click.stop="toggleAudioLoop"
      >
        <span class="audio-icon">{{ audioActive ? '🔊' : '🔈' }}</span>
        <span>Aural FX</span>
      </button>
    </div>

    <!-- Zen Stream Container -->
    <div class="zen-container" @wheel.stop>
      <div class="stream-messages" ref="messagesContainer">
        <div 
          v-for="(msg, idx) in messages" 
          :key="idx" 
          class="message" 
          :class="{ 'system': msg.role === 'system', 'user': msg.role === 'user' }"
        >
          <div class="msg-content">{{ msg.content }}</div>
          <div v-if="msg.resonance" class="msg-resonance">+{{ msg.resonance.toFixed(2) }} Ӕ</div>
        </div>
      </div>

      <!-- Input Area -->
      <div class="input-area">
        <input 
          v-model="inputText" 
          @keydown.enter="submitThought"
          @mousedown.stop
          type="text" 
          placeholder="Broadcast a thought..." 
          class="zen-input"
          :disabled="isProcessing"
        />
        <button @click.stop="submitThought" class="zen-submit-btn" :disabled="!inputText.trim() || isProcessing">
          SEND
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, nextTick, computed, watch } from 'vue'
import { setupWebSocketListener } from '../../shared/websocket.js'
import { API_BASE } from '../../shared/api.js'

const props = defineProps<{
  node: any
  globalNodes?: any[]
  globalLinks?: any[]
}>()

const inputText = ref('')
const isProcessing = ref(false)
const messagesContainer = ref<HTMLElement | null>(null)
const audioActive = ref(false)

// Computed Resonance from Parent Context
const computedResonance = computed(() => {
  if (!props.globalNodes || props.globalNodes.length === 0) return 0.42
  let sum = 0
  const sampleSize = Math.min(10, props.globalNodes.length)
  for (let i = 0; i < sampleSize; i++) {
     sum += Math.abs(props.globalNodes[i].activation || 0)
  }
  return sum / sampleSize
})

watch(computedResonance, (newVal) => {
  if (audioActive.value) {
    updateAudioModulation(newVal)
  }
})

// WebAudio State
let audioCtx: AudioContext | null = null;
let masterGain: GainNode | null = null;
let droneOsc: OscillatorNode | null = null;
let pulseOsc: OscillatorNode | null = null;
let filter: BiquadFilterNode | null = null;

// Mic Loop State
let micStream: MediaStream | null = null;
let analyser: AnalyserNode | null = null;
let dataArray: Uint8Array | null = null;
let micAnimationFrame: number = 0;

function toggleAudioLoop() {
  if (audioActive.value) {
    stopAudio();
  } else {
    startAudio();
  }
}

function startAudio() {
  try {
    audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)();
    
    // Master Gain
    masterGain = audioCtx.createGain();
    masterGain.gain.value = 0.2; // Keep it ambient
    masterGain.connect(audioCtx.destination);
    
    // Lowpass Filter for that deep cybernetic underwater sound
    filter = audioCtx.createBiquadFilter();
    filter.type = 'lowpass';
    filter.frequency.value = 400;
    filter.connect(masterGain);
    
    // Drone Oscillator (Deep Bass)
    droneOsc = audioCtx.createOscillator();
    droneOsc.type = 'sine';
    droneOsc.frequency.value = 55; // Deep A1
    droneOsc.connect(filter);
    
    // Pulse Oscillator (Higher pitched, modulated)
    pulseOsc = audioCtx.createOscillator();
    pulseOsc.type = 'triangle';
    pulseOsc.frequency.value = 220; // A3
    
    // Modulate pulse volume with an LFO
    const lfo = audioCtx.createOscillator();
    lfo.type = 'sine';
    lfo.frequency.value = 0.5; // slow pulse
    
    const pulseGain = audioCtx.createGain();
    pulseGain.gain.value = 0;
    
    lfo.connect(pulseGain.gain);
    pulseOsc.connect(pulseGain);
    pulseGain.connect(filter);
    
    droneOsc.start();
    pulseOsc.start();
    lfo.start();
    
    audioActive.value = true;
    updateAudioModulation(latestResonance.value);

    // --- RAW MICROPHONE LOOP ---
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
      navigator.mediaDevices.getUserMedia({ audio: true, video: false })
        .then(stream => {
          micStream = stream;
          const source = audioCtx!.createMediaStreamSource(stream);
          
          // 1. Cybernetic Echo for the breathing
          const delay = audioCtx!.createDelay(5.0);
          delay.delayTime.value = 0.5; // 500ms echo
          const feedback = audioCtx!.createGain();
          feedback.gain.value = 0.6; // High feedback for deep space echo
          
          source.connect(delay);
          delay.connect(feedback);
          feedback.connect(delay);
          delay.connect(masterGain!);

          // 2. Analyser to "listen" to the breathing volume
          analyser = audioCtx!.createAnalyser();
          analyser.fftSize = 256;
          source.connect(analyser);
          dataArray = new Uint8Array(analyser.frequencyBinCount);
          
          loopMicAnalysis();
        })
        .catch(err => console.error("Mic access denied or unavailable", err));
    } else {
      console.warn("Microphone access is not available (requires HTTPS or localhost).");
    }
  } catch (e) {
    console.error("WebAudio not supported", e);
  }
}

function loopMicAnalysis() {
  if (!audioActive.value || !analyser || !dataArray) return;
  
  analyser.getByteTimeDomainData(dataArray);
  
  // Calculate RMS volume of breath
  let sumSq = 0;
  for (let i = 0; i < dataArray.length; i++) {
    const val = (dataArray[i] - 128) / 128;
    sumSq += val * val;
  }
  const rms = Math.sqrt(sumSq / dataArray.length);
  
  // If user breathes loud (rms > 0.05), trigger a brief UI reaction
  if (rms > 0.05) {
    // Inject the breath back into the LGNN resonance value locally just for audio
    const temporaryResonance = Math.min(1.5, computedResonance.value + (rms * 0.1));
    updateAudioModulation(temporaryResonance);
  }
  
  micAnimationFrame = requestAnimationFrame(loopMicAnalysis);
}

function stopAudio() {
  if (audioCtx) {
    audioCtx.close();
    audioCtx = null;
  }
  if (micStream) {
    micStream.getTracks().forEach(t => t.stop());
    micStream = null;
  }
  if (micAnimationFrame) {
    cancelAnimationFrame(micAnimationFrame);
  }
  audioActive.value = false;
}

function updateAudioModulation(resonance: number) {
  if (!audioActive.value || !filter || !droneOsc || !pulseOsc) return;
  
  // The magic: LGNN Resonance directly dictates the pitch and filter cutoff!
  const targetFilterFreq = 200 + (resonance * 1000); // 200Hz to 1200Hz
  const targetDroneFreq = 40 + (resonance * 30);     // Pitch shifts up as resonance increases
  
  filter.frequency.setTargetAtTime(targetFilterFreq, audioCtx!.currentTime, 0.5);
  droneOsc.frequency.setTargetAtTime(targetDroneFreq, audioCtx!.currentTime, 1.0);
  pulseOsc.frequency.setTargetAtTime(targetDroneFreq * 4, audioCtx!.currentTime, 1.0);
}

interface Message {
  role: 'system' | 'user';
  content: string;
  resonance?: number;
}

const messages = ref<Message[]>([
  { role: 'system', content: 'LGNN Neural Manifold initialized. Awaiting uncaused inclination...' }
])

function handleResize() {
  bgWidth.value = window.innerWidth
  bgHeight.value = window.innerHeight
}

onMounted(() => {
  window.addEventListener('resize', handleResize)
  // Periodically fetch the latest resonance from the graph
  fetchGraphResonance()
  
  // Listen for Live Execution hits from the Matrix
  executionListenerUnsub = setupWebSocketListener('EXECUTION_UPDATE', (data) => {
    triggerTradeSound(data.trade || data)
  })
})

let executionListenerUnsub: (() => void) | null = null

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  if (executionListenerUnsub) executionListenerUnsub()
})

function triggerTradeSound(tradeData: any) {
  if (!audioActive.value || !audioCtx || !masterGain) return;
  
  const osc = audioCtx.createOscillator();
  const env = audioCtx.createGain();
  
  // LONG = High crystalline ping, SHORT = Low heavy thud
  const isLong = tradeData?.side?.toUpperCase() === 'LONG';
  osc.type = isLong ? 'sine' : 'square';
  
  const startFreq = isLong ? 1200 : 150;
  const endFreq = isLong ? 440 : 40;
  
  osc.frequency.setValueAtTime(startFreq, audioCtx.currentTime);
  osc.frequency.exponentialRampToValueAtTime(endFreq, audioCtx.currentTime + 0.1);
  
  env.gain.setValueAtTime(0, audioCtx.currentTime);
  env.gain.linearRampToValueAtTime(0.8, audioCtx.currentTime + 0.01);
  env.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.4);
  
  osc.connect(env);
  env.connect(masterGain); 
  
  osc.start();
  osc.stop(audioCtx.currentTime + 0.45);
  
  // Visual explosion on the graph
  latestResonance.value = Math.min(1.5, latestResonance.value + 0.4);
  updateAudioModulation(latestResonance.value);
}

// Replaced fetchGraphResonance with computed property

async function submitThought() {
  if (!inputText.value.trim() || isProcessing.value) return
  
  const thought = inputText.value
  inputText.value = ''
  isProcessing.value = true
  
  messages.value.push({ role: 'user', content: thought })
  scrollToBottom()
  
  try {
    const senderName = activePersona.value || 'ANONYMOUS'
    // 1. Evolve the LGNN with the text via the real API
    const res = await fetch(`${API_BASE || ''}/lgnn/evolve-text`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: `[FROM: ${senderName}] ${thought}` })
    })

    if (!res.ok) throw new Error("API failed")
    const result = await res.json()
    
    // Echo back the systemic response
    messages.value.push({ 
      role: 'system', 
      content: result.evolved_text || `Broadcasted across manifold. Synaptic bridges aligned.`,
      resonance: computedResonance.value
    })
    
  } catch (error) {
    console.error(error)
    messages.value.push({ role: 'system', content: 'Connection to LGNN manifold disrupted.' })
  } finally {
    isProcessing.value = false
    scrollToBottom()
  }
}

function scrollToBottom() {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}
</script>

<style scoped>
.aura-stream-node {
  width: 380px;
  height: 520px;
  display: flex;
  flex-direction: column;
  background: var(--color-bg-panel);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  overflow: hidden;
  backdrop-filter: blur(8px);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
  font-family: var(--font-family-mono);
}

/* HUD */
.hud {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-color);
  background: rgba(0, 243, 255, 0.05);
}

.aethel-metric {
  display: flex;
  flex-direction: column;
}

.label {
  font-size: 10px;
  text-transform: uppercase;
  color: var(--color-text-muted);
}

.value {
  font-size: 1.1rem;
  font-weight: bold;
  color: var(--color-accent);
}

.audio-btn {
  background: transparent;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  padding: 6px 12px;
  color: var(--color-text-main);
  font-size: 11px;
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.audio-btn:hover {
  border-color: var(--color-accent);
}

.audio-btn.active {
  background: rgba(0, 243, 255, 0.1);
  border-color: var(--color-accent);
  color: var(--color-accent);
}

/* Zen Container */
.zen-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.stream-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.message {
  max-width: 85%;
  line-height: 1.4;
}

.message.system {
  align-self: flex-start;
  color: var(--color-text-muted);
  font-size: 11px;
  font-style: italic;
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 8px 8px 8px 0;
}

.message.user {
  align-self: flex-end;
  background: rgba(0, 243, 255, 0.1);
  border: 1px solid rgba(0, 243, 255, 0.2);
  padding: 10px 14px;
  color: var(--color-text-main);
  font-size: 12px;
  border-radius: 8px 8px 0 8px;
}

.msg-resonance {
  font-size: 10px;
  color: var(--color-accent);
  margin-top: 6px;
  text-align: right;
  opacity: 0.8;
}

/* Input Area */
.input-area {
  padding: 12px;
  border-top: 1px solid var(--border-color);
  display: flex;
  gap: 8px;
  background: rgba(0, 0, 0, 0.2);
}

.zen-input {
  flex: 1;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  padding: 8px 12px;
  color: var(--color-text-main);
  font-size: 12px;
  font-family: var(--font-family-mono);
  outline: none;
  transition: all 0.2s;
}

.zen-input:focus {
  border-color: var(--color-accent);
  background: rgba(0, 243, 255, 0.05);
}

.zen-submit-btn {
  background: transparent;
  border: 1px solid var(--border-color);
  color: var(--color-accent);
  padding: 0 16px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: bold;
  cursor: pointer;
  transition: all 0.2s;
}

.zen-submit-btn:hover:not(:disabled) {
  background: rgba(0, 243, 255, 0.1);
  border-color: var(--color-accent);
}

.zen-submit-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
</style>
