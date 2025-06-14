import ollama
from functools import lru_cache
import logging

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

# Inicjalizacja pojedynczej instancji klienta
llm_client = LLMClient()