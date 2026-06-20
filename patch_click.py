import re

with open("app.js", "r") as f:
    code = f.read()

mousedown_injection = """
            if (this.radialMenu && this.radialMenu.active) {
                this.radialMenu.active = false;
                const dx = e.clientX - this.radialMenu.x;
                const dy = e.clientY - this.radialMenu.y;
                const dist = Math.sqrt(dx*dx + dy*dy);
                if (dist > 15 && dist < 100) {
                    let angle = Math.atan2(dy, dx) + Math.PI/2;
                    if (angle < 0) angle += Math.PI * 2;
                    const slice = (Math.PI * 2) / this.radialMenu.options.length;
                    const index = Math.floor((angle + slice/2) / slice) % this.radialMenu.options.length;
                    const option = this.radialMenu.options[index];
                    this.log(`Radial Action: ${option}`, 'success');
                    
                    if (option === "Spawn Node") {
                        const graphX = (e.clientX - this.panX) / this.zoom;
                        const graphY = (e.clientY - this.panY) / this.zoom;
                        const id = "Node_" + Math.floor(Math.random()*1000);
                        this.nodes.push({id: id, label: "Manual Node", x: graphX, y: graphY, activation: 1.0, is_pinned: true});
                    }
                    if (option === "Dive Dimension" && this.hoveredNodeId) {
                        this.dimensionHistory.push(this.currentDimension);
                        this.currentDimension = this.hoveredNodeId;
                        this.log(`Dived into dimension: ${this.currentDimension}`, 'success');
                        // visually clear nodes to simulate diving
                        this.nodes = [];
                        this.links = [];
                        this.panX = window.innerWidth / 2;
                        this.panY = window.innerHeight / 2;
                        this.zoom = 1.0;
                    }
                }
                return; // Consume click
            }
"""

code = re.sub(r'(if \(e\.button === 0\) \{)', r'\1' + mousedown_injection, code)

with open("app.js", "w") as f:
    f.write(code)

print("Click patch applied.")
