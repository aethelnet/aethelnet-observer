---
tags:
  - type/inventory
  - type/document
  - project/auratic-frontend
  - status/reference
aliases:
  - Component List
  - Code Inventory
---

# Frontend Component Inventory

**Related:** [[FRONTEND_FACTORY_PLAN|Factory Plan]] | [[SETUP_COMPLETE|Setup Complete]]

**Date:** December 29, 2024  
**Location:** Reference Archive  
**Status:** 📦 **EVALUATION PHASE** - Cataloging available code

---

## 📁 **Available Code Snippets**

### **1. `frontend/` (Most Complete - Vue 3 + Tauri)**

**Tech Stack:**
- ✅ Vue 3.3.4 + TypeScript
- ✅ Vite 4.4.5
- ✅ Tailwind CSS 3.3.3
- ✅ Pinia 3.0.4 (state management)
- ✅ Tauri 2.9.4 (desktop app - optional)
- ✅ Chart libraries: ECharts, Lightweight Charts, D3, uPlot
- ✅ Three.js for 3D visualizations
- ✅ GSAP for animations

**Structure:**
```
frontend/
├── src/
│   ├── App.vue                    # Main app (uses HardlineDashboard)
│   ├── components/
│   │   ├── dashboard/            # Dashboard system (8 components)
│   │   ├── widgets/              # 15+ widget components
│   │   ├── visualizers/          # 6 visualization components
│   │   ├── layout/               # Layout components
│   │   └── ui/                   # UI components
│   ├── composables/
│   │   ├── useWebSocket.ts       # WebSocket connection ✅
│   │   ├── useStream.ts          # Data stream with worker ✅
│   │   ├── useAuratic.ts
│   │   ├── useDashboard.ts
│   │   ├── usePersistence.ts
│   │   ├── usePhysics.ts
│   │   └── useSnapshots.ts
│   ├── stores/
│   │   ├── universe.ts           # Main state store ✅
│   │   ├── dashboardStore.ts
│   │   └── systemStatus.ts
│   ├── config/
│   │   ├── constants.ts          # Symbols list ✅
│   │   ├── signalRegistry.ts
│   │   └── widgetRegistry.ts
│   ├── types/
│   │   ├── marketData.d.ts
│   │   └── universe.ts
│   ├── workers/
│   │   └── marketData.worker.ts # Web Worker for data processing
│   └── views/
│       └── HardlineDashboard.vue # Main dashboard view
└── src-tauri/                    # Tauri desktop app config
```

**Key Features:**
- ✅ WebSocket composable (reconnection logic)
- ✅ Stream composable with Web Worker
- ✅ Universe store (comprehensive state management)
- ✅ Dashboard grid system
- ✅ 15+ widget components
- ✅ API URL configurable via env: `VITE_API_URL` (defaults to `http://localhost:8000/api`)

**Widgets Available:**
- ChartWidget, ChronosWidget, ConsoleLogWidget
- GalaxyWidget, GenerativeWidget, MatrixWidget
- PhysicsWidget, SentimentGauge, SentimentOrb
- SnapshotWidget, SpectralWidget, SystemGuideWidget
- SystemWidget, TickerWidget, TopographyWidget
- TradeLogWidget

**Status:** 🟢 **MOST COMPLETE** - Has full dashboard system, state management, WebSocket integration

---

### **2. `frontend (2)`, `frontend (3)`, `frontend (4)`**

**Status:** Appear to be variations/backups of `frontend/`  
**Action:** Compare to see if any have improvements or fixes

---

### **3. `interface/` (Simple Vue 3)**

**Tech Stack:**
- ✅ Vue 3.5.24
- ✅ TypeScript
- ✅ Vite 7.2.4
- ❌ No state management
- ❌ No styling framework

**Structure:**
```
interface/
├── src/
│   ├── App.vue
│   ├── components/
│   │   ├── HelloWorld.vue
│   │   ├── RiskControl.vue      # Risk control component
│   │   └── TradeLog.vue          # Trade log component
│   └── main.ts
```

**Key Features:**
- ✅ Simple structure
- ✅ RiskControl component
- ✅ TradeLog component
- ❌ No API integration
- ❌ No state management

**Status:** 🟡 **SIMPLE** - Basic components, might have useful widgets

---

### **4. `interface (2)/`**

**Status:** Appears to be backup/variation of `interface/`  
**Action:** Compare for differences

---

### **5. `auratic-interface/` (Minimal)**

**Tech Stack:**
- ✅ Vite (rolldown-vite variant)
- ❌ No Vue/React
- ❌ Just basic HTML/JS

**Structure:**
```
auratic-interface/
├── src/
│   ├── counter.js
│   ├── main.js
│   └── style.css
└── index.html
```

