use cosmic::widget::{self, card, column, container, row, text, button, scrollable};
use cosmic::{Element, app};
use cosmic::iced::{Alignment, Length};
use std::path::PathBuf;

use crate::api::models::{OCRResult, OCRItem};
use crate::api::Client;
use crate::core::Message;

/// OCR state
#[derive(Debug, Clone, Default)]
pub struct State {
    /// OCR result
    pub result: Option<OCRResult>,
    
    /// Selected image path
    pub image_path: Option<PathBuf>,
    
    /// Loading state
    pub loading: bool,
    
    /// Error message
    pub error: Option<String>,
}

/// OCR messages
#[derive(Debug, Clone)]
pub enum OCRMessage {
    /// Open camera
    OpenCamera,
    
    /// Select image
    SelectImage,
    
    /// Image selected
    ImageSelected(PathBuf),
    
    /// Process image
    ProcessImage(Vec<u8>),
    
    /// OCR result received
    ResultReceived(OCRResult),
    
    /// Error occurred
    Error(String),
}

/// Update OCR state
pub fn update(state: &mut State, message: OCRMessage, api_client: &Client) -> app::Command<OCRMessage> {
    match message {
        OCRMessage::OpenCamera => {
            // This would be implemented in a more complete version
            // For now, just show an error
            state.error = Some("Camera functionality not implemented yet.".to_string());
            app::Command::none()
        }
        
        OCRMessage::SelectImage => {
            // This would open a file picker in a real implementation
            // For now, just show an error
            state.error = Some("File picker not implemented yet.".to_string());
            app::Command::none()
        }
        
        OCRMessage::ImageSelected(path) => {
            state.image_path = Some(path.clone());
            
            // In a real implementation, we would read the file and send it to the API
            // For now, just show a dummy result
            app::Command::perform(
                async move { 
                    // Placeholder for reading the file
                    vec![]
                },
                OCRMessage::ProcessImage
            )
        }
        
        OCRMessage::ProcessImage(image_data) => {
            state.loading = true;
            state.error = None;
            
            let client = api_client.clone();
            app::Command::perform(
                async move { client.upload_receipt(image_data).await },
                |result| match result {
                    Ok(ocr_result) => OCRMessage::ResultReceived(ocr_result),
                    Err(e) => OCRMessage::Error(e.to_string()),
                }
            )
        }
        
        OCRMessage::ResultReceived(result) => {
            state.result = Some(result);
            state.loading = false;
            app::Command::none()
        }
        
        OCRMessage::Error(error) => {
            state.error = Some(error);
            state.loading = false;
            app::Command::none()
        }
    }
}

/// Render OCR view
pub fn view(state: &State) -> Element<Message> {
    let title = widget::text::title1("Receipt Scanner")
        .size(32);
    
    // Action buttons
    let camera_button = button::standard("Open Camera")
        .on_press(Message::OCR(OCRMessage::OpenCamera))
        .padding(10);
    
    let file_button = button::standard("Select Image")
        .on_press(Message::OCR(OCRMessage::SelectImage))
        .padding(10);
    
    let action_row = row![
        camera_button,
        file_button,
    ]
    .spacing(10)
    .align_items(Alignment::Center);
    
    // Error message
    let error_view = if let Some(error) = &state.error {
        container(
            text::body(error)
                .style(cosmic::iced::Color::from_rgb(0.8, 0.0, 0.0))
        )
        .padding(10)
        .into()
    } else {
        widget::column![].into()
    };
    
    // Selected image
    let image_view = if let Some(path) = &state.image_path {
        container(
            text::body(&format!("Selected image: {}", path.display()))
        )
        .padding(10)
        .into()
    } else {
        widget::column![].into()
    };
    
    // OCR result
    let result_view = if state.loading {
        container(
            text::body("Processing receipt...")
        )
        .padding(10)
        .into()
    } else if let Some(result) = &state.result {
        let store = result.store_name
            .as_deref()
            .unwrap_or("Unknown store");
            
        let date = result.date
            .as_deref()
            .unwrap_or("Unknown date");
            
        let header = column![
            text::title3(&format!("Store: {}", store)),
            text::title4(&format!("Date: {}", date)),
            text::title4(&format!("Total: ${:.2}", result.total)),
        ]
        .spacing(5);
        
        let items = scrollable(
            column(
                result.items
                    .iter()
                    .map(|item| {
                        let category = item.category
                            .as_deref()
                            .unwrap_or("Uncategorized");
                            
                        card::Card::new(
                            text::title4(&item.name),
                            column![
                                text::body(&format!("Price: ${:.2}", item.price)),
                                text::body(&format!("Quantity: {}", item.quantity)),
                                text::body(&format!("Category: {}", category)),
                            ]
                        )
                    })
                    .collect()
            )
            .spacing(10)
        )
        .height(Length::Fill);
        
        container(
            column![
                header,
                items,
            ]
            .spacing(10)
        )
        .padding(10)
        .into()
    } else {
        container(
            text::body("No receipt scanned yet.")
        )
        .padding(10)
        .into()
    };
    
    // Main content
    container(
        column![
            title,
            action_row,
            error_view,
            image_view,
            result_view,
        ]
        .spacing(16)
    )
    .padding(16)
    .width(Length::Fill)
    .height(Length::Fill)
    .into()
} 