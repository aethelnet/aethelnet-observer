<template>
  <div class="observer-3d-view">
    <!-- WebGL Canvas Layer -->
    <canvas ref="canvasRef" class="gl-canvas"></canvas>

    <!-- Overlay Layer -->
    <div class="hud-overlay">
      <div class="top-bar">
        <div class="system-status">
          <div class="pulse-dot"></div>
          <span>AETHELNET CORE ACTIVE</span>
        </div>
        <div class="view-controls">
          <button class="hud-btn" @click="resetCamera">Reset View</button>
          <button class="hud-btn" :class="{ active: autoRotate }" @click="autoRotate = !autoRotate">Auto-Rotate</button>
        </div>
      </div>
      
      <div class="bottom-bar">
        <div class="stats">
          <span>Nodes: {{ nodes.length }}</span>
          <span>Edges: {{ links.length }}</span>
        </div>
      </div>
    </div>
    
    <!-- Telemetry HUD -->
    <TelemetryHUD />
    
    <!-- P2P Mesh Interactive Cockpit -->
    <P2PMeshOverlay style="pointer-events: auto;" />

    <!-- Node Details Panel -->
    <NodeDetailsOverlay 
      v-if="selectedNode" 
      :node="selectedNode" 
      @close="selectedNode = null"
      style="pointer-events: auto;"
    />

    <!-- Ouroboros Concept Injector -->
    <OuroborosInjector style="pointer-events: auto;" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls'
import { useAgentStore } from '../stores/agentStore'
import P2PMeshOverlay from '../components/P2PMeshOverlay.vue'
import TelemetryHUD from '../components/TelemetryHUD.vue'
import NodeDetailsOverlay from '../components/NodeDetailsOverlay.vue'
import OuroborosInjector from '../components/OuroborosInjector.vue'

const agentStore = useAgentStore()
const canvasRef = ref<HTMLCanvasElement | null>(null)
const autoRotate = ref(true)
const selectedNode = ref(null)

// Temporary mock data if store is empty
const nodes = ref(agentStore.nodes.length ? agentStore.nodes : Array.from({ length: 150 }, (_, i) => ({
  id: `n_${i}`,
  x: (Math.random() - 0.5) * 100,
  y: (Math.random() - 0.5) * 100,
  z: (Math.random() - 0.5) * 100,
  type: ['agent', 'data', 'concept'][Math.floor(Math.random() * 3)],
  active: Math.random() > 0.5
})))

const links = ref(agentStore.edges.length ? agentStore.edges : Array.from({ length: 200 }, () => ({
  source: `n_${Math.floor(Math.random() * 150)}`,
  target: `n_${Math.floor(Math.random() * 150)}`,
  value: Math.random()
})))

// Three.js State
let scene: THREE.Scene
let camera: THREE.PerspectiveCamera
let renderer: THREE.WebGLRenderer
let controls: OrbitControls
let animationFrameId: number

let nodeMesh: THREE.InstancedMesh
let linkLines: THREE.LineSegments

const raycaster = new THREE.Raycaster()
const mouse = new THREE.Vector2()

const initThreeJS = () => {
  if (!canvasRef.value) return

  // Scene setup
  scene = new THREE.Scene()
  scene.fog = new THREE.FogExp2(0x050505, 0.01)

  // Camera setup
  camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000)
  camera.position.z = 100

  // Renderer setup
  renderer = new THREE.WebGLRenderer({ canvas: canvasRef.value, antialias: true, alpha: true })
  renderer.setSize(window.innerWidth - 250, window.innerHeight) // Subtract sidebar width
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))

  // Controls
  controls = new OrbitControls(camera, renderer.domElement)
  controls.enableDamping = true
  controls.dampingFactor = 0.05
  controls.autoRotate = autoRotate.value
  controls.autoRotateSpeed = 0.5

  // Lighting
  const ambientLight = new THREE.AmbientLight(0x404040)
  scene.add(ambientLight)
  const directionalLight = new THREE.DirectionalLight(0xffffff, 1)
  directionalLight.position.set(1, 1, 1)
  scene.add(directionalLight)

  createGraph()

  // Handle Resize
  window.addEventListener('resize', onWindowResize)
  
  // Handle Clicks for Raycasting
  renderer.domElement.addEventListener('pointerdown', onPointerDown)
  
  // Start loop
  animate()
}

