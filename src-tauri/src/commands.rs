//! Tauri command handlers
//! 
//! This module contains all Tauri commands that can be invoked from the frontend.
//! All commands use the shared HTTP client and proper error handling.

use crate::error::AppError;
use crate::http_client::get_client;
use crate::types::*;
use crate::config::Config;
use std::process::Command;

/// Fetch system status from backend
///
/// # Returns
/// System status including running state, testnet mode, execution status, and uptime.
///
/// # Errors
/// Returns `AppError` if the HTTP request fails or the response cannot be parsed.
#[tauri::command]
pub async fn fetch_backend_status() -> Result<SystemStatus, AppError> {
    log::debug!("[CMD] fetch_backend_status called");
    let client = get_client()?;
    let status = client.get::<SystemStatus>("/api/dashboard/status").await?;
    log::info!("[CMD] fetch_backend_status - Success");
    Ok(status)
}

/// Fetch trading metrics from backend
///
/// # Returns
/// Trading metrics including PnL, win rate, total trades, and open positions.
///
/// # Errors
/// Returns `AppError` if the HTTP request fails or the response cannot be parsed.
#[tauri::command]
pub async fn fetch_trading_metrics() -> Result<TradingMetrics, AppError> {
    log::debug!("[CMD] fetch_trading_metrics called");
    let client = get_client()?;
    let metrics = client.get::<TradingMetrics>("/api/dashboard/metrics").await?;
    log::info!("[CMD] fetch_trading_metrics - Success");
    Ok(metrics)
}

/// Fetch market data from backend
///
/// # Returns
/// Vector of market data for all monitored symbols.
///
/// # Errors
/// Returns `AppError` if the HTTP request fails or the response cannot be parsed.
#[tauri::command]
pub async fn fetch_market_data() -> Result<Vec<MarketData>, AppError> {
    log::debug!("[CMD] fetch_market_data called");
    let client = get_client()?;
    let data = client.get::<Vec<MarketData>>("/api/dashboard/market-data").await?;
    log::info!("[CMD] fetch_market_data - Success ({} symbols)", data.len());
    Ok(data)
}

/// Fetch positions from backend
///
/// # Returns
/// Vector of current open positions.
///
/// # Errors
/// Returns `AppError` if the HTTP request fails or the response cannot be parsed.
#[tauri::command]
pub async fn fetch_positions() -> Result<Vec<Position>, AppError> {
    log::debug!("[CMD] fetch_positions called");
    let client = get_client()?;
    let positions = client.get::<Vec<Position>>("/api/dashboard/positions").await?;
    log::info!("[CMD] fetch_positions - Success ({} positions)", positions.len());
    Ok(positions)
}

/// Fetch recent trades from backend
///
/// # Returns
/// Vector of recent trade history.
///
/// # Errors
/// Returns `AppError` if the HTTP request fails or the response cannot be parsed.
#[tauri::command]
pub async fn fetch_recent_trades() -> Result<Vec<TradeHistory>, AppError> {
    log::debug!("[CMD] fetch_recent_trades called");
    let client = get_client()?;
    let trades = client.get::<Vec<TradeHistory>>("/api/dashboard/recent-trades").await?;
    log::info!("[CMD] fetch_recent_trades - Success ({} trades)", trades.len());
    Ok(trades)
}

/// Activate emergency stop
///
/// Immediately stops all trading activity and closes all positions.
///
/// # Returns
/// Success message string.
///
/// # Errors
/// Returns `AppError` if the HTTP request fails.
#[tauri::command]
pub async fn emergency_stop() -> Result<String, AppError> {
    log::warn!("[CMD] emergency_stop called");
    let client = get_client()?;
    client.post("/api/failsafe/panic").await?;
    log::warn!("[CMD] emergency_stop - Success");
    Ok("Emergency stop activated".to_string())
}

/// Restart trading
///
/// Resumes trading activity after an emergency stop.
///
/// # Returns
/// Success message string.
///
/// # Errors
/// Returns `AppError` if the HTTP request fails.
#[tauri::command]
pub async fn restart_trading() -> Result<String, AppError> {
    log::info!("[CMD] restart_trading called");
    let client = get_client()?;
    client.post("/api/failsafe/resume").await?;
    log::info!("[CMD] restart_trading - Success");
    Ok("Trading restarted".to_string())
}

/// Start week test
///
/// Initiates a week-long trading test to validate strategy performance.
///
/// # Returns
/// Success message string.
///
/// # Errors
/// Returns `AppError` if the HTTP request fails.
#[tauri::command]
pub async fn start_week_test() -> Result<String, AppError> {
    log::info!("[CMD] start_week_test called");
    let client = get_client()?;
    client.post("/api/dashboard/start-week-test").await?;
    log::info!("[CMD] start_week_test - Success");
    Ok("Week test started".to_string())
}

