use cosmic::widget::{self, card, column, container, row, text, text_input, button, scrollable};
use cosmic::{Element, app};
use cosmic::iced::{Alignment, Length};
use chrono::Utc;

use crate::api::models::{ChatMessage as ApiChatMessage, ChatResponse};
use crate::api::Client;
use crate::core::Message;

/// Chat state
#[derive(Debug, Clone, Default)]
pub struct State {
    /// Chat input text
    pub input_text: String,
    
    /// Chat messages
    pub messages: Vec<ApiChatMessage>,
    
    /// Loading state
    pub loading: bool,
}

/// Chat messages
#[derive(Debug, Clone)]
pub enum ChatMessage {
    /// Input text changed
    InputChanged(String),
    
    /// Send message
    SendMessage,
    
    /// Message response received
    MessageReceived(ChatResponse),
    
    /// Focus input
    FocusInput,
    
    /// Clear chat
    ClearChat,
}

/// Update chat state
pub fn update(state: &mut State, message: ChatMessage, api_client: &Client) -> app::Command<ChatMessage> {
    match message {
        ChatMessage::InputChanged(text) => {
            state.input_text = text;
            app::Command::none()
        }
        
        ChatMessage::SendMessage => {
            if state.input_text.trim().is_empty() || state.loading {
                return app::Command::none();
            }
            
            // Add user message to chat
            let user_message = ApiChatMessage {
                content: state.input_text.clone(),
                is_user: true,
                timestamp: Utc::now(),
                agent: None,
            };
            
            state.messages.push(user_message);
            state.loading = true;
            
            // Clear input
            let message_text = std::mem::take(&mut state.input_text);
            
            // Get context from previous messages (last 5)
            let context = if state.messages.len() > 1 {
                let context_messages = state.messages
                    .iter()
                    .rev()
                    .take(5)
                    .collect::<Vec<_>>()
                    .into_iter()
                    .rev()
                    .map(|msg| {
                        if msg.is_user {
                            format!("User: {}", msg.content)
                        } else {
                            format!("Assistant: {}", msg.content)
                        }
                    })
                    .collect::<Vec<_>>()
                    .join("\n");
                
                Some(context_messages)
            } else {
                None
            };
            
            // Send message to API
            let client = api_client.clone();
            app::Command::perform(
                async move { client.send_chat_message(&message_text, context).await },
                |result| match result {
                    Ok(response) => ChatMessage::MessageReceived(response),
                    Err(e) => {
                        // Return error as a fake response
                        ChatMessage::MessageReceived(ChatResponse {
                            response: format!("Error: {}", e),
                            agent_used: "error".to_string(),
                            confidence: 0.0,
                        })
                    }
                }
            )
        }
        
        ChatMessage::MessageReceived(response) => {
            // Add assistant message to chat
            let assistant_message = ApiChatMessage {
                content: response.response,
                is_user: false,
                timestamp: Utc::now(),
                agent: Some(response.agent_used),
            };
            
            state.messages.push(assistant_message);
            state.loading = false;
            
            app::Command::none()
        }
        
        ChatMessage::FocusInput => {
            // This would require focus management, which is not implemented here
            app::Command::none()
        }
        
        ChatMessage::ClearChat => {
            state.messages.clear();
            app::Command::none()
        }
    }
}

/// Render chat view
pub fn view(state: &State) -> Element<Message> {
    let title = widget::text::title1("Chat with AI")
        .size(32);
    
    // Chat messages
    let messages = scrollable(
        column(
            state.messages
                .iter()
                .map(|msg| {
                    let message_card = if msg.is_user {
                        // User message (right-aligned)
                        card::Card::new(
                            text::title4("You"),
                            text::body(&msg.content)
                        )
                        .style(cosmic::theme::Button::Suggested)
                    } else {
                        // Assistant message (left-aligned)
                        card::Card::new(
                            text::title4(msg.agent.as_deref().unwrap_or("Assistant")),
                            text::body(&msg.content)
                        )
                    };
                    
                    container(message_card)
                        .width(Length::Fill)
                        .align_x(if msg.is_user {
                            Alignment::End
                        } else {
                            Alignment::Start
                        })
                })
                .collect()
        )
        .spacing(10)
        .padding(10)
    )
    .height(Length::Fill);
    
    // Input area
    let input = text_input("Type your message...", &state.input_text)
        .on_input(|text| Message::Chat(ChatMessage::InputChanged(text)))
        .on_submit(Message::Chat(ChatMessage::SendMessage))
        .padding(10);
    
    let send_button = button::standard("Send")
        .on_press(Message::Chat(ChatMessage::SendMessage))
        .padding(10);
    
    let clear_button = button::standard("Clear")
        .on_press(Message::Chat(ChatMessage::ClearChat))
        .padding(10);
    
    let input_row = row![
        input,
        send_button,
        clear_button,
    ]
    .spacing(10)
    .align_items(Alignment::Center);
    
    // Loading indicator
    let status = if state.loading {
        text::body("Assistant is typing...")
    } else {
        text::body("")
    };
    
    // Main content
    container(
        column![
            title,
            messages,
            status,
            input_row,
        ]
        .spacing(16)
    )
    .padding(16)
    .width(Length::Fill)
    .height(Length::Fill)
    .into()
} 