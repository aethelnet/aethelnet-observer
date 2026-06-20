# Market Connections Network - Port 1421

**Interactive 3D network visualization for ML tuning**

---

## 🎯 **Purpose**

This visualization shows how trading markets are connected through correlations. Perfect for:
- **ML Tuning**: Understanding which markets move together
- **Market Analysis**: Seeing correlation patterns
- **Trading Strategy**: Identifying connected market groups

---

## 🚀 **Quick Start**

```bash
cd creative
./serve.sh
# Open http://localhost:1421
```

---

## 🎮 **Features**

### **Interactive Controls**
- **Click Nodes**: Select a trading symbol to see its connections
- **Drag**: Rotate the 3D view
- **Scroll**: Zoom in/out
- **Correlation Filter**: Adjust minimum correlation (0-100%)
- **Toggle Connections**: Show/hide all connection lines
- **Toggle Labels**: Show/hide correlation labels
- **Reset View**: Return camera to default position
- **Reset Filter**: Restore 30% minimum correlation

### **Visualization**
- **Nodes** = Trading symbols (BTCEUR, ETHEUR, etc.)
- **Node Color** = Trading signal (Green=Buy, Red=Sell, Gray=Neutral)
- **Node Size** = Trading volume
- **Connection Lines** = Market correlations
- **Line Color** = Correlation strength (Green=Strong, Yellow=Medium, Gray=Weak)
- **Labels** = Symbol names + correlation percentages

### **Correlation Calculation**
Based on:
1. **Price Movement** (50% weight) - How similar are 24h price changes
2. **Signal Alignment** (30% weight) - Do signals point same direction
3. **Volume Similarity** (20% weight) - Similar trading activity

---

## 📊 **How to Use**

1. **Explore Connections**: Click different nodes to see which markets are connected
2. **Filter by Strength**: Use the slider to show only strong correlations (e.g., 70%+)
3. **Read Labels**: Toggle labels to see exact correlation percentages
4. **Focus View**: Click a node to highlight only its connections

---

## 🔧 **Technical Details**

- **Framework**: Vanilla JavaScript + Three.js
- **Port**: 1421
- **API**: Same backend as MVP (`http://localhost:8000/api`)
- **Auto-refresh**: Updates every 10 seconds

---

## 📝 **Status**

✅ **Complete and Polished**
- Interactive node selection
- Correlation filtering
- Connection highlighting
- Label system
- Smooth animations

---

**Ready for ML tuning!** 🎯
