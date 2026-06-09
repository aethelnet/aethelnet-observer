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
        this.showGossip = true;
        this.showNetwork = true;
        this.showStream = true;
        
        this.init();
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
        this.canvas.addEventListener('contextmenu', (e) => e.preventDefault());
        
        document.getElementById('btn-reconnect').addEventListener('click', () => {
            if (this.socket && this.socket.readyState === WebSocket.OPEN) {
                this.log('Force syncing...', 'info');
                this.socket.send(JSON.stringify({ type: 'sync_request' }));
            } else {
                this.connect();
            }
        });
        
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
                x: existing ? existing.x : width / 2 + (Math.random() - 0.5) * 100,
                y: existing ? existing.y : height / 2 + (Math.random() - 0.5) * 100,
                vx: existing ? existing.vx : 0,
                vy: existing ? existing.vy : 0
            };
        });
        
        this.links = newLinks.map(nl => ({
            source: nl.source,
            target: nl.target,
            weight: nl.weight
        }));
    }

    tick() {
        this.physicsUpdate();
        this.draw();
        requestAnimationFrame(() => this.tick());
    }

    physicsUpdate() {
        if (!this.canvas || this.nodes.length === 0) return;
        
        const width = this.canvas.width;
        const height = this.canvas.height;
        const center = { x: width / 2, y: height / 2 };
        
        // 1. Semantic Boids Swarm Logic
        const separationDist = 200;
        const cohesionWeight = 0.005;
        const alignmentWeight = 0.05;
        const separationWeight = 800;
        const maxSpeed = 3.0;
        const centerGravity = 0.0001;
        
        const nodeLookup = new Map(this.nodes.map(n => [n.id, n]));
        
        // Pre-calculate neighbor data for Boids
        const neighbors = new Map(this.nodes.map(n => [n.id, []]));
        for (const link of this.links) {
            if (neighbors.has(link.source)) neighbors.get(link.source).push({ id: link.target, weight: link.weight });
            if (neighbors.has(link.target)) neighbors.get(link.target).push({ id: link.source, weight: link.weight });
        }
        
        for (let i = 0; i < this.nodes.length; i++) {
            const n = this.nodes[i];
            
            let centerOfMassX = 0, centerOfMassY = 0;
            let avgVx = 0, avgVy = 0;
            let separationFx = 0, separationFy = 0;
            let neighborCount = 0;
            
            const nbrs = neighbors.get(n.id) || [];
            
            // 1. Cohesion & Alignment (from topological links)
            for (const nbrInfo of nbrs) {
                const neighbor = nodeLookup.get(nbrInfo.id);
                if (!neighbor) continue;
                
                // Cohesion (Center of Mass of linked concepts)
                centerOfMassX += neighbor.x;
                centerOfMassY += neighbor.y;
                
                // Alignment (Match velocity of linked concepts)
                avgVx += neighbor.vx || 0;
                avgVy += neighbor.vy || 0;
                neighborCount++;
            }
            
            // 2. Separation (from all nearby nodes to prevent clumping)
            for (let j = 0; j < this.nodes.length; j++) {
                if (i === j) continue;
                const other = this.nodes[j];
                const dx = n.x - other.x;
                const dy = n.y - other.y;
                if (Math.abs(dx) > separationDist || Math.abs(dy) > separationDist) continue;
                
                const dist = Math.sqrt(dx * dx + dy * dy) || 1.0;
                if (dist < separationDist) {
                    separationFx += (dx / dist) * (separationWeight / dist);
                    separationFy += (dy / dist) * (separationWeight / dist);
                }
            }
            
            // Apply Boids Rules
            if (neighborCount > 0) {
                centerOfMassX /= neighborCount;
                centerOfMassY /= neighborCount;
                avgVx /= neighborCount;
                avgVy /= neighborCount;
                
                n.vx += (centerOfMassX - n.x) * cohesionWeight;
                n.vy += (centerOfMassY - n.y) * cohesionWeight;
                
                n.vx += avgVx * alignmentWeight;
                n.vy += avgVy * alignmentWeight;
            }
            
            n.vx += separationFx;
            n.vy += separationFy;
            
            // Galaxy Center Gravity (Rubber-band boundary effect)
            const distFromCenter = Math.sqrt((center.x - n.x)**2 + (center.y - n.y)**2);
            let currentGravity = centerGravity;
            
            // If they drift further than 1500 pixels, gravity increases exponentially to yank them back
            if (distFromCenter > 1500) {
                currentGravity *= (distFromCenter / 500);
            }
            
            n.vx += (center.x - n.x) * currentGravity;
            n.vy += (center.y - n.y) * currentGravity;
            
            // Enforce minimum continuous movement (Nodes never fully sleep in a swarm)
            const speed = Math.sqrt(n.vx * n.vx + n.vy * n.vy) || 1.0;
            if (speed > maxSpeed) {
                n.vx = (n.vx / speed) * maxSpeed;
                n.vy = (n.vy / speed) * maxSpeed;
            } else if (speed < 0.5) {
                // Add a tiny random Brownian drift to keep the swarm alive
                n.vx += (Math.random() - 0.5) * 0.2;
                n.vy += (Math.random() - 0.5) * 0.2;
            }
            
            n.x += n.vx;
            n.y += n.vy;
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
            
            const dx = n.x - graphX;
            const dy = n.y - graphY;
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
            // Left click on node: Select/Inspect
            this.inspectNode(clickedNode.id);
        } else if (e.button === 1 || e.button === 2 || (e.button === 0 && !clickedNode)) {
            // Middle, Right, or Left-drag in empty space: start panning
            this.isPanning = true;
            this.startX = e.clientX - this.panX;
            this.startY = e.clientY - this.panY;
        }
    }

    handleMouseMove(e) {
        if (this.isPanning) {
            this.panX = e.clientX - this.startX;
            this.panY = e.clientY - this.startY;
        }
    }

    handleMouseUp(e) {
        this.isPanning = false;
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
            this.zoom = Math.min(this.zoom * zoomFactor, 5.0);
        } else {
            this.zoom = Math.max(this.zoom / zoomFactor, 0.2);
        }
        
        this.panX = mouseX - graphX * this.zoom;
        this.panY = mouseY - graphY * this.zoom;
    }

    async inspectNode(nodeId) {
        this.selectedNodeId = nodeId;
        this.log(`Loading node data: ${nodeId}`, 'info');
        
        try {
            const host = window.location.hostname;
            const response = await fetch(`http://${host || '127.0.0.1'}:8001/api/lgnn/node/${encodeURIComponent(nodeId)}`);
            if (response.ok) {
                const data = await response.json();
                
                const panel = document.getElementById('inspector-panel');
                if (panel) {
                    panel.style.display = 'block';
                    document.getElementById('inspect-title').textContent = data.id;
                    document.getElementById('inspect-source').textContent = data.source_tag;
                    document.getElementById('inspect-confidence').textContent = Number(data.confidence).toFixed(2);
                    
                    const textContent = data.text_content || 'No text content registered.';
                    document.getElementById('inspect-text').textContent = textContent;

                    // Handle Media Ingestion Paths
                    const mediaContainer = document.getElementById('media-container');
                    const imgEl = document.getElementById('inspect-image');
                    const audioEl = document.getElementById('inspect-audio');
                    
                    mediaContainer.style.display = 'none';
                    imgEl.style.display = 'none';
                    audioEl.style.display = 'none';
                    imgEl.src = '';
                    audioEl.src = '';

                    const ingestRegex = /(\/home\/[^\/]+\/\.aethelnet\/ingest_zone|~\/.aethelnet\/ingest_zone)\/(.+?\.(png|jpg|jpeg|wav|mp3|ogg))/i;
                    const match = textContent.match(ingestRegex);
                    
                    if (match) {
                        const relativePath = match[2];
                        const extension = match[3].toLowerCase();
                        const mediaUrl = `http://${host || '127.0.0.1'}:8001/media/${relativePath}`;
                        
                        mediaContainer.style.display = 'block';
                        if (['png', 'jpg', 'jpeg'].includes(extension)) {
                            imgEl.src = mediaUrl;
                            imgEl.style.display = 'block';
                        } else if (['wav', 'mp3', 'ogg'].includes(extension)) {
                            audioEl.src = mediaUrl;
                            audioEl.style.display = 'block';
                        }
                    }
                }
                
                this.log(`Details loaded for: ${nodeId}`, 'success');
            } else {
                this.log(`Failed to load details for ${nodeId}`, 'error');
            }
        } catch (err) {
            this.log(`Inspector request failed: ${err.message}`, 'error');
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
        
        const nodeLookup = new Map(this.nodes.map(n => [n.id, n]));
        
        // 1. Draw Links
        ctx.lineWidth = Math.max(0.5, 2 * this.zoom);
        for (const link of this.links) {
            // Skip link if it connects to a hidden node type
            if (!this.showGossip && (link.source.startsWith("Obs_") || link.target.startsWith("Obs_"))) continue;
            if (!this.showNetwork && (link.source.startsWith("Net_") || link.target.startsWith("Net_"))) continue;
            if (!this.showStream && (link.source.startsWith("Stream_") || link.target.startsWith("Stream_"))) continue;
            
            const n1 = nodeLookup.get(link.source);
            const n2 = nodeLookup.get(link.target);
            if (!n1 || !n2) continue;
            
            // Spatial Culling: Don't draw links if both nodes are completely off-screen
            const n1sx = n1.x * this.zoom + this.panX;
            const n1sy = n1.y * this.zoom + this.panY;
            const n2sx = n2.x * this.zoom + this.panX;
            const n2sy = n2.y * this.zoom + this.panY;
            
            if ((n1sx < -100 || n1sx > width + 100 || n1sy < -100 || n1sy > height + 100) && 
                (n2sx < -100 || n2sx > width + 100 || n2sy < -100 || n2sy > height + 100)) {
                continue;
            }
            
            ctx.beginPath();
            ctx.moveTo(n1.x, n1.y);
            ctx.lineTo(n2.x, n2.y);
            
            // Glowing connections: opacity and color based on Hebbian weight
            ctx.strokeStyle = `rgba(32, 197, 240, ${0.1 + link.weight * 0.4})`;
            ctx.stroke();
        }
        
        // 2. Draw Nodes
        for (const n of this.nodes) {
            // Skip drawing if node type is hidden
            if (!this.showGossip && n.id.startsWith("Obs_")) continue;
            if (!this.showNetwork && n.id.startsWith("Net_")) continue;
            if (!this.showStream && n.id.startsWith("Stream_")) continue;
            
            // Spatial Culling: Don't draw nodes that are off-screen
            const sx = n.x * this.zoom + this.panX;
            const sy = n.y * this.zoom + this.panY;
            if (sx < -150 || sx > width + 150 || sy < -150 || sy > height + 150) continue;
            
            // Nodes are bigger now for the inline text
            const baseRadius = 25;
            const activationBonus = Math.abs(Math.tanh(n.activation || 0)) * 25;
            const centralityBonus = (n.centrality || 0) * 80;
            
            const rawR = (baseRadius + activationBonus + centralityBonus);
            const r = Math.max(0.1, rawR / Math.pow(this.zoom, 0.6)); 

            // Highlight ring if selected
            if (n.id === this.selectedNodeId) {
                ctx.shadowBlur = 0;
                ctx.strokeStyle = "#eab308";
                ctx.lineWidth = 3 / this.zoom;
                ctx.beginPath();
                ctx.arc(n.x, n.y, r + 8 / this.zoom, 0, 2 * Math.PI);
                ctx.stroke();
            }

            // Color coding
            let nodeColor = 'rgba(6, 182, 212, 0.8)';
            let glowColor = 'rgba(6, 182, 212, 0.4)';
            
            if (n.is_leader) {
                nodeColor = 'rgba(255, 215, 0, 0.9)';
                glowColor = 'rgba(255, 215, 0, 0.6)';
            } else if (n.id.startsWith('Nightmare')) {
                nodeColor = 'rgba(255, 0, 0, 0.8)';
                glowColor = 'rgba(255, 0, 0, 0.8)';
            } else if (n.id.startsWith('Stream_')) {
                nodeColor = 'rgba(255, 0, 128, 0.8)';
                glowColor = 'rgba(255, 0, 128, 0.6)';
            } else if (n.id.includes('Spider')) {
                nodeColor = 'rgba(0, 255, 128, 0.8)';
                glowColor = 'rgba(0, 255, 128, 0.6)';
            } else if (['creativity', 'soziokratie3.0', 'neon genesis evangelion', 'unit734', 'aethelburg'].includes(n.id.toLowerCase())) {
                nodeColor = 'rgba(147, 51, 234, 0.9)';
                glowColor = 'rgba(147, 51, 234, 0.8)';
            }

            ctx.shadowBlur = r * 1.5;
            ctx.shadowColor = glowColor;
            
            ctx.beginPath();
            ctx.arc(n.x, n.y, r, 0, 2 * Math.PI);
            ctx.fillStyle = nodeColor;
            ctx.fill();
            
            // Draw inline text if the node is large enough to show it
            if (r * this.zoom > 15) {
                ctx.shadowBlur = 0;
                ctx.fillStyle = "#ffffff";
                const fontSize = Math.min(12, Math.max(6, (r * 0.4))) / this.zoom;
                ctx.font = `bold ${fontSize}px 'Inter', sans-serif`;
                ctx.textAlign = "center";
                ctx.textBaseline = "middle";
                
                const label = (n.label || n.id || '').split('_').pop().substring(0, 15);
                ctx.fillText(label, n.x, n.y);
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
