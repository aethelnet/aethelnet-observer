<template>
  <div class="vault-node-container glass-panel">
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
  width: 100%;
  height: 100%;
  background: var(--color-bg-primary);
  color: var(--color-text-main);
  font-family: var(--font-family);
  overflow: hidden;
}

.vault-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: #ffffff;
  border-bottom: 2px solid #000000;
}

.vault-header.unlocked {
  background: #f0f0f0;
}

.lock-status {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 14px;
  font-weight: bold;
  letter-spacing: 1px;
  color: #000000;
  text-transform: uppercase;
}

.icon {
  color: #000000;
}
.unlocked .icon {
  color: #000000;
}

.auth-btn {
  background: #ffffff;
  color: #000000;
  border: 2px solid #000000;
  border-radius: 0;
  padding: 8px 16px;
  font-size: 12px;
  font-weight: bold;
  cursor: pointer;
  text-transform: uppercase;
  box-shadow: 2px 2px 0px #000000;
}
.auth-btn:hover {
  background: #000000;
  color: #ffffff;
  transform: translate(-2px, -2px);
  box-shadow: 4px 4px 0px #000000;
}

.lock-btn {
  background: #ffffff;
  color: #000000;
  border: 2px solid #000000;
}
.lock-btn:hover {
  background: #000000;
  color: #ffffff;
}

.vault-body {
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  flex: 1;
  background: #ffffff;
}

.locked-body {
  justify-content: center;
  align-items: center;
  text-align: center;
  background: #ffffff;
  border: 2px dashed #000000;
  margin: 16px;
}

.glitch-text {
  color: #000000;
  font-size: 24px;
  font-weight: 900;
  letter-spacing: 2px;
  text-transform: uppercase;
}

.sub-text {
  font-size: 14px;
  color: #000000;
  margin-top: 16px;
  text-transform: uppercase;
  font-weight: bold;
}

.info-banner {
  font-size: 12px;
  color: #000000;
  background: #ffffff;
  padding: 12px;
  border: 2px solid #000000;
  box-shadow: 2px 2px 0px #000000;
  line-height: 1.5;
  font-weight: bold;
}

.key-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  flex: 1;
  overflow-y: auto;
}

.key-item {
  display: flex;
  gap: 8px;
  align-items: center;
  background: #ffffff;
  padding: 8px;
  border: 2px solid #000000;
  box-shadow: 2px 2px 0px #000000;
}

.key-input {
  width: 120px;
  background: #ffffff;
  border: none;
  border-right: 2px solid #000000;
  color: #000000;
  font-size: 12px;
  padding: 8px;
  font-family: var(--font-family-mono);
  font-weight: bold;
}

.val-input {
  flex: 1;
  background: #ffffff;
  border: none;
  color: #000000;
  font-size: 14px;
  padding: 8px;
  font-family: var(--font-family-mono);
  outline: none;
}

.val-input:focus {
  background: #f0f0f0;
}

.icon-btn {
  background: #ffffff;
  border: 2px solid #000000;
  color: #000000;
  padding: 4px 8px;
  font-size: 12px;
  cursor: pointer;
  font-weight: bold;
}

.icon-btn:hover {
  background: #000000;
  color: #ffffff;
}

.icon-btn.danger:hover {
  background: #000000;
  color: #ffffff;
}

.add-new {
  display: flex;
  gap: 12px;
  margin-top: 16px;
  border-top: 2px solid #000000;
  padding-top: 16px;
}

.new-key-input {
  flex: 1;
  background: #ffffff;
  border: 2px solid #000000;
  border-radius: 0;
  color: #000000;
  padding: 12px;
  font-size: 14px;
  font-family: var(--font-family-mono);
  outline: none;
}

.new-key-input:focus {
  background: #f0f0f0;
  box-shadow: 4px 4px 0px #000000;
}

.add-btn {
  background: #ffffff;
  color: #000000;
  border: 2px solid #000000;
  border-radius: 0;
  font-weight: bold;
  font-size: 14px;
  padding: 0 24px;
  cursor: pointer;
  box-shadow: 2px 2px 0px #000000;
  text-transform: uppercase;
}

.add-btn:not(:disabled):hover {
  background: #000000;
  color: #ffffff;
  transform: translate(-2px, -2px);
  box-shadow: 4px 4px 0px #000000;
}

.add-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  box-shadow: none;
}
</style>
