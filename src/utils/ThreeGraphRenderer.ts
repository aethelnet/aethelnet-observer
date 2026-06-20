import * as THREE from 'three'

export class ThreeGraphRenderer {
  canvas: HTMLCanvasElement
  renderer: THREE.WebGLRenderer
  scene: THREE.Scene
  camera: THREE.OrthographicCamera
  
  nodes: any[]
  links: any[]
  
  nodeMesh!: THREE.InstancedMesh
  linkLines!: THREE.LineSegments
  
  width: number
  height: number
  
  globalTransform: { x: number, y: number, k: number }
  
  raycaster: THREE.Raycaster
  mouse: THREE.Vector2
  onClick?: (node: any) => void
  
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
    
    // Setup Scene & Camera (Orthographic to match 2D D3 behavior)
    this.scene = new THREE.Scene()
    this.camera = new THREE.OrthographicCamera(
      this.width / -2, this.width / 2,
      this.height / 2, this.height / -2,
      1, 1000
    )
    this.camera.position.z = 500
    
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
    const geometry = new THREE.CircleGeometry(5, 16)
    const material = new THREE.MeshBasicMaterial({ color: 0xffffff }) // Use white so vertex colors tint it
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
    lineGeo.setAttribute('position', new THREE.BufferAttribute(positions, 3))
    
    const lineMat = new THREE.LineBasicMaterial({ color: 0x444466, transparent: true, opacity: 0.5 })
    this.linkLines = new THREE.LineSegments(lineGeo, lineMat)
    this.scene.add(this.linkLines)
  }
  
  public updateData(nodes: any[], links: any[]) {
    this.nodes = nodes
    this.links = links
  }
  
  private onResize = () => {
    this.width = window.innerWidth
    this.height = window.innerHeight
    this.renderer.setSize(this.width, this.height)
    this.camera.left = this.width / -2
    this.camera.right = this.width / 2
    this.camera.top = this.height / 2
    this.camera.bottom = this.height / -2
    this.camera.updateProjectionMatrix()
  }
  
  public raycast(clientX: number, clientY: number): boolean {
    const node = this.raycastHover(clientX, clientY)
    if (node) {
      if (this.onClick) {
        this.onClick(node)
      }
      return true
    }
    return false
  }

  public raycastHover(clientX: number, clientY: number): any | null {
    this.mouse.x = (clientX / this.width) * 2 - 1
    this.mouse.y = -(clientY / this.height) * 2 + 1
    
    this.raycaster.setFromCamera(this.mouse, this.camera)
    
    const intersects = this.raycaster.intersectObject(this.nodeMesh)
    
    if (intersects.length > 0) {
      const instanceId = intersects[0].instanceId
      if (instanceId !== undefined && this.nodes[instanceId]) {
        return this.nodes[instanceId]
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
    
    const dummy = new THREE.Object3D()
    let count = 0
    
    for (let i = 0; i < this.nodes.length; i++) {
      const node = this.nodes[i]
      // Skip rendering if it's an app node (it will be rendered by DOM)
      // Or we can render a glow underneath it. Let's just render all for now to verify.
      
      const px = tx + (node.x || 0) * k
      const py = ty + (node.y || 0) * k
      
      // Convert DOM to WebGL screen coords
      const wx = px - this.width / 2
      const wy = -(py - this.height / 2) // Invert Y
      
      dummy.position.set(wx, wy, 0)
      
      // Add pulsing for ghost nodes
      if (node.node_type === 'gravity_well') {
        const pulse = 3.0 + Math.sin(Date.now() / 150 + i) * 1.5
        dummy.scale.set(k * pulse, k * pulse, 1)
        // Dark purple/black hole color
        this.nodeMesh.setColorAt(count, new THREE.Color(0x1a0524))
      } else if (node.source_tag === 'ghost') {
        const pulse = 1.0 + Math.sin(Date.now() / 200 + i) * 0.5
        dummy.scale.set(k * pulse, k * pulse, 1)
        this.nodeMesh.setColorAt(count, new THREE.Color(0xff00ff))
      } else {
        dummy.scale.set(k, k, 1)
        this.nodeMesh.setColorAt(count, new THREE.Color(0x00F3FF))
      }
      
      dummy.updateMatrix()
      this.nodeMesh.setMatrixAt(count, dummy.matrix)
      
      count++
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
      
      const spx = tx + source.x * k
      const spy = ty + source.y * k
      const tpx = tx + target.x * k
      const tpy = ty + target.y * k
      
      const swx = spx - this.width / 2
      const swy = -(spy - this.height / 2)
      
      const twx = tpx - this.width / 2
      const twy = -(tpy - this.height / 2)
      
      positions[lineIdx * 6 + 0] = swx
      positions[lineIdx * 6 + 1] = swy
      positions[lineIdx * 6 + 2] = 0
      
      positions[lineIdx * 6 + 3] = twx
      positions[lineIdx * 6 + 4] = twy
      positions[lineIdx * 6 + 5] = 0
      
      lineIdx++
    }
    
    this.linkLines.geometry.setDrawRange(0, lineIdx * 2)
    this.linkLines.geometry.attributes.position.needsUpdate = true
    
    this.renderer.render(this.scene, this.camera)
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
