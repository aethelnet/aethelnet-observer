# Browser Workflow Guide - Vivaldi/Chromium

**Quick reference for development workflow**

---

## 🔄 **Refresh Shortcuts (Vivaldi/Chromium)**

### **Standard Refresh**
- **Ctrl+R** - Normal refresh (may use cache)
- **F5** - Same as Ctrl+R

### **Hard Refresh (Clear Cache)**
- **Ctrl+Shift+R** - Hard refresh (bypasses cache) ⭐ **USE THIS**
- **Ctrl+F5** - Same as Ctrl+Shift+R

### **Developer Tools Refresh**
- **F12** - Open DevTools
- **Right-click refresh button** → "Empty Cache and Hard Reload"

---

## 🎯 **Recommended Workflow**

### **During Development:**
1. Make code changes
2. Save file
3. **Ctrl+Shift+R** (hard refresh) in browser
4. Check console for `[Creative]` logs
5. See changes immediately

### **If Changes Don't Appear:**
1. **Ctrl+Shift+R** (hard refresh)
2. Still not working? **F12** → Right-click refresh → "Empty Cache and Hard Reload"
3. Check console for errors

---

## 🛠️ **Quick Tips**

### **Keep DevTools Open**
- **F12** to toggle
- Keep Console tab open to see `[Creative]` logs
- Watch for errors in red

### **Multiple Tabs**
- **MVP:** http://localhost:1420 (reference)
- **Creative:** http://localhost:1421 (experimental)
- Keep both open in different tabs

### **Cache Issues?**
- Vivaldi/Chromium caches aggressively
- Always use **Ctrl+Shift+R** during development
- Or disable cache in DevTools (Network tab → "Disable cache" checkbox)

---

## 📝 **Keyboard Shortcuts Cheat Sheet**

| Action | Shortcut |
|--------|----------|
| Normal refresh | Ctrl+R or F5 |
| **Hard refresh** | **Ctrl+Shift+R** ⭐ |
| Open DevTools | F12 |
| Close DevTools | F12 (toggle) |
| Clear console | Ctrl+L (in console) |
| Focus address bar | Ctrl+L |

---

## 🔧 **Pro Tip: Disable Cache in DevTools**

1. Open DevTools (F12)
2. Go to **Network** tab
3. Check **"Disable cache"** checkbox
4. Keep DevTools open while developing
5. Now Ctrl+R will always bypass cache!

---

**Remember:** During development, always use **Ctrl+Shift+R** for hard refresh! 🚀







