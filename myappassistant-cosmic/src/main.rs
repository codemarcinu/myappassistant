use cosmic::app;
use tracing::{info, Level};

mod app;
mod api;
mod core;
mod ui;
mod utils;
mod config;

use app::MyAppAssistant;

fn main() -> cosmic::iced::Result {
    // Initialize logging
    tracing_subscriber::fmt()
        .with_env_filter("myappassistant_cosmic=debug,cosmic=info")
        .with_target(false)
        .init();
    
    info!("Starting MyAppAssistant COSMIC");
    
    // Application settings
    let settings = cosmic::app::Settings::default()
        .theme(cosmic::theme::system_preference())
        .size_limits(cosmic::iced::Size::new(800.0, 600.0).into())
        .debug(cfg!(debug_assertions));

    // Run the application
    cosmic::app::run::<MyAppAssistant>(settings, ())
} 