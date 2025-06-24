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
    
    /// Get food items from pantry
    pub async fn get_food_items(&self) -> Result<Vec<FoodItem>, ApiError> {
        let url = format!("{}/api/pantry/items", self.base_url);
        
        let response = self.http
            .get(&url)
            .send()
            .await
            .map_err(|e| ApiError::RequestFailed(e.to_string()))?;
            
        if response.status().is_success() {
            let items = response
                .json()
                .await
                .map_err(|e| ApiError::ParseFailed(e.to_string()))?;
            Ok(items)
        } else {
            Err(ApiError::HttpError(response.status().as_u16()))
        }
    }
    
    /// Send chat message to AI
    pub async fn send_chat_message(&self, message: &str, context: Option<String>) -> Result<ChatResponse, ApiError> {
        let url = format!("{}/api/chat", self.base_url);
        
        let request = ChatRequest {
            message: message.to_string(),
            context,
        };
        
        let response = self.http
            .post(&url)
            .json(&request)
            .send()
            .await
            .map_err(|e| ApiError::RequestFailed(e.to_string()))?;
            
        if response.status().is_success() {
            let chat_response = response
                .json()
                .await
                .map_err(|e| ApiError::ParseFailed(e.to_string()))?;
            Ok(chat_response)
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