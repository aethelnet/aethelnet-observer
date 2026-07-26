<template>
  <div v-if="show" class="modal-overlay" @click.self="close">
    <div class="modal-content" :class="{ 'analysis-mode': analysisMode }">
      <div class="modal-header">
        <h3>{{ analysisMode ? 'Order Analysis' : 'Order Preview' }}</h3>
        <button class="close-btn" @click="close">×</button>
      </div>
      
      <div class="modal-body">
        <!-- Opportunity Summary -->
        <div class="opportunity-summary">
          <div class="summary-row">
            <span class="label">Symbol:</span>
            <span class="value">{{ opportunity.symbol }}</span>
          </div>
          <div class="summary-row">
            <span class="label">Type:</span>
            <span class="value" :class="opportunity.opportunity_type?.toLowerCase()">
              {{ opportunity.opportunity_type || 'TRADE' }}
            </span>
          </div>
          <div class="summary-row">
            <span class="label">Confidence:</span>
            <span class="value">{{ formatConfidence(opportunity.confidence || 0) }}</span>
          </div>
        </div>
        
        <!-- Price Chart (Analysis Mode) -->
        <div class="section chart-section" v-if="analysisMode && opportunity">
          <h4>Price Analysis</h4>
          <PriceChart
            :symbol="opportunity.symbol"
            :current-price="currentPrice"
            :entry-price-min="entryPriceRange?.min"
            :entry-price-max="entryPriceRange?.max"
            :target-price="opportunity.target_price"
            :stop-loss="opportunity.stop_loss"
            :height="400"
            :view-mode="'candlestick'"
            :timeframe="'5m'"
            :show-volume="true"
            :show-indicators="true"
            :indicators="['MA', 'RSI']"
            :zoom-enabled="true"
            :realtime="true"
          />
        </div>
        
        <!-- Entry Conditions -->
        <div class="section">
          <h4>Entry Conditions</h4>
          <div class="entry-details">
            <div class="detail-row" v-if="entryWindow">
              <span class="label">Time Window:</span>
              <span class="value">
                {{ formatTimeWindow(entryWindow.start, entryWindow.end) }}
                <span class="countdown">(Valid for {{ formatDuration(getWindowSeconds(entryWindow)) }})</span>
              </span>
            </div>
            <div class="detail-row" v-if="entryPriceRange">
              <span class="label">Price Range:</span>
              <span class="value">
                ${{ formatNumber(entryPriceRange.min) }} - ${{ formatNumber(entryPriceRange.max) }}
              </span>
            </div>
            <div class="detail-row" v-if="entryPriceRange">
              <span class="label">Trigger Price:</span>
              <span class="value highlight">
                ${{ formatNumber(entryPriceRange.trigger || entryPriceRange.max) }}
                <span v-if="entryPriceRange.tolerance" class="tolerance">
                  ±${{ formatNumber(entryPriceRange.tolerance) }}
                </span>
              </span>
            </div>
            <div class="detail-row" v-if="currentPrice">
              <span class="label">Current Price:</span>
              <span class="value">${{ formatNumber(currentPrice) }}</span>
            </div>
          </div>
        </div>
        
        <!-- Trade Details -->
        <div class="section">
          <h4>Trade Details</h4>
          <div class="trade-details">
            <div class="detail-row" v-if="execution?.quantity">
              <span class="label">Quantity:</span>
              <span class="value">{{ formatNumber(execution.quantity, 8) }} {{ getBaseSymbol(opportunity.symbol) }}</span>
            </div>
            <div class="detail-row" v-if="execution?.position_value">
              <span class="label">Position Value:</span>
              <span class="value">${{ formatNumber(execution.position_value) }}</span>
            </div>
            <div class="detail-row" v-if="opportunity.target_price">
              <span class="label">Target Price:</span>
              <span class="value positive">${{ formatNumber(opportunity.target_price) }}</span>
            </div>
            <div class="detail-row" v-if="opportunity.stop_loss">
              <span class="label">Stop Loss:</span>
              <span class="value negative">${{ formatNumber(opportunity.stop_loss) }}</span>
            </div>
            <div class="detail-row" v-if="riskMetrics">
              <span class="label">Expected Profit:</span>
              <span class="value positive large">
                {{ formatPercent(opportunity.potential_profit_percent || opportunity.expected_move_percent || 0) }}
                <span v-if="riskMetrics.expected_profit" class="amount">
                  ({{ formatCurrency(riskMetrics.expected_profit) }})
                </span>
              </span>
            </div>
            <div class="detail-row" v-if="riskMetrics?.max_loss">
              <span class="label">Max Loss:</span>
              <span class="value negative">
                {{ formatPercent(riskMetrics.max_loss_percent || 0) }}
                <span class="amount">({{ formatCurrency(riskMetrics.max_loss) }})</span>
              </span>
            </div>
            <div class="detail-row" v-if="riskMetrics?.risk_reward_ratio">
              <span class="label">Risk/Reward:</span>
              <span class="value">{{ formatNumber(riskMetrics.risk_reward_ratio, 2) }}:1</span>
            </div>
          </div>
        </div>
        
        <!-- Order Type -->
        <div class="section">
          <h4>Order Configuration</h4>
          <div class="order-config">
            <div class="detail-row">
              <span class="label">Order Type:</span>
              <span class="value">{{ execution?.order_type || 'LIMIT' }}</span>
            </div>
            <div class="detail-row" v-if="execution?.time_in_force">
              <span class="label">Time in Force:</span>
              <span class="value">{{ execution.time_in_force }}</span>
            </div>
          </div>
        </div>
        
        <!-- Fund Allocation Manager -->
        <div class="section fund-allocation-section" v-if="!analysisMode">
          <h4>Fund Allocation</h4>
          
          <!-- Total Available Funds Summary -->
          <div class="fund-summary" v-if="budgetData">
            <div class="total-funds">
              <span class="label">Total Available:</span>
              <span class="value">${{ formatCurrency(totalAvailableFunds) }}</span>
            </div>
          </div>
          
          <!-- Partition Manager -->
          <div class="partition-manager" v-if="budgetData && fundPartitions.length > 0">
            <div 
              v-for="partition in fundPartitions" 
              :key="partition.id"
              class="partition-item"
              :class="{ 
                'selected': selectedAllocationSource === partition.id,
                'insufficient': partition.available < minAllocation,
                'reserve': partition.id === 'reserve'
              }"
              @click="selectPartition(partition.id)"
            >
              <div class="partition-header">
                <span class="partition-name">{{ partition.name }}</span>
                <span class="partition-amount">${{ formatCurrency(partition.available) }}</span>
              </div>
              <div class="partition-bar">
                <div 
                  class="partition-fill" 
                  :style="{ width: partition.percentage + '%' }"
                  :class="partition.id"
                ></div>
              </div>
              <div class="partition-metrics" v-if="partition.performance">
                <span class="metric">P&L: {{ formatCurrency(partition.performance.pnl) }}</span>
                <span class="metric">Win Rate: {{ formatPercent(partition.performance.winRate * 100) }}</span>
                <span class="metric">Trades: {{ partition.performance.trades }}</span>
              </div>
            </div>
          </div>
          
          <!-- Allocation Controls -->
          <div class="allocation-controls" v-if="budgetData">
            <div class="control-group">
              <label>Allocation Source:</label>
              <select v-model="selectedAllocationSource" @change="onAllocationSourceChange">
                <option value="trading_pool">Trading Pool</option>
                <option value="whitelist">Whitelist</option>
                <option value="auto_discovery">Auto-Discovery</option>
                <option value="reserve">Reserve</option>
              </select>
            </div>
            
            <div class="control-group">
              <label>Allocation Amount:</label>
              <div class="amount-input-group">
                <input 
                  type="number" 
                  v-model.number="customAllocationAmount"
                  :min="0"
                  :max="selectedPartitionAvailable"
                  step="0.01"
                  placeholder="Enter amount"
                  @input="validateAllocationAmount"
                />
                <span class="currency">USD</span>
              </div>
              <div class="preset-buttons">
                <button 
                  v-for="preset in [25, 50, 75, 100]" 
                  :key="preset"
                  @click="setPresetAllocation(preset)"
                  class="preset-btn"
                  :disabled="selectedPartitionAvailable === 0"
                >
                  {{ preset }}%
                </button>
              </div>
              <div class="allocation-warning" v-if="selectedAllocationSource === 'reserve' && allocatedAmount > 0">
                <span class="warning-icon">⚠️</span>
                <span>Reserve pool allocation requires confirmation</span>
              </div>
              <div class="allocation-error" v-if="allocationError">
                {{ allocationError }}
              </div>
            </div>
            
            <!-- Updated Position Value Preview -->
            <div class="allocation-preview" v-if="allocatedAmount > 0">
              <div class="preview-row">
                <span class="label">Original Position Value:</span>
                <span class="value">${{ formatCurrency(originalPositionValue) }}</span>
              </div>
              <div class="preview-row">
                <span class="label">Allocated Amount:</span>
                <span class="value highlight">${{ formatCurrency(allocatedAmount) }}</span>
              </div>
              <div class="preview-row">
                <span class="label">New Position Value:</span>
                <span class="value large">${{ formatCurrency(newPositionValue) }}</span>
              </div>
            </div>
          </div>
          
          <div v-if="!budgetData && !loadingBudget" class="budget-loading">
            <p>Loading budget allocation...</p>
          </div>
        </div>
      </div>
      
      <div class="modal-footer" v-if="!analysisMode">
        <button class="btn-cancel" @click="close">Cancel</button>
        <button class="btn-confirm" @click="confirm" :disabled="confirming">
          {{ confirming ? 'Placing Order...' : 'Confirm Order' }}
        </button>
      </div>
      <div class="modal-footer" v-else>
        <button class="btn-close-analysis" @click="close">Close</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import PriceChart from './PriceChart.vue'
