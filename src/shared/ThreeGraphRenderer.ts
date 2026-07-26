import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'

export class ThreeGraphRenderer {
  canvas: HTMLCanvasElement
  renderer: THREE.WebGLRenderer
  scene: THREE.Scene
  
  orthoCamera: THREE.OrthographicCamera
  perspCamera: THREE.PerspectiveCamera
  activeCamera: THREE.Camera
  controls: OrbitControls
  
  isGalaxyMode: boolean = false
  warpProgress: number = 0
  
  nodes: any[]
  links: any[]
  
  nodeMesh!: THREE.InstancedMesh
  linkLines!: THREE.LineSegments
  synapseMesh!: THREE.InstancedMesh
  starfield!: THREE.Points
  globeMesh!: THREE.Mesh
  lineUniforms: any
  activeSynapses: any[] = []
  
  width: number
  height: number
  
  globalTransform: { x: number, y: number, k: number }
  
  raycaster: THREE.Raycaster
  mouse: THREE.Vector2
  onClick?: (node: any) => void
  onClickEdge?: (link: any) => void
  
  linkIndexMap: any[] = []
  
  // Synaptic Pulse / Shockwaves
  shockwaves: { mesh: THREE.Mesh, scale: number, maxScale: number }[] = []
  
  public triggerShockwave(node: any) {
    const geo = new THREE.RingGeometry(4.5, 5.5, 32)
    const mat = new THREE.MeshBasicMaterial({ 
      color: 0x0ea5e9, // Subtle Sky Blue
      transparent: true, 
      opacity: 0.8, 
      blending: THREE.NormalBlending 
    })
    const mesh = new THREE.Mesh(geo, mat)
    
    const { x: tx, y: ty, k } = this.globalTransform
    const px = tx + (node.x || 0) * k
    const py = ty + (node.y || 0) * k
    const wx = px - this.width / 2
    const wy = -(py - this.height / 2)
    
    mesh.position.set(wx, wy, 1)
    mesh.scale.set(k, k, 1)
    
    this.scene.add(mesh)
    this.shockwaves.push({ mesh, scale: k, maxScale: k * 30 })
  }
  
  private _animationFrameId: number | null = null

  constructor(canvas: HTMLCanvasElement, nodes: any[], links: any[], globalTransform: { x: number, y: number, k: number }) {
    this.canvas = canvas
    this.nodes = nodes
    this.links = links
    this.globalTransform = globalTransform
    
    this.width = window.innerWidth
    this.height = window.innerHeight
    
    // Setup Renderer
    this.renderer = new THREE.WebGLRenderer({ canvas: this.canvas, alpha: true, antialias: true })
    this.renderer.setSize(this.width, this.height)
    this.renderer.setPixelRatio(window.devicePixelRatio)
    
    // Setup Scene & Cameras
    this.scene = new THREE.Scene()
    
    // 2D Camera
    this.orthoCamera = new THREE.OrthographicCamera(
      this.width / -2, this.width / 2,
      this.height / 2, this.height / -2,
      1, 10000
    )
    this.orthoCamera.position.z = 500
    
    // 3D Camera (Galaxy)
    this.perspCamera = new THREE.PerspectiveCamera(75, this.width / this.height, 0.1, 20000)
    this.perspCamera.position.set(0, 0, 800)
    
    this.activeCamera = this.orthoCamera
    
    // Controls
    this.controls = new OrbitControls(this.perspCamera, this.renderer.domElement)
    this.controls.enableDamping = true
    this.controls.dampingFactor = 0.05
    this.controls.enabled = false // Only active in Galaxy mode
    
    this.raycaster = new THREE.Raycaster()
    this.raycaster.params.Points.threshold = 10
    this.raycaster.params.Line.threshold = 10
    
    this.mouse = new THREE.Vector2()
    
    this.initMeshes()
    
    // Handle resize
    window.addEventListener('resize', this.onResize)
    
    this.start()
  }
  