/// Open logs file using system default application
///
/// Opens the backend log file in the system's default text editor.
///
/// # Returns
/// Success message string.
///
/// # Errors
/// Returns `AppError` if the file cannot be opened.
#[tauri::command]
pub async fn open_logs() -> Result<String, AppError> {
    log::debug!("[CMD] open_logs called");
    let config = Config::new();
    log::debug!("[CMD] open_logs - Attempting to open: {}", config.log_path);
    open_path(&config.log_path)?;
    log::info!("[CMD] open_logs - Success");
    Ok("Logs opened".to_string())
}

/// Open vault directory using system default application
///
/// Opens the vault directory in the system's default file manager.
///
/// # Returns
/// Success message string.
///
/// # Errors
/// Returns `AppError` if the directory cannot be opened.
#[tauri::command]
pub async fn open_vault() -> Result<String, AppError> {
    log::debug!("[CMD] open_vault called");
    let config = Config::new();
    log::debug!("[CMD] open_vault - Attempting to open: {}", config.vault_path);
    open_path(&config.vault_path)?;
    log::info!("[CMD] open_vault - Success");
    Ok("Vault opened".to_string())
}

/// Health check - test backend connectivity
///
/// Tests the connection to the backend and measures latency.
///
/// # Returns
/// Health check result with connection status and latency.
///
/// # Errors
/// Returns `AppError` if the health check fails.
#[tauri::command]
pub async fn health_check() -> Result<crate::types::HealthCheck, AppError> {
    log::debug!("[CMD] health_check called");
    let config = Config::new();
    let start_time = std::time::Instant::now();
    
    match get_client() {
        Ok(client) => {
            match client.get::<crate::types::SystemStatus>("/api/dashboard/status").await {
                Ok(_) => {
                    let latency_ms = start_time.elapsed().as_millis() as u64;
                    log::info!("[CMD] health_check - Success (latency: {}ms)", latency_ms);
                    Ok(crate::types::HealthCheck {
                        connected: true,
                        latency_ms: Some(latency_ms),
                        backend_url: config.api_url.clone(),
                        error: None,
                    })
                }
                Err(e) => {
                    let latency_ms = start_time.elapsed().as_millis() as u64;
                    log::warn!("[CMD] health_check - Failed (latency: {}ms): {}", latency_ms, e);
                    Ok(crate::types::HealthCheck {
                        connected: false,
                        latency_ms: Some(latency_ms),
                        backend_url: config.api_url.clone(),
                        error: Some(e.to_string()),
                    })
                }
            }
        }
        Err(e) => {
            log::error!("[CMD] health_check - Client error: {}", e);
            Ok(crate::types::HealthCheck {
                connected: false,
                latency_ms: None,
                backend_url: config.api_url.clone(),
                error: Some(e.to_string()),
            })
        }
    }
}

/// Fetch auto-discovery engine status
///
/// # Returns
/// Auto-discovery status including statistics, budget allocation, and settings.
///
/// # Errors
/// Returns `AppError` if the HTTP request fails or the response cannot be parsed.
#[tauri::command]
pub async fn fetch_auto_discovery_status() -> Result<crate::types::AutoDiscoveryStatus, AppError> {
    log::debug!("[CMD] fetch_auto_discovery_status called");
    let client = get_client()?;
    let status = client.get::<crate::types::AutoDiscoveryStatus>("/api/auto-discovery/status").await?;
    log::info!("[CMD] fetch_auto_discovery_status - Success");
    Ok(status)
}

/// Fetch discovered symbols list
///
/// # Returns
/// List of currently discovered symbols with their status and performance.
///
/// # Errors
/// Returns `AppError` if the HTTP request fails or the response cannot be parsed.
#[tauri::command]
pub async fn fetch_auto_discovery_symbols() -> Result<std::collections::HashMap<String, crate::types::AutoDiscoverySymbol>, AppError> {
    log::debug!("[CMD] fetch_auto_discovery_symbols called");
    let client = get_client()?;
    let response: serde_json::Value = client.get("/api/auto-discovery/symbols").await?;
    
    // Extract symbols from response
    let symbols: std::collections::HashMap<String, crate::types::AutoDiscoverySymbol> = response
        .get("symbols")
        .and_then(|s| serde_json::from_value(s.clone()).ok())
        .unwrap_or_default();
    
    log::info!("[CMD] fetch_auto_discovery_symbols - Success ({} symbols)", symbols.len());
    Ok(symbols)
}

