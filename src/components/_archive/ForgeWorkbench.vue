<template>
  <div class="forge-overlay" @mousedown.stop @touchstart.stop>
    <div class="forge-container">
      <div class="forge-header">
        <div class="header-title">
          <span class="icon">F</span>
          <h2>THE FORGE <span class="subtitle">// OS BUILDER WORKBENCH</span></h2>
        </div>
        <button class="close-btn" @click="$emit('close')">[ X ]</button>
      </div>

      <div class="forge-body">
        <div v-show="activeTab !== 'script'" class="forge-sidebar">
          
          <!-- LIVE PREVIEW BOX -->
          <div class="sidebar-section live-preview-section">
            <label>LIVE PREVIEW</label>
            <div class="live-preview-box" :style="{ borderColor: blueprint.color, boxShadow: `0 0 15px ${blueprint.color}40` }">
              <div class="preview-header" :style="{ background: blueprint.color }">
                <span class="preview-icon">{{ blueprint.icon }}</span>
                <span class="preview-title" style="color: #000;">{{ blueprint.name || 'App Name' }}</span>
              </div>
              <div class="preview-body">
                <div v-for="(val, key) in blueprint.meta_data" :key="key" class="preview-param">
                  <span class="p-key">{{ key }}</span>
                  <div v-if="typeof val === 'number'" class="p-slider-mock"></div>
                  <div v-else-if="typeof val === 'boolean'" class="p-toggle-mock"></div>
                  <span v-else class="p-val-mock">[str]</span>
                </div>
                <div v-if="Object.keys(blueprint.meta_data).length === 0" style="color: #666; font-size: 9px; font-style: italic;">
                  No parameters defined.
                </div>
              </div>
            </div>
          </div>

          <div class="sidebar-section">
            <label>APP NAME</label>
            <input v-model="blueprint.name" class="forge-input" placeholder="e.g. Sentinel Scanner" />
          </div>

          <div class="sidebar-section">
            <label>CATEGORY / TAG</label>
            <input v-model="blueprint.category" class="forge-input" placeholder="e.g. SENSORS, WEAPONS, UTILITY" />
          </div>

          <div class="sidebar-section">
            <label>ASCII IDENTIFIER</label>
            <input v-model="blueprint.icon" class="forge-input" placeholder="e.g. [*]" />
            <div class="ascii-suggester">
              <button 
                v-for="sym in ['[+]', '[*]', '[~]', '[>]', '[#]', '◬', '◈', 'Ξ', 'Σ', 'Ω']" 
                :key="sym"
                class="ascii-btn"
                @click="blueprint.icon = sym"
              >
                {{ sym }}
              </button>
            </div>
          </div>

          <div class="sidebar-section">
            <label>LICENSE</label>
            <input v-model="blueprint.license" class="forge-input" placeholder="e.g. AGPL-3.0" />
            <div style="font-size: 8px; color: var(--color-text-muted); margin-top: 4px;">
              By default, all Aethelnet scripts are AGPL-3.0 to keep the ecosystem open.
            </div>
          </div>

          <div class="sidebar-section">
            <label>THEME COLOR</label>
            <div class="color-picker">
              <button 
                v-for="color in ['#00FF41', '#FF9800', '#E03C31', '#00E5FF', '#F2C12E', '#FFFFFF']" 
                :key="color"
                class="color-btn"
                :style="{ background: color }"
                :class="{ active: blueprint.color === color }"
                @click="blueprint.color = color"
              ></button>
            </div>
          </div>
          
          <div class="sidebar-section" style="margin-top: auto;">
            <button class="forge-action-btn submit-btn" @click="saveBlueprint">
              [+] FORGE BLUEPRINT
            </button>
          </div>
        </div>

        <div class="forge-main">
          <div class="forge-tabs">
            <button :class="['forge-tab', { active: activeTab === 'parameters' }]" @click="activeTab = 'parameters'">PARAMETERS</button>
            <button :class="['forge-tab', { active: activeTab === 'script' }]" @click="activeTab = 'script'">PYTHON LOGIC</button>
            <button :class="['forge-tab', { active: activeTab === 'frontend' }]" @click="activeTab = 'frontend'">FRONTEND UI</button>
          </div>

          <!-- PARAMETERS TAB -->
          <div v-if="activeTab === 'parameters'" class="tab-content">
            <div class="params-header">Define the state variables and UI sliders for this Node.</div>
            
            <div class="param-list">
              <div v-for="(type, key) in blueprint.meta_data" :key="key" class="param-row">
                <span class="param-key">{{ key }}</span>
                <span class="param-type">{{ typeof type }}</span>
                <button class="delete-btn" @click="deleteParam(key as string)">x</button>
              </div>
            </div>

            <div class="add-param-form">
              <input v-model="newParamKey" placeholder="variable_name" class="forge-input small" />
              <select v-model="newParamType" class="forge-input small">
                <option value="string">String</option>
                <option value="number">Number (Slider)</option>
                <option value="boolean">Boolean (Toggle)</option>
              </select>
              <button class="forge-action-btn small" @click="addParam">ADD PARAM</button>
            </div>
          </div>

          <!-- SCRIPT TAB -->
          <div v-if="activeTab === 'script'" class="tab-content" style="padding: 0;">
            <vue-monaco-editor
              v-model:value="blueprint.script"
              theme="vs-dark"
              language="python"
              @mount="handleEditorMount"
              class="forge-editor"
            />
          </div>

          <!-- FRONTEND TAB -->
          <div v-if="activeTab === 'frontend'" class="tab-content" style="padding: 0;">
            <vue-monaco-editor
              v-model:value="blueprint.ui_template"
              theme="vs-dark"
              language="html"
              class="forge-editor"
            />
          </div>

        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { VueMonacoEditor } from '@guolao/vue-monaco-editor'
