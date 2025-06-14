import ollama
from functools import lru_cache
import logging
from typing import List, Dict, Any, AsyncGenerator

class LLMClient:
    """
    Klient do komunikacji z modelami językowymi Ollama.
    """
    def __init__(self):
        logging.info("Inicjalizacja klienta LLM...")

    @lru_cache(maxsize=128)
    def get_completion(self, prompt: str, system_prompt: str, model: str = "llama3") -> str:
        """
        Pobiera odpowiedź z modelu językowego z obsługą cache.
        Zapytania z tymi samymi argumentami będą zwracane z pamięci podręcznej.
        """
        # Ten log pojawi się tylko wtedy, gdy zapytanie NIE pochodzi z cache
        logging.info(f"Wysyłam NOWE zapytanie do modelu: {model}")
        try:
            response = ollama.chat(
                model=model,
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': prompt}
                ]
            )
            return response['message']['content']
        except Exception as e:
            logging.error(f"Błąd podczas komunikacji z Ollama: {e}")
            return f"Wystąpił błąd podczas komunikacji z modelem: {e}"

    async def generate_stream(self, prompt: str, system_prompt: str, model: str = "llama3") -> AsyncGenerator[str, None]:
        """
        Generuje strumień odpowiedzi z modelu językowego.
        """
        try:
            stream = ollama.chat(
                model=model,
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': prompt}
                ],
                stream=True
            )
            for chunk in stream:
                if 'message' in chunk and 'content' in chunk['message']:
                    yield chunk['message']['content']
        except Exception as e:
            logging.error(f"Błąd podczas generowania strumienia: {e}")
            yield f"Wystąpił błąd podczas komunikacji z modelem: {e}"

    async def chat(self, model: str, messages: List[Dict[str, str]], stream: bool = False, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Wysyła wiadomość do modelu i zwraca odpowiedź.
        
        Args:
            model: Nazwa modelu do użycia
            messages: Lista wiadomości w formacie [{'role': str, 'content': str}, ...]
            stream: Czy zwracać strumień odpowiedzi
            options: Dodatkowe opcje dla modelu (np. temperature)
        """
        try:
            response = ollama.chat(
                model=model,
                messages=messages,
                stream=stream,
                options=options or {}
            )
            return response
        except Exception as e:
            logging.error(f"Błąd podczas komunikacji z Ollama: {e}")
            return {'message': {'content': f"Wystąpił błąd podczas komunikacji z modelem: {e}"}}

# Inicjalizacja pojedynczej instancji klienta
llm_client = LLMClient()