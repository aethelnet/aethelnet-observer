<template>
  <div class="custom-node-card" :style="{ borderColor: meta.blueprint?.color || 'var(--border-color)' }">
    <div class="node-header" :style="{ color: meta.blueprint?.color || 'var(--color-text-main)' }">
      <span class="icon">{{ meta.blueprint?.icon || '◈' }}</span>
      <span class="title">{{ meta.blueprint?.name || 'Custom App' }}</span>
    </div>
    
    <div class="node-parts" style="display: flex; flex-direction: column; gap: 8px;">
      <template v-for="(part, i) in meta.blueprint?.parts" :key="i">
        
        <!-- TEXT INPUT -->
        <div v-if="part.type === 'input_text'" style="display: flex; flex-direction: column; gap: 4px;">
          <input 
            type="text" 
            :placeholder="part.placeholder || '...'" 
            v-model="state[i]" 
            @mousedown.stop 
            @change="saveState"
            style="background: #F4F4F0; border: 2px solid #1A1A1A; padding: 4px; font-family: 'Space Mono', monospace; font-size: 12px; outline: none; width: 100%; box-sizing: border-box;"
          />
        </div>

        <!-- SLIDER INPUT -->
        <div v-if="part.type === 'input_slider'" style="display: flex; flex-direction: column; gap: 4px; padding: 4px; border: 2px solid #1A1A1A; background: #F4F4F0;">
          <label style="font-size: 10px; font-weight: bold; display: flex; justify-content: space-between;">
            <span>{{ part.label || 'SLIDER' }}</span>
            <span>{{ state[i] !== undefined ? state[i] : (part.min || 0) }}</span>
          </label>
          <input 
            type="range" 
            :min="part.min || 0" 
            :max="part.max || 100" 
            :step="part.step || 1" 
            v-model.number="state[i]" 
            @mousedown.stop 
            @change="saveState"
            style="width: 100%; accent-color: #1A1A1A; cursor: pointer;"
          />
        </div>

        <!-- WEBHOOK -->
        <div v-if="part.type === 'action_webhook'" class="node-part-webhook">
           <div class="part-label">WEBHOOK</div>
           <input 
              v-model="state[i]" 
              :placeholder="part.url || 'https://...'" 
              @mousedown.stop 
              @change="saveState"
              class="part-input webhook-input"
           />
           <button @click="fireWebhook(i)" class="part-btn">FIRE</button>
        </div>

        <!-- LOGIC SCRIPT (HIDDEN FROM CANVAS UI) -->
        <div v-if="part.type === 'logic_script'" style="display: none;">
          <!-- Scripts are only visible in the Forge or Console Overlay -->
        </div>        <!-- PYTHON SCRIPT (HIDDEN FROM CANVAS UI) -->
        <div v-if="part.type === 'python_script'" style="display: none;">
          <!-- Python logic runs on the backend, edited in Forge -->
        </div>

        <!-- KV STORE -->
        <div v-if="part.type === 'data_store'" style="border: 2px dashed #005096; padding: 8px; background: #F4F4F0; color: #005096;">
          <div style="font-size: 10px; font-weight: bold; margin-bottom: 4px; display: flex; justify-content: space-between;">
            <span>[D] KV STORE</span>
            <span style="cursor: pointer;" @click="clearKV(i)">[CLEAR]</span>
          </div>
          <div style="font-family: 'Space Mono', monospace; font-size: 10px; white-space: pre-wrap; word-break: break-all; max-height: 100px; overflow-y: auto;">
            {{ typeof state[i] === 'object' ? JSON.stringify(state[i], null, 2) : (state[i] || '{}') }}
          </div>
        </div>

        <!-- VISUAL SUB-GRAPH -->
        <div v-if="part.type === 'visual_graph'" style="border: 2px solid #E03C31; padding: 8px; background: #FFF; color: #1A1A1A;">
          <div style="font-size: 10px; font-weight: bold; margin-bottom: 4px; color: #E03C31;">[V] SUB-GRAPH LINKS</div>
          <div style="display: flex; flex-direction: column; gap: 4px; max-height: 100px; overflow-y: auto;">
            <div v-for="conn in (props.node.connections || [])" :key="conn" style="font-size: 10px; font-family: 'Space Mono', monospace; background: #F4F4F0; padding: 2px 4px; border-left: 2px solid #E03C31;">
              -> {{ conn }}
            </div>
            <div v-if="!(props.node.connections && props.node.connections.length)" style="font-size: 10px; font-style: italic; color: #888;">No outgoing links.</div>
          </div>
        </div>

        <!-- UI RENDERER -->
        <div v-if="part.type === 'ui_render'" style="border: 2px solid #9c27b0; padding: 8px; background: #FFF; color: #1A1A1A;">
          <div style="font-size: 10px; font-weight: bold; margin-bottom: 4px; color: #9c27b0; display: flex; justify-content: space-between;">
            <span>[U] UI RENDER</span>
            <span style="cursor: pointer;" @click="forceRenderUpdate = Date.now()">[REFRESH]</span>
          </div>
          <div :key="forceRenderUpdate" v-html="renderedUI(part.code)" style="font-family: 'Space Mono', monospace; font-size: 12px; max-height: 250px; overflow-y: auto;"></div>
        </div>

        <!-- CLOCK TICKER -->
        <div v-if="part.type === 'loop_ticker'" style="border: 2px solid #FF9800; padding: 4px; background: #1A1A1A; color: #FF9800;">
          <div style="font-size: 10px; font-weight: bold; display: flex; align-items: center; justify-content: space-between;">
            <span>[L] CLOCK TICKER ({{ part.placeholder || '?' }}ms)</span>
            <div style="width: 8px; height: 8px; background: #FF9800; border-radius: 50%; animation: pulse 1s infinite;"></div>
          </div>
        </div>

        <!-- EVENT LISTENER -->
        <div v-if="part.type === 'event_listener'" style="border: 2px solid #00BCD4; padding: 4px; background: #1A1A1A; color: #00BCD4;">
          <div style="font-size: 10px; font-weight: bold; display: flex; align-items: center; justify-content: space-between;">
            <span>[E] LISTENS TO: {{ part.placeholder || 'ANY' }}</span>
            <div style="width: 8px; height: 8px; border: 2px solid #00BCD4; border-radius: 50%;"></div>
          </div>
        </div>

      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch, onMounted, onUnmounted } from 'vue'

