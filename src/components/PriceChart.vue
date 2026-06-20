<template>
  <div class="price-chart-container" ref="containerRef">
    <!-- Chart Controls -->
    <div v-if="!loading && !error" class="chart-controls">
      <div class="controls-row">
        <select v-model="localTimeframe" @change="onTimeframeChange" class="control-select">
          <option value="1m">1m</option>
          <option value="5m">5m</option>
          <option value="15m">15m</option>
          <option value="1h">1h</option>
        </select>
        
        <button @click="toggleViewMode" class="control-btn">
          {{ localViewMode === 'line' ? 'Candlesticks' : 'Line' }}
        </button>
        
        <label class="control-checkbox">
          <input type="checkbox" v-model="localShowVolume" />
          Volume
        </label>
        
        <label class="control-checkbox">
          <input type="checkbox" v-model="localShowIndicators" />
          Indicators
        </label>
        
        <select v-if="localShowIndicators" v-model="selectedIndicators" multiple class="control-select indicators-select">
          <option value="MA">MA (SMA)</option>
          <option value="EMA">EMA</option>
          <option value="RSI">RSI</option>
          <option value="MACD">MACD</option>
          <option value="Bollinger">Bollinger Bands</option>
          <option value="Stochastic">Stochastic</option>
          <option value="VWAP">VWAP</option>
          <option value="ATR">ATR</option>
        </select>
        
        <button v-if="props.zoomEnabled" @click="resetZoom" class="control-btn">Reset Zoom</button>
      </div>
      
      <!-- Layer Toggles (Control Deck) -->
      <div class="layer-controls">
        <label class="layer-toggle" :class="{ active: props.showPositions }">
          <input type="checkbox" :checked="props.showPositions" @change="$emit('toggle-layer', { layer: 'positions', enabled: ($event.target as HTMLInputElement).checked })" />
          <span>Positions</span>
        </label>
        <label class="layer-toggle" :class="{ active: props.showTrades }">
          <input type="checkbox" :checked="props.showTrades" @change="$emit('toggle-layer', { layer: 'trades', enabled: ($event.target as HTMLInputElement).checked })" />
          <span>Trades</span>
        </label>
        <label class="layer-toggle" :class="{ active: props.showOpportunities }">
          <input type="checkbox" :checked="props.showOpportunities" @change="$emit('toggle-layer', { layer: 'opportunities', enabled: ($event.target as HTMLInputElement).checked })" />
          <span>Opportunities</span>
        </label>
        <label class="layer-toggle" :class="{ active: props.showHistoricalLevels }">
          <input type="checkbox" :checked="props.showHistoricalLevels" @change="$emit('toggle-layer', { layer: 'historical', enabled: ($event.target as HTMLInputElement).checked })" />
          <span>Historical</span>
        </label>
      </div>
    </div>
    
    <div v-if="loading" class="chart-loading">
      <div class="loading-spinner"></div>
      <div class="loading-text">Loading chart data...</div>
    </div>
    <div v-else-if="error" class="chart-error">
      <div class="error-icon">⚠️</div>
      <div class="error-message">{{ error }}</div>
      <button @click="fetchPriceData" class="retry-button">Retry</button>
    </div>
    <canvas 
      v-else
      ref="chartCanvas"
      class="price-chart"
      :width="width"
      :height="canvasHeight"
      @wheel="handleWheel"
      @mousedown="handleMouseDown"
      @mousemove="handleMouseMove"
      @mouseup="handleMouseUp"
      @mouseleave="handleMouseLeave"
      @dblclick="resetZoom"
    ></canvas>
    
    <!-- Crosshair Tooltip -->
    <div 
      v-if="crosshairTooltip.visible" 
      class="crosshair-tooltip"
      :style="{ left: crosshairTooltip.x + 'px', top: crosshairTooltip.y + 'px' }"
    >
      <div class="tooltip-content">
        <div class="tooltip-row">
          <span class="tooltip-label">Price:</span>
          <span class="tooltip-value">${{ formatPrice(crosshairTooltip.price) }}</span>
        </div>
        <div class="tooltip-row">
          <span class="tooltip-label">Time:</span>
          <span class="tooltip-value">{{ crosshairTooltip.time }}</span>
        </div>
      </div>
    </div>
    
    <!-- Position Tooltip -->
    <div 
      v-if="positionTooltip.visible && positionTooltip.position" 
      class="position-tooltip"
      :style="{ left: Math.min(positionTooltip.x, window.innerWidth - 270) + 'px', top: Math.max(10, positionTooltip.y) + 'px' }"
    >
      <div class="tooltip-content">
        <div class="tooltip-header">Position Details</div>
        <div class="tooltip-row">
          <span class="tooltip-label">Symbol:</span>
          <span class="tooltip-value">{{ positionTooltip.position.symbol }}</span>
        </div>
        <div class="tooltip-row">
          <span class="tooltip-label">Side:</span>
          <span class="tooltip-value" :class="positionTooltip.position.side.toLowerCase() === 'buy' ? 'positive' : 'negative'">
            {{ positionTooltip.position.side.toUpperCase() }}
          </span>
        </div>
        <div class="tooltip-row">
          <span class="tooltip-label">Entry Price:</span>
          <span class="tooltip-value">${{ formatPrice(positionTooltip.position.entry_price) }}</span>
        </div>
        <div class="tooltip-row">
          <span class="tooltip-label">Current Price:</span>
          <span class="tooltip-value">${{ formatPrice(positionTooltip.position.current_price) }}</span>
        </div>
        <div class="tooltip-row">
          <span class="tooltip-label">Quantity:</span>
          <span class="tooltip-value">{{ formatNumber(positionTooltip.position.quantity, 4) }}</span>
        </div>
        <div class="tooltip-row">
          <span class="tooltip-label">Unrealized P&L:</span>
          <span class="tooltip-value" :class="positionTooltip.position.unrealized_pnl >= 0 ? 'positive' : 'negative'">
            {{ positionTooltip.position.unrealized_pnl >= 0 ? '+' : '' }}${{ formatPrice(positionTooltip.position.unrealized_pnl) }}
          </span>
        </div>
        <div class="tooltip-row">
          <span class="tooltip-label">Hold Time:</span>
          <span class="tooltip-value">{{ formatDuration(positionTooltip.position.hold_time_seconds) }}</span>
        </div>
      </div>
    </div>
    
    <!-- Trade Tooltip -->
    <div 
      v-if="tradeTooltip.visible && tradeTooltip.trade" 
      class="trade-tooltip"
      :style="{ left: Math.min(tradeTooltip.x, window.innerWidth - 270) + 'px', top: Math.max(10, tradeTooltip.y) + 'px' }"
    >
      <div class="tooltip-content">
        <div class="tooltip-header">Trade Details</div>
        <div class="tooltip-row">
          <span class="tooltip-label">Symbol:</span>
          <span class="tooltip-value">{{ tradeTooltip.trade.symbol || 'N/A' }}</span>
        </div>
        <div class="tooltip-row">
          <span class="tooltip-label">Side:</span>
          <span class="tooltip-value" :class="(tradeTooltip.trade.side?.toLowerCase() || '') === 'buy' ? 'positive' : 'negative'">
            {{ (tradeTooltip.trade.side || 'LONG').toUpperCase() }}
          </span>
        </div>
        <div class="tooltip-row">
          <span class="tooltip-label">Entry Price:</span>
          <span class="tooltip-value">${{ formatPrice(tradeTooltip.trade.entry_price || 0) }}</span>
        </div>
        <div class="tooltip-row">
          <span class="tooltip-label">Exit Price:</span>
          <span class="tooltip-value">${{ formatPrice(tradeTooltip.trade.exit_price || 0) }}</span>
        </div>
        <div class="tooltip-row">
          <span class="tooltip-label">Quantity:</span>
          <span class="tooltip-value">{{ formatNumber(tradeTooltip.trade.quantity || 0, 4) }}</span>
        </div>
        <div class="tooltip-row">
          <span class="tooltip-label">P&L:</span>
          <span class="tooltip-value" :class="(tradeTooltip.trade.pnl || 0) >= 0 ? 'positive' : 'negative'">
            {{ (tradeTooltip.trade.pnl || 0) >= 0 ? '+' : '' }}${{ formatPrice(tradeTooltip.trade.pnl || 0) }}
          </span>
        </div>
        <div class="tooltip-row">
          <span class="tooltip-label">Hold Time:</span>
          <span class="tooltip-value">{{ formatDuration(tradeTooltip.trade.hold_time_seconds || 0) }}</span>
        </div>
      </div>
    </div>
    
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { setupWebSocketListener } from '../shared/websocket.js'

interface PriceLevel {
  price: number
  label: string
  color: string
  style?: 'solid' | 'dashed'
}

interface OHLCData {
  time: number
  open: number
  high: number
  low: number
  close: number
  volume?: number
}

interface IndicatorData {
  MA: { [period: number]: number[] }
  EMA: { [period: number]: number[] }
  RSI: number[]
  MACD?: {
    macd: number[]
    signal: number[]
    histogram: number[]
  }
  Bollinger?: {
    upper: number[]
    middle: number[]
    lower: number[]
    width?: number[] // Bollinger Band width for squeeze/expansion
  }
  Stochastic?: {
    k: number[]
    d: number[]
  }
  VWAP?: number[]
  ATR?: number[]
}

type ViewMode = 'line' | 'candlestick'
type Timeframe = '1m' | '5m' | '15m' | '1h'

interface Position {
  symbol: string
  side: string
  entry_price: number
  current_price: number
  quantity: number
  unrealized_pnl: number
  entry_time: string | Date
  hold_time_seconds: number
}

interface Trade {
  symbol: string
  side: string
  entry_price: number
  exit_price: number
  quantity: number
  pnl: number
  hold_time_seconds: number
  timestamp: string | Date
}

interface Opportunity {
  id: string
  symbol: string
  opportunity_type: string
  target_price?: number
  stop_loss?: number
  entry_price_min?: number
  entry_price_max?: number
  confidence?: number
  potential_profit_percent?: number
  time_horizon_minutes?: number
  entry_window_start?: string
  entry_window_end?: string
}

interface MarketData {
  symbol: string
  price: number
  high_24h?: number
  low_24h?: number
  volume?: number
  change_24h?: number
  signal?: number
}

interface NeuralTrajectory {
  ts: number
  price: number
  weighted_signal: number
  pillars: {
    rat: number
    momentum: number
    brain: number
    rhyme: number
    soul: number
  }
}

interface Props {
  symbol: string
  currentPrice?: number
  entryPriceMin?: number
  entryPriceMax?: number
  targetPrice?: number
  stopLoss?: number
  height?: number
  viewMode?: ViewMode
  timeframe?: Timeframe
  showVolume?: boolean
  showIndicators?: boolean
  indicators?: string[]
  zoomEnabled?: boolean
  realtime?: boolean
  positions?: Position[]
  tradeHistory?: Trade[]
  opportunities?: Opportunity[]
  useBackendWebSocket?: boolean
  marketData?: MarketData
  showPositions?: boolean
  showTrades?: boolean
  showShadowTrades?: boolean
  showOpportunities?: boolean
  showHistoricalLevels?: boolean
  showNeuralOverlay?: boolean
  shadowTrades?: Trade[]
  trajectories?: NeuralTrajectory[]
}

const props = withDefaults(defineProps<Props>(), {
  height: 300,
  viewMode: 'line',
  timeframe: '1m',
  showVolume: false,
  showIndicators: false,
  indicators: () => [],
  zoomEnabled: false,
  realtime: false,
  positions: () => [],
  tradeHistory: () => [],
  opportunities: () => [],
  useBackendWebSocket: false,
  showPositions: true,
  showTrades: true,
  showOpportunities: true,
  showHistoricalLevels: true,
  showNeuralOverlay: true,
  trajectories: () => []
})

const chartCanvas = ref<HTMLCanvasElement | null>(null)
const containerRef = ref<HTMLDivElement | null>(null)
const loading = ref(true)
const error = ref<string | null>(null)
const width = ref(600)
const priceData = ref<OHLCData[]>([])

// Performance optimization: Animation frame for smooth rendering
let animationFrameId: number | null = null
let pendingRedraw = false

// Crosshair tooltip state
const crosshairTooltip = ref<{ x: number, y: number, price: number, time: string, visible: boolean }>({
  x: 0,
  y: 0,
  price: 0,
  time: '',
  visible: false
})

const indicatorsData = ref<IndicatorData>({ MA: {}, RSI: [] })

// Position/Trade tooltip state
const positionTooltip = ref<{ visible: boolean, x: number, y: number, position: Position | null }>({
  visible: false,
  x: 0,
  y: 0,
  position: null
})

const tradeTooltip = ref<{ visible: boolean, x: number, y: number, trade: Trade | null }>({
  visible: false,
  x: 0,
  y: 0,
  trade: null
})

// Local state for controls
const localViewMode = ref<ViewMode>(props.viewMode)
const localTimeframe = ref<Timeframe>(props.timeframe)
const localShowVolume = ref(props.showVolume)
const localShowIndicators = ref(props.showIndicators)
const selectedIndicators = ref<string[]>(props.indicators || [])

// Zoom/Pan state
const zoomLevel = ref(1)
const panOffset = ref({ x: 0, y: 0 })
const visiblePriceRange = ref<{ min: number, max: number } | null>(null)
const visibleTimeRange = ref<{ start: number, end: number } | null>(null)
const isDragging = ref(false)
const dragStart = ref({ x: 0, y: 0 })

// Real-time updates
const realtimeInterval = ref<ReturnType<typeof setInterval> | null>(null)
const dataCache = ref<Map<string, { data: OHLCData[], timestamp: number }>>(new Map())

