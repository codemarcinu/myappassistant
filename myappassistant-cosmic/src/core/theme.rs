use cosmic::theme::{Theme, ColorPalette};
use crate::config::ThemeMode;

/// Apply theme based on settings
pub fn apply_theme(theme_mode: ThemeMode) -> Theme {
    let mut theme = cosmic::theme::system();
    
    match theme_mode {
        ThemeMode::Light => theme.light(),
        ThemeMode::Dark => theme.dark(),
        ThemeMode::System => theme, // Uses system preference
    }
} 