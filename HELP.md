# Frontend Help & Documentation

Complete guide to all controls and features across all 7 frontend views.

## Quick Access

- **Press F1** or **?** on any page to open help
- **Hover** over any control to see tooltips
- **Click** the **?** button in the bottom-right corner

---

## Port 1420 - MVP Dashboard

### Controls

#### Emergency Stop Button 🛑
- **What it does:** Immediately halts all trading activity
- **When to use:** Emergency situations only
- **Effect:** Stops all open positions and prevents new trades
- **Note:** Requires manual confirmation and can be resumed later

#### Trading Toggle Button ⏸️
- **What it does:** Enable or disable the trading system
- **When to use:** To pause trading without emergency stop
- **Effect:** Stops new trades but continues monitoring
- **Status:** Shows ACTIVE or PAUSED

#### Navigation Links
- **Analytics:** View performance metrics and charts
- **Chartview:** Interactive trading chart with Control Deck
- **Creative:** 3D market connections visualization
- **Execution:** Real-time trade execution monitor

---

## Port 1423 - Trading Chart View

### Control Deck

The Control Deck provides comprehensive control over chart visualization and parameters.

#### Layer Toggles

**📊 HIST** - Historical Data
- Shows historical candlestick data from Binance
- Displays price action over time
- Includes entry/exit markers from past trades

**⚡ LIVE** - Live Updates
- Real-time price updates via WebSocket
- Shows current market price as it changes
- Updates continuously

**📈 VOL** - Volume Bars
- Trading volume for each time period
- Higher volume indicates stronger price movements
- Helps identify significant market activity

**🎮 SIM** - Simulation Lines
- Predicted or simulated price movements
- Based on physics factors and parameters
- Useful for testing strategies

**👻 GHOST** - Ghost Series
- Alternative price series for comparison
- Shadow data for different market views
- Compare multiple data sources

**💧 LIQUID** - Liquidity Markers
- Areas of high trading activity
- Market depth visualization
- Shows where liquidity is concentrated

**💰 TRADES** - Trade Markers
- Historical trade entry/exit points
- Green markers = entry, Red markers = exit
- Shows past trading activity on chart

**📡 SIGNALS** - Signal Markers
- Trading signals from the system
- Buy/sell recommendations
- Includes confidence levels

#### Master Control Sliders

**Aggregation Sensitivity**
- **Range:** 0.1 - 5.0
- **Recommended:** 1.0 - 2.0
- **What it does:** Controls how sensitive the system is to price movements
- **Higher values:** More sensitive, reacts to smaller movements
- **Lower values:** Less sensitive, requires larger movements

**Signal Fidelity**
- **Range:** 0.0 - 1.0
- **Recommended:** 0.3 - 0.7
- **What it does:** Smoothing factor for price signals
- **0.0:** Raw data, no smoothing
- **1.0:** Maximum smoothing, delayed signals
- **Higher values:** Reduces noise but may delay signals

#### Physics Parameters

**Friction**
- **Range:** 0.0 - 1.0
- **Recommended:** 0.2 - 0.5
- **What it does:** Simulates market friction/resistance
- **Higher values:** Slower price movements in simulations
- **Lower values:** Faster, more responsive movements

**Elasticity**
- **Range:** 0.0 - 2.0
- **Recommended:** 0.8 - 1.2
- **What it does:** Controls price bounce-back behavior
- **Higher values:** More elastic (bouncy) behavior
- **Lower values:** Less elastic, more damped

#### Simulation Parameters

**Drift (Bias)**
- **Range:** -1.0 to 1.0
- **Recommended:** -0.2 to 0.2
- **What it does:** Bias term for price direction
- **Positive:** Upward bias
- **Negative:** Downward bias
- **0:** No bias

**Volatility (Noise)**
- **Range:** 0.0 - 2.0
- **Recommended:** 0.1 - 0.5
- **What it does:** Adds random noise to simulations
- **Higher values:** More volatility
- **0:** No noise

#### Toolbar Controls

**Symbol Selector**
- Choose which trading pair to display
- Options: BTCUSDT, ETHUSDT, SOLUSDT, etc.
- Updates chart and data for selected symbol

**Timeframe Buttons**
- **1m, 5m, 15m, 1h, 4h, 1d**
- Change the time period for each candlestick
- Affects historical data granularity

**Control Deck Toggle**
- **HIDE/SHOW:** Minimize or restore the Control Deck
- Saves screen space when not needed

---

## Port 1421 - Market Connections (Creative)

