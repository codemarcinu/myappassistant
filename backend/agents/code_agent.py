from typing import Dict, Any, Optional
from .base_agent import BaseAgent, AgentResponse
from ..core.llm_client import ollama_client  # Importujemy naszego klienta Ollama
from ..config import settings                # Importujemy naszą konfigurację

class CodeAgent(BaseAgent):
    """
    Agent specjalizujący się w generowaniu i analizie kodu.
    """
    def __init__(self):
        # Wywołujemy konstruktor klasy nadrzędnej (BaseAgent)
        # i podajemy nazwę oraz opis naszego agenta.
        super().__init__(
            name="CodeAgent",
            description="Agent do generowania, analizy i modyfikacji kodu w Pythonie."
        )

    async def execute(self, task_description: str, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        """
        Implementacja głównej metody logicznej dla CodeAgent.
        """
        self.logger.info(f"CodeAgent otrzymał zadanie: '{task_description}'")

        # Budujemy szczegółowy prompt, aby dać modelowi LLM lepszy kontekst.
        # To jest przykład prostego 'prompt engineering'.
        prompt = f"""
        Jesteś światowej klasy programistą i ekspertem od języka Python.
        Twoim zadaniem jest napisać zwięzły i poprawny fragment kodu w Pythonie na podstawie poniższego polecenia.
        Odpowiedz TYLKO i WYŁĄCZNIE kodem. Nie dodawaj żadnych wyjaśnień, wstępów, podsumowań ani formatowania Markdown.

        Polecenie: "{task_description}"

        Twój kod w Pythonie:
        """

        try:
            # Używamy naszego klienta Ollama do wygenerowania odpowiedzi.
            # W odróżnieniu od czatu, tutaj chcemy zebrać całą odpowiedź przed jej zwróceniem.
            full_response = ""
            model_to_use = settings.DEFAULT_CODE_MODEL

            async for chunk in ollama_client.generate_stream(model=model_to_use, prompt=prompt):
                if "response" in chunk:
                    full_response += chunk["response"]

            if not full_response.strip():
                self.logger.warning("Model LLM nie wygenerował żadnej odpowiedzi.")
                return AgentResponse(success=False, result=None, error="Model nie zwrócił treści.")

            self.logger.info(f"Model '{model_to_use}' pomyślnie wygenerował kod.")
            # Zwracamy ustandaryzowaną odpowiedź z sukcesem i wygenerowanym kodem
            return AgentResponse(success=True, result=full_response.strip())

        except Exception as e:
            self.logger.error(f"Wystąpił błąd podczas komunikacji z LLM: {e}")
            return AgentResponse(success=False, result=None, error=str(e))

# Tworzymy jedną, gotową do użycia instancję naszego agenta
code_agent = CodeAgent()