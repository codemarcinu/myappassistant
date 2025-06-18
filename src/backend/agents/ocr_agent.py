from typing import Any, Dict

from pydantic import BaseModel, ValidationError

from ..core.ocr import process_image_file, process_pdf_file
from .enhanced_base_agent import EnhancedAgentResponse, ImprovedBaseAgent


class OCRAgentInput(BaseModel):
    """Model wejściowy dla OCRAgent."""

    file_bytes: bytes
    file_type: str


class OCRAgent(ImprovedBaseAgent):
    """Agent odpowiedzialny za optyczne rozpoznawanie znaków (OCR) z obrazów i dokumentów PDF.

    Wykorzystuje Tesseract OCR z obsługą języka polskiego.
    """

    def __init__(self) -> None:
        """Inicjalizuje OCRAgent."""
        super().__init__(name="OCR Agent")

    async def process(self, input_data: Dict[str, Any]) -> EnhancedAgentResponse:
        """
        Przetwarza pliki obrazów lub PDF-ów za pomocą OCR.

        Args:
            input_data (Any): Dane wejściowe, oczekiwany słownik lub OCRAgentInput.

        Returns:
            AgentResponse: Odpowiedź agenta z wynikiem OCR lub błędem.
        """
        try:
            if not isinstance(input_data, OCRAgentInput):
                # Walidacja i konwersja przez Pydantic
                input_data = OCRAgentInput.parse_obj(input_data)
        except ValidationError as ve:
            return EnhancedAgentResponse(
                success=False,
                error=f"Błąd walidacji danych wejściowych: {ve}",
                error_severity="medium",
            )

        file_bytes: bytes = input_data.file_bytes
        file_type: str = input_data.file_type.lower()

        try:
            if file_type == "image":
                text = process_image_file(file_bytes)
            elif file_type == "pdf":
                text = process_pdf_file(file_bytes)
            else:
                return EnhancedAgentResponse(
                    success=False,
                    error=f"Nieobsługiwany typ pliku: {file_type}",
                    error_severity="medium",
                )

            if not text:
                return EnhancedAgentResponse(
                    success=False,
                    error="Nie udało się rozpoznać tekstu z pliku",
                    error_severity="medium",
                )

            return EnhancedAgentResponse(
                success=True,
                text=text,
                message="Pomyślnie wyodrębniono tekst z pliku",
                metadata={"file_type": file_type},
            )
        except Exception as e:
            return EnhancedAgentResponse(
                success=False,
                error=f"Wystąpił błąd podczas przetwarzania pliku: {str(e)}",
                error_severity="high",
            )

    async def execute(
        self, task_description: str, context: Dict[str, Any] = {}
    ) -> EnhancedAgentResponse:
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
