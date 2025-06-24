use cosmic::cosmic_config::{Config, CosmicConfigEntry};
use serde::{Deserialize, Serialize};
use std::path::PathBuf;

/// Theme mode for the application
#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
pub enum ThemeMode {
    Light,
    Dark,
    System,
}

/// Application settings
#[derive(Debug, Clone, Serialize, Deserialize, CosmicConfigEntry)]
pub struct AppSettings {
    /// Backend API URL
    pub backend_url: String,
    
    /// Theme mode
    pub theme_mode: ThemeMode,
    
    /// Enable notifications
    pub notifications_enabled: bool,
    
    /// Auto-sync data with backend
    pub auto_sync: bool,
    
    /// OCR upload directory
    pub ocr_upload_dir: PathBuf,
}

impl Default for AppSettings {
    fn default() -> Self {
        Self {
            backend_url: "http://localhost:8000".to_string(),
            theme_mode: ThemeMode::System,
            notifications_enabled: true,
            auto_sync: true,
            ocr_upload_dir: PathBuf::from("/tmp/myappassistant/ocr"),
        }
    }
}

impl AppSettings {
    /// Load settings from config
    pub fn load() -> anyhow::Result<Self> {
        let config = cosmic::cosmic_config::Config::new(
            "com.github.codemarcinu.myappassistant", 
            cosmic::cosmic_config::VERSION
        )?;
        
        let settings = config.get::<AppSettings>()?;
        Ok(settings)
    }
    
    /// Save settings to config
    pub fn save(&self) -> anyhow::Result<()> {
        let config = cosmic::cosmic_config::Config::new(
            "com.github.codemarcinu.myappassistant", 
            cosmic::cosmic_config::VERSION
        )?;
        
        config.set::<AppSettings>(self)?;
        Ok(())
    }
} 