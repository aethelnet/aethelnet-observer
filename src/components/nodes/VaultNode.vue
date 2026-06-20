<template>
  <div class="vault-node-container" @mousedown.stop @touchstart.stop>
    <div class="vault-header" :class="{ unlocked: isUnlocked }">
      <div class="lock-status">
        <span class="icon">{{ isUnlocked ? '[ OPEN ]' : '[ LOCKED ]' }}</span>
        <span>{{ isUnlocked ? 'VAULT UNLOCKED' : 'VAULT SECURED' }}</span>
      </div>
      <button v-if="!isUnlocked" class="auth-btn" @click="unlock">AUTHENTICATE</button>
      <button v-else class="auth-btn lock-btn" @click="lock">LOCK</button>
    </div>

    <div class="vault-body" v-if="isUnlocked">
      <div class="info-banner">
        ⚠️ Keys are stored locally in your browser and are NEVER synced or shared in blueprints.
      </div>
      
      <div class="key-list">
        <div v-for="(val, key) in secrets" :key="key" class="key-item">
          <input type="text" class="key-input" :value="key" readonly />
          <input :type="showSecrets[key] ? 'text' : 'password'" class="val-input" v-model="secrets[key]" @blur="saveSecrets" placeholder="Paste Secret/API Key..." />
          <button class="icon-btn" @click="toggleVisibility(key as string)">
            {{ showSecrets[key] ? '[HIDE]' : '[SHOW]' }}
          </button>
          <button class="icon-btn danger" @click="removeSecret(key as string)">[X]</button>
        </div>
      </div>

      <div class="add-new">
        <input type="text" class="new-key-input" v-model="newKeyName" placeholder="NEW_VAR_NAME" @keydown.enter="addSecret" />
        <button class="add-btn" @click="addSecret" :disabled="!newKeyName.trim()">ADD</button>
      </div>
    </div>
    <div class="vault-body locked-body" v-else>
      <div class="glitch-text">ACCESS DENIED</div>
      <p class="sub-text">Enter Authorization to Access Encrypted Variables</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'

const props = defineProps<{
  node: any
}>()

const isUnlocked = ref(false)
const secrets = ref<Record<string, string>>({})
const showSecrets = ref<Record<string, boolean>>({})
const newKeyName = ref('')

const storageKey = computed(() => `aethel_vault_${props.node.id}`)

import { computed } from 'vue'

onMounted(() => {
  // We do not load secrets into RAM until unlocked to simulate security
})

function unlock() {
  // In a real app we'd prompt for a password. For now, it's a simulated local vault.
  const stored = localStorage.getItem(storageKey.value)
  if (stored) {
    try {
      secrets.value = JSON.parse(stored)
    } catch (e) {
      secrets.value = {}
    }
  }
  isUnlocked.value = true
}

function lock() {
  isUnlocked.value = false
  secrets.value = {}
  showSecrets.value = {}
}

function saveSecrets() {
  localStorage.setItem(storageKey.value, JSON.stringify(secrets.value))
}

function addSecret() {
  const k = newKeyName.value.trim().toUpperCase().replace(/\s+/g, '_')
  if (k && !secrets.value[k]) {
    secrets.value[k] = ''
    newKeyName.value = ''
    saveSecrets()
  }
}

function removeSecret(key: string) {
  delete secrets.value[key]
  delete showSecrets.value[key]
  saveSecrets()
}

function toggleVisibility(key: string) {
  showSecrets.value[key] = !showSecrets.value[key]
}
</script>

<style scoped>
.vault-node-container {
  display: flex;
  flex-direction: column;
  width: 340px;
  background: rgba(10, 10, 12, 0.7);
  backdrop-filter: blur(15px);
  -webkit-backdrop-filter: blur(15px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  font-family: 'Inter', 'Space Mono', monospace;
  color: #fff;
  box-shadow: 0 10px 30px rgba(0,0,0,0.5), inset 0 0 20px rgba(0,255,65,0.05);
  overflow: hidden;
  transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
}

.vault-node-container:hover {
  box-shadow: 0 15px 40px rgba(0,0,0,0.6), inset 0 0 30px rgba(0,255,65,0.1);
  transform: translateY(-2px);
}

.vault-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: rgba(0, 0, 0, 0.4);
  border-bottom: 2px solid #E03C31;
  transition: all 0.4s ease;
}

.vault-header.unlocked {
  border-bottom-color: #00FF41;
  background: rgba(0, 255, 65, 0.05);
}

.lock-status {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 1.5px;
  color: rgba(255,255,255,0.8);
}

.icon {
  color: #E03C31;
  transition: color 0.4s ease;
}
.unlocked .icon {
  color: #00FF41;
}

.auth-btn {
  background: #E03C31;
  color: #FFF;
  border: none;
  border-radius: 4px;
  padding: 6px 12px;
  font-size: 10px;
  font-weight: 800;
  cursor: pointer;
  text-transform: uppercase;
  transition: all 0.2s ease;
  box-shadow: 0 0 10px rgba(224, 60, 49, 0.3);
}
.auth-btn:hover {
  background: #ff473a;
  box-shadow: 0 0 15px rgba(224, 60, 49, 0.6);
  transform: scale(1.05);
}

