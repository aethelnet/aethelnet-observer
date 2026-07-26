import * as d3 from 'd3'
let simulation: any = null
let workerNodes: any[] = []

self.onmessage = (event) => {
  const { type, payload } = event.data

  if (type === 'INIT' || type === 'UPDATE') {
    const { nodes, links } = payload
    workerNodes = nodes

    if (!simulation) {
      simulation = d3.forceSimulation(nodes)
        .alphaDecay(0.0228)
        // Keep nodes spread apart
        .force("charge", d3.forceManyBody().strength(-2000).distanceMax(2000))
        // Prevent overlapping with a solid radius
        .force("collide", d3.forceCollide().radius(180).iterations(2))
        // Pull connected nodes together
        .force("link", d3.forceLink(links).id((d: any) => d.id).distance(400))
        // Gentle pull to center to prevent drifting to infinity
        .force("center", d3.forceCenter(0, 0))
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
      if (!simulation) return;
      const { id, fx, fy } = payload
      const node = simulation.nodes().find((n: any) => n.id === id)
      if (node) {
          node.fx = fx
          node.fy = fy
          simulation.alpha(0.3).restart()
      }
  }
}
