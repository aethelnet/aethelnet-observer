<template>
  <div class="workbench-view">
    <div class="workbench-header">
      <span class="title">THE FORGE [ NODE BUILDER ]</span>
      <button @click="$emit('close')" class="close-btn">X</button>
    </div>
    
    <div class="workbench-layout">
      <!-- Primitive Palette (Left) -->
      <div class="palette-panel">
        <div class="panel-title">PRIMITIVES</div>
        <div class="primitive-list">
          <div class="primitive-item" draggable="true" @dragstart="onDragStart($event, 'input_text')" @click="addPart('input_text')">[T] TEXT INPUT</div>
          <div class="primitive-item" draggable="true" @dragstart="onDragStart($event, 'logic_script')" @click="addPart('logic_script')">[S] JS SCRIPT</div>
          <div class="primitive-item" draggable="true" @dragstart="onDragStart($event, 'python_script')" @click="addPart('python_script')">[P] PYTHON SCRIPT</div>
          <div class="primitive-item" draggable="true" @dragstart="onDragStart($event, 'action_webhook')" @click="addPart('action_webhook')">[A] WEBHOOK</div>
          <div class="primitive-item" draggable="true" @dragstart="onDragStart($event, 'ui_render')" @click="addPart('ui_render')">[U] UI RENDERER</div>
          <div class="primitive-item" draggable="true" @dragstart="onDragStart($event, 'loop_ticker')" @click="addPart('loop_ticker')">[L] CLOCK TICKER</div>
          <div class="primitive-item" draggable="true" @dragstart="onDragStart($event, 'event_listener')" @click="addPart('event_listener')">[E] EVENT LISTENER</div>
          <div class="primitive-item" draggable="true" @dragstart="onDragStart($event, 'visual_graph')" @click="addPart('visual_graph')">[V] SUB-GRAPH</div>
          <div class="primitive-item" draggable="true" @dragstart="onDragStart($event, 'data_store')" @click="addPart('data_store')">[D] KV STORE</div>
        </div>
      </div>

      <!-- Assembly Canvas (Center) -->
      <div class="assembly-canvas" @dragover.prevent @drop="onDrop">
        <div class="canvas-grid">
          <!-- The visual representation of the new custom node being built -->
          <div class="custom-node-preview" :style="{ borderColor: customColor }">
            <div class="node-header" :style="{ background: customColor }">
              <input v-model="customName" placeholder="APP:MyCustomNode" class="name-input" />
            </div>
            <div class="node-body">
              <div v-if="assembledParts.length === 0" class="empty-hint">
                Drag primitives here to build your node...
              </div>
              
              <div v-for="(part, index) in assembledParts" :key="index" class="assembled-part">
                <div class="part-header">
                  <span>{{ part.type }}</span>
                  <button @click="removePart(index)" class="remove-btn">x</button>
                </div>
                <div class="part-config">
                  <input v-if="part.type === 'input_text'" v-model="part.placeholder" placeholder="Placeholder..." class="config-input" />
                  <input v-if="part.type === 'action_webhook'" v-model="part.url" placeholder="Default URL..." class="config-input" />
                  <textarea v-if="part.type === 'logic_script'" v-model="part.code" placeholder="return input;" class="config-input" rows="2"></textarea>
                  <textarea v-if="part.type === 'python_script'" v-model="part.code" placeholder="# Python Code" class="config-input" rows="2"></textarea>
                  <textarea v-if="part.type === 'ui_render'" v-model="part.code" placeholder="return `<div>${state[0]}</div>`" class="config-input" rows="2"></textarea>
                  <input v-if="part.type === 'loop_ticker'" v-model="part.placeholder" placeholder="Interval in ms (e.g. 1000)" class="config-input" />
                  <input v-if="part.type === 'event_listener'" v-model="part.placeholder" placeholder="Event name (e.g. PLAYER_MOVED)" class="config-input" />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Properties Inspector (Right) -->
      <div class="properties-panel">
        <div class="panel-title">PROPERTIES</div>
        
        <div class="property-group" v-if="savedBlueprints.length > 0" style="margin-bottom: 16px;">
          <label>LOAD EXISTING</label>
          <select @change="loadBlueprint(($event.target as HTMLSelectElement).value)" class="prop-select" style="background: #EAEAEA;">
            <option value="" disabled selected>Select Blueprint...</option>
            <option v-for="name in savedBlueprints" :key="name" :value="name">{{ name }}</option>
          </select>
        </div>

        <div class="property-group">
          <label>THEME COLOR</label>
          <div class="color-picker">
            <button v-for="color in ['#1A1A1A', '#E03C31', '#00FF41', '#FF9800', '#00bcd4', '#9c27b0', '#F2C12E']" 
                    :key="color"
                    class="color-swatch"
                    :class="{ active: customColor === color }"
                    :style="{ background: color }"
                    @click="customColor = color">
            </button>
          </div>
        </div>
        
        <div class="property-group mt-4">
          <label>OUTPUT BEHAVIOR</label>
          <select v-model="outputType" class="prop-select">
            <option value="passthrough">Passthrough (Forward Input)</option>
            <option value="transform">Transform (Script Result)</option>
            <option value="event">Event Trigger Only</option>
          </select>
        </div>

        <button @click="saveCustomNode" class="save-node-btn mt-4">SAVE BLUEPRINT</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, defineEmits, onMounted } from 'vue'

const emit = defineEmits(['close', 'save'])

const customName = ref('APP:Untitled')
const customColor = ref('#1A1A1A')
const outputType = ref('passthrough')
const savedBlueprints = ref<string[]>([])

