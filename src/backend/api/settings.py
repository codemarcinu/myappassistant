from typing import Dict, List

from fastapi import APIRouter, HTTPException

from backend.core.llm_client import llm_client

router = APIRouter()


@router.get("/llm-models", response_model=List[Dict[str, str]])
async def get_llm_models() -> List[Dict[str, str]]:
    """
    Zwraca listę dostępnych modeli LLM z serwera Ollama.
    """
    try:
        models = await llm_client.get_models()
        # Zwracamy tylko nazwę i rozmiar/model_id
        return [
            {"name": m.get("name", ""), "size": str(m.get("size", ""))} for m in models
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Błąd pobierania modeli LLM: {e}")
