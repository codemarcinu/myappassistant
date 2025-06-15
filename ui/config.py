import os


class Config:
    BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
    DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "Llama3 (Ollama)")
    PAGE_TITLE = os.getenv("PAGE_TITLE", "FoodSave AI")
    PAGE_ICON = os.getenv("PAGE_ICON", "🤖")