const onPointerDown = (event: PointerEvent) => {
  if (!camera || !nodeMesh) return
  const rect = renderer.domElement.getBoundingClientRect()
  mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1
  mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1
  
  raycaster.setFromCamera(mouse, camera)
  const intersects = raycaster.intersectObject(nodeMesh)
  
  if (intersects.length > 0 && intersects[0].instanceId !== undefined) {
    const id = intersects[0].instanceId
    selectedNode.value = nodes.value[id]
    
    // Slight flash effect on click
    const color = new THREE.Color(0xffffff)
    nodeMesh.setColorAt(id, color)
    if(nodeMesh.instanceColor) nodeMesh.instanceColor.needsUpdate = true
  } else {
    // Only deselect if they clicked empty space (not a HUD)
    selectedNode.value = null
  }
}

const createGraph = () => {
  // 1. Create Nodes (InstancedMesh for performance)
  const geometry = new THREE.SphereGeometry(1, 16, 16)
  const material = new THREE.MeshBasicMaterial({ color: 0x00ffaa, transparent: true, opacity: 0.8 })
  
  nodeMesh = new THREE.InstancedMesh(geometry, material, nodes.value.length)
  
  const dummy = new THREE.Object3D()
  const color = new THREE.Color()
  
  nodes.value.forEach((node: any, i: number) => {
    dummy.position.set(node.x, node.y, node.z)
    
    // Size based on active state
    const scale = node.active ? 1.5 : 1.0
    dummy.scale.set(scale, scale, scale)
    dummy.updateMatrix()
    
    nodeMesh.setMatrixAt(i, dummy.matrix)
    
    // Color based on type
    if (node.type === 'agent') color.setHex(0x00ffaa)
    else if (node.type === 'data') color.setHex(0x00aaff)
    else color.setHex(0xff3366)
    
    nodeMesh.setColorAt(i, color)
  })
  
  nodeMesh.instanceMatrix.needsUpdate = true
  if(nodeMesh.instanceColor) nodeMesh.instanceColor.needsUpdate = true
  scene.add(nodeMesh)

  // 2. Create Links
  const linkMaterial = new THREE.LineBasicMaterial({ 
    color: 0x00ffaa, 
    transparent: true, 
    opacity: 0.2 
  })
  
  const points: number[] = []
  
  links.value.forEach((link: any) => {
    const sourceNode = nodes.value.find((n: any) => n.id === link.source)
    const targetNode = nodes.value.find((n: any) => n.id === link.target)
    
    if (sourceNode && targetNode) {
      points.push(sourceNode.x, sourceNode.y, sourceNode.z)
      points.push(targetNode.x, targetNode.y, targetNode.z)
    }
  })
  
  const lineGeometry = new THREE.BufferGeometry()
  lineGeometry.setAttribute('position', new THREE.Float32BufferAttribute(points, 3))
  
  linkLines = new THREE.LineSegments(lineGeometry, linkMaterial)
  scene.add(linkLines)
}

const updateGraph = () => {
  if (!scene) return
  
  // Very basic update logic - in a real app, you'd update positions based on physics
  const dummy = new THREE.Object3D()
  const time = Date.now() * 0.001
  
  nodes.value.forEach((node: any, i: number) => {
    // Slight idle float
    const yOffset = Math.sin(time + node.x) * 2
    dummy.position.set(node.x, node.y + yOffset, node.z)
    
    const scale = node.active ? 1.5 + Math.sin(time*5)*0.2 : 1.0
    dummy.scale.set(scale, scale, scale)
    
    dummy.updateMatrix()
    nodeMesh.setMatrixAt(i, dummy.matrix)
  })
  
  nodeMesh.instanceMatrix.needsUpdate = true
}

