import * as d3 from 'd3'

/**
 * Aethelnet Quantum & Theoretical Physics Forces
 * "Spooky action at a distance and molecular dynamics for cognitive nodes."
 */

// 1. LENNARD-JONES POTENTIAL (Intermolecular Forces)
// Replaces standard d3.forceCollide and d3.forceManyBody with a mathematically accurate 
// Lennard-Jones interaction: V(r) = 4ε [ (σ/r)^12 - (σ/r)^6 ]
// Extremely strong repulsion at short distances, mild attraction at medium distances.
export function forceLennardJones() {
  let nodes: any[]
  
  function force(alpha: number) {
    const epsilon = 0.5 // Depth of the potential well
    const sigma = 50.0  // Distance at which intermolecular potential is zero
    
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const nodeA = nodes[i]
        const nodeB = nodes[j]
        
        const dx = (nodeB.x || 0) - (nodeA.x || 0)
        const dy = (nodeB.y || 0) - (nodeA.y || 0)
        const r2 = dx * dx + dy * dy
        const r = Math.sqrt(r2)
        
        // Prevent mathematical explosions if nodes are exactly on top of each other
        if (r === 0) {
          nodeA.vx = (nodeA.vx || 0) + (Math.random() - 0.5) * 10
          nodeA.vy = (nodeA.vy || 0) + (Math.random() - 0.5) * 10
          continue
        }
        if (r > sigma * 3) continue // Optimization cutoff
        
        // Clamp minimum radius to prevent force from shooting to infinity
        const safeR = Math.max(r, 10.0) 
        
        const sr = sigma / safeR
        const sr6 = Math.pow(sr, 6)
        const sr12 = sr6 * sr6
        
        // Derivative of LJ potential gives the force magnitude
        // F(r) = 24ε/r * [ 2(σ/r)^12 - (σ/r)^6 ]
        let forceMag = (24 * epsilon / safeR) * (2 * sr12 - sr6)
        
        // Clamp force magnitude to a safe maximum so velocities don't explode to NaN
        forceMag = Math.max(-500, Math.min(500, forceMag))
        
        // Apply force
        const fx = (dx / r) * forceMag * alpha
        const fy = (dy / r) * forceMag * alpha
        
        nodeA.vx -= fx
        nodeA.vy -= fy
        nodeB.vx += fx
        nodeB.vy += fy
      }
    }
  }
  
  force.initialize = function(_nodes: any[]) {
    nodes = _nodes
  }
  
  return force
}

// 2. QUANTUM ENTANGLEMENT (Spooky Action at a Distance)
// Nodes that share the same entanglement_id will mirror their momentum states instantaneously
// regardless of the distance between them.
export function forceEntanglement() {
  let nodes: any[]
  
  function force(alpha: number) {
    // Group nodes by entanglement signature
    const entangledGroups = new Map<string, any[]>()
    
    for (const node of nodes) {
      const eId = node.meta_data?.entanglement_id
      if (eId) {
        if (!entangledGroups.has(eId)) entangledGroups.set(eId, [])
        entangledGroups.get(eId)!.push(node)
      }
    }
    
    // Wave-function collapse / momentum mirroring
    for (const group of entangledGroups.values()) {
      if (group.length < 2) continue
      
      // Calculate average momentum of the entangled pair/group
      let avgVx = 0
      let avgVy = 0
      for (const node of group) {
        avgVx += node.vx || 0
        avgVy += node.vy || 0
      }
      avgVx /= group.length
      avgVy /= group.length
      
      // Instantly apply the shared momentum state to all entangled particles
      for (const node of group) {
        // Blending current velocity with the entangled state
        node.vx = (node.vx || 0) * (1 - alpha) + avgVx * alpha
        node.vy = (node.vy || 0) * (1 - alpha) + avgVy * alpha
      }
    }
  }
  
  force.initialize = function(_nodes: any[]) {
    nodes = _nodes
  }
  
  return force
}

// 3. HAWKING RADIATION FOR GRAVITY WELLS
// Black holes (Gravity Anomalies) emit tiny amounts of thermal radiation (jitter)
// near their event horizons, causing them to slowly lose mass over time.
export function forceHawkingRadiation() {
  let nodes: any[]
  
  function force(alpha: number) {
    for (const node of nodes) {
      if (node.node_type === 'gravity_well' || (node.meta_data && node.meta_data.is_anomaly)) {
        // Emit jitter based on current strength
        const strength = node.meta_data.gravity_strength || 1.0
        
        // Hawking jitter: inversely proportional to mass (smaller black holes radiate hotter/faster)
        const jitter = (1.0 / Math.max(strength, 0.1)) * alpha * 2.0
        
        node.vx = (node.vx || 0) + (Math.random() - 0.5) * jitter
        node.vy = (node.vy || 0) + (Math.random() - 0.5) * jitter
        
        // Slowly evaporate mass
        if (Math.random() < 0.05 * alpha) {
          node.meta_data.gravity_strength = Math.max(0, strength - 0.001)
        }
      }
    }
  }
  
  force.initialize = function(_nodes: any[]) {
    nodes = _nodes
  }
  
  return force
}
