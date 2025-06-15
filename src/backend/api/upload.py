from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel

from backend.core.ocr import process_image_file, process_pdf_file


class UploadRequest(BaseModel):
    command: Optional[str] = None


class UploadResponse(BaseModel):
    text: str
    content_type: str


class OcrService:
    def process(self, file_bytes: bytes, content_type: str) -> str:
        if content_type.startswith("image/"):
            text = process_image_file(file_bytes)
        elif content_type == "application/pdf":
            text = process_pdf_file(file_bytes)
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Nieobsługiwany typ pliku: {content_type}. Obsługiwane typy: image/*, application/pdf",
            )

        if text is None:
            raise HTTPException(
                status_code=500, detail="Błąd podczas przetwarzania pliku przez OCR."
            )
        return text


def get_ocr_service() -> OcrService:
    return OcrService()


router = APIRouter()


@router.post("/upload", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    request: UploadRequest = Depends(),
    service: OcrService = Depends(get_ocr_service),
):
    """
    Endpoint do przesyłania plików (obrazów lub PDF) do przetworzenia przez OCR.

    Args:
        file: Plik do przetworzenia (obraz lub PDF)
        command: Opcjonalne polecenie tekstowe do wykonania na rozpoznanym tekście
    """
    try:
        content_type = file.content_type
        if not content_type:
            raise HTTPException(status_code=400, detail="Nie można określić typu pliku")

        file_bytes = await file.read()
        ocr_text = service.process(file_bytes, content_type)

        return UploadResponse(text=ocr_text, content_type=content_type)

    except HTTPException as e:
        # Re-raise HTTPException to preserve status code and detail
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Wystąpił nieoczekiwany błąd: {e}")
