<template>
  <div v-if="node" class="console-overlay" :class="{ 'is-fullscreen': isFullscreen }" @mousedown.stop @touchstart.stop>
    
    <!-- HEADER -->
    <div class="console-header">
      <div class="header-left">
        <span class="icon">⚙️</span>
        <span class="title">{{ node.label || node.id }}</span>
        <span class="tag">[{{ node.source_tag || 'custom' }}]</span>
      </div>
      <div class="header-right">
        <button class="ctrl-btn" @click="toggleFullscreen">
          {{ isFullscreen ? '[ EXIT FULLSCREEN ]' : '[ FULLSCREEN ]' }}
        </button>
        <button class="ctrl-btn close" @click="$emit('close')">[ X ]</button>
      </div>
    </div>

    <!-- TABS -->
    <div class="console-tabs">
      <button 
        class="tab-btn" 
        :class="{ active: activeTab === 'config' }" 
        @click="activeTab = 'config'"
      >
        CONFIG
      </button>
      <button 
        class="tab-btn" 
        :class="{ active: activeTab === 'script' }" 
        @click="activeTab = 'script'"
      >
        SCRIPT / DATA
      </button>
      <button 
        class="tab-btn" 
        :class="{ active: activeTab === 'logs' }" 
        @click="activeTab = 'logs'"
      >
        LOGS
      </button>
      <button 
        class="tab-btn" 
        :class="{ active: activeTab === 'access' }" 
        @click="activeTab = 'access'"
      >
        ACCESS
      </button>
    </div>

    <!-- CONTENT AREA -->
    <div class="console-body">
      
      <!-- CONFIG TAB -->
      <div v-if="activeTab === 'config'" class="tab-content config-tab">
        <div v-if="Object.keys(parsedMeta).length === 0" class="empty-state">
          No configurable parameters found in node metadata.
          <br><br>
          <button class="action-btn" @click="initializeDefaultMeta">
            + INITIATE PARAMETERS
          </button>
        </div>
        
        <div v-else class="param-list">
          <div v-for="(val, key) in parsedMeta" :key="key" class="param-row">
            <label class="param-label">{{ key }}</label>
            
            <!-- Number Slider -->
            <div v-if="typeof val === 'number'" class="param-input-group">
              <input 
                type="range" 
                :min="0" 
                :max="val > 100 ? val * 2 : 100" 
                step="0.1" 
                :value="val" 
                @input="updateMeta(key, parseFloat(($event.target as HTMLInputElement).value))" 
                class="slider"
              />
              <span class="val-display">{{ val }}</span>
            </div>
            
            <!-- Boolean Toggle -->
            <div v-else-if="typeof val === 'boolean'" class="param-input-group">
              <button 
                class="toggle-btn" 
                :class="{ on: val }" 
                @click="updateMeta(key, !val)"
              >
                {{ val ? 'ENABLED' : 'DISABLED' }}
              </button>
            </div>
            
            <!-- String Input -->
            <div v-else class="param-input-group">
              <input 
                type="text" 
                :value="val" 
                @input="updateMeta(key, ($event.target as HTMLInputElement).value)" 
                class="text-input"
              />
            </div>
            
            <button class="del-param-btn" @click="deleteMeta(key)" title="Remove Parameter">x</button>
          </div>
          
          <div class="add-param-row">
            <input v-model="newParamKey" placeholder="new_parameter" class="text-input small" />
            <select v-model="newParamType" class="text-input small">
              <option value="string">String</option>
              <option value="number">Number</option>
              <option value="boolean">Boolean</option>
            </select>
            <button class="action-btn small" @click="addNewParam">ADD</button>
          </div>
        </div>
      </div>

      <!-- SCRIPT TAB -->
      <div v-if="activeTab === 'script'" class="tab-content script-tab">
        <AethelnetTip id="tip-obsidian-links">
          <strong>Pro Tip:</strong> You can type <code>[[</code> in the editor below to auto-complete and link to other nodes in the Aethelnet. Linked nodes share context natively.
        </AethelnetTip>
        <vue-monaco-editor
          v-model:value="editContent"
          theme="vs-dark"
          language="python"
          :options="monacoOptions"
          class="code-editor"
          @mount="handleEditorMount"
        />
        <div class="script-actions">
          <button class="action-btn primary" @click="saveContent">
            {{ isSaved ? 'SAVED ✓' : 'SAVE CHANGES' }}
          </button>
        </div>
      </div>

      <!-- ACCESS TAB -->
      <div v-if="activeTab === 'access'" class="tab-content access-tab">
        <div class="access-header">
          <h3>NODE PERMISSIONS</h3>
          <p>Control who can edit or interact with this specific node in the P2P network.</p>
        </div>
        
        <div class="access-options">
          <div 
            class="access-card" 
            :class="{ active: parsedMeta.permission_mode === 'public' }"
            @click="updateMeta('permission_mode', 'public')"
          >
            <div class="access-icon">[ ~ ]</div>
            <div class="access-info">
              <h4>PUBLIC (Wiki Mode)</h4>
              <p>Anyone in the network can edit the script and contents of this node.</p>
            </div>
          </div>

          <div 
            class="access-card" 
            :class="{ active: parsedMeta.permission_mode === 'protected' || !parsedMeta.permission_mode }"
            @click="updateMeta('permission_mode', 'protected')"
          >
            <div class="access-icon">[ * ]</div>
            <div class="access-info">
              <h4>PROTECTED (Forum Post Mode)</h4>
              <p>Only you can edit this node. Others can only read it or attach replies (edges) to it.</p>
            </div>
          </div>

          <div 
            class="access-card" 
            :class="{ active: parsedMeta.permission_mode === 'private' }"
            @click="updateMeta('permission_mode', 'private')"
          >
            <div class="access-icon">[ x ]</div>
            <div class="access-info">
              <h4>PRIVATE (Vault Mode)</h4>
              <p>Only you can see this node. It will not be synced to the global network.</p>
            </div>
          </div>
        </div>
        
        <div style="margin-top: 24px; padding: 16px; background: rgba(0,0,0,0.2); border-left: 2px solid #E03C31;">
          <label style="font-size: 10px; color: var(--color-text-muted); font-weight: bold; margin-bottom: 4px; display: block;">OWNER PUBLIC KEY</label>
          <input 
            type="text" 
            class="text-input" 
            style="width: 100%; font-family: monospace; font-size: 11px; background: rgba(0,0,0,0.5); color: #888;" 
            :value="parsedMeta.owner_pubkey || 'LOCAL_GUEST_ID_9921'" 
            readonly 
          />
        </div>
      </div>

      <!-- LOGS TAB -->
      <div v-if="activeTab === 'logs'" class="tab-content logs-tab">
        <div class="log-terminal">
          <div class="log-line system">> Node {{ node.id }} connected to Aethelnet.</div>
          <div class="log-line system">> Initializing semantic space...</div>
          <div class="log-line info" v-if="node.source_tag === 'spider'">> Waiting for crawl targets...</div>
          <div class="log-line info" v-if="node.source_tag === 'audio'">> VAD standby mode active.</div>
          <div class="log-line empty">_</div>
        </div>
      </div>

    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { VueMonacoEditor } from '@guolao/vue-monaco-editor'
import AethelnetTip from './AethelnetTip.vue'

const props = defineProps<{
  node: any | null,
  allNodes?: any[]
}>()

const emit = defineEmits(['close', 'update-node'])

const activeTab = ref('script')
const isFullscreen = ref(false)
const editContent = ref('')
const parsedMeta = ref<any>({})
const newParamKey = ref('')
const newParamType = ref('string')
const isSaved = ref(false)

const monacoOptions = {
  minimap: { enabled: false },
  wordWrap: 'on',
  lineNumbers: 'on',
  fontSize: 12,
  fontFamily: "'Space Mono', monospace"
}

let providerDisposable: any = null

function handleEditorMount(editor: any, monaco: any) {
  if (providerDisposable) providerDisposable.dispose()

  providerDisposable = monaco.languages.registerCompletionItemProvider(['python', 'javascript', 'markdown', 'json'], {
    triggerCharacters: ['['],
    provideCompletionItems: (model: any, position: any) => {
      const textUntilPosition = model.getValueInRange({
        startLineNumber: position.lineNumber,
        startColumn: 1,
        endLineNumber: position.lineNumber,
        endColumn: position.column
      });
      
      // Match when user types "[[something"
      const match = textUntilPosition.match(/\[\[(.*)$/);
      if (!match) {
        return { suggestions: [] };
      }
      
      const nodes = props.allNodes || []
      const suggestions = nodes.map(n => {
        let title = n.id;
        try {
          if (n.meta_data && typeof n.meta_data === 'string') {
            const meta = JSON.parse(n.meta_data);
            if (meta.title) title = meta.title;
          }
        } catch(e) {}
          
        return {
          label: `[[${title}]]`,
          kind: monaco.languages.CompletionItemKind.Reference,
          insertText: `${title}]]`,
          documentation: `ID: ${n.id}\nSource: ${n.source_tag}`,
          detail: 'Aethelnet Node Link'
        }
      })
      
      return { suggestions };
    }
  })
}

watch(() => props.node, (newNode) => {
  if (!newNode) return
  try {
    parsedMeta.value = JSON.parse(newNode.meta_data || '{}')
  } catch(e) {
    parsedMeta.value = {}
  }
  editContent.value = newNode.content || newNode.text_content || ''
}, { immediate: true })

function toggleFullscreen() {
  isFullscreen.value = !isFullscreen.value
}

function saveContent() {
  emit('update-node', props.node, parsedMeta.value, editContent.value)
  isSaved.value = true
  setTimeout(() => { isSaved.value = false }, 2000)
}

function updateMeta(key: string, value: any) {
  const newMeta = { ...parsedMeta.value, [key]: value }
  emit('update-node', props.node, newMeta, editContent.value)
}

function deleteMeta(key: string) {
  const newMeta = { ...parsedMeta.value }
  delete newMeta[key]
  emit('update-node', props.node, newMeta, editContent.value)
}

function initializeDefaultMeta() {
  updateMeta('confidence_threshold', 0.85)
  updateMeta('auto_execute', false)
  updateMeta('description', '')
}

function addNewParam() {
  if (!newParamKey.value) return
  let val: any = ''
  if (newParamType.value === 'number') val = 0
  if (newParamType.value === 'boolean') val = false
  updateMeta(newParamKey.value, val)
  newParamKey.value = ''
}
</script>

<style scoped>
.console-overlay {
  position: absolute;
  top: 60px;
  right: 20px;
  width: 400px;
  height: 500px;
  max-height: calc(100vh - 100px);
  background: rgba(10, 10, 10, 0.95);
  backdrop-filter: blur(10px);
  border: 1px solid var(--border-color);
  box-shadow: 0 10px 30px rgba(0,0,0,0.5), 0 0 0 1px rgba(255,255,255,0.1);
  display: flex;
  flex-direction: column;
  z-index: 3000;
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
  color: var(--color-text-main);
  font-family: 'Space Mono', monospace;
}

.console-overlay.is-fullscreen {
  top: 20px;
  right: 20px;
  left: 20px;
  bottom: 20px;
  width: auto;
  max-height: none;
}

.console-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: var(--color-bg-primary);
  border-bottom: 1px solid var(--border-color);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
  overflow: hidden;
}

.header-left .title {
  font-weight: 900;
  font-size: 14px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.header-left .tag {
  font-size: 10px;
  color: var(--color-text-muted);
  text-transform: uppercase;
}

.ctrl-btn {
  background: transparent;
  border: none;
  color: var(--color-text-muted);
  font-family: inherit;
  font-size: 10px;
  font-weight: 900;
  cursor: pointer;
}

.ctrl-btn:hover {
  color: var(--color-text-main);
}

.ctrl-btn.close:hover {
  color: #FF453A;
}

.console-tabs {
  display: flex;
  border-bottom: 1px solid var(--border-color);
}

.tab-btn {
  flex: 1;
  background: transparent;
  border: none;
  padding: 10px;
  color: var(--color-text-muted);
  font-family: inherit;
  font-size: 11px;
  font-weight: 900;
  cursor: pointer;
  border-bottom: 2px solid transparent;
}

.tab-btn:hover {
  background: rgba(255,255,255,0.05);
}

.tab-btn.active {
  color: var(--color-accent);
  border-bottom: 2px solid var(--color-accent);
}

.console-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.tab-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 16px;
  overflow-y: auto;
}

/* CONFIG TAB */
.empty-state {
  text-align: center;
  color: var(--color-text-muted);
  padding: 32px 16px;
  font-size: 13px;
}

/* Access Tab Styles */
.access-header {
  margin-bottom: 24px;
}
.access-header h3 {
  color: var(--color-text-main);
  margin-bottom: 8px;
  font-size: 14px;
}
.access-header p {
  color: var(--color-text-muted);
  font-size: 11px;
}
.access-options {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.access-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: rgba(0,0,0,0.3);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
}
.access-card:hover {
  background: rgba(255,255,255,0.05);
  border-color: rgba(255,255,255,0.3);
}
.access-card.active {
  background: rgba(0, 188, 212, 0.1);
  border-color: #00BCD4;
}
.access-icon {
  font-size: 24px;
}
.access-info h4 {
  margin: 0 0 4px 0;
  font-size: 13px;
  color: var(--color-text-main);
}
.access-card.active .access-info h4 {
  color: #00BCD4;
}
.access-info p {
  margin: 0;
  font-size: 11px;
  color: var(--color-text-muted);
}

.param-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.param-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.param-label {
  flex: 0 0 120px;
  font-size: 11px;
  font-weight: bold;
  overflow: hidden;
  text-overflow: ellipsis;
}

.param-input-group {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
}

.slider {
  flex: 1;
  accent-color: var(--color-accent);
}

.val-display {
  font-size: 10px;
  width: 40px;
  text-align: right;
  color: var(--color-accent);
}

.toggle-btn {
  background: transparent;
  border: 1px solid var(--border-color);
  color: var(--color-text-muted);
  padding: 4px 12px;
  font-family: inherit;
  font-size: 10px;
  font-weight: 900;
  cursor: pointer;
}

.toggle-btn.on {
  background: var(--color-accent);
  color: #000;
  border-color: var(--color-accent);
}

.text-input {
  width: 100%;
  background: rgba(0,0,0,0.3);
  border: 1px solid var(--border-color);
  color: var(--color-text-main);
  padding: 6px;
  font-family: inherit;
  font-size: 11px;
}

.del-param-btn {
  background: transparent;
  border: none;
  color: var(--color-text-muted);
  cursor: pointer;
}
.del-param-btn:hover { color: #FF453A; }

.add-param-row {
  display: flex;
  gap: 8px;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px dashed var(--border-color);
}

.text-input.small { width: auto; flex: 1; }

.action-btn {
  background: transparent;
  border: 1px solid var(--border-color);
  color: var(--color-text-main);
  padding: 8px 16px;
  font-family: inherit;
  font-size: 11px;
  font-weight: 900;
  cursor: pointer;
}
.action-btn:hover { background: rgba(255,255,255,0.1); }
.action-btn.small { padding: 4px 8px; }
.action-btn.primary {
  background: var(--color-accent);
  color: #000;
  border-color: var(--color-accent);
}
.action-btn.primary:hover {
  background: #00cc33;
}

/* SCRIPT TAB */
.script-tab {
  padding: 0;
  display: flex;
  flex-direction: column;
}

.code-editor {
  flex: 1;
  width: 100%;
  border-bottom: 1px solid var(--border-color);
}

.script-actions {
  display: flex;
  justify-content: flex-end;
  padding: 12px;
  background: var(--color-bg-primary);
}

/* LOGS TAB */
.log-terminal {
  flex: 1;
  background: #000;
  border: 1px solid var(--border-color);
  padding: 12px;
  font-size: 11px;
  overflow-y: auto;
}

.log-line { margin-bottom: 4px; }
.log-line.system { color: #888; }
.log-line.info { color: #00FF41; }
.log-line.empty { animation: blink 1s infinite; }

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}
</style>