**Status:** 🔴 **MINIMAL** - Probably not useful for our needs

---

### **6. `victory-bridge/` (React-based)**

**Tech Stack:**
- ✅ React 19.2.3
- ✅ TypeScript
- ✅ Socket.io-client 4.8.1
- ✅ Zustand 5.0.9 (state management)
- ✅ Ink (terminal UI framework)

**Structure:**
```
victory-bridge/
├── src/
│   └── (React components)
└── market_data.db               # SQLite database
```

**Key Features:**
- ✅ Socket.io client (different from WebSocket)
- ✅ Zustand state management
- ✅ Terminal UI (Ink)
- ✅ Database integration

**Status:** 🟡 **DIFFERENT STACK** - React instead of Vue, might have useful API client code

---

## 🎯 **Recommended Approach**

### **Primary Source: `frontend/`**

**Why:**
- ✅ Most complete implementation
- ✅ Vue 3 + TypeScript (modern stack)
- ✅ Full dashboard system
- ✅ WebSocket integration
- ✅ State management (Pinia)
- ✅ Widget system
- ✅ API URL configurable

**What to Use:**
1. **Core Structure:** Use `frontend/` as base
2. **Components:** All widgets and dashboard components
3. **Composables:** `useWebSocket.ts`, `useStream.ts`
4. **Stores:** `universe.ts` (main store)
5. **Config:** `constants.ts` for symbols

### **Secondary Sources:**

1. **`interface/` components:**
   - Check `RiskControl.vue` - might be useful
   - Check `TradeLog.vue` - compare with `TradeLogWidget.vue`

2. **`victory-bridge/`:**
   - Check Socket.io client code (if we need Socket.io instead of WebSocket)
   - Check database integration approach

3. **Compare `frontend (2)`, `(3)`, `(4)`:**
   - See if any have bug fixes or improvements
   - Check for different API integrations

---

## 📋 **Component Checklist**

### **Core Infrastructure:**
- [x] ✅ WebSocket composable (`useWebSocket.ts`)
- [x] ✅ Stream composable (`useStream.ts`)
- [x] ✅ State store (`universe.ts`)
- [x] ✅ API URL configuration
- [x] ✅ Dashboard system
- [x] ✅ Widget registry

### **Widgets Needed (from backend API):**
- [x] ✅ Metrics widget (P&L, win rate, trades)
- [x] ✅ Control widget (emergency stop, trading toggle)
- [x] ✅ Market data widget (prices, signals)
- [x] ✅ Positions widget (open positions)
- [x] ✅ Trades widget (trade history)
- [x] ✅ Week test widget (validation progress)

### **Available Widgets:**
- [x] ✅ TradeLogWidget (trades)
- [x] ✅ TickerWidget (market data)
- [x] ✅ SystemWidget (metrics?)
- [x] ✅ ChartWidget (charts)
- [ ] ⚠️ Need: Control widget (emergency stop)
- [ ] ⚠️ Need: Positions widget
- [ ] ⚠️ Need: Week test widget

---

## 🔧 **Next Steps**

### **Phase 1: Evaluation (Now)**
1. ✅ Create this inventory
2. ⏳ Compare `frontend (2)`, `(3)`, `(4)` for differences
3. ⏳ Check `interface/` components for useful code
4. ⏳ Review `victory-bridge/` API client approach

### **Phase 2: Assembly (Next)**
1. ⏳ Use `frontend/` as base
2. ⏳ Copy working components
3. ⏳ Update API endpoints to match backend
4. ⏳ Test WebSocket connection
5. ⏳ Create missing widgets (Control, Positions, Week Test)

### **Phase 3: Integration (After Assembly)**
1. ⏳ Connect to backend API
2. ⏳ Test all widgets
3. ⏳ Verify real-time updates
4. ⏳ Fix any integration issues

---

## 💡 **Key Insights**

**What Works:**
- ✅ Complete Vue 3 + TypeScript setup
- ✅ WebSocket integration with reconnection
- ✅ State management with Pinia
- ✅ Dashboard grid system
- ✅ Widget architecture

**What Needs:**
- ⚠️ Update API endpoints to match backend
- ⚠️ Create missing widgets (Control, Positions, Week Test)
- ⚠️ Test WebSocket connection to `ws://localhost:8000/ws`
- ⚠️ Verify data format matches backend

**What to Avoid:**
- ❌ Don't force performance optimizations first
- ❌ Don't over-engineer
- ❌ Don't merge everything at once
- ✅ Start simple, add complexity gradually

---

**Status:** 📦 **INVENTORY COMPLETE** - Ready to start assembly phase.

**Next:** Compare variations, then start merging working components.

