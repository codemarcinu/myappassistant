mod api;

use iced::widget::{button, column, container, row, text, text_input};
use iced::{Alignment, Element, Sandbox, Settings, Length, Color, Background, Theme, BorderRadius};
use api::Client;

fn main() -> iced::Result {
    println!("Uruchamianie MyAppAssistant GUI...");
    
    MyAppAssistant::run(Settings::default())
}

struct MyAppAssistant {
    input_value: String,
    messages: Vec<(String, String)>, // (agent, message)
    api_client: Client,
}

#[derive(Debug, Clone)]
enum Message {
    InputChanged(String),
    SendMessage,
}

// Definiujemy własne style dla kontenerów
#[derive(Debug, Clone, Copy)]
enum ContainerStyle {
    User,
    Assistant,
}

impl container::StyleSheet for ContainerStyle {
    type Style = Theme;

    fn appearance(&self, _style: &Self::Style) -> container::Appearance {
        match self {
            ContainerStyle::User => container::Appearance {
                background: Some(Background::Color(Color::from_rgb(0.9, 0.9, 1.0))),
                border_radius: BorderRadius::from(5.0),
                border_width: 1.0,
                border_color: Color::from_rgb(0.7, 0.7, 0.9),
                text_color: None,
            },
            ContainerStyle::Assistant => container::Appearance {
                background: Some(Background::Color(Color::from_rgb(0.9, 1.0, 0.9))),
                border_radius: BorderRadius::from(5.0),
                border_width: 1.0,
                border_color: Color::from_rgb(0.7, 0.9, 0.7),
                text_color: None,
            },
        }
    }
}

impl From<ContainerStyle> for iced::theme::Container {
    fn from(style: ContainerStyle) -> Self {
        iced::theme::Container::Custom(Box::new(style))
    }
}

impl Sandbox for MyAppAssistant {
    type Message = Message;

    fn new() -> Self {
        Self {
            input_value: String::new(),
            messages: vec![
                ("System".to_string(), "Witaj w MyAppAssistant! Jak mogę Ci pomóc?".to_string()),
            ],
            api_client: Client::new("http://localhost:8000"),
        }
    }

    fn title(&self) -> String {
        String::from("MyAppAssistant")
    }

    fn update(&mut self, message: Message) {
        match message {
            Message::InputChanged(value) => {
                self.input_value = value;
            }
            Message::SendMessage => {
                if !self.input_value.is_empty() {
                    // Dodaj wiadomość użytkownika
                    self.messages.push(("Ty".to_string(), self.input_value.clone()));
                    
                    // Symulacja odpowiedzi (w rzeczywistej aplikacji byłoby wywołanie API)
                    let response = if self.input_value.to_lowercase().contains("pogoda") {
                        ("WeatherAgent".to_string(), "Obecnie jest słonecznie i 25°C na zewnątrz.".to_string())
                    } else if self.input_value.to_lowercase().contains("przepis") 
                        || self.input_value.to_lowercase().contains("jedzenie") {
                        ("ChefAgent".to_string(), "Znalazłem świetny przepis na makaron dla Ciebie!".to_string())
                    } else {
                        ("GeneralAgent".to_string(), format!("Otrzymałem Twoją wiadomość: {}", self.input_value))
                    };
                    
                    // Dodaj odpowiedź asystenta
                    self.messages.push(response);
                    
                    // Wyczyść pole wejściowe
                    self.input_value = String::new();
                    
                    // TODO: W przyszłości użyj API client do wysłania wiadomości
                    // Przykład:
                    // let response = self.api_client.send_chat_message(&self.input_value, None).await;
                }
            }
        }
    }

    fn view(&self) -> Element<Message> {
        let title = text("MyAppAssistant")
            .size(30)
            .width(Length::Fill)
            .horizontal_alignment(iced::alignment::Horizontal::Center);
            
        // Wiadomości
        let messages = self.messages.iter().fold(
            column![].spacing(10).padding(20),
            |column, (agent, message)| {
                column.push(
                    container(
                        column![
                            text(agent).size(14),
                            text(message).size(16)
                        ]
                        .spacing(5)
                    )
                    .padding(10)
                    .style(iced::theme::Container::Custom(Box::new(
                        if agent == "Ty" {
                            ContainerStyle::User
                        } else {
                            ContainerStyle::Assistant
                        }
                    )))
                    .width(Length::Fill)
                )
            }
        );
        
        // Pole wejściowe i przycisk wysyłania
        let input = row![
            text_input("Wpisz wiadomość...", &self.input_value)
                .on_input(Message::InputChanged)
                .on_submit(Message::SendMessage)
                .padding(10)
                .width(Length::Fill),
            button("Wyślij")
                .on_press(Message::SendMessage)
                .padding(10)
        ]
        .spacing(10)
        .padding(20)
        .width(Length::Fill);
        
        // Główny układ
        container(
            column![
                title,
                messages,
                input
            ]
            .spacing(20)
            .align_items(Alignment::Center)
        )
        .width(Length::Fill)
        .height(Length::Fill)
        .center_x()
        .into()
    }
}