/// Fetch learned episode patterns
///
/// # Returns
/// Summary of learned patterns from historical successful trades.
///
/// # Errors
/// Returns `AppError` if the HTTP request fails or the response cannot be parsed.
#[allow(dead_code)]
#[tauri::command]
pub async fn fetch_auto_discovery_patterns() -> Result<crate::types::EpisodePatternSummary, AppError> {
    log::debug!("[CMD] fetch_auto_discovery_patterns called");
    let client = get_client()?;
    let patterns = client.get::<crate::types::EpisodePatternSummary>("/api/auto-discovery/patterns").await?;
    log::info!("[CMD] fetch_auto_discovery_patterns - Success ({} patterns)", patterns.pattern_count);
    Ok(patterns)
}

/// Promote a discovered symbol to the whitelist
///
/// # Arguments
/// * `symbol` - The symbol to promote (e.g., "BTCUSDT")
///
/// # Returns
/// Success message string.
///
/// # Errors
/// Returns `AppError` if the HTTP request fails or the symbol is not found.
#[tauri::command]
pub async fn promote_symbol_to_whitelist(symbol: String) -> Result<String, AppError> {
    log::info!("[CMD] promote_symbol_to_whitelist called for: {}", symbol);
    let client = get_client()?;
    let endpoint = format!("/api/auto-discovery/promote/{}", symbol);
    client.post(&endpoint).await?;
    log::info!("[CMD] promote_symbol_to_whitelist - Success for: {}", symbol);
    Ok(format!("Symbol {} promoted to whitelist", symbol))
}

/// Remove a symbol from auto-discovery
///
/// # Arguments
/// * `symbol` - The symbol to remove (e.g., "BTCUSDT")
///
/// # Returns
/// Success message string.
///
/// # Errors
/// Returns `AppError` if the HTTP request fails or the symbol is not found.
#[tauri::command]
pub async fn remove_discovered_symbol(symbol: String) -> Result<String, AppError> {
    log::info!("[CMD] remove_discovered_symbol called for: {}", symbol);
    let client = get_client()?;
    let endpoint = format!("/api/auto-discovery/remove/{}", symbol);
    client.post(&endpoint).await?;
    log::info!("[CMD] remove_discovered_symbol - Success for: {}", symbol);
    Ok(format!("Symbol {} removed from auto-discovery", symbol))
}

/// Update episode patterns by triggering pattern analysis
///
/// # Returns
/// Success message string.
///
/// # Errors
/// Returns `AppError` if the HTTP request fails.
#[allow(dead_code)]
#[tauri::command]
pub async fn update_episode_patterns() -> Result<String, AppError> {
    log::info!("[CMD] update_episode_patterns called");
    let client = get_client()?;
    client.post("/api/auto-discovery/patterns/update").await?;
    log::info!("[CMD] update_episode_patterns - Success");
    Ok("Pattern analysis started in background".to_string())
}

/// Cross-platform path opening helper
fn open_path(path: &str) -> Result<(), AppError> {
    #[cfg(target_os = "linux")]
    {
        log::debug!("[CMD] open_path - Linux: xdg-open {}", path);
        match Command::new("xdg-open").arg(path).spawn() {
            Ok(_) => {
                log::debug!("[CMD] open_path - Successfully spawned xdg-open");
                Ok(())
            }
            Err(e) => {
                log::error!("[CMD] open_path - Failed to spawn xdg-open: {}", e);
                Err(AppError::System(format!("Failed to open path: {}", e)))
            }
        }
    }
    
    #[cfg(target_os = "macos")]
    {
        log::debug!("[CMD] open_path - macOS: open {}", path);
        match Command::new("open").arg(path).spawn() {
            Ok(_) => {
                log::debug!("[CMD] open_path - Successfully spawned open");
                Ok(())
            }
            Err(e) => {
                log::error!("[CMD] open_path - Failed to spawn open: {}", e);
                Err(AppError::System(format!("Failed to open path: {}", e)))
            }
        }
    }
    
    #[cfg(target_os = "windows")]
    {
        log::debug!("[CMD] open_path - Windows: cmd /C start {}", path);
        match Command::new("cmd").args(["/C", "start", "", path]).spawn() {
            Ok(_) => {
                log::debug!("[CMD] open_path - Successfully spawned cmd");
                Ok(())
            }
            Err(e) => {
                log::error!("[CMD] open_path - Failed to spawn cmd: {}", e);
                Err(AppError::System(format!("Failed to open path: {}", e)))
            }
        }
    }
    
    #[cfg(not(any(target_os = "linux", target_os = "macos", target_os = "windows")))]
    {
        log::error!("[CMD] open_path - Unsupported platform");
        Err(AppError::System("Unsupported platform for opening paths".to_string()))
    }
}

