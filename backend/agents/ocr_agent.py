from typing import Any, Dict
from .base_agent import BaseAgent, AgentResponse
from ..core.ocr import process_image_file, process_pdf_file

class OCRAgent(BaseAgent):
    """
    Agent odpowiedzialny za optyczne rozpoznawanie znaków (OCR) z obrazów i dokumentów PDF.
    Wykorzystuje Tesseract OCR z obsługą języka polskiego.
    """
    def __init__(self):
        super().__init__(
            name="OCR Agent",
            description="Agent do optycznego rozpoznawania znaków z obrazów i PDF-ów"
        )

    async def execute(self, task_description: str, context: Dict[str, Any] = {}) -> AgentResponse:
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
        if not context or 'file_bytes' not in context or 'file_type' not in context:
            return AgentResponse(
                success=False,
                result=None,
                error="Brak wymaganych danych: file_bytes i file_type"
            )

        file_bytes = context['file_bytes']
        file_type = context['file_type'].lower()

        try:
            if file_type == 'image':
                text = process_image_file(file_bytes)
            elif file_type == 'pdf':
                text = process_pdf_file(file_bytes)
            else:
                return AgentResponse(
                    success=False,
                    result=None,
                    error=f"Nieobsługiwany typ pliku: {file_type}"
                )

            if text is None:
                return AgentResponse(
                    success=False,
                    result=None,
                    error="Nie udało się rozpoznać tekstu z pliku"
                )

            return AgentResponse(
                success=True,
                result={"text": text}
            )

        except Exception as e:
            self.logger.error(f"Błąd podczas przetwarzania pliku: {str(e)}")
            return AgentResponse(
                success=False,
                result=None,
                error=f"Wystąpił błąd podczas przetwarzania pliku: {str(e)}"
            ) 