### Controls

**Reset View**
- Returns 3D camera to default position and angle
- Useful when you've rotated or zoomed too far

**Toggle Connections**
- Show/hide connection lines between market nodes
- Connections represent correlations between markets

**Toggle Labels**
- Show/hide correlation values on connection lines
- Labels show the strength of relationships

**Reset Filter**
- Resets correlation filter to 30% threshold
- Shows only connections above this threshold

### Mouse Controls

- **Drag:** Rotate the 3D view
- **Scroll:** Zoom in/out
- **Click node:** Highlight connections for that market

---

## Port 1422 - Market Connections v2

### Controls

**📊 Chart**
- Toggle price history chart overlay
- Shows detailed price movements for selected market

**🔄 Reset**
- Return 3D camera to default position
- Resets view to initial state

**🏷️ Labels**
- Show/hide market name labels on nodes
- Useful for identifying specific markets

**🐛 Debug**
- Show/hide debug information panel
- Technical details about the visualization

### Interaction

- **Click node:** Select a market to see its price chart
- **Drag:** Rotate the 3D view
- **Scroll:** Zoom in/out
- **Click market in list:** Select and focus on that market

---

## Port 1424 - Performance Analytics

### Overview
Displays comprehensive performance analytics including P&L metrics, win rates, trade statistics, and visual charts.

### Metrics

- **Total P&L:** Combined profit/loss from all trades
- **Win Rate:** Percentage of profitable trades
- **Total Trades:** Number of completed trades
- **Average P&L:** Average profit/loss per trade
- **Best Trade:** Highest profit from a single trade
- **Worst Trade:** Largest loss from a single trade

### Charts
Visual representations of trading performance over time, including:
- Equity curve
- P&L timeline
- Win rate trend
- Drawdown periods
- Trade P&L distribution

### Data Updates
Metrics and charts update automatically every 5 seconds from the trading backend.

---

## Port 1425 - Risk Management

### Overview
Monitors risk metrics and alerts you to potential issues with your trading system.

### Risk Alerts

- **Critical:** Immediate action required - trading may be halted
- **Warning:** Risk levels elevated - monitor closely
- **Info:** Important risk information

### Risk Metrics

- **Max Drawdown:** Largest peak-to-trough decline
- **Position Size:** Current position sizing
- **Exposure:** Total market exposure
- **Leverage:** Current leverage ratio

### Charts
Visual representations of risk metrics over time, including:
- Drawdown history
- Position sizing trends
- Risk heat maps
- Correlation matrices

### Data Updates
Risk metrics update automatically every 5 seconds from the trading backend.

---

## Port 1426 - Trade Execution Monitor

### Overview
Shows real-time trade execution data, including live trade feed, execution metrics, and trade timeline.

### Live Trade Feed
Shows trades as they execute in real-time, including:
- Entry and exit prices
- Trade direction (LONG/SHORT)
- P&L for each trade
- Hold time and slippage

### Execution Metrics

- **Total Trades:** Number of executed trades
- **Success Rate:** Percentage of profitable trades
- **Avg Slippage:** Average price slippage on execution
- **Avg Hold Time:** Average time positions are held

### Trade Timeline
Chart showing a timeline of all trades, helping visualize trading activity over time.

### Data Updates
Trade feed and metrics update automatically in real-time via WebSocket connection.

---

## Keyboard Shortcuts

- **F1** or **?:** Show help modal (on any page)
- **ESC:** Close help modal
- **Tab:** Navigate between controls (accessibility)

---

## Troubleshooting

### Backend Not Connected
- Check that backend is running on `http://localhost:8000`
- Verify API endpoint is accessible
- Check browser console for connection errors

### Charts Not Loading
- Ensure Chart.js or Lightweight Charts library loaded
- Check browser console for JavaScript errors
- Verify data is being received from backend

### Controls Not Responding
- Refresh the page
- Check browser console for errors
- Verify help-system.js is loaded

### Tooltips Not Showing
- Ensure help-system.js is included
- Check that `window.helpSystem` is available
- Hover over controls to trigger tooltips

---

## Additional Resources

- **Backend API:** `http://localhost:8000/api`
- **WebSocket:** `ws://localhost:8000/ws`
- **Documentation:** See individual view README files

---

## Getting Help

1. **Hover** over any control for instant tooltips
2. **Press F1** or **?** for full help modal
3. **Click** the **?** button in bottom-right corner
4. Check browser console for detailed error messages

---

*Last updated: December 31, 2024*