  private initMeshes() {
    // 1. Instanced Mesh for Nodes
    const maxNodes = 10000
    const geometry = new THREE.PlaneGeometry(10, 10)
    const material = new THREE.MeshBasicMaterial({ 
      color: 0xffffff, 
      transparent: true, 
      opacity: 1.0, 
      blending: THREE.NormalBlending,
      depthWrite: false
    })
    
    material.onBeforeCompile = (shader) => {
      shader.vertexShader = `
        varying vec2 vMyUv;
        ${shader.vertexShader}
      `.replace(
        '#include <project_vertex>',
        `#include <project_vertex>
         vMyUv = uv;`
      )
      
      shader.fragmentShader = `
        varying vec2 vMyUv;
        ${shader.fragmentShader}
      `.replace(
        '#include <color_fragment>',
        `#include <color_fragment>
         float dist = distance(vMyUv, vec2(0.5));
         if (dist > 0.5) discard;
         
         // Clean flat circle with subtle border
         float alpha = smoothstep(0.5, 0.45, dist);
         float border = smoothstep(0.48, 0.45, dist) - smoothstep(0.45, 0.42, dist);
         
         // Darken the border slightly for crispness in light mode
         vec3 finalColor = mix(diffuseColor.rgb, diffuseColor.rgb * 0.8, border);
         
         diffuseColor.rgb = finalColor;
         diffuseColor.a *= alpha;
        `
      )
    }
    
    this.nodeMesh = new THREE.InstancedMesh(geometry, material, maxNodes)
    this.nodeMesh.instanceMatrix.setUsage(THREE.DynamicDrawUsage)
    
    // Pre-allocate color buffer
    const colorArray = new Float32Array(maxNodes * 3)
    this.nodeMesh.instanceColor = new THREE.InstancedBufferAttribute(colorArray, 3)
    this.nodeMesh.instanceColor.setUsage(THREE.DynamicDrawUsage)
    
    this.scene.add(this.nodeMesh)
    
    // 2. Line Segments for Links
    const maxLinks = 20000
    const lineGeo = new THREE.BufferGeometry()
    const positions = new Float32Array(maxLinks * 2 * 3)
    const progress = new Float32Array(maxLinks * 2)
    for (let i = 0; i < maxLinks; i++) {
        progress[i * 2] = 0.0
        progress[i * 2 + 1] = 1.0
    }
    
    lineGeo.setAttribute('position', new THREE.BufferAttribute(positions, 3))
    lineGeo.setAttribute('aProgress', new THREE.BufferAttribute(progress, 1))
    
    const lineMat = new THREE.LineBasicMaterial({ 
      color: 0xcbd5e1, // Light slate border color
      transparent: true, 
      opacity: 0.6,
      blending: THREE.NormalBlending
    })
    
    this.lineUniforms = {
      uTime: { value: 0 }
    }
    
    lineMat.onBeforeCompile = (shader) => {
      shader.uniforms.uTime = this.lineUniforms.uTime
      
      shader.vertexShader = `
        attribute float aProgress;
        varying float vProgress;
        ${shader.vertexShader}
      `.replace(
        '#include <project_vertex>',
        `#include <project_vertex>
         vProgress = aProgress;`
      )
      
      shader.fragmentShader = `
        uniform float uTime;
        varying float vProgress;
        ${shader.fragmentShader}
      `.replace(
        '#include <color_fragment>',
        `#include <color_fragment>
         float speed = uTime * 1.5;
         float pulse1 = sin((vProgress - speed) * 30.0);
         float pulse2 = sin((vProgress + speed * 0.5) * 15.0);
         
         float edgeFade = smoothstep(0.0, 0.15, vProgress) * smoothstep(1.0, 0.85, vProgress);
         float glow = max(0.0, pulse1 * 0.5 + pulse2 * 0.5);
         
         // Subtle blueish pulse on grey lines
         vec3 pulseColor = mix(diffuseColor.rgb, vec3(0.0, 0.7, 0.9), glow * 0.5);
         
         diffuseColor.rgb = pulseColor;
         diffuseColor.a *= (0.3 + 0.7 * glow) * edgeFade;
        `
      )
    }
    
    this.linkLines = new THREE.LineSegments(lineGeo, lineMat)
    this.scene.add(this.linkLines)
    
    // 3. Synapses (Data Packets)
    const synapseGeo = new THREE.PlaneGeometry(3, 3)
    const synapseMat = new THREE.MeshBasicMaterial({ 
      color: 0x0ea5e9, // Subtle Blue
      transparent: true, 
      opacity: 0.9, 
      blending: THREE.NormalBlending,
      depthWrite: false
    })
    
    synapseMat.onBeforeCompile = (shader) => {
      shader.vertexShader = `
        varying vec2 vMyUv;
        ${shader.vertexShader}
      `.replace(
        '#include <project_vertex>',
        `#include <project_vertex>
         vMyUv = uv;`
      )
      
      shader.fragmentShader = `
        varying vec2 vMyUv;
        ${shader.fragmentShader}
      `.replace(
        '#include <color_fragment>',
        `#include <color_fragment>
         float dist = distance(vMyUv, vec2(0.5));
         if (dist > 0.5) discard;
         
         float alpha = smoothstep(0.5, 0.3, dist);
         diffuseColor.a *= alpha;
        `
      )
    }
    
    this.synapseMesh = new THREE.InstancedMesh(synapseGeo, synapseMat, maxLinks)
    this.synapseMesh.instanceMatrix.setUsage(THREE.DynamicDrawUsage)
    this.scene.add(this.synapseMesh)
    
    // 4. Background Starfield (Subtle dark dots for light theme)
    const starGeo = new THREE.BufferGeometry()
    const starPositions = new Float32Array(5000 * 3)
    const starColors = new Float32Array(5000 * 3)
    for (let i = 0; i < 5000 * 3; i+=3) {
      starPositions[i] = (Math.random() - 0.5) * 4000
      starPositions[i+1] = (Math.random() - 0.5) * 4000
      starPositions[i+2] = (Math.random() - 0.5) * 4000
      
      // Subtle slate/grey dots
      const shade = 0.5 + Math.random() * 0.3
      starColors[i] = shade
      starColors[i+1] = shade
      starColors[i+2] = shade + 0.1
    }
    starGeo.setAttribute('position', new THREE.BufferAttribute(starPositions, 3))
    starGeo.setAttribute('color', new THREE.BufferAttribute(starColors, 3))
    
    const starMat = new THREE.PointsMaterial({ 
      size: 2, 
      vertexColors: true, 
      transparent: true,
      opacity: 0,
      sizeAttenuation: true,
      blending: THREE.NormalBlending,
      depthWrite: false
    })
    
    starMat.onBeforeCompile = (shader) => {
      shader.fragmentShader = shader.fragmentShader.replace(
        '#include <color_fragment>',
        `#include <color_fragment>
         float dist = distance(gl_PointCoord, vec2(0.5));
         if (dist > 0.5) discard;
         diffuseColor.a *= (1.0 - (dist * 2.0));
        `
      )
    }
    
    this.starfield = new THREE.Points(starGeo, starMat)
    this.scene.add(this.starfield)

    // Wireframe Globe (Subtle light grey)
    const globeGeo = new THREE.SphereGeometry(300, 32, 32)
    const globeMat = new THREE.MeshBasicMaterial({
      color: 0xe2e8f0,
      wireframe: true,
      transparent: true,
      opacity: 0.1,
      blending: THREE.NormalBlending,
      depthWrite: false
    })
    this.globeMesh = new THREE.Mesh(globeGeo, globeMat)
    this.globeMesh.visible = false
    this.scene.add(this.globeMesh)
  }
  
