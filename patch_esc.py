import re

with open("app.js", "r") as f:
    code = f.read()

esc_injection = """
                if (e.key === 'Escape') {
                    if (this.currentDimension !== "root" && this.dimensionHistory.length > 0) {
                        this.currentDimension = this.dimensionHistory.pop();
                        this.log(`Ascended back to dimension: ${this.currentDimension}`, 'info');
                        // In a real app we'd restore the nodes from a dictionary. For now we just sync with backend.
                        this.socket.send(JSON.stringify({ type: "request_full_sync" }));
                        e.preventDefault();
                        return;
                    }
"""

code = re.sub(r'(if \(e\.key === \'Escape\'\) \{)', esc_injection, code)

with open("app.js", "w") as f:
    f.write(code)

print("Esc patch applied.")