// Calculate canvas height (accounting for volume and RSI if shown)
const canvasHeight = computed(() => {
  // Calculate height needed for indicators
  let indicatorHeight = 0
  if (localShowIndicators.value) {
    if (selectedIndicators.value.includes('RSI')) indicatorHeight += 90
    if (selectedIndicators.value.includes('MACD')) indicatorHeight += 90
    if (selectedIndicators.value.includes('Stochastic')) indicatorHeight += 90
  }
  
  return props.height + (localShowVolume.value ? 60 : 0) + indicatorHeight
})

// Fetch recent price history from Binance
async function fetchPriceData() {
  if (!props.symbol) return
  
  // Check cache first
  const cacheKey = `${props.symbol}_${localTimeframe.value}`
  const cached = dataCache.value.get(cacheKey)
  const now = Date.now()
  
  if (cached && (now - cached.timestamp) < 60000) { // Cache valid for 1 minute
    priceData.value = cached.data
    loading.value = false
    calculateIndicators()
    return
  }
  
  loading.value = true
  error.value = null
  
  try {
    const binanceSymbol = props.symbol.toUpperCase().replace('/', '')
    const limit = localTimeframe.value === '1h' ? 500 : 200
    const url = `https://api.binance.com/api/v3/klines?symbol=${binanceSymbol}&interval=${localTimeframe.value}&limit=${limit}`
    const response = await fetch(url)
    
    if (!response.ok) {
      throw new Error(`Failed to fetch data: ${response.status}`)
    }
    
    const klines = await response.json()
    
    // Convert to OHLC data
    const ohlcData: OHLCData[] = klines.map((k: any[]) => ({
      time: Math.floor(k[0] / 1000), // Convert ms to seconds
      open: parseFloat(k[1]),
      high: parseFloat(k[2]),
      low: parseFloat(k[3]),
      close: parseFloat(k[4]),
      volume: parseFloat(k[5])
    }))
    
    // Limit to 1000 candles for performance
    priceData.value = ohlcData.slice(-1000)
    
    // Cache the data
    dataCache.value.set(cacheKey, { data: priceData.value, timestamp: now })
    
    loading.value = false
    calculateIndicators()
  } catch (err: any) {
    const errorMessage = err?.message || err?.toString() || 'Failed to load chart data'
    error.value = `Unable to load chart data. ${errorMessage.includes('Failed to fetch') ? 'Please check your internet connection.' : 'Please try again.'}`
    loading.value = false
      // Error handled below
    
    // Retry after 5 seconds
    setTimeout(() => {
      if (props.symbol && error.value) {
        // Retrying data fetch after error
        fetchPriceData()
      }
    }, 5000)
  }
}

// Fetch latest candle for real-time updates
async function fetchLatestCandle() {
  if (!props.symbol || !props.realtime) return
  
  try {
    const binanceSymbol = props.symbol.toUpperCase()
    const url = `https://api.binance.com/api/v3/klines?symbol=${binanceSymbol}&interval=${localTimeframe.value}&limit=1`
    const response = await fetch(url)
    
    if (!response.ok) return
    
    const klines = await response.json()
    if (klines.length === 0) return
    
    const latest: OHLCData = {
      time: Math.floor(klines[0][0] / 1000),
      open: parseFloat(klines[0][1]),
      high: parseFloat(klines[0][2]),
      low: parseFloat(klines[0][3]),
      close: parseFloat(klines[0][4]),
      volume: parseFloat(klines[0][5])
    }
    
    // Update or append latest candle
    if (priceData.value.length > 0) {
      const lastCandle = priceData.value[priceData.value.length - 1]
      if (latest.time === lastCandle.time) {
        // Update existing candle
        priceData.value[priceData.value.length - 1] = latest
      } else if (latest.time > lastCandle.time) {
        // Append new candle
        priceData.value.push(latest)
        // Keep only last 1000 candles
        if (priceData.value.length > 1000) {
          priceData.value = priceData.value.slice(-1000)
        }
      }
    }
    
    calculateIndicators()
    scheduleRedraw()
  } catch (err) {
    // Silently fail for real-time updates to avoid spamming console
    // Only log if it's a persistent issue
    if (error.value === null) {
      // Silently handle latest candle fetch error, will retry on next update
    }
  }
}

// WebSocket listener for backend updates
let wsUnsubscribe: (() => void) | null = null

// Helper to parse timestamp (string, Date, or number) to seconds
function parseTimestampToSeconds(ts: string | Date | number | any): number {
  if (ts === null || ts === undefined) return 0
  if (typeof ts === 'number') {
    return ts > 100000000000 ? Math.floor(ts / 1000) : ts
  }
  if (ts instanceof Date) {
    return Math.floor(ts.getTime() / 1000)
  }
  if (typeof ts === 'string') {
    const parsed = new Date(ts).getTime()
    return isNaN(parsed) ? 0 : Math.floor(parsed / 1000)
  }
  // Fallback for cases where it has a getTime function but isn't instanceof Date (e.g. from some libraries)
  if (ts && typeof ts.getTime === 'function') {
    return Math.floor(ts.getTime() / 1000)
  }
  return 0
}

// Helper to get candle time for a given timestamp
function getCandleTime(timestamp: number, timeframe: Timeframe): number {
  const date = new Date(timestamp * 1000)
  const minutes = date.getMinutes()
  
  switch (timeframe) {
    case '1m':
      date.setSeconds(0, 0)
      break
    case '5m':
      date.setMinutes(Math.floor(minutes / 5) * 5, 0, 0)
      break
    case '15m':
      date.setMinutes(Math.floor(minutes / 15) * 15, 0, 0)
      break
    case '1h':
      date.setMinutes(0, 0, 0)
      break
  }
  
  return Math.floor(date.getTime() / 1000)
}

// Start real-time updates
function startRealtimeUpdates() {
  if (!props.realtime) return
  
  // Use backend WebSocket if enabled
  if (props.useBackendWebSocket) {
    // Listen for ticker_update messages from backend
    wsUnsubscribe = setupWebSocketListener('ticker_update', (data: any) => {
      if (!data || !data.data || !Array.isArray(data.data)) return
      
      // Find ticker data for current symbol
      const ticker = data.data.find((t: any) => t.symbol === props.symbol)
      if (!ticker || !ticker.price) return
      
      // Update latest candle with new price
      if (priceData.value.length > 0) {
        const lastCandle = priceData.value[priceData.value.length - 1]
        const now = Math.floor(Date.now() / 1000)
        const candleTime = getCandleTime(now, localTimeframe.value)
        
        // If same candle, update close price
        if (lastCandle.time === candleTime) {
          lastCandle.close = ticker.price
          lastCandle.high = Math.max(lastCandle.high, ticker.price)
          lastCandle.low = Math.min(lastCandle.low, ticker.price)
          if (ticker.volume) {
            lastCandle.volume = (lastCandle.volume || 0) + ticker.volume
          }
        } else {
          // New candle - add it
          priceData.value.push({
            time: candleTime,
            open: lastCandle.close,
            high: ticker.price,
            low: ticker.price,
            close: ticker.price,
            volume: ticker.volume || 0
          })
          
          // Keep only last 500 candles
          if (priceData.value.length > 500) {
            priceData.value.shift()
          }
        }
        
        // Recalculate indicators
        calculateIndicators()
        
        // Trigger redraw
        scheduleRedraw()
      }
    })
  } else {
    // Use Binance polling
    if (realtimeInterval.value) return
    
    realtimeInterval.value = setInterval(() => {
      fetchLatestCandle()
    }, 2000) // Update every 2 seconds
  }
}

// Stop real-time updates
function stopRealtimeUpdates() {
  if (realtimeInterval.value) {
    clearInterval(realtimeInterval.value)
    realtimeInterval.value = null
  }
  
  if (wsUnsubscribe) {
    wsUnsubscribe()
    wsUnsubscribe = null
  }
}

// Draw candlesticks
function drawCandlesticks(ctx: CanvasRenderingContext2D, priceToY: (p: number) => number, timeToX: (t: number) => number, candleWidth: number) {
  priceData.value.forEach((candle) => {
    const x = timeToX(candle.time) - candleWidth / 2
    const openY = priceToY(candle.open)
    const closeY = priceToY(candle.close)
    const highY = priceToY(candle.high)
    const lowY = priceToY(candle.low)
    
    const isBullish = candle.close >= candle.open
    const color = isBullish ? 'rgba(74, 222, 128, 1)' : 'rgba(248, 113, 113, 1)'
    
    // Draw wick
    ctx.strokeStyle = color
    ctx.lineWidth = 1
    ctx.beginPath()
    ctx.moveTo(x + candleWidth / 2, highY)
    ctx.lineTo(x + candleWidth / 2, lowY)
    ctx.stroke()
    
    // Draw body
    const bodyTop = Math.min(openY, closeY)
    const bodyHeight = Math.abs(closeY - openY) || 1
    
    ctx.fillStyle = color
    ctx.fillRect(x, bodyTop, candleWidth, bodyHeight)
    
    // Draw outline
    ctx.strokeStyle = color
    ctx.strokeRect(x, bodyTop, candleWidth, bodyHeight)
  })
}

// Draw volume bars
function drawVolume(ctx: CanvasRenderingContext2D, timeToX: (t: number) => number, candleWidth: number, volumeHeight: number, volumeY: number) {
  if (!localShowVolume.value || priceData.value.length === 0) return
  
  const volumes = priceData.value.map(d => d.volume || 0)
  const maxVolume = Math.max(...volumes)
  
  priceData.value.forEach((candle) => {
    const x = timeToX(candle.time) - candleWidth / 2
    const volume = candle.volume || 0
    const barHeight = (volume / maxVolume) * volumeHeight
    const isBullish = candle.close >= candle.open
    const color = isBullish ? 'rgba(74, 222, 128, 0.5)' : 'rgba(248, 113, 113, 0.5)'
    
    ctx.fillStyle = color
    ctx.fillRect(x, volumeY - barHeight, candleWidth, barHeight)
  })
}

// Draw position markers with enhanced visualization
function drawPositionMarkers(ctx: CanvasRenderingContext2D, priceToY: (p: number) => number, timeToX: (t: number) => number, chartWidth: number) {
  if (!props.showPositions || !props.positions || props.positions.length === 0) return
  
  props.positions.forEach((position) => {
    // Convert entry_time to timestamp
    let entryTime = 0
    try {
      entryTime = parseTimestampToSeconds(position.entry_time)
      if (entryTime === 0) return
    } catch {
      return // Skip if time is invalid
    }
    
    const entryX = timeToX(entryTime)
    const entryY = priceToY(position.entry_price)
    const currentY = priceToY(position.current_price)
    const currentX = timeToX(Math.floor(Date.now() / 1000))
    
    const isBuy = position.side.toLowerCase() === 'buy'
    const entryColor = isBuy ? 'rgba(74, 222, 128, 0.8)' : 'rgba(248, 113, 113, 0.8)'
    const currentColor = isBuy ? 'rgba(74, 222, 128, 1)' : 'rgba(248, 113, 113, 1)'
    const pnlColor = position.unrealized_pnl >= 0 ? 'rgba(74, 222, 128, 1)' : 'rgba(248, 113, 113, 1)'
    
    // Draw entry price line (horizontal dashed line across chart)
    ctx.strokeStyle = entryColor
    ctx.lineWidth = 1.5
    ctx.setLineDash([8, 4])
    ctx.beginPath()
    ctx.moveTo(60, entryY)
    ctx.lineTo(60 + chartWidth, entryY)
    ctx.stroke()
    ctx.setLineDash([])
    
    // Draw entry point marker
    ctx.fillStyle = entryColor
    ctx.strokeStyle = entryColor
    ctx.lineWidth = 2
    ctx.beginPath()
    ctx.arc(entryX, entryY, 6, 0, Math.PI * 2)
    ctx.fill()
    ctx.stroke()
    
    // Draw entry price label
    ctx.fillStyle = entryColor
    ctx.font = '11px sans-serif'
    ctx.textAlign = 'left'
    ctx.fillText(`Entry: $${position.entry_price.toFixed(2)}`, 60 + chartWidth + 8, entryY - 4)
    
    // Draw current price line (horizontal solid line across chart)
    ctx.strokeStyle = currentColor
    ctx.lineWidth = 2
    ctx.beginPath()
    ctx.moveTo(60, currentY)
    ctx.lineTo(60 + chartWidth, currentY)
    ctx.stroke()
    
    // Draw current price marker
    ctx.fillStyle = currentColor
    ctx.strokeStyle = currentColor
    ctx.lineWidth = 2
    ctx.beginPath()
    ctx.arc(currentX, currentY, 5, 0, Math.PI * 2)
    ctx.fill()
    ctx.stroke()
    
    // Draw connecting line from entry to current
    ctx.strokeStyle = entryColor
    ctx.lineWidth = 1.5
    ctx.setLineDash([3, 3])
    ctx.beginPath()
    ctx.moveTo(entryX, entryY)
    ctx.lineTo(currentX, currentY)
    ctx.stroke()
    ctx.setLineDash([])
    
    // Draw enhanced PnL annotation with background
    const pnlText = `${position.unrealized_pnl >= 0 ? '+' : ''}$${position.unrealized_pnl.toFixed(2)}`
    const pnlPercent = position.entry_price > 0 
      ? ((position.current_price - position.entry_price) / position.entry_price * 100)
      : 0
    const pnlPercentText = `${pnlPercent >= 0 ? '+' : ''}${pnlPercent.toFixed(2)}%`
    
    ctx.font = 'bold 12px sans-serif'
    ctx.textAlign = 'left'
    const textMetrics = ctx.measureText(`${pnlText} (${pnlPercentText})`)
    const textWidth = textMetrics.width
    const textX = currentX + 10
    const textY = currentY - 8
    
    // Draw background for PnL text
    ctx.fillStyle = 'rgba(0, 0, 0, 0.7)'
    ctx.fillRect(textX - 4, textY - 12, textWidth + 8, 18)
    
    // Draw PnL text
    ctx.fillStyle = pnlColor
    ctx.fillText(pnlText, textX, textY)
    ctx.font = '11px sans-serif'
    ctx.fillText(`(${pnlPercentText})`, textX, textY + 12)
  })
}

