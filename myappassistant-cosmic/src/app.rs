use cosmic::{app, cosmic_config, cosmic_theme, Application, ApplicationExt, Element};
use cosmic::iced::{Alignment, Length, Subscription};
use cosmic::widget::{self, nav_bar};
use tracing::{info, error};

use crate::config::AppSettings;
use crate::core::{Message, Flags, AppState, messages::Page};
use crate::core::theme;
use crate::api::Client;

/// Main application struct
pub struct MyAppAssistant {
    /// Core application state
    core: app::Core,
    
    /// Navigation bar model
    nav: nav_bar::Model,
    
    /// Application state
    state: AppState,
    
    /// API client
    api_client: Client,
}

impl Application for MyAppAssistant {
    type Executor = cosmic::executor::Default;
    type Flags = Flags;
    type Message = Message;
    const APP_ID: &'static str = "com.github.codemarcinu.myappassistant";

    fn core(&self) -> &app::Core {
        &self.core
    }

    fn core_mut(&mut self) -> &mut app::Core {
        &mut self.core
    }

    fn init(core: app::Core, flags: Self::Flags) -> (Self, app::Command<Self::Message>) {
        // Initialize navigation
        let mut nav = nav_bar::Model::default();
        nav.add_item("dashboard", "Dashboard");
        nav.add_item("chat", "Chat");
        nav.add_item("pantry", "Pantry");
        nav.add_item("ocr", "OCR");
        nav.add_item("settings", "Settings");
        nav.activate("dashboard");
        
        // Load settings or use defaults
        let settings = AppSettings::load().unwrap_or_default();
        
        // Create API client
        let api_client = Client::new(&settings.backend_url);
        
        // Create application state
        let state = AppState::default();
        
        let app = MyAppAssistant {
            core,
            nav,
            state,
            api_client,
        };

        // Initial command to load dashboard data
        let initial_command = app::Command::perform(
            async move { 
                // Placeholder for initial data loading
                Ok(())
            },
            |_| Message::Dashboard(crate::ui::dashboard::DashboardMessage::RefreshWeather)
        );

        (app, initial_command)
    }

    fn nav_model(&self) -> Option<&nav_bar::Model> {
        Some(&self.nav)
    }

    fn on_nav_select(&mut self, id: nav_bar::Id) -> app::Command<Self::Message> {
        self.nav.activate(id.clone());
        
        match id.as_str() {
            "dashboard" => {
                self.state.current_page = Page::Dashboard;
                app::Command::perform(
                    self.api_client.get_weather(),
                    |result| match result {
                        Ok(weather) => Message::Dashboard(crate::ui::dashboard::DashboardMessage::WeatherLoaded(weather)),
                        Err(e) => Message::Error(e.to_string()),
                    }
                )
            }
            "chat" => {
                self.state.current_page = Page::Chat;
                app::Command::none()
            }
            "pantry" => {
                self.state.current_page = Page::Pantry;
                app::Command::perform(
                    self.api_client.get_food_items(),
                    |result| match result {
                        Ok(items) => Message::Pantry(crate::ui::pantry::PantryMessage::ItemsLoaded(items)),
                        Err(e) => Message::Error(e.to_string()),
                    }
                )
            }
            "ocr" => {
                self.state.current_page = Page::OCR;
                app::Command::none()
            }
            "settings" => {
                self.state.current_page = Page::Settings;
                app::Command::none()
            }
            _ => app::Command::none(),
        }
    }

    fn update(&mut self, message: Self::Message) -> app::Command<Self::Message> {
        match message {
            Message::NavigateTo(page) => {
                let id = match page {
                    Page::Dashboard => "dashboard",
                    Page::Chat => "chat",
                    Page::Pantry => "pantry",
                    Page::OCR => "ocr",
                    Page::Settings => "settings",
                };
                self.on_nav_select(nav_bar::Id::from(id))
            }
            
            Message::Dashboard(msg) => {
                crate::ui::dashboard::update(&mut self.state.dashboard_state, msg, &self.api_client)
                    .map(Message::Dashboard)
            }
            
            Message::Chat(msg) => {
                crate::ui::chat::update(&mut self.state.chat_state, msg, &self.api_client)
                    .map(Message::Chat)
            }
            
            Message::Pantry(msg) => {
                crate::ui::pantry::update(&mut self.state.pantry_state, msg, &self.api_client)
                    .map(Message::Pantry)
            }
            
            Message::OCR(msg) => {
                crate::ui::ocr::update(&mut self.state.ocr_state, msg, &self.api_client)
                    .map(Message::OCR)
            }
            
            Message::Settings(msg) => {
                crate::ui::settings::update(&mut self.state.settings_state, msg, &mut self.state.settings)
                    .map(Message::Settings)
            }
            
            Message::Config(new_settings) => {
                self.state.settings = new_settings;
                self.api_client = Client::new(&self.state.settings.backend_url);
                app::Command::none()
            }
            
            Message::Close => {
                app::Command::perform(async {}, |_| cosmic::app::message::AppMessage::Quit.into())
            }
            
            Message::Minimize => {
                app::Command::perform(async {}, |_| cosmic::app::message::AppMessage::Minimize.into())
            }
            
            Message::Error(error_message) => {
                error!("Application error: {}", error_message);
                self.state.error_state = Some(error_message);
                app::Command::none()
            }
        }
    }

    fn view(&self) -> Element<Self::Message> {
        let header = widget::header_bar()
            .title("MyAppAssistant")
            .on_close(Message::Close)
            .on_minimize(Message::Minimize);

        let content = match self.state.current_page {
            Page::Dashboard => crate::ui::dashboard::view(&self.state.dashboard_state),
            Page::Chat => crate::ui::chat::view(&self.state.chat_state),
            Page::Pantry => crate::ui::pantry::view(&self.state.pantry_state),
            Page::OCR => crate::ui::ocr::view(&self.state.ocr_state),
            Page::Settings => crate::ui::settings::view(&self.state.settings_state),
        };

        // Show error message if present
        let content_with_error = if let Some(error) = &self.state.error_state {
            widget::column()
                .push(
                    widget::container(
                        widget::text(error)
                            .style(cosmic::iced::Color::from_rgb(0.8, 0.0, 0.0))
                    )
                    .padding(10)
                )
                .push(content)
                .into()
        } else {
            content
        };

        widget::column()
            .push(header)
            .push(content_with_error)
            .into()
    }

    fn subscription(&self) -> Subscription<Self::Message> {
        Subscription::batch([
            cosmic::cosmic_config::config_subscription(
                std::any::TypeId::of::<AppSettings>(),
                Self::APP_ID.into(),
                cosmic_config::VERSION,
            ).map(|update| Message::Config(update.config)),
        ])
    }
    
    fn theme(&self) -> cosmic::theme::Theme {
        theme::apply_theme(self.state.settings.theme_mode)
    }
} 