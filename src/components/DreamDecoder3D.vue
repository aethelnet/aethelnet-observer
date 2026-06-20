<template>
  <div class="dream-decoder-3d" ref="container"></div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import * as THREE from 'three'

const props = defineProps({
  inputData: {
    type: [String, Object, Number],
    default: null
  },
  width: {
    type: Number,
    default: 200
  },
  height: {
    type: Number,
    default: 200
  }
})

import { API_BASE } from '../shared/api.js'

const container = ref<HTMLElement | null>(null)
let scene: THREE.Scene
let camera: THREE.PerspectiveCamera
let renderer: THREE.WebGLRenderer
let animationId: number
let moleculeGroup: THREE.Group

interface GraphNode {
  id: string
  activation: number
  mesh: THREE.Mesh
  vel: THREE.Vector3
}

interface GraphLink {
  sourceId: string
  targetId: string
  weight: number
  line: THREE.Line
}

const graphNodes = new Map<string, GraphNode>()
const graphLinks: GraphLink[] = []

const sphereGeo = new THREE.SphereGeometry(0.5, 16, 16)
const materialMap = new Map<number, THREE.MeshPhongMaterial>()

function getMaterial(activation: number) {
  // Map activation to a bright color. Low activation = beautiful slate-white/blue, High = pure bright cyan
  const intensity = Math.min(1.0, Math.max(0, activation / 20))
  const color = new THREE.Color().setHSL(0.55, 0.6 + intensity * 0.4, 0.7 + intensity * 0.3)
  const mat = new THREE.MeshPhongMaterial({ 
    color, 
    shininess: 150,
    emissive: color,
    emissiveIntensity: intensity * 0.8 + 0.2
  })
  return mat
}

const lineMat = new THREE.LineBasicMaterial({ color: 0x88DDFF, transparent: true, opacity: 0.5 })

async function fetchGraphData() {
  try {
    const res = await fetch(`${API_BASE || ''}/api/lgnn/graph`)
    if (res.ok) {
      const data = await res.json()
      updateGraphStructure(data.nodes || [], data.links || [])
    }
  } catch (err) {
    console.error('Failed to fetch LGNN graph', err)
  }
}

function updateGraphStructure(apiNodes: any[], apiLinks: any[]) {
  const currentIds = new Set<string>()
  
  // Add or update nodes
  for (const n of apiNodes) {
    currentIds.add(n.id)
    const activation = n.mean_activation || 0
    
    if (!graphNodes.has(n.id)) {
      // New Node!
      const mesh = new THREE.Mesh(sphereGeo, getMaterial(activation))
      // Spawn at random position
      mesh.position.set(
        (Math.random() - 0.5) * 10,
        (Math.random() - 0.5) * 10,
        (Math.random() - 0.5) * 10
      )
      moleculeGroup.add(mesh)
      graphNodes.set(n.id, {
        id: n.id,
        activation,
        mesh,
        vel: new THREE.Vector3(0, 0, 0)
      })
    } else {
      // Update existing node
      const node = graphNodes.get(n.id)!
      node.activation = activation
      node.mesh.material = getMaterial(activation)
      // Node scale based on activation
      const scale = 1 + Math.min(2, Math.abs(activation) / 10)
      node.mesh.scale.set(scale, scale, scale)
    }
  }
  
  // Remove missing nodes
  for (const [id, node] of Array.from(graphNodes.entries())) {
    if (!currentIds.has(id)) {
      moleculeGroup.remove(node.mesh)
      graphNodes.delete(id)
    }
  }
  
  // Rebuild links (for simplicity, we just clear and recreate them every fetch)
  for (const link of graphLinks) {
    moleculeGroup.remove(link.line)
    link.line.geometry.dispose()
  }
  graphLinks.length = 0
  
  for (const l of apiLinks) {
    if (graphNodes.has(l.source) && graphNodes.has(l.target)) {
      const lineGeo = new THREE.BufferGeometry().setFromPoints([
        graphNodes.get(l.source)!.mesh.position,
        graphNodes.get(l.target)!.mesh.position
      ])
      // Thicker/brighter line for higher weight
      const weight = l.weight || 0.1
      const lMat = new THREE.LineBasicMaterial({ 
        color: 0x88DDFF, 
        transparent: true, 
        opacity: Math.min(0.9, 0.4 + weight * 5) 
      })
      const line = new THREE.Line(lineGeo, lMat)
      moleculeGroup.add(line)
      graphLinks.push({
        sourceId: l.source,
        targetId: l.target,
        weight,
        line
      })
    }
  }
}

