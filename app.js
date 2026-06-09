/**
 * Aethelnet Unit - GNN Canvas Visualizer
 * Fully responsive 2D physics-based graph rendering.
 */

class SwarmClient {
    constructor() {
        this.wsUrl = 'ws://' + (window.location.hostname || '127.0.0.1') + ':8001/ws';
        this.socket = null;
        this.reconnectTimer = null;
        this.reconnectAttempts = 0;
        
        // DOM Elements
        this.elStatus = document.getElementById('ws-status');
        this.elLight = document.getElementById('ws-light');
        this.elLog = document.getElementById('event-log');
        this.elNodes = document.getElementById('val-nodes');
        this.elBridges = document.getElementById('val-bridges');
        this.elState = document.getElementById('val-state');
        this.elLeader = document.getElementById('val-leader');
        this.canvasContainer = document.getElementById('manifold-canvas');
        
        // Visualizer Physics State
        this.canvas = null;
        this.ctx = null;
        this.nodes = [];
        this.links = [];
        this.selectedNodeId = null;
        
        // Pan & Zoom state
        this.panX = 0;
        this.panY = 0;
        this.zoom = 1.0;
        this.isPanning = false;
        this.startX = 0;
        this.startY = 0;
        this.showGossip = false;
        this.showNetwork = true;
        this.showStream = true;
        this.swarmHistory = [];
        
        // Workbench State
        this.isWiring = false;
        this.wireSourceNode = null;
        this.wireTargetIso = null;
        
        this.init();
    }

    // 2.5D Isometric Projection Math
    toIso(x, y, z = 0) {
        return {
            x: x - y,
            y: (x + y) / 2 - z
        };
    }

    fromIso(isoX, isoY, z = 0) {
        const yBase = isoY + z;
        return {
            x: yBase + isoX / 2,
            y: yBase - isoX / 2
        };
    }

