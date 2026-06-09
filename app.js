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
                this.elNodes.textContent = data.nodes;
                this.elBridges.textContent = data.bridges;
                this.elState.textContent = data.state;
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
        const center = { x: width / 2, y: height / 2, z: 0 };
        const fov = 1000; // Field of view for 3D projection
        const ctx = this.ctx;
        ctx.clearRect(0, 0, width, height);

        // 1. Force calculations with dynamic zoom scaling
        // Scale repulsion exponentially with zoom so zooming in pushes nodes aggressively apart
        const kRepulsion = 40000 * Math.max(0.5, Math.pow(this.zoom, 2.5));
        const kAttraction = 0.004; // Drastically reduced from 0.03 so nodes float more freely
        const kGravity = 0.006;    // Slightly reduced gravity to let them expand
        const damping = 0.85;      // Kept the same so they don't lose all momentum instantly
        
        // Ensure nodes have Z coordinates
        for (const n of this.nodes) {
            if (n.z === undefined) {
                n.z = (Math.random() - 0.5) * 800; // Random depth
                n.vz = 0;
            }
        }

        // Link resolution
        const nodeLookup = new Map(this.nodes.map(n => [n.id, n]));
        for (const link of this.links) {
            link.sourceNode = nodeLookup.get(link.source);
            link.targetNode = nodeLookup.get(link.target);
        }

        // Repulsion between all nodes (3D)
        for (let i = 0; i < this.nodes.length; i++) {
            const n1 = this.nodes[i];
            for (let j = i + 1; j < this.nodes.length; j++) {
                const n2 = this.nodes[j];
                const dx = n2.x - n1.x;
                const dy = n2.y - n1.y;
                const dz = n2.z - n1.z;
                const dist = Math.sqrt(dx * dx + dy * dy + dz * dz) || 1.0;
                
                // Repulsion radius scales sharply with zoom
                const repulsionRadius = 800 * Math.max(0.5, Math.pow(this.zoom, 1.5));
                if (dist < repulsionRadius) {
                    const force = kRepulsion / (dist * dist + 800);
                    const fx = (dx / dist) * force;
                    const fy = (dy / dist) * force;
                    const fz = (dz / dist) * force;
                    n1.vx -= fx; n1.vy -= fy; n1.vz -= fz;
                    n2.vx += fx; n2.vy += fy; n2.vz += fz;
                }
            }
        }
        
        // Attraction along links (3D)
        for (const link of this.links) {
            const s = link.sourceNode;
            const t = link.targetNode;
            if (s && t) {
                const dx = t.x - s.x;
                const dy = t.y - s.y;
                const dz = t.z - s.z;
                const dist = Math.sqrt(dx * dx + dy * dy + dz * dz) || 1.0;
                
                const restLength = 100;
                const force = kAttraction * (dist - restLength) * link.weight;
                const fx = (dx / dist) * force;
                const fy = (dy / dist) * force;
                const fz = (dz / dist) * force;
                
                s.vx += fx; s.vy += fy; s.vz += fz;
                t.vx -= fx; t.vy -= fy; t.vz -= fz;
            }
        }
        
        // Gravity, Damping, and Position update (3D)
        for (const n of this.nodes) {
            n.vx += (center.x - n.x) * kGravity;
            n.vy += (center.y - n.y) * kGravity;
            n.vz += (center.z - n.z) * kGravity;
            
            n.vx *= damping;
            n.vy *= damping;
            n.vz *= damping;
            
            n.x += n.vx;
            n.y += n.vy;
            n.z += n.vz;
        }

        // 2. Draw bridges (Lines are drawn 2D projected)
        ctx.lineWidth = 1;
        for (const link of this.links) {
            const s = link.sourceNode;
            const t = link.targetNode;
            if (s && t) {
                // Project 3D to 2D
                const sScale = fov / (fov + s.z);
                const tScale = fov / (fov + t.z);

                const sx = this.panX + (s.x - center.x) * this.zoom * sScale + center.x;
                const sy = this.panY + (s.y - center.y) * this.zoom * sScale + center.y;
                const tx = this.panX + (t.x - center.x) * this.zoom * tScale + center.x;
                const ty = this.panY + (t.y - center.y) * this.zoom * tScale + center.y;

                ctx.beginPath();
                ctx.moveTo(sx, sy);
                ctx.lineTo(tx, ty);
                ctx.strokeStyle = `rgba(6, 182, 212, ${Math.min(0.8, 0.1 * link.weight)})`;
                ctx.stroke();
            }
        }
        
        // 3. Draw nodes (Painters algorithm: sort by depth Z descending)
        const sortedNodes = [...this.nodes].sort((a, b) => b.z - a.z);

        for (const n of sortedNodes) {
            // If the node is behind the camera, don't draw it
            if (n.z <= -fov + 10) continue;

            const scale = Math.max(0.01, fov / (fov + n.z)); // Perspective scale (clamped to avoid negative/infinity)
            const x = this.panX + (n.x - center.x) * this.zoom * scale + center.x;
            const y = this.panY + (n.y - center.y) * this.zoom * scale + center.y;
            
            // Limit the maximum visual size so they don't become blobs when zoomed in
            const baseRadius = 8;
            const activationBonus = Math.max(0, n.activation || 0) * 5;
            const centralityBonus = (n.centrality || 0) * 100;
            
            // Scale radius relative to zoom AND 3D depth, ensuring it never goes negative
            const rawR = (baseRadius + activationBonus + centralityBonus);
            const r = Math.max(0.1, rawR * Math.pow(this.zoom, 0.4) * scale); 

            // Color coding based on node ID/Type
            let nodeColor = 'rgba(6, 182, 212, 0.8)'; // Default Cyan
            let glowColor = 'rgba(6, 182, 212, 0.4)';
            
            if (n.is_leader) {
                nodeColor = 'rgba(255, 215, 0, 1)'; // Gold Leader
                glowColor = 'rgba(255, 215, 0, 0.6)';
            } else if (n.id.startsWith('Stream_')) {
                nodeColor = 'rgba(255, 0, 128, 1)'; // Pink Streams
                glowColor = 'rgba(255, 0, 128, 0.6)';
            } else if (n.id.includes('Spider')) {
                nodeColor = 'rgba(0, 255, 128, 1)'; // Neon Green Spiders
                glowColor = 'rgba(0, 255, 128, 0.6)';
            } else if (['creativity', 'soziokratie3.0', 'neon genesis evangelion', 'unit734', 'aethelburg'].includes(n.id.toLowerCase())) {
                nodeColor = 'rgba(147, 51, 234, 1)'; // Deep Purple Reality Anchors
                glowColor = 'rgba(147, 51, 234, 0.8)';
            }

            // Alpha fade out for objects far in the background
            const alpha = Math.max(0.05, Math.min(1.0, 1.5 - (n.z / 1000)));

            ctx.beginPath();
            ctx.arc(x, y, r, 0, Math.PI * 2);
            
            // Apply depth alpha to colors securely
            ctx.fillStyle = nodeColor.replace('1)', `${alpha})`).replace('0.8)', `${alpha * 0.8})`);
            ctx.shadowColor = glowColor.replace('0.6)', `${alpha * 0.6})`).replace('0.4)', `${alpha * 0.4})`).replace('0.8)', `${alpha * 0.8})`);
            
            ctx.shadowBlur = r * 2;
            ctx.fill();
            
            ctx.shadowBlur = 0; // Reset
            
            // Draw Label if zoomed in enough or if it's a leader/anchor/stream, and not too far back
            if ((this.zoom > 0.8 || n.is_leader || n.id.startsWith('Stream_') || ['creativity', 'unit734'].includes(n.id.toLowerCase())) && n.z < 500) {
                ctx.fillStyle = `rgba(255,255,255,${alpha * 0.9})`;
                ctx.font = `${Math.max(10, 12 * Math.pow(this.zoom, 0.5) * scale)}px 'JetBrains Mono'`;
                ctx.textAlign = 'center';
                ctx.fillText((n.label || n.id || '').substring(0, 24), x, y + r + 15 * Math.min(1, scale));
            }
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
            
            const baseRadius = 6;
            const activationBonus = Math.abs(Math.tanh(n.activation || 0)) * 20;
            const centralityBonus = (n.centrality || 0) * 150;
            const radius = baseRadius + activationBonus + centralityBonus;
            
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
        ctx.lineWidth = 1.5 / this.zoom;
        for (const link of this.links) {
            // Skip link if it connects to a hidden node type
            if (!this.showGossip && (link.source.startsWith("Obs_") || link.target.startsWith("Obs_"))) continue;
            if (!this.showNetwork && (link.source.startsWith("Net_") || link.target.startsWith("Net_"))) continue;
            if (!this.showStream && (link.source.startsWith("Stream_") || link.target.startsWith("Stream_"))) continue;
            
            const n1 = nodeLookup.get(link.source);
            const n2 = nodeLookup.get(link.target);
            if (!n1 || !n2) continue;
            
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
            
            // Calculate node radius with more variance based on activation and centrality
            const baseRadius = 6;
            const activationBonus = Math.abs(Math.tanh(n.activation || 0)) * 20;
            const centralityBonus = (n.centrality || 0) * 150; // Centrality is usually very small (e.g. 0.05), so we multiply by a large number
            const radius = baseRadius + activationBonus + centralityBonus;

            // Highlight ring if selected
            if (n.id === this.selectedNodeId) {
                ctx.shadowBlur = 0;
                ctx.strokeStyle = "#eab308";
                ctx.lineWidth = 2 / this.zoom;
                ctx.beginPath();
                ctx.arc(n.x, n.y, radius + 5, 0, 2 * Math.PI);
                ctx.stroke();
            }

            // Glow effect
            ctx.shadowBlur = 15;
            if (n.is_leader) {
                ctx.shadowColor = "rgba(234, 179, 8, 0.8)";
            } else if (n.id.startsWith("Net_")) {
                ctx.shadowColor = "rgba(59, 130, 246, 0.6)"; // Blue
            } else if (n.id.startsWith("Stream_")) {
                ctx.shadowColor = "rgba(6, 182, 212, 0.6)"; // Cyan
            } else {
                ctx.shadowColor = n.id.startsWith("Obs_") ? "rgba(168, 85, 247, 0.6)" : "rgba(34, 197, 94, 0.6)";
            }
            
            ctx.beginPath();
            ctx.arc(n.x, n.y, radius, 0, 2 * Math.PI);
            if (n.is_leader) {
                ctx.fillStyle = "#eab308";
            } else if (n.id.startsWith("Net_")) {
                ctx.fillStyle = "#3b82f6";
            } else if (n.id.startsWith("Stream_")) {
                ctx.fillStyle = "#06b6d4";
            } else {
                ctx.fillStyle = n.id.startsWith("Obs_") ? "#a855f7" : "#22c55e";
            }
            ctx.fill();
            
            // Pulsing orbit ring for elected leader node
            if (n.is_leader) {
                ctx.shadowBlur = 0;
                ctx.strokeStyle = "rgba(234, 179, 8, 0.5)";
                ctx.lineWidth = 1.5 / this.zoom;
                const pulseRadius = radius + 6 + Math.sin(Date.now() * 0.005) * 3;
                ctx.beginPath();
                ctx.arc(n.x, n.y, pulseRadius, 0, 2 * Math.PI);
                ctx.stroke();
            }
            
            // Draw labels
            ctx.shadowBlur = 0; // Disable shadow for clean text
            ctx.fillStyle = n.is_leader ? "#eab308" : "#ffffff";
            ctx.font = `bold ${11 / this.zoom}px 'JetBrains Mono', monospace`;
            ctx.textAlign = "center";
            ctx.fillText(n.id, n.x, n.y - (radius + 6 / this.zoom));
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
