use reqwest::{Client as HttpClient, StatusCode};
use std::time::Duration;
use anyhow::Result;

use crate::api::error::ApiError;
use crate::api::models::*;

/// API client for backend communication
#[derive(Clone)]
pub struct Client {
    http: HttpClient,
    base_url: String,
}

impl Client {
    /// Create a new API client
    pub fn new(base_url: &str) -> Self {
        let http = HttpClient::builder()
            .timeout(Duration::from_secs(30))
            .build()
            .expect("Failed to create HTTP client");
            
        Self {
            http,
            base_url: base_url.to_string(),
        }
    }
    
    /// Get pantry products
    pub async fn get_pantry_products(&self) -> Result<Vec<PantryProduct>, ApiError> {
        let url = format!("{}/api/pantry/products", self.base_url);
        
        let response = self.http
            .get(&url)
            .send()
            .await
            .map_err(|e| ApiError::RequestFailed(e.to_string()))?;
            
        if response.status().is_success() {
            let products = response
                .json()
                .await
                .map_err(|e| ApiError::ParseFailed(e.to_string()))?;
            Ok(products)
        } else {
            Err(ApiError::HttpError(response.status().as_u16()))
        }
    }
    
    /// Send chat message to AI
    pub async fn send_chat_message(&self, prompt: &str, model: Option<&str>) -> Result<String, ApiError> {
        let url = format!("{}/api/chat", self.base_url);
        
        let request = ChatRequest {
            prompt: prompt.to_string(),
            model: model.map(|s| s.to_string()),
        };
        
        let response = self.http
            .post(&url)
            .json(&request)
            .send()
            .await
            .map_err(|e| ApiError::RequestFailed(e.to_string()))?;
            
        if response.status().is_success() {
            // This is a streaming response, so we need to read it as text
            let text = response
                .text()
                .await
                .map_err(|e| ApiError::ParseFailed(e.to_string()))?;
            Ok(text)
        } else {
            Err(ApiError::HttpError(response.status().as_u16()))
        }
    }
    
    /// Send memory chat message
    pub async fn send_memory_chat_message(
        &self, 
        message: &str, 
        session_id: &str,
        use_perplexity: Option<bool>,
        use_bielik: Option<bool>,
    ) -> Result<String, ApiError> {
        let url = format!("{}/api/memory_chat", self.base_url);
        
        let request = MemoryChatRequest {
            message: message.to_string(),
            session_id: session_id.to_string(),
            use_perplexity,
            use_bielik,
            agent_states: None,
        };
        
        let response = self.http
            .post(&url)
            .json(&request)
            .send()
            .await
            .map_err(|e| ApiError::RequestFailed(e.to_string()))?;
            
        if response.status().is_success() {
            // This is a streaming response, so we need to read it as text
            let text = response
                .text()
                .await
                .map_err(|e| ApiError::ParseFailed(e.to_string()))?;
            Ok(text)
        } else {
            Err(ApiError::HttpError(response.status().as_u16()))
        }
    }
    
    /// Upload receipt image for OCR
    pub async fn upload_receipt(&self, image_data: Vec<u8>) -> Result<OCRResult, ApiError> {
        let url = format!("{}/api/ocr", self.base_url);
        
        let form = reqwest::multipart::Form::new()
            .part("file", reqwest::multipart::Part::bytes(image_data)
                .file_name("receipt.jpg")
                .mime_str("image/jpeg")
                .unwrap());
        
        let response = self.http
            .post(&url)
            .multipart(form)
            .send()
            .await
            .map_err(|e| ApiError::RequestFailed(e.to_string()))?;
            
        if response.status().is_success() {
            let ocr_result = response
                .json()
                .await
                .map_err(|e| ApiError::ParseFailed(e.to_string()))?;
            Ok(ocr_result)
        } else {
            Err(ApiError::HttpError(response.status().as_u16()))
        }
    }
    
    /// Get weather data
    pub async fn get_weather(&self) -> Result<WeatherData, ApiError> {
        let url = format!("{}/api/weather", self.base_url);
        
        let response = self.http
            .get(&url)
            .send()
            .await
            .map_err(|e| ApiError::RequestFailed(e.to_string()))?;
            
        if response.status().is_success() {
            let weather = response
                .json()
                .await
                .map_err(|e| ApiError::ParseFailed(e.to_string()))?;
            Ok(weather)
        } else {
            Err(ApiError::HttpError(response.status().as_u16()))
        }
    }
}
