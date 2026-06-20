# Browser Refresh Tips

**Quick reference for seeing your code changes**

---

## ✅ **Yes, Your Servers Reflect Current Code!**

The HTTP servers (`python3 -m http.server` or `php -S`) serve files **directly from disk**. This means:

- ✅ **Changes are immediate** - No need to restart servers
- ✅ **Just refresh browser** - Changes appear after refresh
- ✅ **Branch switches work** - Files on disk change when you switch branches

---

## 🔄 **Refresh Methods**

### **Standard Refresh:**
- **Windows/Linux:** `Ctrl + R` or `F5`
- **Mac:** `Cmd + R`

### **Hard Refresh (Clear Cache):**
- **Windows/Linux:** `Ctrl + Shift + R` or `Ctrl + F5`
- **Mac:** `Cmd + Shift + R`
- **Vivaldi/Chrome:** `Ctrl + Shift + R` (recommended for development)

### **Why Hard Refresh?**
- Clears browser cache
- Forces reload of all assets (HTML, CSS, JS)
- Ensures you see the latest code changes
- **Always use hard refresh during development!**

---

## 🎯 **Quick Workflow**

1. **Edit code** in your editor
2. **Save file** (Ctrl+S / Cmd+S)
3. **Hard refresh browser** (Ctrl+Shift+R)
4. **Check console** (F12) for logs/errors
5. **See changes immediately!**

---

## 🔍 **Verifying You See Latest Code**

### **Check Console Logs:**
- Look for `[Risk] [DEBUG]` logs (if on 1425)
- Check timestamps in logs
- Verify function calls match your latest code

### **Check Network Tab:**
- Open DevTools → Network tab
- Hard refresh
- Check if files are loaded from cache or server
- Look for "200" status codes

### **Add Temporary Log:**
```javascript
console.log('Code updated at:', new Date().toISOString());
```
- Add this to your code
- Hard refresh
- Check console for timestamp
- If timestamp updates, you're seeing latest code!

---

## ⚠️ **Common Issues**

### **Not Seeing Changes?**
1. **Hard refresh** (Ctrl+Shift+R) - Most common fix!
2. **Check you're on correct branch** - `git branch --show-current`
3. **Verify file was saved** - Check file timestamp
4. **Clear browser cache** - Settings → Clear browsing data
5. **Check server is running** - Look at terminal output

### **Server Not Running?**
```bash
# Check if server is running
ps aux | grep "http.server"

# Restart if needed
cd risk && ./serve.sh  # or any other view
```

### **Wrong Branch?**
```bash
# Check current branch
git branch --show-current

# Switch if needed
git checkout experimental  # or mvp, main
```

---

## 🚀 **Pro Tips**

1. **Always hard refresh during development** - Avoids cache issues
2. **Keep DevTools open** - See errors/logs immediately
3. **Watch console while coding** - Catch errors early
4. **Use browser DevTools** - Inspect, debug, test
5. **Check Network tab** - Verify files are loading correctly

---

## 📝 **For Your Current Situation**

Since you have servers running:
- ✅ **Just hard refresh** (Ctrl+Shift+R) in each browser tab
- ✅ **Check console** (F12) for debug logs
- ✅ **No need to restart servers** - They serve current files
- ✅ **Branch switches work** - Files on disk reflect current branch

**You're all set!** Just refresh and you'll see the latest code. 🎉