import { API_BASE } from '../shared/api.js'

const emit = defineEmits(['close', 'blueprint-forged'])

const activeTab = ref('parameters')

const blueprint = ref({
  id: 'APP_' + Date.now(),
  name: 'New Custom App',
  category: 'CUSTOM BLUEPRINTS',
  license: 'AGPL-3.0',
  icon: '[*]',
  color: '#00FF41',
  meta_data: {} as Record<string, any>,
  script: `# =====================================================================
# 🧠 AETHELNET PYTHON CORE (Backend Logic)
# =====================================================================
# This script runs securely in the LGNN backend.
# You have access to three magical variables:
# 1. state (dict): Persistent memory. Variables you save here are 
#    available next time the script runs! (e.g. state['count'] = 1)
# 2. node_id (str): The unique ID of this node.
# 3. graph (object): The Liquid Graph itself (Advanced users only).
#
# Standard modules like math, json, random, datetime are already 
# injected and ready to use! No need to import them.
# =====================================================================

# Example: A simple counter that remembers its value
count = state.get("count", 0)
count += 1
state["count"] = count

print(f"Node {node_id} executed {count} times.")
`,
  ui_template: `<!-- =====================================================================
  🌐 AETHELNET UI CANVAS (Frontend View)
======================================================================
  Welcome to your custom app's visual interface!
  We automatically inject a beautiful CSS framework for you.
  Try using classes like 'container', 'card', 'btn', and 'bar'.
====================================================================== -->

<div class="container">
  <h1>Welcome to my App!</h1>
  
  <div class="card">
    <p>This is a custom Aethelnet App running in a secure Sandbox.</p>
    
    <!-- 
      You can communicate with your Python backend by calling:
      Aethelnet.sendMessage("my_action")
    -->
    <button class="btn" onclick="Aethelnet.sendMessage('clicked')">EXECUTE</button>
  </div>
</div>`
})

const newParamKey = ref('')
const newParamType = ref('string')
const isForging = ref(false)

function handleEditorMount(editor: any, monaco: any) {
  // Register Aethelnet-specific Python snippets and autocomplete
  monaco.languages.registerCompletionItemProvider('python', {
    provideCompletionItems: (model: any, position: any) => {
      const suggestions = [
        {
          label: 'graph.find_nodes',
          kind: monaco.languages.CompletionItemKind.Function,
          insertText: 'graph.find_nodes(source_tag="${1:tag}")',
          insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
          documentation: 'Returns a list of nodes matching the source tag.'
        },
        {
          label: 'graph.spawn_node',
          kind: monaco.languages.CompletionItemKind.Function,
          insertText: 'graph.spawn_node(label="${1:New Node}", content="${2:Data}", source_tag="${3:custom}")',
          insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
          documentation: 'Spawns a new node into the active graph.'
        },
        {
          label: 'state.get',
          kind: monaco.languages.CompletionItemKind.Method,
          insertText: 'state.get("${1:key}", ${2:default})',
          insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
          documentation: 'Get a parameter from the node state.'
        },
        {
          label: 'state.set',
          kind: monaco.languages.CompletionItemKind.Method,
          insertText: 'state.set("${1:key}", ${2:value})',
          insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
          documentation: 'Save a parameter to the node state.'
        },
        {
          label: 'aethelnet_macro',
          kind: monaco.languages.CompletionItemKind.Snippet,
          insertText: [
            'def run(node, graph, state):',
            '\t# Get input parameter',
            '\ttarget = state.get("target_url", "")',
            '\t',
            '\t# Spawn a result node',
            '\tgraph.spawn_node(label="Result", content=target)',
            '\t',
            '\treturn {"status": "success"}'
          ].join('\n'),
          insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
          documentation: 'Boilerplate for a standard Aethelnet App execution block.'
        }
      ]
      return { suggestions }
    }
  })
}