// Draw historical levels (24h high/low, support/resistance)
// If skipLabels is true, only draws lines (labels are handled in priceLevels section)
function drawHistoricalLevels(ctx: CanvasRenderingContext2D, priceToY: (p: number) => number, chartWidth: number, skipLabels: boolean = false) {
  // Need either marketData with high_24h/low_24h, or currentPrice to calculate support/resistance
  if (!props.currentPrice) return
  
  const currentPrice = props.currentPrice
  
  // Calculate 24h high/low from price data if not provided in marketData
  let high24h: number | null = null
  let low24h: number | null = null
  
  if (props.marketData && (props.marketData.high_24h !== undefined || props.marketData.low_24h !== undefined)) {
    high24h = props.marketData.high_24h || null
    low24h = props.marketData.low_24h || null
  }
  
  // If not provided, calculate from price data (last 24 hours worth of candles)
  if (!high24h || !low24h) {
    const now = Date.now() / 1000
    const oneDayAgo = now - (24 * 60 * 60)
    
    const recentData = priceData.value.filter(candle => candle.time >= oneDayAgo)
    if (recentData.length > 0) {
      const highs = recentData.map(c => c.high)
      const lows = recentData.map(c => c.low)
      high24h = high24h || Math.max(...highs)
      low24h = low24h || Math.min(...lows)
    } else {
      // Fallback to current price ± 5% if no data
      high24h = high24h || currentPrice * 1.05
      low24h = low24h || currentPrice * 0.95
    }
  }
  
  // Ensure we have valid values (fallback if still null)
  if (!high24h) high24h = currentPrice * 1.05
  if (!low24h) low24h = currentPrice * 0.95
  
  // Draw 24h high
  if (high24h > currentPrice) {
    const highY = priceToY(high24h)
    ctx.strokeStyle = 'rgba(74, 222, 128, 0.5)'
    ctx.lineWidth = 1
    ctx.setLineDash([5, 5])
    ctx.beginPath()
    ctx.moveTo(60, highY)
    ctx.lineTo(60 + chartWidth, highY)
    ctx.stroke()
    ctx.setLineDash([])
    
    if (!skipLabels) {
      ctx.fillStyle = 'rgba(74, 222, 128, 0.8)'
      ctx.font = '10px sans-serif'
      ctx.textAlign = 'left'
      ctx.fillText(`24h High: $${high24h.toFixed(2)}`, 60 + chartWidth + 8, highY + 4)
    }
  }
  
  // Draw 24h low
  if (low24h < currentPrice) {
    const lowY = priceToY(low24h)
    ctx.strokeStyle = 'rgba(248, 113, 113, 0.5)'
    ctx.lineWidth = 1
    ctx.setLineDash([5, 5])
    ctx.beginPath()
    ctx.moveTo(60, lowY)
    ctx.lineTo(60 + chartWidth, lowY)
    ctx.stroke()
    ctx.setLineDash([])
    
    ctx.fillStyle = 'rgba(248, 113, 113, 0.8)'
    ctx.font = '10px sans-serif'
    ctx.textAlign = 'left'
    if (!skipLabels) {
      ctx.fillText(`24h Low: $${low24h.toFixed(2)}`, 60 + chartWidth + 8, lowY + 4)
    }
  }
  
  // Draw support level (5% below current)
  const supportLevel = currentPrice * 0.95
  const supportY = priceToY(supportLevel)
  ctx.strokeStyle = 'rgba(16, 185, 129, 0.6)'
  ctx.lineWidth = 1.5
  ctx.setLineDash([10, 5])
  ctx.beginPath()
  ctx.moveTo(60, supportY)
  ctx.lineTo(60 + chartWidth, supportY)
  ctx.stroke()
  ctx.setLineDash([])
  
  ctx.fillStyle = 'rgba(16, 185, 129, 0.9)'
  ctx.font = '10px sans-serif'
  ctx.textAlign = 'left'
  if (!skipLabels) {
    ctx.fillText(`Support: $${supportLevel.toFixed(2)}`, 60 + chartWidth + 8, supportY + 4)
  }
  
  // Draw resistance level (5% above current)
  const resistanceLevel = currentPrice * 1.05
  const resistanceY = priceToY(resistanceLevel)
  ctx.strokeStyle = 'rgba(16, 185, 129, 0.6)'
  ctx.lineWidth = 1.5
  ctx.setLineDash([10, 5])
  ctx.beginPath()
  ctx.moveTo(60, resistanceY)
  ctx.lineTo(60 + chartWidth, resistanceY)
  ctx.stroke()
  ctx.setLineDash([])
  
  ctx.fillStyle = 'rgba(16, 185, 129, 0.9)'
  ctx.font = '10px sans-serif'
  ctx.textAlign = 'left'
  if (!skipLabels) {
    ctx.fillText(`Resistance: $${resistanceLevel.toFixed(2)}`, 60 + chartWidth + 8, resistanceY + 4)
  }
}

// Draw trade history markers
function drawTradeHistory(ctx: CanvasRenderingContext2D, priceToY: (p: number) => number, timeToX: (t: number) => number) {
  if (!props.showTrades || !props.tradeHistory || props.tradeHistory.length === 0) return
  
  props.tradeHistory.forEach((trade) => {
    // Convert timestamps
    let entryTime = 0
    let exitTime = 0
    try {
      entryTime = parseTimestampToSeconds(trade.timestamp)
      if (entryTime === 0) return
      // For simplicity, assume exit is shortly after entry (you may need to adjust based on your data)
      exitTime = entryTime + (trade.hold_time_seconds || 0)
    } catch {
      return
    }
    
    const entryX = timeToX(entryTime)
    const exitX = timeToX(exitTime)
    const entryY = priceToY(trade.entry_price)
    const exitY = priceToY(trade.exit_price)
    
    const isProfit = trade.pnl >= 0
    const color = isProfit ? 'rgba(74, 222, 128, 0.8)' : 'rgba(248, 113, 113, 0.8)'
    
    // Draw connecting line
    ctx.strokeStyle = color
    ctx.lineWidth = 1.5
    ctx.beginPath()
    ctx.moveTo(entryX, entryY)
    ctx.lineTo(exitX, exitY)
    ctx.stroke()
    
    // Draw entry point
    ctx.fillStyle = color
    ctx.beginPath()
    ctx.arc(entryX, entryY, 4, 0, Math.PI * 2)
    ctx.fill()
    
    // Draw exit point
    ctx.fillStyle = color
    ctx.beginPath()
    ctx.arc(exitX, exitY, 4, 0, Math.PI * 2)
    ctx.fill()
    
    // Draw PnL annotation
    ctx.fillStyle = color
    ctx.font = '10px sans-serif'
    ctx.textAlign = 'center'
    const pnlText = `${trade.pnl >= 0 ? '+' : ''}$${trade.pnl.toFixed(2)}`
    ctx.fillText(pnlText, (entryX + exitX) / 2, Math.min(entryY, exitY) - 8)
  })
}

// Draw shadow trade markers (Ghost Trades)
function drawShadowTrades(ctx: CanvasRenderingContext2D, priceToY: (p: number) => number, timeToX: (t: number) => number) {
  if (!props.showShadowTrades || !props.shadowTrades || props.shadowTrades.length === 0) return
  
  props.shadowTrades.forEach((trade) => {
    let entryTime = 0
    let exitTime = 0
    try {
      entryTime = parseTimestampToSeconds(trade.timestamp)
      if (entryTime === 0) return
      exitTime = entryTime + (trade.hold_time_seconds || 120) // Default 2m for ghost
    } catch {
      return
    }
    
    const entryX = timeToX(entryTime)
    const exitX = timeToX(exitTime)
    const entryY = priceToY(trade.entry_price)
    const exitY = priceToY(trade.exit_price)
    
    const isProfit = trade.pnl >= 0
    // Use semi-transparent neon colors for "Ghost" effect
    const color = isProfit ? 'rgba(34, 197, 94, 0.4)' : 'rgba(239, 68, 68, 0.4)'
    const glowColor = isProfit ? 'rgba(34, 197, 94, 0.2)' : 'rgba(239, 68, 68, 0.2)'
    
    // Draw connecting line (dashed for ghost)
    ctx.setLineDash([5, 5])
    ctx.strokeStyle = color
    ctx.lineWidth = 1
    ctx.beginPath()
    ctx.moveTo(entryX, entryY)
    ctx.lineTo(exitX, exitY)
    ctx.stroke()
    ctx.setLineDash([]) // Reset
    
    // Draw entry point (hollow for ghost)
    ctx.strokeStyle = color
    ctx.lineWidth = 2
    ctx.beginPath()
    ctx.arc(entryX, entryY, 5, 0, Math.PI * 2)
    ctx.stroke()
    
    // Draw exit point (hollow for ghost)
    ctx.beginPath()
    ctx.arc(exitX, exitY, 5, 0, Math.PI * 2)
    ctx.stroke()
    
    // Simple label
    ctx.fillStyle = color
    ctx.font = 'italic 9px sans-serif'
    ctx.textAlign = 'center'
    ctx.fillText('GHOST', (entryX + exitX) / 2, Math.min(entryY, exitY) - 12)
  })
}

// Draw neural overlays (7 Pillars & Weighted Signal)
function drawNeuralOverlays(ctx: CanvasRenderingContext2D, timeToX: (t: number) => number, chartHeight: number) {
  if (!props.showNeuralOverlay || !props.trajectories || props.trajectories.length === 0) return
  
  // We render the signals in a separate pane at the bottom of the price chart
  // or as an overlay. Let's do a sub-pane for clarity.
  const overlayHeight = 80
  const overlayY = chartHeight - overlayHeight - (localShowVolume.value ? 60 : 0) - 20
  
  // Draw Background
  ctx.fillStyle = 'rgba(0, 0, 0, 0.3)'
  ctx.fillRect(60, overlayY, width.value - 60, overlayHeight)
  ctx.strokeStyle = 'rgba(255, 255, 255, 0.1)'
  ctx.strokeRect(60, overlayY, width.value - 60, overlayHeight)
  
  // Draw Zero Line
  const zeroY = overlayY + overlayHeight / 2
  ctx.strokeStyle = 'rgba(255, 255, 255, 0.2)'
  ctx.setLineDash([2, 2])
  ctx.beginPath()
  ctx.moveTo(60, zeroY)
  ctx.lineTo(width.value, zeroY)
  ctx.stroke()
  ctx.setLineDash([])
  
  // Helper to map signal (-1 to 1) to Y coordinate
  const signalToY = (sig: number) => zeroY - (sig * (overlayHeight / 2.2))
  
  // 1. Draw Individual Pillars (Subtle)
  const pillars = ['rat', 'momentum', 'brain', 'rhyme', 'soul']
  const pillarColors: Record<string, string> = {
    rat: 'rgba(236, 72, 153, 0.3)',      // Pink
    momentum: 'rgba(59, 130, 246, 0.3)', // Blue
    brain: 'rgba(168, 85, 247, 0.3)',    // Purple
    rhyme: 'rgba(234, 179, 8, 0.3)',     // Yellow
    soul: 'rgba(20, 184, 166, 0.3)'      // Teal
  }
  
  pillars.forEach(p => {
    ctx.strokeStyle = pillarColors[p]
    ctx.lineWidth = 1
    ctx.beginPath()
    let first = true
    
    props.trajectories!.forEach(point => {
      const x = timeToX(point.ts / 1000)
      const y = signalToY((point.pillars as any)[p] || 0)
      
      if (first) {
        ctx.moveTo(x, y)
        first = false
      } else {
        ctx.lineTo(x, y)
      }
    })
    ctx.stroke()
  })
  
  // 2. Draw Weighted Signal (Bold)
  ctx.strokeStyle = 'rgba(255, 255, 255, 0.9)'
  ctx.lineWidth = 2
  ctx.shadowBlur = 10
  ctx.shadowColor = 'rgba(255, 255, 255, 0.5)'
  ctx.beginPath()
  let first = true
  
  props.trajectories!.forEach(point => {
    const x = timeToX(point.ts / 1000)
    const y = signalToY(point.weighted_signal)
    
    if (first) {
      ctx.moveTo(x, y)
      first = false
    } else {
      ctx.lineTo(x, y)
    }
  })
  ctx.stroke()
  ctx.shadowBlur = 0 // Reset shadow
  
  // Label
  ctx.fillStyle = 'rgba(255, 255, 255, 0.7)'
  ctx.font = '10px sans-serif'
  ctx.textAlign = 'left'
  ctx.fillText('NEURAL MANIFOLD (7 PILLARS)', 70, overlayY + 15)
}

