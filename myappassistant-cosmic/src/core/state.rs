use std::collections::HashMap;
use crate::config::AppSettings;
use crate::core::messages::Page;
use crate::ui::pages::{
    dashboard, 
    chat, 
    pantry, 
    ocr, 
    settings
};

/// Main application state
#[derive(Debug, Clone)]
pub struct AppState {
    /// Current active page
    pub current_page: Page,
    
    /// Application settings
    pub settings: AppSettings,
    
    /// Loading states for different operations
    pub loading_states: HashMap<String, bool>,
    
    /// Error state
    pub error_state: Option<String>,
    
    /// Dashboard state
    pub dashboard_state: dashboard::State,
    
    /// Chat state
    pub chat_state: chat::State,
    
    /// Pantry state
    pub pantry_state: pantry::State,
    
    /// OCR state
    pub ocr_state: ocr::State,
    
    /// Settings state
    pub settings_state: settings::State,
}

impl Default for AppState {
    fn default() -> Self {
        Self {
            current_page: Page::Dashboard,
            settings: AppSettings::default(),
            loading_states: HashMap::new(),
            error_state: None,
            dashboard_state: dashboard::State::default(),
            chat_state: chat::State::default(),
            pantry_state: pantry::State::default(),
            ocr_state: ocr::State::default(),
            settings_state: settings::State::default(),
        }
    }
} 