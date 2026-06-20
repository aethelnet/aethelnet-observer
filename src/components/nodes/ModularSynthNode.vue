<template>
  <div class="synth-node">
    <div class="synth-header">
      [ MODULAR SYNTH ]
    </div>
    
    <div class="synth-body">
      <!-- VCO Section -->
      <div class="module">
        <label>VCO (Oscillator)</label>
        <div class="controls">
          <select v-model="oscType" @change="updateSynth">
            <option value="sine">Sine</option>
            <option value="square">Square</option>
            <option value="sawtooth">Saw</option>
          </select>
          <input type="range" min="50" max="1000" v-model="frequency" @input="updateSynth" />
          <span>{{ frequency }} Hz</span>
        </div>
      </div>

      <!-- VCF Section -->
      <div class="module">
        <label>VCF (Filter)</label>
        <div class="controls">
          <input type="range" min="100" max="5000" v-model="filterFreq" @input="updateSynth" />
          <span>{{ filterFreq }} Hz</span>
        </div>
      </div>

      <!-- Actions -->
      <div class="actions">
        <button @click="togglePlay" :class="{ playing: isPlaying }">
          {{ isPlaying ? '[ STOP ]' : '[ PLAY ]' }}
        </button>
      </div>
    </div>

    <!-- Script Injection (Lua Concept) -->
    <div class="lua-script" v-if="node.meta_data?.lua_script">
      <div class="lua-label">LUA SCRIPT ATTACHED</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'

const props = defineProps<{
  node: any;
}>()

const emit = defineEmits(['update-node'])

// [CORE] Web Audio API context for the modular synthesis chain.
let audioCtx: AudioContext | null = null
let oscillator: OscillatorNode | null = null
let filter: BiquadFilterNode | null = null
let gainNode: GainNode | null = null

// UI State
const isPlaying = ref(false)
const oscType = ref<OscillatorType>('sawtooth')
const frequency = ref(440)
const filterFreq = ref(2000)

// [ARCH] We initialize the audio context lazily on user interaction
// to comply with browser autoplay policies.
function initAudio() {
  if (!audioCtx) {
    audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)()
    
    // [ARCH] Routing: VCO -> VCF -> VCA -> Master
    filter = audioCtx.createBiquadFilter()
    filter.type = 'lowpass'
    
    gainNode = audioCtx.createGain()
    gainNode.gain.value = 0.1 // Master volume

    filter.connect(gainNode)
    gainNode.connect(audioCtx.destination)
  }
}

function togglePlay() {
  if (!isPlaying.value) {
    initAudio()
    if (audioCtx?.state === 'suspended') audioCtx.resume()

    // [CORE] Create oscillator node. Must be recreated every play.
    oscillator = audioCtx!.createOscillator()
    oscillator.type = oscType.value
    oscillator.frequency.value = frequency.value
    
    filter!.frequency.value = filterFreq.value

    oscillator.connect(filter!)
    oscillator.start()
    isPlaying.value = true
  } else {
    // [TIP] Use a slight ramp-down here in a real app to avoid clicking (ADSR envelope).
    if (oscillator) {
      oscillator.stop()
      oscillator.disconnect()
      oscillator = null
    }
    isPlaying.value = false
  }
}

function updateSynth() {
  if (isPlaying.value && oscillator && filter) {
    oscillator.type = oscType.value
    // [TIP] Using linearRampToValueAtTime prevents audio artifacts/zipper noise
    oscillator.frequency.linearRampToValueAtTime(frequency.value, audioCtx!.currentTime + 0.05)
    filter.frequency.linearRampToValueAtTime(filterFreq.value, audioCtx!.currentTime + 0.05)
  }
}

// [ARCH] Cleanup resources when node is deleted or unmounted
onBeforeUnmount(() => {
  if (oscillator) {
    oscillator.stop()
    oscillator.disconnect()
  }
  if (audioCtx) {
    audioCtx.close()
  }
})
</script>

<style scoped>
.synth-node {
  background: var(--color-bg-panel, #111);
  border: 2px solid #FF9800;
  border-radius: 8px;
  width: 250px;
  color: var(--color-text-main, #EEE);
  font-family: var(--font-family-mono, monospace);
  box-shadow: 4px 4px 0 rgba(255, 152, 0, 0.3);
  overflow: hidden;
}

.synth-header {
  background: #FF9800;
  color: #000;
  padding: 8px;
  font-weight: 900;
  text-align: center;
  border-bottom: 2px solid #000;
}

.synth-body {
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.module {
  background: rgba(0,0,0,0.4);
  padding: 8px;
  border: 1px solid #333;
}

.module label {
  display: block;
  font-size: 10px;
  color: #FF9800;
  margin-bottom: 8px;
  font-weight: bold;
}

.controls {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 11px;
}

input[type=range] {
  accent-color: #FF9800;
}

select {
  background: #000;
  color: #FF9800;
  border: 1px solid #333;
  padding: 2px;
  font-family: inherit;
}

.actions {
  display: flex;
  justify-content: center;
  margin-top: 8px;
}

button {
  background: transparent;
  color: #FF9800;
  border: 1px solid #FF9800;
  padding: 6px 12px;
  font-weight: bold;
  cursor: pointer;
  transition: all 0.2s;
}

button.playing {
  background: #E03C31;
  color: #FFF;
  border-color: #E03C31;
}

button:hover:not(.playing) {
  background: #FF9800;
  color: #000;
}

.lua-script {
  background: #1A1A1A;
  padding: 4px;
  text-align: center;
  font-size: 9px;
  color: #00BCD4;
  border-top: 1px dashed #333;
}
</style>
