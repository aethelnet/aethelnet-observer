<template>
  <div class="pinned-summary" :class="{ 'is-collapsed': isCollapsed }">
    <!-- Header -->
    <div class="summary-header" @click="toggleCollapse">
      <div class="header-left">
        <span class="header-icon">📌</span>
        <h3 class="header-title" :title="t('ui.summary.header')">
          {{ t('ui.pins.title') }}
          <span class="item-count" v-if="summary.totalCount > 0">
            {{ summary.totalCount }}
          </span>
        </h3>
      </div>
      
      <div class="header-actions">
        <button 
          class="action-btn" 
          @click.stop="copyToClipboard"
          :title="TOOLTIPS.summary.export"
        >
          <span class="action-icon">📋</span>
        </button>
        <button 
          class="action-btn" 
          @click.stop="refreshAll"
          :title="TOOLTIPS.summary.refresh"
        >
          <span class="action-icon" :class="{ spinning: isRefreshing }">🔄</span>
        </button>
        <button 
          class="action-btn danger" 
          @click.stop="confirmClear"
          :title="TOOLTIPS.summary.clear"
          v-if="summary.totalCount > 0"
        >
          <span class="action-icon">🗑️</span>
        </button>
        <span class="collapse-indicator">{{ isCollapsed ? '▼' : '▲' }}</span>
      </div>
    </div>
    
    <!-- Content -->
    <div class="summary-content" v-show="!isCollapsed">
      <!-- Empty State -->
      <div class="empty-state" v-if="summary.totalCount === 0">
        <span class="empty-icon">📍</span>
        <p class="empty-text">{{ t('ui.pins.empty') }}</p>
        <p class="empty-hint">{{ t('ui.pins.subtitle') }}</p>
      </div>
      
      <!-- Symbols Section -->
      <section v-if="summary.symbols.length > 0" class="item-section">
        <h4 class="section-title" :title="TOOLTIPS.itemTypes.symbol">
          <span class="section-icon">💹</span> Symbols
        </h4>
        <div class="items-grid">
          <div 
            v-for="item in summary.symbols" 
            :key="item.id"
            class="pinned-item symbol-item"
            :title="`${item.label} - ${TOOLTIPS.itemTypes.symbol}`"
          >
            <div class="item-header">
              <span class="item-label">{{ item.label }}</span>
              <button 
                class="unpin-btn" 
                @click="unpin(item.id)"
                title="Unpin this symbol"
              >×</button>
            </div>
            <div class="item-body" v-if="item.metadata">
              <div class="price-row">
                <span class="price">${{ formatPrice(item.metadata.price) }}</span>
                <span 
                  class="change" 
                  :class="getPriceChangeClass(item.metadata.priceChangePercent)"
                >
                  {{ formatChange(item.metadata.priceChangePercent) }}
                </span>
              </div>
              <div 
                class="signal-row" 
                v-if="item.metadata.signal"
                :title="TOOLTIPS.signals[item.metadata.signal]"
              >
                <span class="signal-badge" :class="getSignalClass(item.metadata.signal)">
                  {{ item.metadata.signal }}
                </span>
                <span 
                  class="confidence" 
                  v-if="item.metadata.confidence"
                  :title="TOOLTIPS.confidence(item.metadata.confidence)"
                >
                  {{ item.metadata.confidence }}%
                </span>
              </div>
            </div>
          </div>
        </div>
      </section>
      
      <!-- Clusters Section -->
      <section v-if="summary.clusters.length > 0" class="item-section">
        <h4 class="section-title" :title="TOOLTIPS.itemTypes.cluster">
          <span class="section-icon">🔗</span> Clusters
        </h4>
        <div class="items-list">
          <div 
            v-for="item in summary.clusters" 
            :key="item.id"
            class="pinned-item cluster-item"
          >
            <span class="item-label">{{ item.label }}</span>
            <span 
              class="cluster-meta" 
              v-if="item.metadata?.memberCount"
              :title="`${item.metadata.memberCount} correlated assets`"
            >
              {{ item.metadata.memberCount }} assets
            </span>
            <button class="unpin-btn" @click="unpin(item.id)" title="Unpin">×</button>
          </div>
        </div>
      </section>
      
      <!-- News Section -->
      <section v-if="summary.newsStreams.length > 0" class="item-section">
        <h4 class="section-title" :title="TOOLTIPS.itemTypes.news_stream">
          <span class="section-icon">📰</span> News
        </h4>
        <div class="items-list">
          <div 
            v-for="item in summary.newsStreams" 
            :key="item.id"
            class="pinned-item news-item"
          >
            <div class="news-content">
              <span 
                class="sentiment-dot" 
                :class="getSentimentClass(item.metadata?.sentiment)"
                :title="getSentimentLabel(item.metadata?.sentiment)"
              ></span>
              <span class="item-label">{{ item.label }}</span>
            </div>
            <button class="unpin-btn" @click="unpin(item.id)" title="Unpin">×</button>
          </div>
        </div>
      </section>
      
      <!-- Opportunities Section -->
      <section v-if="summary.opportunities.length > 0" class="item-section">
        <h4 class="section-title" :title="TOOLTIPS.itemTypes.opportunity">
          <span class="section-icon">🎯</span> Opportunities
        </h4>
        <div class="items-list">
          <div 
            v-for="item in summary.opportunities" 
            :key="item.id"
            class="pinned-item opportunity-item"
            :title="item.metadata?.riskLevel ? TOOLTIPS.riskLevel[item.metadata.riskLevel] : ''"
          >
            <span class="item-label">{{ item.label }}</span>
            <span 
              class="risk-badge" 
              :class="getRiskClass(item.metadata?.riskLevel)"
              v-if="item.metadata?.riskLevel"
            >
              {{ item.metadata.riskLevel }}
            </span>
            <span 
              class="potential-gain" 
              v-if="item.metadata?.potentialGain"
            >
              +{{ item.metadata.potentialGain }}%
            </span>
            <button class="unpin-btn" @click="unpin(item.id)" title="Unpin">×</button>
          </div>
        </div>
      </section>
      
      <!-- Calendar Events Section -->
      <section v-if="summary.calendarEvents.length > 0" class="item-section">
        <h4 class="section-title" :title="TOOLTIPS.itemTypes.calendar_event">
          <span class="section-icon">📅</span> Upcoming Events
        </h4>
        <div class="items-list">
          <div 
            v-for="item in summary.calendarEvents" 
            :key="item.id"
            class="pinned-item event-item"
          >
            <span class="event-countdown" v-if="item.metadata?.eventTime">
              {{ formatCountdown(item.metadata.eventTime) }}
            </span>
            <span class="item-label">{{ item.label }}</span>
            <button class="unpin-btn" @click="unpin(item.id)" title="Unpin">×</button>
          </div>
        </div>
      </section>
      
      <!-- Last Updated -->
      <div class="last-updated" v-if="summary.totalCount > 0">
        {{ t('ui.summary.updated', { time: formatRelativeTime(summary.lastUpdated) }) }}
      </div>
    </div>
    
    <!-- Copy Toast -->
    <Transition name="toast">
      <div class="copy-toast" v-if="showCopyToast">
        {{ t('ui.summary.copied') }}
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { usePinnedItems, TOOLTIPS } from '../composables/usePinnedItems';
import { formatForTelegram } from '../utils/telegramFormatter';
import { useI18n } from '../composables/useI18n';