    init() {
        this.log('Initializing Aethelnet Unit...', 'info');
        this.setupCanvas();
        this.connect();
        
        const chkGossip = document.getElementById('chk-gossip');
        if (chkGossip) {
            chkGossip.addEventListener('change', (e) => {
                this.showGossip = e.target.checked;
                this.log(this.showGossip ? 'Showing gossip nodes' : 'Hiding gossip nodes', 'info');
            });
        }

        const chkNetwork = document.getElementById('chk-network');
        if (chkNetwork) {
            chkNetwork.addEventListener('change', (e) => {
                this.showNetwork = e.target.checked;
                this.log(this.showNetwork ? 'Showing network nodes' : 'Hiding network nodes', 'info');
            });
        }

        const chkStream = document.getElementById('chk-stream');
        if (chkStream) {
            chkStream.addEventListener('change', (e) => {
                this.showStream = e.target.checked;
                this.log(this.showStream ? 'Showing live streams' : 'Hiding live streams', 'info');
            });
        }
        
        this.canvas.addEventListener('mousedown', (e) => this.handleMouseDown(e));
        this.canvas.addEventListener('mousemove', (e) => this.handleMouseMove(e));
        this.canvas.addEventListener('mouseup', (e) => this.handleMouseUp(e));
        this.canvas.addEventListener('wheel', (e) => this.handleWheel(e), { passive: false });
        this.canvas.addEventListener('contextmenu', (e) => e.preventDefault()); // Disable right-click menu
        this.canvas.addEventListener('contextmenu', (e) => e.preventDefault());
        
        document.getElementById('btn-reconnect').addEventListener('click', () => {
            if (this.socket && this.socket.readyState === WebSocket.OPEN) {
                this.log('Force syncing...', 'info');
                this.socket.send(JSON.stringify({ type: 'sync_request' }));
            } else {
                this.connect();
            }
        });

        // Removed HTML Inspector DOM Listeners
        
        window.addEventListener('resize', () => this.resizeCanvas());
        
        const tuner = document.getElementById('resonance-tuner');
        if (tuner) {
            let debounceTimer;
            tuner.addEventListener('input', (e) => {
                clearTimeout(debounceTimer);
                debounceTimer = setTimeout(() => {
                    const query = e.target.value.trim();
                    if (this.socket && this.socket.readyState === WebSocket.OPEN && query.length > 0) {
                        this.log(`Tuning resonance to: "${query}"`, 'info');
                        this.socket.send(JSON.stringify({ type: 'tune_resonance', query: query }));
                    }
                }, 500); // 500ms debounce
            });

            // Allow dropping Memory Fragments into the graph via Enter
            tuner.addEventListener('keydown', async (e) => {
                if (e.key === 'Enter') {
                    const query = e.target.value.trim();
                    if (query.length > 0) {
                        this.log(`Injecting Memory Fragment: "${query}"`, 'success');
                        try {
                            const host = window.location.hostname;
                            await fetch(`http://${host || '127.0.0.1'}:8001/api/lgnn/universal_ingest`, {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({
                                    bot_name: "ObserverDashboard",
                                    observation: query
                                })
                            });
                            e.target.value = ''; // Clear after injection
                        } catch (err) {
                            this.log(`Failed to inject fragment: ${err.message}`, 'error');
                        }
                    }
                }
            });
        }
        
        // --- Continuous Time Keystream Sensor ---
        this.keyBuffer = [];
        this.lastKeyTime = Date.now();
        this.keystreamTimer = null;
        
        const flushKeystream = () => {
            if (this.keyBuffer.length > 0) {
                const streamData = JSON.stringify(this.keyBuffer);
                this.keyBuffer = []; // reset
                
                try {
                    const host = window.location.hostname;
                    fetch(`http://${host || '127.0.0.1'}:8001/api/lgnn/universal_ingest`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            bot_name: "Raw_Keystream",
                            observation: `KEYSTREAM_WITH_TIMING: ${streamData}`,
                            confidence: 1.0
                        })
                    });
                    this.log(`[Sensor] Flushed time-series keystream`, 'info');
                } catch (err) {}
            }
        };

        document.addEventListener('keydown', (e) => {
            // Hotkeys for Node Actions
            if (e.target.tagName !== 'INPUT' && e.target.tagName !== 'TEXTAREA') {
                if (e.key === ' ' || e.key === 'Enter') {
                    if (this.selectedNodeId) this.diveIntoNode(this.selectedNodeId);
                    e.preventDefault();
                    return;
                }
                if (e.key === 'Escape') {
                    this.zoomOut();
                    e.preventDefault();
                    return;
                }
                if (e.key === 'c' || e.key === 'C') {
                    if (this.selectedNodeId) this.duplicateNode(this.selectedNodeId);
                    return;
                }
                if (e.key === 's' || e.key === 'S') {
                    if (this.selectedNodeId) this.deploySpider(this.selectedNodeId);
                    return;
                }
                if (e.key === 'f' || e.key === 'F') {
                    if (this.selectedNodes && this.selectedNodes.size > 1) {
                        this.fuseNodes(Array.from(this.selectedNodes));
                    }
                    return;
                }
            }
            
            // Sensor logging
            if (e.key.length > 1 && e.key !== "Backspace") return;
            
            const now = Date.now();
            const deltaMs = now - this.lastKeyTime;
            this.lastKeyTime = now;
            
            let keyObj = e.key === " " ? "[SPACE]" : e.key;
            this.keyBuffer.push([keyObj, deltaMs]);
            
            clearTimeout(this.keystreamTimer);
            
            if (this.keyBuffer.length >= 20) {
                flushKeystream();
            } else {
                // Flush if user pauses for more than 2 seconds
                this.keystreamTimer = setTimeout(flushKeystream, 2000);
            }
        });
        
        // Start animation frame loop
        requestAnimationFrame(() => this.tick());
    }

    setupCanvas() {
        this.canvasContainer.innerHTML = '';
        this.canvas = document.createElement('canvas');
        this.canvasContainer.appendChild(this.canvas);
        this.ctx = this.canvas.getContext('2d');
        this.resizeCanvas();
    }

    resizeCanvas() {
        if (this.canvas) {
            this.canvas.width = this.canvasContainer.clientWidth;
            this.canvas.height = this.canvasContainer.clientHeight;
        }
    }

    updateStatus(text, className) {
        if (this.elStatus) this.elStatus.textContent = text;
        if (this.elLight) {
            this.elLight.className = `indicator-light ${className}`;
        }
    }

    connect() {
        if (this.socket && (this.socket.readyState === WebSocket.CONNECTING || this.socket.readyState === WebSocket.OPEN)) {
            return;
        }
        this.updateStatus('Connecting...', 'connecting');
        try {
            this.socket = new WebSocket(this.wsUrl);
            this.socket.onopen = (e) => this.onOpen(e);
            this.socket.onmessage = (e) => this.onMessage(e);
            this.socket.onclose = (e) => this.onClose(e);
            this.socket.onerror = (e) => this.onError(e);
        } catch (error) {
            this.log(`WS Error: ${error.message}`, 'error');
            this.updateStatus('Disconnected', 'disconnected');
        }
    }

    onOpen() {
        this.reconnectAttempts = 0;
        this.updateStatus('Connected', 'connected');
        this.log('Quantum conduit established with Aethelnet.', 'success');
    }

    onMessage(event) {
        try {
            const data = JSON.parse(event.data);
            if (data.type === 'telemetry') {
                if (this.elNodes) this.elNodes.textContent = data.nodes;
                if (this.elBridges) this.elBridges.textContent = data.bridges;
                if (this.elState) this.elState.textContent = data.state;
                if (this.elLeader) {
                    this.elLeader.textContent = data.leader || 'None';
                    this.elLeader.title = data.leader || 'Calculating...';
                }
                
                if (data.graph) {
                    this.updateGraph(data.graph.nodes, data.graph.links);
                }
            }
        } catch (e) {
            this.log(`Data parse error: ${e.message}`, 'error');
        }
    }

    onClose() {
        this.updateStatus('Disconnected', 'disconnected');
        this.scheduleReconnect();
    }

    onError() {
        this.updateStatus('Error', 'disconnected');
    }

    scheduleReconnect() {
        this.reconnectAttempts++;
        const delay = Math.min(1000 * Math.pow(1.5, this.reconnectAttempts), 5000);
        clearTimeout(this.reconnectTimer);
        this.reconnectTimer = setTimeout(() => this.connect(), delay);
    }

    updateGraph(newNodes, newLinks) {
        // Ignore global updates if we are in a sub-swarm
        if (this.swarmHistory && this.swarmHistory.length > 0) return;
        
        // Keep positions of existing nodes, spawn new ones in center
        const width = this.canvas.width;
        const height = this.canvas.height;
        
        const nodeMap = new Map(this.nodes.map(n => [n.id, n]));
        
        this.nodes = newNodes.map(nn => {
            const existing = nodeMap.get(nn.id);
            return {
                id: nn.id,
                activation: nn.activation,
                is_leader: nn.is_leader || false,
                centrality: nn.centrality || 0.0,
                x: existing ? existing.x : width / 2 + (Math.random() - 0.5) * 4000,
                y: existing ? existing.y : height / 2 + (Math.random() - 0.5) * 4000,
                vx: existing ? existing.vx : (Math.random() - 0.5) * 10.0,
                vy: existing ? existing.vy : (Math.random() - 0.5) * 10.0
            };
        });
        
        this.links = newLinks.map(nl => ({
            source: nl.source,
            target: nl.target,
            weight: nl.weight
        }));
    }

    tick(timestamp) {
        if (!this.lastFrameTime) {
            this.lastFrameTime = timestamp || performance.now();
            this.perfScale = 1.0;
        }
        const now = timestamp || performance.now();
        const dt = now - this.lastFrameTime;
        this.lastFrameTime = now;
        
        const currentFps = 1000 / Math.max(dt, 1);
        if (!this.avgFps) this.avgFps = currentFps;
        this.avgFps = this.avgFps * 0.9 + currentFps * 0.1;
        
        // Auto-scale performance if FPS drops below 20 or is stable above 30
        if (this.avgFps < 20) {
            this.perfScale = Math.max(0.1, this.perfScale - 0.05);
        } else if (this.avgFps > 30) {
            this.perfScale = Math.min(1.0, this.perfScale + 0.01);
        }
        
        const fpsCounter = document.getElementById('fps-counter');
        if (fpsCounter) {
            fpsCounter.textContent = `${Math.round(this.avgFps)} FPS [LOD: ${(this.perfScale*100).toFixed(0)}%]`;
            fpsCounter.style.color = this.avgFps < 15 ? '#E03C31' : (this.avgFps < 25 ? '#F2C12E' : 'var(--accent-blue)');
        }

        this.physicsUpdate();
        this.draw();
        requestAnimationFrame((ts) => this.tick(ts));
    }

    physicsUpdate() {
        if (!this.canvas || this.nodes.length === 0) return;
        
        const width = this.canvas.width;
        const height = this.canvas.height;
        const center = { x: width / 2, y: height / 2 };
        
        // --- TIME DILATION ---
        const timeScale = this.selectedNodeId ? 0.02 : 1.0;
        
        // 1. Semantic Boids Swarm Logic
        const separationDist = 800; // Extreme whitespace
        const cohesionWeight = 0.0002 * timeScale; // Minimal cohesion
        const alignmentWeight = 0.01 * timeScale;
        const separationWeight = 1000 * timeScale; // Softer, wider push
        const maxSpeed = 15.0 * timeScale;
        const centerGravity = 0.000005 * timeScale; // Minimal gravity
        
        const nodeLookup = new Map(this.nodes.map(n => [n.id, n]));
        
        // Pre-calculate neighbor data for fast O(1) lookup
        const neighbors = new Map(this.nodes.map(n => [n.id, new Set()]));
        for (const link of this.links) {
            if (neighbors.has(link.source)) neighbors.get(link.source).add(link.target);
            if (neighbors.has(link.target)) neighbors.get(link.target).add(link.source);
        }

        // --- SPATIAL HASH GRID (O(N) Optimization) ---
        const cellSize = separationDist;
        const grid = new Map();
        for (const n of this.nodes) {
            // Skip hidden nodes from physics calculations
            if (!this.showGossip && n.id.startsWith("Obs_")) continue;
            if (!this.showNetwork && n.id.startsWith("Net_")) continue;
            if (!this.showStream && n.id.startsWith("Stream_")) continue;
            
            const gx = Math.floor(n.x / cellSize);
            const gy = Math.floor(n.y / cellSize);
            const key = `${gx},${gy}`;
            if (!grid.has(key)) grid.set(key, []);
            grid.get(key).push(n);
        }
        
        for (let i = 0; i < this.nodes.length; i++) {
            const n = this.nodes[i];
            
            // Skip hidden nodes
            if (!this.showGossip && n.id.startsWith("Obs_")) continue;
            if (!this.showNetwork && n.id.startsWith("Net_")) continue;
            if (!this.showStream && n.id.startsWith("Stream_")) continue;
            
            if (n.vx === undefined) { n.vx = 0; n.vy = 0; }
            
            let centerOfMassX = 0, centerOfMassY = 0;
            let avgVx = 0, avgVy = 0;
            let separationFx = 0, separationFy = 0;
            let neighborCount = 0;
            
            const nbrIds = neighbors.get(n.id) || new Set();
            
            // 1. Cohesion & Alignment (from topological links)
            for (const nbrId of nbrIds) {
                const neighbor = nodeLookup.get(nbrId);
                if (!neighbor) continue;
                
                centerOfMassX += neighbor.x;
                centerOfMassY += neighbor.y;
                avgVx += neighbor.vx || 0;
                avgVy += neighbor.vy || 0;
                neighborCount++;
            }
            
            // 2. Separation (Spatial Grid O(N) instead of O(N^2))
            const myGx = Math.floor(n.x / cellSize);
            const myGy = Math.floor(n.y / cellSize);
            
            for (let xOff = -1; xOff <= 1; xOff++) {
                for (let yOff = -1; yOff <= 1; yOff++) {
                    const key = `${myGx + xOff},${myGy + yOff}`;
                    const cellNodes = grid.get(key);
                    if (!cellNodes) continue;
                    
                    for (const other of cellNodes) {
                        if (n === other) continue;
                        let dx = n.x - other.x;
                        let dy = n.y - other.y;
                        
                        // Prevent nodes getting permanently stuck on the exact same pixel
                        if (dx === 0 && dy === 0) {
                            dx = (Math.random() - 0.5) * 10.0;
                            dy = (Math.random() - 0.5) * 10.0;
                        }
                        
                        const isNeighbor = nbrIds.has(other.id);
                        const actualSepDist = isNeighbor ? 300 : separationDist;
                        
                        if (Math.abs(dx) > actualSepDist || Math.abs(dy) > actualSepDist) continue;
                        
                        const dist = Math.sqrt(dx * dx + dy * dy) || 1.0;
                        if (dist < actualSepDist) {
                            const weight = isNeighbor ? separationWeight * 0.2 : separationWeight;
                            separationFx += (dx / dist) * (weight / dist);
                            separationFy += (dy / dist) * (weight / dist);
                        }
                    }
                }
            }
            
            // Brutalist Flowchart Grid Snapping
            const GRID_SIZE = 400; // Large rigid blocks
            
            // If the node is pinned/selected, don't force it, but let others snap
            const isSelected = this.selectedNodeId === n.id;
            
            if (!isSelected) {
                const targetX = Math.round(n.x / GRID_SIZE) * GRID_SIZE;
                const targetY = Math.round(n.y / GRID_SIZE) * GRID_SIZE;
                
                // Magnetic force snapping them to the nearest rigid grid point
                n.vx += (targetX - n.x) * 0.1 * timeScale;
                n.vy += (targetY - n.y) * 0.1 * timeScale;
            }
            
            // Separation ensures nodes pushed to the same grid point push each other to the NEXT grid point
            n.vx += separationFx * 3.0;
            n.vy += separationFy * 3.0;
            
            // Gentle center gravity just to keep the grid from drifting infinitely into the void
            n.vx += (center.x - n.x) * 0.000001;
            n.vy += (center.y - n.y) * 0.000001;
            
            // Friction for crystallization (strong dampening to prevent jitter)
            n.vx *= 0.5;
            n.vy *= 0.5;
            
            // Speed limits and freezing (Crystallization)
            const speed = Math.sqrt(n.vx * n.vx + n.vy * n.vy) || 0;
            if (speed > maxSpeed) {
                n.vx = (n.vx / Math.max(speed, 0.1)) * maxSpeed;
                n.vy = (n.vy / Math.max(speed, 0.1)) * maxSpeed;
            } else if (speed < 0.5) {
                // Completely freeze when settled to prevent micro-jittering
                n.vx = 0;
                n.vy = 0;
            }
            
            if (!n.is_pinned) {
                n.x += n.vx;
                n.y += n.vy;
            } else {
                n.vx = 0;
                n.vy = 0;
            }
        }

        // Cinematic Camera Tracking
        if (!this.isPanning && this.nodes.length > 0) {
            let targetX = center.x;
            let targetY = center.y;

            if (this.selectedNodeId) {
                // Track selected node
                const selected = this.nodes.find(n => n.id === this.selectedNodeId);
                if (selected) {
                    targetX = selected.x;
                    targetY = selected.y;
                }
            } else {
                // Track center of mass of the swarm
                let cmX = 0, cmY = 0;
                for (const n of this.nodes) {
                    cmX += n.x;
                    cmY += n.y;
                }
                targetX = cmX / this.nodes.length;
                targetY = cmY / this.nodes.length;
            }

            // Calculate where panX/panY need to be to center targetX/targetY on the screen
            const idealPanX = width / 2 - targetX * this.zoom;
            const idealPanY = height / 2 - targetY * this.zoom;

            // Smooth Lerp
            this.panX += (idealPanX - this.panX) * 0.05;
            this.panY += (idealPanY - this.panY) * 0.05;
        }
    }

    handleMouseDown(e) {
        if (!this.canvas || this.nodes.length === 0) return;
        const rect = this.canvas.getBoundingClientRect();
        const mouseX = e.clientX - rect.left;
        const mouseY = e.clientY - rect.top;
        
        // Convert screen coordinates to graph coordinates by reversing pan and zoom
        const graphX = (mouseX - this.panX) / this.zoom;
        const graphY = (mouseY - this.panY) / this.zoom;
        
        let clickedNode = null;
        for (const n of this.nodes) {
            if (!this.showGossip && n.id.startsWith("Obs_")) continue;
            if (!this.showNetwork && n.id.startsWith("Net_")) continue;
            if (!this.showStream && n.id.startsWith("Stream_")) continue;
            
            const zOffset = n.is_leader ? 300 : (n.id.startsWith("Obs_") ? -200 : 0);
            const iso = this.toIso(n.x, n.y, zOffset);
            const dx = iso.x - graphX;
            const dy = iso.y - graphY;
            const dist = Math.sqrt(dx * dx + dy * dy);
            
            const baseRadius = 8;
            const activationBonus = Math.abs(Math.tanh(n.activation || 0)) * 15;
            const centralityBonus = (n.centrality || 0) * 50;
            const rawR = baseRadius + activationBonus + centralityBonus;
            const radius = Math.max(0.1, rawR / Math.pow(this.zoom, 0.6));
            
            if (dist < radius + 10) {
                clickedNode = n;
                break;
            }
        }
        
        if (e.button === 0 && clickedNode) {
            if (e.altKey) {
                // Workbench: Start Wiring
                this.isWiring = true;
                this.wireSourceNode = clickedNode;
                this.wireTargetIso = { x: graphX, y: graphY };
                return;
            }
            
            this.draggedNode = clickedNode;
            this.isDraggingNode = true;
            clickedNode.is_pinned = true; // Pin the reality anchor

            // Left click on node: Select/Inspect
            if (!this.selectedNodes) this.selectedNodes = new Set();
            
            if (e.shiftKey) {
                this.selectedNodes.add(clickedNode.id);
                this.selectedNodeId = clickedNode.id;
                
                // Multi-select enabled (no HTML title update needed)
            } else {
                this.selectedNodes = new Set([clickedNode.id]);
                this.inspectNode(clickedNode.id);
            }
            // Smoothly auto-zoom in
            this.zoom = 2.0;
        } else if (e.button === 0 && !clickedNode) {
            // Start panning (Don't deselect or hide the window automatically!)
            this.isPanning = true;
            this.startX = e.clientX - this.panX;
            this.startY = e.clientY - this.panY;
        } else if (e.button === 1 || e.button === 2) {
            if (e.button === 2 && clickedNode) {
                clickedNode.is_pinned = false;
                this.log(`Reality anchor lifted. [${clickedNode.id}] unpinned.`, 'info');
                return; // Don't pan
            }
            // Middle or Right click: start panning
            this.isPanning = true;
            this.startX = e.clientX - this.panX;
            this.startY = e.clientY - this.panY;
        }
    }

    handleMouseMove(e) {
        if (this.isWiring) {
            const rect = this.canvas.getBoundingClientRect();
            const mouseX = e.clientX - rect.left;
            const mouseY = e.clientY - rect.top;
            this.wireTargetIso = {
                x: (mouseX - this.panX) / this.zoom,
                y: (mouseY - this.panY) / this.zoom
            };
            return;
        }
        
        if (this.isDraggingNode && this.draggedNode) {
            const rect = this.canvas.getBoundingClientRect();
            const mouseX = e.clientX - rect.left;
            const mouseY = e.clientY - rect.top;
            
            const graphX = (mouseX - this.panX) / this.zoom;
            const graphY = (mouseY - this.panY) / this.zoom;
            
            const n = this.draggedNode;
            const zOffset = n.is_leader ? 300 : (n.id.startsWith("Obs_") ? -200 : 0);
            const flatCoords = this.fromIso(graphX, graphY, zOffset);
            
            this.draggedNode.x = flatCoords.x;
            this.draggedNode.y = flatCoords.y;
            this.draggedNode.vx = 0;
            this.draggedNode.vy = 0;
            return;
        }
        
        if (this.isPanning) {
            this.panX = e.clientX - this.startX;
            this.panY = e.clientY - this.startY;
        }
    }

    handleMouseUp(e) {
        if (this.isWiring) {
            this.isWiring = false;
            if (this.wireSourceNode && this.wireTargetIso) {
                // Find node under wireTargetIso
                let targetNode = null;
                for (const n of this.nodes) {
                    if (!this.showGossip && n.id.startsWith("Obs_")) continue;
                    if (!this.showNetwork && n.id.startsWith("Net_")) continue;
                    if (!this.showStream && n.id.startsWith("Stream_")) continue;
                    if (n.id === this.wireSourceNode.id) continue;
                    
                    const zOffset = n.is_leader ? 300 : (n.id.startsWith("Obs_") ? -200 : 0);
                    const iso = this.toIso(n.x, n.y, zOffset);
                    const dx = iso.x - this.wireTargetIso.x;
                    const dy = iso.y - this.wireTargetIso.y;
                    const dist = Math.sqrt(dx * dx + dy * dy);
                    
                    const baseRadius = 8;
                    const activationBonus = Math.abs(Math.tanh(n.activation || 0)) * 15;
                    const centralityBonus = (n.centrality || 0) * 50;
                    const rawR = baseRadius + activationBonus + centralityBonus;
                    const radius = Math.max(0.1, rawR / Math.pow(this.zoom, 0.6));
                    
                    if (dist < radius + 10) {
                        targetNode = n;
                        break;
                    }
                }
                
                if (targetNode) {
                    // Create link
                    this.links.push({
                        source: this.wireSourceNode.id,
                        target: targetNode.id,
                        weight: 1.0
                    });
                    this.log(`Linked [${this.wireSourceNode.id}] to [${targetNode.id}]`, 'success');
                }
            }
            this.wireSourceNode = null;
            this.wireTargetIso = null;
        }
        
        this.isPanning = false;
        if (this.isDraggingNode) {
            this.isDraggingNode = false;
            this.draggedNode = null;
        }
    }

    handleWheel(e) {
        e.preventDefault();
        const rect = this.canvas.getBoundingClientRect();
        const mouseX = e.clientX - rect.left;
        const mouseY = e.clientY - rect.top;
        
        const graphX = (mouseX - this.panX) / this.zoom;
        const graphY = (mouseY - this.panY) / this.zoom;
        
        const zoomFactor = 1.1;
        if (e.deltaY < 0) {
            this.zoom *= zoomFactor;
            
            // Hard limit if no node selected
            if (this.zoom > 5.0 && !this.selectedNodeId) {
                this.zoom = 5.0;
            }
        } else {
            this.zoom = Math.max(this.zoom / zoomFactor, 0.1);
        }
        
        this.panX = mouseX - graphX * this.zoom;
        this.panY = mouseY - graphY * this.zoom;
    }

    diveIntoNode(nodeId) {
        // Prevent multiple dives
        if (this.isDiving) return;
        this.isDiving = true;
        
        this.log(`Initiating fractal dive into [${nodeId}]...`, 'info');
        
        // Save history for zooming out
        this.swarmHistory.push({
            nodes: [...this.nodes],
            links: [...this.links],
            selectedNodeId: this.selectedNodeId
        });
        
        // Visual Flash
        const flash = document.createElement('div');
        flash.style.position = 'absolute';
        flash.style.top = '0'; flash.style.left = '0';
        flash.style.width = '100vw'; flash.style.height = '100vh';
        flash.style.backgroundColor = '#fff';
        flash.style.zIndex = '9999';
        flash.style.transition = 'opacity 1s ease-out';
        document.body.appendChild(flash);
        
        // Show Zoom Out Button
        const btnZoomOut = document.getElementById('btn-zoomout');
        if (btnZoomOut) btnZoomOut.style.display = 'block';
        
        setTimeout(() => {
            // Reset state
            this.zoom = 0.5;
            this.panX = this.canvas.width / 2;
            this.panY = this.canvas.height / 2;
            
            // Generate fractal children for prototype
            const children = [];
            const links = [];
            for (let i=0; i<15; i++) {
                const childId = `${nodeId}_frag_${i}`;
                children.push({
                    id: childId,
                    activation: Math.random(),
                    centrality: Math.random() * 0.5,
                    x: this.canvas.width / 2 + (Math.random() - 0.5) * 400,
                    y: this.canvas.height / 2 + (Math.random() - 0.5) * 400,
                    vx: (Math.random() - 0.5) * 15.0,
                    vy: (Math.random() - 0.5) * 15.0
                });
                if (i > 0) {
                    links.push({
                        source: children[Math.floor(Math.random() * i)].id,
                        target: childId,
                        weight: Math.random()
                    });
                }
            }
            
            this.nodes = children;
            this.links = links;
            this.selectedNodeId = null;
            
            // Fade out flash
            flash.style.opacity = '0';
            setTimeout(() => {
                document.body.removeChild(flash);
                this.isDiving = false;
            }, 1000);
            
            this.log(`Successfully materialized interior of [${nodeId}]`, 'success');
        }, 100);
    }

    zoomOut() {
        if (this.swarmHistory.length === 0) return;
        
        this.log('Ascending to parent swarm...', 'info');
        
        const previousState = this.swarmHistory.pop();
        this.nodes = previousState.nodes;
        this.links = previousState.links;
        this.selectedNodeId = previousState.selectedNodeId;
        
        this.zoom = 2.0; // Keep it somewhat zoomed so we see what we popped out of
        
        if (this.swarmHistory.length === 0) {
            const btnZoomOut = document.getElementById('btn-zoomout');
            if (btnZoomOut) btnZoomOut.style.display = 'none';
        }
    }

    duplicateNode(nodeId) {
        const source = this.nodes.find(n => n.id === nodeId);
        if (!source) return;
        
        const cloneId = `${source.id}_Clone_${Math.floor(Math.random()*1000)}`;
        const clone = {
            ...source,
            id: cloneId,
            x: source.x + 400, // Offset it by one grid unit right
            y: source.y,
            is_pinned: false,
            activation: 1.0,
            full_data: source.full_data ? JSON.parse(JSON.stringify(source.full_data)) : null
        };
        this.nodes.push(clone);
        this.log(`Duplicated [${nodeId}] -> [${cloneId}]`, 'success');
        
        // Auto-select clone
        this.selectedNodeId = cloneId;
        this.selectedNodes = new Set([cloneId]);
    }

    generateMockImage() {
        const c = document.createElement('canvas');
        c.width = 200; c.height = 200;
        const ctx = c.getContext('2d');
        const r1 = Math.floor(Math.random() * 255);
        const g1 = Math.floor(Math.random() * 255);
        const b1 = Math.floor(Math.random() * 255);
        const grad = ctx.createLinearGradient(0,0,200,200);
        grad.addColorStop(0, `rgb(${r1},${g1},${b1})`);
        grad.addColorStop(1, '#1A1A1A');
        ctx.fillStyle = grad;
        ctx.fillRect(0,0,200,200);
        
        const img = new Image();
        img.src = c.toDataURL();
        return img;
    }

    async deploySpider(nodeId) {
        this.log(`Deploying Autonomous Spider to [${nodeId}]...`, 'info');
        const source = this.nodes.find(n => n.id === nodeId);
        if (!source) return;
        
        // Send a telemetry ping for the backend log, but spawn nodes locally immediately
        try {
            const host = window.location.hostname;
            fetch(`http://${host || '127.0.0.1'}:8001/api/lgnn/universal_ingest`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    bot_name: "AethelSpider",
                    observation: `SPIDER REPORT: Investigating node ${nodeId} for hidden connections and gossip.`,
                    confidence: 0.8
                })
            }).catch(()=>{});
        } catch(e) {}
        
        // Simulate a delay for the spider searching
        setTimeout(() => {
            for (let i = 0; i < 3; i++) {
                const resultId = `SpiderResult_${nodeId}_${i}`;
                this.nodes.push({
                    id: resultId,
                    activation: 0.8,
                    centrality: 0.5,
                    is_pinned: false,
                    is_leader: false,
                    x: source.x + (Math.random() - 0.5) * 800,
                    y: source.y + (Math.random() - 0.5) * 800,
                    full_data: {
                        confidence: 0.6 + Math.random() * 0.3,
                        text_content: `Image Search Result #${i+1} for ${nodeId}`
                    },
                    // We generate a beautiful random abstract gradient for the image search
                    cached_image: this.generateMockImage()
                });
                
                this.links.push({
                    source: source.id,
                    target: resultId,
                    weight: 0.8
                });
            }
            this.log(`Spider returned 3 correlated image results for [${nodeId}]`, 'success');
        }, 800);
    }

    async fuseNodes(nodeIds) {
        if (nodeIds.length < 2) return;
        this.log(`Fusing ${nodeIds.length} nodes into new synthesis...`, 'info');
        const fusionName = `Fusion_${nodeIds[0].substring(0,8)}...`;
        try {
            const host = window.location.hostname;
            await fetch(`http://${host || '127.0.0.1'}:8001/api/lgnn/universal_ingest`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    bot_name: "FusionEngine",
                    observation: `FUSION PROTOCOL: Merged ${nodeIds.join(' + ')}. Synthesized new concept.`,
                    confidence: 1.0
                })
            });
            this.selectedNodes.clear();
            this.selectedNodeId = null;
            this.log(`Fusion complete. Spawning new concept.`, 'success');
        } catch (e) {
            this.log(`Fusion failed: ${e.message}`, 'error');
        }
    }

    async inspectNode(nodeId, forceFormat = null) {
        this.selectedNodeId = nodeId;
        this.log(`Loading node data: ${nodeId}`, 'info');
        
        try {
            const host = window.location.hostname;
            let format = forceFormat || 'AUTO';
            
            const response = await fetch(`http://${host || '127.0.0.1'}:8001/api/lgnn/node/${encodeURIComponent(nodeId)}?format=${format}`);
            if (response.ok) {
                const data = await response.json();
                
                const node = this.nodes.find(n => n.id === nodeId);
                if (node) {
                    node.full_data = data;
                    
                    // If image, pre-load it for canvas
                    if (data.format === 'IMG' && data.media_b64) {
                        const img = new Image();
                        img.src = 'data:image/png;base64,' + data.media_b64;
                        node.cached_image = img;
                    }
                }
            } else {
                this.log(`Failed to inspect node: ${response.status}`, 'error');
            }
        } catch (e) {
            this.log(`Fetch error: ${e.message}`, 'error');
        }
    }

    draw() {
        if (!this.canvas || !this.ctx) return;
        
        const ctx = this.ctx;
        ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        ctx.save();
        
        // Apply pan and zoom
        ctx.translate(this.panX, this.panY);
        ctx.scale(this.zoom, this.zoom);
        
        // Calculate viewport bounds for Off-screen Culling (X220 Performance)
        const vLeft = -this.panX / this.zoom;
        const vRight = (this.canvas.width - this.panX) / this.zoom;
        const vTop = -this.panY / this.zoom;
        const vBottom = (this.canvas.height - this.panY) / this.zoom;
        
        const nodeLookup = new Map(this.nodes.map(n => [n.id, n]));
        
        // 1. Draw Links
        ctx.lineWidth = Math.max(0.5, 2 * this.zoom);
        for (const link of this.links) {
            const n1 = nodeLookup.get(link.source);
            const n2 = nodeLookup.get(link.target);
            if (!n1 || !n2) continue;
            
            const isConnectedToSelected = this.selectedNodeId && (n1.id === this.selectedNodeId || n2.id === this.selectedNodeId);
            
            // Smooth LOD for bridges with Performance Hardware Scaling
            let lodAlpha = 1.0;
            if (!isConnectedToSelected) {
                const perfPenalty = (1.0 - (this.perfScale || 1.0)) * 2.0;
                
                let a1 = 1.0;
                if (!n1.is_leader) {
                    const f1 = 0.8 - (n1.centrality || 0) * 0.7 + perfPenalty;
                    if (this.zoom < f1) a1 = Math.max(0, (this.zoom - 0.05) / (f1 - 0.05));
                }
                let a2 = 1.0;
                if (!n2.is_leader) {
                    const f2 = 0.8 - (n2.centrality || 0) * 0.7 + perfPenalty;
                    if (this.zoom < f2) a2 = Math.max(0, (this.zoom - 0.05) / (f2 - 0.05));
                }
                lodAlpha = Math.min(a1, a2);
                
                // Hard Culling to save draw calls when performance is terrible
                if (this.perfScale < 0.5 && ((n1.centrality || 0) < 0.2 || (n2.centrality || 0) < 0.2)) {
                    lodAlpha = 0;
                }
            }
            if (lodAlpha <= 0.01) continue;
            
            // Skip hidden nodes
            if (!this.showGossip && (n1.id.startsWith("Obs_") || n2.id.startsWith("Obs_"))) continue;
            if (!this.showNetwork && (n1.id.startsWith("Net_") || n2.id.startsWith("Net_"))) continue;
            if (!this.showStream && (n1.id.startsWith("Stream_") || n2.id.startsWith("Stream_"))) continue;

            const z1 = n1.is_leader ? 300 : (n1.id.startsWith("Obs_") ? -200 : 0);
            const z2 = n2.is_leader ? 300 : (n2.id.startsWith("Obs_") ? -200 : 0);
            
            const iso1 = this.toIso(n1.x, n1.y, z1);
            const iso2 = this.toIso(n2.x, n2.y, z2);
            
            // Manhattan Routing (Calculated in 2D, projected to 2.5D)
            const midX = (n1.x + n2.x) / 2;
            const midIso1 = this.toIso(midX, n1.y, z1);
            const midIso2 = this.toIso(midX, n2.y, z2);

            ctx.beginPath();
            ctx.moveTo(iso1.x, iso1.y);
            ctx.lineTo(midIso1.x, midIso1.y);
            ctx.lineTo(midIso2.x, midIso2.y);
            ctx.lineTo(iso2.x, iso2.y);
            
            // Constellation Focus Logic
            
            if (this.selectedNodeId) {
                if (isConnectedToSelected) {
                    // Stark black lines for the direct constellation
                    ctx.strokeStyle = `rgba(26, 26, 26, ${0.8 * lodAlpha})`;
                    ctx.lineWidth = 2 / this.zoom;
                } else {
                    // Extremely faint for background context
                    ctx.strokeStyle = `rgba(26, 26, 26, ${0.05 * lodAlpha})`;
                    ctx.lineWidth = 0.5 / this.zoom;
                }
            } else {
                // Default view: Faint hints of structure
                ctx.strokeStyle = `rgba(26, 26, 26, ${(0.05 + link.weight * 0.15) * lodAlpha})`;
                ctx.lineWidth = 1 / this.zoom;
            }
            
            ctx.stroke();
        }
        
        // Draw temporary workbench wire
        if (this.isWiring && this.wireSourceNode && this.wireTargetIso) {
            const z1 = this.wireSourceNode.is_leader ? 300 : (this.wireSourceNode.id.startsWith("Obs_") ? -200 : 0);
            const iso1 = this.toIso(this.wireSourceNode.x, this.wireSourceNode.y, z1);
            
            ctx.beginPath();
            ctx.moveTo(iso1.x, iso1.y);
            ctx.lineTo(this.wireTargetIso.x, this.wireTargetIso.y);
            ctx.strokeStyle = '#F2C12E'; // Yellow highlight wire
            ctx.lineWidth = 2 / this.zoom;
            ctx.setLineDash([5 / this.zoom, 5 / this.zoom]);
            ctx.stroke();
            ctx.setLineDash([]);
        }
        
        // 2. Draw Nodes
        for (const n of this.nodes) {
            // Skip drawing if node type is hidden
            if (!this.showGossip && n.id.startsWith("Obs_")) continue;
            if (!this.showNetwork && n.id.startsWith("Net_")) continue;
            if (!this.showStream && n.id.startsWith("Stream_")) continue;
            
            // Smooth LOD: Fade unimportant worker nodes smoothly when zoomed out
            const isSelected = this.selectedNodeId === n.id;
            let lodAlpha = 1.0;
            
            if (!isSelected && !n.is_leader) {
                const perfPenalty = (1.0 - (this.perfScale || 1.0)) * 2.0;
                const fadeStartZoom = 0.8 - (n.centrality || 0) * 0.7 + perfPenalty;
                
                if (this.zoom < fadeStartZoom) {
                    lodAlpha = Math.max(0, (this.zoom - 0.05) / (fadeStartZoom - 0.05));
                }
                
                if (this.perfScale < 0.5 && (n.centrality || 0) < 0.2) {
                    lodAlpha = 0;
                }
            }
            
            if (lodAlpha <= 0.01) continue; // Skip rendering entirely if invisible
            
            // Nodes are bigger now for the inline text
            const baseRadius = 25;
            const activationBonus = Math.abs(Math.tanh(n.activation || 0)) * 25;
            const centralityBonus = (n.centrality || 0) * 50;
            const rawR = baseRadius + activationBonus + centralityBonus;
            // Radius scales slightly with zoom but not 1:1
            const r = Math.max(0.1, rawR / Math.pow(this.zoom, 0.6)); 
            
            // Iso Projection
            const zOffset = n.is_leader ? 300 : (n.id.startsWith("Obs_") ? -200 : 0);
            const iso = this.toIso(n.x, n.y, zOffset);
            
            // Off-screen Culling (Massive performance boost when zoomed in)
            if (iso.x + r < vLeft || iso.x - r > vRight || iso.y + r < vTop || iso.y - r > vBottom) {
                continue;
            }
            
            // Dim nodes that are not part of the active constellation
            const isFocused = !this.selectedNodeId || n.id === this.selectedNodeId || 
                              this.links.some(l => (l.source === n.id && l.target === this.selectedNodeId) || 
                                                 (l.target === n.id && l.source === this.selectedNodeId));
            
            ctx.globalAlpha = (isFocused ? 1.0 : 0.2) * lodAlpha;
            
            ctx.beginPath();
            ctx.arc(iso.x, iso.y, r, 0, 2 * Math.PI);
            
            // Bauhaus Colors based on node type
            ctx.shadowBlur = 0; // No glowing in Bauhaus!
            
            if (n.id === this.selectedNodeId) {
                ctx.fillStyle = '#F2C12E'; // Yellow highlight
                ctx.strokeStyle = '#1A1A1A'; // Black border
                ctx.lineWidth = 3 / this.zoom;
            } else if (n.is_leader || n.id.startsWith('Nightmare')) {
                ctx.fillStyle = '#E03C31'; // Red for leaders/nightmares
                ctx.strokeStyle = '#1A1A1A';
                ctx.lineWidth = 1.5 / this.zoom;
            } else if (n.id.startsWith("Net_") || n.id.startsWith("Stream_")) {
                ctx.fillStyle = '#005096'; // Blue net/stream
                ctx.strokeStyle = '#1A1A1A';
                ctx.lineWidth = 1.5 / this.zoom;
            } else {
                ctx.fillStyle = '#FFFFFF'; // White default
                ctx.strokeStyle = '#1A1A1A';
                ctx.lineWidth = 1.5 / this.zoom;
            }
            
            ctx.fill();
            ctx.stroke();
            
            ctx.globalAlpha = 1.0; // reset for labels
            
            // Check if we are zoomed in deep enough to render the inner content
            if (this.zoom > 3.0 && isFocused && n.full_data) {
                ctx.save();
                ctx.beginPath();
                ctx.arc(iso.x, iso.y, r, 0, 2 * Math.PI);
                ctx.clip(); // Restrict drawing to inside the circle
                
                // Draw background image if it exists
                if (n.cached_image) {
                    ctx.drawImage(n.cached_image, iso.x - r, iso.y - r, r*2, r*2);
                    // Add dark overlay for text readability
                    ctx.fillStyle = "rgba(0,0,0,0.6)";
                    ctx.fillRect(iso.x - r, iso.y - r, r*2, r*2);
                }
                
                ctx.fillStyle = n.cached_image ? "#FFFFFF" : "#1A1A1A";
                const fontSize = Math.max(2, r / 12);
                ctx.font = `bold ${fontSize}px 'Inter', sans-serif`;
                ctx.textAlign = "center";
                ctx.textBaseline = "middle";
                
                // Word wrapping inside the circle
                const text = n.full_data.text_content || n.id;
                const words = text.split(' ');
                let line = '';
                const lines = [];
                const maxWidth = r * 1.5;
                
                for(let j = 0; j < words.length; j++) {
                    const testLine = line + words[j] + ' ';
                    const metrics = ctx.measureText(testLine);
                    if (metrics.width > maxWidth && j > 0) {
                        lines.push(line);
                        line = words[j] + ' ';
                    } else {
                        line = testLine;
                    }
                }
                lines.push(line);
                
                const lineHeight = fontSize * 1.2;
                const totalHeight = lines.length * lineHeight;
                let startY = iso.y - (totalHeight / 2) + (lineHeight / 2);
                
                // Draw the wrapped text
                for (let j = 0; j < lines.length; j++) {
                    ctx.fillText(lines[j].trim(), iso.x, startY + (j * lineHeight));
                }
                
                // Draw Confidence Meta Tag at the bottom
                ctx.font = `bold ${fontSize * 0.7}px 'Inter', monospace`;
                ctx.fillStyle = n.cached_image ? "#F2C12E" : "#E03C31";
                ctx.fillText(`CONF: ${(n.full_data.confidence * 100).toFixed(0)}%`, iso.x, iso.y + r - (fontSize * 1.5));
                
                ctx.restore();
                
            } else if (this.zoom > 0.8 && isFocused) {
                // X220 Performance Safeguard: Text rendering is incredibly slow.
                // If FPS is bad, don't draw text labels for unimportant nodes unless zoomed in very close!
                if (this.perfScale < 0.8 && this.zoom < 2.5 && !n.is_leader && (n.centrality || 0) < 0.8) {
                    continue; 
                }

                // Minimalistic text label (default view)
                ctx.fillStyle = "#1A1A1A"; // Dark text for Light Mode
                const fontSize = Math.min(12, Math.max(6, (r * 0.4))) / this.zoom;
                ctx.font = `bold ${fontSize}px 'Inter', sans-serif`;
                ctx.textAlign = "center";
                ctx.textBaseline = "middle";
                
                const label = (n.label || n.id || '').split('_').pop().substring(0, 15);
                ctx.fillText(label, iso.x, iso.y);
            }
        }
        
        ctx.restore();
    }

    log(message, type = 'info') {
        const time = new Date().toLocaleTimeString('en-US', { hour12: false });
        const el = document.createElement('div');
        el.className = 'log-entry';
        el.innerHTML = `<span class="log-time">[${time}]</span><span class="log-msg ${type}">${message}</span>`;
        this.elLog.appendChild(el);
        this.elLog.scrollTop = this.elLog.scrollHeight;
        while (this.elLog.children.length > 50) {
            this.elLog.removeChild(this.elLog.firstChild);
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.swarmClient = new SwarmClient();
});