// Draw opportunity markers
function drawOpportunityMarkers(ctx: CanvasRenderingContext2D, priceToY: (p: number) => number, chartWidth: number) {
  if (!props.showOpportunities || !props.opportunities || props.opportunities.length === 0) return
  
  props.opportunities.forEach((opp) => {
    // Draw entry window if available
    if (opp.entry_price_min && opp.entry_price_max) {
      const minY = priceToY(opp.entry_price_min)
      const maxY = priceToY(opp.entry_price_max)
      
      // Shaded entry window
      ctx.fillStyle = 'rgba(74, 222, 128, 0.1)'
      ctx.fillRect(60, Math.min(minY, maxY), chartWidth, Math.abs(maxY - minY))
      
      // Entry window borders
      ctx.strokeStyle = 'rgba(74, 222, 128, 0.4)'
      ctx.lineWidth = 1
      ctx.setLineDash([5, 5])
      ctx.beginPath()
      ctx.moveTo(60, minY)
      ctx.lineTo(60 + chartWidth, minY)
      ctx.moveTo(60, maxY)
      ctx.lineTo(60 + chartWidth, maxY)
      ctx.stroke()
      ctx.setLineDash([])
    }
    
    // Draw target price
    if (opp.target_price) {
      const targetY = priceToY(opp.target_price)
      ctx.strokeStyle = 'rgba(74, 222, 128, 0.6)'
      ctx.lineWidth = 1.5
      ctx.setLineDash([8, 4])
      ctx.beginPath()
      ctx.moveTo(60, targetY)
      ctx.lineTo(60 + chartWidth, targetY)
      ctx.stroke()
      ctx.setLineDash([])
      
      // Label
      ctx.fillStyle = 'rgba(74, 222, 128, 0.8)'
      ctx.font = '10px sans-serif'
      ctx.textAlign = 'left'
      ctx.fillText(`Target: $${formatPrice(opp.target_price)}`, 60 + chartWidth + 8, targetY + 4)
    }
    
    // Draw stop loss
    if (opp.stop_loss) {
      const stopY = priceToY(opp.stop_loss)
      ctx.strokeStyle = 'rgba(248, 113, 113, 0.6)'
      ctx.lineWidth = 1.5
      ctx.setLineDash([8, 4])
      ctx.beginPath()
      ctx.moveTo(60, stopY)
      ctx.lineTo(60 + chartWidth, stopY)
      ctx.stroke()
      ctx.setLineDash([])
      
      // Label
      ctx.fillStyle = 'rgba(248, 113, 113, 0.8)'
      ctx.font = '10px sans-serif'
      ctx.textAlign = 'left'
      ctx.fillText(`Stop: $${formatPrice(opp.stop_loss)}`, 60 + chartWidth + 8, stopY + 4)
    }
  })
}

// Draw indicators
function drawIndicators(ctx: CanvasRenderingContext2D, priceToY: (p: number) => number, timeToX: (t: number) => number, volumeHeight: number, volumeY: number) {
  if (!localShowIndicators.value) return
  
  // Draw Moving Averages (SMA)
  if (selectedIndicators.value.includes('MA')) {
    const maColors: { [key: number]: string } = {
      10: 'rgba(255, 152, 0, 0.8)',
      20: 'rgba(255, 193, 7, 0.8)',
      50: 'rgba(33, 150, 243, 0.8)',
      100: 'rgba(76, 175, 80, 0.8)',
      200: 'rgba(156, 39, 176, 0.8)'
    }
    
    Object.entries(indicatorsData.value.MA).forEach(([period, values]) => {
      const color = maColors[parseInt(period)] || 'rgba(136, 136, 136, 0.8)'
      ctx.strokeStyle = color
      ctx.lineWidth = 1.5
      ctx.beginPath()
      
      let firstPoint = true
      values.forEach((ma, index) => {
        if (!isNaN(ma) && index < priceData.value.length) {
          const x = timeToX(priceData.value[index].time)
          const y = priceToY(ma)
          
          if (firstPoint) {
            ctx.moveTo(x, y)
            firstPoint = false
          } else {
            ctx.lineTo(x, y)
          }
        }
      })
      ctx.stroke()
      
      // Label
      if (values.length > 0 && !isNaN(values[values.length - 1])) {
        const lastIndex = values.length - 1
        const x = timeToX(priceData.value[lastIndex].time)
        const y = priceToY(values[lastIndex])
        ctx.fillStyle = color
        ctx.font = '10px sans-serif'
        ctx.textAlign = 'left'
        ctx.fillText(`MA${period}`, x + 4, y - 4)
      }
    })
  }
  
  // Draw Exponential Moving Averages (EMA)
  if (selectedIndicators.value.includes('EMA')) {
    const emaColors: { [key: number]: string } = {
      10: 'rgba(255, 87, 34, 0.8)',
      20: 'rgba(255, 152, 0, 0.8)',
      50: 'rgba(3, 169, 244, 0.8)',
      200: 'rgba(103, 58, 183, 0.8)'
    }
    
    Object.entries(indicatorsData.value.EMA).forEach(([period, values]) => {
      const color = emaColors[parseInt(period)] || 'rgba(136, 136, 136, 0.8)'
      ctx.strokeStyle = color
      ctx.lineWidth = 1.5
      ctx.setLineDash([3, 3]) // Dashed line to distinguish from SMA
      ctx.beginPath()
      
      let firstPoint = true
      values.forEach((ema, index) => {
        if (!isNaN(ema) && index < priceData.value.length) {
          const x = timeToX(priceData.value[index].time)
          const y = priceToY(ema)
          
          if (firstPoint) {
            ctx.moveTo(x, y)
            firstPoint = false
          } else {
            ctx.lineTo(x, y)
          }
        }
      })
      ctx.stroke()
      ctx.setLineDash([]) // Reset dash
      
      // Label
      if (values.length > 0 && !isNaN(values[values.length - 1])) {
        const lastIndex = values.length - 1
        const x = timeToX(priceData.value[lastIndex].time)
        const y = priceToY(values[lastIndex])
        ctx.fillStyle = color
        ctx.font = '10px sans-serif'
        ctx.textAlign = 'left'
        ctx.fillText(`EMA${period}`, x + 4, y - 4)
      }
    })
  }
  
  // Draw VWAP
  if (selectedIndicators.value.includes('VWAP') && indicatorsData.value.VWAP) {
    ctx.strokeStyle = 'rgba(255, 152, 0, 0.9)'
    ctx.lineWidth = 2
    ctx.setLineDash([5, 5])
    ctx.beginPath()
    
    let firstPoint = true
    indicatorsData.value.VWAP.forEach((vwap, index) => {
      if (!isNaN(vwap) && index < priceData.value.length) {
        const x = timeToX(priceData.value[index].time)
        const y = priceToY(vwap)
        
        if (firstPoint) {
          ctx.moveTo(x, y)
          firstPoint = false
        } else {
          ctx.lineTo(x, y)
        }
      }
    })
    ctx.stroke()
    ctx.setLineDash([])
    
    // Label
    if (indicatorsData.value.VWAP.length > 0) {
      const lastIndex = indicatorsData.value.VWAP.length - 1
      const lastVWAP = indicatorsData.value.VWAP[lastIndex]
      if (!isNaN(lastVWAP)) {
        const x = timeToX(priceData.value[lastIndex].time)
        const y = priceToY(lastVWAP)
        ctx.fillStyle = 'rgba(255, 152, 0, 0.9)'
        ctx.font = '10px sans-serif'
        ctx.textAlign = 'left'
        ctx.fillText('VWAP', x + 4, y - 4)
      }
    }
  }
  
  // Draw Bollinger Bands
  if (selectedIndicators.value.includes('Bollinger') && indicatorsData.value.Bollinger) {
    const bb = indicatorsData.value.Bollinger
    const bbColor = 'rgba(96, 165, 250, 0.3)'
    
    // Draw upper band
    ctx.strokeStyle = bbColor
    ctx.lineWidth = 1
    ctx.setLineDash([5, 5])
    ctx.beginPath()
    for (let i = 0; i < bb.upper.length && i < priceData.value.length; i++) {
      if (!isNaN(bb.upper[i])) {
        const x = timeToX(priceData.value[i].time)
        const y = priceToY(bb.upper[i])
        if (i === 0) ctx.moveTo(x, y)
        else ctx.lineTo(x, y)
      }
    }
    ctx.stroke()
    
    // Draw lower band
    ctx.beginPath()
    for (let i = 0; i < bb.lower.length && i < priceData.value.length; i++) {
      if (!isNaN(bb.lower[i])) {
        const x = timeToX(priceData.value[i].time)
        const y = priceToY(bb.lower[i])
        if (i === 0) ctx.moveTo(x, y)
        else ctx.lineTo(x, y)
      }
    }
    ctx.stroke()
    
    // Draw middle band (SMA)
    ctx.strokeStyle = 'rgba(96, 165, 250, 0.5)'
    ctx.setLineDash([3, 3])
    ctx.beginPath()
    for (let i = 0; i < bb.middle.length && i < priceData.value.length; i++) {
      if (!isNaN(bb.middle[i])) {
        const x = timeToX(priceData.value[i].time)
        const y = priceToY(bb.middle[i])
        if (i === 0) ctx.moveTo(x, y)
        else ctx.lineTo(x, y)
      }
    }
    ctx.stroke()
    ctx.setLineDash([])
    
    // Fill between bands
    ctx.fillStyle = 'rgba(96, 165, 250, 0.05)'
    ctx.beginPath()
    for (let i = 0; i < bb.upper.length && i < priceData.value.length; i++) {
      if (!isNaN(bb.upper[i]) && !isNaN(bb.lower[i])) {
        const x = timeToX(priceData.value[i].time)
        const upperY = priceToY(bb.upper[i])
        const lowerY = priceToY(bb.lower[i])
        if (i === 0) {
          ctx.moveTo(x, upperY)
          ctx.lineTo(x, lowerY)
        } else {
          ctx.lineTo(x, lowerY)
        }
      }
    }
    // Close the path
    for (let i = bb.upper.length - 1; i >= 0 && i < priceData.value.length; i--) {
      if (!isNaN(bb.upper[i])) {
        const x = timeToX(priceData.value[i].time)
        const upperY = priceToY(bb.upper[i])
        ctx.lineTo(x, upperY)
      }
    }
    ctx.closePath()
    ctx.fill()
    
    // Highlight when price touches bands
    for (let i = 0; i < priceData.value.length && i < bb.upper.length; i++) {
      const candle = priceData.value[i]
      const upper = bb.upper[i]
      const lower = bb.lower[i]
      
      if (!isNaN(upper) && !isNaN(lower)) {
        // Check if price touched upper band
        if (candle.high >= upper * 0.998) { // 0.2% tolerance
          const x = timeToX(candle.time)
          const y = priceToY(upper)
          ctx.fillStyle = 'rgba(248, 113, 113, 0.6)'
          ctx.beginPath()
          ctx.arc(x, y, 4, 0, Math.PI * 2)
          ctx.fill()
        }
        // Check if price touched lower band
        if (candle.low <= lower * 1.002) { // 0.2% tolerance
          const x = timeToX(candle.time)
          const y = priceToY(lower)
          ctx.fillStyle = 'rgba(74, 222, 128, 0.6)'
          ctx.beginPath()
          ctx.arc(x, y, 4, 0, Math.PI * 2)
          ctx.fill()
        }
      }
    }
    
    // Display Bollinger Band width (squeeze/expansion) in top right
    if (bb.width && bb.width.length > 0) {
      const lastWidth = bb.width[bb.width.length - 1]
      if (!isNaN(lastWidth)) {
        ctx.fillStyle = 'rgba(96, 165, 250, 0.8)'
        ctx.font = '11px sans-serif'
        ctx.textAlign = 'right'
        const yOffset = 15
        ctx.fillText(`BB Width: ${lastWidth.toFixed(2)}%`, width.value - 20, yOffset)
        
        // Color code: green for squeeze (low width), red for expansion (high width)
        const validWidths = bb.width.filter(w => !isNaN(w))
        if (validWidths.length > 0) {
          const avgWidth = validWidths.reduce((a, b) => a + b, 0) / validWidths.length
          if (lastWidth < avgWidth * 0.7) {
            ctx.fillStyle = 'rgba(74, 222, 128, 0.9)' // Squeeze (potential breakout)
            ctx.fillText('Squeeze', width.value - 20, yOffset + 15)
          } else if (lastWidth > avgWidth * 1.3) {
            ctx.fillStyle = 'rgba(248, 113, 113, 0.9)' // Expansion (high volatility)
            ctx.fillText('Expansion', width.value - 20, yOffset + 15)
          }
        }
      }
    }
  }
  
  // Draw indicator combination signals
  if (localShowIndicators.value && priceData.value.length > 0) {
    const lastIndex = priceData.value.length - 1
    const lastCandle = priceData.value[lastIndex]
    let signalY = 30
    
    // Check for RSI oversold + price at lower Bollinger Band
    if (selectedIndicators.value.includes('RSI') && selectedIndicators.value.includes('Bollinger') &&
        indicatorsData.value.RSI.length > lastIndex && indicatorsData.value.Bollinger) {
      const rsi = indicatorsData.value.RSI[lastIndex]
      const bb = indicatorsData.value.Bollinger
      
      if (!isNaN(rsi) && bb.lower && bb.lower.length > lastIndex) {
        const lowerBB = bb.lower[lastIndex]
        const priceNearLower = lastCandle.close <= lowerBB * 1.01 // Within 1% of lower band
        
        if (rsi < 30 && priceNearLower && !isNaN(lowerBB)) {
          // Strong buy signal
          ctx.fillStyle = 'rgba(74, 222, 128, 0.9)'
          ctx.font = 'bold 12px sans-serif'
          ctx.textAlign = 'left'
          ctx.fillText('🔔 BUY Signal: RSI Oversold + Price at Lower BB', 20, signalY)
          signalY += 20
        }
      }
    }
    
    // Check for RSI overbought + price at upper Bollinger Band
    if (selectedIndicators.value.includes('RSI') && selectedIndicators.value.includes('Bollinger') &&
        indicatorsData.value.RSI.length > lastIndex && indicatorsData.value.Bollinger) {
      const rsi = indicatorsData.value.RSI[lastIndex]
      const bb = indicatorsData.value.Bollinger
      
      if (!isNaN(rsi) && bb.upper && bb.upper.length > lastIndex) {
        const upperBB = bb.upper[lastIndex]
        const priceNearUpper = lastCandle.close >= upperBB * 0.99 // Within 1% of upper band
        
        if (rsi > 70 && priceNearUpper && !isNaN(upperBB)) {
          // Strong sell signal
          ctx.fillStyle = 'rgba(248, 113, 113, 0.9)'
          ctx.font = 'bold 12px sans-serif'
          ctx.textAlign = 'left'
          ctx.fillText('🔔 SELL Signal: RSI Overbought + Price at Upper BB', 20, signalY)
          signalY += 20
        }
      }
    }
    
    // Check for Stochastic oversold + RSI oversold
    if (selectedIndicators.value.includes('Stochastic') && selectedIndicators.value.includes('RSI') &&
        indicatorsData.value.Stochastic && indicatorsData.value.RSI.length > lastIndex) {
      const stoch = indicatorsData.value.Stochastic
      const rsi = indicatorsData.value.RSI[lastIndex]
      
      if (stoch.k && stoch.k.length > lastIndex && stoch.d && stoch.d.length > lastIndex) {
        const stochK = stoch.k[lastIndex]
        const stochD = stoch.d[lastIndex]
        
        if (!isNaN(stochK) && !isNaN(stochD) && !isNaN(rsi)) {
          if (stochK < 20 && stochD < 20 && rsi < 30) {
            // Triple oversold - very strong buy signal
            ctx.fillStyle = 'rgba(74, 222, 128, 0.9)'
            ctx.font = 'bold 12px sans-serif'
            ctx.textAlign = 'left'
            ctx.fillText('🔔 STRONG BUY: Triple Oversold (RSI + Stoch K + Stoch D)', 20, signalY)
            signalY += 20
          } else if (stochK > 80 && stochD > 80 && rsi > 70) {
            // Triple overbought - very strong sell signal
            ctx.fillStyle = 'rgba(248, 113, 113, 0.9)'
            ctx.font = 'bold 12px sans-serif'
            ctx.textAlign = 'left'
            ctx.fillText('🔔 STRONG SELL: Triple Overbought (RSI + Stoch K + Stoch D)', 20, signalY)
            signalY += 20
          }
        }
      }
    }
  }
  
  // Draw RSI sub-chart
  if (selectedIndicators.value.includes('RSI') && indicatorsData.value.RSI.length > 0) {
    // RSI is positioned below the main chart and volume
    const rsiY = volumeY + volumeHeight + 10
    const rsiHeight = 80
    
    // RSI background
    ctx.fillStyle = 'rgba(136, 136, 136, 0.1)'
    ctx.fillRect(60, rsiY, width.value - 120, rsiHeight)
    
    // RSI levels (30, 50, 70)
    ctx.strokeStyle = 'rgba(136, 136, 136, 0.3)'
    ctx.lineWidth = 1
    const levels = [30, 50, 70]
    levels.forEach(level => {
      const y = rsiY + rsiHeight - (level / 100) * rsiHeight
      ctx.beginPath()
      ctx.moveTo(60, y)
      ctx.lineTo(width.value - 60, y)
      ctx.stroke()
    })
    
    // RSI line
    ctx.strokeStyle = 'rgba(74, 222, 128, 0.8)'
    ctx.lineWidth = 2
    ctx.beginPath()
    
    let firstPoint = true
    indicatorsData.value.RSI.forEach((rsi, index) => {
      if (!isNaN(rsi) && index < priceData.value.length) {
        const x = timeToX(priceData.value[index].time)
        const y = rsiY + rsiHeight - (rsi / 100) * rsiHeight
        
        if (firstPoint) {
          ctx.moveTo(x, y)
          firstPoint = false
        } else {
          ctx.lineTo(x, y)
        }
      }
    })
    ctx.stroke()
    
    // RSI labels
    ctx.fillStyle = 'rgba(136, 136, 136, 0.8)'
    ctx.font = '10px sans-serif'
    ctx.textAlign = 'right'
    ctx.fillText('100', 55, rsiY + 5)
    ctx.fillText('50', 55, rsiY + rsiHeight / 2 + 4)
    ctx.fillText('0', 55, rsiY + rsiHeight - 2)
    ctx.fillText('RSI', 55, rsiY + rsiHeight / 2 - 20)
  }
  
  // Draw MACD sub-chart
  if (selectedIndicators.value.includes('MACD') && indicatorsData.value.MACD) {
    const macd = indicatorsData.value.MACD
    const macdY = volumeY + volumeHeight + (selectedIndicators.value.includes('RSI') ? 90 : 10)
    const macdHeight = 80
    
    // MACD background
    ctx.fillStyle = 'rgba(20, 20, 30, 0.5)'
    ctx.fillRect(60, macdY, width.value - 120, macdHeight)
    
    // Find min/max for scaling
    let min = Infinity
    let max = -Infinity
    macd.macd.forEach(v => { if (!isNaN(v)) { min = Math.min(min, v); max = Math.max(max, v) } })
    macd.signal.forEach(v => { if (!isNaN(v)) { min = Math.min(min, v); max = Math.max(max, v) } })
    macd.histogram.forEach(v => { if (!isNaN(v)) { min = Math.min(min, v); max = Math.max(max, v) } })
    
    if (min === Infinity) return
    
    const range = max - min || 1
    const macdToY = (value: number) => macdY + macdHeight - ((value - min) / range) * macdHeight
    
    // Zero line
    const zeroY = macdToY(0)
    ctx.strokeStyle = 'rgba(136, 136, 136, 0.5)'
    ctx.lineWidth = 1
    ctx.beginPath()
    ctx.moveTo(60, zeroY)
    ctx.lineTo(width.value - 60, zeroY)
    ctx.stroke()
    
    // Draw histogram
    macd.histogram.forEach((value, index) => {
      if (!isNaN(value) && index < priceData.value.length) {
        const x = timeToX(priceData.value[index].time)
        const y = macdToY(value)
        const zeroYPos = macdToY(0)
        const barHeight = Math.abs(y - zeroYPos)
        
        ctx.fillStyle = value >= 0 ? 'rgba(74, 222, 128, 0.6)' : 'rgba(248, 113, 113, 0.6)'
        ctx.fillRect(x - 2, Math.min(y, zeroYPos), 4, barHeight)
      }
    })
    
    // Draw MACD line
    ctx.strokeStyle = 'rgba(96, 165, 250, 1)'
    ctx.lineWidth = 1.5
    ctx.beginPath()
    let firstPoint = true
    macd.macd.forEach((value, index) => {
      if (!isNaN(value) && index < priceData.value.length) {
        const x = timeToX(priceData.value[index].time)
        const y = macdToY(value)
        if (firstPoint) {
          ctx.moveTo(x, y)
          firstPoint = false
        } else {
          ctx.lineTo(x, y)
        }
      }
    })
    ctx.stroke()
    
    // Draw signal line
    ctx.strokeStyle = 'rgba(251, 191, 36, 1)'
    ctx.lineWidth = 1.5
    ctx.beginPath()
    firstPoint = true
    macd.signal.forEach((value, index) => {
      if (!isNaN(value) && index < priceData.value.length) {
        const x = timeToX(priceData.value[index].time)
        const y = macdToY(value)
        if (firstPoint) {
          ctx.moveTo(x, y)
          firstPoint = false
        } else {
          ctx.lineTo(x, y)
        }
      }
    })
    ctx.stroke()
    
    // MACD labels
    ctx.fillStyle = '#888'
    ctx.font = '10px sans-serif'
    ctx.textAlign = 'right'
    ctx.fillText(max.toFixed(4), 55, macdY + 5)
    ctx.fillText('0', 55, zeroY + 4)
    ctx.fillText(min.toFixed(4), 55, macdY + macdHeight - 2)
    ctx.textAlign = 'left'
    ctx.fillText('MACD', 55, macdY + macdHeight / 2 - 20)
  }
}