// ─────────────────────────────────────────────────────────────────────────────
// Props & Emits
// ─────────────────────────────────────────────────────────────────────────────

const props = withDefaults(defineProps<{
  initialCollapsed?: boolean;
}>(), {
  initialCollapsed: false,
});

const emit = defineEmits<{
  (e: 'cleared'): void;
  (e: 'copied', text: string): void;
}>();

// ─────────────────────────────────────────────────────────────────────────────
// State
// ─────────────────────────────────────────────────────────────────────────────

const { aggregatedSummary: summary, unpin, clearAll } = usePinnedItems();
const { t } = useI18n();

const isCollapsed = ref(props.initialCollapsed);
const isRefreshing = ref(false);
const showCopyToast = ref(false);

let countdownInterval: ReturnType<typeof setInterval> | null = null;

// ─────────────────────────────────────────────────────────────────────────────
// Lifecycle
// ─────────────────────────────────────────────────────────────────────────────

onMounted(() => {
  // Update countdowns every second
  countdownInterval = setInterval(() => {
    // Force re-render for countdown updates
  }, 1000);
});

onUnmounted(() => {
  if (countdownInterval) clearInterval(countdownInterval);
});

// ─────────────────────────────────────────────────────────────────────────────
// Methods
// ─────────────────────────────────────────────────────────────────────────────

function toggleCollapse() {
  isCollapsed.value = !isCollapsed.value;
}

async function copyToClipboard() {
  const text = formatForTelegram(summary.value);
  try {
    await navigator.clipboard.writeText(text);
    showCopyToast.value = true;
    setTimeout(() => { showCopyToast.value = false; }, 2000);
    emit('copied', text);
  } catch (e) {
    console.error('Failed to copy:', e);
  }
}

