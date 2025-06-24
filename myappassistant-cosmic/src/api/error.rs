use thiserror::Error;

/// API client errors
#[derive(Error, Debug, Clone)]
pub enum ApiError {
    #[error("Network request failed: {0}")]
    RequestFailed(String),
    
    #[error("Failed to parse response: {0}")]
    ParseFailed(String),
    
    #[error("HTTP error: {0}")]
    HttpError(u16),
    
    #[error("Request timeout")]
    Timeout,
    
    #[error("Authentication failed")]
    AuthenticationFailed,
    
    #[error("Invalid request: {0}")]
    InvalidRequest(String),
}
