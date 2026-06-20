/**
 * usePinnedItems.ts
 * Core state management for pinned items across the Auratic dashboard.
 * Handles symbols, clusters, news streams, opportunities, and calendar events.
 */

import { ref, computed, watch } from 'vue';

// ─────────────────────────────────────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────────────────────────────────────

export type PinnedItemType = 'symbol' | 'cluster' | 'news_stream' | 'opportunity' | 'calendar_event';

export interface PinnedItem {
    id: string;
    type: PinnedItemType;
    label: string;
    pinnedAt: number;
    metadata?: {
        // Symbol-specific
        price?: number;
        priceChange?: number;
        priceChangePercent?: number;
        signal?: 'BUY' | 'SELL' | 'HOLD' | 'WAIT';
        confidence?: number;
        // News-specific
        headline?: string;
        sentiment?: 'bullish' | 'bearish' | 'neutral';
        // Calendar-specific
        eventTime?: number;
        eventType?: string;
        // Opportunity-specific
        potentialGain?: number;
        riskLevel?: 'low' | 'medium' | 'high';
        // Cluster-specific
        memberCount?: number;
        avgChange?: number;
    };
}

export interface AggregatedSummary {
    symbols: PinnedItem[];
    clusters: PinnedItem[];
    newsStreams: PinnedItem[];
    opportunities: PinnedItem[];
    calendarEvents: PinnedItem[];
    totalCount: number;
    lastUpdated: number;
}

// ─────────────────────────────────────────────────────────────────────────────
// Tooltip Descriptions (for UI)
// ─────────────────────────────────────────────────────────────────────────────

export const TOOLTIPS = {
    pinButton: {
        pinned: 'Click to unpin this item from your watchlist',
        unpinned: 'Click to pin this item to your watchlist for quick access',
    },
    itemTypes: {
        symbol: 'Trading pair with live price and signal data',
        cluster: 'Group of correlated assets moving together',
        news_stream: 'Live news feed filtered by keywords or assets',
        opportunity: 'Detected trading opportunity based on market conditions',
        calendar_event: 'Upcoming market event that may cause volatility',
    },
    signals: {
        BUY: 'System suggests entering a long position',
        SELL: 'System suggests exiting or shorting',
        HOLD: 'Maintain current position, no action needed',
        WAIT: 'Conditions unclear, patience recommended',
    },
    confidence: (value: number) =>
        value >= 80 ? 'High confidence signal - strong alignment across indicators' :
            value >= 60 ? 'Moderate confidence - some indicators aligned' :
                'Low confidence - mixed signals, proceed with caution',
    riskLevel: {
        low: 'Low risk opportunity with conservative potential',
        medium: 'Moderate risk/reward balance',
        high: 'High risk opportunity - manage position size carefully',
    },
    summary: {
        header: 'Your pinned items aggregated in one view. Updates in real-time.',
        export: 'Copy this summary in Telegram-friendly format',
        clear: 'Remove all pinned items',
        refresh: 'Force refresh all pinned item data',
    },
} as const;

// ─────────────────────────────────────────────────────────────────────────────
// State (Singleton)
// ─────────────────────────────────────────────────────────────────────────────

const STORAGE_KEY = 'auratic_pinned_items';

const pinnedItems = ref<Map<string, PinnedItem>>(new Map());
const isInitialized = ref(false);

// ─────────────────────────────────────────────────────────────────────────────
// Persistence
// ─────────────────────────────────────────────────────────────────────────────

function loadFromStorage(): void {
    try {
        const stored = localStorage.getItem(STORAGE_KEY);
        if (stored) {
            const parsed = JSON.parse(stored);
            pinnedItems.value = new Map(parsed);
        }
    } catch (e) {
        console.warn('[PinnedItems] Failed to load from storage:', e);
    }
    isInitialized.value = true;
}

function saveToStorage(): void {
    try {
        const serialized = JSON.stringify(Array.from(pinnedItems.value.entries()));
        localStorage.setItem(STORAGE_KEY, serialized);
    } catch (e) {
        console.warn('[PinnedItems] Failed to save to storage:', e);
    }
}

// Auto-save on changes
watch(pinnedItems, saveToStorage, { deep: true });

// ─────────────────────────────────────────────────────────────────────────────
// Composable
// ─────────────────────────────────────────────────────────────────────────────

export function usePinnedItems() {
    // Initialize on first use
    if (!isInitialized.value) {
        loadFromStorage();
    }

    // ─────────────────────────────────────────────────────────────────────────
    // Computed
    // ─────────────────────────────────────────────────────────────────────────

    const pinnedCount = computed(() => pinnedItems.value.size);

    const pinnedList = computed(() =>
        Array.from(pinnedItems.value.values())
            .sort((a, b) => b.pinnedAt - a.pinnedAt)
    );

    const aggregatedSummary = computed<AggregatedSummary>(() => {
        const items = pinnedList.value;
        return {
            symbols: items.filter(i => i.type === 'symbol'),
            clusters: items.filter(i => i.type === 'cluster'),
            newsStreams: items.filter(i => i.type === 'news_stream'),
            opportunities: items.filter(i => i.type === 'opportunity'),
            calendarEvents: items.filter(i => i.type === 'calendar_event'),
            totalCount: items.length,
            lastUpdated: Date.now(),
        };
    });

    // ─────────────────────────────────────────────────────────────────────────
    // Actions
    // ─────────────────────────────────────────────────────────────────────────

    function pin(item: Omit<PinnedItem, 'pinnedAt'>): void {
        const fullItem: PinnedItem = {
            ...item,
            pinnedAt: Date.now(),
        };
        pinnedItems.value.set(item.id, fullItem);
        // Trigger reactivity
        pinnedItems.value = new Map(pinnedItems.value);
    }

    function unpin(id: string): void {
        pinnedItems.value.delete(id);
        pinnedItems.value = new Map(pinnedItems.value);
    }

    function toggle(item: Omit<PinnedItem, 'pinnedAt'>): boolean {
        if (isPinned(item.id)) {
            unpin(item.id);
            return false;
        } else {
            pin(item);
            return true;
        }
    }

    function isPinned(id: string): boolean {
        return pinnedItems.value.has(id);
    }

    function getItem(id: string): PinnedItem | undefined {
        return pinnedItems.value.get(id);
    }

    function updateMetadata(id: string, metadata: Partial<PinnedItem['metadata']>): void {
        const item = pinnedItems.value.get(id);
        if (item) {
            item.metadata = { ...item.metadata, ...metadata };
            pinnedItems.value = new Map(pinnedItems.value);
        }
    }

    function clearAll(): void {
        pinnedItems.value.clear();
        pinnedItems.value = new Map();
    }

    function getPinnedByType(type: PinnedItemType): PinnedItem[] {
        return pinnedList.value.filter(item => item.type === type);
    }

    // ─────────────────────────────────────────────────────────────────────────
    // Return
    // ─────────────────────────────────────────────────────────────────────────

    return {
        // State
        pinnedItems,
        pinnedCount,
        pinnedList,
        aggregatedSummary,

        // Actions
        pin,
        unpin,
        toggle,
        isPinned,
        getItem,
        updateMetadata,
        clearAll,
        getPinnedByType,

        // Constants
        TOOLTIPS,
    };
}

// Default export for convenience
export default usePinnedItems;