// Performance optimization: Schedule redraw using requestAnimationFrame
function scheduleRedraw() {
  if (pendingRedraw) return
  pendingRedraw = true
  if (animationFrameId) {
    cancelAnimationFrame(animationFrameId)
  }
  animationFrameId = requestAnimationFrame(() => {
    drawChart()
    pendingRedraw = false
    animationFrameId = null
  })
}

// Update crosshair tooltip with price and time
function updateCrosshairTooltip(canvasX: number, canvasY: number, screenX: number, screenY: number) {
  if (!chartCanvas.value || priceData.value.length === 0) {
    crosshairTooltip.value.visible = false
    return
  }
  
  const padding = { top: 20, right: 60, bottom: 40, left: 60 }
  const chartWidth = width.value - padding.left - padding.right
  const chartHeight = props.height - padding.top - padding.bottom
  
  // Check if mouse is within chart area
  if (canvasX < padding.left || canvasX > padding.left + chartWidth ||
      canvasY < padding.top || canvasY > padding.top + chartHeight) {
    crosshairTooltip.value.visible = false
    return
  }
  
  // Calculate price and time from mouse position (use same logic as drawChart)
  const times = priceData.value.map(d => d.time)
  const timeMin = Math.min(...times)
  const timeMax = Math.max(...times)
  const timeRange = timeMax - timeMin
  
  const prices = priceData.value.flatMap(d => [d.high, d.low])
  
  // Add price levels to range calculation (same as drawChart)
  const allPrices = [...prices]
  if (props.entryPriceMin) allPrices.push(props.entryPriceMin)
  if (props.entryPriceMax) allPrices.push(props.entryPriceMax)
  if (props.targetPrice) allPrices.push(props.targetPrice)
  if (props.stopLoss) allPrices.push(props.stopLoss)
  if (props.currentPrice) allPrices.push(props.currentPrice)
  
  const priceMin = Math.min(...allPrices)
  const priceMax = Math.max(...allPrices)
  const priceRange = priceMax - priceMin
  const pricePadding = priceRange * 0.1
  
  let chartMinPrice = priceMin - pricePadding
  let chartMaxPrice = priceMax + pricePadding
  
  // Apply zoom to price range (same as drawChart)
  if (props.zoomEnabled && zoomLevel.value !== 1) {
    const centerPrice = (chartMinPrice + chartMaxPrice) / 2
    const zoomedRange = (chartMaxPrice - chartMinPrice) / zoomLevel.value
    chartMinPrice = centerPrice - zoomedRange / 2
    chartMaxPrice = centerPrice + zoomedRange / 2
  }
  
  const chartPriceRange = chartMaxPrice - chartMinPrice
  
  // Convert X to time (account for pan offset if zoom enabled)
  let relativeX = canvasX - padding.left
  if (props.zoomEnabled) {
    // Adjust for pan offset
    relativeX -= panOffset.value.x
  }
  const timeRatio = Math.max(0, Math.min(1, relativeX / chartWidth))
  const time = timeMin + timeRange * timeRatio
  const date = new Date(time * 1000)
  const timeStr = date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
  
  // Convert Y to price (pan only affects X/time, not Y/price)
  const relativeY = canvasY - padding.top
  const priceRatio = Math.max(0, Math.min(1, 1 - (relativeY / chartHeight)))
  const price = chartMinPrice + chartPriceRange * priceRatio
  
  // Update tooltip
  crosshairTooltip.value = {
    x: screenX + 10,
    y: screenY - 10,
    price,
    time: timeStr,
    visible: true
  }
}

