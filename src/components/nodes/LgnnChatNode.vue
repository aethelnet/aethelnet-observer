<template>
  <HoloFrame 
    title="TOM RIDDLE DIARY" 
    color="#E03C31" 
    :width="360"
    @collapse="$emit('toggle-expand')"
    @action-primary="clearHistory"
  >
    <template #icon>
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="width:14px; height:14px;">
        <path d="M4 19 C 4 19, 12 11, 20 19" />
        <path d="M4 5 C 4 5, 12 13, 20 5" />
        <line x1="12" y1="5" x2="12" y2="19" stroke-dasharray="2 2" />
        <circle cx="4" cy="19" r="2" fill="currentColor"/>
        <circle cx="20" cy="5" r="2" fill="currentColor"/>
      </svg>
    </template>
    <template #action-primary-icon>🗑️</template>
    
    <div class="chat-history" ref="historyRef">
      <div v-for="(msg, idx) in messages" :key="idx" :class="['message', msg.role]">
        <div class="msg-role">{{ msg.role === 'user' ? 'YOU' : 'LGNN' }}</div>
        <div class="msg-content">{{ msg.content }}</div>
      </div>
      <div v-if="isLoading" class="message lgnn loading">
        <div class="msg-role">LGNN</div>
        <div class="msg-content blink">evolving topology...</div>
      </div>
    </div>
    
    <template #footer>
      <div class="chat-input-area">
        <textarea 
          v-model="inputText" 
          placeholder="Enter mathematical resonance prompt..." 
          @keydown.enter.prevent="sendMessage"
        ></textarea>
        <button @click="sendMessage" :disabled="isLoading || !inputText.trim()">SEND</button>
      </div>
    </template>
  </HoloFrame>
</template>

<script setup lang="ts">
import { ref, nextTick } from 'vue'
import { API_BASE } from '../../shared/api.js'
import HoloFrame from '../HoloFrame.vue'

const props = defineProps<{ node: any }>()
const emit = defineEmits(['update', 'toggle-expand'])

const messages = ref<{role: string, content: string}[]>([])
const inputText = ref('')
const isLoading = ref(false)
const historyRef = ref<HTMLElement | null>(null)

function clearHistory() {
  messages.value = []
}

async function sendMessage() {
  if (!inputText.value.trim() || isLoading.value) return
  
  const userText = inputText.value
  messages.value.push({ role: 'user', content: userText })
  inputText.value = ''
  isLoading.value = true
  
  await nextTick()
  if (historyRef.value) historyRef.value.scrollTop = historyRef.value.scrollHeight

  try {
    const url = `${API_BASE}/api/lgnn/evolve-text`
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: userText })
    })
    
    if (!res.ok) throw new Error('Network response was not ok')
    
    const data = await res.json()
    messages.value.push({ role: 'lgnn', content: data.evolved_text || JSON.stringify(data) })
  } catch (err: any) {
    messages.value.push({ role: 'lgnn', content: `[ERROR] ${err.message}` })
  } finally {
    isLoading.value = false
    await nextTick()
    if (historyRef.value) historyRef.value.scrollTop = historyRef.value.scrollHeight
  }
}
</script>

<style scoped>
.chat-history {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.message {
  padding: 10px;
  border-radius: 4px;
  font-size: 14px;
  line-height: 1.4;
  white-space: pre-wrap;
}
.message.user {
  background: #2a2a2a;
  border-left: 3px solid #00d4ff;
  align-self: flex-end;
  max-width: 85%;
}
.message.lgnn {
  background: #1a1a1a;
  border-left: 3px solid #E03C31;
  align-self: flex-start;
  max-width: 85%;
}
.msg-role {
  font-size: 10px;
  color: #888;
  margin-bottom: 4px;
  font-weight: bold;
}
.chat-input-area {
  display: flex;
  padding: 10px;
  border-top: 1px solid var(--border-color);
  background: #111;
}
textarea {
  flex: 1;
  background: #222;
  color: #fff;
  border: 1px solid #333;
  padding: 8px;
  font-family: var(--font-family-mono);
  resize: none;
  height: 40px;
}
textarea:focus {
  outline: none;
  border-color: #00d4ff;
}
button {
  background: #00d4ff;
  color: #000;
  border: none;
  font-weight: bold;
  padding: 0 16px;
  cursor: pointer;
  margin-left: 8px;
}
button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.blink {
  animation: blink 1s infinite;
}
@keyframes blink {
  50% { opacity: 0.5; }
}
</style>
