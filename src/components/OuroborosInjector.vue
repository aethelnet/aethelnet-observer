<template>
  <div class="ouroboros-injector" :class="{ 'is-focused': isFocused }">
    <div class="glow-line"></div>
    <div class="input-wrapper">
      <span class="prompt-symbol">><span class="cursor" v-if="!isFocused">_</span></span>
      <input 
        type="text" 
        v-model="concept" 
        @focus="isFocused = true" 
        @blur="isFocused = false"
        @keyup.enter="injectConcept"
        placeholder="INJECT CONCEPT INTO GLOBAL MESH..."
        :disabled="isInjecting"
      />
      <div class="ouroboros-icon" :class="{ 'spinning': isInjecting }">⏣</div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';

const concept = ref('');
const isFocused = ref(false);
const isInjecting = ref(false);

const injectConcept = async () => {
  const text = concept.value.trim();
  if (!text) return;
  
  isInjecting.value = true;
  
  try {
    const baseUrl = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';
    
    // Inject into local LGNN
    const res = await fetch(`${baseUrl}/api/lgnn/feed`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text })
    });
    
    if (res.ok) {
      // The local backend will handle the P2P gossip sync if publishLocal is enabled
      // The graph store/3D view will fetch the new node on its next poll
      concept.value = '';
    }
  } catch (err) {
    console.error("[OUROBOROS] Injection failed:", err);
  } finally {
    isInjecting.value = false;
  }
};
</script>

<style scoped>
.ouroboros-injector {
  position: absolute;
  bottom: 30px;
  left: 50%;
  transform: translateX(-50%);
  width: 500px;
  background: rgba(10, 10, 15, 0.7);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(0, 255, 204, 0.2);
  border-radius: 4px;
  z-index: 9998;
  transition: all 0.3s ease;
  overflow: hidden;
}

.ouroboros-injector.is-focused {
  width: 600px;
  background: rgba(10, 10, 15, 0.9);
  border-color: #00ffcc;
  box-shadow: 0 0 20px rgba(0, 255, 204, 0.1);
}

.glow-line {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 2px;
  background: #00ffcc;
  transform: scaleX(0);
  transition: transform 0.3s ease;
  transform-origin: center;
}

.ouroboros-injector.is-focused .glow-line {
  transform: scaleX(1);
}

.input-wrapper {
  display: flex;
  align-items: center;
  padding: 12px 20px;
}

.prompt-symbol {
  color: #00ffcc;
  font-family: 'JetBrains Mono', monospace;
  font-size: 1.1rem;
  font-weight: bold;
  margin-right: 12px;
}

.cursor {
  animation: blink 1s step-end infinite;
}

input {
  flex: 1;
  background: transparent;
  border: none;
  color: #fff;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.9rem;
  outline: none;
}

input::placeholder {
  color: rgba(255, 255, 255, 0.3);
  letter-spacing: 1px;
}

.ouroboros-icon {
  color: rgba(0, 255, 204, 0.5);
  font-size: 1.2rem;
  margin-left: 10px;
  transition: color 0.3s ease;
}

.ouroboros-injector.is-focused .ouroboros-icon {
  color: #00ffcc;
}

.spinning {
  animation: spin 1s linear infinite;
  color: #ff3366 !important;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