// Draw chart on canvas
function drawChart() {
  if (!chartCanvas.value || priceData.value.length === 0) return
  
  const canvas = chartCanvas.value
  const ctx = canvas.getContext('2d')
  if (!ctx) return
  
  const volumeHeight = localShowVolume.value ? 60 : 0
  const padding = { top: 20, right: 60, bottom: 40, left: 60 }
  const chartWidth = width.value - padding.left - padding.right
  const chartHeight = props.height - padding.top - padding.bottom
  // Volume starts at the bottom of the main chart area (after padding)
  const volumeY = props.height - padding.bottom
  
  // Clear canvas
  ctx.clearRect(0, 0, width.value, canvasHeight.value)
  
  // Calculate price range (with zoom support)
  const prices = priceData.value.flatMap(d => [d.high, d.low])
  
  // Add price levels to range calculation
  const allPrices = [...prices]
  if (props.entryPriceMin) allPrices.push(props.entryPriceMin)
  if (props.entryPriceMax) allPrices.push(props.entryPriceMax)
  if (props.targetPrice) allPrices.push(props.targetPrice)
  if (props.stopLoss) allPrices.push(props.stopLoss)
  if (props.currentPrice) allPrices.push(props.currentPrice)
  
  const priceMin = Math.min(...allPrices)
  const priceMax = Math.max(...allPrices)
  const priceRange = priceMax - priceMin
  const pricePadding = priceRange * 0.1
  
  let chartMinPrice = priceMin - pricePadding
  let chartMaxPrice = priceMax + pricePadding
  
  // Apply zoom to price range
  if (props.zoomEnabled && zoomLevel.value !== 1) {
    const centerPrice = (chartMinPrice + chartMaxPrice) / 2
    const zoomedRange = (chartMaxPrice - chartMinPrice) / zoomLevel.value
    chartMinPrice = centerPrice - zoomedRange / 2
    chartMaxPrice = centerPrice + zoomedRange / 2
  }
  
  const chartPriceRange = chartMaxPrice - chartMinPrice
  
  // Time range
  const times = priceData.value.map(d => d.time)
  const timeMin = Math.min(...times)
  const timeMax = Math.max(...times)
  const timeRange = timeMax - timeMin
  
  // Price to Y coordinate
  const priceToY = (price: number) => {
    return padding.top + chartHeight - ((price - chartMinPrice) / chartPriceRange) * chartHeight
  }
  
  // Time to X coordinate (with pan support)
  const timeToX = (time: number) => {
    let x = padding.left + ((time - timeMin) / timeRange) * chartWidth
    if (props.zoomEnabled) {
      x += panOffset.value.x
    }
    return x
  }
  
  // Calculate candle width
  const candleWidth = Math.max(2, Math.min(10, chartWidth / priceData.value.length * 0.8))
  
  // Draw grid lines
  ctx.strokeStyle = 'rgba(136, 136, 136, 0.2)'
  ctx.lineWidth = 1
  
  // Horizontal grid lines (price levels)
  const priceSteps = 5
  for (let i = 0; i <= priceSteps; i++) {
    const price = chartMinPrice + (chartPriceRange / priceSteps) * i
    const y = priceToY(price)
    ctx.beginPath()
    ctx.moveTo(padding.left, y)
    ctx.lineTo(padding.left + chartWidth, y)
    ctx.stroke()
    
    // Price labels
    ctx.fillStyle = 'rgba(136, 136, 136, 0.8)'
    ctx.font = '11px sans-serif'
    ctx.textAlign = 'right'
    ctx.fillText(formatPrice(price), padding.left - 8, y + 4)
  }
  
  // Draw chart based on view mode
  if (localViewMode.value === 'candlestick') {
    drawCandlesticks(ctx, priceToY, timeToX, candleWidth)
  } else {
    // Draw price line
    ctx.strokeStyle = 'rgba(74, 222, 128, 0.8)'
    ctx.lineWidth = 2
    ctx.beginPath()
    
    priceData.value.forEach((point, index) => {
      const x = timeToX(point.time)
      const y = priceToY(point.close)
      
      if (index === 0) {
        ctx.moveTo(x, y)
      } else {
        ctx.lineTo(x, y)
      }
    })
    ctx.stroke()
  }
  
  // Draw volume bars
  drawVolume(ctx, timeToX, candleWidth, volumeHeight, volumeY)
  
  // Draw indicators
  drawIndicators(ctx, priceToY, timeToX, volumeHeight, volumeY)
  
  // Draw historical levels (24h high/low, support/resistance) - lines only
  // Labels are now handled in the priceLevels section to prevent overlap
  if (props.showHistoricalLevels) {
    drawHistoricalLevels(ctx, priceToY, chartWidth, true) // Pass true to skip labels
  }
  
  // Draw position markers
  if (props.showPositions) {
    drawPositionMarkers(ctx, priceToY, timeToX, chartWidth)
  }
  
  // Draw trade history
  if (props.showTrades) {
    drawTradeHistory(ctx, priceToY, timeToX)
  }
  
  // Draw shadow trades (Tuning Mode)
  if (props.showShadowTrades) {
    drawShadowTrades(ctx, priceToY, timeToX)
    drawNeuralOverlays(ctx, timeToX, canvasHeight.value)
  }
  
  // Draw opportunity markers
  if (props.showOpportunities) {
    drawOpportunityMarkers(ctx, priceToY, chartWidth)
  }
  
  // Draw price levels
  const priceLevels: PriceLevel[] = []
  
  if (props.entryPriceMin && props.entryPriceMax) {
    priceLevels.push({
      price: props.entryPriceMin,
      label: 'Entry Min',
      color: 'rgba(74, 222, 128, 0.6)',
      style: 'dashed'
    })
    priceLevels.push({
      price: props.entryPriceMax,
      label: 'Entry Max',
      color: 'rgba(74, 222, 128, 0.6)',
      style: 'dashed'
    })
  }
  
  if (props.targetPrice) {
    priceLevels.push({
      price: props.targetPrice,
      label: 'Target',
      color: 'rgba(74, 222, 128, 1)',
      style: 'solid'
    })
  }
  
  if (props.stopLoss) {
    priceLevels.push({
      price: props.stopLoss,
      label: 'Stop Loss',
      color: 'rgba(248, 113, 113, 1)',
      style: 'solid'
    })
  }
  
  // Collect all price levels with their Y positions for overlap detection
  const allPriceLevels: Array<{ y: number, label: string, color: string, level: PriceLevel }> = []
  
  priceLevels.forEach(level => {
    const y = priceToY(level.price)
    allPriceLevels.push({
      y,
      label: `${level.label}: ${formatPrice(level.price)}`,
      color: level.color,
      level
    })
  })
  
  // Add historical levels if enabled
  if (props.showHistoricalLevels && props.currentPrice) {
    const currentPrice = props.currentPrice
    
    // Calculate 24h high/low from price data if not provided in marketData
    let high24h: number | null = null
    let low24h: number | null = null
    
    if (props.marketData && (props.marketData.high_24h !== undefined || props.marketData.low_24h !== undefined)) {
      high24h = props.marketData.high_24h || null
      low24h = props.marketData.low_24h || null
    }
    
    // If not provided, calculate from price data (last 24 hours worth of candles)
    if (!high24h || !low24h) {
      const now = Date.now() / 1000
      const oneDayAgo = now - (24 * 60 * 60)
      
      const recentData = priceData.value.filter(candle => candle.time >= oneDayAgo)
      if (recentData.length > 0) {
        const highs = recentData.map(c => c.high)
        const lows = recentData.map(c => c.low)
        high24h = high24h || Math.max(...highs)
        low24h = low24h || Math.min(...lows)
      } else {
        // Fallback to current price ± 5% if no data
        high24h = high24h || currentPrice * 1.05
        low24h = low24h || currentPrice * 0.95
      }
    }
    
    // Ensure we have valid values
    if (!high24h) high24h = currentPrice * 1.05
    if (!low24h) low24h = currentPrice * 0.95
    
    if (high24h > currentPrice) {
      const highY = priceToY(high24h)
      allPriceLevels.push({
        y: highY,
        label: `24h High: $${high24h.toFixed(2)}`,
        color: 'rgba(74, 222, 128, 0.8)',
        level: null as any
      })
    }
    
    if (low24h < currentPrice) {
      const lowY = priceToY(low24h)
      allPriceLevels.push({
        y: lowY,
        label: `24h Low: $${low24h.toFixed(2)}`,
        color: 'rgba(248, 113, 113, 0.8)',
        level: null as any
      })
    }
    
    const supportLevel = currentPrice * 0.95
    const supportY = priceToY(supportLevel)
    allPriceLevels.push({
      y: supportY,
      label: `Support: $${supportLevel.toFixed(2)}`,
      color: 'rgba(16, 185, 129, 0.9)',
      level: null as any
    })
    
    const resistanceLevel = currentPrice * 1.05
    const resistanceY = priceToY(resistanceLevel)
    allPriceLevels.push({
      y: resistanceY,
      label: `Resistance: $${resistanceLevel.toFixed(2)}`,
      color: 'rgba(16, 185, 129, 0.9)',
      level: null as any
    })
  }
  
  // Sort by Y position (top to bottom)
  allPriceLevels.sort((a, b) => a.y - b.y)
  
  // Calculate label positions with overlap prevention
  const MIN_LABEL_SPACING = 18 // Minimum pixels between labels
  const labelPositions: Array<{ y: number, offsetX: number }> = []
  
  allPriceLevels.forEach((item, index) => {
    let offsetX = 0
    let labelY = item.y + 4
    
    // Check for overlap with previous labels
    for (let i = index - 1; i >= 0; i--) {
      const prevPos = labelPositions[i]
      const spacing = Math.abs(labelY - prevPos.y)
      if (spacing < MIN_LABEL_SPACING) {
        // Overlap detected - offset this label to the right
        offsetX = Math.max(offsetX, prevPos.offsetX + 120) // 120px per column
        labelY = prevPos.y + MIN_LABEL_SPACING // Stack vertically
      }
    }
    
    labelPositions.push({ y: labelY, offsetX })
  })
  
  // Draw lines and labels
  allPriceLevels.forEach((item, index) => {
    const { level } = item
    const labelPos = labelPositions[index]
    
    // Draw line only for price levels (not historical levels - those are drawn separately)
    if (level) {
      const y = priceToY(level.price)
      ctx.strokeStyle = level.color
      ctx.lineWidth = level.style === 'dashed' ? 1.5 : 2
      ctx.setLineDash(level.style === 'dashed' ? [5, 5] : [])
      
      ctx.beginPath()
      ctx.moveTo(padding.left, y)
      ctx.lineTo(padding.left + chartWidth, y)
      ctx.stroke()
      ctx.setLineDash([])
    }
    
    // Draw label with calculated position
    ctx.fillStyle = item.color
    ctx.font = '11px sans-serif'
    ctx.textAlign = 'left'
    ctx.fillText(item.label, padding.left + chartWidth + 8 + labelPos.offsetX, labelPos.y)
  })
  
  ctx.setLineDash([])
  
  // Draw current price indicator
  if (props.currentPrice) {
    const y = priceToY(props.currentPrice)
    
    // Horizontal line
    ctx.strokeStyle = 'rgba(74, 222, 128, 0.9)'
    ctx.lineWidth = 2
    ctx.setLineDash([3, 3])
    ctx.beginPath()
    ctx.moveTo(padding.left, y)
    ctx.lineTo(padding.left + chartWidth, y)
    ctx.stroke()
    ctx.setLineDash([])
    
    // Circle indicator
    const x = timeToX(timeMax)
    ctx.fillStyle = 'rgba(74, 222, 128, 1)'
    ctx.beginPath()
    ctx.arc(x, y, 4, 0, Math.PI * 2)
    ctx.fill()
    
    // Current price label
    ctx.fillStyle = 'rgba(74, 222, 128, 1)'
    ctx.font = 'bold 12px sans-serif'
    ctx.textAlign = 'right'
    ctx.fillText(`Current: ${formatPrice(props.currentPrice)}`, padding.left + chartWidth, y - 8)
  }
  
  // Draw time labels on X axis
  ctx.fillStyle = 'rgba(136, 136, 136, 0.9)'
  ctx.font = '11px sans-serif'
  ctx.textAlign = 'center'
  
  const timeSteps = 5
  // Calculate Y position at bottom of canvas (accounting for volume and indicator sub-charts)
  // Time labels should be at the very bottom, below all indicators
  let timeLabelY: number
  let offsetY = 0
  if (localShowVolume.value) {
    offsetY += volumeHeight + 10
  }
  if (localShowIndicators.value && selectedIndicators.value.includes('RSI')) {
    offsetY += 80 + 10 // RSI height is 80
  }
  if (localShowIndicators.value && selectedIndicators.value.includes('MACD')) {
    offsetY += 80 + 10 // MACD height is 80
  }
  
  if (offsetY > 0) {
    timeLabelY = volumeY + offsetY + 15 // Add 15px spacing below all indicators
  } else {
    // No volume or indicators, place labels at bottom of main chart
    timeLabelY = props.height - padding.bottom + 15
  }
  
  // Ensure labels don't go beyond canvas
  timeLabelY = Math.min(timeLabelY, canvasHeight.value - 5)
  
  for (let i = 0; i <= timeSteps; i++) {
    const time = timeMin + (timeRange / timeSteps) * i
    const x = timeToX(time)
    
    // Ensure X is within visible bounds
    if (x < padding.left || x > padding.left + chartWidth) continue
    
    const date = new Date(time * 1000)
    // Format time based on timeframe - show more detail for shorter timeframes
    let timeStr: string
    if (localTimeframe.value === '1m' || localTimeframe.value === '5m') {
      timeStr = date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
    } else if (localTimeframe.value === '15m' || localTimeframe.value === '30m') {
      timeStr = date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
    } else {
      timeStr = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) + ' ' + 
                date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
    }
    
    ctx.fillText(timeStr, x, timeLabelY)
  }
}

// Calculate Moving Average
function calculateMA(period: number): number[] {
  if (priceData.value.length < period) return []
  
  const ma: number[] = []
  for (let i = 0; i < priceData.value.length; i++) {
    if (i < period - 1) {
      ma.push(NaN)
    } else {
      let sum = 0
      for (let j = i - period + 1; j <= i; j++) {
        sum += priceData.value[j].close
      }
      ma.push(sum / period)
    }
  }
  return ma
}

// Calculate RSI
function calculateRSI(period: number = 14): number[] {
  if (priceData.value.length < period + 1) return []
  
  const rsi: number[] = []
  const gains: number[] = []
  const losses: number[] = []
  
  // Calculate price changes
  for (let i = 1; i < priceData.value.length; i++) {
    const change = priceData.value[i].close - priceData.value[i - 1].close
    gains.push(change > 0 ? change : 0)
    losses.push(change < 0 ? -change : 0)
  }
  
  // Calculate initial average gain/loss
  let avgGain = gains.slice(0, period).reduce((a, b) => a + b, 0) / period
  let avgLoss = losses.slice(0, period).reduce((a, b) => a + b, 0) / period
  
  rsi.push(NaN) // First value is NaN
  
  // Calculate RSI for remaining periods
  for (let i = period; i < gains.length; i++) {
    avgGain = (avgGain * (period - 1) + gains[i]) / period
    avgLoss = (avgLoss * (period - 1) + losses[i]) / period
    
    if (avgLoss === 0) {
      rsi.push(100)
    } else {
      const rs = avgGain / avgLoss
      rsi.push(100 - (100 / (1 + rs)))
    }
  }
  
  return rsi
}

