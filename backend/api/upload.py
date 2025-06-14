from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Optional
from ..agents.orchestrator import orchestrator
from ..agents.state import ConversationState

router = APIRouter()

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    command: Optional[str] = None
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
        if content_type.startswith('image/'):
            file_type = 'image'
        elif content_type == 'application/pdf':
            file_type = 'pdf'
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Nieobsługiwany typ pliku: {content_type}. Obsługiwane typy: image/*, application/pdf"
            )
            
        # Wczytaj zawartość pliku
        file_bytes = await file.read()
        
        # Przetwórz plik przez orchestrator
        state = ConversationState()
        result = await orchestrator.process_command(
            user_command=command or "Dodaj zakupy z paragonu",
            state=state,
            file_data={
                "file_bytes": file_bytes,
                "file_type": file_type
            }
        )
        
        return {"result": result}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 