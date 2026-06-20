<template>
  <button @click="showHelp = true" class="help-btn" :title="title" :key="`help-btn-${props.viewName}`">
    <span>ℹ️</span> Help
  </button>
  
  <!-- Help Modal -->
  <div v-if="showHelp" class="help-modal-overlay" @click="showHelp = false">
    <div class="help-modal" @click.stop :key="`help-modal-${props.viewName}`">
      <div class="help-modal-header">
        <div>
          <h2>{{ modalTitle }}</h2>
          <div style="font-size: 11px; color: var(--color-text-muted, #888); margin-top: 4px;">
            View: {{ props.viewName }} | Sections: {{ helpContent.length }}
          </div>
        </div>
        <button @click="showHelp = false" class="help-modal-close">×</button>
      </div>
      <div class="help-modal-content" :key="`help-content-${props.viewName}`">
        <div v-for="(section, index) in helpContent" :key="index" class="help-section">
          <h3>{{ section.title }}</h3>
          <dl>
            <template v-for="(item, itemIndex) in section.items" :key="itemIndex">
              <dt><strong>{{ item.term }}</strong></dt>
              <dd v-html="item.definition"></dd>
            </template>
          </dl>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

interface HelpItem {
  term: string
  definition: string
}

interface HelpSection {
  title: string
  items: HelpItem[]
}

interface Props {
  viewName: string
  title?: string
}

const props = defineProps<Props>()

const showHelp = ref(false)

// Ensure title has a default
const title = computed(() => props.title || 'Help & Information')


const modalTitle = computed(() => {
  const titles: Record<string, string> = {
    'status': 'Status View Help',
    'opportunities': 'Opportunities View Help',
    'auto-discovery': 'Discovery View Help',
    'chart': 'Chart View Help',
    'execution': 'Execution View Help'
  }
  return titles[props.viewName] || 'Help & Information'
})

