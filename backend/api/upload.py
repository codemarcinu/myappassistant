from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel


class UploadRequest(BaseModel):
    command: Optional[str] = None


class UploadResponse(BaseModel):
    result: dict


class DummyService:
    def process(self, file_bytes: bytes) -> str:
        return "dummy result"


def get_dummy_service() -> DummyService:
    return DummyService()


router = APIRouter()


@router.post("/upload", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    request: UploadRequest = Depends(),
    service: DummyService = Depends(get_dummy_service),
):
    """
    Endpoint do przesyłania plików (obrazów lub PDF) do przetworzenia przez OCR.

    Args:
        file: Plik do przetworzenia (obraz lub PDF)
        command: Opcjonalne polecenie tekstowe do wykonania na rozpoznanym tekście
    """
    try:
        # Sprawdź typ pliku
        content_type = file.content_type
        if not content_type:
            raise HTTPException(status_code=400, detail="Nie można określić typu pliku")

        # Określ typ pliku na podstawie content_type
        if content_type.startswith("image/"):
            pass  # file_type = "image"
        elif content_type == "application/pdf":
            pass  # file_type = "pdf"
        else:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Nieobsługiwany typ pliku: {content_type}. "
                    "Obsługiwane typy: image/*, application/pdf"
                ),
            )

        # Wczytaj zawartość pliku
        file_bytes = await file.read()

        # Użycie serwisu przez DI
        dummy_result = service.process(file_bytes)

        # Przykład walidacji odpowiedzi przez Pydantic
        return UploadResponse(result={"dummy": dummy_result})

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
