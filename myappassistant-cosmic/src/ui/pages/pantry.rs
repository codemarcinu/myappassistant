use cosmic::widget::{self, card, column, container, row, text, text_input, button, scrollable};
use cosmic::{Element, app};
use cosmic::iced::{Alignment, Length};

use crate::api::models::FoodItem;
use crate::api::Client;
use crate::core::Message;

/// Pantry state
#[derive(Debug, Clone, Default)]
pub struct State {
    /// Food items
    pub items: Vec<FoodItem>,
    
    /// Filter text
    pub filter_text: String,
    
    /// Loading state
    pub loading: bool,
}

/// Pantry messages
#[derive(Debug, Clone)]
pub enum PantryMessage {
    /// Items loaded
    ItemsLoaded(Vec<FoodItem>),
    
    /// Load items
    LoadItems,
    
    /// Filter text changed
    FilterChanged(String),
    
    /// Add item
    AddItem(FoodItem),
    
    /// Remove item
    RemoveItem(String),
}

/// Update pantry state
pub fn update(state: &mut State, message: PantryMessage, api_client: &Client) -> app::Command<PantryMessage> {
    match message {
        PantryMessage::ItemsLoaded(items) => {
            state.items = items;
            state.loading = false;
            app::Command::none()
        }
        
        PantryMessage::LoadItems => {
            state.loading = true;
            
            let client = api_client.clone();
            app::Command::perform(
                async move { client.get_food_items().await },
                |result| match result {
                    Ok(items) => PantryMessage::ItemsLoaded(items),
                    Err(_) => PantryMessage::ItemsLoaded(vec![]),
                }
            )
        }
        
        PantryMessage::FilterChanged(text) => {
            state.filter_text = text;
            app::Command::none()
        }
        
        PantryMessage::AddItem(_) => {
            // This would be implemented in a more complete version
            app::Command::none()
        }
        
        PantryMessage::RemoveItem(_) => {
            // This would be implemented in a more complete version
            app::Command::none()
        }
    }
}

/// Render pantry view
pub fn view(state: &State) -> Element<Message> {
    let title = widget::text::title1("Pantry")
        .size(32);
    
    // Filter
    let filter = text_input("Filter items...", &state.filter_text)
        .on_input(|text| Message::Pantry(PantryMessage::FilterChanged(text)))
        .padding(10);
    
    // Refresh button
    let refresh_button = button::standard("Refresh")
        .on_press(Message::Pantry(PantryMessage::LoadItems))
        .padding(10);
    
    let filter_row = row![
        filter,
        refresh_button,
    ]
    .spacing(10)
    .align_items(Alignment::Center);
    
    // Food items
    let filtered_items = if state.filter_text.is_empty() {
        state.items.clone()
    } else {
        state.items
            .iter()
            .filter(|item| {
                item.name.to_lowercase().contains(&state.filter_text.to_lowercase()) ||
                item.category.to_lowercase().contains(&state.filter_text.to_lowercase())
            })
            .cloned()
            .collect()
    };
    
    let items_view = if state.loading {
        column![text::body("Loading items...")].into()
    } else if filtered_items.is_empty() {
        column![text::body("No items found.")].into()
    } else {
        scrollable(
            column(
                filtered_items
                    .iter()
                    .map(|item| {
                        let expiration = item.expiration_date
                            .as_deref()
                            .unwrap_or("No expiration date");
                            
                        card::Card::new(
                            text::title4(&item.name),
                            column![
                                text::body(&format!("Category: {}", item.category)),
                                text::body(&format!("Expiration: {}", expiration)),
                                text::body(&format!("Quantity: {}", item.quantity)),
                            ]
                        )
                    })
                    .collect()
            )
            .spacing(10)
        )
        .height(Length::Fill)
        .into()
    };
    
    // Main content
    container(
        column![
            title,
            filter_row,
            items_view,
        ]
        .spacing(16)
    )
    .padding(16)
    .width(Length::Fill)
    .height(Length::Fill)
    .into()
} 