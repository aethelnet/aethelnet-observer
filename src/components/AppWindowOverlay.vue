<template>
  <div class="app-window-overlay" @mousedown.stop @touchstart.stop>
    <div class="app-window" :style="{ borderColor: themeColor, boxShadow: `0 0 20px ${themeColor}40` }">
      <!-- WINDOW HEADER -->
      <div class="app-header" :style="{ background: themeColor }">
        <div class="header-left">
          <span class="app-icon">{{ meta.icon || '◈' }}</span>
          <span class="app-title" style="color: #000;">{{ meta.name || 'Custom App' }}</span>
        </div>
        <div class="header-right">
          <button class="ctrl-btn close" @click="$emit('close')">[ X ]</button>
        </div>
      </div>

      <!-- WINDOW BODY (IFRAME) -->
      <div class="app-body">
        <iframe 
          class="app-frame" 
          sandbox="allow-scripts allow-same-origin allow-forms allow-popups" 
          :srcdoc="srcdocContent"
        ></iframe>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  node: any
}>()

const emit = defineEmits(['close'])

const meta = computed(() => {
  if (typeof props.node.meta_data === 'string') {
    try { return JSON.parse(props.node.meta_data) } catch (e) { return {} }
  }
  return props.node.meta_data || {}
})

const themeColor = computed(() => meta.value.color || '#00FF41')

const srcdocContent = computed(() => {
  const uiTemplate = meta.value.ui_template || ''
  
  // Provide basic styling and some default Aethelnet context variables via JS
  return `
    <!DOCTYPE html>
    <html>
      <head>
        <meta charset="utf-8">
        <style>
          /* Aethelnet Default CSS Theme Injection */
          :root {
            --theme-color: ${themeColor.value};
            --bg-main: #0A0A0A;
            --bg-panel: rgba(255, 255, 255, 0.03);
            --text-main: #EEEEEE;
            --text-muted: #888888;
            --border-color: rgba(255, 255, 255, 0.1);
          }
          body {
            margin: 0;
            padding: 20px;
            background: var(--bg-main);
            color: var(--text-main);
            font-family: 'Space Mono', monospace, sans-serif;
            overflow-x: hidden;
          }
          * { box-sizing: border-box; }
          
          /* Typography */
          h1, h2, h3, h4, h5, h6 { color: var(--theme-color); margin-top: 0; text-transform: uppercase; letter-spacing: 1px; }
          a { color: var(--theme-color); text-decoration: none; }
          a:hover { text-decoration: underline; }
          
          /* Common Components */
          .container { max-width: 1200px; margin: 0 auto; }
          .card { 
            background: var(--bg-panel); 
            border: 1px solid var(--border-color); 
            padding: 16px; 
            border-radius: 4px;
            margin-bottom: 16px;
          }
          
          /* Forms & Buttons */
          button, .btn {
            background: transparent;
            color: var(--theme-color);
            border: 1px solid var(--theme-color);
            padding: 8px 16px;
            font-family: 'Space Mono', monospace;
            font-weight: bold;
            cursor: pointer;
            text-transform: uppercase;
            border-radius: 4px;
            transition: all 0.2s;
          }
          button:hover, .btn:hover {
            background: var(--theme-color);
            color: #000;
          }
          input, textarea, select {
            background: rgba(0,0,0,0.5);
            border: 1px solid var(--border-color);
            color: var(--text-main);
            padding: 8px;
            font-family: 'Space Mono', monospace;
            border-radius: 4px;
            width: 100%;
            margin-bottom: 8px;
            outline: none;
          }
          input:focus, textarea:focus { border-color: var(--theme-color); }
          
          /* Scrollbars */
          ::-webkit-scrollbar { width: 8px; height: 8px; }
          ::-webkit-scrollbar-track { background: var(--bg-main); }
          ::-webkit-scrollbar-thumb { background: #333; border-radius: 4px; }
          ::-webkit-scrollbar-thumb:hover { background: #555; }
        </style>
        <script>
          // Basic Aethelnet API for the iframe
          window.Aethelnet = {
            nodeId: "${props.node.id}",
            sendMessage: function(msg) {
              console.log("[Aethelnet App Message]", msg);
              // Future: window.parent.postMessage({ type: 'AETHEL_MSG', data: msg }, '*');
            }
          };
        </scr` + `ipt>
      </head>
      <body>
        ${uiTemplate}
      </body>
    </html>
  `
})
</script>

<style scoped>
.app-window-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(10px);
  z-index: 10000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}

.app-window {
  width: 100%;
  max-width: 1200px;
  height: 100%;
  max-height: 800px;
  background: #0A0A0A;
  border: 2px solid #00FF41;
  display: flex;
  flex-direction: column;
  border-radius: 8px;
  overflow: hidden;
}

.app-header {
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  background: #00FF41;
  user-select: none;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.app-icon {
  font-size: 16px;
  color: #000;
}

.app-title {
  font-family: 'Space Mono', monospace;
  font-weight: bold;
  font-size: 14px;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.header-right {
  display: flex;
  align-items: center;
}

.ctrl-btn {
  background: transparent;
  border: none;
  color: #000;
  font-family: 'Space Mono', monospace;
  font-size: 14px;
  font-weight: bold;
  cursor: pointer;
}

.ctrl-btn:hover {
  color: #FFF;
}

.app-body {
  flex: 1;
  background: #111;
  position: relative;
}

.app-frame {
  width: 100%;
  height: 100%;
  border: none;
  display: block;
}
</style>