function addParam() {
  if (!newParamKey.value) return
  let val: any = ''
  if (newParamType.value === 'number') val = 0
  if (newParamType.value === 'boolean') val = false
  
  blueprint.value.meta_data[newParamKey.value] = val
  newParamKey.value = ''
}

function deleteParam(key: string) {
  delete blueprint.value.meta_data[key]
}

async function saveBlueprint() {
  // Save to localStorage so Toolbox can load it
  const existing = JSON.parse(localStorage.getItem('aethelnet_blueprints') || '[]')
  existing.push(blueprint.value)
  localStorage.setItem('aethelnet_blueprints', JSON.stringify(existing))
  
  // Publish to LGNN MARKETPLACE subgraph
  try {
    const pubNode = {
      id: `bp_${blueprint.value.name.replace(/\\s+/g, '_').toLowerCase()}_${Date.now()}`,
      label: blueprint.value.name,
      content: blueprint.value.script,
      source_tag: "blueprint",
      meta_data: {
        ...blueprint.value.meta_data,
        name: blueprint.value.name,
        category: blueprint.value.category,
        license: blueprint.value.license,
        permission_mode: "public", // Allow others to see and fork
        ui_template: blueprint.value.ui_template
      },
      parent_id: "MARKETPLACE"
    }
    await fetch(`${API_BASE}/lgnn/node`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(pubNode)
    })
  } catch (e) {
    console.error("Failed to publish blueprint to Global Market:", e)
  }
  
  emit('blueprint-forged', blueprint.value)
  emit('close')
}
</script>

<style scoped>
.forge-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(5, 5, 5, 0.9);
  backdrop-filter: blur(15px);
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  animation: fadeIn 0.3s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; transform: scale(1.05); }
  to { opacity: 1; transform: scale(1); }
}

.forge-container {
  width: 1100px;
  height: 750px;
  max-width: 95vw;
  max-height: 95vh;
  background: var(--color-bg-panel);
  background-image: 
    linear-gradient(rgba(0, 255, 65, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0, 255, 65, 0.03) 1px, transparent 1px);
  background-size: 20px 20px;
  border: 1px solid var(--border-color);
  box-shadow: 0 0 50px rgba(0,0,0,0.8), 0 0 0 1px rgba(255,255,255,0.1), inset 0 0 100px rgba(0,0,0,0.5);
  display: flex;
  flex-direction: column;
  position: relative;
  overflow: hidden;
}

.forge-container::after {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  background: linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.25) 50%), linear-gradient(90deg, rgba(255, 0, 0, 0.06), rgba(0, 255, 0, 0.02), rgba(0, 0, 255, 0.06));
  background-size: 100% 2px, 3px 100%;
  pointer-events: none;
  z-index: 10;
}

.forge-header {
  height: 50px;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
  background: rgba(20, 20, 20, 0.9);
}

.header-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-title .icon {
  font-weight: 900;
  color: #E03C31;
  font-size: 18px;
}

.header-title h2 {
  margin: 0;
  font-size: 14px;
  font-weight: 900;
  letter-spacing: 1px;
}

.subtitle {
  color: var(--color-text-muted);
  font-weight: normal;
}

.close-btn {
  background: none;
  border: none;
  color: var(--color-text-muted);
  font-family: 'Space Mono', monospace;
  cursor: pointer;
}
.close-btn:hover {
  color: #E03C31;
}