import { fetchBudgetAllocation } from '../shared/api.js'

interface EntryPriceRange {
  min: number
  max: number
  trigger?: number
  tolerance?: number
}

interface EntryTimeWindow {
  start: string
  end: string
  expires_at: string
}

interface Execution {
  order_type?: string
  quantity?: number
  position_value?: number
  time_in_force?: string
}

interface RiskMetrics {
  max_loss?: number
  max_loss_percent?: number
  risk_reward_ratio?: number
  expected_profit?: number
}

interface Opportunity {
  id?: string
  symbol: string
  opportunity_type?: string
  confidence?: number
  target_price?: number
  stop_loss?: number
  potential_profit_percent?: number
  expected_move_percent?: number
  entry_price_range?: EntryPriceRange
  entry_time_window?: EntryTimeWindow
  execution?: Execution
  risk_metrics?: RiskMetrics
}

const props = defineProps<{
  show: boolean
  opportunity: Opportunity | null
  currentPrice?: number
  analysisMode?: boolean
}>()

const emit = defineEmits<{
  confirm: [allocationData?: {
    allocationSource: string
    allocatedAmount: number
    originalPositionValue: number
    newPositionValue: number
    confirmReserve?: boolean
  }]
  close: []
}>()

const confirming = ref(false)

// Fund allocation state
const budgetData = ref<any>(null)
const loadingBudget = ref(false)
const selectedAllocationSource = ref<string>('trading_pool')
const customAllocationAmount = ref<number | null>(null)
const allocationError = ref<string | null>(null)
const performanceMetrics = ref<any>(null)
const minAllocation = ref(0.01) // Minimum allocation amount

