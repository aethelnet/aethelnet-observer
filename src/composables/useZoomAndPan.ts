import { ref, watch, Ref } from 'vue'
import * as d3 from 'd3'

export function useZoomAndPan(
  canvasContainer: Ref<HTMLElement | null>,
  isSpacePressed: Ref<boolean>,
  updateProjection: () => void
) {
  const globalTransform = ref({ x: 0, y: 0, k: 1 })
  const d3ZoomInstance = ref<any>(null)

  function setupZoomAndPan() {
    if (!canvasContainer.value) return

    const svg = d3.select(canvasContainer.value)
    const zoomBehavior = d3.zoom<HTMLDivElement, unknown>()
      .scaleExtent([0.1, 4])
      .filter((e) => {
        // Don't pan on shift+drag (used for box select)
        if (e.type === 'mousedown' && e.shiftKey) return false
        // Only pan if Spacebar is pressed, OR if the event target is the background
        if (e.type === 'mousedown' && !isSpacePressed.value) {
          if (e.target && e.target.closest) {
             if (e.target.closest('.concept-node') || 
                 e.target.closest('.app-window-overlay') || 
                 e.target.closest('.toolbox') ||
                 e.target.closest('.floating-action-bar') ||
                 e.target.closest('.timeline-hud') ||
                 e.target.closest('.galaxy-view')) {
               return false
             }
          }
        }
        return true
      })
      .on("zoom", (e) => {
        globalTransform.value = e.transform
        localStorage.setItem('aethelnet_canvas_transform', JSON.stringify({ x: e.transform.x, y: e.transform.y, k: e.transform.k }))
        updateProjection()
      })
    
    // Always bind the zoom behavior first
    svg.call(zoomBehavior as any)
    d3ZoomInstance.value = zoomBehavior

    // Load saved transform
    const savedTransform = localStorage.getItem('aethelnet_canvas_transform')
    if (savedTransform) {
      try {
        const { x, y, k } = JSON.parse(savedTransform)
        svg.call(d3ZoomInstance.value.transform as any, d3.zoomIdentity.translate(x, y).scale(k))
      } catch(e) {}
    }
    
    svg.on("dblclick.zoom", null)
  }

  function resetZoom() {
    if (!canvasContainer.value || !d3ZoomInstance.value) return
    const svg = d3.select(canvasContainer.value)
    svg.transition().duration(500).call(d3ZoomInstance.value.transform, d3.zoomIdentity)
  }

  function zoomToNode(nodeX: number, nodeY: number) {
    if (!canvasContainer.value || !d3ZoomInstance.value) return
    const svg = d3.select(canvasContainer.value)
    
    // Calculate translate to center node
    const k = globalTransform.value.k
    const tx = (window.innerWidth / 2) - (nodeX * k)
    const ty = (window.innerHeight / 2) - (nodeY * k)
    
    svg.transition().duration(500).call(
      d3ZoomInstance.value.transform, 
      d3.zoomIdentity.translate(tx, ty).scale(k)
    )
  }

  return {
    globalTransform,
    d3ZoomInstance,
    setupZoomAndPan,
    resetZoom,
    zoomToNode
  }
}
