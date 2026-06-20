import re

with open("app.js", "r") as f:
    code = f.read()

# 1. Add variables to constructor
constructor_injection = """
        // Phase 2: Radial Menu & Dimensions
        this.radialMenu = { active: false, x: 0, y: 0, options: ["Spawn Node", "Delete Node", "Dive Dimension"] };
        this.currentDimension = "root";
        this.dimensionHistory = [];
"""
code = re.sub(r'(this\.isWorkbenchMode = false;)', r'\1' + constructor_injection, code)

# 2. Add Context Menu listener to init()
init_injection = """
        // Context Menu
        this.canvas.addEventListener('contextmenu', (e) => {
            e.preventDefault();
            this.radialMenu.active = true;
            this.radialMenu.x = e.clientX;
            this.radialMenu.y = e.clientY;
        });
"""
code = re.sub(r'(this\.canvas\.addEventListener\(\'mousedown\', \(e\) => \{)', init_injection + r'\n        \1', code)

# 3. Add radial menu draw logic to the end of draw()
draw_injection = """
        // Draw Radial Menu
        if (this.radialMenu && this.radialMenu.active) {
            ctx.save();
            ctx.setTransform(1, 0, 0, 1, 0, 0); // reset to screen space
            
            const rx = this.radialMenu.x;
            const ry = this.radialMenu.y;
            
            ctx.fillStyle = 'rgba(15, 15, 20, 0.9)';
            ctx.beginPath();
            ctx.arc(rx, ry, 100, 0, Math.PI * 2);
            ctx.fill();
            ctx.strokeStyle = '#00ffcc';
            ctx.lineWidth = 2;
            ctx.stroke();

            const slice = (Math.PI * 2) / this.radialMenu.options.length;
            for (let i = 0; i < this.radialMenu.options.length; i++) {
                const angle = i * slice - Math.PI/2;
                const optX = rx + Math.cos(angle) * 60;
                const optY = ry + Math.sin(angle) * 60;
                
                ctx.fillStyle = '#fff';
                ctx.font = '14px monospace';
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.fillText(this.radialMenu.options[i], optX, optY);
            }
            
            ctx.beginPath();
            ctx.arc(rx, ry, 15, 0, Math.PI * 2);
            ctx.fillStyle = '#00ffcc';
            ctx.fill();
            ctx.restore();
        }
"""
code = re.sub(r'(requestAnimationFrame\(\(\) => this\.draw\(\)\);\n    \})', draw_injection + r'\n        \1', code)

with open("app.js", "w") as f:
    f.write(code)

print("Patch applied.")
