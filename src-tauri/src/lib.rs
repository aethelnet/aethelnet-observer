// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

//! Auratic Systems Tauri Application
//!
//! This is the Rust backend for the Tauri desktop application.
//! It provides Tauri commands that the frontend can invoke to interact
//! with the Python FastAPI backend.
//!
//! ## Module Structure
//!
//! - `commands` - Tauri command handlers
//! - `config` - Configuration management
//! - `error` - Error types and handling
//! - `http_client` - HTTP client for API requests
//! - `types` - Data structures for API communication

mod commands;
mod config;
mod error;
mod http_client;
mod types;

// Re-export types for external use
pub use types::*;

use commands::*;

/// Initialize and run the Tauri application
#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    log::info!("[APP] Starting Auratic Systems Tauri application");
    log::debug!("[APP] Loading configuration...");
    
    // Initialize HTTP client early to catch configuration errors
    match http_client::get_client() {
        Ok(_) => {
            log::info!("[APP] HTTP client initialized successfully");
        }
        Err(e) => {
            log::error!("[APP] Failed to initialize HTTP client: {}", e);
            log::error!("[APP] Application will continue but API calls may fail");
        }
    }

    tauri::Builder::default()
        .plugin(
            tauri_plugin_log::Builder::default()
                .level(log::LevelFilter::Info)
                .build(),
        )
        .invoke_handler(tauri::generate_handler![
            fetch_backend_status,
            fetch_trading_metrics,
            fetch_market_data,
            fetch_positions,
            fetch_recent_trades,
            emergency_stop,
            restart_trading,
            start_week_test,
            open_logs,
            open_vault,
            health_check,
            fetch_auto_discovery_status,
            fetch_auto_discovery_symbols,
            promote_symbol_to_whitelist,
            remove_discovered_symbol
            // TODO: Fix serialization for these commands if needed
            // fetch_auto_discovery_patterns,
            // update_episode_patterns
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