const props = defineProps<{
  node: any
}>()

const emit = defineEmits(['update-node'])

const meta = computed(() => {
  if (typeof props.node.meta_data === 'string') {
    try { return JSON.parse(props.node.meta_data || '{}') } catch (e) { return {} }
  }
  return props.node.meta_data || {}
})

// state object to store values of inputs (indexed by part index)
const state = ref<Record<number, string>>(meta.value.state || {})
const forceRenderUpdate = ref(Date.now())

function renderedUI(code: string) {
  if (!code) return '<i style="color:#888;">No render code provided.</i>';
  try {
    const kvIndices = meta.value.blueprint?.parts
      .map((p: any, i: number) => p.type === 'data_store' ? i : -1)
      .filter((i: number) => i !== -1) || [];
      
    const kv = {
      get: (idx: number = kvIndices[0]) => {
        if (idx === undefined) return null;
        try { return JSON.parse(state.value[idx] || '{}') } catch(e) { return {} }
      }
    };
    
    // Evaluate as a function that returns an HTML string
    const fn = new Function('state', 'kv', code);
    return fn(state.value, kv);
  } catch (err: any) {
    return `<div style="color:red; font-weight:bold;">Render Error: ${err.message}</div>`;
  }
}

function saveState() {
  const newMeta = { ...meta.value, state: state.value }
  emit('update-node', props.node, newMeta)
}

let tickerInterval: any = null;

