/**
 * Aethelnet Unit - GNN Canvas Visualizer
 * Fully responsive 2D physics-based graph rendering.
 */

class SwarmClient {
    constructor() {
        const host = window.location.hostname || 'localhost';
        this.wsUrl = `ws://${host}:8001/ws`;
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
        this.elAethel = document.getElementById('val-aethel');
        this.canvasContainer = document.getElementById('manifold-canvas');

        // Web Components HUD
        this.compStatus = document.getElementById('system-status-widget');
        this.compNodes = document.getElementById('metric-nodes');
        this.compBridges = document.getElementById('metric-bridges');
        this.compState = document.getElementById('metric-state');
        
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
        this.isCameraTracking = true;
        this.showGossip = false;
        this.showNetwork = true;
        this.showStream = true;
        this.swarmHistory = [];
        
        // Workbench State
        this.isWiring = false;
        this.wireSourceNode = null;
        this.wireTargetIso = null;

        // Custom Visual & Dynamic parameters state
        this.activePersonaNodes = new Set();
        this.isSpiderHunting = false;
        this.spiderPulseRadius = 0;
        this.selectedNodes = new Set();
        this.radialMenu = {
            active: false,
            x: 0,
            y: 0,
            nodeId: null,
            options: []
        };
        
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
        const chkWorkbench = document.getElementById('chk-workbench');
        if (chkWorkbench) {
            chkWorkbench.addEventListener('change', (e) => {
                this.isWorkbenchMode = e.target.checked;
                this.log(this.isWorkbenchMode ? 'Entered WORKBENCH MODE' : 'Exited WORKBENCH MODE', 'success');
            });
        }
        
        this.canvas.addEventListener('mousedown', (e) => this.handleMouseDown(e));
        this.canvas.addEventListener('mousemove', (e) => this.handleMouseMove(e));
        this.canvas.addEventListener('mouseup', (e) => this.handleMouseUp(e));
        this.canvas.addEventListener('wheel', (e) => this.handleWheel(e), { passive: false });
        
        // Context Menu Radial Trigger
        this.canvas.addEventListener('contextmenu', (e) => {
            e.preventDefault();
            const rect = this.canvas.getBoundingClientRect();
            const mouseX = e.clientX - rect.left;
            const mouseY = e.clientY - rect.top;
            
            const graphX = (mouseX - this.panX) / this.zoom;
            const graphY = (mouseY - this.panY) / this.zoom;
            
            let targetNode = null;
            for (const n of this.nodes) {
                const zOffset = n.is_leader ? 300 : (n.id.startsWith("Obs_") ? -200 : 0);
                const iso = this.toIso(n.x, n.y, zOffset);
                const dx = iso.x - graphX;
                const dy = iso.y - graphY;
                const dist = Math.sqrt(dx*dx + dy*dy);
                
                const baseRadius = 25;
                const activationBonus = Math.abs(Math.tanh(n.activation || 0)) * 25;
                const centralityBonus = (n.centrality || 0) * 50;
                const radius = Math.max(0.1, (baseRadius + activationBonus + centralityBonus) / Math.pow(this.zoom, 0.6));
                
                if (dist < radius + 25) {
                    targetNode = n;
                    break;
                }
            }
            
            this.radialMenu.active = true;
            this.radialMenu.x = e.clientX;
            this.radialMenu.y = e.clientY;
            
            if (targetNode) {
                this.radialMenu.nodeId = targetNode.id;
                this.radialMenu.options = ["Inspect", "Link Source", "Pin/Unpin", "Delete Node"];
            } else {
                this.radialMenu.nodeId = null;
                this.radialMenu.options = ["Spawn Node", "Force Sync", "Close Menu"];
            }
        });
        
        // Double-click to create new node
        this.canvas.addEventListener('dblclick', (e) => {
            const rect = this.canvas.getBoundingClientRect();
            const mouseX = e.clientX - rect.left;
            const mouseY = e.clientY - rect.top;
            
            const graphX = (mouseX - this.panX) / this.zoom;
            const graphY = (mouseY - this.panY) / this.zoom;
            const flatCoords = this.fromIso(graphX, graphY, 0);

            const label = prompt("Enter text content for the new GNN Node:");
            if (label && label.trim().length > 0) {
                const nodeName = prompt("Enter a unique name/ID for this node (optional):", "Node_" + Math.floor(Math.random()*1000));
                if (nodeName && nodeName.trim().length > 0) {
                    this.log(`Creating manual GNN Node: [${nodeName}]`, 'info');
                    this.createNode(nodeName, label.trim(), flatCoords.x, flatCoords.y);
                }
            }
        });
        
        document.getElementById('btn-reconnect').addEventListener('click', () => {
            if (this.socket && this.socket.readyState === WebSocket.OPEN) {
                this.log('Force syncing...', 'info');
                this.socket.send(JSON.stringify({ type: 'sync_request' }));
            } else {
                this.connect();
            }
        });

        // Live-Sync Auto-Saving Node Content
        const contentArea = document.getElementById('inspector-content');
        if (contentArea) {
            let autoSaveTimer;
            contentArea.addEventListener('input', () => {
                clearTimeout(autoSaveTimer);
                autoSaveTimer = setTimeout(async () => {
                    if (!this.selectedNodeId) return;
                    const newContent = contentArea.value;
                    
                    try {
                        const apiHost = window.location.hostname === 'localhost' ? 'localhost' : window.location.hostname;
                        await fetch(`http://${apiHost}:8001/api/lgnn/node/update`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                id: this.selectedNodeId,
                                text_content: newContent
                            })
                        });
                        
                        // Update local node full_data
                        const node = this.nodes.find(n => n.id === this.selectedNodeId);
                        if (node && node.full_data) {
                            node.full_data.text_content = newContent;
                        }
                    } catch (err) {}
                }, 800); // 800ms debounce
            });
        }

        // Bind Spider Hunt Controller
        const btnDeploySpider = document.getElementById('btn-deploy-spider');
        const inputSpider = document.getElementById('spider-query');
        if (btnDeploySpider && inputSpider) {
            btnDeploySpider.addEventListener('click', async () => {
                const query = inputSpider.value.trim();
                if (query.length === 0) return;
                
                this.log(`Deploying ArXiv Spider for hunt: "${query}"`, 'info');
                try {
                    const apiHost = window.location.hostname === 'localhost' ? 'localhost' : window.location.hostname;
                    const res = await fetch(`http://${apiHost}:8001/api/lgnn/universal_ingest`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            bot_name: "AethelSpider_ArXiv",
                            observation: query
                        })
                    });
                    if (res.ok) {
                        this.log(`Spider deployed. Mining results in background...`, 'success');
                        inputSpider.value = '';
                        this.isSpiderHunting = true;
                        this.spiderPulseRadius = 0;
                        if (this.spiderTimer) clearTimeout(this.spiderTimer);
                        this.spiderTimer = setTimeout(() => {
                            this.isSpiderHunting = false;
                            this.spiderTimer = null;
                        }, 12000); // Pulse for 12 seconds
                    } else {
                        this.log(`Failed to deploy spider`, 'error');
                    }
                } catch (e) {
                    this.log(`Deploy error: ${e.message}`, 'error');
                }
            });
        }

        // Bind Persona Creator from Multi-Selection
        const btnCreatePersona = document.getElementById('btn-create-persona');
        if (btnCreatePersona) {
            btnCreatePersona.addEventListener('click', async () => {
                if (!this.selectedNodes || this.selectedNodes.size === 0) {
                    alert("Please select one or more nodes first (Hold Shift and Click on nodes).");
                    return;
                }
                const name = prompt("Enter a name for the new GNN Persona:");
                if (!name || name.trim().length === 0) return;
                
                this.log(`Creating persona [${name}] with ${this.selectedNodes.size} nodes...`, 'info');
                try {
                    const apiHost = window.location.hostname === 'localhost' ? 'localhost' : window.location.hostname;
                    const res = await fetch(`http://${apiHost}:8001/api/lgnn/persona/create`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            name: name.trim(),
                            nodes: Array.from(this.selectedNodes)
                        })
                    });
                    if (res.ok) {
                        this.log(`Persona [${name}] created successfully!`, 'success');
                        this.selectedNodes = new Set(); // Reset selection
                        this.loadPersonas(); // Reload persona list
                    } else {
                        const err = await res.text();
                        this.log(`Failed to create persona: ${err}`, 'error');
                    }
                } catch (e) {
                    this.log(`Persona creation failed: ${e.message}`, 'error');
                }
            });
        }

        // Bind Control Sliders for Dynamic GNN Tuning
        const sliderDecay = document.getElementById('slider-decay');
        if (sliderDecay) {
            sliderDecay.addEventListener('change', (e) => {
                const value = e.detail.value;
                this.log(`Tuning Hebbian Decay to: ${value}`, 'info');
                if (this.socket && this.socket.readyState === WebSocket.OPEN) {
                    this.socket.send(JSON.stringify({
                        type: 'update_params',
                        decay_rate: value
                    }));
                }
            });
        }

        const sliderResonance = document.getElementById('slider-resonance');
        if (sliderResonance) {
            sliderResonance.addEventListener('change', (e) => {
                const value = e.detail.value;
                this.log(`Tuning Resonance Limit to: ${value}`, 'info');
                if (this.socket && this.socket.readyState === WebSocket.OPEN) {
                    this.socket.send(JSON.stringify({
                        type: 'update_params',
                        resonance_threshold: value
                    }));
                }
            });
        }

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
                        let botName = "ObserverDashboard";
                        let actualQuery = query;
                        
                        // Villain Arc: Spider Command Override
                        if (query.toLowerCase().startsWith('/spider ')) {
                            botName = "AethelSpider_ArXiv";
                            actualQuery = query.substring(8);
                            this.log(`[SYSTEM] Deploying ArXiv Spider to hunt for: "${actualQuery}"`, 'success');
                        } else {
                            this.log(`Injecting Memory Fragment: "${query}"`, 'success');
                        }
                        
                        try {
                            // Determine host for API call (fallback to localhost if running locally)
                            const apiHost = window.location.hostname === 'localhost' ? 'localhost' : window.location.hostname;
                            await fetch(`http://${apiHost}:8001/api/lgnn/universal_ingest`, {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({
                                    bot_name: botName,
                                    observation: actualQuery
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
        


        document.addEventListener('keydown', (e) => {
            // Hotkeys for Node Actions
            if (e.target.tagName !== 'INPUT' && e.target.tagName !== 'TEXTAREA') {
                if (e.key === ' ' || e.key === 'Enter') {
                    if (this.selectedNodeId) this.diveIntoNode(this.selectedNodeId);
                    e.preventDefault();
                    return;
                }
                if (e.key === 'w' || e.key === 'W') {
                    this.isWorkbenchMode = !this.isWorkbenchMode;
                    const chkWorkbench = document.getElementById('chk-workbench');
                    if (chkWorkbench) chkWorkbench.checked = this.isWorkbenchMode;
                    this.log(this.isWorkbenchMode ? 'Entered WORKBENCH MODE' : 'Exited WORKBENCH MODE', 'success');
                    return;
                }
                
                if (e.key === 'Escape') {
                    if (this.currentDimension !== "root" && this.dimensionHistory.length > 0) {
                        this.currentDimension = this.dimensionHistory.pop();
                        this.log(`Ascended back to dimension: ${this.currentDimension}`, 'info');
                        // In a real app we'd restore the nodes from a dictionary. For now we just sync with backend.
                        this.socket.send(JSON.stringify({ type: "request_full_sync" }));
                        e.preventDefault();
                        return;
                    }

                    if (this.selectedNodeId || (this.selectedNodes && this.selectedNodes.size > 0)) {
                        this.deselectAll();
                    } else {
                        this.zoomOut();
                    }
                    e.preventDefault();
                    return;
                }
                if (e.key === 'PageUp' || e.key === 'PageDown') {
                    const rect = this.canvas.getBoundingClientRect();
                    const centerX = rect.width / 2;
                    const centerY = rect.height / 2;
                    const graphX = (centerX - this.panX) / this.zoom;
                    const graphY = (centerY - this.panY) / this.zoom;
                    
                    const zoomFactor = e.key === 'PageUp' ? 1.5 : (1 / 1.5);
                    this.zoom *= zoomFactor;
                    
                    if (this.zoom > 5.0 && !this.selectedNodeId) this.zoom = 5.0;
                    if (this.zoom < 0.05) this.zoom = 0.05;
                    
                    this.panX = centerX - graphX * this.zoom;
                    this.panY = centerY - graphY * this.zoom;
                    
                    e.preventDefault();
                    return;
                }
                if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(e.key)) {
                    if (this.selectedNodeId) {
                        const currentNode = this.nodes.find(n => n.id === this.selectedNodeId);
                        if (currentNode) {
                            const neighborIds = this.links
                                .filter(l => l.source === currentNode.id || l.target === currentNode.id)
                                .map(l => l.source === currentNode.id ? l.target : l.source);
                            
                            const neighbors = this.nodes.filter(n => neighborIds.includes(n.id));
                            if (neighbors.length > 0) {
                                let bestMatch = null;
                                let bestScore = -Infinity;
                                
                                for (const neighbor of neighbors) {
                                    const isoCurr = this.toIso(currentNode.x, currentNode.y, 0);
                                    const isoNeigh = this.toIso(neighbor.x, neighbor.y, 0);
                                    const idx = isoNeigh.x - isoCurr.x;
                                    const idy = isoNeigh.y - isoCurr.y;
                                    
                                    let score = 0;
                                    if (e.key === 'ArrowUp') score = -idy - Math.abs(idx)*0.5;
                                    if (e.key === 'ArrowDown') score = idy - Math.abs(idx)*0.5;
                                    if (e.key === 'ArrowLeft') score = -idx - Math.abs(idy)*0.5;
                                    if (e.key === 'ArrowRight') score = idx - Math.abs(idy)*0.5;
                                    
                                    if (score > bestScore) {
                                        bestScore = score;
                                        bestMatch = neighbor;
                                    }
                                }
                                
                                if (bestMatch) {
                                    this.selectedNodes = new Set([bestMatch.id]);
                                    this.inspectNode(bestMatch.id);
                                }
                            }
                        }
                    }
                    e.preventDefault();
                    return;
                }
                if (e.key === 'c' || e.key === 'C') {
                    if (this.selectedNodeId) this.duplicateNode(this.selectedNodeId);
                    return;
                }
                if (e.key === 'p' || e.key === 'P') {
                    this.spawnConnector();
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
        if (this.canvas && this.canvasContainer) {
            const w = this.canvasContainer.clientWidth;
            const h = this.canvasContainer.clientHeight;
            if (this.canvas.width !== w || this.canvas.height !== h) {
                this.canvas.width = w;
                this.canvas.height = h;
            }
        }
    }

    updateStatus(text, className) {
        if (this.elStatus) this.elStatus.textContent = text;
        if (this.elLight) {
            this.elLight.className = `indicator-light ${className}`;
        }
        if (this.compStatus) {
            this.compStatus.setAttribute('connected', className === 'connected' ? 'true' : 'false');
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
        this.loadPersonas();
    }

    onMessage(event) {
        try {
            const data = JSON.parse(event.data);
            if (data.type === 'telemetry') {
                if (this.elNodes) this.elNodes.textContent = data.nodes;
                if (this.elBridges) this.elBridges.textContent = data.bridges;
                if (this.elState) this.elState.textContent = data.state;
                
                if (this.compNodes) this.compNodes.setAttribute('value', data.nodes);
                if (this.compBridges) this.compBridges.setAttribute('value', data.bridges);
                if (this.compState) {
                    const stateVal = typeof data.state === 'number' ? data.state.toFixed(4) : data.state;
                    this.compState.setAttribute('value', stateVal);
                }

                if (this.elLeader) {
                    this.elLeader.textContent = typeof data.leader === 'string' ? data.leader : 
                        (data.leader && data.leader.length > 0 ? data.leader[0] : 'None');
                }
                
                // Live AETHEL Wallet Sync
                if (data.balance !== undefined && this.elAethel) {
                    const current = parseFloat(this.elAethel.textContent) || 0;
                    const target = parseFloat(data.balance);
                    if (current !== target) {
                        this.elAethel.textContent = target.toFixed(4);
                        this.elAethel.style.color = 'var(--accent-yellow)';
                        setTimeout(() => this.elAethel.style.color = 'var(--text-color)', 500);
                    }
                }

                if (data.graph) {
                    this.updateGraph(data.graph.nodes || [], data.graph.links || []);
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
            if (existing) {
                // Preserve reference, positions, velocity and pinned state
                existing.activation = nn.activation;
                existing.is_leader = nn.is_leader || false;
                existing.centrality = nn.centrality || 0.0;
                existing.label = nn.label || nn.id;
                if (!existing.full_data) {
                    existing.full_data = {
                        text_content: nn.text_content || '',
                        confidence: nn.confidence || 0.8,
                        is_public: nn.is_public !== undefined ? nn.is_public : true,
                        parent_id: nn.parent_id || 'root'
                    };
                } else {
                    existing.full_data.text_content = nn.text_content || existing.full_data.text_content;
                    existing.full_data.is_public = nn.is_public !== undefined ? nn.is_public : existing.full_data.is_public;
                }
                return existing;
            }
            return {
                id: nn.id,
                label: nn.label || nn.id,
                activation: nn.activation,
                is_leader: nn.is_leader || false,
                centrality: nn.centrality || 0.0,
                x: width / 2 + (Math.random() - 0.5) * 1000,
                y: height / 2 + (Math.random() - 0.5) * 1000,
                vx: (Math.random() - 0.5) * 10.0,
                vy: (Math.random() - 0.5) * 10.0,
                full_data: {
                    text_content: nn.text_content || '',
                    confidence: nn.confidence || 0.8,
                    is_public: nn.is_public !== undefined ? nn.is_public : true,
                    parent_id: nn.parent_id || 'root'
                }
            };
        });
        
        this.links = newLinks.map(nl => ({
            source: nl.source,
            target: nl.target,
            weight: nl.weight
        }));
    }

    tick(timestamp) {
        this.resizeCanvas();
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
        if (this.compStatus) {
            this.compStatus.setAttribute('fps', Math.round(this.avgFps));
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
            
            /* Commented out Brutalist Flowchart Grid Snapping for smooth, default node physics behavior
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
            */
            
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
        if (this.isCameraTracking && !this.isPanning && !this.isDraggingNode && this.nodes.length > 0) {
            let targetX = center.x;
            let targetY = center.y;
            let targetZ = 0;

            if (this.selectedNodeId) {
                // Track selected node
                const selected = this.nodes.find(n => n.id === this.selectedNodeId);
                if (selected) {
                    targetX = selected.x;
                    targetY = selected.y;
                    targetZ = selected.is_leader ? 300 : (selected.id.startsWith("Obs_") ? -200 : 0);
                }
            } else {
                // Track center of mass of the swarm
                let cmX = 0, cmY = 0;
                let visibleCount = 0;
                for (const n of this.nodes) {
                    if (!this.showGossip && n.id.startsWith("Obs_")) continue;
                    cmX += n.x;
                    cmY += n.y;
                    visibleCount++;
                }
                if (visibleCount > 0) {
                    targetX = cmX / visibleCount;
                    targetY = cmY / visibleCount;
                }
                targetZ = 0;
            }

            // Project tracking target into Isometric space!
            const targetIso = this.toIso(targetX, targetY, targetZ);

            // Calculate where panX/panY need to be to center the ISOMETRIC point on the screen
            const idealPanX = width / 2 - targetIso.x * this.zoom;
            const idealPanY = height / 2 - targetIso.y * this.zoom;

            // Smooth Lerp
            this.panX += (idealPanX - this.panX) * 0.05;
            this.panY += (idealPanY - this.panY) * 0.05;
        }
    }

    handleMouseDown(e) {
        if (!this.canvas) return;
        const rect = this.canvas.getBoundingClientRect();
        const mouseX = e.clientX - rect.left;
        const mouseY = e.clientY - rect.top;
        
        // Handle Radial menu clicks
        if (this.radialMenu && this.radialMenu.active) {
            this.radialMenu.active = false;
            const dx = e.clientX - this.radialMenu.x;
            const dy = e.clientY - this.radialMenu.y;
            const dist = Math.sqrt(dx*dx + dy*dy);
            
            if (dist > 15 && dist < 110) {
                let angle = Math.atan2(dy, dx) + Math.PI/2;
                if (angle < 0) angle += Math.PI * 2;
                const slice = (Math.PI * 2) / this.radialMenu.options.length;
                const index = Math.floor((angle + slice/2) / slice) % this.radialMenu.options.length;
                const option = this.radialMenu.options[index];
                
                this.log(`Radial Action: ${option}`, 'success');
                
                if (option === "Inspect" && this.radialMenu.nodeId) {
                    this.inspectNode(this.radialMenu.nodeId);
                } else if (option === "Link Source" && this.radialMenu.nodeId) {
                    this.isWiring = true;
                    this.wireSourceNode = this.nodes.find(n => n.id === this.radialMenu.nodeId);
                    this.wireTargetIso = null;
                } else if (option === "Pin/Unpin" && this.radialMenu.nodeId) {
                    const node = this.nodes.find(n => n.id === this.radialMenu.nodeId);
                    if (node) {
                        node.is_pinned = !node.is_pinned;
                        this.log(`Toggled pinned state of [${node.id}]`, 'info');
                    }
                } else if (option === "Delete Node" && this.radialMenu.nodeId) {
                    if (confirm(`Delete GNN Node [${this.radialMenu.nodeId}]?`)) {
                        this.socket.send(JSON.stringify({
                            type: 'delete_nodes',
                            nodes: [this.radialMenu.nodeId]
                        }));
                        this.nodes = this.nodes.filter(n => n.id !== this.radialMenu.nodeId);
                        this.selectedNodeId = null;
                    }
                } else if (option === "Spawn Node") {
                    const graphX = (this.radialMenu.x - rect.left - this.panX) / this.zoom;
                    const graphY = (this.radialMenu.y - rect.top - this.panY) / this.zoom;
                    const flatCoords = this.fromIso(graphX, graphY, 0);
                    
                    const label = prompt("Enter text content for the new GNN Node:");
                    if (label && label.trim().length > 0) {
                        const nodeName = prompt("Enter unique ID/name:", "Node_" + Math.floor(Math.random()*1000));
                        if (nodeName) this.createNode(nodeName, label.trim(), flatCoords.x, flatCoords.y);
                    }
                } else if (option === "Force Sync") {
                    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
                        this.socket.send(JSON.stringify({ type: 'sync_request' }));
                    }
                }
            }
            return;
        }

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
            
            // Arcade-style forgiving hitbox matching the new larger visual size
            const baseRadius = 25;
            const activationBonus = Math.abs(Math.tanh(n.activation || 0)) * 25;
            const centralityBonus = (n.centrality || 0) * 50;
            const rawR = baseRadius + activationBonus + centralityBonus;
            const radius = Math.max(0.1, rawR / Math.pow(this.zoom, 0.6));
            
            // Generous padding that scales up when zoomed out so it's always easy to click
            const hitPadding = 30 / this.zoom;
            
            if (dist < radius + hitPadding) {
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
            
            if (e.shiftKey) {
                if (!this.selectedNodes) this.selectedNodes = new Set();
                if (this.selectedNodes.has(clickedNode.id)) {
                    this.selectedNodes.delete(clickedNode.id);
                } else {
                    this.selectedNodes.add(clickedNode.id);
                }
                this.log(`Selected nodes count: ${this.selectedNodes.size}`, 'info');
                return;
            }

            this.draggedNode = clickedNode;
            this.isDraggingNode = true;
            clickedNode.is_pinned = true; // Pin the reality anchor
            
            // Calculate drag offset to prevent coordinate snapping
            const zOffset = clickedNode.is_leader ? 300 : (clickedNode.id.startsWith("Obs_") ? -200 : 0);
            const nodeIso = this.toIso(clickedNode.x, clickedNode.y, zOffset);
            this.dragOffsetX = graphX - nodeIso.x;
            this.dragOffsetY = graphY - nodeIso.y;

            // Left click on node: Select/Inspect
            if (!this.selectedNodes) this.selectedNodes = new Set();
            this.selectedNodes = new Set([clickedNode.id]);
            this.inspectNode(clickedNode.id);
        } else if (e.button === 0 && !clickedNode) {
            // Start panning
            this.isPanning = true;
            this.isCameraTracking = false;
            this.startX = e.clientX - this.panX;
            this.startY = e.clientY - this.panY;
            this.panStartDistance = 0;
            this.panMouseStartX = e.clientX;
            this.panMouseStartY = e.clientY;
        } else if (e.button === 1 || e.button === 2) {
            if (e.button === 2 && clickedNode) {
                // Prevent default menu & handle radial opening instead (done in contextmenu listener)
                return;
            }
            // Middle or Right click: start panning
            this.isPanning = true;
            this.isCameraTracking = false;
            this.startX = e.clientX - this.panX;
            this.startY = e.clientY - this.panY;
            this.panMouseStartX = e.clientX;
            this.panMouseStartY = e.clientY;
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
            
            const targetIsoX = graphX - (this.dragOffsetX || 0);
            const targetIsoY = graphY - (this.dragOffsetY || 0);
            const flatCoords = this.fromIso(targetIsoX, targetIsoY, zOffset);
            
            this.draggedNode.x = flatCoords.x;
            this.draggedNode.y = flatCoords.y;
            this.draggedNode.vx = 0;
            this.draggedNode.vy = 0;
            return;
        }
        
        if (this.isPanning) {
            this.panX = e.clientX - this.startX;
            this.panY = e.clientY - this.startY;
            const dx = e.clientX - this.panMouseStartX;
            const dy = e.clientY - this.panMouseStartY;
            this.panStartDistance = Math.sqrt(dx * dx + dy * dy);
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
                    
                    const baseRadius = 25;
                    const activationBonus = Math.abs(Math.tanh(n.activation || 0)) * 25;
                    const centralityBonus = (n.centrality || 0) * 50;
                    const rawR = baseRadius + activationBonus + centralityBonus;
                    const radius = Math.max(0.1, rawR / Math.pow(this.zoom, 0.6));
                    
                    const hitPadding = 30 / this.zoom;
                    
                    if (dist < radius + hitPadding) {
                        targetNode = n;
                        break;
                    }
                }
                
                if (targetNode) {
                    // Create link locally for immediate visual feedback
                    this.links.push({
                        source: this.wireSourceNode.id,
                        target: targetNode.id,
                        weight: 1.0
                    });
                    
                    // Send to backend
                    this.sendAction('create_link', {
                        source: this.wireSourceNode.id,
                        target: targetNode.id
                    });
                    this.log(`Linked [${this.wireSourceNode.id}] to [${targetNode.id}]`, 'success');
                }
            }
            this.wireSourceNode = null;
            this.wireTargetIso = null;
        }
        
        if (this.isPanning) {
            this.isPanning = false;
            if (typeof this.panStartDistance === 'number' && this.panStartDistance < 5) {
                this.deselectAll();
            }
        }
        if (this.isDraggingNode && this.draggedNode) {
            // Smooth natural placement (No snap-to-grid jumps)
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

    spawnConnector() {
        const rect = this.canvas.getBoundingClientRect();
        const centerX = rect.width / 2;
        const centerY = rect.height / 2;
        
        const graphX = (centerX - this.panX) / this.zoom;
        const graphY = (centerY - this.panY) / this.zoom;
        const flatCoords = this.fromIso(graphX, graphY, 0);
        
        // Blueprint Grid Snapping (400x400 units)
        const snappedX = Math.round(flatCoords.x / 400) * 400;
        const snappedY = Math.round(flatCoords.y / 400) * 400;

        const connectorId = `Connector_${Math.floor(Math.random()*10000)}`;
        const connector = {
            id: connectorId,
            x: snappedX,
            y: snappedY,
            is_pinned: true,
            activation: 0,
            centrality: 0,
            is_leader: false,
            full_data: {
                text_content: "Workbench Connector Node\nUse this to anchor your subgraphs."
            }
        };
        this.nodes.push(connector);
        this.log(`Spawned Workbench Connector at [${snappedX}, ${snappedY}]`, 'success');
        
        this.selectedNodeId = connectorId;
        this.selectedNodes = new Set([connectorId]);
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
            fetch(`http://${window.location.hostname}:8001/api/lgnn/universal_ingest`, {
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
                const conf = 0.6 + Math.random() * 0.4; // 60% to 100% confidence
                const resultId = `Image_${nodeId}_${i}`;
                this.nodes.push({
                    id: resultId,
                    activation: conf * 1.5, // Scale visual radius by confidence
                    centrality: conf * 0.5,
                    is_pinned: true, // Pin to workbench!
                    is_leader: false,
                    x: source.x + (Math.random() - 0.5) * 800,
                    y: source.y + (Math.random() - 0.5) * 800,
                    full_data: {
                        confidence: conf,
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
            await fetch(`http://${window.location.hostname}:8001/api/lgnn/universal_ingest`, {
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
        this.isCameraTracking = true;
        this.log(`Loading node data: ${nodeId}`, 'info');
        
        try {
            let format = forceFormat || 'AUTO';
            const response = await fetch(`http://${window.location.hostname}:8001/api/lgnn/node/${encodeURIComponent(nodeId)}?format=${format}`);
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
                
                // Populate Inspector UI
                const inspector = document.getElementById('inspector-hud');
                const title = document.getElementById('inspector-title');
                const conf = document.getElementById('inspector-confidence');
                const tag = document.getElementById('inspector-tag');
                const content = document.getElementById('inspector-content');
                
                if (inspector) {
                    inspector.style.display = 'block';
                    title.textContent = nodeId;
                    
                    // Format node based on whether it's local graph data or full fetched data
                    const graphNode = this.nodes.find(n => n.id === nodeId);
                    const isGrounded = graphNode ? graphNode.is_grounded : false;
                    let confidenceStr = '--';
                    if (graphNode && graphNode.confidence !== undefined) {
                        confidenceStr = (graphNode.confidence * 100).toFixed(1) + '%';
                    }
                    const sourceTag = graphNode ? graphNode.source_tag : 'unknown';
                    
                    conf.textContent = confidenceStr;
                    tag.textContent = sourceTag;
                    
                    if (isGrounded) {
                        conf.style.color = 'var(--accent-yellow)';
                    } else {
                        conf.style.color = 'var(--text-color)';
                    }
                    
                    if (data.format === 'IMG' && data.media_b64) {
                        content.style.display = 'none';
                    } else {
                        content.style.display = 'block';
                        content.value = data.text_content || data.content || '';
                    }
                }
            } else {
                this.log(`Failed to inspect node: ${response.status}`, 'error');
            }
        } catch (e) {
            this.log(`Fetch error: ${e.message}`, 'error');
        }
    }

    deselectAll() {
        this.selectedNodeId = null;
        this.selectedNodes = new Set();
        this.isCameraTracking = true;
        const hud = document.getElementById('inspector-hud');
        if (hud) hud.style.display = 'none';
        this.log('Deselected all nodes', 'info');
    }

    async loadPersonas() {
        try {
            const apiHost = window.location.hostname === 'localhost' ? 'localhost' : window.location.hostname;
            const res = await fetch(`http://${apiHost}:8001/api/lgnn/personas`);
            if (res.ok) {
                const personas = await res.json();
                const container = document.getElementById('personas-list');
                if (container) {
                    container.innerHTML = ''; // Clear loading text/previous items
                    if (personas.length === 0) {
                        container.innerHTML = `<span style="font-size: 0.75rem; color: #888; font-family: var(--font-mono);">No personas defined</span>`;
                        return;
                    }
                    this.activePersonaNodes = new Set();
                    personas.forEach(p => {
                    if (p.active && p.nodes) {
                        p.nodes.forEach(nid => this.activePersonaNodes.add(nid));
                    }
                    
                    const row = document.createElement('div');
                        row.style.display = 'flex';
                        row.style.justifyContent = 'space-between';
                        row.style.alignItems = 'center';
                        row.style.fontFamily = 'var(--font-mono)';
                        row.style.fontSize = '0.75rem';
                        row.style.marginBottom = '6px';
                        
                        const label = document.createElement('span');
                        label.textContent = p.name;
                        label.style.fontWeight = 'bold';
                        label.style.color = 'var(--text-color)';
                        label.style.overflow = 'hidden';
                        label.style.textOverflow = 'ellipsis';
                        label.style.whiteSpace = 'nowrap';
                        label.style.marginRight = '8px';
                        
                        const toggle = document.createElement('button');
                        toggle.textContent = p.active ? '[ ACTIVE ]' : '[ DORMANT ]';
                        toggle.style.background = p.active ? 'var(--accent-blue)' : '#FFF';
                        toggle.style.color = p.active ? '#FFF' : '#1A1A1A';
                        toggle.style.border = '2px solid #1A1A1A';
                        toggle.style.fontSize = '0.65rem';
                        toggle.style.padding = '2px 6px';
                        toggle.style.cursor = 'pointer';
                        toggle.style.fontFamily = 'var(--font-mono)';
                        toggle.style.whiteSpace = 'nowrap';
                        toggle.style.flexShrink = '0';
                        
                        toggle.addEventListener('click', async () => {
                            const newActive = !p.active;
                            this.log(`Toggling persona ${p.name} to ${newActive ? 'active' : 'dormant'}...`, 'info');
                            try {
                                const toggleRes = await fetch(`http://${apiHost}:8001/api/lgnn/persona/toggle`, {
                                    method: 'POST',
                                    headers: { 'Content-Type': 'application/json' },
                                    body: JSON.stringify({
                                        name: p.name,
                                        active: newActive
                                    })
                                });
                                if (toggleRes.ok) {
                                    p.active = newActive;
                                    toggle.textContent = p.active ? '[ ACTIVE ]' : '[ DORMANT ]';
                                    toggle.style.background = p.active ? 'var(--accent-blue)' : '#FFF';
                                    toggle.style.color = p.active ? '#FFF' : '#1A1A1A';
                                    this.log(`Persona ${p.name} toggled successfully.`, 'success');
                                } else {
                                    this.log(`Failed to toggle persona`, 'error');
                                }
                            } catch (e) {
                                this.log(`Error toggling: ${e.message}`, 'error');
                            }
                        });
                        
                        row.appendChild(label);
                        row.appendChild(toggle);
                        container.appendChild(row);
                    });
                }
            }
        } catch (e) {
            console.error('Failed to load personas', e);
        }
    }

    async createNode(nodeId, textContent, x, y) {
        try {
            const apiHost = window.location.hostname === 'localhost' ? 'localhost' : window.location.hostname;
            const res = await fetch(`http://${apiHost}:8001/api/lgnn/node`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    id: nodeId,
                    text_content: textContent,
                    connections: [],
                    source_tag: "user_injected"
                })
            });
            if (res.ok) {
                this.log(`Successfully created GNN Node [${nodeId}]`, 'success');
                if (this.socket && this.socket.readyState === WebSocket.OPEN) {
                    this.socket.send(JSON.stringify({ type: 'sync_request' }));
                }
            } else {
                const err = await res.text();
                this.log(`Failed to create node: ${err}`, 'error');
            }
        } catch (err) {
            this.log(`Create node failed: ${err.message}`, 'error');
        }
    }

    draw() {
        if (!this.canvas || !this.ctx) return;
        
        const ctx = this.ctx;
        
        // Clear screen with faint grid lines
        ctx.fillStyle = '#F4F4F0';
        ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Draw grid
        ctx.strokeStyle = 'rgba(26, 26, 26, 0.04)';
        ctx.lineWidth = 1;
        const gridGap = 40;
        const startX = this.panX % gridGap;
        const startY = this.panY % gridGap;
        for (let x = startX; x < this.canvas.width; x += gridGap) {
            ctx.beginPath();
            ctx.moveTo(x, 0);
            ctx.lineTo(x, this.canvas.height);
            ctx.stroke();
        }
        for (let y = startY; y < this.canvas.height; y += gridGap) {
            ctx.beginPath();
            ctx.moveTo(0, y);
            ctx.lineTo(this.canvas.width, y);
            ctx.stroke();
        }
        
        // Draw Spider Radar Ingestion pulse
        if (this.isSpiderHunting) {
            this.spiderPulseRadius += 4;
            if (this.spiderPulseRadius > Math.max(this.canvas.width, this.canvas.height) * 1.5) {
                this.spiderPulseRadius = 0;
            }
            
            ctx.save();
            // Reset to screen coordinates
            ctx.setTransform(1, 0, 0, 1, 0, 0);
            
            ctx.beginPath();
            ctx.arc(this.canvas.width / 2, this.canvas.height / 2, this.spiderPulseRadius, 0, Math.PI * 2);
            ctx.strokeStyle = 'rgba(242, 193, 46, 0.15)';
            ctx.lineWidth = 3;
            ctx.stroke();
            
            ctx.beginPath();
            ctx.arc(this.canvas.width / 2, this.canvas.height / 2, Math.max(0, this.spiderPulseRadius - 200), 0, Math.PI * 2);
            ctx.strokeStyle = 'rgba(242, 193, 46, 0.06)';
            ctx.lineWidth = 1.5;
            ctx.stroke();
            
            ctx.restore();
        }
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
        
        // --- Central Workbench Dropzone (Villain Overseer) ---
        ctx.save();
        ctx.beginPath();
        ctx.arc(0, 0, 800, 0, Math.PI * 2);
        ctx.strokeStyle = 'rgba(255, 0, 50, 0.15)'; // Crimson Red Override
        ctx.lineWidth = 6 / this.zoom;
        ctx.setLineDash([15 / this.zoom, 30 / this.zoom]);
        ctx.stroke();
        
        ctx.beginPath();
        ctx.arc(0, 0, 810, 0, Math.PI * 2);
        ctx.strokeStyle = 'rgba(255, 50, 50, 0.3)';
        ctx.lineWidth = 2 / this.zoom;
        ctx.setLineDash([]);
        ctx.stroke();
        ctx.restore();
        
        // --- Workbench Filtering ---
        let visibleNodes = this.nodes;
        let visibleLinks = this.links;
        
        if (this.isWorkbenchMode) {
            visibleNodes = this.nodes.filter(n => 
                n.is_pinned || 
                n.id === this.selectedNodeId || 
                (this.selectedNodes && this.selectedNodes.has(n.id)) ||
                (n.source_tag && (n.source_tag === 'upload' || n.source_tag === 'MVP_Tuner' || n.source_tag === 'DragDrop_Injector'))
            );
            const visibleNodeIds = new Set(visibleNodes.map(n => n.id));
            visibleLinks = this.links.filter(l => visibleNodeIds.has(l.source) && visibleNodeIds.has(l.target));
        }
        
        // 1. Draw Links
        ctx.lineWidth = Math.max(0.5, 2 * this.zoom);
        for (const link of visibleLinks) {
            const n1 = nodeLookup.get(link.source);
            const n2 = nodeLookup.get(link.target);
            if (!n1 || !n2) continue;
            
            const isConnectedToSelected = this.selectedNodeId && (n1.id === this.selectedNodeId || n2.id === this.selectedNodeId);
            
            // Strict LOD for bridges with staggered vanishing points
            let lodAlpha = 1.0;
            if (!isConnectedToSelected) {
                const perfPenalty = (1.0 - (this.perfScale || 1.0)) * 2.0;
                
                // Stagger cull points based on node IDs to prevent simultaneous vanishing
                const charHash1 = (n1.id.charCodeAt(0) + n1.id.charCodeAt(n1.id.length - 1)) % 100;
                const stagger1 = charHash1 / 500.0; // 0.0 to 0.198
                const charHash2 = (n2.id.charCodeAt(0) + n2.id.charCodeAt(n2.id.length - 1)) % 100;
                const stagger2 = charHash2 / 500.0; // 0.0 to 0.198
                
                let c1 = !n1.is_leader && this.zoom < (0.1 - (n1.centrality || 0) * 0.2 + perfPenalty + stagger1);
                let c2 = !n2.is_leader && this.zoom < (0.1 - (n2.centrality || 0) * 0.2 + perfPenalty + stagger2);
                
                // Hard Cull if either end is uninteresting and we are zoomed out
                if (c1 || c2) {
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
            
            // Draw straight lines
            ctx.beginPath();
            ctx.moveTo(iso1.x, iso1.y);
            ctx.lineTo(iso2.x, iso2.y);
            
            // Constellation & Persona Focus Logic
            const hasSelection = this.selectedNodeId || (this.selectedNodes && this.selectedNodes.size > 0);
            const isLinkSelected = (this.selectedNodeId && (n1.id === this.selectedNodeId || n2.id === this.selectedNodeId)) ||
                                   (this.selectedNodes && (this.selectedNodes.has(n1.id) || this.selectedNodes.has(n2.id)));
            
            const hasActivePersona = this.activePersonaNodes && this.activePersonaNodes.size > 0;
            const isLinkInActivePersona = hasActivePersona && this.activePersonaNodes.has(n1.id) && this.activePersonaNodes.has(n2.id);

            let strokeStyle = '';
            let lineWidth = 1 / this.zoom;

            if (hasActivePersona) {
                if (isLinkInActivePersona) {
                    strokeStyle = `rgba(0, 80, 150, ${0.9 * lodAlpha})`;
                    lineWidth = 3 / this.zoom;
                } else {
                    strokeStyle = `rgba(26, 26, 26, ${0.01 * lodAlpha})`;
                    lineWidth = 0.5 / this.zoom;
                }
            } else if (hasSelection) {
                if (isLinkSelected) {
                    strokeStyle = `rgba(26, 26, 26, ${0.8 * lodAlpha})`;
                    lineWidth = 2.5 / this.zoom;
                } else {
                    strokeStyle = `rgba(26, 26, 26, ${0.03 * lodAlpha})`;
                    lineWidth = 0.5 / this.zoom;
                }
            } else {
                strokeStyle = `rgba(26, 26, 26, ${(0.05 + link.weight * 0.15) * lodAlpha})`;
                lineWidth = 1 / this.zoom;
            }

            ctx.strokeStyle = strokeStyle;
            ctx.lineWidth = lineWidth;
            
            ctx.stroke();
        }
        
        // Draw temporary workbench wire
        if (this.isWiring && this.wireSourceNode && this.wireTargetIso) {
            const z1 = this.wireSourceNode.is_leader ? 300 : (this.wireSourceNode.id.startsWith("Obs_") ? -200 : 0);
            const iso1 = this.toIso(this.wireSourceNode.x, this.wireSourceNode.y, z1);
            
            // Draw straight lines for temporary wire
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
        for (const n of visibleNodes) {
            // Skip drawing if node type is hidden
            if (!this.showGossip && n.id.startsWith("Obs_")) continue;
            if (!this.showNetwork && n.id.startsWith("Net_")) continue;
            if (!this.showStream && n.id.startsWith("Stream_")) continue;
            
            // Strict LOD: Cull unimportant worker nodes when zoomed out (Staggered)
            const isSelected = this.selectedNodeId === n.id;
            let lodAlpha = 1.0;
            
            if (!isSelected && !n.is_leader) {
                const perfPenalty = (1.0 - (this.perfScale || 1.0)) * 2.0;
                
                // Stagger the culling based on a stable pseudo-random hash of the node ID
                // This prevents the visual "pop" of 1000 nodes vanishing simultaneously
                const charHash = (n.id.charCodeAt(0) + n.id.charCodeAt(n.id.length - 1)) % 100;
                const stagger = charHash / 500.0; // 0.0 to 0.198
                
                const cullThreshold = 0.1 - (n.centrality || 0) * 0.2 + perfPenalty + stagger;
                
                if (this.zoom < cullThreshold) {
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
            const radius = Math.max(0.1, rawR / Math.pow(this.zoom, 0.6)); 
            
            // Iso Projection
            const zOffset = n.is_leader ? 300 : (n.id.startsWith("Obs_") ? -200 : 0);
            const iso = this.toIso(n.x, n.y, zOffset);
            
            // Off-screen Culling (Massive performance boost when zoomed in)
            if (iso.x + radius < vLeft || iso.x - radius > vRight || iso.y + radius < vTop || iso.y - radius > vBottom) {
                continue;
            }
            
            // Dim nodes that are not part of the active constellation
            const hasSelection = this.selectedNodeId || (this.selectedNodes && this.selectedNodes.size > 0);
            const isFocused = !hasSelection || 
                              n.id === this.selectedNodeId || 
                              (this.selectedNodes && this.selectedNodes.has(n.id)) ||
                              this.links.some(l => {
                                  if (this.selectedNodeId && (l.source === this.selectedNodeId || l.target === this.selectedNodeId)) {
                                      if (l.source === n.id || l.target === n.id) return true;
                                  }
                                  if (this.selectedNodes && this.selectedNodes.size > 0) {
                                      if (this.selectedNodes.has(l.source) && l.target === n.id) return true;
                                      if (this.selectedNodes.has(l.target) && l.source === n.id) return true;
                                  }
                                  return false;
                              });
            
            const hasActivePersona = this.activePersonaNodes && this.activePersonaNodes.size > 0;
            let baseAlpha = isFocused ? 1.0 : 0.2;
            if (hasActivePersona) {
                if (this.activePersonaNodes.has(n.id)) {
                    baseAlpha = 1.0;
                } else {
                    baseAlpha = 0.05;
                }
            }
            
            ctx.globalAlpha = baseAlpha * lodAlpha;
            // Render active persona indicator
            const isPersonaActive = this.activePersonaNodes && this.activePersonaNodes.has(n.id);
            if (isPersonaActive) {
                ctx.beginPath();
                ctx.arc(iso.x, iso.y, radius * 1.5, 0, Math.PI * 2);
                ctx.fillStyle = 'rgba(0, 80, 150, 0.12)';
                ctx.fill();
                
                ctx.beginPath();
                ctx.arc(iso.x, iso.y, radius * 1.35, 0, Math.PI * 2);
                ctx.strokeStyle = 'var(--accent-blue)';
                ctx.lineWidth = 1.5;
                ctx.setLineDash([4, 4]);
                ctx.stroke();
                ctx.setLineDash([]);
            }

            // Render selected node indicator
            const isMultiSelected = this.selectedNodes && this.selectedNodes.has(n.id);
            if (isMultiSelected) {
                ctx.beginPath();
                ctx.arc(iso.x, iso.y, radius * 1.45, 0, Math.PI * 2);
                ctx.strokeStyle = 'var(--accent-yellow)';
                ctx.lineWidth = 3.5;
                ctx.stroke();
            }

            // Draw Node Circle
            ctx.beginPath();
            ctx.arc(iso.x, iso.y, radius, 0, 2 * Math.PI);
            
            // Bauhaus Colors based on node type
            ctx.shadowBlur = 0; // No glowing in Bauhaus!
            
            if (n.id === this.selectedNodeId) {
                ctx.fillStyle = '#FFFFFF'; // White/Empty inside
                ctx.strokeStyle = '#F2C12E'; // Yellow highlight border
                ctx.lineWidth = 3 / this.zoom;
            } else if (n.id.startsWith("Connector_")) {
                ctx.fillStyle = '#1A1A1A'; // Black core
                ctx.strokeStyle = '#FFFFFF'; // White border
                ctx.lineWidth = 2 / this.zoom;
                ctx.setLineDash([5 / this.zoom, 5 / this.zoom]);
            } else if (n.is_leader || n.id.startsWith('Nightmare')) {
                ctx.fillStyle = '#E03C31'; // Safety Red
                ctx.strokeStyle = '#1A1A1A';
                ctx.lineWidth = 1.5 / this.zoom;
                
                if (n.id.startsWith('Nightmare')) {
                    // Glitchy/Dashed external warning ring for Nightmare Inversions
                    const time = Date.now() / 1000;
                    ctx.save();
                    ctx.beginPath();
                    ctx.arc(iso.x, iso.y, radius * 1.35, 0, Math.PI * 2);
                    ctx.strokeStyle = 'rgba(224, 60, 49, 0.8)';
                    ctx.lineWidth = 1.5 / this.zoom;
                    ctx.setLineDash([4 / this.zoom, 6 / this.zoom]);
                    ctx.stroke();
                    ctx.restore();
                }
            } else if (n.id.startsWith("Spider_")) {
                ctx.fillStyle = '#F2C12E'; // Electric Yellow
                ctx.strokeStyle = '#1A1A1A';
                ctx.lineWidth = 1.5 / this.zoom;
                
                // Concentric Radar Rings
                const time = Date.now() / 1000;
                ctx.save();
                for (let rIndex = 1; rIndex <= 3; rIndex++) {
                    const pulseRadius = radius * (1.0 + ((time * 0.5 + rIndex / 3) % 1.0) * 1.5);
                    const alpha = 1.0 - ((time * 0.5 + rIndex / 3) % 1.0);
                    ctx.beginPath();
                    ctx.arc(iso.x, iso.y, pulseRadius, 0, Math.PI * 2);
                    ctx.strokeStyle = `rgba(242, 193, 46, ${alpha * 0.6})`;
                    ctx.lineWidth = 2 / this.zoom;
                    ctx.stroke();
                }
                ctx.restore();
            } else if (n.id.startsWith("Decoder_")) {
                ctx.fillStyle = '#E87A00'; // Safety Orange
                ctx.strokeStyle = '#1A1A1A';
                ctx.lineWidth = 1.5 / this.zoom;
            } else if (n.id.startsWith("Image_")) {
                ctx.fillStyle = '#8B008B'; // Deep Magenta
                ctx.strokeStyle = '#1A1A1A';
                ctx.lineWidth = 1.5 / this.zoom;
            } else if (n.id.startsWith("Net_") || n.id.startsWith("Stream_")) {
                ctx.fillStyle = '#005096'; // Ultramarine Blue
                ctx.strokeStyle = '#1A1A1A';
                ctx.lineWidth = 1.5 / this.zoom;
            } else {
                ctx.fillStyle = '#FFFFFF'; // White default
                ctx.strokeStyle = '#1A1A1A';
                ctx.lineWidth = 1.5 / this.zoom;
            }
            
            ctx.fill();
            ctx.stroke();
            ctx.setLineDash([]); // Reset for other nodes!
            
            ctx.globalAlpha = 1.0; // reset for labels
            
            // Check if we are zoomed in deep enough to render the inner content
            if (this.zoom > 1.8 && isFocused && n.full_data) {
                ctx.save();
                ctx.beginPath();
                if (n.id.startsWith("Anchor_")) {
                ctx.fillStyle = '#FF0033'; // Aggressive Crimson
                ctx.fillRect(iso.x - r/2, iso.y - r/2, r, r);
                ctx.strokeStyle = 'rgba(255, 0, 50, 0.8)';
                ctx.lineWidth = 2 / this.zoom;
                ctx.strokeRect(iso.x - r*1.5, iso.y - r*1.5, r*3, r*3);
            } else if (n.id.startsWith("Obs_")) {
                ctx.fillStyle = '#00FF66'; // Toxic Green
                ctx.beginPath();
                ctx.arc(iso.x, iso.y, r/2, 0, Math.PI*2);
                ctx.fill();
                ctx.strokeStyle = 'rgba(0, 255, 102, 0.5)';
                ctx.lineWidth = 1 / this.zoom;
                ctx.stroke();
            } else {
                ctx.fillStyle = '#FFFFFF';
                ctx.fillRect(iso.x - r/2, iso.y - r/2, r, r);
            }
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
                
            } else if (this.zoom > 0.3) {
                // X220 Performance Safeguard: Text rendering is incredibly slow.
                // If FPS is bad, don't draw text labels for unimportant nodes unless zoomed in very close!
                if (this.perfScale < 0.8 && this.zoom < 1.0 && !n.is_leader && !n.is_pinned && (n.centrality || 0) < 0.8) {
                    continue; 
                }

                // Minimalistic text label BELOW the node
                ctx.fillStyle = "#1A1A1A"; // Dark text for Light Mode
                const fontSize = Math.min(14, Math.max(8, (r * 0.6))) / this.zoom;
                ctx.font = `bold ${fontSize}px 'Inter', sans-serif`;
                ctx.textAlign = "center";
                ctx.textBaseline = "top";
                
                const label = (n.label || n.id || '').split('_').pop().substring(0, 15);
                ctx.fillText(label, iso.x, iso.y + r + (5 / this.zoom));
            }
        }
        ctx.restore();
        
        this.updateHolograms();

        // Draw Radial Menu (in screen coordinates) on top of everything
        if (this.radialMenu && this.radialMenu.active) {
            ctx.save();
            ctx.setTransform(1, 0, 0, 1, 0, 0); // reset to screen coordinates
            
            const rx = this.radialMenu.x;
            const ry = this.radialMenu.y;
            
            // Hard shadow offset
            ctx.fillStyle = '#1A1A1A';
            ctx.beginPath();
            ctx.arc(rx + 6, ry + 6, 110, 0, Math.PI * 2);
            ctx.fill();
            
            // Outer Ring (Bauhaus solid white)
            ctx.fillStyle = '#FFFFFF';
            ctx.beginPath();
            ctx.arc(rx, ry, 110, 0, Math.PI * 2);
            ctx.fill();
            ctx.strokeStyle = '#1A1A1A';
            ctx.lineWidth = 3;
            ctx.stroke();
            
            const numOptions = this.radialMenu.options.length;
            const slice = (Math.PI * 2) / numOptions;
            
            // Draw lines separating options
            ctx.strokeStyle = '#1A1A1A';
            ctx.lineWidth = 2;
            for (let i = 0; i < numOptions; i++) {
                const angle = i * slice - Math.PI / 2;
                ctx.beginPath();
                ctx.moveTo(rx, ry);
                ctx.lineTo(rx + Math.cos(angle) * 110, ry + Math.sin(angle) * 110);
                ctx.stroke();
            }
            
            // Render Option Text
            for (let i = 0; i < numOptions; i++) {
                const angle = i * slice - Math.PI / 2 + slice / 2;
                const tx = rx + Math.cos(angle) * 65;
                const ty = ry + Math.sin(angle) * 65;
                
                ctx.fillStyle = '#1A1A1A';
                ctx.font = 'bold 0.75rem "JetBrains Mono", monospace';
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.fillText(this.radialMenu.options[i], tx, ty);
            }
            
            // Center Core circle
            ctx.fillStyle = 'var(--accent-red)';
            ctx.beginPath();
            ctx.arc(rx, ry, 15, 0, Math.PI * 2);
            ctx.fill();
            ctx.strokeStyle = '#1A1A1A';
            ctx.lineWidth = 3;
            ctx.stroke();
            
            ctx.restore();
        }
    }
    
    updateHolograms() {
        const layer = document.getElementById('hologram-layer');
        if (!layer) return;
        
        // Only show widget if we are in Workbench mode or if we specifically select a spider
        if (!this.selectedNodeId || !this.selectedNodeId.startsWith("Spider_")) {
            layer.innerHTML = '';
            return;
        }
        
        const n = this.nodes.find(node => node.id === this.selectedNodeId);
        if (!n) return;
        
        // Calculate screen coordinates!
        const zOffset = n.is_leader ? 300 : (n.id.startsWith("Obs_") ? -200 : 0);
        const iso = this.toIso(n.x, n.y, zOffset);
        
        const screenX = this.panX + (iso.x * this.zoom);
        const screenY = this.panY + (iso.y * this.zoom);
        
        // Node visual radius
        const baseRadius = 25;
        const activationBonus = Math.abs(Math.tanh(n.activation || 0)) * 25;
        const centralityBonus = (n.centrality || 0) * 50;
        const rawR = baseRadius + activationBonus + centralityBonus;
        const r = Math.max(0.1, rawR / Math.pow(this.zoom, 0.6)) * this.zoom;
        
        // Create or update the widget
        let widget = document.getElementById('spider-widget');
        if (!widget) {
            widget = document.createElement('div');
            widget.id = 'spider-widget';
            // Pure Bauhaus / FigJam aesthetics
            widget.style.position = 'absolute';
            widget.style.background = '#FFFFFF';
            widget.style.border = '2px solid #1A1A1A';
            widget.style.padding = '8px';
            widget.style.boxShadow = '4px 4px 0px #1A1A1A';
            widget.style.pointerEvents = 'auto'; // allow clicking
            widget.style.display = 'flex';
            widget.style.flexDirection = 'column';
            widget.style.gap = '8px';
            
            widget.innerHTML = `
                <div style="font-size: 0.7rem; font-weight: bold; letter-spacing: 1px; color: #F2C12E; background: #1A1A1A; padding: 2px 4px; text-transform: uppercase;">[ SPIDER UPLINK ]</div>
                <input type="text" id="spider-concept" placeholder="Target Concept..." style="border: 1px solid #1A1A1A; outline: none; padding: 4px; font-family: var(--font-mono); font-size: 0.8rem; width: 150px;">
                <button id="spider-deploy-btn" style="background: #F2C12E; color: #1A1A1A; font-weight: bold; font-family: var(--font-mono); border: 2px solid #1A1A1A; cursor: pointer; padding: 4px;">DEPLOY</button>
            `;
            layer.appendChild(widget);
            
            document.getElementById('spider-deploy-btn').addEventListener('click', () => {
                const concept = document.getElementById('spider-concept').value;
                this.log(`Spider programmed with concept: "${concept}"`, 'info');
                this.deploySpider(n.id);
            });
            
            // Allow typing without triggering canvas hotkeys
            document.getElementById('spider-concept').addEventListener('keydown', (e) => {
                e.stopPropagation();
                if (e.key === 'Enter') {
                    document.getElementById('spider-deploy-btn').click();
                }
            });
        }
        
        // Position it right next to the node!
        widget.style.left = `${screenX + r + 20}px`;
        widget.style.top = `${screenY - r}px`;
        
        // Hide if offscreen or zoomed out too far
        if (this.zoom < 0.4) {
            widget.style.display = 'none';
        } else {
            widget.style.display = 'flex';
        }
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

function startApp() {
    if (window.swarmClient) return; // Prevent double initialization
    window.swarmClient = new SwarmClient();
    
    // Tuner Input Logic
    const tunerInput = document.getElementById('resonance-tuner');
    if (tunerInput) {
        tunerInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && tunerInput.value.trim() !== '') {
                if (window.swarmClient) {
                    window.swarmClient.sendAction('tune_resonance', { query: tunerInput.value.trim() });
                    
                    fetch(`http://${window.location.hostname}:8001/api/lgnn/universal_ingest`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            bot_name: "MVP_Tuner",
                            observation: tunerInput.value.trim(),
                            confidence: 0.9,
                            context_tags: ["manual_input"]
                        })
                    }).catch(err => console.error(err));
                    
                    tunerInput.value = '';
                }
            }
        });
    }
    
    // Inspector UI Bindings
    document.getElementById('btn-close-inspector')?.addEventListener('click', () => {
        document.getElementById('inspector-hud').style.display = 'none';
    });
    
    document.getElementById('btn-pin-node')?.addEventListener('click', () => {
        if (window.swarmClient && window.swarmClient.selectedNodeId) {
            const n = window.swarmClient.nodes.find(node => node.id === window.swarmClient.selectedNodeId);
            if (n) {
                n.is_pinned = !n.is_pinned;
                window.swarmClient.log(`Node ${n.id} ${n.is_pinned ? 'pinned' : 'unpinned'}`, 'success');
                document.getElementById('btn-pin-node').style.background = n.is_pinned ? 'var(--accent-blue)' : 'transparent';
                document.getElementById('btn-pin-node').style.color = n.is_pinned ? '#FFF' : 'var(--text-color)';
            }
        }
    });
    
    document.getElementById('btn-delete-node')?.addEventListener('click', () => {
        if (window.swarmClient && window.swarmClient.selectedNodeId) {
            window.swarmClient.sendAction('delete_nodes', { nodes: [window.swarmClient.selectedNodeId] });
            document.getElementById('inspector-hud').style.display = 'none';
            window.swarmClient.selectedNodeId = null;
        }
    });

    // Drag and Drop Upload
    document.body.addEventListener('dragover', (e) => {
        e.preventDefault();
        e.stopPropagation();
    });
    document.body.addEventListener('dragenter', (e) => {
        e.preventDefault();
        e.stopPropagation();
    });
    document.body.addEventListener('dragleave', (e) => {
        e.preventDefault();
        e.stopPropagation();
    });
    document.body.addEventListener('drop', (e) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            const file = e.dataTransfer.files[0];
            window.swarmClient.log(`Absorbing file into swarm: ${file.name}`, 'info');
            
            const reader = new FileReader();
            reader.onload = (event) => {
                const b64 = event.target.result.split(',')[1]; // remove data:image/png;base64,
                fetch(`http://${window.location.hostname}:8001/api/lgnn/universal_ingest`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        bot_name: "DragDrop_Injector",
                        observation: `File Uploaded: ${file.name}`,
                        confidence: 0.9,
                        context_tags: ["upload", file.name],
                        media_b64: b64,
                        media_type: file.type
                    })
                }).catch(err => console.error(err));
            };
            reader.readAsDataURL(file);
        }
    });
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', startApp);
} else {
    startApp();
}
