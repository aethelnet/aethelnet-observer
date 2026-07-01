<template>
  <canvas ref="webglCanvas" class="galaxy-view-container" :style="{ pointerEvents: isGalaxyMode ? 'auto' : 'none' }"></canvas>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { ThreeGraphRenderer } from '../utils/ThreeGraphRenderer'

const props = defineProps<{
  nodes: any[],
  links: any[],
  transform: { x: number, y: number, k: number },
  isEcoMode?: boolean,
  isGalaxyMode?: boolean
}>()

const webglCanvas = ref<HTMLCanvasElement | null>(null)
let threeRenderer: ThreeGraphRenderer | null = null

const emit = defineEmits(['node-click', 'edge-click', 'node-hover', 'edge-hover'])

onMounted(() => {
  if (webglCanvas.value) {
    threeRenderer = new ThreeGraphRenderer(webglCanvas.value, props.nodes, props.links, props.transform)
    threeRenderer.isGalaxyMode = !!props.isGalaxyMode
    threeRenderer.onClick = (node: any) => emit('node-click', node)
    threeRenderer.onClickEdge = (link: any) => emit('edge-click', link)
    
    // Add event listeners for raycasting
    webglCanvas.value.addEventListener('click', (e) => {
      if (threeRenderer && threeRenderer.isGalaxyMode) {
        threeRenderer.raycast(e.clientX, e.clientY)
      }
    })
    
    webglCanvas.value.addEventListener('mousemove', (e) => {
      if (threeRenderer && threeRenderer.isGalaxyMode) {
        const hoverResult = threeRenderer.raycastHover(e.clientX, e.clientY)
        if (hoverResult) {
          if (hoverResult.type === 'node') {
            emit('node-hover', hoverResult.data, e.clientX, e.clientY)
            emit('edge-hover', null, e.clientX, e.clientY)
          } else if (hoverResult.type === 'link') {
            emit('edge-hover', hoverResult.data, e.clientX, e.clientY)
            emit('node-hover', null, e.clientX, e.clientY)
          }
        } else {
          emit('node-hover', null, e.clientX, e.clientY)
          emit('edge-hover', null, e.clientX, e.clientY)
        }
      }
    })
  }
})

watch(() => props.nodes, (newNodes) => {
  if (threeRenderer) {
    threeRenderer.updateData(newNodes, props.links)
  }
}, { deep: false }) // Avoid deep watch on 10,000 nodes if possible, but LgnnView currently replaces arrays

watch(() => props.transform, (newTransform) => {
  if (threeRenderer) {
    threeRenderer.globalTransform = newTransform
  }
}, { deep: true })

watch(() => props.isGalaxyMode, (newVal) => {
  if (threeRenderer) {
    threeRenderer.setGalaxyMode(!!newVal)
  }
})

watch(() => props.isEcoMode, (newVal) => {
  if (threeRenderer) {
    if (newVal) {
      if (typeof threeRenderer.pause === 'function') threeRenderer.pause()
    } else {
      if (typeof threeRenderer.resume === 'function') threeRenderer.resume()
    }
  }
})

onUnmounted(() => {
  if (threeRenderer) {
    threeRenderer.dispose()
    threeRenderer = null
  }
})
</script>

<style scoped>
.galaxy-view-container {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none; /* D3 container handles mouse events in LgnnView */
  z-index: 1; /* Keep it below DOM overlays */
}
</style>