const helpContent = computed<HelpSection[]>(() => {
  // Ensure we're using the correct viewName
  const currentViewName = props.viewName
  
  const content: Record<string, HelpSection[]> = {
    'status': [
      {
        title: 'System Status',
        items: [
          {
            term: 'Backend Connection',
            definition: 'Shows whether the trading backend is connected and running. Green indicates active connection.'
          },
          {
            term: 'Execution Enabled',
            definition: 'Indicates if automatic trade execution is enabled. When disabled, the system will only analyze but not place trades.'
          },
          {
            term: 'Testnet Mode',
            definition: 'When enabled, all trades are executed on testnet (fake money) for safe testing.'
          },
          {
            term: 'Panic Mode',
            definition: 'Emergency stop that immediately halts all trading activity. Use this if you need to stop trading urgently.'
          }
        ]
      },
      {
        title: 'Trading Metrics',
        items: [
          {
            term: 'Total P&L',
            definition: 'Your total profit and loss across all trades. Positive values are in green, negative in red.'
          },
          {
            term: 'Win Rate',
            definition: 'Percentage of profitable trades out of all completed trades.'
          },
          {
            term: 'Open Positions',
            definition: 'Number of currently active trading positions.'
          },
          {
            term: 'Total Trades',
            definition: 'Total number of trades executed since the system started.'
          }
        ]
      },
      {
        title: 'Actions',
        items: [
          {
            term: 'Activate Panic',
            definition: 'Immediately stops all trading activity. Use in emergency situations.'
          },
          {
            term: 'Resume Trading',
            definition: 'Resumes trading after panic mode has been activated.'
          },
          {
            term: 'Reallocate to Autopilot',
            definition: 'Automatically distributes funds across different trading pools based on system recommendations.'
          }
        ]
      }
    ],
    'opportunities': [
      {
        title: 'Trading Opportunities',
        items: [
          {
            term: 'Opportunity',
            definition: 'A potential trade identified by the system based on market analysis and strategy signals.'
          },
          {
            term: 'Signal Strength',
            definition: 'A measure of how strong the trading signal is. Higher values indicate stronger confidence in the opportunity.'
          },
          {
            term: 'Entry Price Range',
            definition: 'The price range where you should enter the position. Orders placed within this range will be executed.'
          },
          {
            term: 'Target Price',
            definition: 'The expected profit target. When price reaches this level, consider taking profits.'
          },
          {
            term: 'Stop Loss',
            definition: 'The maximum loss you\'re willing to accept. If price falls to this level, the position should be closed.'
          },
          {
            term: 'Time Remaining',
            definition: 'How much time is left before the opportunity expires. After expiry, the opportunity is no longer valid.'
          }
        ]
      },
      {
        title: 'Actions',
        items: [
          {
            term: 'Place Order',
            definition: 'Manually place a trade order for this opportunity. You can specify the allocation amount.'
          },
          {
            term: 'Order Status',
            definition: 'View detailed information about a placed order, including its current status and execution details.'
          },
          {
            term: 'Auto-Execute',
            definition: 'When enabled, orders are automatically placed when entry conditions are met, without manual confirmation.'
          }
        ]
      },
      {
        title: 'Allocation',
        items: [
          {
            term: 'Trading Pool',
            definition: 'Funds available for manual trading opportunities.'
          },
          {
            term: 'Reserve',
            definition: 'Emergency reserve funds kept aside.'
          },
          {
            term: 'Whitelist',
            definition: 'Funds allocated to whitelisted symbols for automatic trading.'
          },
          {
            term: 'Auto-Discovery',
            definition: 'Funds allocated to automatically discovered trading opportunities.'
          }
        ]
      }
    ],
    'auto-discovery': [
      {
        title: 'Discovery System',
        items: [
          {
            term: 'Discovered Symbols',
            definition: 'Trading symbols that the system has identified as having potential trading opportunities based on market analysis.'
          },
          {
            term: 'Whitelisted Symbols',
            definition: 'Symbols that have been promoted and are now eligible for automatic trading. These symbols receive dedicated budget allocation.'
          },
          {
            term: 'Signal Strength',
            definition: 'A measure of how strong the trading signal is for a symbol. Higher absolute values indicate stronger signals (positive for bullish, negative for bearish).'
          },
          {
            term: 'Strategy Fit Score',
            definition: 'How well the symbol matches your trading strategy. Higher scores indicate better alignment.'
          },
          {
            term: 'Pending Discovery',
            definition: 'Symbols that appear in opportunities but haven\'t been fully discovered yet. They cannot be promoted until discovery completes.'
          }
        ]
      },
      {
        title: 'Actions',
        items: [
          {
            term: 'Promote',
            definition: 'Add a discovered symbol to the whitelist, making it eligible for automatic trading with dedicated budget allocation.'
          },
          {
            term: 'Remove',
            definition: 'Remove a symbol from the discovery list. This does not affect whitelisted symbols.'
          }
        ]
      },
      {
        title: 'Filters',
        items: [
          {
            term: 'All',
            definition: 'Show all symbols (whitelisted, discovered, and pending).'
          },
          {
            term: 'Whitelisted',
            definition: 'Show only symbols that are currently whitelisted for automatic trading.'
          },
          {
            term: 'Discovered',
            definition: 'Show only symbols that have been discovered but not yet whitelisted.'
          }
        ]
      }
    ],
    'chart': [
      {
        title: 'Price Levels',
        items: [
          {
            term: 'Current Price',
            definition: 'The most recent market price for this symbol, shown as a green dashed line with a circle marker.'
          },
          {
            term: 'Entry Min / Entry Max',
            definition: 'The price range where you can enter a position. Shown as green dashed lines. Orders placed within this range will be executed.'
          },
          {
            term: 'Target',
            definition: 'The profit target price for a position. When the price reaches this level, you may want to take profits. Shown as a solid green line.'
          },
          {
            term: 'Stop Loss',
            definition: 'The maximum loss you\'re willing to accept. If price falls to this level, the position should be closed to limit losses. Shown as a solid red line.'
          }
        ]
      },
      {
        title: 'Historical Levels',
        items: [
          {
            term: '24h High / 24h Low',
            definition: 'The highest and lowest prices reached in the last 24 hours. Useful for understanding recent price range.'
          },
          {
            term: 'Support',
            definition: 'A price level (typically 5% below current) where buying pressure may increase, potentially preventing further price decline. Shown as a green dashed line.'
          },
          {
            term: 'Resistance',
            definition: 'A price level (typically 5% above current) where selling pressure may increase, potentially preventing further price rise. Shown as a green dashed line.'
          }
        ]
      },
      {
        title: 'Moving Averages (MA)',
        items: [
          {
            term: 'MA20',
            definition: '20-period Moving Average - The average price over the last 20 candles. A short-term trend indicator. Price above MA20 suggests bullish momentum.'
          },
          {
            term: 'MA50',
            definition: '50-period Moving Average - The average price over the last 50 candles. A medium-term trend indicator. Often used to confirm trend direction.'
          },
          {
            term: 'MA200',
            definition: '200-period Moving Average - The average price over the last 200 candles. A long-term trend indicator. Price above MA200 is often considered a bullish signal.'
          }
        ]
      },
      {
        title: 'Technical Indicators',
        items: [
          {
            term: 'MA (Moving Average / SMA)',
            definition: 'Simple Moving Average - the average price over a specified period. Available periods: 10, 20, 50, 100, 200. Helps identify trends and support/resistance levels. Price above MA suggests uptrend, below suggests downtrend.'
          },
          {
            term: 'EMA (Exponential Moving Average)',
            definition: 'Exponential Moving Average - gives more weight to recent prices, making it more responsive than SMA. Shown as dashed lines. Useful for short-term trend identification and entry/exit timing.'
          },
          {
            term: 'RSI (Relative Strength Index)',
            definition: 'A momentum oscillator that measures the speed and magnitude of price changes. Values range from 0-100:<br><ul><li><strong>RSI > 70:</strong> Potentially overbought (may indicate selling opportunity)</li><li><strong>RSI < 30:</strong> Potentially oversold (may indicate buying opportunity)</li><li><strong>RSI 30-70:</strong> Neutral range</li></ul>'
          },
          {
            term: 'MACD (Moving Average Convergence Divergence)',
            definition: 'Shows the relationship between two moving averages. Consists of:<br><ul><li><strong>MACD Line:</strong> Difference between fast and slow EMA</li><li><strong>Signal Line:</strong> EMA of the MACD line</li><li><strong>Histogram:</strong> Difference between MACD and Signal lines</li></ul>When MACD crosses above Signal, it\'s a bullish signal. When it crosses below, it\'s bearish.'
          },
          {
            term: 'Bollinger Bands',
            definition: 'Volatility bands placed above and below a moving average. The bands expand and contract based on volatility:<br><ul><li><strong>Upper/Lower Bands:</strong> 2 standard deviations from the middle band</li><li><strong>Price touches upper band:</strong> Potentially overbought (red dots)</li><li><strong>Price touches lower band:</strong> Potentially oversold (green dots)</li><li><strong>Band Width:</strong> Shows squeeze (low volatility, potential breakout) or expansion (high volatility)</li></ul>'
          },
          {
            term: 'Stochastic Oscillator',
            definition: 'Momentum indicator comparing closing price to price range over a period. Values range from 0-100:<br><ul><li><strong>%K Line:</strong> Fast stochastic line</li><li><strong>%D Line:</strong> Slow stochastic line (SMA of %K)</li><li><strong>Above 80:</strong> Overbought</li><li><strong>Below 20:</strong> Oversold</li></ul>When %K crosses above %D in oversold territory, it\'s a buy signal.'
          },
          {
            term: 'VWAP (Volume Weighted Average Price)',
            definition: 'The average price weighted by volume. Shows where most trading activity occurred. Price above VWAP suggests bullish sentiment, below suggests bearish. Useful for intraday trading and identifying fair value.'
          },
          {
            term: 'ATR (Average True Range)',
            definition: 'Measures market volatility by calculating the average of true ranges over a period. Higher ATR = more volatility. Useful for:<br><ul><li>Setting stop-loss distances</li><li>Position sizing based on volatility</li><li>Identifying periods of high/low volatility</li></ul>'
          },
          {
            term: 'Volume',
            definition: 'The total amount of the asset traded during each time period. Higher volume often indicates stronger price movements and more reliable trends. Shown as bars at the bottom of the chart.'
          },
          {
            term: 'Indicator Combination Signals',
            definition: 'The chart automatically detects when multiple indicators align:<br><ul><li><strong>BUY Signal:</strong> RSI oversold + Price at lower Bollinger Band</li><li><strong>SELL Signal:</strong> RSI overbought + Price at upper Bollinger Band</li><li><strong>STRONG BUY:</strong> Triple oversold (RSI + Stochastic K + Stochastic D all oversold)</li><li><strong>STRONG SELL:</strong> Triple overbought (RSI + Stochastic K + Stochastic D all overbought)</li></ul>These signals appear as alerts on the chart when conditions are met.'
          }
        ]
      },
      {
        title: 'Chart Elements',
        items: [
          {
            term: 'Positions',
            definition: 'Your open trading positions. Shown as markers on the chart with entry price, current price, and unrealized P&L.'
          },
          {
            term: 'Trades',
            definition: 'Your completed trades. Shown as lines connecting entry and exit points, colored green for profits and red for losses.'
          },
          {
            term: 'Opportunities',
            definition: 'Trading opportunities identified by the system. Shown as markers indicating potential entry points based on strategy analysis.'
          },
          {
            term: 'Candlesticks',
            definition: 'Each candle shows the open, high, low, and close prices for a time period. Green candles indicate price went up, red candles indicate price went down.'
          }
        ]
      }
    ],
    'execution': [
      {
        title: 'Trade Execution',
        items: [
          {
            term: 'Recent Trades',
            definition: 'A list of all completed trades, showing entry and exit prices, profit/loss, and duration.'
          },
          {
            term: 'Trade Side',
            definition: 'Whether the trade was a BUY (going long) or SELL (going short) position.'
          },
          {
            term: 'P&L',
            definition: 'Profit and Loss for each trade. Positive values (green) indicate profit, negative values (red) indicate loss.'
          },
          {
            term: 'Hold Time',
            definition: 'How long the position was held before being closed.'
          }
        ]
      },
      {
        title: 'Performance Metrics',
        items: [
          {
            term: 'Total Trades',
            definition: 'Total number of completed trades.'
          },
          {
            term: 'Win Rate',
            definition: 'Percentage of profitable trades out of all completed trades.'
          },
          {
            term: 'Total P&L',
            definition: 'Cumulative profit and loss across all trades.'
          },
          {
            term: 'Average Hold Time',
            definition: 'Average duration that positions are held before being closed.'
          },
          {
            term: 'Best Trade',
            definition: 'The most profitable single trade.'
          },
          {
            term: 'Worst Trade',
            definition: 'The trade with the largest loss.'
          }
        ]
      },
      {
        title: 'Symbol Performance',
        items: [
          {
            term: 'Symbol Breakdown',
            definition: 'Performance statistics broken down by trading symbol, showing which symbols are most profitable.'
          },
          {
            term: 'Average Slippage',
            definition: 'The average difference between expected and actual execution price. Lower is better.'
          },
          {
            term: 'Average Fill Time',
            definition: 'Average time it takes for orders to be filled after being placed.'
          }
        ]
      }
    ]
  }
  
  // Get content for current view, with fallback
  const selectedContent = content[currentViewName]
  
  if (!selectedContent) {
    console.warn('[HelpButton] No content found for viewName:', currentViewName, 'Available keys:', Object.keys(content))
  }
  
  return selectedContent || [
    {
      title: 'General Help',
      items: [
        {
          term: 'Navigation',
          definition: 'Use the sidebar to navigate between different views of the trading system.'
        },
        {
          term: 'Status',
          definition: 'Check the status view to monitor system health and connection status.'
        }
      ]
    }
  ]
})
</script>

