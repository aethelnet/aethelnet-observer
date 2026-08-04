# Future Features - Deferred for Next Year

This document tracks features that were removed from the current interface but are planned for future implementation.

## Creative2 (Port 1422) - 3D Market Visualization

### Labels Toggle Button (Removed)
- **Status:** Deferred
- **Reason:** The button existed but had no handler and no 3D text labels were being rendered on nodes
- **Planned Implementation:**
  - Add Three.js text sprites or canvas-based labels to display market symbols on 3D nodes
  - Implement toggle functionality to show/hide labels
  - Consider using `THREE.Sprite` with `THREE.CanvasTexture` for text rendering
  - Alternative: Use HTML overlays positioned via raycasting (more complex but better text quality)
- **Priority:** Low (node list sidebar already provides symbol identification)
- **Estimated Effort:** 2-4 hours

## Notes

All other buttons across all 7 views have been verified and are fully functional:
- ✅ MVP Dashboard (Port 1420) - All buttons functional
- ✅ ChartView (Port 1423) - All layer toggles and controls functional
- ✅ Creative (Port 1421) - All buttons functional
- ✅ Creative2 (Port 1422) - Labels toggle removed, all other buttons functional
- ✅ Analytics (Port 1424) - Help button functional
- ✅ Risk (Port 1425) - Help button functional
- ✅ Execution (Port 1426) - All buttons and click handlers functional