// Calculate MACD
function calculateMACD(fastPeriod: number = 12, slowPeriod: number = 26, signalPeriod: number = 9) {
  if (priceData.value.length < slowPeriod + signalPeriod) {
    return { macd: [], signal: [], histogram: [] }
  }
  
  const fastEMA = calculateEMA(fastPeriod)
  const slowEMA = calculateEMA(slowPeriod)
  
  const macd: number[] = []
  for (let i = 0; i < fastEMA.length; i++) {
    if (i < slowPeriod - 1) {
      macd.push(NaN)
    } else {
      macd.push(fastEMA[i] - slowEMA[i])
    }
  }
  
  // Calculate signal line (EMA of MACD)
  const signal = calculateEMAFromArray(macd, signalPeriod)
  
  // Calculate histogram (MACD - Signal)
  const histogram: number[] = []
  for (let i = 0; i < macd.length; i++) {
    if (isNaN(macd[i]) || isNaN(signal[i])) {
      histogram.push(NaN)
    } else {
      histogram.push(macd[i] - signal[i])
    }
  }
  
  return { macd, signal, histogram }
}

// Calculate EMA (Exponential Moving Average)
function calculateEMA(period: number): number[] {
  if (priceData.value.length < period) return []
  
  const ema: number[] = []
  const multiplier = 2 / (period + 1)
  
  // First EMA value is SMA
  let sum = 0
  for (let i = 0; i < period; i++) {
    sum += priceData.value[i].close
  }
  ema.push(sum / period)
  
  // Calculate remaining EMA values
  for (let i = period; i < priceData.value.length; i++) {
    ema.push((priceData.value[i].close - ema[ema.length - 1]) * multiplier + ema[ema.length - 1])
  }
  
  // Pad beginning with NaN
  const padded = new Array(period - 1).fill(NaN)
  return [...padded, ...ema]
}

// Calculate EMA from an array of numbers
function calculateEMAFromArray(data: number[], period: number): number[] {
  if (data.length < period) return []
  
  const ema: number[] = []
  const multiplier = 2 / (period + 1)
  
  // Find first valid value
  let startIdx = 0
  while (startIdx < data.length && isNaN(data[startIdx])) {
    startIdx++
  }
  
  if (startIdx >= data.length) return new Array(data.length).fill(NaN)
  
  // First EMA value is average of first period valid values
  let sum = 0
  let count = 0
  for (let i = startIdx; i < Math.min(startIdx + period, data.length); i++) {
    if (!isNaN(data[i])) {
      sum += data[i]
      count++
    }
  }
  
  if (count === 0) return new Array(data.length).fill(NaN)
  
  ema.push(sum / count)
  
  // Calculate remaining EMA values
  for (let i = startIdx + period; i < data.length; i++) {
    if (isNaN(data[i])) {
      ema.push(NaN)
    } else {
      ema.push((data[i] - ema[ema.length - 1]) * multiplier + ema[ema.length - 1])
    }
  }
  
  // Pad beginning with NaN
  const padded = new Array(startIdx).fill(NaN)
  return [...padded, ...ema]
}

// Calculate Bollinger Bands
function calculateBollingerBands(period: number = 20, stdDev: number = 2) {
  if (priceData.value.length < period) {
    return { upper: [], middle: [], lower: [], width: [] }
  }
  
  const middle = calculateMA(period) // Middle band is SMA
  const upper: number[] = []
  const lower: number[] = []
  const width: number[] = []
  
  for (let i = period - 1; i < priceData.value.length; i++) {
    // Calculate standard deviation for this period
    let sum = 0
    for (let j = i - period + 1; j <= i; j++) {
      sum += Math.pow(priceData.value[j].close - middle[i], 2)
    }
    const variance = sum / period
    const standardDeviation = Math.sqrt(variance)
    
    const upperVal = middle[i] + (stdDev * standardDeviation)
    const lowerVal = middle[i] - (stdDev * standardDeviation)
    
    upper.push(upperVal)
    lower.push(lowerVal)
    // Band width = (upper - lower) / middle, as percentage
    width.push((upperVal - lowerVal) / middle[i] * 100)
  }
  
  // Pad beginning with NaN
  const padded = new Array(period - 1).fill(NaN)
  return {
    upper: [...padded, ...upper],
    middle: middle,
    lower: [...padded, ...lower],
    width: [...padded, ...width]
  }
}

// Calculate Stochastic Oscillator
function calculateStochastic(kPeriod: number = 14, dPeriod: number = 3) {
  if (priceData.value.length < kPeriod + dPeriod) {
    return { k: [], d: [] }
  }
  
  const k: number[] = []
  
  // Calculate %K
  for (let i = kPeriod - 1; i < priceData.value.length; i++) {
    let highestHigh = -Infinity
    let lowestLow = Infinity
    
    for (let j = i - kPeriod + 1; j <= i; j++) {
      highestHigh = Math.max(highestHigh, priceData.value[j].high)
      lowestLow = Math.min(lowestLow, priceData.value[j].low)
    }
    
    const currentClose = priceData.value[i].close
    const range = highestHigh - lowestLow
    
    if (range === 0) {
      k.push(50) // Neutral if no range
    } else {
      const stochK = ((currentClose - lowestLow) / range) * 100
      k.push(stochK)
    }
  }
  
  // Calculate %D (SMA of %K)
  const d: number[] = []
  for (let i = 0; i < kPeriod - 1; i++) {
    d.push(NaN)
  }
  
  for (let i = dPeriod - 1; i < k.length; i++) {
    let sum = 0
    for (let j = i - dPeriod + 1; j <= i; j++) {
      sum += k[j]
    }
    d.push(sum / dPeriod)
  }
  
  // Pad beginning of k
  const paddedK = new Array(kPeriod - 1).fill(NaN)
  return {
    k: [...paddedK, ...k],
    d: d
  }
}

// Calculate VWAP (Volume Weighted Average Price)
function calculateVWAP() {
  if (priceData.value.length === 0) return []
  
  const vwap: number[] = []
  let cumulativeTPV = 0 // Cumulative Typical Price * Volume
  let cumulativeVolume = 0
  
  priceData.value.forEach((candle) => {
    const typicalPrice = (candle.high + candle.low + candle.close) / 3
    const volume = candle.volume || 0
    
    cumulativeTPV += typicalPrice * volume
    cumulativeVolume += volume
    
    if (cumulativeVolume === 0) {
      vwap.push(candle.close) // Fallback to close if no volume
    } else {
      vwap.push(cumulativeTPV / cumulativeVolume)
    }
  })
  
  return vwap
}

// Calculate ATR (Average True Range)
function calculateATR(period: number = 14) {
  if (priceData.value.length < period + 1) {
    return []
  }
  
  const trueRanges: number[] = []
  
  // Calculate True Range for each candle
  for (let i = 1; i < priceData.value.length; i++) {
    const current = priceData.value[i]
    const previous = priceData.value[i - 1]
    
    const tr1 = current.high - current.low
    const tr2 = Math.abs(current.high - previous.close)
    const tr3 = Math.abs(current.low - previous.close)
    
    trueRanges.push(Math.max(tr1, tr2, tr3))
  }
  
  // Calculate ATR as SMA of True Ranges
  const atr: number[] = [NaN] // First candle has no ATR
  
  for (let i = period - 1; i < trueRanges.length; i++) {
    let sum = 0
    for (let j = i - period + 1; j <= i; j++) {
      sum += trueRanges[j]
    }
    atr.push(sum / period)
  }
  
  return atr
}

// Calculate all indicators
function calculateIndicators() {
  if (!localShowIndicators.value || priceData.value.length === 0) {
    // Clear indicators when disabled or no data
    indicatorsData.value = { MA: {}, EMA: {}, RSI: [] }
    return
  }
  
  // Initialize with empty structure
  indicatorsData.value = {
    MA: {},
    EMA: {},
    RSI: []
  }
  
  // Calculate only selected indicators with error handling
  try {
    if (selectedIndicators.value.includes('MA')) {
      const ma10 = calculateMA(10)
      const ma20 = calculateMA(20)
      const ma50 = calculateMA(50)
      const ma100 = calculateMA(100)
      const ma200 = calculateMA(200)
      if (ma10 && ma10.length > 0) indicatorsData.value.MA[10] = ma10
      if (ma20 && ma20.length > 0) indicatorsData.value.MA[20] = ma20
      if (ma50 && ma50.length > 0) indicatorsData.value.MA[50] = ma50
      if (ma100 && ma100.length > 0) indicatorsData.value.MA[100] = ma100
      if (ma200 && ma200.length > 0) indicatorsData.value.MA[200] = ma200
    }
    
    if (selectedIndicators.value.includes('EMA')) {
      const ema10 = calculateEMA(10)
      const ema20 = calculateEMA(20)
      const ema50 = calculateEMA(50)
      const ema200 = calculateEMA(200)
      if (ema10 && ema10.length > 0) indicatorsData.value.EMA[10] = ema10
      if (ema20 && ema20.length > 0) indicatorsData.value.EMA[20] = ema20
      if (ema50 && ema50.length > 0) indicatorsData.value.EMA[50] = ema50
      if (ema200 && ema200.length > 0) indicatorsData.value.EMA[200] = ema200
    }
    
    if (selectedIndicators.value.includes('RSI')) {
      const rsi = calculateRSI(14)
      if (rsi && rsi.length > 0) indicatorsData.value.RSI = rsi
    }
    
    if (selectedIndicators.value.includes('MACD')) {
      const macdResult = calculateMACD(12, 26, 9)
      if (macdResult && macdResult.macd && macdResult.macd.length > 0) {
        indicatorsData.value.MACD = macdResult
      }
    }
    
    if (selectedIndicators.value.includes('Bollinger')) {
      const bbResult = calculateBollingerBands(20, 2)
      if (bbResult && bbResult.upper && bbResult.upper.length > 0) {
        indicatorsData.value.Bollinger = bbResult
      }
    }
    
    if (selectedIndicators.value.includes('Stochastic')) {
      const stochResult = calculateStochastic(14, 3)
      if (stochResult && stochResult.k && stochResult.k.length > 0) {
        indicatorsData.value.Stochastic = stochResult
      }
    }
    
    if (selectedIndicators.value.includes('VWAP')) {
      const vwap = calculateVWAP()
      if (vwap && vwap.length > 0) {
        indicatorsData.value.VWAP = vwap
      }
    }
    
    if (selectedIndicators.value.includes('ATR')) {
      const atr = calculateATR(14)
      if (atr && atr.length > 0) {
        indicatorsData.value.ATR = atr
      }
    }
  } catch (err) {
    // Silently handle calculation errors to prevent breaking the chart
    console.error('[PriceChart] Error calculating indicators:', err)
  }
}

// Control handlers
function toggleViewMode() {
  localViewMode.value = localViewMode.value === 'line' ? 'candlestick' : 'line'
  scheduleRedraw()
}

function onTimeframeChange() {
  fetchPriceData()
}

function resetZoom() {
  zoomLevel.value = 1
  panOffset.value = { x: 0, y: 0 }
  visiblePriceRange.value = null
  visibleTimeRange.value = null
  scheduleRedraw()
}

// Zoom/Pan handlers
function handleWheel(e: WheelEvent) {
  if (!props.zoomEnabled) return
  e.preventDefault()
  
  const delta = e.deltaY > 0 ? 0.9 : 1.1
  zoomLevel.value = Math.max(0.5, Math.min(5, zoomLevel.value * delta))
  
  scheduleRedraw()
}

function handleMouseDown(e: MouseEvent) {
  if (!props.zoomEnabled || !chartCanvas.value) return
  isDragging.value = true
  const rect = chartCanvas.value.getBoundingClientRect()
  dragStart.value = { x: e.clientX - rect.left, y: e.clientY - rect.top }
}

function handleMouseMove(e: MouseEvent) {
  if (!chartCanvas.value || priceData.value.length === 0) return
  
  const canvas = chartCanvas.value
  const rect = canvas.getBoundingClientRect()
  const x = e.clientX - rect.left
  const y = e.clientY - rect.top
  
  // Handle dragging for zoom/pan
  if (props.zoomEnabled && isDragging.value) {
    const dx = x - dragStart.value.x
    const dy = y - dragStart.value.y
    
    panOffset.value.x += dx
    panOffset.value.y += dy
    
    dragStart.value = { x, y }
    scheduleRedraw()
    return
  }
  
  // Check for position/trade hover
  checkPositionTradeHover(x, y, e.clientX, e.clientY)
  
  // Update crosshair tooltip
  updateCrosshairTooltip(x, y, e.clientX, e.clientY)
}

