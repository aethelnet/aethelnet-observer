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
      color: 0x00F3FF, 
      transparent: true, 
      opacity: 1.0, 
      blending: THREE.AdditiveBlending 
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
    // Increase threshold to make clicking tiny dots easier
    this.raycaster.params.Points.threshold = 10
    this.raycaster.params.Line.threshold = 10
    // Wait, InstancedMesh with CircleGeometry uses mesh intersection. Circle is small (radius 5).
    // Let's just use standard mesh intersection.
    
    this.mouse = new THREE.Vector2()
    
    this.initMeshes()
    
    // Handle resize
    window.addEventListener('resize', this.onResize)
    
    this.start()
  }
  
  private initMeshes() {
    // 1. Instanced Mesh for Nodes
    // Max nodes buffer: let's say 10000
    const maxNodes = 10000
    // Use a PlaneGeometry instead of CircleGeometry for the shader
    const geometry = new THREE.PlaneGeometry(10, 10)
    const material = new THREE.MeshBasicMaterial({ 
      color: 0xffffff, 
      transparent: true, 
      opacity: 1.0, 
      blending: THREE.AdditiveBlending,
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
         
         // Smooth outer glow
         float alpha = smoothstep(0.5, 0.2, dist);
         
         // Inner bright core
         float core = smoothstep(0.25, 0.0, dist);
         
         // Edge ring (glass-like rim lighting)
         float rim = smoothstep(0.4, 0.45, dist) * smoothstep(0.5, 0.45, dist);
         
         vec3 coreColor = mix(diffuseColor.rgb, vec3(1.0), core);
         diffuseColor.rgb = coreColor * 1.5 + (diffuseColor.rgb * rim * 3.0); // Boost intensity and rim
         diffuseColor.a *= (alpha * 0.7 + rim + core);
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
    const positions = new Float32Array(maxLinks * 2 * 3) // 2 vertices per line, 3 coords per vertex
    const progress = new Float32Array(maxLinks * 2)
    for (let i = 0; i < maxLinks; i++) {
        progress[i * 2] = 0.0
        progress[i * 2 + 1] = 1.0
    }
    
    lineGeo.setAttribute('position', new THREE.BufferAttribute(positions, 3))
    lineGeo.setAttribute('aProgress', new THREE.BufferAttribute(progress, 1))
    
    const lineMat = new THREE.LineBasicMaterial({ 
      color: 0x4ade80, // Base accent color
      transparent: true, 
      opacity: 0.6,
      blending: THREE.AdditiveBlending
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
         // Create a flowing pulse effect along the line (Spider-silk data transfer)
         float speed = uTime * 1.5;
         float pulse1 = sin((vProgress - speed) * 30.0);
         float pulse2 = sin((vProgress + speed * 0.5) * 15.0);
         
         // Make the edges fade out at the very ends so they blend smoothly into the nodes
         float edgeFade = smoothstep(0.0, 0.15, vProgress) * smoothstep(1.0, 0.85, vProgress);
         
         // Boost brightness on pulse
         float glow = max(0.0, pulse1 * 0.7 + pulse2 * 0.3);
         
         // Color shifting
         vec3 pulseColor = mix(diffuseColor.rgb, vec3(0.0, 1.0, 0.8), glow);
         
         diffuseColor.rgb = pulseColor + (vec3(1.0) * glow * 0.8);
         diffuseColor.a *= (0.2 + 0.8 * glow) * edgeFade;
        `
      )
    }
    
    this.linkLines = new THREE.LineSegments(lineGeo, lineMat)
    this.scene.add(this.linkLines)
    
    // 3. Planeswalker Synapses (Particles moving on links)
    const synapseGeo = new THREE.PlaneGeometry(6, 6)
    const synapseMat = new THREE.MeshBasicMaterial({ 
      color: 0x00FFCC, 
      transparent: true, 
      opacity: 1.0, 
      blending: THREE.AdditiveBlending,
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
         
         // Intense neon spark
         float core = smoothstep(0.1, 0.0, dist);
         float flare = 0.05 / (dist + 0.001);
         float alpha = clamp(flare, 0.0, 1.0) * smoothstep(0.5, 0.0, dist);
         
         diffuseColor.rgb = mix(diffuseColor.rgb * flare, vec3(1.0), core);
         diffuseColor.a *= alpha + core;
        `
      )
    }
    
    this.synapseMesh = new THREE.InstancedMesh(synapseGeo, synapseMat, maxLinks)
    this.synapseMesh.instanceMatrix.setUsage(THREE.DynamicDrawUsage)
    this.scene.add(this.synapseMesh)
    
    // 4. Background Starfield
    const starGeo = new THREE.BufferGeometry()
    const starPositions = new Float32Array(5000 * 3)
    const starColors = new Float32Array(5000 * 3)
    for (let i = 0; i < 5000 * 3; i+=3) {
      starPositions[i] = (Math.random() - 0.5) * 4000
      starPositions[i+1] = (Math.random() - 0.5) * 4000
      starPositions[i+2] = (Math.random() - 0.5) * 4000
      
      // Slight blueish tint for stars
      starColors[i] = 0.5 + Math.random() * 0.5
      starColors[i+1] = 0.7 + Math.random() * 0.3
      starColors[i+2] = 0.9 + Math.random() * 0.1
    }
    starGeo.setAttribute('position', new THREE.BufferAttribute(starPositions, 3))
    starGeo.setAttribute('color', new THREE.BufferAttribute(starColors, 3))
    
    const starMat = new THREE.PointsMaterial({ 
      size: 2, 
      vertexColors: true, 
      transparent: true,
      opacity: 0,
      sizeAttenuation: true,
      blending: THREE.AdditiveBlending,
      depthWrite: false
    })
    
    // Starfield Shader to make stars round
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

    // Add Wireframe Cyber-Globe
    const globeGeo = new THREE.SphereGeometry(300, 32, 32)
    const globeMat = new THREE.MeshBasicMaterial({
      color: 0x10b981,
      wireframe: true,
      transparent: true,
      opacity: 0.15,
      blending: THREE.AdditiveBlending,
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
    
    // Reset warp
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
    
    // Check nodes first
    const intersects = this.raycaster.intersectObject(this.nodeMesh)
    
    if (intersects.length > 0) {
      const instanceId = intersects[0].instanceId
      if (instanceId !== undefined && this.nodes[instanceId]) {
        return { type: 'node', data: this.nodes[instanceId] }
      }
    }
    
    // Check links
    const linkIntersects = this.raycaster.intersectObject(this.linkLines)
    if (linkIntersects.length > 0) {
      // For LineSegments, the faceIndex isn't used, but index gives the vertex index.
      // Since there are 2 vertices per segment, the segment index is Math.floor(index / 2)
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
    
    // The OrthographicCamera is centered at (0,0), but CSS/DOM translates from top-left.
    // We map D3 coordinates (x,y) to WebGL coordinates.
    // WebGL: (0,0) is center. x right, y up.
    // DOM: (0,0) is top-left. x right, y down.
    
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
      (this.starfield.material as THREE.PointsMaterial).opacity = this.warpProgress * 0.8
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
      
      // Calculate 2D position (Graph Mode)
      const px2d = tx + (node.x || 0) * k
      const py2d = ty + (node.y || 0) * k
      const wx2d = px2d - this.width / 2
      const wy2d = -(py2d - this.height / 2)
      
      // Calculate 3D position (Galaxy Mode)
      // Generate a stable pseudo-random z-depth based on node ID
      if (node.z3d === undefined) {
        let hash = 0;
        const str = node.id || 'unknown';
        for (let j = 0; j < str.length; j++) hash = Math.imul(31, hash) + str.charCodeAt(j) | 0;
        node.z3d = (hash % 1000) - 500; // -500 to 500 spread
      }
      
      let wx3d = (node.x || 0) * 6.0
      let wy3d = -(node.y || 0) * 6.0
      let wz3d = node.z3d * 8.0

      // Map Geo-Anchors to the 3D Sphere
      let isGeoNode = false;
      if (node.source_tag === 'geo' && node.meta_data?.spatial) {
        isGeoNode = true;
        const lat = node.meta_data.spatial.lat * (Math.PI / 180);
        const lng = node.meta_data.spatial.lng * (Math.PI / 180);
        const radius = 300;
        // Standard spherical coordinate projection (Three.js coordinates: Y is up)
        wx3d = radius * Math.cos(lat) * Math.sin(lng);
        wy3d = radius * Math.sin(lat);
        wz3d = radius * Math.cos(lat) * Math.cos(lng);
      }
      
      if (isGeoNode) hasGeoNodes = true;
      
      // Interpolate based on warpProgress
      const wx = wx2d * (1 - this.warpProgress) + wx3d * this.warpProgress
      const wy = wy2d * (1 - this.warpProgress) + wy3d * this.warpProgress
      const wz = 0 * (1 - this.warpProgress) + wz3d * this.warpProgress
      
      // Scale interpolates too (we don't want D3 transform 'k' to apply in 3D)
      const currentK = k * (1 - this.warpProgress) + 1.0 * this.warpProgress
      
      dummy.position.set(wx, wy, wz)
      
      // Billboard to face active camera
      if (this.isGalaxyMode) {
        dummy.quaternion.copy(this.activeCamera.quaternion)
      } else {
        dummy.quaternion.identity()
      }
      
      // Vektorfield Alignment: Dynamic glowing sizes and colors
      const baseScale = node.size ? Math.min(node.size * 0.5, 3.0) : 1.2; // Slightly larger base scale, capped at 3.0
      
      // Setup dynamic coloring with premium neon colors
      if (node.isSelected) {
        const pulse = 2.0 + Math.sin(Date.now() / 150 + i) * 0.4
        dummy.scale.set(currentK * pulse * baseScale, currentK * pulse * baseScale, 1)
        this.nodeMesh.setColorAt(count, new THREE.Color(0x00f3ff)) // Neon Cyan
      } else if (node.meta_data?.is_shielded) {
        dummy.scale.set(currentK * baseScale, currentK * baseScale, 1)
        this.nodeMesh.setColorAt(count, new THREE.Color(0x14b8a6)) // Teal for shielded Incubator nodes
      } else if (node.node_type === 'gravity_well') {
        const pulse = 3.0 + Math.sin(Date.now() / 200 + i) * 1.0
        dummy.scale.set(currentK * pulse * baseScale, currentK * pulse * baseScale, 1)
        this.nodeMesh.setColorAt(count, new THREE.Color(0xb5179e)) // Deep Neon Purple
      } else if (node.source_tag === 'ghost') {
        const pulse = 1.0 + Math.sin(Date.now() / 100 + i) * 0.8
        dummy.scale.set(currentK * pulse * baseScale, currentK * pulse * baseScale, 1)
        this.nodeMesh.setColorAt(count, new THREE.Color(0xff0a54)) // Hot Pink / Neon Red
      } else if (node.source_tag === 'spider' || node.source_tag === 'spider_swarm') {
        dummy.scale.set(currentK * baseScale, currentK * baseScale, 1)
        this.nodeMesh.setColorAt(count, new THREE.Color(0x34d399)) // Emerald Teal
      } else if (node.node_type === 'abstract' || node.id.startsWith('Hub_') || node.id.startsWith('Core_') || node.id.startsWith('Mechanism_') || node.id.startsWith('Metaphor_')) {
        dummy.scale.set(currentK * baseScale * 0.8, currentK * baseScale * 0.8, 1)
        this.nodeMesh.setColorAt(count, new THREE.Color(0x94a3b8)) // Slate Glass (dimmer engine nodes)
      } else if (node.source_tag === 'app' || node.source_tag === 'tool') {
        dummy.scale.set(currentK * baseScale * 1.2, currentK * baseScale * 1.2, 1)
        this.nodeMesh.setColorAt(count, new THREE.Color(0x818cf8)) // Indigo Glass
      } else if (node.meta_data?.color) {
        dummy.scale.set(currentK * baseScale, currentK * baseScale, 1)
        this.nodeMesh.setColorAt(count, new THREE.Color(node.meta_data.color))
      } else if (node.source_tag === 'arxiv' || node.source_tag === 'concept') {
        dummy.scale.set(currentK * baseScale, currentK * baseScale, 1)
        this.nodeMesh.setColorAt(count, new THREE.Color(0x38bdf8)) // Sky Teal
      } else if (node.source_tag === 'identity' || node.id.startsWith('identity_')) {
        const pulse = 1.5 + Math.sin(Date.now() / 250 + i) * 0.3
        dummy.scale.set(currentK * pulse * baseScale, currentK * pulse * baseScale, 1)
        this.nodeMesh.setColorAt(count, new THREE.Color(0xfee440)) // Neon Gold (keep identity prominent)
      } else {
        dummy.scale.set(currentK * baseScale, currentK * baseScale, 1)
        this.nodeMesh.setColorAt(count, new THREE.Color(0x2dd4bf)) // Base Light Glass Teal
      }
      
      dummy.updateMatrix()
      this.nodeMesh.setMatrixAt(count, dummy.matrix)
      
      count++
    }
    
    // Toggle globe visibility
    if (this.globeMesh) {
      this.globeMesh.visible = hasGeoNodes && this.warpProgress > 0;
      (this.globeMesh.material as THREE.MeshBasicMaterial).opacity = 0.15 * this.warpProgress;
    }
    
    this.nodeMesh.count = count
    this.nodeMesh.instanceMatrix.needsUpdate = true
    if (this.nodeMesh.instanceColor) this.nodeMesh.instanceColor.needsUpdate = true
    
    // Update Links
    const positions = this.linkLines.geometry.attributes.position.array as Float32Array
    let lineIdx = 0
    
    for (let i = 0; i < this.links.length; i++) {
      const link = this.links[i]
      const source = link.source
      const target = link.target
      
      if (!source || !target || source.x === undefined || target.x === undefined) continue
      
      this.linkIndexMap[lineIdx] = link
      
      // 2D Line coords
      const spx = tx + source.x * k
      const spy = ty + source.y * k
      const tpx = tx + target.x * k
      const tpy = ty + target.y * k
      
      const swx2d = spx - this.width / 2
      const swy2d = -(spy - this.height / 2)
      const twx2d = tpx - this.width / 2
      const twy2d = -(tpy - this.height / 2)
      
      // 3D Line coords
      const swx3d = source.x * 6.0
      const swy3d = -source.y * 6.0
      const swz3d = source.z3d * 8.0
      
      const twx3d = target.x * 6.0
      const twy3d = -target.y * 6.0
      const twz3d = target.z3d * 8.0
      
      // Interpolate
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
    
    // Update Synapses (Data Packets)
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
    
    // Render shockwaves (Synaptic Pulse)
    for (let i = this.shockwaves.length - 1; i >= 0; i--) {
      const sw = this.shockwaves[i]
      sw.scale += (sw.maxScale - sw.scale) * 0.05 + 0.2
      sw.mesh.scale.set(sw.scale, sw.scale, 1)
      const opacity = 1.0 - (sw.scale / sw.maxScale)
      ;(sw.mesh.material as THREE.MeshBasicMaterial).opacity = Math.max(0, opacity)
      
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