interface AssembledPart {
  type: string;
  placeholder?: string;
  url?: string;
  code?: string;
}

const assembledParts = ref<AssembledPart[]>([])

onMounted(() => {
  const saved = localStorage.getItem('aethelnet_custom_blueprints')
  if (saved) {
    const bps = JSON.parse(saved)
    savedBlueprints.value = Object.keys(bps)
  }
})

function loadBlueprint(name: string) {
  const saved = localStorage.getItem('aethelnet_custom_blueprints')
  if (saved) {
    const bps = JSON.parse(saved)
    const bp = bps[name]
    if (bp) {
      customName.value = bp.name
      customColor.value = bp.color || '#1A1A1A'
      outputType.value = bp.outputType || 'passthrough'
      assembledParts.value = JSON.parse(JSON.stringify(bp.parts || []))
    }
  }
}

function onDragStart(event: DragEvent, type: string) {
  if (event.dataTransfer) {
    event.dataTransfer.setData('text/plain', type)
  }
}

function onDrop(event: DragEvent) {
  const type = event.dataTransfer?.getData('text/plain')
  if (type) {
    addPart(type)
  }
}

function addPart(type: string) {
  assembledParts.value.push({ type })
}

function removePart(index: number) {
  assembledParts.value.splice(index, 1)
}

function saveCustomNode() {
  const blueprint = {
    id: 'bp_' + Date.now() + '_' + Math.floor(Math.random() * 1000),
    name: customName.value,
    color: customColor.value,
    outputType: outputType.value,
    parts: assembledParts.value
  }
  // In the future, send this to backend or localStorage
  alert("Blueprint saved: " + customName.value)
  emit('save', blueprint)
}
</script>

<style scoped>
.workbench-view {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 900px;
  height: 600px;
  background: #F4F4F0;
  border: 4px solid #1A1A1A;
  box-shadow: 8px 8px 0px #1A1A1A;
  display: flex;
  flex-direction: column;
  z-index: 1000;
  font-family: 'Space Mono', monospace;
}

.workbench-header {
  background: #1A1A1A;
  color: #FFF;
  padding: 8px 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 900;
  font-size: 14px;
}

.close-btn {
  background: transparent;
  color: #FFF;
  border: none;
  font-weight: 900;
  cursor: pointer;
}

.workbench-layout {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.palette-panel, .properties-panel {
  width: 250px;
  background: #FFF;
  border-right: 2px solid #1A1A1A;
  padding: 16px;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
}

.properties-panel {
  border-right: none;
  border-left: 2px solid #1A1A1A;
}

.panel-title {
  font-weight: 900;
  font-size: 12px;
  margin-bottom: 16px;
  color: #1A1A1A;
  border-bottom: 2px solid #1A1A1A;
  padding-bottom: 4px;
}

.primitive-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.primitive-item {
  border: 2px solid #1A1A1A;
  padding: 8px;
  background: #F4F4F0;
  font-size: 12px;
  font-weight: bold;
  cursor: grab;
  box-shadow: 2px 2px 0px #1A1A1A;
}

.primitive-item:active {
  cursor: grabbing;
}

.assembly-canvas {
  flex: 1;
  background: #EAEAEA;
  background-image: radial-gradient(#CCC 1px, transparent 1px);
  background-size: 20px 20px;
  display: flex;
  justify-content: center;
  align-items: center;
  overflow: auto;
}

.custom-node-preview {
  width: 250px;
  min-height: 150px;
  background: #FFF;
  border: 3px solid;
  display: flex;
  flex-direction: column;
  box-shadow: 4px 4px 0px rgba(0,0,0,0.2);
}

.node-header {
  padding: 8px;
}

.name-input {
  width: 100%;
  background: transparent;
  border: none;
  color: #FFF;
  font-family: 'Space Mono', monospace;
  font-weight: 900;
  font-size: 14px;
  outline: none;
}

.name-input::placeholder {
  color: rgba(255,255,255,0.7);
}

.node-body {
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  flex: 1;
}

.empty-hint {
  text-align: center;
  color: #999;
  font-size: 10px;
  font-style: italic;
  margin: auto 0;
}

.assembled-part {
  border: 2px solid #1A1A1A;
  background: #F4F4F0;
  padding: 4px;
}

.part-header {
  display: flex;
  justify-content: space-between;
  font-size: 10px;
  font-weight: bold;
  margin-bottom: 4px;
}

.remove-btn {
  background: transparent;
  border: none;
  color: #E03C31;
  font-weight: bold;
  cursor: pointer;
}

.config-input {
  width: 100%;
  box-sizing: border-box;
  font-size: 10px;
  font-family: inherit;
  border: 1px solid #CCC;
  padding: 2px 4px;
}

.property-group label {
  display: block;
  font-size: 10px;
  font-weight: bold;
  margin-bottom: 4px;
}

.color-picker {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.color-swatch {
  width: 24px;
  height: 24px;
  border: 2px solid transparent;
  cursor: pointer;
  padding: 0;
}

.color-swatch.active {
  border-color: #000;
  transform: scale(1.1);
}

.prop-select {
  width: 100%;
  font-family: inherit;
  font-size: 12px;
  padding: 4px;
  border: 2px solid #1A1A1A;
}

.save-node-btn {
  background: #1A1A1A;
  color: #FFF;
  border: none;
  padding: 12px;
  font-weight: 900;
  cursor: pointer;
  font-family: inherit;
  margin-top: auto;
}

.save-node-btn:hover {
  background: #E03C31;
}

.mt-4 { margin-top: 16px; }
</style>
