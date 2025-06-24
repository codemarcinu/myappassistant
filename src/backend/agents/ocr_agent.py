from typing import Any, Dict, Union

from pydantic import BaseModel, ValidationError

from backend.agents.base_agent import BaseAgent
from backend.agents.interfaces import AgentResponse
from backend.core.decorators import handle_exceptions
from backend.core.ocr import process_image_file, process_pdf_file


class OCRAgentInput(BaseModel):
    """Model wejściowy dla OCRAgent."""

    file_bytes: bytes
    file_type: str


class OCRAgent(BaseAgent):
    """Agent odpowiedzialny za optyczne rozpoznawanie znaków (OCR) z obrazów i dokumentów PDF.

    Wykorzystuje Tesseract OCR z obsługą języka polskiego.
    """

    def __init__(
        self,
        name: str = "OCRAgent",
        error_handler: Any = None,
        fallback_manager: Any = None,
        **kwargs: Any,
    ) -> None:
        """Inicjalizuje OCRAgent."""
        super().__init__(
            name=name, error_handler=error_handler, fallback_manager=fallback_manager
        )
        # Dodaję atrybuty konfiguracyjne
        self.TIMEOUT = kwargs.get("timeout", 30)
        self.default_language = kwargs.get("language", "eng")

    @handle_exceptions(max_retries=1, retry_delay=0.5)
    async def process(
        self, input_data: Union[OCRAgentInput, Dict[str, Any]]
    ) -> AgentResponse:
        """
        Przetwarza pliki obrazów lub PDF-ów za pomocą OCR.

        Args:
            input_data (Union[OCRAgentInput, Dict[str, Any]]): Dane wejściowe, oczekiwany słownik lub OCRAgentInput.

        Returns:
            AgentResponse: Odpowiedź agenta z wynikiem OCR lub błędem.
        """
        try:
            if not isinstance(input_data, OCRAgentInput):
                # Walidacja i konwersja przez Pydantic (używamy model_validate zgodnie z Pydantic V2.0)
                input_data = OCRAgentInput.model_validate(input_data)
        except ValidationError as ve:
            return AgentResponse(
                success=False,
                error=f"Błąd walidacji danych wejściowych: {ve}",
            )

        file_bytes: bytes
        file_type: str

        # Directly access attributes now that input_data is guaranteed to be OCRAgentInput
        file_bytes = input_data.file_bytes
        file_type = input_data.file_type.lower()

        try:
            if file_type == "image":
                text = process_image_file(file_bytes)
            elif file_type == "pdf":
                text = process_pdf_file(file_bytes)
            else:
                return AgentResponse(
                    success=False,
                    error=f"Nieobsługiwany typ pliku: {file_type}",
                )

            if not text:
                return AgentResponse(
                    success=False,
                    error="Nie udało się rozpoznać tekstu z pliku",
                )

            return AgentResponse(
                success=True,
                text=text,
                message="Pomyślnie wyodrębniono tekst z pliku",
                metadata={"file_type": file_type},
            )
        except Exception as e:
            return AgentResponse(
                success=False,
                error=f"Wystąpił błąd podczas przetwarzania pliku: {str(e)}",
            )

    @handle_exceptions(max_retries=1)
    async def execute(
        self, task_description: str, context: Dict[str, Any] = {}
    ) -> AgentResponse:
        """
        Wykonuje OCR na przesłanym pliku.

        Args:
            task_description: Opis zadania (nieużywany w tym agencie)
            context: Słownik zawierający:
                - file_bytes: bajty pliku do przetworzenia
                - file_type: typ pliku ('image' lub 'pdf')

        Returns:
            AgentResponse zawierający rozpoznany tekst lub informację o błędzie
        """
        return await self.process(context)
