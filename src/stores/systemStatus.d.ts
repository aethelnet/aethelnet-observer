/**
 * TypeScript declarations for src/stores/systemStatus.js
 */

import { Ref, ComputedRef } from 'vue';

export interface SystemInfo {
  is_running?: boolean;
  execution_enabled?: boolean;
  testnet_mode?: boolean;
  panic_active?: boolean;
  backend_connected?: boolean;
  [key: string]: any;
}

export interface TradingMetrics {
  total_pnl?: number;
  win_rate?: number;
  total_trades?: number;
  open_positions?: number;
  [key: string]: any;
}

export interface Position {
  symbol: string;
  [key: string]: any;
}

export interface MarketData {
  symbol: string;
  price: number;
  signal_strength?: string;
  change_24h?: number;
  volume?: number;
  [key: string]: any;
}

export interface RecentTrade {
  symbol: string;
  [key: string]: any;
}

export interface AuthorizationStatus {
  beta_rat: boolean;
  is_authorized: boolean;
  authorization_method?: string;
  current_user?: string;
  whitelist?: string[];
  blacklist?: string[];
  [key: string]: any;
}

export interface SystemStatusStore {
  // Connection State
  connectionState: Ref<'idle' | 'connecting' | 'connected' | 'error' | 'reconnecting'>;
  isLive: ComputedRef<boolean>;
  statusColor: ComputedRef<string>;
  lastHeartbeat: Ref<number>;
  errorLog: Ref<string[]>;
  setStatus: (status: 'idle' | 'connecting' | 'connected' | 'error' | 'reconnecting') => void;
  logError: (msg: string) => void;

  // System Info
  systemInfo: Ref<SystemInfo | null>;
  systemInfoLoading: Ref<boolean>;
  systemInfoError: Ref<string | null>;
  systemInfoLastUpdate: Ref<number | null>;
  setSystemInfo: (info: SystemInfo | null) => void;
  setSystemInfoLoading: (loading: boolean) => void;
  setSystemInfoError: (error: string | null) => void;

  // Trading Metrics
  tradingMetrics: Ref<TradingMetrics | null>;
  tradingMetricsLoading: Ref<boolean>;
  tradingMetricsError: Ref<string | null>;
  tradingMetricsLastUpdate: Ref<number | null>;
  setTradingMetrics: (metrics: TradingMetrics | null) => void;
  setTradingMetricsLoading: (loading: boolean) => void;
  setTradingMetricsError: (error: string | null) => void;

  // Positions
  positions: Ref<Position[]>;
  positionsLoading: Ref<boolean>;
  positionsError: Ref<string | null>;
  positionsLastUpdate: Ref<number | null>;
  setPositions: (pos: Position[] | null) => void;
  setPositionsLoading: (loading: boolean) => void;
  setPositionsError: (error: string | null) => void;

  // Market Data
  marketData: Ref<MarketData[]>;
  marketDataLoading: Ref<boolean>;
  marketDataError: Ref<string | null>;
  marketDataLastUpdate: Ref<number | null>;
  setMarketData: (data: MarketData[] | null) => void;
  setMarketDataLoading: (loading: boolean) => void;
  setMarketDataError: (error: string | null) => void;

  // Recent Trades
  recentTrades: Ref<RecentTrade[]>;
  recentTradesLoading: Ref<boolean>;
  recentTradesError: Ref<string | null>;
  recentTradesLastUpdate: Ref<number | null>;
  setRecentTrades: (trades: RecentTrade[] | null) => void;
  setRecentTradesLoading: (loading: boolean) => void;
  setRecentTradesError: (error: string | null) => void;

  // Authorization
  authorizationStatus: Ref<AuthorizationStatus | null>;
  authorizationLoading: Ref<boolean>;
  authorizationError: Ref<string | null>;
  authorizationLastUpdate: Ref<number | null>;
  isAuthorized: ComputedRef<boolean>;
  isBetaRat: ComputedRef<boolean>;
  authorizationMethod: ComputedRef<string | null>;
  setAuthorizationStatus: (status: AuthorizationStatus | null) => void;
  fetchAuthorizationStatus: () => Promise<void>;
  startAuthorizationRefresh: () => void;
  stopAuthorizationRefresh: () => void;

  // Utility
  clearErrors: () => void;
}

export function useSystemStatus(): SystemStatusStore;

