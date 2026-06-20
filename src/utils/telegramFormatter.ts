/**
 * telegramFormatter.ts
 * Formats aggregated pinned items into Telegram-friendly text messages.
 * Designed for bot integration with clean, readable output.
 */

import type { AggregatedSummary, PinnedItem } from '../composables/usePinnedItems';

// ─────────────────────────────────────────────────────────────────────────────
// Constants
// ─────────────────────────────────────────────────────────────────────────────

const DIVIDER = '━━━━━━━━━━━━━━━━━━━━';
const DIVIDER_LIGHT = '──────────────────';

const SIGNAL_EMOJI: Record<string, string> = {
    BUY: '🟢',
    SELL: '🔴',
    HOLD: '🟡',
    WAIT: '⚪',
};

const SENTIMENT_EMOJI: Record<string, string> = {
    bullish: '📈',
    bearish: '📉',
    neutral: '➖',
};

const RISK_EMOJI: Record<string, string> = {
    low: '🟢',
    medium: '🟡',
    high: '🔴',
};

// ─────────────────────────────────────────────────────────────────────────────
// Main Formatter
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Formats the aggregated summary into a Telegram-friendly message.
 * Keeps output concise but informative.
 */
export function formatForTelegram(summary: AggregatedSummary): string {
    const lines: string[] = [];

    // Header
    lines.push('📊 *AURATIC SUMMARY*');
    lines.push(DIVIDER);

    if (summary.totalCount === 0) {
        lines.push('');
        lines.push('_No pinned items_');
        lines.push('');
        lines.push(DIVIDER);
        return lines.join('\n');
    }

    // Symbols
    if (summary.symbols.length > 0) {
        lines.push('');
        lines.push('*📌 SYMBOLS*');
        for (const item of summary.symbols) {
            lines.push(formatSymbol(item));
        }
    }

    // Clusters
    if (summary.clusters.length > 0) {
        lines.push('');
        lines.push('*🔗 CLUSTERS*');
        for (const item of summary.clusters) {
            lines.push(formatCluster(item));
        }
    }

    // News
    if (summary.newsStreams.length > 0) {
        lines.push('');
        lines.push('*📰 NEWS*');
        for (const item of summary.newsStreams) {
            lines.push(formatNews(item));
        }
    }

    // Opportunities
    if (summary.opportunities.length > 0) {
        lines.push('');
        lines.push('*🎯 OPPORTUNITIES*');
        for (const item of summary.opportunities) {
            lines.push(formatOpportunity(item));
        }
    }

    // Calendar Events
    if (summary.calendarEvents.length > 0) {
        lines.push('');
        lines.push('*📅 UPCOMING*');
        for (const item of summary.calendarEvents) {
            lines.push(formatCalendarEvent(item));
        }
    }

    // Footer
    lines.push('');
    lines.push(DIVIDER);
    lines.push(`_Updated: ${formatTimestamp(summary.lastUpdated)}_`);

    return lines.join('\n');
}

// ─────────────────────────────────────────────────────────────────────────────
// Item Formatters
// ─────────────────────────────────────────────────────────────────────────────

function formatSymbol(item: PinnedItem): string {
    const meta = item.metadata || {};
    const price = meta.price ? `$${formatPrice(meta.price)}` : '—';
    const change = meta.priceChangePercent !== undefined
        ? `(${meta.priceChangePercent >= 0 ? '+' : ''}${meta.priceChangePercent.toFixed(1)}%)`
        : '';

    let line = `  ${item.label}: ${price} ${change}`;

    if (meta.signal) {
        const emoji = SIGNAL_EMOJI[meta.signal] || '⚪';
        const conf = meta.confidence ? ` ${meta.confidence}%` : '';
        line += `\n     ${emoji} ${meta.signal}${conf}`;
    }

    return line;
}

function formatCluster(item: PinnedItem): string {
    const meta = item.metadata || {};
    const count = meta.memberCount ? `(${meta.memberCount} assets)` : '';
    const avgChange = meta.avgChange !== undefined
        ? ` ${meta.avgChange >= 0 ? '↑' : '↓'}${Math.abs(meta.avgChange).toFixed(1)}%`
        : '';

    return `  ${item.label} ${count}${avgChange}`;
}

function formatNews(item: PinnedItem): string {
    const meta = item.metadata || {};
    const emoji = SENTIMENT_EMOJI[meta.sentiment || 'neutral'];

    // Truncate headline if too long
    let label = item.label;
    if (label.length > 50) {
        label = label.substring(0, 47) + '...';
    }

    return `  ${emoji} ${label}`;
}

