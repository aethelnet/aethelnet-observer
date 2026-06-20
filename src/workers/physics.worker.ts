import * as d3 from 'd3'

let simulation: any = null

self.onmessage = (event) => {
  const { type, payload } = event.data

  if (type === 'INIT' || type === 'UPDATE') {
    const { nodes, links } = payload

    if (!simulation) {
      simulation = d3.forceSimulation(nodes)
        .force("charge", d3.forceManyBody().strength(-300))
        .force("link", d3.forceLink(links).id((d: any) => d.id).distance(150))
        .force("collide", d3.forceCollide().radius(45))
        .on("tick", () => {
          // Send simplified payload back to main thread
          const positions = nodes.map((n: any) => ({
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