const entryPriceRange = computed(() => props.opportunity?.entry_price_range)
const entryWindow = computed(() => props.opportunity?.entry_time_window)
const execution = computed(() => props.opportunity?.execution)
const riskMetrics = computed(() => props.opportunity?.risk_metrics)

function formatNumber(num: number, decimals: number = 2): string {
  if (num === null || num === undefined) return '0'
  return num.toLocaleString('en-US', { 
    minimumFractionDigits: decimals, 
    maximumFractionDigits: decimals 
  })
}

function formatCurrency(value: number): string {
  if (value === null || value === undefined) return '$0.00'
  const sign = value >= 0 ? '+' : ''
  return `${sign}$${value.toFixed(2)}`
}

function formatPercent(value: number): string {
  if (value === null || value === undefined) return '0%'
  const sign = value >= 0 ? '+' : ''
  return `${sign}${value.toFixed(2)}%`
}

function formatConfidence(confidence: number): string {
  if (confidence === null || confidence === undefined) return '0%'
  return `${(confidence * 100).toFixed(0)}%`
}

function formatDuration(seconds: number): string {
  if (!seconds || seconds < 0) return '0s'
  const minutes = Math.floor(seconds / 60)
  const secs = seconds % 60
  if (minutes > 0) {
    return `${minutes}m ${secs}s`
  }
  return `${secs}s`
}