function formatOpportunity(item: PinnedItem): string {
    const meta = item.metadata || {};
    const risk = meta.riskLevel ? RISK_EMOJI[meta.riskLevel] : '';
    const gain = meta.potentialGain ? `+${meta.potentialGain}%` : '';

    return `  ${risk} ${item.label} ${gain}`;
}

function formatCalendarEvent(item: PinnedItem): string {
    const meta = item.metadata || {};
    const countdown = meta.eventTime
        ? `⏰ ${formatCountdown(meta.eventTime)}`
        : '';

    return `  ${countdown} ${item.label}`;
}

// ─────────────────────────────────────────────────────────────────────────────
// Utility Formatters
// ─────────────────────────────────────────────────────────────────────────────

function formatPrice(price: number): string {
    if (price >= 10000) return price.toLocaleString('en-US', { maximumFractionDigits: 0 });
    if (price >= 1) return price.toFixed(2);
    return price.toPrecision(4);
}

function formatCountdown(timestamp: number): string {
    const diff = timestamp - Date.now();
    if (diff <= 0) return 'NOW!';

    const hours = Math.floor(diff / 3600000);
    const mins = Math.floor((diff % 3600000) / 60000);

    if (hours >= 24) return `${Math.floor(hours / 24)}d ${hours % 24}h`;
    if (hours > 0) return `${hours}h ${mins}m`;
    return `${mins}m`;
}

function formatTimestamp(ts: number): string {
    return new Date(ts).toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        hour12: false,
    });
}

// ─────────────────────────────────────────────────────────────────────────────
// Compact Format (for inline bot responses)
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Creates a super-compact one-liner summary.
 * Useful for inline bot queries or quick status checks.
 */
export function formatCompact(summary: AggregatedSummary): string {
    if (summary.totalCount === 0) return '📊 No pinned items';

    const parts: string[] = [];

    if (summary.symbols.length > 0) {
        const symbolSummary = summary.symbols
            .slice(0, 3)
            .map(s => {
                const change = s.metadata?.priceChangePercent;
                const arrow = change !== undefined ? (change >= 0 ? '↑' : '↓') : '';
                return `${s.label}${arrow}`;
            })
            .join(', ');
        parts.push(`📌 ${symbolSummary}`);
    }

    if (summary.calendarEvents.length > 0) {
        const next = summary.calendarEvents[0];
        parts.push(`📅 ${next.label}`);
    }

    if (summary.opportunities.length > 0) {
        parts.push(`🎯 ${summary.opportunities.length} opp`);
    }

    return parts.join(' | ');
}

// ─────────────────────────────────────────────────────────────────────────────
// Action Recommendations
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Generates a brief action recommendation based on pinned items.
 * For Telegram bot "what should I do?" queries.
 */
export function formatRecommendation(summary: AggregatedSummary): string {
    const lines: string[] = ['🤖 *RECOMMENDATION*', ''];

    // Check for strong signals
    const buySignals = summary.symbols.filter(
        s => s.metadata?.signal === 'BUY' && (s.metadata?.confidence || 0) >= 70
    );
    const sellSignals = summary.symbols.filter(
        s => s.metadata?.signal === 'SELL' && (s.metadata?.confidence || 0) >= 70
    );

    if (buySignals.length > 0) {
        lines.push(`🟢 *Strong BUY on:* ${buySignals.map(s => s.label).join(', ')}`);
    }

    if (sellSignals.length > 0) {
        lines.push(`🔴 *Strong SELL on:* ${sellSignals.map(s => s.label).join(', ')}`);
    }

    // Check for upcoming events
    const soonEvents = summary.calendarEvents.filter(e => {
        const diff = (e.metadata?.eventTime || 0) - Date.now();
        return diff > 0 && diff < 3600000; // Within 1 hour
    });

    if (soonEvents.length > 0) {
        lines.push(`⚠️ *Volatility warning:* ${soonEvents[0].label} in ${formatCountdown(soonEvents[0].metadata!.eventTime!)}`);
    }

    // Default recommendation
    if (lines.length === 2) {
        lines.push('⏳ *Status:* WAIT');
        lines.push('_No strong signals detected. Patience recommended._');
    }

    return lines.join('\n');
}

// Default export
export default formatForTelegram;
