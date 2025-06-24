pub mod messages;
pub mod state;
pub mod theme;

pub use messages::Message;
pub use state::AppState;

/// Application flags for initialization
#[derive(Debug, Default)]
pub struct Flags {
    // Add initialization flags if needed
} 