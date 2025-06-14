from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Główna klasa do zarządzania ustawieniami aplikacji.
    Ustawienia są wczytywane ze zmiennych środowiskowych lub pliku .env.
    """
    APP_NAME: str = "Osobisty Asystent AI"
    APP_VERSION: str = "0.1.0"

    # Konfiguracja dla klienta Ollama
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    DEFAULT_CODE_MODEL: str = "deepseek-coder-v2:16b"
    DEFAULT_CHAT_MODEL: str = "SpeakLeash/bielik-11b-v2.3-instruct:Q6_K"  # Model do rozpoznawania intencji w języku polskim
    DEFAULT_EMBEDDING_MODEL: str = "nomic-embed-text:latest"

    # Ta linia mówi Pydantic, aby wczytał zmienne z pliku .env w głównym katalogu
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding='utf-8')

# Tworzymy jedną, globalną instancję ustawień,
# której będziemy używać w całej aplikacji.
settings = Settings()