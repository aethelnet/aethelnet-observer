<template>
  <div class="script-view">
    <div class="code-header">
      <div class="title-group">
        <span class="title">Extension Node</span>
        <select v-model="mode" class="mode-select">
          <option value="logic">JavaScript Logic</option>
          <option value="ui">UI Extension (HTML/JS)</option>
        </select>
      </div>
      <button class="run-btn" @click="runScript">RUN</button>
    </div>
    
    <div class="editor-container" :class="{ 'split-view': mode === 'ui' }">
      <!-- VERSION CONTROL SIDEBAR -->
      <div class="version-sidebar" v-if="showVersionControl">
        <div class="sidebar-header">REALITY BRANCHES</div>
        
        <div class="branch-selector">
          <select v-model="currentBranch" @change="checkoutBranch" class="brutal-select">
            <option v-for="b in branches" :key="b.name" :value="b.name">
              {{ b.name }}
            </option>
          </select>
          <button class="icon-btn" @click="promptNewBranch">[+] FORK</button>
        </div>

        <div class="commits-list">
          <div 
            v-for="commit in currentCommits" 
            :key="commit.id" 
            class="commit-item"
            :class="{ active: commit.id === currentCommitId }"
            @click="checkoutCommit(commit.id)"
          >
            <div class="commit-hash">{{ commit.id.substring(0,6) }}</div>
            <div class="commit-msg">{{ commit.message }}</div>
          </div>
        </div>
        
        <div class="commit-action">
          <input v-model="commitMessage" class="brutal-input" placeholder="Commit message..." @keyup.enter="makeCommit" />
          <button class="run-btn" @click="makeCommit">COMMIT</button>
        </div>
      </div>

      <div class="editor-pane">
        <vue-monaco-editor
          v-model:value="code"
          :language="mode === 'ui' ? 'html' : 'javascript'"
          theme="vs-dark"
          :options="{
            minimap: { enabled: false },
            fontSize: 14,
            wordWrap: 'on',
            lineNumbers: 'on',
            scrollBeyondLastLine: false,
            automaticLayout: true
          }"
          @mount="handleEditorMount"
        />
      </div>
      
      <div class="preview-pane" v-if="mode === 'ui'">
        <div class="preview-header">LIVE PREVIEW</div>
        <iframe ref="previewFrame" class="preview-iframe" sandbox="allow-scripts allow-same-origin"></iframe>
      </div>
    </div>
    
    <div class="io-panel" v-if="mode === 'logic'">
      <div class="panel-section">
        <div class="section-title">INPUTS</div>
        <pre class="json-viewer">{{ inputs }}</pre>
      </div>
      <div class="panel-section">
        <div class="section-title">OUTPUTS</div>
        <pre class="json-viewer">{{ lastOutput }}</pre>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, shallowRef, computed } from 'vue'
import VueMonacoEditor from '@guolao/vue-monaco-editor'

const props = defineProps<{
  inputs: Record<string, any>
}>()

const emit = defineEmits(['output'])

const mode = ref('logic')
const code = ref(`/* JavaScript Logic */
// Available variables: 
// - inputs: Record<string, any> (data from connected nodes)
// - emit(data): function to output data to connected nodes

const sum = Object.values(inputs).reduce((a, b) => a + (b.value || 0), 0);
emit({ value: sum });`)

const lastOutput = ref<any>(null)
const error = ref<string | null>(null)
const previewFrame = ref<HTMLIFrameElement | null>(null)
const editorRef = shallowRef()

// --- REALITY BRANCHING (MINI-GIT) ---
const showVersionControl = ref(true)

interface Commit {
  id: string
  message: string
  code: string
  timestamp: number
  parentId: string | null
}

interface Branch {
  name: string
  head: string | null
}

const commits = ref<Commit[]>([])
const branches = ref<Branch[]>([{ name: 'main', head: null }])
const currentBranch = ref('main')
const currentCommitId = ref<string | null>(null)
const commitMessage = ref('')

