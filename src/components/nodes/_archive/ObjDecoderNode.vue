<template>
  <div class="obj-decoder-node" :class="{ 'fullscreen': isFullscreen }" style="padding: 16px; background: #0A0A0A; color: #FFF; border: 2px solid #00F3FF; box-shadow: 4px 4px 0 #00F3FF; display: flex; flex-direction: column;" :style="isFullscreen ? 'width: 100vw; height: 100vh; position: fixed; top: 0; left: 0; z-index: 9999; box-sizing: border-box;' : 'width: 300px;'">
    <div style="font-weight: 900; font-size: 14px; border-bottom: 2px solid #00F3FF; padding-bottom: 8px; margin-bottom: 8px; text-transform: uppercase; color: #00F3FF; display: flex; justify-content: space-between; align-items: center;">
      <span>[ TENSOR TOPOLOGY ]</span>
      <div style="display: flex; gap: 8px;">
        <button @click="toggleFullscreen" style="background: transparent; color: #00F3FF; border: 1px solid #00F3FF; cursor: pointer; padding: 2px 8px; font-family: 'Space Mono', monospace; font-size: 10px;">
          {{ isFullscreen ? 'MINIMIZE' : 'FULLSCREEN' }}
        </button>
        <i class="fas fa-cube"></i>
      </div>
    </div>
    
    <div style="font-family: 'Space Mono', monospace; font-size: 10px; color: #888; margin-bottom: 8px;">
      Decoding Environmental Signature for Node: <br/>
      <strong style="color: #00F3FF;">{{ node.id }}</strong>
    </div>

    <!-- 3D Canvas Container -->
    <div ref="container" style="flex: 1; min-height: 250px; background: #000; border: 1px solid #333; position: relative;">
      <div v-if="loading" style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); color: #00F3FF; font-family: 'Space Mono', monospace; font-size: 10px;">
        DECODING...
      </div>
      <div v-if="error" style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); color: #FF3366; font-family: 'Space Mono', monospace; font-size: 10px;">
        DECODE FAILED
      </div>
    </div>
    
    <div style="display: flex; gap: 8px; margin-top: 8px;">
      <button @click="loadObj" style="flex: 1; background: #00F3FF; color: #0A0A0A; border: none; font-weight: 900; cursor: pointer; padding: 6px; font-family: 'Space Mono', monospace;">RE-SYNTHESIZE</button>
      <button @click="toggleWireframe" style="background: #333; color: #00F3FF; border: 1px solid #00F3FF; font-weight: 900; cursor: pointer; padding: 6px; font-family: 'Space Mono', monospace;">WIREFRAME</button>
      <button @click="exportObj" style="background: #333; color: #FFF; border: none; font-weight: 900; cursor: pointer; padding: 6px; font-family: 'Space Mono', monospace;"><i class="fas fa-download"></i></button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import * as THREE from 'three'
import { OBJLoader } from 'three/examples/jsm/loaders/OBJLoader.js'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'

const props = defineProps<{
  node: any
}>()

const container = ref<HTMLElement | null>(null)
const loading = ref(true)
const error = ref(false)
let rawObjData = ""

let scene: THREE.Scene
let camera: THREE.PerspectiveCamera
let renderer: THREE.WebGLRenderer
let animationId: number
let objectGroup: THREE.Group
let controls: OrbitControls
let currentMaterial: THREE.MeshPhongMaterial
const isFullscreen = ref(false)
const isWireframe = ref(true)

onMounted(() => {
  initThree()
  loadObj()
})

onBeforeUnmount(() => {
  if (animationId) cancelAnimationFrame(animationId)
  if (renderer) renderer.dispose()
})

function initThree() {
  if (!container.value) return
  
  scene = new THREE.Scene()
  scene.background = new THREE.Color(0x000000)
  
  camera = new THREE.PerspectiveCamera(45, container.value.clientWidth / container.value.clientHeight, 0.1, 1000)
  camera.position.z = 4
  
  renderer = new THREE.WebGLRenderer({ antialias: true })
  renderer.setSize(container.value.clientWidth, container.value.clientHeight)
  container.value.appendChild(renderer.domElement)
  
  const ambientLight = new THREE.AmbientLight(0xffffff, 0.4)
  scene.add(ambientLight)
  
  const dirLight = new THREE.DirectionalLight(0x00F3FF, 0.8)
  dirLight.position.set(5, 5, 5)
  scene.add(dirLight)
  
  const dirLight2 = new THREE.DirectionalLight(0xFF3366, 0.5)
  dirLight2.position.set(-5, -5, 2)
  scene.add(dirLight2)
  
  objectGroup = new THREE.Group()
  scene.add(objectGroup)
  
  controls = new OrbitControls(camera, renderer.domElement)
  controls.enableDamping = true
  controls.dampingFactor = 0.05
  controls.autoRotate = true
  controls.autoRotateSpeed = 2.0
  
  window.addEventListener('resize', onWindowResize)
  
  animate()
}

function onWindowResize() {
  if (!container.value || !camera || !renderer) return
  camera.aspect = container.value.clientWidth / container.value.clientHeight
  camera.updateProjectionMatrix()
  renderer.setSize(container.value.clientWidth, container.value.clientHeight)
}

function toggleFullscreen() {
  isFullscreen.value = !isFullscreen.value
  nextTick(() => {
    onWindowResize()
  })
}

function toggleWireframe() {
  isWireframe.value = !isWireframe.value
  if (currentMaterial) {
    currentMaterial.wireframe = isWireframe.value
  }
}

function animate() {
  animationId = requestAnimationFrame(animate)
  if (controls) controls.update()
  renderer.render(scene, camera)
}

async function loadObj() {
  loading.value = true
  error.value = false
  
  try {
    const API_BASE = (window as any).API_BASE || ''
    const url = API_BASE ? `${API_BASE}/lgnn/decoder/obj/${props.node.id}` : `/api/lgnn/decoder/obj/${props.node.id}`
    const res = await fetch(url)
    
    if (!res.ok) throw new Error('Network response was not ok')
    
    rawObjData = await res.text()
    
    // Clear previous
    while (objectGroup.children.length > 0) { 
        objectGroup.remove(objectGroup.children[0]); 
    }
    
    const loader = new OBJLoader()
    const obj = loader.parse(rawObjData)
    
    // Materialize
    currentMaterial = new THREE.MeshPhongMaterial({
      color: 0x00F3FF,
      wireframe: isWireframe.value,
      transparent: true,
      opacity: 0.8,
      side: THREE.DoubleSide
    })
    
    obj.traverse((child) => {
      if (child instanceof THREE.Mesh) {
        child.material = currentMaterial
      }
    })
    
    // Center object
    const box = new THREE.Box3().setFromObject(obj)
    const center = box.getCenter(new THREE.Vector3())
    obj.position.x += (obj.position.x - center.x)
    obj.position.y += (obj.position.y - center.y)
    obj.position.z += (obj.position.z - center.z)
    
    // Scale object to fit nicely
    const size = box.getSize(new THREE.Vector3()).length()
    const scale = 2.0 / size
    obj.scale.set(scale, scale, scale)
    
    objectGroup.add(obj)
    
  } catch (err) {
    console.error('Failed to load OBJ:', err)
    error.value = true
  } finally {
    loading.value = false
  }
}

function exportObj() {
  if (!rawObjData) return
  const blob = new Blob([rawObjData], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `aethelnet_signature_${props.node.id}.obj`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

watch(() => props.node.id, () => {
  loadObj()
})
</script>