function formatTimeWindow(start: string, end: string): string {
  try {
    const startDate = new Date(start)
    const endDate = new Date(end)
    const startTime = startDate.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
    const endTime = endDate.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
    return `${startTime} - ${endTime}`
  } catch {
    return `${start} - ${end}`
  }
}

function getWindowSeconds(window: EntryTimeWindow): number {
  try {
    const end = new Date(window.end)
    const now = new Date()
    return Math.max(0, Math.floor((end.getTime() - now.getTime()) / 1000))
  } catch {
    return 0
  }
}

function getBaseSymbol(symbol: string): string {
  // Extract base symbol (e.g., "BTC" from "BTCUSDT")
  if (symbol.includes('USDT') || symbol.includes('USDC') || symbol.includes('EUR')) {
    return symbol.replace(/USDT|USDC|EUR/g, '')
  }
  return symbol.substring(0, 3)
}

// Fund allocation computed properties
const totalAvailableFunds = computed(() => {
  if (!budgetData.value) return 0
  return (budgetData.value.trading_pool || 0) + 
         (budgetData.value.whitelist || 0) + 
         (budgetData.value.auto_discovery || 0) + 
         (budgetData.value.reserve || 0)
})

const fundPartitions = computed(() => {
  if (!budgetData.value) return []
  const total = totalAvailableFunds.value
  if (total === 0) return []
  
  return [
    {
      id: 'trading_pool',
      name: 'Trading Pool',
      available: budgetData.value.trading_pool || 0,
      percentage: total > 0 ? ((budgetData.value.trading_pool || 0) / total) * 100 : 0,
      performance: performanceMetrics.value?.trading_pool
    },
    {
      id: 'whitelist',
      name: 'Whitelist',
      available: budgetData.value.whitelist || 0,
      percentage: total > 0 ? ((budgetData.value.whitelist || 0) / total) * 100 : 0,
      performance: performanceMetrics.value?.whitelist
    },
    {
      id: 'auto_discovery',
      name: 'Auto-Discovery',
      available: budgetData.value.auto_discovery || 0,
      percentage: total > 0 ? ((budgetData.value.auto_discovery || 0) / total) * 100 : 0,
      performance: performanceMetrics.value?.auto_discovery
    },
    {
      id: 'reserve',
      name: 'Reserve',
      available: budgetData.value.reserve || 0,
      percentage: total > 0 ? ((budgetData.value.reserve || 0) / total) * 100 : 0,
      performance: performanceMetrics.value?.reserve
    }
  ]
})

const selectedPartitionAvailable = computed(() => {
  const partition = fundPartitions.value.find(p => p.id === selectedAllocationSource.value)
  return partition?.available || 0
})

const allocatedAmount = computed(() => {
  if (customAllocationAmount.value !== null && customAllocationAmount.value > 0) {
    return Math.min(customAllocationAmount.value, selectedPartitionAvailable.value)
  }
  return 0
})

const originalPositionValue = computed(() => {
  return props.opportunity?.execution?.position_value || 0
})

const newPositionValue = computed(() => {
  return allocatedAmount.value || originalPositionValue.value
})

// Fund allocation methods
async function fetchBudgetData() {
  loadingBudget.value = true
  allocationError.value = null
  try {
    const data = await fetchBudgetAllocation()
    if (data) {
      budgetData.value = data
      // Extract performance metrics if available (optional enhancement)
      // This would come from the same endpoint if backend provides it
    }
  } catch (err) {
    console.error('[OrderPreviewModal] Failed to fetch budget allocation:', err)
  } finally {
    loadingBudget.value = false
  }
}