const currentCommits = computed(() => {
  // Trace back from current branch head
  const b = branches.value.find(b => b.name === currentBranch.value)
  if (!b || !b.head) return []
  
  const history: Commit[] = []
  let curr = commits.value.find(c => c.id === b.head)
  while (curr) {
    history.push(curr)
    curr = commits.value.find(c => c.id === curr!.parentId)
  }
  return history
})

function makeCommit() {
  if (!commitMessage.value.trim()) {
    commitMessage.value = `Update ${new Date().toLocaleTimeString()}`
  }
  const newId = Math.random().toString(36).substring(2, 10)
  const c: Commit = {
    id: newId,
    message: commitMessage.value,
    code: code.value,
    timestamp: Date.now(),
    parentId: currentCommitId.value
  }
  commits.value.push(c)
  currentCommitId.value = newId
  
  // Update branch head
  const b = branches.value.find(b => b.name === currentBranch.value)
  if (b) {
    b.head = newId
  }
  
  commitMessage.value = ''
}

function promptNewBranch() {
  const name = prompt("Enter new branch name:")
  if (name && !branches.value.find(b => b.name === name)) {
    branches.value.push({ name, head: currentCommitId.value })
    currentBranch.value = name
  }
}

function checkoutBranch() {
  const b = branches.value.find(b => b.name === currentBranch.value)
  if (b && b.head) {
    checkoutCommit(b.head)
  }
}

function checkoutCommit(id: string) {
  const c = commits.value.find(c => c.id === id)
  if (c) {
    currentCommitId.value = c.id
    code.value = c.code
  }
}

// Initial commit
onMounted(() => {
  if (commits.value.length === 0) {
    commitMessage.value = 'Initial commit'
    makeCommit()
  }
})
// ------------------------------------

function handleEditorMount(editor: any) {
  editorRef.value = editor
}

watch(mode, (newMode) => {
  if (newMode === 'ui' && code.value.includes('JavaScript Logic')) {
    code.value = `<!-- HTML UI Extension -->
<style>
  body { font-family: 'Inter', sans-serif; background: #222; color: #00FF41; margin: 0; padding: 16px; }
  .btn { background: #E03C31; color: white; border: none; padding: 8px 16px; cursor: pointer; font-weight: bold; }
</style>

<div id="app">
  <h2>My Extension</h2>
  <p id="data-display">Waiting for data...</p>
  <button class="btn" onclick="sendOutput()">Send Output</button>
</div>

<script>
  // Listen for data from the node's inputs
  window.addEventListener('message', (event) => {
    if (event.data.type === 'INPUT_UPDATE') {
      document.getElementById('data-display').innerText = JSON.stringify(event.data.payload);
    }
  });

  function sendOutput() {
    // Send data back to the node's output
    window.parent.postMessage({ type: 'EXTENSION_OUTPUT', payload: { clicked: true } }, '*');
  }
<\/script>`
  }
})

watch(() => props.inputs, () => {
  if (mode.value === 'logic' && code.value) {
    runScript()
  } else if (mode.value === 'ui' && previewFrame.value?.contentWindow) {
    previewFrame.value.contentWindow.postMessage({
      type: 'INPUT_UPDATE',
      payload: props.inputs
    }, '*')
  }
}, { deep: true })

onMounted(() => {
  window.addEventListener('message', handleIframeMessage)
})

function handleIframeMessage(event: MessageEvent) {
  if (event.data?.type === 'EXTENSION_OUTPUT') {
    lastOutput.value = event.data.payload
    emit('output', event.data.payload)
  }
}

function runScript() {
  error.value = null
  
  if (mode.value === 'ui') {
    if (previewFrame.value) {
      previewFrame.value.srcdoc = code.value
    }
    return
  }
  
  try {
    const emitFn = (data: any) => {
      lastOutput.value = data
      emit('output', data)
    }
    
    const inputVals = Object.values(props.inputs || {})
    const firstInput = inputVals.filter(v => typeof v === 'string').join(" ") || null
    
    const func = new Function('inputs', 'input', 'emit', code.value)
    const result = func(props.inputs || {}, firstInput, emitFn)
    if (result !== undefined) {
      emitFn(result)
    }
  } catch (err: any) {
    error.value = err.message
    lastOutput.value = { error: err.message }
  }
}
</script>