function initThree() {
  if (!container.value) return

  scene = new THREE.Scene()
  camera = new THREE.PerspectiveCamera(45, props.width / props.height, 0.1, 1000)
  camera.position.z = 25

  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })
  renderer.setSize(props.width, props.height)
  renderer.setPixelRatio(window.devicePixelRatio)
  container.value.appendChild(renderer.domElement)

  // Lighting
  const ambientLight = new THREE.AmbientLight(0x404040)
  scene.add(ambientLight)
  const pointLight = new THREE.PointLight(0x4FC3F7, 1, 100)
  pointLight.position.set(10, 10, 10)
  scene.add(pointLight)
  const pointLight2 = new THREE.PointLight(0xffaaaa, 0.8, 100)
  pointLight2.position.set(-10, -10, 10)
  scene.add(pointLight2)

  moleculeGroup = new THREE.Group()
  scene.add(moleculeGroup)

  animate()
}

// Simple Force-Directed Layout logic
function applyForces() {
  const nodes = Array.from(graphNodes.values())
  const damping = 0.85
  const repulsion = 2.0
  const springLength = 5.0
  const springStrength = 0.05
  const gravity = 0.01

  // Repulsion
  for (let i = 0; i < nodes.length; i++) {
    for (let j = i + 1; j < nodes.length; j++) {
      const n1 = nodes[i]
      const n2 = nodes[j]
      const dx = n1.mesh.position.x - n2.mesh.position.x
      const dy = n1.mesh.position.y - n2.mesh.position.y
      const dz = n1.mesh.position.z - n2.mesh.position.z
      let distSq = dx*dx + dy*dy + dz*dz
      if (distSq < 0.1) distSq = 0.1
      
      const force = repulsion / distSq
      const fx = (dx / Math.sqrt(distSq)) * force
      const fy = (dy / Math.sqrt(distSq)) * force
      const fz = (dz / Math.sqrt(distSq)) * force
      
      n1.vel.x += fx
      n1.vel.y += fy
      n1.vel.z += fz
      n2.vel.x -= fx
      n2.vel.y -= fy
      n2.vel.z -= fz
    }
  }

  // Attraction (Links)
  for (const link of graphLinks) {
    const n1 = graphNodes.get(link.sourceId)
    const n2 = graphNodes.get(link.targetId)
    if (!n1 || !n2) continue

    const dx = n2.mesh.position.x - n1.mesh.position.x
    const dy = n2.mesh.position.y - n1.mesh.position.y
    const dz = n2.mesh.position.z - n1.mesh.position.z
    const dist = Math.sqrt(dx*dx + dy*dy + dz*dz)
    
    // Spring force based on weight
    const force = (dist - springLength) * springStrength * (0.5 + link.weight)
    const fx = (dx / dist) * force
    const fy = (dy / dist) * force
    const fz = (dz / dist) * force
    
    n1.vel.x += fx
    n1.vel.y += fy
    n1.vel.z += fz
    n2.vel.x -= fx
    n2.vel.y -= fy
    n2.vel.z -= fz
  }

  // Gravity to center & update pos
  for (const n of nodes) {
    n.vel.x -= n.mesh.position.x * gravity
    n.vel.y -= n.mesh.position.y * gravity
    n.vel.z -= n.mesh.position.z * gravity
    
    n.vel.multiplyScalar(damping)
    n.mesh.position.add(n.vel)
  }

  // Update Line Geometries
  for (const link of graphLinks) {
    const n1 = graphNodes.get(link.sourceId)
    const n2 = graphNodes.get(link.targetId)
    if (n1 && n2) {
      const positions = new Float32Array([
        n1.mesh.position.x, n1.mesh.position.y, n1.mesh.position.z,
        n2.mesh.position.x, n2.mesh.position.y, n2.mesh.position.z
      ])
      link.line.geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3))
    }
  }
}

function animate() {
  animationId = requestAnimationFrame(animate)
  applyForces()
  
  // Slow gentle rotation of the whole group
  if (moleculeGroup) {
    moleculeGroup.rotation.y += 0.002
    moleculeGroup.rotation.x += 0.001
  }
  
  renderer.render(scene, camera)
}

let fetchInterval: number

// Watch size changes (for full screen Lens)
watch([() => props.width, () => props.height], () => {
  if (camera && renderer) {
    camera.aspect = props.width / props.height
    camera.updateProjectionMatrix()
    renderer.setSize(props.width, props.height)
  }
})

onMounted(() => {
  initThree()
  fetchGraphData()
  fetchInterval = window.setInterval(fetchGraphData, 2000) // Poll every 2s
})

onBeforeUnmount(() => {
  cancelAnimationFrame(animationId)
  clearInterval(fetchInterval)
  if (renderer) {
    renderer.dispose()
  }
})
</script>

<style scoped>
.dream-decoder-3d {
  background: transparent;
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
  height: 100%;
}
</style>