function selectPartition(partitionId: string) {
  selectedAllocationSource.value = partitionId
  customAllocationAmount.value = null
  allocationError.value = null
}

function onAllocationSourceChange() {
  customAllocationAmount.value = null
  allocationError.value = null
}

function setPresetAllocation(percentage: number) {
  const available = selectedPartitionAvailable.value
  if (available > 0) {
    customAllocationAmount.value = (available * percentage) / 100
    allocationError.value = null
  }
}

function validateAllocationAmount() {
  allocationError.value = null
  
  if (customAllocationAmount.value === null || customAllocationAmount.value <= 0) {
    return
  }
  
  if (customAllocationAmount.value > selectedPartitionAvailable.value) {
    allocationError.value = `Insufficient funds. Available: $${formatCurrency(selectedPartitionAvailable.value)}`
    customAllocationAmount.value = selectedPartitionAvailable.value
  }
  
  if (customAllocationAmount.value < minAllocation.value) {
    allocationError.value = `Minimum allocation is $${formatCurrency(minAllocation.value)}`
  }
}

function close() {
  emit('close')
  // Reset allocation state when closing
  customAllocationAmount.value = null
  selectedAllocationSource.value = 'trading_pool'
  allocationError.value = null
}

function confirm() {
  console.log('[DEBUG] OrderPreviewModal confirm() called', { opportunityId: props.opportunity?.id, symbol: props.opportunity?.symbol });
  
  // Validate allocation if provided
  if (allocatedAmount.value > 0) {
    if (allocatedAmount.value > selectedPartitionAvailable.value) {
      allocationError.value = 'Insufficient funds in selected pool'
      return
    }
    
    if (selectedAllocationSource.value === 'reserve' && allocatedAmount.value > 0) {
      // Reserve allocation requires confirmation - frontend will show warning
      // Backend should also validate this
    }
  }
  
  confirming.value = true
  
  // Prepare allocation data if user allocated funds
  const allocationData = allocatedAmount.value > 0 ? {
    allocationSource: selectedAllocationSource.value,
    allocatedAmount: allocatedAmount.value,
    originalPositionValue: originalPositionValue.value,
    newPositionValue: newPositionValue.value,
    confirmReserve: selectedAllocationSource.value === 'reserve'
  } : undefined
  
  emit('confirm', allocationData)
  console.log('[DEBUG] OrderPreviewModal confirm event emitted', allocationData);
  // Reset after a delay in case of error
  setTimeout(() => {
    confirming.value = false
  }, 2000)
}

// Lifecycle hooks
onMounted(() => {
  if (props.show && !props.analysisMode) {
    fetchBudgetData()
  }
})

watch(() => props.show, (newVal) => {
  if (newVal && !props.analysisMode && !budgetData.value) {
    fetchBudgetData()
  }
})
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10000;
  padding: 20px;
}

.modal-content {
  background: var(--color-bg-card, rgba(20, 20, 30, 0.95));
  border: 1px solid var(--color-text-muted, rgba(136, 136, 136, 0.2));
  border-radius: 12px;
  max-width: 600px;
  width: 100%;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
}

.modal-content.analysis-mode {
  max-width: 1200px;
  max-height: 95vh;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid var(--color-text-muted, rgba(136, 136, 136, 0.2));
}

.modal-header h3 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: var(--color-text, #e8e8e8);
}

