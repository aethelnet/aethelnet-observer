---
tags:
  - type/reference
  - type/cheatsheet
  - project/auratic-frontend
  - status/active
  - excalibrain/favorite
aliases:
  - Cheat Sheet
  - Quick Ref
---

# Quick Reference Card

**One-page cheat sheet for daily use**

**Related:** [[README|README]] | [[QUICK_START|Quick Start]] | [[OBSIDIAN_VAULT|Obsidian Vault]]

---

## 🚀 **Start Development**

```bash
./serve.sh                    # Start HTTP server on port 1420
# Open http://localhost:1420 in browser
```

---

## 📊 **Watch Backend Logs**

```bash
./watch_logs.sh errors        # 🔴 Only errors
./watch_logs.sh trades        # 💰 Only trades  
./watch_logs.sh api           # 🌐 Only API calls
./watch_logs.sh metrics       # 📊 Only metrics
./watch_logs.sh websocket     # 🔌 WebSocket activity
./watch_logs.sh all           # 📋 Everything
```

---

## 🔍 **Check Backend**

```bash
./check_endpoints.sh          # List all API endpoints
./log_stats.sh                # Show log statistics
curl http://localhost:8000/api/dashboard/metrics
```

---

## 📡 **API Endpoints**

| Endpoint | Purpose |
|----------|---------|
| `GET /api/dashboard/metrics` | P&L, win rate, trades |
| `GET /api/dashboard/market-data` | Prices, signals |
| `GET /api/dashboard/recent-trades` | Trade history |
| `POST /api/failsafe/panic` | Emergency stop |
| `POST /api/failsafe/resume` | Resume trading |
| `GET /api/failsafe/status` | Trading status |
| `GET /docs` | API documentation |

---

## 🎯 **Frontend File**

- **Main file:** `index.html` (everything in one file!)
- **Edit → Save → Refresh** (no build step)

## 🌿 **Git Workflow**

```bash
# Start new feature
git checkout mvp
git checkout -b feature/port-142X-name

# Commit changes
git add .
git commit -m "Feature: Description"

# Merge when done
git checkout mvp
git merge feature/port-142X-name
```

**See:** `GIT_WORKFLOW.md` for full guide

---

## 🐛 **Debugging**

1. **Browser Console** (F12) - Frontend errors
2. **`./watch_logs.sh errors`** - Backend errors
3. **`./check_endpoints.sh`** - Verify API endpoints

---

## 📚 **Documentation**

- `QUICK_START.md` - Development workflow
- `BACKEND_LOGS.md` - Log filtering guide
- `OBSIDIAN_VAULT.md` - Full vault documentation
- `README.md` - Project overview

---

**Pro Tip:** Pin this file in Obsidian for quick access!