function setupTicker() {
  if (tickerInterval) clearInterval(tickerInterval);
  const parts = meta.value.blueprint?.parts || [];
  const tickerPart = parts.find((p: any) => p.type === 'loop_ticker');
  if (tickerPart && tickerPart.placeholder) {
    const ms = parseInt(tickerPart.placeholder);
    if (!isNaN(ms) && ms > 0) {
      // Find the first script part to execute
      const scriptIndex = parts.findIndex((p: any) => p.type === 'logic_script');
      if (scriptIndex !== -1) {
        tickerInterval = setInterval(() => {
          runScript(scriptIndex);
        }, ms);
      }
    }
  }
}

const handleGlobalEvent = (e: any) => {
  const parts = meta.value.blueprint?.parts || [];
  const eventPartIndex = parts.findIndex((p: any) => p.type === 'event_listener');
  if (eventPartIndex !== -1) {
    const eventPart = parts[eventPartIndex];
    if (eventPart.placeholder === e.detail.event_name || eventPart.placeholder === 'ANY' || !eventPart.placeholder) {
      // Put the payload into the event listener's state slot
      state.value[eventPartIndex] = JSON.stringify(e.detail.payload);
      saveState();
      
      // Execute the first script we find
      const scriptIndex = parts.findIndex((p: any) => p.type === 'logic_script' || p.type === 'python_script');
      if (scriptIndex !== -1) {
        if (parts[scriptIndex].type === 'python_script') {
          runPythonScript(scriptIndex);
        } else {
          runScript(scriptIndex);
        }
      }
    }
  }
};

onMounted(() => {
  setupTicker();
  window.addEventListener('aethel-global-event', handleGlobalEvent);
});

onUnmounted(() => {
  if (tickerInterval) clearInterval(tickerInterval);
  window.removeEventListener('aethel-global-event', handleGlobalEvent);
});

async function fireWebhook(partIndex: number) {
  const part = meta.value.blueprint.parts[partIndex]
  const url = state.value[partIndex] || part.url
  if (!url) {
    alert("No webhook URL provided.")
    return
  }

  // Gather payload from input_text parts
  const payload: Record<string, string> = {}
  meta.value.blueprint.parts.forEach((p: any, idx: number) => {
    if (p.type === 'input_text') {
      payload[`input_${idx}`] = state.value[idx] || ''
    }
  })

  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
    const text = await res.text()
    alert(`Webhook returned: ${res.status}\n${text}`)
  } catch (err: any) {
    alert(`Webhook error: ${err.message}`)
  }
}
async function runPythonScript(partIndex: number) {
  const code = state.value[partIndex]
  if (!code) return
  
  try {
    const res = await fetch((import.meta.env.VITE_API_BASE || '') + '/api/lgnn/execute_python', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        code,
        node_id: props.node.id,
        state: state.value
      })
    })
    const data = await res.json()
    if (data.status === 'success') {
      // Update our local state with whatever the python script mutated
      for (const [k, v] of Object.entries(data.state)) {
        state.value[Number(k)] = v as string;
      }
      saveState()
      if (data.output) alert(`Python Output:\n${data.output}`)
    } else {
      alert(`Python Error:\n${data.error}`)
    }
  } catch (err: any) {
    alert(`Failed to execute python: ${err.message}`)
  }
}

