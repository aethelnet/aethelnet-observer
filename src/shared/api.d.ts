/**
 * TypeScript declarations for src/shared/api.js
 */

export interface ApiError {
  error: true;
  status?: number;
  detail?: string;
}

export interface Opportunity {
  id: string;
  symbol: string;
  entry_start: string;
  entry_end: string;
  exit_time: string;
  confidence: number;
  urgency: number;
  direction: 'LONG' | 'SHORT';
  entry_price?: number;
  target_price?: number;
  stop_loss?: number;
  order_status?: string;
  allocation?: { source: string; amount: number } | null;
}

export interface SymbolAnalysis {
  symbol: string;
  predictions: any[];
  currentPrice: number;
  opportunities: Opportunity[];
  isWhitelisted: boolean;
  isDiscovered: boolean;
  analysis: {
    hasPredictions: boolean;
    hasOpportunities: boolean;
    lastUpdate: string | null;
  };
  error?: boolean;
  detail?: string;
}

export interface BaseQuoteConfig {
  baseCurrencies: string[];
  quoteCurrencies: string[];
}

export interface SymbolValidation {
  valid: boolean;
  error?: string;
  base?: string;
  quote?: string;
}

export interface HiveStatus {
  beta_rat: boolean;
  is_authorized: boolean;
  authorization_method?: string;
  current_user?: string;
  whitelist?: string[];
  blacklist?: string[];
}

export interface OrderStatus {
  order_status: string;
  [key: string]: any;
}

export interface OrderProgress {
  completed: number;
  pending: number;
  total: number;
  completedIds: string[];
  pendingIds: string[];
}

export interface OpportunityFilters {
  symbol?: string;
  min_confidence?: number;
  max_confidence?: number;
  urgency?: number;
  direction?: 'LONG' | 'SHORT';
}

export const API_BASE: string;

// Core API functions
export function fetchMetrics(): Promise<any | ApiError | null>;
export function fetchMarketData(): Promise<any[] | ApiError | null>;
export function fetchPositions(): Promise<any[] | ApiError | null>;
export function fetchRecentTrades(limit?: number): Promise<any[] | ApiError | null>;
export function fetchFailsafeStatus(): Promise<any | ApiError | null>;
export function activatePanic(): Promise<any | ApiError | null>;
export function resumeTrading(): Promise<any | ApiError | null>;

// Prediction functions
export function fetchPredictions(symbol?: string | null): Promise<any | ApiError | null>;

// Opportunity functions
export function fetchOpportunities(filters?: OpportunityFilters): Promise<Opportunity[] | ApiError | null>;
export function fetchSymbolOpportunities(): Promise<any[] | ApiError | null>;
export function placeOpportunityOrder(opportunity: Opportunity, autoExecute?: boolean): Promise<any | ApiError | null>;
export function getOpportunityOrderStatus(opportunityId: string): Promise<OrderStatus | ApiError | null>;
export function fetchUpcomingTrades(): Promise<any[]>;
export function fetchActiveOrders(): Promise<any[]>;
export function waitForOrdersCompletion(
  opportunityIds: string[],
  onProgress?: ((progress: OrderProgress) => void) | null,
  pollInterval?: number,
  maxWaitTime?: number
): Promise<{ completed: string[]; pending: string[] }>;

// Auto-discovery functions
export function fetchAutoDiscoveryStatus(): Promise<any | ApiError | null>;
export function fetchAutoDiscoveryDiagnostics(): Promise<any | ApiError | null>;
export function triggerAutoDiscoveryScan(): Promise<any | ApiError | null>;
export function fetchAutoDiscoverySymbols(): Promise<any | ApiError | null>;
export function promoteToWhitelist(symbol: string): Promise<any | ApiError | null>;
export function removeFromDiscovery(symbol: string): Promise<any | ApiError | null>;

// Symbol functions
export function fetchAllSymbols(): Promise<string[] | null>;
export function getSymbolAnalysis(symbol: string): Promise<SymbolAnalysis | null>;
export function getBaseQuoteConfig(): Promise<BaseQuoteConfig | null>;
export function parseSymbolForBaseQuote(symbol: string): {
  canBeBase: boolean;
  base: string | null;
  quote: string | null;
};
export function validateSymbolFormat(symbol: string, validQuotes?: string[]): SymbolValidation;

// Budget functions
export function fetchBudgetAllocation(): Promise<any | ApiError | null>;
export function reallocateToAutopilot(pools?: string[]): Promise<any | ApiError | null>;

// Authorization functions
export function fetchHiveStatus(): Promise<HiveStatus | ApiError | null>;
export function addHiveAlly(username: string): Promise<any | ApiError | null>;
export function revokeHiveAlly(username: string): Promise<any | ApiError | null>;

// Formatting functions
export function formatCurrency(value: number | string | null | undefined): string;
export function formatPercentage(value: number | string | null | undefined, decimals?: number): string;
export function formatNumber(value: number | string | null | undefined, decimals?: number): string;
export function formatDuration(seconds: number): string;