.forge-body {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.forge-sidebar {
  width: 300px;
  border-right: 1px solid var(--border-color);
  background: rgba(10, 10, 10, 0.8);
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  z-index: 20;
}

.live-preview-box {
  background: rgba(0,0,0,0.6);
  border: 1px solid var(--border-color);
  border-radius: 4px;
  overflow: hidden;
  margin-top: 8px;
}
.preview-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  font-weight: 900;
  font-size: 11px;
}
.preview-body {
  padding: 10px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.preview-param {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.p-key {
  font-size: 9px;
  color: var(--color-text-main);
  font-family: 'Space Mono', monospace;
}
.p-slider-mock {
  width: 50px; height: 4px; background: rgba(255, 255, 255, 0.5); border-radius: 2px;
}
.p-toggle-mock {
  width: 20px; height: 10px; background: rgba(255, 255, 255, 0.5); border-radius: 5px;
}
.p-val-mock {
  font-size: 9px; color: #aaa;
}

.sidebar-section label {
  display: block;
  font-size: 10px;
  color: var(--color-text-muted);
  margin-bottom: 6px;
  font-family: 'Space Mono', monospace;
}

.forge-input {
  width: 100%;
  background: rgba(0,0,0,0.5);
  border: 1px solid var(--border-color);
  color: #fff;
  padding: 8px;
  font-family: 'Space Mono', monospace;
  font-size: 12px;
}
.forge-input:focus {
  outline: none;
  border-color: #00FF41;
}

.color-picker {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.color-btn {
  width: 24px;
  height: 24px;
  border-radius: 4px;
  border: 2px solid transparent;
  cursor: pointer;
}
.color-btn.active {
  border-color: #fff;
  box-shadow: 0 0 10px currentColor;
}

.ascii-suggester {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 8px;
}
.ascii-btn {
  background: rgba(255,255,255,0.05);
  border: 1px solid var(--border-color);
  color: var(--color-text-main);
  padding: 4px 8px;
  font-family: 'Space Mono', monospace;
  font-size: 10px;
  cursor: pointer;
}
.ascii-btn:hover {
  background: rgba(255,255,255,0.1);
  border-color: #00FF41;
}

.forge-action-btn {
  width: 100%;
  background: transparent;
  border: 1px solid var(--color-text-muted);
  color: var(--color-text-main);
  padding: 10px;
  font-weight: 900;
  cursor: pointer;
  text-transform: uppercase;
  font-size: 12px;
  transition: all 0.2s;
}
.forge-action-btn:hover {
  background: rgba(255,255,255,0.1);
}
.forge-action-btn.submit-btn {
  background: #E03C31;
  border-color: #E03C31;
  color: #111;
}
.forge-action-btn.submit-btn:hover {
  background: #ff5246;
}

.forge-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  z-index: 20;
}

.forge-tabs {
  display: flex;
  border-bottom: 1px solid var(--border-color);
}

.forge-tab {
  padding: 12px 20px;
  background: transparent;
  border: none;
  border-right: 1px solid var(--border-color);
  color: var(--color-text-muted);
  font-weight: bold;
  font-size: 11px;
  cursor: pointer;
}
.forge-tab.active {
  background: rgba(255,255,255,0.05);
  color: #fff;
  border-bottom: 2px solid #E03C31;
}

.tab-content {
  flex: 1;
  padding: 20px;
  display: flex;
  flex-direction: column;
  overflow: auto;
}

.params-header {
  font-size: 12px;
  color: var(--color-text-muted);
  margin-bottom: 20px;
}

.param-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 20px;
}

.param-row {
  display: flex;
  align-items: center;
  gap: 12px;
  background: rgba(0,0,0,0.3);
  padding: 8px 12px;
  border: 1px solid var(--border-color);
}

.param-key {
  color: #00FF41;
  font-family: 'Space Mono', monospace;
  font-size: 12px;
  flex: 1;
}

.param-type {
  color: var(--color-text-muted);
  font-size: 10px;
  text-transform: uppercase;
}

.delete-btn {
  background: none;
  border: none;
  color: #E03C31;
  cursor: pointer;
  font-weight: bold;
}

.add-param-form {
  display: flex;
  gap: 12px;
  background: rgba(255,255,255,0.02);
  padding: 12px;
  border: 1px dashed var(--border-color);
}
.add-param-form .small {
  padding: 6px;
}

.forge-editor {
  width: 100%;
  height: 100%;
}
</style>