<style scoped>
.script-view {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--color-bg-primary, #F4F4F0);
  color: var(--color-text-main, #1A1A1A);
  font-family: 'Inter', monospace;
}

.code-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  border-bottom: 2px solid var(--border-color, #1A1A1A);
  background: #E8E8E8;
}

.title-group {
  display: flex;
  align-items: center;
  gap: 12px;
}

.title {
  font-weight: 900;
  text-transform: uppercase;
}

.mode-select {
  background: #fff;
  border: 1px solid #1A1A1A;
  padding: 2px 6px;
  font-family: inherit;
  font-size: 12px;
  cursor: pointer;
}

.run-btn {
  background: var(--color-accent, #E03C31);
  color: #FFF;
  border: 2px solid #1A1A1A;
  padding: 4px 12px;
  font-weight: 900;
  cursor: pointer;
  box-shadow: 2px 2px 0 #1A1A1A;
}
.run-btn:active {
  transform: translate(2px, 2px);
  box-shadow: none;
}

.editor-container {
  flex: 1;
  display: flex;
  min-height: 0;
  overflow: hidden;
}

.version-sidebar {
  width: 280px;
  background: #111;
  color: #00FF41;
  display: flex;
  flex-direction: column;
  border-right: 2px solid #1A1A1A;
}

.sidebar-header {
  padding: 8px;
  background: #E03C31;
  color: #FFF;
  font-weight: 900;
  font-size: 12px;
  text-align: center;
}

.branch-selector {
  display: flex;
  padding: 8px;
  gap: 8px;
  border-bottom: 1px solid #333;
}

.brutal-select {
  flex: 1;
  background: #000;
  color: #00FF41;
  border: 1px solid #00FF41;
  font-family: inherit;
  font-size: 12px;
}

.icon-btn {
  background: #333;
  color: #FFF;
  border: 1px solid #555;
  cursor: pointer;
  font-size: 10px;
  padding: 4px 8px;
  font-family: inherit;
}
.icon-btn:hover { background: #555; }

.commits-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.commit-item {
  display: flex;
  gap: 8px;
  padding: 6px;
  background: #222;
  border: 1px solid #333;
  cursor: pointer;
  font-size: 11px;
}

.commit-item:hover {
  border-color: #00FF41;
}

.commit-item.active {
  background: rgba(0, 255, 65, 0.1);
  border-left: 4px solid #00FF41;
}

.commit-hash {
  color: #E03C31;
  font-weight: bold;
}

.commit-msg {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.commit-action {
  padding: 8px;
  display: flex;
  gap: 8px;
  border-top: 1px solid #333;
}

.brutal-input {
  flex: 1;
  background: #000;
  color: #FFF;
  border: 1px solid #555;
  padding: 4px;
  font-family: inherit;
  font-size: 11px;
}

.split-view .editor-pane {
  flex: 1;
  border-right: 2px solid #1A1A1A;
}

.editor-pane {
  flex: 1;
  height: 100%;
}

.preview-pane {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #000;
}

.preview-header {
  background: #1A1A1A;
  color: #00FF41;
  font-size: 10px;
  padding: 4px 8px;
  font-weight: bold;
}

.preview-iframe {
  flex: 1;
  border: none;
  width: 100%;
  background: #FFF;
}

.io-panel {
  height: 120px;
  display: flex;
  border-top: 2px solid #1A1A1A;
}

.panel-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  border-right: 1px solid #CCC;
}
.panel-section:last-child {
  border-right: none;
}

.section-title {
  background: #E8E8E8;
  padding: 4px 8px;
  font-size: 10px;
  font-weight: bold;
  border-bottom: 1px solid #CCC;
}

.json-viewer {
  flex: 1;
  margin: 0;
  padding: 8px;
  font-size: 11px;
  background: #F4F4F0;
  color: #1A1A1A;
  overflow-y: auto;
  white-space: pre-wrap;
  word-wrap: break-word;
}
</style>
