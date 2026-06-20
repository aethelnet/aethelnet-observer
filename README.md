# Auratic Frontend - Unified Dashboard SPA

**Status:** ✅ **Fully Operational SPA** (Port 1420 with Hash Routing)  
**Architecture:** Vue 3 + TypeScript + Vite + Pinia  
**Philosophy:** Robust, modular, reactive

---

## 📖 **Documentation**

**👉 [Usage Guide](USAGE_GUIDE.md)** - Complete user guide for getting comfortable with the interface

**👉 [Developer Guide](DEVELOPER_GUIDE.md)** - Technical guide for developers: frontend-backend connections, code patterns, verification methods

---

## 🚀 **Quick Start**

### **Development Mode (Vite)**
Run the Vite development server with hot-reloading:
```bash
# Serves the application on port 1420
./serve.sh
# or directly: npm run dev
```

### **Production / Static Built Mode**
Start the background server serving the compiled static assets in `/dist`:
```bash
# Start background server
./launch-all.sh

# Stop background server
./launch-all.sh --stop
```

---

## 📊 **Unified Views (via Hash Routing)**

All views are part of a unified Single Page Application served on port 1420:

| Path | View Component | Status |
|------|------|--------|
| `http://localhost:1420/#status` | `StatusView.vue` (Main Status & Control) | ✅ Active |
| `http://localhost:1420/#opportunities` | `OpportunitiesView.vue` (Trading Opportunities) | ✅ Active |
| `http://localhost:1420/#auto-discovery` | `AutoDiscoveryView.vue` (Autonomous Pools) | ✅ Active |
| `http://localhost:1420/#galaxy` | `GalaxyView.vue` (3D Market Connections) | ✅ Active |
| `http://localhost:1420/#chart` | `ChartView.vue` (Trading Candlestick & Control Deck) | ✅ Active |
| `http://localhost:1420/#execution` | `ExecutionView.vue` (Real-time Trade Execution) | ✅ Active |
| `http://localhost:1420/#settings` | `SettingsView.vue` (System Settings & Config) | ✅ Active |

---

## 🎯 **Architecture**

### **Vue 3 + Vite + TypeScript**
- Modern Single Page Application (SPA) structure.
- State management powered by Pinia (`stores/systemStatus.js`).
- Dynamic charting using Lightweight Charts, Chart.js, and ECharts.
- Unified event listener structure utilizing native WebSockets.

### **Backend Integration**
- API Base: `http://localhost:8000/api`
- WebSocket: `ws://localhost:8000/ws`
- Read-only - No interference with backend

---

## 📁 **Project Structure**

```
Frontend/
├── index.html              # 1420: MVP Dashboard
├── chartview/              # 1423: Trading Chart View
│   ├── index.html
│   ├── HOW_TO_USE.md
│   └── CHARTVIEW_DESIGN.md
├── creative/               # 1421: Market Connections
├── creative2/              # 1422: Market Connections v2
├── analytics/              # 1424: Performance Analytics
├── risk/                   # 1425: Risk Management
├── execution/              # 1426: Trade Execution
├── input/backups/          # Legacy code for reference
└── serve.sh                # Development server
```

---

## 📚 **Documentation**

### **Frontend-Specific Docs (Here)**
- `README.md` - This file
- `QUICK_START.md` - Quick start guide
- `QUICK_REFERENCE.md` - Quick reference
- `API_MAPPING.md` - API endpoint mapping
- `ARCHITECTURE_DECISION.md` - Architecture decisions
- `ARCHITECTURE_EVALUATION.md` - Architecture evaluation
- `FRONTEND_FACTORY_PLAN.md` - Factory setup plan
- `COMPONENT_INVENTORY.md` - Component inventory
- `AI_DEBUGGING_GUIDE.md` - AI debugging guide
- `DEBUGGING.md` - Debugging guide
- View-specific docs in each view folder

### **Project Management Docs (In Cursor Workspace)**
- Git workflow → `03-Circle-Development/Guides/Git-Workflow/`
- GitHub guides → `03-Circle-Development/Guides/Git-Workflow/`
- Backend logs → `05-Troubleshooting/`
- Status updates → `02-Progress/`
- Bug reports → `03-Circle-Development/Guides/Git-Workflow/bugs/`

---

## 🔧 **Development**

### **No Build Step**
1. Edit HTML/JS files
2. Save
3. Refresh browser
4. Done!

### **Adding New Views**
1. Create new folder (e.g., `port-1427/`)
2. Add `index.html` with view code
3. Add `serve.sh` for development server
4. Add `README.md` for documentation
5. Update this README

---

## 🎯 **Key Features**

### **1420: MVP Dashboard**
- Performance metrics (P&L, win rate, trades)
- Market data table
- Recent trades log
- Emergency stop button
- Trading toggle

### **1423: Trading Chart View**
- Professional candlestick charts
- Position markers (entry/exit lines)
- Real-time price updates
- Symbol selector
- Timeframe selector

### **Other Views**
- 1421/1422: 3D network visualizations
- 1424: Time-series analytics
- 1425: Risk metrics and heat maps
- 1426: Live trade feed

---

## 📝 **Philosophy**

### **"Simple & Stable"**
- No unnecessary complexity
- Easy to understand and debug
- Consistent patterns
- AI-friendly code

### **"Merge, Don't Write"**
- Evaluate existing code from `input/backups`
- Merge working pieces
- Don't rewrite from scratch
- Build on stable foundation

---

## 🔗 **Related Documentation**

**For Git workflow, GitHub, backend, and project management:**
- See Cursor workspace: `/var/home/nhrlyn/Projects/Cursor`
- Git workflow: `03-Circle-Development/Guides/Git-Workflow/`
- Backend docs: `05-Troubleshooting/`
- Status updates: `02-Progress/`

---

**Status:** 🟢 **ALL VIEWS OPERATIONAL** - Frontend complete and ready for use!