const animate = () => {
  animationFrameId = requestAnimationFrame(animate)
  controls.autoRotate = autoRotate.value
  controls.update()
  updateGraph()
  renderer.render(scene, camera)
}

const onWindowResize = () => {
  if (!camera || !renderer) return
  const width = window.innerWidth - 250 // Sidebar width
  const height = window.innerHeight
  
  camera.aspect = width / height
  camera.updateProjectionMatrix()
  renderer.setSize(width, height)
}

const resetCamera = () => {
  if (!camera || !controls) return
  // Smooth transition could be added here
  camera.position.set(0, 0, 100)
  controls.target.set(0, 0, 0)
}

watch(autoRotate, (val) => {
  if (controls) controls.autoRotate = val
})

onMounted(() => {
  initThreeJS()
})

onBeforeUnmount(() => {
  cancelAnimationFrame(animationFrameId)
  window.removeEventListener('resize', onWindowResize)
  if (renderer && renderer.domElement) {
    renderer.domElement.removeEventListener('pointerdown', onPointerDown)
    renderer.dispose()
    renderer.forceContextLoss()
  }
  // Dispose geometries and materials
  scene?.traverse((object) => {
    if ((object as THREE.Mesh).isMesh) {
      const mesh = object as THREE.Mesh
      mesh.geometry.dispose()
      if (Array.isArray(mesh.material)) {
        mesh.material.forEach(m => m.dispose())
      } else {
        mesh.material.dispose()
      }
    }
  })
})
</script>

<style scoped>
.observer-3d-view {
  width: 100%;
  height: 100%;
  position: relative;
  background-color: #050505;
  overflow: hidden;
}

.gl-canvas {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  outline: none;
}

.hud-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none; /* Let clicks pass through to canvas */
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 1.5rem;
  box-sizing: border-box;
}

.top-bar {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  pointer-events: auto;
}

.system-status {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  background: rgba(0, 20, 10, 0.6);
  border: 1px solid rgba(0, 255, 170, 0.3);
  padding: 0.5rem 1rem;
  border-radius: 20px;
  backdrop-filter: blur(4px);
  color: #00ffaa;
  font-family: monospace;
  font-size: 0.8rem;
  letter-spacing: 1px;
}

.pulse-dot {
  width: 8px;
  height: 8px;
  background: #00ffaa;
  border-radius: 50%;
  box-shadow: 0 0 10px #00ffaa;
  animation: pulse 2s infinite;
}

.view-controls {
  display: flex;
  gap: 0.5rem;
}

.hud-btn {
  background: rgba(10, 10, 15, 0.8);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.7);
  padding: 0.5rem 1rem;
  border-radius: 6px;
  font-size: 0.8rem;
  cursor: pointer;
  transition: all 0.2s;
  backdrop-filter: blur(4px);
}

.hud-btn:hover {
  background: rgba(20, 20, 30, 0.9);
  color: #fff;
  border-color: rgba(0, 255, 170, 0.3);
}

.hud-btn.active {
  background: rgba(0, 255, 170, 0.1);
  color: #00ffaa;
  border-color: rgba(0, 255, 170, 0.5);
}

.bottom-bar {
  display: flex;
  justify-content: flex-end;
  pointer-events: auto;
}

.stats {
  display: flex;
  gap: 1.5rem;
  background: rgba(0, 0, 0, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.1);
  padding: 0.5rem 1rem;
  border-radius: 6px;
  font-family: monospace;
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.5);
  backdrop-filter: blur(4px);
}

@keyframes pulse {
  0% { transform: scale(0.95); opacity: 0.5; }
  50% { transform: scale(1.05); opacity: 1; }
  100% { transform: scale(0.95); opacity: 0.5; }
}
</style>
