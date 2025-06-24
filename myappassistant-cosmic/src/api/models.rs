use serde::{Deserialize, Serialize};
use chrono::{DateTime, Utc};

/// Food item from pantry
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FoodItem {
    pub id: String,
    pub name: String,
    pub category: String,
    pub expiration_date: Option<String>,
    pub quantity: i32,
}

/// Chat message request
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ChatRequest {
    pub prompt: String,
    pub model: Option<String>,
}

/// Memory chat request
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MemoryChatRequest {
    pub message: String,
    pub session_id: String,
    pub use_perplexity: Option<bool>,
    pub use_bielik: Option<bool>,
    pub agent_states: Option<std::collections::HashMap<String, bool>>,
}

/// Chat message response
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ChatResponse {
    pub response: String,
    pub model: String,
}

/// Chat message
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ChatMessage {
    pub content: String,
    pub is_user: bool,
    pub timestamp: DateTime<Utc>,
    pub agent: Option<String>,
}

/// OCR result from receipt
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OCRResult {
    pub items: Vec<OCRItem>,
    pub total: f32,
    pub store_name: Option<String>,
    pub date: Option<String>,
}

/// OCR detected item
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OCRItem {
    pub name: String,
    pub quantity: f32,
    pub price: f32,
    pub category: Option<String>,
}

/// Weather data
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WeatherData {
    pub temperature: f32,
    pub description: String,
    pub humidity: i32,
    pub wind_speed: f32,
    pub location: String,
}

/// Pantry product
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PantryProduct {
    pub id: i32,
    pub name: String,
    pub unified_category: String,
}