async function runScript(partIndex: number) {
  const code = state.value[partIndex]
  if (!code) return
  
  // Find KV store indices so script can read/write them
  const kvIndices = meta.value.blueprint.parts
    .map((p: any, i: number) => p.type === 'data_store' ? i : -1)
    .filter((i: number) => i !== -1)
    
  // Expose a safe KV API to the script
  const kv = {
    get: (idx: number = kvIndices[0]) => {
      if (idx === undefined) return null;
      try { return JSON.parse(state.value[idx] || '{}') } catch(e) { return {} }
    },
    set: (data: any, idx: number = kvIndices[0]) => {
      if (idx === undefined) return;
      state.value[idx] = JSON.stringify(data)
      saveState()
    }
  }

  // Expose Graph API
  const graph = {
    spawn: async (content: string, type: string = "standard", meta: any = {}) => {
      const id = 'script_' + Date.now() + Math.floor(Math.random()*1000);
      await fetch((import.meta.env.VITE_API_BASE || '') + '/api/lgnn/node', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          id, text_content: content, source_tag: "script", node_type: type, meta_data: JSON.stringify(meta)
        })
      });
      return id;
    },
    link: async (targetId: string, weight: number = 1.0) => {
      await fetch((import.meta.env.VITE_API_BASE || '') + '/api/lgnn/edge', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          source: props.node.id, target: targetId, weight
        })
      });
    },
    emit: async (eventName: string, payload: any = {}) => {
      await fetch((import.meta.env.VITE_API_BASE || '') + '/api/lgnn/emit_event', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ event_name: eventName, payload })
      });
    },
    getIncomingNodes: async () => {
      const res = await fetch((import.meta.env.VITE_API_BASE || '') + '/api/lgnn/graph');
      const data = await res.json();
      const incomingLinks = data.links.filter((l: any) => l.target === props.node.id);
      return incomingLinks.map((l: any) => data.nodes.find((n: any) => n.id === l.source)).filter(Boolean);
    }
  }

  try {
    const cleanCode = code.replace(/^```javascript\n?/g, '').replace(/^```js\n?/g, '').replace(/^```\n?/g, '').replace(/```$/g, '');
    const AsyncFunction = Object.getPrototypeOf(async function(){}).constructor;
    const fn = new AsyncFunction('state', 'node', 'kv', 'graph', 'alert', cleanCode)
    await fn(state.value, props.node, kv, graph, alert)
    saveState()
  } catch (err: any) {
    alert(`Script Error: ${err.message}`)
  }
}

function clearKV(partIndex: number) {
  state.value[partIndex] = '{}'
  saveState()
}
</script>

<style scoped>
.custom-node-card {
  padding: 16px; 
  background: var(--color-bg-card); 
  color: var(--color-text-main); 
  border: 1px solid var(--border-color); 
  border-radius: 12px;
  box-shadow: var(--shadow-md); 
  display: flex; 
  flex-direction: column; 
  min-width: 220px;
  backdrop-filter: blur(10px);
}

.node-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 700; 
  font-size: 14px; 
  border-bottom: 1px solid var(--border-color); 
  padding-bottom: 12px; 
  margin-bottom: 12px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.icon {
  font-family: 'Space Mono', monospace;
  opacity: 0.8;
}

.part-label {
  font-size: 10px; 
  font-weight: 600; 
  margin-bottom: 4px;
  color: var(--color-text-muted);
  letter-spacing: 0.5px;
}

.part-input {
  background: rgba(0,0,0,0.2); 
  border: 1px solid var(--border-color); 
  color: var(--color-text-main);
  padding: 6px 8px; 
  font-family: 'Inter', sans-serif; 
  font-size: 12px; 
  outline: none; 
  width: 100%; 
  box-sizing: border-box;
  border-radius: 4px;
  transition: all 0.2s;
}

.part-input:focus {
  border-color: var(--color-accent);
}

.part-btn {
  width: 100%; 
  background: var(--color-bg-elevated); 
  color: var(--color-text-main); 
  border: 1px solid var(--border-color); 
  font-weight: 600; 
  cursor: pointer; 
  padding: 8px;
  border-radius: 4px;
  transition: all 0.2s;
}

.part-btn:hover {
  background: var(--color-accent);
  color: #000;
  border-color: var(--color-accent);
}

.webhook-input {
  font-family: 'Space Mono', monospace; 
  font-size: 10px; 
  margin-bottom: 8px;
}

.node-part-webhook {
  border: 1px solid var(--border-color); 
  padding: 12px; 
  background: rgba(0,0,0,0.1);
  border-radius: 8px;
}
</style>
