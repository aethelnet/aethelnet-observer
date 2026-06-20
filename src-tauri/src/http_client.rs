//! HTTP client for making API requests
//!
//! Provides a shared, configured HTTP client with:
//! - Request timeouts
//! - Automatic retry logic with exponential backoff
//! - Proper error handling
//! - JSON deserialization
//! - Connection pooling
//!
//! # Example
//!
//! ```rust,no_run
//! use crate::http_client::get_client;
//!
//! async fn example() -> Result<(), AppError> {
//!     let client = get_client()?;
//!     let data = client.get::<MyType>("/api/endpoint").await?;
//!     Ok(())
//! }
//! ```

use crate::config::Config;
use crate::error::AppError;
use reqwest::Client;
use std::time::Duration;

/// Shared HTTP client with proper configuration
pub struct HttpClient {
    client: Client,
    config: Config,
}

impl HttpClient {
    /// Create a new HTTP client with configuration
    pub fn new(config: Config) -> Result<Self, AppError> {
        log::debug!("[HTTP] Initializing HTTP client with timeout: {}s", config.request_timeout_secs);
        let client = Client::builder()
            .timeout(Duration::from_secs(config.request_timeout_secs))
            .build()
            .map_err(|e| {
                log::error!("[HTTP] Failed to create HTTP client: {}", e);
                AppError::Config(format!("Failed to create HTTP client: {}", e))
            })?;

        log::info!("[HTTP] HTTP client initialized successfully");
        Ok(Self { client, config })
    }

    /// Generic GET request with JSON deserialization and retry logic
    ///
    /// Automatically retries on transient errors (timeout, connection) with exponential backoff.
    /// Does not retry on 4xx client errors.
    pub async fn get<T>(&self, endpoint: &str) -> Result<T, AppError>
    where
        T: serde::de::DeserializeOwned,
    {
        let url = self.config.api_endpoint(endpoint);
        log::debug!("[HTTP] GET request to: {}", url);

        let mut last_reqwest_error: Option<reqwest::Error> = None;
        let mut last_app_error: Option<AppError> = None;
        
        for attempt in 0..=self.config.max_retry_attempts {
            if attempt > 0 {
                let delay_ms = (self.config.retry_base_delay_ms as f64 
                    * self.config.retry_backoff_multiplier.powi(attempt as i32 - 1)) as u64;
                log::debug!("[HTTP] GET {} - Retry attempt {}/{} after {}ms delay", 
                    url, attempt, self.config.max_retry_attempts, delay_ms);
                tokio::time::sleep(Duration::from_millis(delay_ms)).await;
            }

            let start_time = std::time::Instant::now();
            let response_result = self.client.get(&url).send().await;
            
            let response = match response_result {
                Ok(resp) => {
                    let elapsed = start_time.elapsed();
                    log::debug!("[HTTP] GET {} - Response received in {:?}", url, elapsed);
                    resp
                }
                Err(e) => {
                    let elapsed = start_time.elapsed();
                    last_reqwest_error = Some(e);
                    
                    // Check if error is retryable (timeout or connection error)
                    let is_retryable = last_reqwest_error.as_ref().map(|err| {
                        err.is_timeout() || err.is_connect()
                    }).unwrap_or(false);
                    
                    if is_retryable && attempt < self.config.max_retry_attempts {
                        log::warn!("[HTTP] GET {} - Transient error after {:?} (attempt {}): {}", 
                            url, elapsed, attempt + 1, last_reqwest_error.as_ref().unwrap());
                        continue; // Retry
                    } else {
                        log::error!("[HTTP] GET {} - Request failed after {:?}: {}", url, elapsed, last_reqwest_error.as_ref().unwrap());
                        return Err(last_reqwest_error.unwrap().into());
                    }
                }
            };

            let status = response.status();
            log::debug!("[HTTP] GET {} - Status: {}", url, status);
            
            if !status.is_success() {
                let status_code = status.as_u16();
                // Don't retry on 4xx client errors
                if status_code >= 400 && status_code < 500 {
                    log::warn!("[HTTP] GET {} - Client error (non-retryable): {}", url, status_code);
                    return Err(AppError::HttpStatus(status_code));
                }
                // Retry on 5xx server errors
                if attempt < self.config.max_retry_attempts {
                    log::warn!("[HTTP] GET {} - Server error {} (attempt {}), will retry", 
                        url, status_code, attempt + 1);
                    last_app_error = Some(AppError::HttpStatus(status_code));
                    continue;
                } else {
                    log::error!("[HTTP] GET {} - Server error after all retries: {}", url, status_code);
                    return Err(AppError::HttpStatus(status_code));
                }
            }

            match response.json().await {
                Ok(data) => {
                    log::debug!("[HTTP] GET {} - Successfully parsed JSON response", url);
                    return Ok(data);
                }
                Err(e) => {
                    // JSON parse errors are not retryable
                    log::error!("[HTTP] GET {} - JSON parse error: {}", url, e);
                    return Err(e.into());
                }
            }
        }
        
        // Should never reach here, but handle it gracefully
        Err(last_app_error.unwrap_or_else(|| {
            last_reqwest_error.map(|e| e.into()).unwrap_or_else(|| {
                AppError::HttpRequest("Request failed after all retry attempts".to_string())
            })
        }))
    }

