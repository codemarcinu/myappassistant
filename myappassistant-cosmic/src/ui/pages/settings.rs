use cosmic::widget::{self, card, column, container, row, text, text_input, button, toggler};
use cosmic::{Element, app};
use cosmic::iced::{Alignment, Length};
use std::path::PathBuf;

use crate::config::{AppSettings, ThemeMode};
use crate::core::Message;

/// Settings state
#[derive(Debug, Clone, Default)]
pub struct State {
    /// Edited settings
    pub edited_settings: Option<AppSettings>,
    
    /// Saving state
    pub saving: bool,
}

/// Settings messages
#[derive(Debug, Clone)]
pub enum SettingsMessage {
    /// Edit backend URL
    EditBackendUrl(String),
    
    /// Toggle theme mode
    ToggleThemeMode(ThemeMode),
    
    /// Toggle notifications
    ToggleNotifications(bool),
    
    /// Toggle auto sync
    ToggleAutoSync(bool),
    
    /// Edit OCR upload directory
    EditOcrUploadDir(String),
    
    /// Save settings
    SaveSettings,
    
    /// Reset settings
    ResetSettings,
}

/// Update settings state
pub fn update(state: &mut State, message: SettingsMessage, settings: &mut AppSettings) -> app::Command<SettingsMessage> {
    // Ensure we have edited settings
    if state.edited_settings.is_none() {
        state.edited_settings = Some(settings.clone());
    }
    
    let edited_settings = state.edited_settings.as_mut().unwrap();
    
    match message {
        SettingsMessage::EditBackendUrl(url) => {
            edited_settings.backend_url = url;
            app::Command::none()
        }
        
        SettingsMessage::ToggleThemeMode(mode) => {
            edited_settings.theme_mode = mode;
            app::Command::none()
        }
        
        SettingsMessage::ToggleNotifications(enabled) => {
            edited_settings.notifications_enabled = enabled;
            app::Command::none()
        }
        
        SettingsMessage::ToggleAutoSync(enabled) => {
            edited_settings.auto_sync = enabled;
            app::Command::none()
        }
        
        SettingsMessage::EditOcrUploadDir(dir) => {
            edited_settings.ocr_upload_dir = PathBuf::from(dir);
            app::Command::none()
        }
        
        SettingsMessage::SaveSettings => {
            // Apply edited settings
            *settings = edited_settings.clone();
            
            // Save settings to config
            if let Err(e) = settings.save() {
                // In a real app, we would handle this error
                eprintln!("Failed to save settings: {}", e);
            }
            
            app::Command::none()
        }
        
        SettingsMessage::ResetSettings => {
            // Reset to default settings
            state.edited_settings = Some(AppSettings::default());
            app::Command::none()
        }
    }
}

/// Render settings view
pub fn view(state: &State) -> Element<Message> {
    let title = widget::text::title1("Settings")
        .size(32);
    
    // Get settings to display
    let settings = state.edited_settings.as_ref().unwrap_or(&AppSettings::default());
    
    // Backend URL
    let backend_url = text_input("Backend URL", &settings.backend_url)
        .on_input(|url| Message::Settings(SettingsMessage::EditBackendUrl(url)))
        .padding(10);
    
    // Theme mode
    let theme_light = toggler(
        "Light Theme",
        settings.theme_mode == ThemeMode::Light,
        |_| Message::Settings(SettingsMessage::ToggleThemeMode(ThemeMode::Light))
    );
    
    let theme_dark = toggler(
        "Dark Theme",
        settings.theme_mode == ThemeMode::Dark,
        |_| Message::Settings(SettingsMessage::ToggleThemeMode(ThemeMode::Dark))
    );
    
    let theme_system = toggler(
        "System Theme",
        settings.theme_mode == ThemeMode::System,
        |_| Message::Settings(SettingsMessage::ToggleThemeMode(ThemeMode::System))
    );
    
    // Notifications
    let notifications = toggler(
        "Enable Notifications",
        settings.notifications_enabled,
        |enabled| Message::Settings(SettingsMessage::ToggleNotifications(enabled))
    );
    
    // Auto sync
    let auto_sync = toggler(
        "Auto Sync",
        settings.auto_sync,
        |enabled| Message::Settings(SettingsMessage::ToggleAutoSync(enabled))
    );
    
    // OCR upload directory
    let ocr_dir = text_input(
        "OCR Upload Directory",
        &settings.ocr_upload_dir.to_string_lossy()
    )
    .on_input(|dir| Message::Settings(SettingsMessage::EditOcrUploadDir(dir)))
    .padding(10);
    
    // Action buttons
    let save_button = button::standard("Save")
        .on_press(Message::Settings(SettingsMessage::SaveSettings))
        .padding(10);
    
    let reset_button = button::standard("Reset")
        .on_press(Message::Settings(SettingsMessage::ResetSettings))
        .padding(10);
    
    let action_row = row![
        save_button,
        reset_button,
    ]
    .spacing(10)
    .align_items(Alignment::Center);
    
    // Main content
    container(
        column![
            title,
            
            card::Card::new(
                text::title4("Backend"),
                column![
                    backend_url,
                ]
            ),
            
            card::Card::new(
                text::title4("Theme"),
                column![
                    theme_light,
                    theme_dark,
                    theme_system,
                ]
                .spacing(5)
            ),
            
            card::Card::new(
                text::title4("Notifications"),
                column![
                    notifications,
                ]
            ),
            
            card::Card::new(
                text::title4("Synchronization"),
                column![
                    auto_sync,
                ]
            ),
            
            card::Card::new(
                text::title4("OCR"),
                column![
                    ocr_dir,
                ]
            ),
            
            action_row,
        ]
        .spacing(16)
    )
    .padding(16)
    .width(Length::Fill)
    .height(Length::Fill)
    .into()
} 