import logging
import uuid
from functools import lru_cache
from typing import Any, AsyncGenerator, Dict, List, Optional

import ollama


class LLMClient:
    """
    Klient do komunikacji z modelami językowymi Ollama.
    Zawiera ujednolicone metody dostępu i obsługi błędów.
    """

    def __init__(self):
        logging.info("Inicjalizacja klienta LLM...")

    def _format_response(self, content: str, as_error: bool = False) -> Dict[str, Any]:
        """
        Tworzy ujednoliconą strukturę odpowiedzi.

        Args:
            content: Treść odpowiedzi
            as_error: Czy odpowiedź jest błędem

        Returns:
            Ujednolicona struktura odpowiedzi
        """
        if as_error:
            logging.error(f"Error response: {content}")

        return {
            "message": {"content": content},
            "response": content,  # Dodatkowe pole dla kompatybilności z chat.py
        }

    def _create_messages(self, prompt: str, system_prompt: str) -> List[Dict[str, str]]:
        """
        Tworzy listę wiadomości w formacie wymaganym przez Ollama.

        Args:
            prompt: Treść zapytania użytkownika
            system_prompt: Treść instrukcji systemowych

        Returns:
            Lista wiadomości w formacie [{'role': str, 'content': str}, ...]
        """
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ]

    def _get_safe_content(self, response: Any) -> str:
        """
        Bezpiecznie pobiera treść odpowiedzi.

        Args:
            response: Odpowiedź z modelu

        Returns:
            Treść odpowiedzi lub komunikat o błędzie
        """
        # Sprawdzamy typ odpowiedzi i używamy .get z domyślną wartością dla bezpiecznego dostępu
        if isinstance(response, dict):
            return response.get("message", {}).get("content", "No content returned")
        return "No content returned"

    def _validate_messages(self, messages: List[Dict[str, str]]) -> None:
        """
        Waliduje format wiadomości.

        Args:
            messages: Lista wiadomości do sprawdzenia

        Raises:
            ValueError: Jeśli format wiadomości jest nieprawidłowy
        """
        if not isinstance(messages, list) or not messages:
            raise ValueError("Messages must be a non-empty list")

        for msg in messages:
            if not isinstance(msg, dict) or "role" not in msg or "content" not in msg:
                raise ValueError(
                    "Each message must be a dict with 'role' and 'content' keys"
                )

    @lru_cache(maxsize=128)
    def get_completion(
        self, prompt: str, system_prompt: str = "", model: str = "llama3"
    ) -> str:
        """
        Pobiera odpowiedź z modelu językowego z obsługą cache.
        Zapytania z tymi samymi argumentami będą zwracane z pamięci podręcznej.

        Args:
            prompt: Treść zapytania
            system_prompt: Instrukcje systemowe dla modelu
            model: Nazwa modelu do użycia

        Returns:
            Treść odpowiedzi jako string
        """
        # Ten log pojawi się tylko wtedy, gdy zapytanie NIE pochodzi z cache
        request_id = str(uuid.uuid4())[:8]
        logging.info(f"[{request_id}] Wysyłam NOWE zapytanie do modelu: {model}")

        try:
            # Tworzymy wiadomości w odpowiednim formacie
            messages = self._create_messages(prompt, system_prompt)

            # Wywołujemy ollama.chat bez typowania messages aby uniknąć błędów
            response = ollama.chat(model=model, messages=messages)  # type: ignore

            # Bezpiecznie pobieramy zawartość
            return self._get_safe_content(response)
        except Exception as e:
            logging.error(
                f"[{request_id}] Błąd podczas komunikacji z Ollama: {e}", exc_info=True
            )
            return f"Wystąpił błąd podczas komunikacji z modelem: {e}"

    async def generate_stream(
        self,
        model: str = "llama3",
        prompt: str = "",
        system_prompt: str = "",
        messages: Optional[List[Dict[str, str]]] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Generuje strumień odpowiedzi z modelu językowego.

        Args:
            model: Nazwa modelu do użycia
            prompt: Treść zapytania (używane tylko gdy messages=None)
            system_prompt: Instrukcje systemowe (używane tylko gdy messages=None)
            messages: Opcjonalna lista gotowych wiadomości (ma priorytet nad prompt/system_prompt)

        Yields:
            Fragmenty odpowiedzi jako słowniki z kluczami 'message' i 'response'
        """
        request_id = str(uuid.uuid4())[:8]
        logging.info(
            f"[{request_id}] Rozpoczynam generowanie strumienia z modelu: {model}"
        )

        try:
            # Użyj messages jeśli podane, w przeciwnym razie utwórz z prompt/system_prompt
            msg_list = (
                messages
                if messages is not None
                else self._create_messages(prompt, system_prompt)
            )

            # Wywołujemy ollama.chat bez typowania messages aby uniknąć błędów
            stream = ollama.chat(
                model=model,
                messages=msg_list,  # type: ignore
                stream=True,
            )

            for chunk in stream:
                if isinstance(chunk, dict):
                    # Pobierz treść z chunk["message"]["content"] jeśli istnieje
                    content = chunk.get("message", {}).get("content", "")
                    if content:
                        # Zwracamy format zgodny z oczekiwaniami w chat.py
                        yield {
                            "message": {"content": content},
                            "response": content,  # Dla kompatybilności z chat.py
                        }
        except Exception as e:
            error_msg = f"Wystąpił błąd podczas komunikacji z modelem: {e}"
            logging.error(f"[{request_id}] {error_msg}", exc_info=True)
            yield self._format_response(error_msg, as_error=True)

    async def chat(
        self,
        model: str,
        messages: List[Dict[str, str]],
        stream: bool = False,
        options: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """
        Wysyła wiadomość do modelu i zwraca odpowiedź.

        Args:
            model: Nazwa modelu do użycia
            messages: Lista wiadomości w formacie [{'role': str, 'content': str}, ...]
            stream: Czy zwracać strumień odpowiedzi
            options: Dodatkowe opcje dla modelu (np. temperature)

        Returns:
            Odpowiedź w formie słownika lub generator strumienia
        """
        request_id = str(uuid.uuid4())[:8]

        try:
            # Walidacja parametrów
            self._validate_messages(messages)
            if options is not None and not isinstance(options, dict):
                raise ValueError("Options must be a dictionary")

            logging.info(f"[{request_id}] Sending request to Ollama model: {model}")
            logging.debug(f"[{request_id}] Messages: {messages}")

            if stream:
                # Dla trybu strumieniowego zwracamy generator
                return self.generate_stream(model=model, messages=messages)
            else:
                # Wywołujemy ollama.chat bez typowania messages aby uniknąć błędów
                response = ollama.chat(
                    model=model,
                    messages=messages,  # type: ignore
                    options=options or {},  # type: ignore
                )

                logging.debug(
                    f"[{request_id}] Received response from Ollama: {response}"
                )
                return response
        except Exception as e:
            logging.error(
                f"[{request_id}] Błąd podczas komunikacji z Ollama: {e}", exc_info=True
            )
            return self._format_response(
                f"Wystąpił błąd podczas komunikacji z modelem: {e}", as_error=True
            )


# Inicjalizacja pojedynczej instancji klienta
llm_client = LLMClient()