.lock-btn {
  background: rgba(0, 255, 65, 0.1);
  color: #00FF41;
  border: 1px solid rgba(0, 255, 65, 0.3);
  box-shadow: none;
}
.lock-btn:hover {
  background: rgba(0, 255, 65, 0.2);
  border-color: #00FF41;
  box-shadow: 0 0 15px rgba(0, 255, 65, 0.4);
}

.vault-body {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 180px;
}

.locked-body {
  justify-content: center;
  align-items: center;
  text-align: center;
  background: repeating-linear-gradient(
    45deg,
    rgba(20,20,20,0.5),
    rgba(20,20,20,0.5) 10px,
    rgba(30,30,30,0.5) 10px,
    rgba(30,30,30,0.5) 20px
  );
  position: relative;
  overflow: hidden;
}

.locked-body::after {
  content: "";
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  background: linear-gradient(180deg, transparent 0%, rgba(224, 60, 49, 0.1) 100%);
  pointer-events: none;
}

.glitch-text {
  color: #E03C31;
  font-size: 20px;
  font-weight: 900;
  letter-spacing: 4px;
  text-shadow: 2px 0 0 rgba(255,0,0,0.8), -2px 0 0 rgba(0,255,255,0.8);
  animation: glitch-anim 2s infinite linear alternate-reverse;
}

@keyframes glitch-anim {
  0% { text-shadow: 2px 0 0 rgba(255,0,0,0.8), -2px 0 0 rgba(0,255,255,0.8); }
  25% { text-shadow: -2px 0 0 rgba(255,0,0,0.8), 2px 0 0 rgba(0,255,255,0.8); }
  50% { text-shadow: 2px 0 0 rgba(255,0,0,0.8), 2px 0 0 rgba(0,255,255,0.8); }
  75% { text-shadow: -2px 0 0 rgba(255,0,0,0.8), -2px 0 0 rgba(0,255,255,0.8); }
  100% { text-shadow: 2px 0 0 rgba(255,0,0,0.8), -2px 0 0 rgba(0,255,255,0.8); }
}

.sub-text {
  font-size: 11px;
  color: rgba(255,255,255,0.5);
  margin-top: 12px;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.info-banner {
  font-size: 10px;
  color: #F2C12E;
  background: rgba(242, 193, 46, 0.05);
  padding: 8px 10px;
  border-radius: 4px;
  border-left: 3px solid #F2C12E;
  line-height: 1.4;
}

.key-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-height: 220px;
  overflow-y: auto;
  padding-right: 4px;
}

.key-list::-webkit-scrollbar {
  width: 4px;
}
.key-list::-webkit-scrollbar-track {
  background: rgba(0,0,0,0.2);
}
.key-list::-webkit-scrollbar-thumb {
  background: rgba(255,255,255,0.2);
  border-radius: 2px;
}

.key-item {
  display: flex;
  gap: 6px;
  align-items: center;
  background: rgba(0,0,0,0.3);
  padding: 4px;
  border-radius: 4px;
  border: 1px solid rgba(255,255,255,0.05);
}

.key-input {
  width: 90px;
  background: transparent;
  border: none;
  border-right: 1px solid rgba(255,255,255,0.1);
  color: rgba(255,255,255,0.7);
  font-size: 10px;
  padding: 4px 6px;
  font-family: 'Space Mono', monospace;
}

.val-input {
  flex: 1;
  background: transparent;
  border: none;
  color: #00FF41;
  font-size: 11px;
  padding: 4px 8px;
  font-family: 'Space Mono', monospace;
  outline: none;
  transition: all 0.2s ease;
}
.val-input:focus {
  background: rgba(0, 255, 65, 0.05);
}

.icon-btn {
  background: transparent;
  border: none;
  color: rgba(255,255,255,0.4);
  padding: 4px 6px;
  font-size: 10px;
  cursor: pointer;
  transition: all 0.2s ease;
  border-radius: 3px;
}
.icon-btn:hover {
  color: #FFF;
  background: rgba(255,255,255,0.1);
}
.icon-btn.danger:hover {
  background: rgba(224, 60, 49, 0.2);
  color: #E03C31;
}

.add-new {
  display: flex;
  gap: 8px;
  margin-top: auto;
  border-top: 1px solid rgba(255,255,255,0.1);
  padding-top: 16px;
}

.new-key-input {
  flex: 1;
  background: rgba(0,0,0,0.4);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 4px;
  color: #FFF;
  padding: 8px 10px;
  font-size: 11px;
  font-family: 'Space Mono', monospace;
  outline: none;
  transition: all 0.2s ease;
}
.new-key-input:focus {
  border-color: #00FF41;
  box-shadow: 0 0 10px rgba(0,255,65,0.2);
}

.add-btn {
  background: rgba(255,255,255,0.1);
  color: #FFF;
  border: 1px solid rgba(255,255,255,0.2);
  border-radius: 4px;
  font-weight: 800;
  font-size: 11px;
  padding: 0 16px;
  cursor: pointer;
  transition: all 0.2s ease;
}
.add-btn:not(:disabled):hover {
  background: #FFF;
  color: #000;
  transform: translateY(-1px);
}
.add-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}
</style>
