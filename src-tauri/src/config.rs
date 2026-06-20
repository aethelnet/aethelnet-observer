//! Configuration management for the Tauri application
//!
//! Reads configuration from environment variables with sensible defaults.
//! All paths and URLs are configurable to support different deployment scenarios.
//!
//! # Environment Variables
//!
//! - `AURATIC_API_URL` - Backend API base URL (default: `http://localhost:8000`)
//! - `AURATIC_LOG_PATH` - Path to backend log file
//! - `AURATIC_VAULT_PATH` - Path to vault directory
//! - `AURATIC_REQUEST_TIMEOUT` - HTTP request timeout in seconds (default: 10)
//! - `AURATIC_MAX_RETRIES` - Maximum retry attempts (default: 3)
//! - `AURATIC_RETRY_BACKOFF` - Retry backoff multiplier (default: 2.0)
//! - `AURATIC_RETRY_DELAY_MS` - Base retry delay in milliseconds (default: 500)
//!
//! # Example
//!
//! ```rust,no_run
//! use crate::config::Config;
//!
//! let config = Config::new();
//! let url = config.api_endpoint("/api/status");
//! ```

use std::env;

/// Application configuration
///
/// Holds all configuration values for the Tauri application.
/// Values are loaded from environment variables with sensible defaults.
pub struct Config {
    /// Backend API base URL
    pub api_url: String,
    /// Path to backend log file
    pub log_path: String,
    /// Path to vault directory
    pub vault_path: String,
    /// HTTP request timeout in seconds
    pub request_timeout_secs: u64,
    /// Maximum retry attempts for HTTP requests
    pub max_retry_attempts: u32,
    /// Retry backoff multiplier (delay = base_delay * multiplier^attempt)
    pub retry_backoff_multiplier: f64,
    /// Base delay in milliseconds before first retry
    pub retry_base_delay_ms: u64,
}

impl Config {
    /// Create a new Config instance with defaults or environment variables
    pub fn new() -> Self {
        log::debug!("[CONFIG] Loading configuration from environment");
        
        let api_url = env::var("AURATIC_API_URL")
            .unwrap_or_else(|_| {
                let default = "http://localhost:8000".to_string();
                log::debug!("[CONFIG] Using default API URL: {}", default);
                default
            });
        log::info!("[CONFIG] API URL: {}", api_url);
        
        let log_path = env::var("AURATIC_LOG_PATH").unwrap_or_else(|_| {
            let home = env::var("HOME").unwrap_or_else(|_| "~".to_string());
            let default = format!("{}/Projects/Backup/auratic-systems-prime/backend.log", home);
            log::debug!("[CONFIG] Using default log path: {}", default);
            default
        });
        log::info!("[CONFIG] Log path: {}", log_path);
        
        let vault_path = env::var("AURATIC_VAULT_PATH").unwrap_or_else(|_| {
            let home = env::var("HOME").unwrap_or_else(|_| "~".to_string());
            let default = format!("{}/Projects/Cursor", home);
            log::debug!("[CONFIG] Using default vault path: {}", default);
            default
        });
        log::info!("[CONFIG] Vault path: {}", vault_path);
        
        let request_timeout_secs = env::var("AURATIC_REQUEST_TIMEOUT")
            .ok()
            .and_then(|v| v.parse().ok())
            .unwrap_or_else(|| {
                let default = 10;
                log::debug!("[CONFIG] Using default request timeout: {}s", default);
                default
            });
        log::info!("[CONFIG] Request timeout: {}s", request_timeout_secs);
        
        let max_retry_attempts = env::var("AURATIC_MAX_RETRIES")
            .ok()
            .and_then(|v| v.parse().ok())
            .unwrap_or_else(|| {
                let default = 3;
                log::debug!("[CONFIG] Using default max retry attempts: {}", default);
                default
            });
        log::info!("[CONFIG] Max retry attempts: {}", max_retry_attempts);
        
        let retry_backoff_multiplier = env::var("AURATIC_RETRY_BACKOFF")
            .ok()
            .and_then(|v| v.parse().ok())
            .unwrap_or_else(|| {
                let default = 2.0;
                log::debug!("[CONFIG] Using default retry backoff multiplier: {}", default);
                default
            });
        log::info!("[CONFIG] Retry backoff multiplier: {}", retry_backoff_multiplier);
        
        let retry_base_delay_ms = env::var("AURATIC_RETRY_DELAY_MS")
            .ok()
            .and_then(|v| v.parse().ok())
            .unwrap_or_else(|| {
                let default = 500;
                log::debug!("[CONFIG] Using default retry base delay: {}ms", default);
                default
            });
        log::info!("[CONFIG] Retry base delay: {}ms", retry_base_delay_ms);
        
        Self {
            api_url,
            log_path,
            vault_path,
            request_timeout_secs,
            max_retry_attempts,
            retry_backoff_multiplier,
            retry_base_delay_ms,
        }
    }

    /// Get the full API URL for an endpoint
    pub fn api_endpoint(&self, path: &str) -> String {
        format!("{}{}", self.api_url, path)
    }
}

impl Default for Config {
    fn default() -> Self {
        Self::new()
    }
}

