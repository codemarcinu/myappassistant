use chrono::{DateTime, NaiveDate, Utc};
use std::path::PathBuf;

/// Format a date string in a user-friendly way
pub fn format_date(date_str: &str) -> String {
    if let Ok(date) = NaiveDate::parse_from_str(date_str, "%Y-%m-%d") {
        date.format("%d %b %Y").to_string()
    } else {
        date_str.to_string()
    }
}

/// Check if a date is expired
pub fn is_expired(date_str: &str) -> bool {
    if let Ok(date) = NaiveDate::parse_from_str(date_str, "%Y-%m-%d") {
        let today = Utc::now().date_naive();
        date < today
    } else {
        false
    }
}

/// Create directory if it doesn't exist
pub fn ensure_directory(path: &PathBuf) -> std::io::Result<()> {
    if !path.exists() {
        std::fs::create_dir_all(path)?;
    }
    Ok(())
}

/// Get file extension from a path
pub fn get_file_extension(path: &PathBuf) -> Option<String> {
    path.extension()
        .and_then(|ext| ext.to_str())
        .map(|ext| ext.to_string())
} 