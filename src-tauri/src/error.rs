//! Error types for the Tauri application
//!
//! Provides a unified error type that implements `std::error::Error`
//! and can be converted from common error types (reqwest, serde, io).
//!
//! # Example
//!
//! ```rust,no_run
//! use crate::error::AppError;
//!
//! fn example() -> Result<(), AppError> {
//!     // Errors automatically convert to AppError
//!     let client = get_client()?;
//!     let data = client.get::<Data>("/api/endpoint").await?;
//!     Ok(())
//! }
//! ```

use std::fmt;
use serde::{Serialize, Deserialize};

/// Unified error type for the Tauri application
///
/// All Tauri commands return `Result<T, AppError>` to provide consistent
/// error handling and user-friendly error messages.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum AppError {
    /// HTTP request failed (network error, timeout, connection refused)
    HttpRequest(String),
    /// Failed to parse JSON response from the backend
    JsonParse(String),
    /// Invalid HTTP response status code (4xx, 5xx)
    HttpStatus(u16),
    /// System/OS operation failed (file operations, process spawning)
    System(String),
    /// Configuration error (invalid settings, missing environment variables)
    Config(String),
    /// Generic error with message
    Other(String),
}

impl fmt::Display for AppError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            AppError::HttpRequest(msg) => write!(f, "HTTP request failed: {}", msg),
            AppError::JsonParse(msg) => write!(f, "Failed to parse JSON: {}", msg),
            AppError::HttpStatus(code) => write!(f, "HTTP error status: {}", code),
            AppError::System(msg) => write!(f, "System error: {}", msg),
            AppError::Config(msg) => write!(f, "Configuration error: {}", msg),
            AppError::Other(msg) => write!(f, "Error: {}", msg),
        }
    }
}

impl std::error::Error for AppError {}

impl From<reqwest::Error> for AppError {
    fn from(err: reqwest::Error) -> Self {
        if err.is_timeout() {
            AppError::HttpRequest(format!("Request timeout - the server took too long to respond. Please check your connection and try again."))
        } else if err.is_connect() {
            AppError::HttpRequest(format!("Connection failed - unable to reach the backend server. Please ensure the backend is running at the configured API URL."))
        } else if err.is_decode() {
            AppError::HttpRequest(format!("Invalid response format - the server returned data in an unexpected format."))
        } else {
            AppError::HttpRequest(format!("Network error: {}", err))
        }
    }
}

impl From<serde_json::Error> for AppError {
    fn from(err: serde_json::Error) -> Self {
        AppError::JsonParse(err.to_string())
    }
}

impl From<std::io::Error> for AppError {
    fn from(err: std::io::Error) -> Self {
        AppError::System(err.to_string())
    }
}