<style scoped>
.help-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border: 1px solid var(--color-text-muted, rgba(136, 136, 136, 0.3));
  border-radius: 4px;
  background: var(--color-bg, rgba(10, 10, 10, 0.8));
  color: var(--color-text, #e8e8e8);
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.help-btn:hover {
  border-color: var(--color-accent, rgba(74, 222, 128, 0.5));
  background: var(--color-accent-dark, rgba(74, 222, 128, 0.1));
}

.help-btn span {
  font-size: 14px;
}

/* Help Modal Styles */
.help-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(4px);
}

.help-modal {
  background: var(--color-bg-panel, rgba(20, 20, 30, 0.95));
  border: 1px solid var(--color-text-muted, rgba(136, 136, 136, 0.3));
  border-radius: 12px;
  max-width: 700px;
  max-height: 85vh;
  width: 90%;
  display: flex;
  flex-direction: column;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
}

.help-modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid var(--color-text-muted, rgba(136, 136, 136, 0.2));
}

.help-modal-header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: var(--color-text, #e8e8e8);
}

.help-modal-close {
  background: none;
  border: none;
  font-size: 32px;
  line-height: 1;
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

.help-modal-close:hover {
  background: var(--color-bg-card, rgba(20, 20, 30, 0.5));
  color: var(--color-text, #e8e8e8);
}

.help-modal-content {
  padding: 24px;
  overflow-y: auto;
  flex: 1;
}

.help-section {
  margin-bottom: 32px;
}

.help-section:last-child {
  margin-bottom: 0;
}

.help-section h3 {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--color-accent, #4ade80);
  border-bottom: 1px solid var(--color-text-muted, rgba(136, 136, 136, 0.2));
  padding-bottom: 8px;
}

.help-section dl {
  margin: 0;
}

.help-section dt {
  margin-top: 16px;
  margin-bottom: 6px;
  color: var(--color-text, #e8e8e8);
  font-size: 14px;
}

.help-section dt:first-child {
  margin-top: 0;
}

.help-section dt strong {
  color: var(--color-accent, #4ade80);
}

.help-section dd {
  margin: 0 0 0 20px;
  color: var(--color-text-muted, #888);
  font-size: 13px;
  line-height: 1.6;
}

.help-section dd :deep(ul) {
  margin: 8px 0 0 20px;
  padding: 0;
  list-style: disc;
}

.help-section dd :deep(li) {
  margin: 4px 0;
  color: var(--color-text-muted, #888);
  font-size: 13px;
  line-height: 1.5;
}

.help-section dd :deep(li strong) {
  color: var(--color-text, #e8e8e8);
}

@media (prefers-color-scheme: light) {
  .help-modal {
    background: var(--color-bg-panel, rgba(255, 255, 255, 0.95));
    border-color: var(--color-text-muted, rgba(107, 114, 128, 0.3));
  }
  
  .help-modal-header {
    border-bottom-color: var(--color-text-muted, rgba(107, 114, 128, 0.2));
  }
  
  .help-modal-header h2 {
    color: var(--color-text, #1a1a1a);
  }
  
  .help-section h3 {
    color: var(--color-accent, #4ade80);
    border-bottom-color: var(--color-text-muted, rgba(107, 114, 128, 0.2));
  }
  
  .help-section dt {
    color: var(--color-text, #1a1a1a);
  }
  
  .help-section dt strong {
    color: var(--color-accent, #4ade80);
  }
  
  .help-section dd :deep(li strong) {
    color: var(--color-text, #1a1a1a);
  }
}
</style>

