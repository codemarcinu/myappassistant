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
            name="OCR Agent"
        )

    async def process(self, input_data: Any) -> AgentResponse:
        """
        Przetwarza pliki obrazów lub PDF-ów za pomocą OCR.
        
        Args:
            input_data: Słownik zawierający:
                - file_bytes: bajty pliku do przetworzenia
                - file_type: typ pliku ('image' lub 'pdf')
        """
        if not isinstance(input_data, dict) or 'file_bytes' not in input_data or 'file_type' not in input_data:
            return AgentResponse(
                success=False,
                error="Brak wymaganych danych: file_bytes i file_type"
            )

        file_bytes = input_data['file_bytes']
        file_type = input_data['file_type'].lower()

        try:
            if file_type == 'image':
                text = process_image_file(file_bytes)
            elif file_type == 'pdf':
                text = process_pdf_file(file_bytes)
            else:
                return AgentResponse(
                    success=False,
                    error=f"Nieobsługiwany typ pliku: {file_type}"
                )

            if text is None:
                return AgentResponse(
                    success=False,
                    error="Nie udało się rozpoznać tekstu z pliku"
                )

            return AgentResponse(
                success=True,
                data={"text": text},
                message="Pomyślnie wyodrębniono tekst z pliku"
            )

        except Exception as e:
            return AgentResponse(
                success=False,
                error=f"Wystąpił błąd podczas przetwarzania pliku: {str(e)}"
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
        return await self.process(context) 