    /// Generic POST request with retry logic
    ///
    /// Automatically retries on transient errors (timeout, connection) with exponential backoff.
    /// Does not retry on 4xx client errors.
    pub async fn post(&self, endpoint: &str) -> Result<(), AppError> {
        let url = self.config.api_endpoint(endpoint);
        log::debug!("[HTTP] POST request to: {}", url);

        let mut last_reqwest_error: Option<reqwest::Error> = None;
        let mut last_app_error: Option<AppError> = None;
        
        for attempt in 0..=self.config.max_retry_attempts {
            if attempt > 0 {
                let delay_ms = (self.config.retry_base_delay_ms as f64 
                    * self.config.retry_backoff_multiplier.powi(attempt as i32 - 1)) as u64;
                log::debug!("[HTTP] POST {} - Retry attempt {}/{} after {}ms delay", 
                    url, attempt, self.config.max_retry_attempts, delay_ms);
                tokio::time::sleep(Duration::from_millis(delay_ms)).await;
            }

            let start_time = std::time::Instant::now();
            let response_result = self.client.post(&url).send().await;
            
            let response = match response_result {
                Ok(resp) => {
                    let elapsed = start_time.elapsed();
                    log::debug!("[HTTP] POST {} - Response received in {:?}", url, elapsed);
                    resp
                }
                Err(e) => {
                    let elapsed = start_time.elapsed();
                    last_reqwest_error = Some(e);
                    
                    // Check if error is retryable (timeout or connection error)
                    let is_retryable = last_reqwest_error.as_ref().map(|err| {
                        err.is_timeout() || err.is_connect()
                    }).unwrap_or(false);
                    
                    if is_retryable && attempt < self.config.max_retry_attempts {
                        log::warn!("[HTTP] POST {} - Transient error after {:?} (attempt {}): {}", 
                            url, elapsed, attempt + 1, last_reqwest_error.as_ref().unwrap());
                        continue; // Retry
                    } else {
                        log::error!("[HTTP] POST {} - Request failed after {:?}: {}", url, elapsed, last_reqwest_error.as_ref().unwrap());
                        return Err(last_reqwest_error.unwrap().into());
                    }
                }
            };

            let status = response.status();
            log::debug!("[HTTP] POST {} - Status: {}", url, status);
            
            if !status.is_success() {
                let status_code = status.as_u16();
                // Don't retry on 4xx client errors
                if status_code >= 400 && status_code < 500 {
                    log::warn!("[HTTP] POST {} - Client error (non-retryable): {}", url, status_code);
                    return Err(AppError::HttpStatus(status_code));
                }
                // Retry on 5xx server errors
                if attempt < self.config.max_retry_attempts {
                    log::warn!("[HTTP] POST {} - Server error {} (attempt {}), will retry", 
                        url, status_code, attempt + 1);
                    last_app_error = Some(AppError::HttpStatus(status_code));
                    continue;
                } else {
                    log::error!("[HTTP] POST {} - Server error after all retries: {}", url, status_code);
                    return Err(AppError::HttpStatus(status_code));
                }
            }

            log::debug!("[HTTP] POST {} - Success", url);
            return Ok(());
        }
        
        // Should never reach here, but handle it gracefully
        Err(last_app_error.unwrap_or_else(|| {
            last_reqwest_error.map(|e| e.into()).unwrap_or_else(|| {
                AppError::HttpRequest("Request failed after all retry attempts".to_string())
            })
        }))
    }
}

/// Get a shared HTTP client instance
/// Uses OnceLock pattern - creates once, reuses
use std::sync::OnceLock;

static HTTP_CLIENT: OnceLock<Result<HttpClient, AppError>> = OnceLock::new();

pub fn get_client() -> Result<&'static HttpClient, AppError> {
    let result = HTTP_CLIENT.get_or_init(|| {
        log::debug!("[HTTP] Creating new HTTP client instance");
        let config = Config::new();
        HttpClient::new(config)
    });
    
    match result {
        Ok(client) => Ok(client),
        Err(e) => Err(e.clone()),
    }
}

