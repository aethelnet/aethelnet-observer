import { Ref } from 'vue'

export function useLgnnPhysics(
  nodes: Ref<any[]>,
  updateProjection: () => void,
  constrainToBounds: (node: any) => void
) {
  let physicsWorker: Worker | null = null

  function initPhysicsWorker() {
    if (!physicsWorker) {
      physicsWorker = new Worker(new URL('../workers/physics.worker.ts', import.meta.url), { type: 'module' })
      physicsWorker.onmessage = (e) => {
        if (e.data.type === 'TICK') {
          const positions = e.data.payload
          const nodeMap = new Map(nodes.value.map(n => [n.id, n]))
          for (const p of positions) {
            const node = nodeMap.get(p.id)
            if (node && !node.isDragged) { // don't override dragged position
              node.x = p.x
              node.y = p.y
              node.vx = p.vx
              node.vy = p.vy
            }
          }
          nodes.value.forEach(constrainToBounds)
          updateProjection()
        }
      }
    }
    return physicsWorker
  }

  // Setup the mock simulation proxy to intercept all legacy d3 calls
  const simulationMock = {
    alpha: (v: number) => {
      if (v > 0) physicsWorker?.postMessage({ type: 'DREAM' })
      return simulationMock
    },
    alphaTarget: (v: number) => {
      if (v > 0) physicsWorker?.postMessage({ type: 'DREAM' })
      else physicsWorker?.postMessage({ type: 'STOP' })
      return simulationMock
    },
    restart: () => {
      physicsWorker?.postMessage({ type: 'DREAM' })
      return simulationMock
    },
    stop: () => {
      physicsWorker?.postMessage({ type: 'STOP' })
      return simulationMock
    },
    nodes: (n: any) => simulationMock,
    force: (name: string, f?: any) => {
      if (f === undefined) return { links: () => {} }
      return simulationMock
    },
    alphaDecay: (v: number) => simulationMock,
    on: (event: string, cb: any) => simulationMock
  }

  function updatePhysicsData(links: any[], engineSettings: any, linkDistance: any) {
    if (!physicsWorker) return

    const d3Links = links.map(l => ({ 
      source: (l.source as any).id ?? l.source, 
      target: (l.target as any).id ?? l.target, 
      weight: l.weight 
    }))

    physicsWorker.postMessage({
      type: 'UPDATE',
      payload: {
        nodes: JSON.parse(JSON.stringify(nodes.value)), // strip reactivity
        links: d3Links,
        engineSettings,
        linkDistance
      }
    })
  }

  function setPhysicsState(state: 'DREAM' | 'STOP') {
    physicsWorker?.postMessage({ type: state })
  }

  function getWorker() {
    return physicsWorker
  }

  return {
    initPhysicsWorker,
    simulation: simulationMock,
    updatePhysicsData,
    setPhysicsState,
    getWorker
  }
}
