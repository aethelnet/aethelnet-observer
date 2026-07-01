<template>
  <div class="audio-node">
    <div class="header">
      <span class="icon" :class="{ recording: isRecording }"></span> [ AUDIO CORTEX ]
    </div>
    
    <div class="visualizer-container">
      <canvas ref="canvasRef" width="280" height="80" class="visualizer"></canvas>
    </div>

    <div class="classification-strip">
      <div class="status-label">SIGNAL:</div>
      <div class="status-value" :style="{ color: signalColor }">[{{ classification }}]</div>
    </div>
    
    <div class="controls">
      <button v-if="!isRecording" @click="startRecording" class="rec-btn start">
        INITIATE SCAN
      </button>
      <button v-else @click="stopRecording" class="rec-btn stop">
        TERMINATE
      </button>
    </div>

    <div v-if="transcript" class="transcript-box">
      > {{ transcript }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'

const props = defineProps<{
  node: any
}>()

const emit = defineEmits(['update-node', 'refresh'])

const canvasRef = ref<HTMLCanvasElement | null>(null)
const isRecording = ref(false)
const classification = ref('IDLE')
const transcript = ref('')

let audioContext: AudioContext | null = null
let analyser: AnalyserNode | null = null
let stream: MediaStream | null = null
let animationId: number = 0
let recognition: any = null

let voiceEnergyScore = 0
let noiseEnergyScore = 0

const signalColor = computed(() => {
  if (classification.value === 'SPEECH') return '#00FF41'
  if (classification.value === 'AMBIENT/NOISE') return '#FF9800'
  return '#666'
})

onMounted(() => {
  // Setup Speech Recognition
  const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
  if (SpeechRecognition) {
    recognition = new SpeechRecognition()
    recognition.continuous = true
    recognition.interimResults = true
    
    recognition.onresult = (event: any) => {
      let finalTranscript = ''
      for (let i = event.resultIndex; i < event.results.length; ++i) {
        if (event.results[i].isFinal) {
          finalTranscript += event.results[i][0].transcript
        }
      }
      if (finalTranscript) {
        transcript.value += finalTranscript + ' '
        classification.value = 'SPEECH'
      }
    }
  }
})

onUnmounted(() => {
  if (isRecording.value) stopRecording()
})

async function startRecording() {
  try {
    stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    audioContext = new (window.AudioContext || (window as any).webkitAudioContext)()
    analyser = audioContext.createAnalyser()
    analyser.fftSize = 512
    
    const source = audioContext.createMediaStreamSource(stream)
    source.connect(analyser)
    
    isRecording.value = true
    classification.value = 'ANALYZING...'
    transcript.value = ''
    voiceEnergyScore = 0
    noiseEnergyScore = 0
    
    if (recognition) recognition.start()
    
    drawVisualizer()
  } catch (e) {
    console.error("Audio init failed", e)
    classification.value = 'ERR_NO_MIC'
  }
}

function stopRecording() {
  isRecording.value = false
  if (recognition) recognition.stop()
  if (animationId) cancelAnimationFrame(animationId)
  if (stream) stream.getTracks().forEach(t => t.stop())
  if (audioContext) audioContext.close()
  
  // Decide final classification based on energy if no transcript was caught
  if (!transcript.value) {
    if (voiceEnergyScore > noiseEnergyScore * 1.5) {
      classification.value = 'SPEECH_UNRECOGNIZED'
    } else if (noiseEnergyScore > 50) {
      classification.value = 'AMBIENT/NOISE'
    } else {
      classification.value = 'SILENCE'
    }
  }

  // Send to backend
  processAndSaveNode()
}

async function processAndSaveNode() {
  const API_BASE = (window as any).API_BASE || ''
  
  const payload = {
    parent_id: props.node.parent_id || 'ROOT',
    source_id: props.node.id,
    type: classification.value.includes('SPEECH') ? 'text' : 'audio_signature',
    content: transcript.value || `[AMBIENT NOISE SIGNATURE: v=${voiceEnergyScore}, n=${noiseEnergyScore}]`,
    metadata: {
       voiceEnergy: voiceEnergyScore,
       noiseEnergy: noiseEnergyScore,
       isAmbient: classification.value === 'AMBIENT/NOISE'
    }
  }

  try {
    // We send this to a universal endpoint that creates a connected node
    await fetch(`${API_BASE || ''}/api/lgnn/audio/process`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
    emit('refresh')
  } catch(e) {
    console.error("Save audio node failed", e)
  }
}

function drawVisualizer() {
  if (!canvasRef.value || !analyser || !isRecording.value) return
  
  const canvas = canvasRef.value
  const ctx = canvas.getContext('2d')
  if (!ctx) return
  
  const bufferLength = analyser.frequencyBinCount
  const dataArray = new Uint8Array(bufferLength)
  
  const draw = () => {
    if (!isRecording.value) return
    animationId = requestAnimationFrame(draw)
    
    analyser!.getByteFrequencyData(dataArray)
    
    let currentVoice = 0
    let currentNoise = 0
    
    for (let i = 0; i < bufferLength; i++) {
      if (i > 3 && i < 40) currentVoice += dataArray[i]
      else currentNoise += dataArray[i]
    }
    
    voiceEnergyScore += currentVoice / 1000
    noiseEnergyScore += currentNoise / 1000
    
    if (classification.value !== 'SPEECH' && transcript.value === '') {
       if (currentVoice > currentNoise * 2 && currentVoice > 1000) {
         classification.value = 'POSSIBLE_SPEECH'
       } else if (currentNoise > 2000) {
         classification.value = 'AMBIENT/NOISE'
       }
    }

    ctx.fillStyle = '#0a0a0a'
    ctx.fillRect(0, 0, canvas.width, canvas.height)
    
    const barWidth = (canvas.width / bufferLength) * 2.5
    let barHeight
    let x = 0
    
    for (let i = 0; i < bufferLength; i++) {
      barHeight = dataArray[i] / 255 * canvas.height
      
      if (i > 3 && i < 40) {
        ctx.fillStyle = `rgb(0, ${Math.min(255, dataArray[i] + 50)}, 65)`
      } else {
        ctx.fillStyle = `rgb(${Math.min(255, dataArray[i] + 100)}, 100, 0)`
      }
      
      ctx.fillRect(x, canvas.height - barHeight, barWidth, barHeight)
      x += barWidth + 1
    }
  }
  
  draw()
}
</script>

<style scoped>
.audio-node {
  width: 300px;
  background: #111;
  border: 1px solid #333;
  display: flex;
  flex-direction: column;
  font-family: 'Space Mono', monospace;
  color: #fff;
}

.header {
  padding: 8px 12px;
  background: #1a1a1a;
  border-bottom: 1px solid #333;
  font-weight: 900;
  font-size: 12px;
  letter-spacing: 1px;
}

.icon.recording {
  color: #FF453A;
  animation: pulse 1s infinite;
}

.visualizer-container {
  padding: 10px;
  background: #000;
}

.visualizer {
  width: 100%;
  height: 80px;
  display: block;
}

.classification-strip {
  display: flex;
  justify-content: space-between;
  padding: 6px 12px;
  font-size: 10px;
  font-weight: bold;
  background: #151515;
  border-bottom: 1px solid #333;
}

.status-label {
  color: #888;
}

.controls {
  padding: 10px;
}

.rec-btn {
  width: 100%;
  padding: 8px;
  border: none;
  font-weight: 900;
  font-family: inherit;
  cursor: pointer;
  letter-spacing: 1px;
}

.rec-btn.start {
  background: #00FF41;
  color: #000;
}

.rec-btn.start:hover {
  background: #00cc33;
}

.rec-btn.stop {
  background: #FF453A;
  color: #FFF;
}

.transcript-box {
  padding: 10px;
  font-size: 10px;
  color: #00FF41;
  background: #051505;
  border-top: 1px solid #333;
  word-wrap: break-word;
}
</style>
