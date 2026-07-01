import * as d3 from 'd3'
import { forceLennardJones, forceEntanglement, forceHawkingRadiation } from '../utils/quantumPhysics'

let simulation: any = null
let workerNodes: any[] = []

const forceCluster = (alpha: number) => {
  const nodeMap = new Map(workerNodes.map(n => [n.id, n]))
  for (const node of workerNodes) {
    if (node.parent_id && node.parent_id !== 'root') {
      const parentNode = nodeMap.get(node.parent_id)
      if (parentNode) {
        const dx = (parentNode.x || 0) - (node.x || 0)
        const dy = (parentNode.y || 0) - (node.y || 0)
        const dist = Math.sqrt(dx * dx + dy * dy)
        if (dist > 150) {
          node.vx = (node.vx || 0) + dx * alpha * 0.5
          node.vy = (node.vy || 0) + dy * alpha * 0.5
        }
      }
    }
  }
}

const forceGravityWells = (alpha: number) => {
  const gravityWells = workerNodes.filter(n => n.node_type === 'gravity_well' || (n.meta_data && n.meta_data.is_anomaly))
  if (gravityWells.length === 0) return
  
  for (const well of gravityWells) {
    const strength = well.meta_data?.gravity_strength || 0.5
    for (const node of workerNodes) {
      if (node.id === well.id) continue
      const dx = (well.x || 0) - (node.x || 0)
      const dy = (well.y || 0) - (node.y || 0)
      const dist = Math.sqrt(dx * dx + dy * dy)
      if (dist > 10 && dist < 800) {
        const pull = (strength * 1000) / (dist * dist)
        node.vx = (node.vx || 0) + (dx / dist) * pull * alpha
        node.vy = (node.vy || 0) + (dy / dist) * pull * alpha
      }
    }
  }
}

self.onmessage = (event) => {
  const { type, payload } = event.data

  if (type === 'INIT' || type === 'UPDATE') {
    const { nodes, links, engineSettings, linkDistance } = payload
    workerNodes = nodes

    if (!simulation) {
      simulation = d3.forceSimulation(nodes)
        .alphaDecay(engineSettings?.physicsDecay || 0.0228)
        .force("charge", d3.forceManyBody().strength(-100).theta(1.5))
        .force("quantum_lj", forceLennardJones())
        .force("quantum_entanglement", forceEntanglement())
        .force("hawking_radiation", forceHawkingRadiation())
        .force("cluster", forceCluster)
        .force("gravity_wells", forceGravityWells)
        .force("link", d3.forceLink(links).id((d: any) => d.id).distance(linkDistance || 150))
        .on("tick", () => {
          // Send simplified payload back to main thread
          const positions = workerNodes.map((n: any) => ({
            id: n.id,
            x: n.x,
            y: n.y,
            vx: n.vx,
            vy: n.vy
          }))
          self.postMessage({ type: 'TICK', payload: positions })
        })
    } else {
      simulation.nodes(nodes)
      simulation.force("link").links(links)
      simulation.alpha(0.3).restart()
    }
  } else if (type === 'DREAM') {
      if (simulation) {
          simulation.alpha(1).restart()
      }
  } else if (type === 'STOP') {
      if (simulation) {
          simulation.stop()
      }
  } else if (type === 'DRAG') {
      const { id, fx, fy } = payload
      const node = simulation.nodes().find((n: any) => n.id === id)
      if (node) {
          node.fx = fx
          node.fy = fy
          simulation.alpha(0.3).restart()
      }
  }
}