.close-btn {
  background: none;
  border: none;
  font-size: 28px;
  color: var(--color-text-muted, #888);
  cursor: pointer;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: all 0.2s ease;
}

.close-btn:hover {
  background: var(--color-text-muted, rgba(136, 136, 136, 0.2));
  color: var(--color-text, #e8e8e8);
}

.modal-body {
  padding: 20px;
}

.section {
  margin-bottom: 24px;
}

.section:last-child {
  margin-bottom: 0;
}

.section h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-muted, #888);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.chart-section {
  margin-bottom: 24px;
}

.chart-section h4 {
  margin-bottom: 12px;
}

.opportunity-summary,
.entry-details,
.trade-details,
.order-config {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.summary-row,
.detail-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid var(--color-text-muted, rgba(136, 136, 136, 0.1));
}

.detail-row:last-child {
  border-bottom: none;
}

.label {
  color: var(--color-text-muted, #888);
  font-size: 13px;
}

.value {
  color: var(--color-text, #e8e8e8);
  font-size: 13px;
  font-weight: 500;
  text-align: right;
}

.value.positive {
  color: var(--color-accent, #4ade80);
}

.value.negative {
  color: var(--color-danger, #f87171);
}

.value.large {
  font-size: 16px;
  font-weight: 600;
}

.value.highlight {
  color: var(--color-accent, #4ade80);
  font-weight: 600;
}

.value.buy {
  color: var(--color-accent, #4ade80);
}

.value.sell {
  color: var(--color-danger, #f87171);
}

.amount {
  font-size: 11px;
  opacity: 0.8;
  margin-left: 4px;
}

.tolerance {
  font-size: 11px;
  opacity: 0.7;
  margin-left: 4px;
}

.countdown {
  font-size: 11px;
  color: var(--color-text-muted, #888);
  margin-left: 8px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 20px;
  border-top: 1px solid var(--color-text-muted, rgba(136, 136, 136, 0.2));
}

.btn-cancel,
.btn-confirm {
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.2s ease;
}

.btn-cancel {
  background: var(--color-text-muted, rgba(136, 136, 136, 0.2));
  color: var(--color-text, #e8e8e8);
}

.btn-cancel:hover {
  opacity: 0.8;
}

.btn-confirm {
  background: var(--color-accent, #4ade80);
  color: var(--color-bg, #0a0a0a);
}

.btn-confirm:hover:not(:disabled) {
  opacity: 0.9;
}

.btn-confirm:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-close-analysis {
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.2s ease;
  background: var(--color-text-muted, rgba(136, 136, 136, 0.2));
  color: var(--color-text, #e8e8e8);
  width: 100%;
}

.btn-close-analysis:hover {
  opacity: 0.8;
}

@media (prefers-color-scheme: light) {
  .modal-content {
    background: var(--color-bg-card, rgba(255, 255, 255, 0.95));
    border-color: var(--color-text-muted, rgba(107, 114, 128, 0.2));
  }
  
  .modal-header,
  .modal-footer {
    border-color: var(--color-text-muted, rgba(107, 114, 128, 0.2));
  }
}

/* Fund Allocation Section */
.fund-allocation-section {
  border-top: 1px solid var(--color-border, rgba(136, 136, 136, 0.2));
  padding-top: 20px;
}

.fund-summary {
  margin-bottom: 20px;
  padding: 12px;
  background: var(--color-bg-secondary, rgba(255, 255, 255, 0.05));
  border-radius: 8px;
}

.total-funds {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.total-funds .label {
  font-weight: 600;
  color: var(--color-text, #e8e8e8);
}

.total-funds .value {
  font-size: 18px;
  font-weight: 700;
  color: var(--color-accent, #60a5fa);
}

.partition-manager {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
  margin-bottom: 20px;
}

.partition-item {
  padding: 12px;
  border: 2px solid var(--color-border, rgba(136, 136, 136, 0.2));
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  background: var(--color-bg-secondary, rgba(255, 255, 255, 0.03));
}

.partition-item:hover {
  border-color: var(--color-accent, #60a5fa);
  background: var(--color-bg-secondary, rgba(96, 165, 250, 0.1));
}

.partition-item.selected {
  border-color: var(--color-accent, #60a5fa);
  background: var(--color-bg-secondary, rgba(96, 165, 250, 0.15));
  box-shadow: 0 0 0 2px rgba(96, 165, 250, 0.2);
}

.partition-item.reserve {
  border-color: var(--color-warning, #fbbf24);
}

.partition-item.reserve.selected {
  border-color: var(--color-warning, #fbbf24);
  background: var(--color-bg-secondary, rgba(251, 191, 36, 0.15));
  box-shadow: 0 0 0 2px rgba(251, 191, 36, 0.2);
}

.partition-item.insufficient {
  opacity: 0.5;
  cursor: not-allowed;
}

.partition-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.partition-name {
  font-weight: 600;
  color: var(--color-text, #e8e8e8);
  font-size: 14px;
}

.partition-amount {
  font-weight: 700;
  color: var(--color-accent, #60a5fa);
  font-size: 16px;
}

.partition-bar {
  height: 8px;
  background: var(--color-bg-tertiary, rgba(0, 0, 0, 0.2));
  border-radius: 4px;
  overflow: hidden;
  margin: 8px 0;
}

.partition-fill {
  height: 100%;
  transition: width 0.3s ease;
}

.partition-fill.trading_pool {
  background: #60a5fa;
}

.partition-fill.whitelist {
  background: #4ade80;
}

.partition-fill.auto_discovery {
  background: #fbbf24;
}

.partition-fill.reserve {
  background: #a78bfa;
}

.partition-metrics {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-top: 8px;
  font-size: 11px;
  color: var(--color-text-muted, #888);
}

.partition-metrics .metric {
  display: flex;
  justify-content: space-between;
}

.allocation-controls {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.control-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.control-group label {
  font-weight: 600;
  color: var(--color-text, #e8e8e8);
  font-size: 14px;
}

.control-group select {
  padding: 8px 12px;
  border: 1px solid var(--color-border, rgba(136, 136, 136, 0.2));
  border-radius: 6px;
  background: var(--color-bg-secondary, rgba(255, 255, 255, 0.05));
  color: var(--color-text, #e8e8e8);
  font-size: 14px;
  cursor: pointer;
}

.control-group select:focus {
  outline: none;
  border-color: var(--color-accent, #60a5fa);
}

.amount-input-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.amount-input-group input {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid var(--color-border, rgba(136, 136, 136, 0.2));
  border-radius: 6px;
  background: var(--color-bg-secondary, rgba(255, 255, 255, 0.05));
  color: var(--color-text, #e8e8e8);
  font-size: 14px;
}

.amount-input-group input:focus {
  outline: none;
  border-color: var(--color-accent, #60a5fa);
}

.amount-input-group .currency {
  color: var(--color-text-muted, #888);
  font-size: 14px;
}

.preset-buttons {
  display: flex;
  gap: 8px;
  margin-top: 8px;
}

.preset-btn {
  flex: 1;
  padding: 6px 12px;
  border: 1px solid var(--color-border, rgba(136, 136, 136, 0.2));
  border-radius: 4px;
  background: var(--color-bg-secondary, rgba(255, 255, 255, 0.05));
  color: var(--color-text, #e8e8e8);
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 12px;
}

.preset-btn:hover:not(:disabled) {
  background: var(--color-accent, #60a5fa);
  border-color: var(--color-accent, #60a5fa);
  color: white;
}

.preset-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.allocation-warning {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: rgba(251, 191, 36, 0.1);
  border: 1px solid rgba(251, 191, 36, 0.3);
  border-radius: 6px;
  color: var(--color-warning, #fbbf24);
  font-size: 12px;
  margin-top: 8px;
}

.allocation-warning .warning-icon {
  font-size: 16px;
}

.allocation-error {
  padding: 8px 12px;
  background: rgba(248, 113, 113, 0.1);
  border: 1px solid rgba(248, 113, 113, 0.3);
  border-radius: 6px;
  color: var(--color-danger, #f87171);
  font-size: 12px;
  margin-top: 8px;
}

.allocation-preview {
  padding: 12px;
  background: var(--color-bg-secondary, rgba(255, 255, 255, 0.05));
  border-radius: 8px;
  margin-top: 12px;
}

.preview-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 0;
}

.preview-row .label {
  color: var(--color-text-muted, #888);
  font-size: 13px;
}

.preview-row .value {
  color: var(--color-text, #e8e8e8);
  font-size: 14px;
  font-weight: 600;
}

.preview-row .value.highlight {
  color: var(--color-accent, #60a5fa);
  font-weight: 700;
}

.preview-row .value.large {
  font-size: 16px;
  font-weight: 700;
  color: var(--color-accent, #60a5fa);
}

.budget-loading {
  padding: 20px;
  text-align: center;
  color: var(--color-text-muted, #888);
  font-size: 14px;
}
</style>

