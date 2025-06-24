use crate::config::AppSettings;
use crate::ui::pages::{
    dashboard, 
    chat, 
    pantry, 
    ocr, 
    settings
};

/// Main application message enum
#[derive(Debug, Clone)]
pub enum Message {
    // Navigation messages
    NavigateTo(Page),
    
    // Dashboard messages
    Dashboard(dashboard::DashboardMessage),
    
    // Chat messages
    Chat(chat::ChatMessage),
    
    // Pantry messages
    Pantry(pantry::PantryMessage),
    
    // OCR messages
    OCR(ocr::OCRMessage),
    
    // Settings messages
    Settings(settings::SettingsMessage),
    
    // Config messages
    Config(AppSettings),
    
    // Window messages
    Close,
    Minimize,
    
    // Error handling
    Error(String),
}

/// Application pages
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Page {
    Dashboard,
    Chat,
    Pantry,
    OCR,
    Settings,
} 