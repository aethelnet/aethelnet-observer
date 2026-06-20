# Visualization Mapping Guide

**What backend data maps to what visual properties**

---

## 🎨 **Visual Properties Mapped to Backend Data**

### **1. Planet Color = Trading Signal**
- **Green** = BUY signal (algorithm suggests buying)
- **Red** = SELL signal (algorithm suggests selling)  
- **Gray** = Neutral/No signal
- **Brightness** = Signal strength (STRONG signals are brighter)

### **2. Planet Size = Trading Volume**
- **Larger planet** = Higher 24-hour trading volume
- Uses logarithmic scale (so huge volumes don't create giant planets)
- **Pulsing** = Volume-based pulse speed (higher volume = faster pulse)

### **3. Rotation Speed = Price Volatility (24h Change)**
- **Faster rotation** = More price change in 24 hours
- More volatile symbols spin faster
- Creates a "volatility" indicator

### **4. Glow Intensity = Price Change**
- **Brighter glow** = More price change (volatility)
- Glows brighter when price is moving more
- Pulsing glow effect

### **5. Floating Speed = Symbol Identity**
- Each planet floats at different speed
- Based on symbol name (for variety)
- Creates organic, living galaxy effect

### **6. Position = Market Position**
- Arranged in 3D spiral pattern
- Even distribution in spherical coordinates
- Creates the "golden ratio spiral" you see

---

## 📊 **Backend Data Fields Used**

From `/api/dashboard/market-data`:

| Field | Maps To | Effect |
|-------|---------|--------|
| `symbol` | Planet identity | Which planet represents which symbol |
| `price` | Info panel | Displayed in sidebar |
| `signal_strength` | Planet color | Green/Red/Gray |
| `volume` | Planet size + pulse speed | Bigger planet, faster pulse |
| `change_24h` | Rotation speed + glow | Faster spin, brighter glow |
| `signal` | (Not used yet) | Could map to orbit radius |

---

## 🔄 **Animations**

1. **Rotation** - Planets spin (speed = volatility)
2. **Pulsing** - Planets grow/shrink (speed = volume)
3. **Glowing** - Planets glow brighter (intensity = volatility)
4. **Floating** - Planets float up/down (organic movement)

---

## 💡 **Future Mappings (Ideas)**

- `signal` value → Orbit radius
- Trade frequency → Particle effects
- Win rate → Planet texture
- P&L → Color gradient
- Drawdown → Warning pulses

---

**Current Status:** ✅ All core mappings working!