  public updateData(nodes: any[], links: any[]) {
    this.nodes = nodes
    this.links = links
  }
  
  public setGalaxyMode(enabled: boolean) {
    if (this.isGalaxyMode === enabled) return;
    this.isGalaxyMode = enabled
    this.controls.enabled = enabled
    this.activeCamera = enabled ? this.perspCamera : this.orthoCamera
    this.warpProgress = enabled ? 0 : 1; 
  }

  private onResize = () => {
    this.width = window.innerWidth
    this.height = window.innerHeight
    this.renderer.setSize(this.width, this.height)
    
    this.orthoCamera.left = this.width / -2
    this.orthoCamera.right = this.width / 2
    this.orthoCamera.top = this.height / 2
    this.orthoCamera.bottom = this.height / -2
    this.orthoCamera.updateProjectionMatrix()
    
    this.perspCamera.aspect = this.width / this.height
    this.perspCamera.updateProjectionMatrix()
  }
  
  public raycast(clientX: number, clientY: number): boolean {
    const hoverResult = this.raycastHover(clientX, clientY)
    if (hoverResult) {
      if (hoverResult.type === 'node' && this.onClick) {
        this.onClick(hoverResult.data)
        return true
      } else if (hoverResult.type === 'link' && this.onClickEdge) {
        this.onClickEdge(hoverResult.data)
        return true
      }
    }
    return false
  }

