---
tags:
  - type/plan
  - type/document
  - project/auratic-frontend
  - workflow/factory
  - status/reference
aliases:
  - Factory Plan
  - MVP Plan
---

# Frontend Factory - Clean MVP Setup

**Related:** [[SETUP_COMPLETE|Setup Complete]] | [[COMPONENT_INVENTORY|Component Inventory]]

**Date:** December 29, 2024  
**Philosophy:** Build clean, don't break what works, incremental assembly  
**Strategy:** Factory approach - assemble working pieces into MVP

---

## 🎯 **Factory Philosophy**

### **Backend Model:**
- ✅ Backend is stable, don't touch it
- ✅ It works, we preserve it
- ✅ We build on top, don't break it

### **Frontend Model:**
- 🏭 **Factory Setup:** Clean new project
- 📦 **Input Folder:** Reference only (don't work in it)
- 🔧 **Assembly:** Copy working pieces, don't modify originals
- 🚀 **MVP First:** Get something working, then add features
- 🌿 **Branch Safety:** Use branches to protect working code

---

## 🏗️ **Factory Structure**

```
Frontend/
├── input/                    # 📦 REFERENCE ONLY (don't work here)
│   └── backups/             # All previous attempts
├── src/                      # 🏭 FACTORY (clean new project)
│   ├── components/          # Working components (copied from input)
│   ├── composables/        # API clients, WebSocket (copied)
│   ├── stores/             # State management (copied)
│   └── ...
├── .gitignore               # Excludes input/ folder
└── README.md
```

**Key Principle:** 
- `input/` = Library of parts (read-only reference)
- `src/` = Factory floor (where we build)

---

## 🚀 **MVP Goals**

### **Phase 1: MVP (Must Work)**
1. ✅ Connect to backend API (`http://localhost:8000/api`)
2. ✅ Connect to backend WebSocket (`ws://localhost:8000/ws`)
3. ✅ Display metrics (P&L, win rate, trades)
4. ✅ Display market data (prices, signals)
5. ✅ Display positions (open positions)
6. ✅ Display trades (trade history)
7. ✅ Basic control (emergency stop button)

**Success Criteria:**
- ✅ Can see backend data
- ✅ Real-time updates work
- ✅ No crashes
- ✅ Simple, clean UI

### **Phase 2: Polish (After MVP Works)**
- Add more widgets
- Improve styling
- Add animations
- Add more controls

---

## 🌿 **Git Branch Strategy**

### **Branches:**
- `main` - Production-ready code (protected)
- `mvp` - MVP branch (working baseline)
- `feature/*` - New features (merge to mvp, then main)

### **Workflow:**
1. **Start on `mvp` branch:**
   ```bash
   git checkout -b mvp
   ```

2. **Build MVP:**
   - Copy working pieces from `input/`
   - Assemble into working MVP
   - Test with backend
   - Commit when working

3. **Add Features:**
   ```bash
   git checkout -b feature/new-widget
   # Add feature
   git checkout mvp
   git merge feature/new-widget
   # Test, then merge to main if stable
   ```

4. **Protect `main`:**
   - Only merge from `mvp` when stable
   - `main` always works

---

## 📋 **Assembly Plan**

### **Step 1: Create Clean Project**
- ✅ Initialize Vue 3 + TypeScript + Vite
- ✅ Install dependencies (Pinia, Tailwind, etc.)
- ✅ Set up basic structure

### **Step 2: Copy Working Pieces**
From `input/backups/frontend/`:
- ✅ `composables/useWebSocket.ts` - WebSocket connection
- ✅ `composables/useStream.ts` - Data stream (if needed)
- ✅ `stores/universe.ts` - State management (adapt for our needs)
- ✅ `config/constants.ts` - Symbols list
- ✅ Widget components (as needed)

### **Step 3: Create MVP Widgets**
- ✅ MetricsWidget - P&L, win rate, trades
- ✅ MarketDataWidget - Prices, signals
- ✅ PositionsWidget - Open positions
- ✅ TradesWidget - Trade history
- ✅ ControlWidget - Emergency stop

### **Step 4: Connect to Backend**
- ✅ Update API URL to `http://localhost:8000/api`
- ✅ Update WebSocket URL to `ws://localhost:8000/ws`
- ✅ Test connection
- ✅ Verify data flow

### **Step 5: Test & Iterate**
- ✅ Test with running backend
- ✅ Fix any integration issues
- ✅ Ensure real-time updates work
- ✅ Commit working MVP

---

## 🔧 **Tech Stack (MVP)**

**Core:**
- Vue 3 + TypeScript
- Vite (build tool)
- Pinia (state management)

**Styling:**
- Tailwind CSS (utility-first)

**API:**
- Fetch API (HTTP)
- WebSocket API (real-time)

**Charts (if needed):**
- Lightweight Charts (simple, fast)

**No Tauri (yet):**
- Focus on browser version first
- Add desktop app later if needed

---

## 📝 **Assembly Checklist**

### **Setup:**
- [ ] Create clean Vue 3 project
- [ ] Set up git branches (main, mvp)
- [ ] Install dependencies
- [ ] Configure Tailwind
- [ ] Set up API configuration

### **Core Infrastructure:**
- [ ] Copy WebSocket composable
- [ ] Copy/adapt state store
- [ ] Create API client
- [ ] Set up environment variables

### **MVP Widgets:**
- [ ] MetricsWidget
- [ ] MarketDataWidget
- [ ] PositionsWidget
- [ ] TradesWidget
- [ ] ControlWidget

### **Integration:**
- [ ] Connect to backend API
- [ ] Connect to backend WebSocket
- [ ] Test data flow
- [ ] Verify real-time updates

### **Polish:**
- [ ] Basic styling
- [ ] Error handling
- [ ] Loading states
- [ ] Responsive layout

---

## 🚫 **What NOT to Do**

- ❌ Don't work in `input/` folder
- ❌ Don't modify original backup files
- ❌ Don't add features before MVP works
- ❌ Don't optimize prematurely
- ❌ Don't break what works

## ✅ **What TO Do**

- ✅ Copy files from `input/` to `src/`
- ✅ Adapt copied code for our needs
- ✅ Test incrementally
- ✅ Commit working code
- ✅ Use branches for safety
- ✅ Build MVP first, add features later

---

## 🎯 **Success Definition**

**MVP is "done" when:**
- ✅ Can see backend metrics
- ✅ Can see market data
- ✅ Can see positions
- ✅ Can see trades
- ✅ Can trigger emergency stop
- ✅ Real-time updates work
- ✅ No crashes
- ✅ Clean, simple UI

**Then we can:**
- Add more widgets
- Improve styling
- Add animations
- Add more features

---

**Status:** 🏭 **FACTORY READY** - Let's build clean MVP from working pieces.