// Check if mouse is hovering over a position or trade marker
function checkPositionTradeHover(canvasX: number, canvasY: number, screenX: number, screenY: number) {
  if (!chartCanvas.value || priceData.value.length === 0) {
    positionTooltip.value.visible = false
    tradeTooltip.value.visible = false
    return
  }
  
  // Get coordinate functions - need to match the main draw function logic
  const padding = { top: 20, right: 20, bottom: 40, left: 60 }
  const chartWidth = width.value - padding.left - padding.right
  const chartHeight = props.height - padding.top - padding.bottom
  
  // Calculate price range (matching main draw function)
  const prices = priceData.value.map(d => d.close)
  const priceMin = Math.min(...prices)
  const priceMax = Math.max(...prices)
  const pricePadding = (priceMax - priceMin) * 0.1
  let chartMinPrice = priceMin - pricePadding
  let chartMaxPrice = priceMax + pricePadding
  
  // Apply zoom to price range
  if (props.zoomEnabled && zoomLevel.value !== 1) {
    const centerPrice = (chartMinPrice + chartMaxPrice) / 2
    const zoomedRange = (chartMaxPrice - chartMinPrice) / zoomLevel.value
    chartMinPrice = centerPrice - zoomedRange / 2
    chartMaxPrice = centerPrice + zoomedRange / 2
  }
  
  const chartPriceRange = chartMaxPrice - chartMinPrice || 1
  
  // Time range
  const times = priceData.value.map(d => d.time)
  const timeMin = Math.min(...times)
  const timeMax = Math.max(...times)
  const timeRange = timeMax - timeMin || 1
  
  const priceToY = (price: number) => {
    return padding.top + chartHeight - ((price - chartMinPrice) / chartPriceRange) * chartHeight
  }
  
  const timeToX = (time: number) => {
    let x = padding.left + ((time - timeMin) / timeRange) * chartWidth
    if (props.zoomEnabled) {
      x += panOffset.value.x
    }
    return x
  }
  const HOVER_THRESHOLD = 10 // pixels
  
  // Check positions
  if (props.showPositions && props.positions && props.positions.length > 0) {
    let foundPosition: Position | null = null
    
    for (const position of props.positions) {
      try {
        if (!position || typeof position.entry_price !== 'number' || typeof position.current_price !== 'number') continue
        
        let entryTime = parseTimestampToSeconds(position.entry_time)
        if (entryTime === 0 || isNaN(entryTime)) continue
        
        const entryX = timeToX(entryTime)
        const entryY = priceToY(position.entry_price)
        const currentY = priceToY(position.current_price)
        const currentX = timeToX(Math.floor(Date.now() / 1000))
        
        // Check if mouse is near entry point, current point, or line
        const distToEntry = Math.sqrt(Math.pow(canvasX - entryX, 2) + Math.pow(canvasY - entryY, 2))
        const distToCurrent = Math.sqrt(Math.pow(canvasX - currentX, 2) + Math.pow(canvasY - currentY, 2))
        const distToLine = Math.abs(canvasY - entryY) // Distance to horizontal entry line
        
        if (distToEntry < HOVER_THRESHOLD || distToCurrent < HOVER_THRESHOLD || distToLine < 3) {
          foundPosition = position
          break
        }
      } catch {
        continue
      }
    }
    
    if (foundPosition) {
      positionTooltip.value = {
        visible: true,
        x: screenX + 10,
        y: screenY - 10,
        position: foundPosition
      }
    } else {
      positionTooltip.value.visible = false
    }
  } else {
    positionTooltip.value.visible = false
  }
  
  // Check trades
  if (props.showTrades && props.tradeHistory && props.tradeHistory.length > 0) {
    let foundTrade: Trade | null = null
    
    for (const trade of props.tradeHistory) {
      try {
        if (!trade || typeof trade.entry_price !== 'number' || typeof trade.exit_price !== 'number') continue
        
        let entryTime = parseTimestampToSeconds(trade.timestamp)
        let exitTime = 0
        
        if (entryTime === 0 || isNaN(entryTime)) continue
        
        exitTime = entryTime + (trade.hold_time_seconds || 0)
        
        const entryX = timeToX(entryTime)
        const exitX = timeToX(exitTime)
        const entryY = priceToY(trade.entry_price)
        const exitY = priceToY(trade.exit_price)
        
        // Check if mouse is near entry point, exit point, or line
        const distToEntry = Math.sqrt(Math.pow(canvasX - entryX, 2) + Math.pow(canvasY - entryY, 2))
        const distToExit = Math.sqrt(Math.pow(canvasX - exitX, 2) + Math.pow(canvasY - exitY, 2))
        
        // Check distance to line segment
        const lineLength = Math.sqrt(Math.pow(exitX - entryX, 2) + Math.pow(exitY - entryY, 2))
        if (lineLength > 0) {
          const t = Math.max(0, Math.min(1, ((canvasX - entryX) * (exitX - entryX) + (canvasY - entryY) * (exitY - entryY)) / (lineLength * lineLength)))
          const projX = entryX + t * (exitX - entryX)
          const projY = entryY + t * (exitY - entryY)
          const distToLine = Math.sqrt(Math.pow(canvasX - projX, 2) + Math.pow(canvasY - projY, 2))
          
          if (distToEntry < HOVER_THRESHOLD || distToExit < HOVER_THRESHOLD || distToLine < 5) {
            foundTrade = trade
            break
          }
        }
      } catch {
        continue
      }
    }
    
    if (foundTrade) {
      tradeTooltip.value = {
        visible: true,
        x: screenX + 10,
        y: screenY - 10,
        trade: foundTrade
      }
    } else {
      tradeTooltip.value.visible = false
    }
  } else {
    tradeTooltip.value.visible = false
  }
}

function handleMouseLeave() {
  isDragging.value = false
  crosshairTooltip.value.visible = false
  positionTooltip.value.visible = false
  tradeTooltip.value.visible = false
}

function handleMouseUp() {
  isDragging.value = false
}

function formatNumber(num: number, decimals: number = 2): string {
  if (num === null || num === undefined || isNaN(num)) return '0'
  return num.toLocaleString('en-US', { 
    minimumFractionDigits: decimals, 
    maximumFractionDigits: decimals 
  })
}

function formatDuration(seconds: number): string {
  if (seconds < 60) return `${seconds}s`
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m`
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`
  return `${Math.floor(seconds / 86400)}d ${Math.floor((seconds % 86400) / 3600)}h`
}

function formatPrice(price: number): string {
  if (price >= 1000) {
    return price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
  } else if (price >= 1) {
    return price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 4 })
  } else {
    return price.toLocaleString('en-US', { minimumFractionDigits: 4, maximumFractionDigits: 8 })
  }
}

// Watch for prop changes and redraw
watch(() => [props.symbol, props.currentPrice, props.entryPriceMin, props.entryPriceMax, props.targetPrice, props.stopLoss], 
  () => {
    if (props.symbol) {
      fetchPriceData()
    }
  },
  { immediate: false }
)

// Watch for timeframe changes
watch(localTimeframe, () => {
  fetchPriceData()
})

// Watch for view mode changes
watch(localViewMode, () => {
  scheduleRedraw()
})

// Watch for volume/indicators toggles
watch([localShowVolume, localShowIndicators, selectedIndicators], () => {
  if (localShowIndicators.value) {
    calculateIndicators()
  }
  scheduleRedraw()
}, { deep: true })

// Watch for realtime prop changes
watch(() => props.realtime, (newVal) => {
  if (newVal) {
    startRealtimeUpdates()
  } else {
    stopRealtimeUpdates()
  }
})

// Watch for data changes and redraw
watch(priceData, () => {
  scheduleRedraw()
}, { deep: true })

// Debounce resize handler for performance
let resizeTimeout: ReturnType<typeof setTimeout> | null = null

// Handle resize with debouncing
function updateWidth() {
  if (resizeTimeout) {
    clearTimeout(resizeTimeout)
  }
  
  resizeTimeout = setTimeout(() => {
    if (containerRef.value) {
      const containerWidth = containerRef.value.clientWidth
      if (containerWidth > 0) {
        width.value = containerWidth
        scheduleRedraw()
      }
    } else if (chartCanvas.value?.parentElement) {
      const parentWidth = chartCanvas.value.parentElement.clientWidth
      if (parentWidth > 0) {
        width.value = parentWidth
        scheduleRedraw()
      }
    }
    resizeTimeout = null
  }, 150) // Debounce resize by 150ms
}

let resizeObserver: ResizeObserver | null = null

onMounted(() => {
  // Initialize local state from props
  localViewMode.value = props.viewMode
  localTimeframe.value = props.timeframe
  localShowVolume.value = props.showVolume
  localShowIndicators.value = props.showIndicators
  selectedIndicators.value = [...(props.indicators || [])]
  
  if (props.symbol) {
    fetchPriceData()
  }
  
  // Initial width update
  updateWidth()
  
  // Use ResizeObserver for container-based resizing
  if (containerRef.value && 'ResizeObserver' in window) {
    resizeObserver = new ResizeObserver(() => {
      updateWidth()
    })
    resizeObserver.observe(containerRef.value)
  }
  
  // Fallback to window resize
  window.addEventListener('resize', updateWidth)
  
  if (props.realtime) {
    startRealtimeUpdates()
  }
  
  // Also watch for height changes
  watch(() => props.height, () => {
    scheduleRedraw()
  })
  
  scheduleRedraw()
})

onUnmounted(() => {
  window.removeEventListener('resize', updateWidth)
  if (resizeObserver) {
    resizeObserver.disconnect()
  }
  if (resizeTimeout) {
    clearTimeout(resizeTimeout)
  }
  if (animationFrameId) {
    cancelAnimationFrame(animationFrameId)
  }
  stopRealtimeUpdates()
})
</script>

<style scoped>
.price-chart-container {
  width: 100%;
  height: 100%;
  min-width: 0;
  min-height: 0;
  position: relative;
  display: flex;
  flex-direction: column;
  flex: 1 1 auto;
  overflow: hidden;
}

.chart-controls {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px;
  background: var(--color-bg-card, rgba(20, 20, 30, 0.5));
  border-bottom: 1px solid var(--color-text-muted, rgba(136, 136, 136, 0.2));
}

.controls-row {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.layer-controls {
  display: flex;
  align-items: center;
  gap: 12px;
  padding-top: 8px;
  border-top: 1px solid var(--color-text-muted, rgba(136, 136, 136, 0.2));
}

.layer-toggle {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 8px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  color: var(--color-text-muted, #888);
  transition: all 0.2s ease;
}

.layer-toggle:hover {
  background: var(--color-accent-dark, rgba(74, 222, 128, 0.1));
  color: var(--color-text, #e8e8e8);
}

.layer-toggle.active {
  background: var(--color-accent-dark, rgba(74, 222, 128, 0.2));
  color: var(--color-accent, #4ade80);
}

.layer-toggle input[type="checkbox"] {
  width: 14px;
  height: 14px;
  accent-color: var(--color-accent, #4ade80);
  cursor: pointer;
}

.control-select {
  padding: 6px 10px;
  border: 1px solid var(--color-text-muted, rgba(136, 136, 136, 0.3));
  border-radius: 4px;
  background: var(--color-bg, rgba(10, 10, 10, 0.8));
  color: var(--color-text, #e8e8e8);
  font-size: 12px;
  cursor: pointer;
  transition: border-color 0.2s ease;
}

.control-select:hover {
  border-color: var(--color-accent, rgba(74, 222, 128, 0.5));
}

.control-select.indicators-select {
  min-width: 100px;
}

.control-btn {
  padding: 6px 12px;
  border: 1px solid var(--color-text-muted, rgba(136, 136, 136, 0.3));
  border-radius: 4px;
  background: var(--color-bg, rgba(10, 10, 10, 0.8));
  color: var(--color-text, #e8e8e8);
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.control-btn:hover {
  border-color: var(--color-accent, rgba(74, 222, 128, 0.5));
  background: var(--color-accent-dark, rgba(74, 222, 128, 0.1));
}

.control-checkbox {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--color-text, #e8e8e8);
  cursor: pointer;
}

.control-checkbox input[type="checkbox"] {
  cursor: pointer;
}

.price-chart {
  width: 100%;
  height: 100%;
  display: block;
  cursor: grab;
}

.price-chart:active {
  cursor: grabbing;
}

.chart-loading,
.chart-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 300px;
  gap: 12px;
  color: var(--color-text-muted, #888);
  font-size: 14px;
}

.loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid var(--color-text-muted, rgba(136, 136, 136, 0.2));
  border-top-color: var(--color-accent, #4ade80);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-text {
  color: var(--color-text-muted, #888);
  font-size: 14px;
}

.chart-error {
  color: var(--color-danger, #f87171);
}

.error-icon {
  font-size: 32px;
  margin-bottom: 8px;
}

.error-message {
  text-align: center;
  max-width: 400px;
  line-height: 1.5;
}

.retry-button {
  margin-top: 8px;
  padding: 8px 16px;
  background: var(--color-accent, #4ade80);
  color: var(--color-bg, #0a0a0a);
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s ease;
}

.retry-button:hover {
  background: var(--color-accent-dark, rgba(74, 222, 128, 0.8));
}

/* Crosshair Tooltip */
.crosshair-tooltip,
.position-tooltip,
.trade-tooltip {
  position: fixed;
  pointer-events: none;
  z-index: 1000;
  background: var(--color-bg-card, rgba(20, 20, 30, 0.95));
  border: 1px solid var(--color-text-muted, rgba(136, 136, 136, 0.3));
  border-radius: 6px;
  padding: 8px 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  max-width: 250px;
}

.position-tooltip,
.trade-tooltip {
  border-color: var(--color-accent, rgba(74, 222, 128, 0.4));
  box-shadow: 0 4px 16px rgba(74, 222, 128, 0.2);
}

.tooltip-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.tooltip-row {
  display: flex;
  gap: 8px;
  font-size: 12px;
}

.tooltip-label {
  color: var(--color-text-muted, #888);
}

.tooltip-header {
  font-weight: 600;
  font-size: 13px;
  color: var(--color-accent, #4ade80);
  margin-bottom: 6px;
  padding-bottom: 4px;
  border-bottom: 1px solid var(--color-text-muted, rgba(136, 136, 136, 0.2));
}

.tooltip-value.positive {
  color: var(--color-accent, #4ade80);
  font-weight: 600;
}

.tooltip-value.negative {
  color: var(--color-danger, #f87171);
  font-weight: 600;
}

.tooltip-value {
  color: var(--color-text, #e8e8e8);
  font-weight: 500;
}

/* Light mode adjustments */
@media (prefers-color-scheme: light) {
  .chart-controls {
    background: var(--color-bg-card, rgba(255, 255, 255, 0.5));
    border-bottom-color: var(--color-text-muted, rgba(107, 114, 128, 0.2));
  }
  
  .control-select,
  .control-btn {
    background: var(--color-bg, rgba(255, 255, 255, 0.8));
    color: var(--color-text, #1a1a1a);
    border-color: var(--color-text-muted, rgba(107, 114, 128, 0.3));
  }
  
  .control-checkbox {
    color: var(--color-text, #1a1a1a);
  }
}

</style>

