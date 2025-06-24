# MyAppAssistant COSMIC

A native desktop application built with COSMIC Toolkit that integrates with the existing Python/FastAPI backend.

## Features

- Native desktop experience with COSMIC UI
- Chat interface with AI assistants
- Pantry management
- OCR receipt scanning
- Weather information
- Dark/light theme support

## Requirements

- Rust 1.70 or newer
- COSMIC Toolkit dependencies
- Python/FastAPI backend (existing)

## Building

### Install Rust

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

### Install Just

```bash
cargo install just
```

### Clone and Build

```bash
git clone https://github.com/yourusername/myappassistant-cosmic.git
cd myappassistant-cosmic
just build
```

### Run

```bash
just run
```

## Development

This project follows the Elm Architecture pattern as implemented by COSMIC Toolkit:

1. **State** - Application data structures
2. **Message** - Events and user interactions
3. **Update** - State transformation logic
4. **View** - UI rendering from state

### Project Structure

```
src/
├── main.rs              # Application entry point
├── app.rs               # Main application struct implementing cosmic::Application
├── core/                # Business logic and state management
│   ├── mod.rs
│   ├── messages.rs      # Message types
│   ├── state.rs         # Application state
│   └── theme.rs         # Theme management
├── ui/                  # User interface components
│   ├── mod.rs
│   ├── pages/           # Application pages/views
│   │   ├── mod.rs
│   │   ├── dashboard.rs
│   │   ├── chat.rs
│   │   ├── pantry.rs
│   │   ├── ocr.rs
│   │   └── settings.rs
│   └── components/      # Reusable UI components
├── api/                 # Backend integration
│   ├── mod.rs
│   ├── client.rs        # HTTP client for Python backend
│   └── models.rs        # Data structures for API responses
├── config.rs            # Application configuration
└── utils/               # Utility functions
    ├── mod.rs
    ├── error.rs         # Error handling
    └── helpers.rs       # Helper functions
```

## Backend Integration

This application communicates with the existing Python/FastAPI backend through HTTP REST API. The API client is implemented in `src/api/client.rs`.

## License

MIT 