  public raycastHover(clientX: number, clientY: number): { type: 'node' | 'link', data: any } | null {
    this.mouse.x = (clientX / this.width) * 2 - 1
    this.mouse.y = -(clientY / this.height) * 2 + 1
    
    this.raycaster.setFromCamera(this.mouse, this.activeCamera)
    
    const intersects = this.raycaster.intersectObject(this.nodeMesh)
    
    if (intersects.length > 0) {
      const instanceId = intersects[0].instanceId
      if (instanceId !== undefined && this.nodes[instanceId]) {
        return { type: 'node', data: this.nodes[instanceId] }
      }
    }
    
    const linkIntersects = this.raycaster.intersectObject(this.linkLines)
    if (linkIntersects.length > 0) {
      const vertexIndex = linkIntersects[0].index
      if (vertexIndex !== undefined) {
        const lineIdx = Math.floor(vertexIndex / 2)
        const link = this.linkIndexMap[lineIdx]
        if (link) {
          return { type: 'link', data: link }
        }
      }
    }
    
    return null
  }
  
  private render = () => {
    this._animationFrameId = requestAnimationFrame(this.render)
    
    const { x: tx, y: ty, k } = this.globalTransform
    
    if (this.warpProgress > 0) {
      if (this.warpProgress < 1 && !this.isGalaxyMode) {
        this.warpProgress = Math.max(0, this.warpProgress - 0.02)
      } else if (this.warpProgress < 1 && this.isGalaxyMode) {
        this.warpProgress = Math.min(1, this.warpProgress + 0.02)
      }
    } else if (this.isGalaxyMode) {
      this.warpProgress += 0.02
    }
    
    if (this.starfield) {
      (this.starfield.material as THREE.PointsMaterial).opacity = this.warpProgress * 0.4
      this.starfield.rotation.y += 0.0002
      this.starfield.rotation.x += 0.0001
    }
    
    if (this.lineUniforms) {
      this.lineUniforms.uTime.value = performance.now() / 1000.0
    }
    
    if (this.isGalaxyMode) {
      this.controls.update()
    }

    const dummy = new THREE.Object3D()
    let count = 0
    let hasGeoNodes = false
    
    for (let i = 0; i < this.nodes.length; i++) {
      const node = this.nodes[i]
      
      const px2d = tx + (node.x || 0) * k
      const py2d = ty + (node.y || 0) * k
      const wx2d = px2d - this.width / 2
      const wy2d = -(py2d - this.height / 2)
      
      if (node.z3d === undefined) {
        let hash = 0;
        const str = node.id || 'unknown';
        for (let j = 0; j < str.length; j++) hash = Math.imul(31, hash) + str.charCodeAt(j) | 0;
        node.z3d = (hash % 1000) - 500;
      }
      
      let wx3d = (node.x || 0) * 6.0
      let wy3d = -(node.y || 0) * 6.0
      let wz3d = node.z3d * 8.0

      let isGeoNode = false;
      if (node.source_tag === 'geo' && node.meta_data?.spatial) {
        isGeoNode = true;
        const lat = node.meta_data.spatial.lat * (Math.PI / 180);
        const lng = node.meta_data.spatial.lng * (Math.PI / 180);
        const radius = 300;
        wx3d = radius * Math.cos(lat) * Math.sin(lng);
        wy3d = radius * Math.sin(lat);
        wz3d = radius * Math.cos(lat) * Math.cos(lng);
      }
      
      if (isGeoNode) hasGeoNodes = true;
      
      const wx = wx2d * (1 - this.warpProgress) + wx3d * this.warpProgress
      const wy = wy2d * (1 - this.warpProgress) + wy3d * this.warpProgress
      const wz = 0 * (1 - this.warpProgress) + wz3d * this.warpProgress
      
      const currentK = k * (1 - this.warpProgress) + 1.0 * this.warpProgress
      
      dummy.position.set(wx, wy, wz)
      
      if (this.isGalaxyMode) {
        dummy.quaternion.copy(this.activeCamera.quaternion)
      } else {
        dummy.quaternion.identity()
      }
      
      const baseScale = node.size ? Math.min(node.size * 0.5, 3.0) : 1.2;
      
      // Light Theme Colors
      if (node.isSelected) {
        const pulse = 1.2 + Math.sin(Date.now() / 150 + i) * 0.2
        dummy.scale.set(currentK * pulse * baseScale, currentK * pulse * baseScale, 1)
        this.nodeMesh.setColorAt(count, new THREE.Color(0x0ea5e9)) // Sky Blue
      } else if (node.meta_data?.is_shielded) {
        dummy.scale.set(currentK * baseScale, currentK * baseScale, 1)
        this.nodeMesh.setColorAt(count, new THREE.Color(0x0d9488)) // Darker Teal
      } else if (node.node_type === 'gravity_well') {
        const pulse = 1.2 + Math.sin(Date.now() / 200 + i) * 0.2
        dummy.scale.set(currentK * pulse * baseScale, currentK * pulse * baseScale, 1)
        this.nodeMesh.setColorAt(count, new THREE.Color(0x8b5cf6)) // Violet
      } else if (node.source_tag === 'ghost') {
        const pulse = 1.0 + Math.sin(Date.now() / 100 + i) * 0.2
        dummy.scale.set(currentK * pulse * baseScale, currentK * pulse * baseScale, 1)
        this.nodeMesh.setColorAt(count, new THREE.Color(0xf43f5e)) // Rose
      } else if (node.source_tag === 'spider' || node.source_tag === 'spider_swarm') {
        dummy.scale.set(currentK * baseScale, currentK * baseScale, 1)
        this.nodeMesh.setColorAt(count, new THREE.Color(0x10b981)) // Emerald
      } else if (node.node_type === 'abstract' || node.id.startsWith('Hub_') || node.id.startsWith('Core_') || node.id.startsWith('Mechanism_') || node.id.startsWith('Metaphor_')) {
        dummy.scale.set(currentK * baseScale * 0.8, currentK * baseScale * 0.8, 1)
        this.nodeMesh.setColorAt(count, new THREE.Color(0x64748b)) // Slate
      } else if (node.source_tag === 'app' || node.source_tag === 'tool') {
        dummy.scale.set(currentK * baseScale * 1.2, currentK * baseScale * 1.2, 1)
        this.nodeMesh.setColorAt(count, new THREE.Color(0x6366f1)) // Indigo
      } else if (node.meta_data?.color) {
        dummy.scale.set(currentK * baseScale, currentK * baseScale, 1)
        this.nodeMesh.setColorAt(count, new THREE.Color(node.meta_data.color))
      } else if (node.source_tag === 'arxiv' || node.source_tag === 'concept') {
        dummy.scale.set(currentK * baseScale, currentK * baseScale, 1)
        this.nodeMesh.setColorAt(count, new THREE.Color(0x0284c7)) // Light Sky Blue
      } else if (node.source_tag === 'identity' || node.id.startsWith('identity_')) {
        const pulse = 1.2 + Math.sin(Date.now() / 250 + i) * 0.1
        dummy.scale.set(currentK * pulse * baseScale, currentK * pulse * baseScale, 1)
        this.nodeMesh.setColorAt(count, new THREE.Color(0xf59e0b)) // Amber
      } else {
        dummy.scale.set(currentK * baseScale, currentK * baseScale, 1)
        this.nodeMesh.setColorAt(count, new THREE.Color(0x94a3b8)) // Subtle Slate Base
      }
      
      dummy.updateMatrix()
      this.nodeMesh.setMatrixAt(count, dummy.matrix)
      
      count++
    }
    
    if (this.globeMesh) {
      this.globeMesh.visible = hasGeoNodes && this.warpProgress > 0;
      (this.globeMesh.material as THREE.MeshBasicMaterial).opacity = 0.1 * this.warpProgress;
    }
    
    this.nodeMesh.count = count
    this.nodeMesh.instanceMatrix.needsUpdate = true
    if (this.nodeMesh.instanceColor) this.nodeMesh.instanceColor.needsUpdate = true
    
    const positions = this.linkLines.geometry.attributes.position.array as Float32Array
    let lineIdx = 0
    
    for (let i = 0; i < this.links.length; i++) {
      const link = this.links[i]
      const source = link.source
      const target = link.target
      
      if (!source || !target || source.x === undefined || target.x === undefined) continue
      
      this.linkIndexMap[lineIdx] = link
      
      const spx = tx + source.x * k
      const spy = ty + source.y * k
      const tpx = tx + target.x * k
      const tpy = ty + target.y * k
      
      const swx2d = spx - this.width / 2
      const swy2d = -(spy - this.height / 2)
      const twx2d = tpx - this.width / 2
      const twy2d = -(tpy - this.height / 2)
      
      const swx3d = source.x * 6.0
      const swy3d = -source.y * 6.0
      const swz3d = source.z3d * 8.0
      
      const twx3d = target.x * 6.0
      const twy3d = -target.y * 6.0
      const twz3d = target.z3d * 8.0
      
      const swx = swx2d * (1 - this.warpProgress) + swx3d * this.warpProgress
      const swy = swy2d * (1 - this.warpProgress) + swy3d * this.warpProgress
      const swz = 0 * (1 - this.warpProgress) + swz3d * this.warpProgress
      
      const twx = twx2d * (1 - this.warpProgress) + twx3d * this.warpProgress
      const twy = twy2d * (1 - this.warpProgress) + twy3d * this.warpProgress
      const twz = 0 * (1 - this.warpProgress) + twz3d * this.warpProgress
      
      positions[lineIdx * 6 + 0] = swx
      positions[lineIdx * 6 + 1] = swy
      positions[lineIdx * 6 + 2] = swz
      
      positions[lineIdx * 6 + 3] = twx
      positions[lineIdx * 6 + 4] = twy
      positions[lineIdx * 6 + 5] = twz
      
      lineIdx++
    }
    
    this.linkLines.geometry.setDrawRange(0, lineIdx * 2)
    this.linkLines.geometry.attributes.position.needsUpdate = true
    
    const maxActiveSynapses = Math.min(1000, this.links.length)
    if (this.activeSynapses.length < maxActiveSynapses && this.links.length > 0) {
      for (let i = 0; i < 5; i++) {
        if (this.activeSynapses.length >= maxActiveSynapses) break;
        const randomLinkIdx = Math.floor(Math.random() * this.links.length)
        this.activeSynapses.push({
          linkIdx: randomLinkIdx,
          progress: 0,
          speed: 0.005 + Math.random() * 0.015
        })
      }
    }
    
    let synapseCount = 0
    for (let i = this.activeSynapses.length - 1; i >= 0; i--) {
      const syn = this.activeSynapses[i]
      syn.progress += syn.speed
      
      if (syn.progress >= 1.0) {
        this.activeSynapses.splice(i, 1)
        continue
      }
      
      const link = this.links[syn.linkIdx]
      if (!link || !link.source || !link.target || link.source.x === undefined || link.target.x === undefined) {
        this.activeSynapses.splice(i, 1)
        continue
      }
      
      const source = link.source
      const target = link.target
      
      const spx = tx + source.x * k
      const spy = ty + source.y * k
      const tpx = tx + target.x * k
      const tpy = ty + target.y * k
      
      const swx2d = spx - this.width / 2
      const swy2d = -(spy - this.height / 2)
      const twx2d = tpx - this.width / 2
      const twy2d = -(tpy - this.height / 2)
      
      const swx3d = source.x * 6.0
      const swy3d = -source.y * 6.0
      const swz3d = source.z3d * 8.0
      
      const twx3d = target.x * 6.0
      const twy3d = -target.y * 6.0
      const twz3d = target.z3d * 8.0
      
      const swx = swx2d * (1 - this.warpProgress) + swx3d * this.warpProgress
      const swy = swy2d * (1 - this.warpProgress) + swy3d * this.warpProgress
      const swz = 0 * (1 - this.warpProgress) + swz3d * this.warpProgress
      
      const twx = twx2d * (1 - this.warpProgress) + twx3d * this.warpProgress
      const twy = twy2d * (1 - this.warpProgress) + twy3d * this.warpProgress
      const twz = 0 * (1 - this.warpProgress) + twz3d * this.warpProgress
      
      const currentX = swx + (twx - swx) * syn.progress
      const currentY = swy + (twy - swy) * syn.progress
      const currentZ = swz + (twz - swz) * syn.progress
      
      dummy.position.set(currentX, currentY, currentZ)
      
      if (this.isGalaxyMode) {
        dummy.quaternion.copy(this.activeCamera.quaternion)
      } else {
        dummy.quaternion.identity()
      }
      
      const currentK = k * (1 - this.warpProgress) + 1.0 * this.warpProgress
      dummy.scale.set(currentK, currentK, 1)
      dummy.updateMatrix()
      
      this.synapseMesh.setMatrixAt(synapseCount, dummy.matrix)
      synapseCount++
    }
    
    this.synapseMesh.count = synapseCount
    this.synapseMesh.instanceMatrix.needsUpdate = true
    
    for (let i = this.shockwaves.length - 1; i >= 0; i--) {
      const sw = this.shockwaves[i]
      sw.scale += (sw.maxScale - sw.scale) * 0.05 + 0.2
      sw.mesh.scale.set(sw.scale, sw.scale, 1)
      const opacity = 1.0 - (sw.scale / sw.maxScale)
      ;(sw.mesh.material as THREE.MeshBasicMaterial).opacity = Math.max(0, opacity * 0.5) // Reduced intensity
      
      if (opacity <= 0.05) {
        this.scene.remove(sw.mesh)
        sw.mesh.geometry.dispose()
        ;(sw.mesh.material as THREE.Material).dispose()
        this.shockwaves.splice(i, 1)
      }
    }
    
    this.renderer.render(this.scene, this.activeCamera)
  }
  
  public dispose() {
    if (this._animationFrameId) {
      cancelAnimationFrame(this._animationFrameId)
    }
    window.removeEventListener('resize', this.onResize)
    this.renderer.dispose()
  }
  
  public pause() {
    if (this._animationFrameId) {
      cancelAnimationFrame(this._animationFrameId)
      this._animationFrameId = null
    }
  }

  public resume() {
    if (!this._animationFrameId) {
      this.render()
    }
  }

  public start() {
    if (!this._animationFrameId) {
      this.render()
    }
  }
}
