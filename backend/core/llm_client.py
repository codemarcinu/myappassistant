import aiohttp
import json
from typing import Dict, Any, AsyncGenerator, Optional

# Importujemy nasz obiekt 'settings' z modułu config
from ..config import settings

class OllamaClient:
    """
    Klient do asynchronicznej komunikacji z API serwera Ollama.
    """
    def __init__(self, base_url: str = settings.OLLAMA_BASE_URL):
        """Inicjalizuje klienta, pobierając adres URL z naszej konfiguracji."""
        self.base_url = base_url
        self.generate_url = f"{self.base_url}/api/generate"

    async def generate_stream(
        self, model: str, prompt: str
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Wysyła zapytanie do modelu i streamuje odpowiedź kawałek po kawałku.

        Args:
            model: Nazwa modelu do użycia (np. 'deepseek-coder-v2:16b').
            prompt: Tekst zapytania (prompt), który ma przetworzyć model.

        Yields:
            Kolejne fragmenty odpowiedzi JSON prosto z API Ollama.
        """
        payload = {"model": model, "prompt": prompt, "stream": True}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.generate_url, json=payload) as response:
                    # Rzuci wyjątkiem, jeśli serwer Ollama zwróci błąd (np. 404, 500)
                    response.raise_for_status()

                    # Odpowiedź Ollama jest strumieniem, gdzie każda linia to osobny obiekt JSON.
                    # Przetwarzamy go linia po linii, w miarę jak dane spływają.
                    async for line in response.content:
                        if line:
                            yield json.loads(line.decode('utf-8'))

        except aiohttp.ClientError as e:
            # W przyszłości dodamy tu logowanie błędów
            print(f"Błąd połączenia z Ollama: {e}")
            raise

    async def chat(self, model: str, messages: list, options: Optional[dict] = None, stream: bool = False) -> dict:
        """
        Wysyła zapytanie do endpointu /api/chat z listą wiadomości (system/user) i zwraca odpowiedź modelu.
        Args:
            model: Nazwa modelu do użycia.
            messages: Lista słowników z kluczami 'role' i 'content'.
            options: Dodatkowe opcje (np. temperature).
            stream: Czy odpowiedź ma być strumieniowana (domyślnie False).
        Returns:
            Słownik z odpowiedzią modelu (np. response['message']['content']).
        """
        url = f"{self.base_url}/api/chat"
        payload = {"model": model, "messages": messages, "stream": stream}
        if options:
            payload["options"] = options
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    response.raise_for_status()
                    return await response.json()
        except aiohttp.ClientError as e:
            print(f"Błąd połączenia z Ollama (chat): {e}")
            raise

# Tworzymy jedną, globalną instancję klienta, dostępną dla całej aplikacji.
ollama_client = OllamaClient()