use thiserror::Error;
use std::io;

/// Application errors
#[derive(Error, Debug)]
pub enum AppError {
    #[error("IO error: {0}")]
    IoError(#[from] io::Error),
    
    #[error("API error: {0}")]
    ApiError(#[from] crate::api::ApiError),
    
    #[error("Configuration error: {0}")]
    ConfigError(String),
    
    #[error("Parsing error: {0}")]
    ParseError(String),
    
    #[error("Unknown error: {0}")]
    Unknown(String),
}

/// Result type for application operations
pub type AppResult<T> = Result<T, AppError>; 