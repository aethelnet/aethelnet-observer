---
tags:
  - type/guide
  - type/tutorial
  - project/auratic-frontend
  - workflow/development
  - status/active
aliases:
  - Getting Started
  - Development Guide
---

# Quick Start Guide - Simple HTML Workflow

**Welcome to the simple HTML workflow!** This guide helps you get comfortable with this approach.

**Related:** [[README|README]] | [[QUICK_REFERENCE|Quick Reference]] | [[OBSIDIAN_VAULT|Obsidian Vault]]

---

## 🚀 **How to Run**

### Option 1: Direct File Open (Simplest)
```bash
# Just open the HTML file in your browser
firefox index.html
# or
google-chrome index.html
```

**Note:** Some browsers may block WebSocket connections when opening files directly. If you see connection errors, use Option 2.

### Option 2: Simple HTTP Server (Recommended)
```bash
# Python 3 (most common)
python3 -m http.server 1420

# Then open: http://localhost:1420
```

```bash
# Or with Node.js (if you have it)
npx serve -p 1420

# Or with PHP
php -S localhost:1420
```

---

## 🔧 **Development Workflow**

### **1. Edit the HTML File**
- Open `index.html` in your editor
- Make changes directly
- Save the file
- Refresh your browser (F5 or Ctrl+R)

**That's it!** No build step, no compilation, just edit and refresh.

### **2. Test Backend Connection**
The dashboard expects:
- **API:** `http://localhost:8000/api` (required)
- **WebSocket:** `ws://localhost:8000/ws` (optional - for instant updates)

**Important:** The dashboard works perfectly with API polling alone. WebSocket failures are expected if the backend WebSocket endpoint isn't available, but this doesn't affect functionality.

If backend API is not running, you'll see:
- Status: "Disconnected" (red)
- Metrics show "--"
- Console shows connection errors

### **3. Browser DevTools**
**Press F12** to open developer tools:
- **Console tab:** See logs, errors, WebSocket messages
- **Network tab:** See API requests
- **Elements tab:** Inspect HTML/CSS

---

## 📝 **File Structure**

```
Frontend/
├── index.html          # 🎯 Main file - edit this!
├── .gitignore          # Git ignore rules
├── README.md           # Project overview
└── QUICK_START.md      # This file
```

**Everything is in one file:** HTML, CSS, and JavaScript are all in `index.html`.

---

## 🎨 **Making Changes**

### **Add a New Metric**
1. Find the metrics section in HTML (around line 190)
2. Add a new `<div class="metric">` entry
3. Add JavaScript to update it in `updateMetrics()` function
4. Refresh browser

### **Change Colors/Styles**
- All CSS is in the `<style>` tag (around line 11)
- Edit directly, save, refresh

### **Add a New API Endpoint**
1. Create a new `fetchXxx()` function
2. Call it in `init()` function
3. Add auto-refresh with `setInterval()` if needed

---

## 🐛 **Debugging Tips**

### **Check Console**
Open browser console (F12) and look for:
- `[ERROR]` - Something broke
- Connection errors - Backend might be down
- WebSocket messages - Real-time data flow

### **Test API Endpoints**
```bash
# Test if backend is running
curl http://localhost:8000/api/metrics

# Should return JSON data
```

### **Common Issues**

**"Disconnected" status:**
- Backend not running? Start it first
- Wrong port? Check `API_BASE` in JavaScript (line 233)

**Charts not showing:**
- Check browser console for Chart.js errors
- Make sure internet connection works (Chart.js loads from CDN)

**WebSocket not connecting:**
- This is **expected** if the backend WebSocket endpoint isn't available
- The dashboard works perfectly with API polling (updates every 5-10 seconds)
- WebSocket is optional - only provides instant updates if available
- Check console for `[WebSocket]` logs to see connection attempts

---

## 💡 **Workflow Tips**

### **1. Keep It Simple**
- One file = easy to understand
- No build step = instant feedback
- Vanilla JS = no framework complexity

### **2. Incremental Changes**
- Make small changes
- Test after each change
- Commit when something works

### **3. Use Browser DevTools**
- Inspect elements
- Test JavaScript in console
- Monitor network requests

### **4. Version Control**
```bash
# Commit working changes
git add index.html
git commit -m "Add trades history section"

# Create branches for experiments
git checkout -b feature/new-widget
```

---

## 🔄 **Collaboration Workflow**

### **With AI (like me):**
1. Tell me what you want to change
2. I'll edit `index.html` directly
3. You refresh browser to see changes
4. Tell me if something doesn't work

### **With Team:**
1. Edit `index.html`
2. Test locally
3. Commit changes
4. Push to git
5. Others pull and refresh browser

**No build conflicts, no dependency issues, just one file!**

---

## 📚 **What's in the HTML File?**

The file is organized in sections:

1. **HTML Structure** (lines 1-230)
   - Header, cards, charts, controls

2. **CSS Styles** (lines 11-176)
   - All styling in `<style>` tag

3. **JavaScript** (lines 231-450)
   - Configuration
   - Chart initialization
   - API functions
   - WebSocket handling
   - Event handlers

**Everything is in one place - easy to find and edit!**

---

## ✅ **Quick Checklist**

Before starting work:
- [ ] Backend running on `localhost:8000`?
- [ ] HTTP server running (if needed)?
- [ ] Browser console open (F12)?
- [ ] `index.html` open in editor?

After making changes:
- [ ] Saved the file?
- [ ] Refreshed browser?
- [ ] Checked console for errors?
- [ ] Tested the feature?

---

## 🎯 **Next Steps**

1. **Start the backend** (if you have it)
2. **Open `index.html`** in browser or start HTTP server
3. **Open browser console** (F12) to see what's happening
4. **Make a small change** to see the workflow
5. **Get comfortable** with edit → save → refresh cycle

**You're all set!** This simple workflow is designed to be:
- ✅ Fast (no build step)
- ✅ Clear (one file)
- ✅ Reliable (proven tech)
- ✅ AI-friendly (easy to understand and modify)

---

**Questions?** Just ask! The beauty of this approach is its simplicity.

