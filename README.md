# Aethelnet Observer (Sphere UI)

The **Aethelnet Observer** is the immersive visual frontend for the continuous-time Liquid Graph Neural Network (LGNN) nodes. It breaks out of the traditional "box paradigm" grid UI, replacing it with a fluid, full-screen, non-Euclidean canvas.

It connects to your local `aethelnet-node` daemon and visualizes the chaotic, organic topology of the network in real-time.

## Features
- **Immersive Node Canvas:** A full-screen dark-matter canvas where nodes are rendered as glowing spheres with inline semantic text.
- **Proof-of-Truth HUD:** A live `$AETHEL` crypto-wallet balance display that updates dynamically as your local Spiders mine semantic truth.
- **Glassmorphism Overlays:** Transparent, blurred UI elements that float unobtrusively above the data topology.
- **Real-Time Physics:** Nodes gravitate, attract, and repel based on continuous Hebbian learning weights powered by the backend ODE solvers.

## Setup
Currently, this is a vanilla HTML/JS application built for maximum performance without framework overhead. Simply serve the directory with a lightweight web server:

```bash
python -m http.server 3000
```
Then navigate to `http://localhost:3000`.

## License
This project is licensed under the **AGPL-3.0 License**. See the `LICENSE` file for details.
