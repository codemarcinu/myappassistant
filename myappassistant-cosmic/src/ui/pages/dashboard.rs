use cosmic::widget::{self, card, column, container, row, text, button};
use cosmic::{Element, app};
use cosmic::iced::{Alignment, Length};

use crate::api::models::WeatherData;
use crate::api::Client;
use crate::core::Message;

/// Dashboard state
#[derive(Debug, Clone, Default)]
pub struct State {
    /// Weather data
    pub weather: Option<WeatherData>,
    
    /// Recent activities
    pub recent_activities: Vec<String>,
    
    /// Loading state
    pub loading: bool,
}

/// Dashboard messages
#[derive(Debug, Clone)]
pub enum DashboardMessage {
    /// Weather data loaded
    WeatherLoaded(WeatherData),
    
    /// Refresh weather data
    RefreshWeather,
    
    /// Navigate to page
    NavigateToPage(crate::core::messages::Page),
}

/// Update dashboard state
pub fn update(state: &mut State, message: DashboardMessage, api_client: &Client) -> app::Command<DashboardMessage> {
    match message {
        DashboardMessage::WeatherLoaded(weather) => {
            state.weather = Some(weather);
            state.loading = false;
            app::Command::none()
        }
        
        DashboardMessage::RefreshWeather => {
            state.loading = true;
            
            let client = api_client.clone();
            app::Command::perform(
                async move { client.get_weather().await },
                |result| match result {
                    Ok(weather) => DashboardMessage::WeatherLoaded(weather),
                    Err(_) => DashboardMessage::RefreshWeather,
                }
            )
        }
        
        DashboardMessage::NavigateToPage(_) => {
            // This will be handled by the parent
            app::Command::none()
        }
    }
}

/// Render dashboard view
pub fn view(state: &State) -> Element<Message> {
    let title = widget::text::title1("Dashboard")
        .size(32);
    
    // Weather card
    let weather_card = if let Some(weather) = &state.weather {
        card::Card::new(
            text::title4("Weather"),
            column![
                text::body(&format!("{}°C - {}", weather.temperature, weather.description)),
                text::body(&format!("Humidity: {}%", weather.humidity)),
                text::body(&format!("Wind: {} km/h", weather.wind_speed)),
                text::body(&format!("Location: {}", weather.location)),
            ].spacing(5)
        )
    } else if state.loading {
        card::Card::new(
            text::title4("Weather"),
            text::body("Loading weather data...")
        )
    } else {
        card::Card::new(
            text::title4("Weather"),
            column![
                text::body("Weather data unavailable"),
                button::standard("Refresh")
                    .on_press(Message::Dashboard(DashboardMessage::RefreshWeather))
            ]
        )
    };
    
    // Quick actions
    let quick_actions = card::Card::new(
        text::title4("Quick Actions"),
        column![
            button::standard("Check Pantry")
                .on_press(Message::NavigateTo(crate::core::messages::Page::Pantry)),
            button::standard("Scan Receipt")
                .on_press(Message::NavigateTo(crate::core::messages::Page::OCR)),
            button::standard("Chat with AI")
                .on_press(Message::NavigateTo(crate::core::messages::Page::Chat)),
        ].spacing(8)
    );
    
    // Recent activities
    let activities = if state.recent_activities.is_empty() {
        text::body("No recent activities")
    } else {
        column(
            state.recent_activities
                .iter()
                .map(|activity| text::body(activity))
                .collect()
        )
        .spacing(5)
        .into()
    };
    
    let recent_activities = card::Card::new(
        text::title4("Recent Activities"),
        activities
    );
    
    // Main content
    container(
        column![
            title,
            row![
                weather_card,
                quick_actions,
            ].spacing(16),
            recent_activities,
        ]
        .spacing(16)
    )
    .padding(16)
    .width(Length::Fill)
    .height(Length::Fill)
    .into()
} 