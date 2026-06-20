//! Type definitions for API responses
//!
//! This module contains all data structures used for communication
//! between the Tauri backend and the Python FastAPI backend.
//!
//! All types implement `Serialize` and `Deserialize` for JSON communication
//! and `Clone` for efficient data handling.

use serde::{Deserialize, Serialize};
use chrono::{DateTime, Utc};
use std::collections::HashMap;

/// System status information from the backend
#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct SystemStatus {
    pub is_running: bool,
    pub testnet_mode: bool,
    pub execution_enabled: bool,
    pub last_heartbeat: Option<DateTime<Utc>>,
    pub uptime_seconds: u64,
    pub errors_count: u32,
}

/// Trading performance metrics
#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct TradingMetrics {
    pub total_pnl: f64,
    pub total_trades: u32,
    pub winning_trades: u32,
    pub win_rate: f64,
    pub open_positions: u32,
    pub daily_pnl: f64,
    pub max_drawdown: f64,
}

/// Market data for a single symbol
#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct MarketData {
    pub symbol: String,
    pub price: f64,
    pub signal: f64,
    pub signal_strength: String,
    pub volume: f64,
    pub change_24h: f64,
    pub last_update: DateTime<Utc>,
}

/// Open trading position information
#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct Position {
    pub symbol: String,
    pub side: String,
    pub entry_price: f64,
    pub current_price: f64,
    pub quantity: f64,
    pub unrealized_pnl: f64,
    pub entry_time: DateTime<Utc>,
    pub hold_time_seconds: u64,
}

/// Historical trade information
#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct TradeHistory {
    pub symbol: String,
    pub side: String,
    pub entry_price: f64,
    pub exit_price: f64,
    pub quantity: f64,
    pub pnl: f64,
    pub hold_time_seconds: u64,
    pub timestamp: DateTime<Utc>,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct DashboardData {
    pub system_status: SystemStatus,
    pub trading_metrics: TradingMetrics,
    pub market_data: Vec<MarketData>,
    pub positions: Vec<Position>,
    pub recent_trades: Vec<TradeHistory>,
}

/// Auto-discovery engine status and statistics
#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct AutoDiscoveryStatus {
    pub enabled: bool,
    pub is_running: bool,
    pub stats: AutoDiscoveryStats,
    pub budget_allocation: BudgetAllocation,
    pub settings: AutoDiscoverySettings,
}

/// Auto-discovery statistics
#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct AutoDiscoveryStats {
    pub discovered_symbols: u32,
    pub active_symbols: u32,
    pub total_pnl: f64,
    pub total_trades: u32,
    pub winning_trades: u32,
    pub win_rate: f64,
    pub symbols: HashMap<String, AutoDiscoverySymbol>,
    pub closed_trades: Vec<ClosedTrade>,
}

/// Information about a discovered symbol
#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct AutoDiscoverySymbol {
    pub strategy_fit_score: f64,
    pub allocated_budget: f64,
    pub total_trades: u32,
    pub win_rate: f64,
    pub cumulative_pnl: f64,
    pub status: String,
    pub discovery_time: Option<String>,
}

/// Closed trade information
#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct ClosedTrade {
    pub symbol: String,
    pub entry_price: f64,
    pub exit_price: f64,
    pub pnl: f64,
    pub hold_time: f64,
    pub reason: String,
    pub timestamp: f64,
}

/// Budget allocation breakdown
#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct BudgetAllocation {
    pub reserve: f64,
    pub whitelist: f64,
    pub auto_discovery: f64,
    pub trading_pool: f64,
}

/// Auto-discovery configuration settings
#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct AutoDiscoverySettings {
    pub max_symbols: u32,
    pub min_signal: f64,
    pub discovery_interval_minutes: u32,
    pub rebalance_hours: u32,
}

/// Episode pattern information
#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct EpisodePattern {
    pub id: String,
    pub regime: String,
    pub success_rate: f64,
    pub avg_pnl_pct: f64,
    pub sample_count: u32,
    pub volatility_range: (f64, f64),
    pub signal_strength_range: (f64, f64),
}

/// Episode pattern summary
#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct EpisodePatternSummary {
    pub pattern_count: u32,
    pub patterns: Vec<EpisodePattern>,
    pub last_analysis: Option<String>,
}

/// Health check response
#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct HealthCheck {
    pub connected: bool,
    pub latency_ms: Option<u64>,
    pub backend_url: String,
    pub error: Option<String>,
}

