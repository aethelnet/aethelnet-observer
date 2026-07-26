import { ref, Ref, shallowRef } from 'vue'
import * as d3 from 'd3'
import { engineSettings } from '../utils/engineSettings'

export interface D3GraphState {
  nodes: Ref<any[]>
  links: Ref<any[]>
  globalTransform: Ref<{ x: number, y: number, k: number }>
  d3ZoomInstance: Ref<any>
}

export function useD3Graph(canvasContainerRef: Ref<HTMLElement | null>) {
  const globalTransform = ref({ x: 0, y: 0, k: 1 })
  const d3ZoomInstance = ref<any>(null)
  const isSpacePressed = ref(false)

  // Zoom Behavior
  function setupZoomAndPan(onZoomUpdate: (transform: { x: number, y: number, k: number }) => void) {
    if (!canvasContainerRef.value) return

    const svg = d3.select(canvasContainerRef.value)
    const zoomBehavior = d3.zoom<HTMLDivElement, unknown>()
      .scaleExtent([0.1, 4])
      .filter((e: any) => {
        if (e.type === 'mousedown' && e.shiftKey) return false
        if (e.type === 'mousedown' && !isSpacePressed.value) {
          if (e.target && e.target.closest) {
             if (e.target.closest('.concept-node') || 
                 e.target.closest('.app-window-overlay') || 
                 e.target.closest('.toolbox') ||
                 e.target.closest('.floating-action-bar')) {
               return false
             }
          }
        }
        return true
      })
      .on("zoom", (e) => {
        globalTransform.value = e.transform
        localStorage.setItem('aethelnet_canvas_transform', JSON.stringify({ x: e.transform.x, y: e.transform.y, k: e.transform.k }))
        onZoomUpdate(e.transform)
      })
    
    svg.call(zoomBehavior as any)
    d3ZoomInstance.value = zoomBehavior

    const savedTransform = localStorage.getItem('aethelnet_canvas_transform')
    if (savedTransform) {
      try {
        const { x, y, k } = JSON.parse(savedTransform)
        svg.call(d3ZoomInstance.value.transform as any, d3.zoomIdentity.translate(x, y).scale(k))
      } catch(e) {}
    }
    
    svg.on("dblclick.zoom", null)
  }

  function handleKeyDown(e: KeyboardEvent) {
    if (e.code === 'Space') {
      isSpacePressed.value = true
    }
  }

  function handleKeyUp(e: KeyboardEvent) {
    if (e.code === 'Space') {
      isSpacePressed.value = false
    }
  }

  return {
    globalTransform,
    d3ZoomInstance,
    isSpacePressed,
    setupZoomAndPan,
    handleKeyDown,
    handleKeyUp
  }
}
