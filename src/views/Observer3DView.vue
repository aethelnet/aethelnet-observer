<template>
  <div class="observer-3d" ref="container">
    <div class="hud">
      <span class="hud-title">MACRO VISION (UNIT 734)</span>
      <span class="hud-status">[WebGL Engine Active] >> Rendering 10,000 Reservoir Nodes</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import * as THREE from 'three'
import { API_BASE } from '../shared/api.js'

const container = ref<HTMLDivElement | null>(null)
let scene: THREE.Scene, camera: THREE.PerspectiveCamera, renderer: THREE.WebGLRenderer
let particles: THREE.Points | null = null
let animationId: number
let mouseX = 0, mouseY = 0
let fetchInterval: number

const onMouseMove = (event: MouseEvent) => {
  const halfX = window.innerWidth / 2
  const halfY = window.innerHeight / 2
  mouseX = (event.clientX - halfX) * 0.5
  mouseY = (event.clientY - halfY) * 0.5
}

const onResize = () => {
  if (!container.value) return
  camera.aspect = container.value.clientWidth / container.value.clientHeight
  camera.updateProjectionMatrix()
  renderer.setSize(container.value.clientWidth, container.value.clientHeight)
}

const fetchLiveNodes = async () => {
  try {
    const url = API_BASE ? `${API_BASE}/lgnn/graph` : '/api/lgnn/graph';
    const res = await fetch(url)
    if (!res.ok) return
    const data = await res.json()
    
    if (particles) {
      scene.remove(particles)
      particles.geometry.dispose()
      ;(particles.material as THREE.Material).dispose()
    }

    const geometry = new THREE.BufferGeometry()
    const vertices = []
    const colors = []
    
    // Scale factor to spread the nodes out in the 3D space
    const scale = 25.0 

    for (const node of data.nodes) {
      const isManual = node.id.startsWith('seed_') || node.id.startsWith('wiki_') || node.id.startsWith('manual_') || node.isManual
      const act = Math.abs(node.mean_activation || 0)
      
      // Use backend coordinates or random jitter
      const x = (node.x || (Math.random() - 0.5) * 50) * scale
      const y = (node.y || (Math.random() - 0.5) * 50) * scale
      const z = (node.z || (Math.random() - 0.5) * 50) * scale
      vertices.push(x, y, z)
      
      if (isManual) {
        colors.push(0.88, 0.23, 0.19) // #E03C31 accent for manual thoughts
      } else if (act > 0.45) {
        // High resonance (Opus threshold passed!) gets red
        colors.push(0.88, 0.23, 0.19)
      } else {
        // Background noise gets the brutalist white
        colors.push(0.95, 0.95, 0.94)
      }
    }
    
    geometry.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3))
    geometry.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3))

    const material = new THREE.PointsMaterial({
      size: 5,
      vertexColors: true,
      transparent: true,
      opacity: 0.85,
      sizeAttenuation: true
    })

    particles = new THREE.Points(geometry, material)
    scene.add(particles)
  } catch (e) {
    console.error("Failed to fetch 3D graph data", e)
  }
}

onMounted(() => {
  if (!container.value) return

  // 1. Scene Setup
  scene = new THREE.Scene()
  scene.fog = new THREE.FogExp2(0x1a1a1a, 0.0004)

  // 2. Camera
  camera = new THREE.PerspectiveCamera(75, container.value.clientWidth / container.value.clientHeight, 1, 6000)
  camera.position.z = 1800

  // 3. Renderer (Brutalist dark theme)
  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })
  renderer.setSize(container.value.clientWidth, container.value.clientHeight)
  renderer.setClearColor(0x1a1a1a, 1) // Brutalist dark base
  container.value.appendChild(renderer.domElement)

  // Initial fetch and setup polling
  fetchLiveNodes()
  fetchInterval = window.setInterval(fetchLiveNodes, 5000)

  // 4. Animation Loop
  const animate = () => {
    animationId = requestAnimationFrame(animate)
    
    if (particles) {
      // Slow cinematic rotation of the entire universe
      particles.rotation.x += 0.0002
      particles.rotation.y += 0.0005
    }
    
    // Parallax mouse drift
    camera.position.x += (mouseX - camera.position.x) * 0.05
    camera.position.y += (-mouseY - camera.position.y) * 0.05
    camera.lookAt(scene.position)
    
    renderer.render(scene, camera)
  }
  
  window.addEventListener('mousemove', onMouseMove)
  window.addEventListener('resize', onResize)

  animate()
})

onUnmounted(() => {
  if (animationId) cancelAnimationFrame(animationId)
  if (fetchInterval) clearInterval(fetchInterval)
  if (renderer && renderer.domElement) {
    renderer.dispose()
  }
  window.removeEventListener('mousemove', onMouseMove)
  window.removeEventListener('resize', onResize)
})
</script>

<style scoped>
.observer-3d {
  width: 100%;
  height: 100%;
  position: relative;
  background: #1A1A1A;
  overflow: hidden;
}

.hud {
  position: absolute;
  top: 16px;
  left: 16px;
  z-index: 10;
  display: flex;
  flex-direction: column;
  pointer-events: none;
}

.hud-title {
  color: #F4F4F0;
  font-family: 'Space Mono', monospace;
  font-size: 24px;
  font-weight: 900;
  letter-spacing: 2px;
  text-shadow: 2px 2px 0px #000;
}

.hud-status {
  color: #E03C31;
  font-family: 'Courier New', Courier, monospace;
  font-weight: bold;
  margin-top: 4px;
}
</style>