function refreshAll() {
  isRefreshing.value = true;
  // Emit event for parent to handle refresh
  setTimeout(() => { isRefreshing.value = false; }, 1000);
}

function confirmClear() {
  if (confirm('Remove all pinned items?')) {
    clearAll();
    emit('cleared');
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Formatters
// ─────────────────────────────────────────────────────────────────────────────

function formatPrice(price?: number): string {
  if (!price) return '—';
  if (price >= 1000) return price.toLocaleString('en-US', { maximumFractionDigits: 0 });
  if (price >= 1) return price.toFixed(2);
  return price.toPrecision(4);
}

function formatChange(percent?: number): string {
  if (percent === undefined) return '';
  const sign = percent >= 0 ? '+' : '';
  return `${sign}${percent.toFixed(2)}%`;
}

function formatCountdown(timestamp: number): string {
  const diff = timestamp - Date.now();
  if (diff <= 0) return 'NOW';
  
  const hours = Math.floor(diff / 3600000);
  const mins = Math.floor((diff % 3600000) / 60000);
  
  if (hours > 24) return `${Math.floor(hours / 24)}d`;
  if (hours > 0) return `${hours}h ${mins}m`;
  return `${mins}m`;
}

function formatRelativeTime(timestamp: number): string {
  const diff = Date.now() - timestamp;
  if (diff < 1000) return t('ui.time.now');
  if (diff < 60000) return t('ui.time.sec', { count: Math.floor(diff / 1000) });
  return t('ui.time.min', { count: Math.floor(diff / 60000) });
}

// ─────────────────────────────────────────────────────────────────────────────
// Class Helpers
// ─────────────────────────────────────────────────────────────────────────────

function getPriceChangeClass(percent?: number): string {
  if (!percent) return '';
  return percent >= 0 ? 'positive' : 'negative';
}

function getSignalClass(signal?: string): string {
  if (!signal) return '';
  return signal.toLowerCase();
}

function getSentimentClass(sentiment?: string): string {
  return sentiment || 'neutral';
}

function getSentimentLabel(sentiment?: string): string {
  switch (sentiment) {
    case 'bullish': return 'Bullish sentiment detected';
    case 'bearish': return 'Bearish sentiment detected';
    default: return 'Neutral sentiment';
  }
}

function getRiskClass(risk?: string): string {
  return risk || 'medium';
}
</script>

<style scoped>
.pinned-summary {
  background: var(--color-bg-card, #1a1a2e);
  border: 1px solid var(--color-border, #2a2a4a);
  border-radius: 12px;
  overflow: hidden;
  transition: all 0.3s ease;
}

.pinned-summary.is-collapsed {
  border-radius: 8px;
}

/* Header */
.summary-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: var(--color-bg-elevated, #252540);
  cursor: pointer;
  user-select: none;
}

.summary-header:hover {
  background: var(--color-bg-hover, #2a2a50);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-icon {
  font-size: 1.25rem;
}

.header-title {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
  color: var(--color-text, #fff);
  display: flex;
  align-items: center;
  gap: 8px;
}

.item-count {
  background: var(--color-accent, #10b981);
  color: #000;
  font-size: 0.75rem;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 10px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.action-btn {
  background: none;
  border: none;
  padding: 6px;
  cursor: pointer;
  border-radius: 6px;
  transition: all 0.2s;
}

.action-btn:hover {
  background: rgba(255, 255, 255, 0.1);
}

.action-btn.danger:hover {
  background: rgba(248, 113, 113, 0.2);
}

.action-icon {
  font-size: 1rem;
  display: inline-block;
}

.action-icon.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.collapse-indicator {
  color: var(--color-text-muted, #888);
  font-size: 0.75rem;
  margin-left: 4px;
}

/* Content */
.summary-content {
  padding: 16px;
  max-height: 60vh;
  overflow-y: auto;
}

/* Empty State */
.empty-state {
  text-align: center;
  padding: 32px 16px;
  color: var(--color-text-muted, #888);
}

.empty-icon {
  font-size: 2.5rem;
  opacity: 0.5;
}

.empty-text {
  margin: 12px 0 4px;
  font-weight: 500;
  color: var(--color-text, #fff);
}

.empty-hint {
  font-size: 0.85rem;
  opacity: 0.7;
}

/* Sections */
.item-section {
  margin-bottom: 20px;
}

.item-section:last-child {
  margin-bottom: 0;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 12px;
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--color-text-muted, #aaa);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.section-icon {
  font-size: 1rem;
}

/* Items Grid (for Symbols) */
.items-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 12px;
}

/* Items List */
.items-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

/* Pinned Item Base */
.pinned-item {
  background: var(--color-bg, #0f0f1a);
  border: 1px solid var(--color-border, #2a2a4a);
  border-radius: 8px;
  padding: 10px 12px;
  transition: all 0.2s;
  position: relative;
}

.pinned-item:hover {
  border-color: var(--color-accent, #10b981);
}

.item-label {
  font-weight: 500;
  color: var(--color-text, #fff);
  font-size: 0.9rem;
}

.unpin-btn {
  position: absolute;
  top: 4px;
  right: 4px;
  background: none;
  border: none;
  color: var(--color-text-muted, #666);
  font-size: 1.1rem;
  cursor: pointer;
  padding: 2px 6px;
  border-radius: 4px;
  opacity: 0;
  transition: all 0.2s;
}

.pinned-item:hover .unpin-btn {
  opacity: 1;
}

.unpin-btn:hover {
  background: rgba(248, 113, 113, 0.2);
  color: var(--color-danger, #f87171);
}

/* Symbol Item */
.symbol-item .item-header {
  margin-bottom: 8px;
}

.price-row {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 6px;
}

.price {
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--color-text, #fff);
}

.change {
  font-size: 0.85rem;
  font-weight: 500;
}

.change.positive { color: var(--color-success, #10b981); }
.change.negative { color: var(--color-danger, #f87171); }

.signal-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.signal-badge {
  font-size: 0.7rem;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 4px;
  text-transform: uppercase;
}

.signal-badge.buy { 
  background: rgba(16, 185, 129, 0.2); 
  color: var(--color-success, #10b981); 
}
.signal-badge.sell { 
  background: rgba(248, 113, 113, 0.2); 
  color: var(--color-danger, #f87171); 
}
.signal-badge.hold { 
  background: rgba(251, 191, 36, 0.2); 
  color: var(--color-warning, #fbbf24); 
}
.signal-badge.wait { 
  background: rgba(148, 163, 184, 0.2); 
  color: var(--color-text-muted, #94a3b8); 
}

.confidence {
  font-size: 0.75rem;
  color: var(--color-text-muted, #888);
}

/* Cluster Item */
.cluster-item {
  display: flex;
  align-items: center;
  gap: 10px;
}

.cluster-meta {
  font-size: 0.75rem;
  color: var(--color-text-muted, #888);
  margin-left: auto;
  margin-right: 24px;
}

/* News Item */
.news-item {
  display: flex;
  align-items: center;
}

.news-content {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
}

.sentiment-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.sentiment-dot.bullish { background: var(--color-success, #10b981); }
.sentiment-dot.bearish { background: var(--color-danger, #f87171); }
.sentiment-dot.neutral { background: var(--color-text-muted, #888); }

/* Opportunity Item */
.opportunity-item {
  display: flex;
  align-items: center;
  gap: 10px;
}

.risk-badge {
  font-size: 0.65rem;
  font-weight: 600;
  padding: 2px 6px;
  border-radius: 4px;
  text-transform: uppercase;
}

.risk-badge.low { background: rgba(16, 185, 129, 0.2); color: #10b981; }
.risk-badge.medium { background: rgba(251, 191, 36, 0.2); color: #fbbf24; }
.risk-badge.high { background: rgba(248, 113, 113, 0.2); color: #f87171; }

.potential-gain {
  color: var(--color-success, #10b981);
  font-weight: 600;
  font-size: 0.85rem;
  margin-left: auto;
  margin-right: 24px;
}

/* Event Item */
.event-item {
  display: flex;
  align-items: center;
  gap: 10px;
}

.event-countdown {
  background: var(--color-accent-dark, rgba(16, 185, 129, 0.1));
  color: var(--color-accent, #10b981);
  font-size: 0.75rem;
  font-weight: 600;
  padding: 4px 8px;
  border-radius: 4px;
  min-width: 50px;
  text-align: center;
}

/* Last Updated */
.last-updated {
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px solid var(--color-border, #2a2a4a);
  font-size: 0.75rem;
  color: var(--color-text-muted, #666);
  text-align: center;
}

/* Copy Toast */
.copy-toast {
  position: absolute;
  bottom: 16px;
  left: 50%;
  transform: translateX(-50%);
  background: var(--color-success, #10b981);
  color: #000;
  padding: 8px 16px;
  border-radius: 6px;
  font-size: 0.85rem;
  font-weight: 500;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(10px);
}
</style>
