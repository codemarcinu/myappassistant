import json
import os
from typing import Dict, List

from fastapi import APIRouter, HTTPException

from backend.core.llm_client import llm_client

router = APIRouter()

LLM_SETTINGS_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "..",
    "data",
    "config",
    "llm_settings.json",
)


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


def get_selected_llm_model() -> str:
    """
    Odczytuje aktualnie wybrany model LLM z pliku konfiguracyjnego.
    """
    try:
        with open(LLM_SETTINGS_PATH, "r") as f:
            data = json.load(f)
            return data.get("selected_model", "")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Błąd odczytu wybranego modelu: {e}"
        )


@router.get("/llm-selected", response_model=Dict[str, str])
async def get_llm_selected() -> Dict[str, str]:
    """
    Zwraca aktualnie wybrany model LLM.
    """
    selected = get_selected_llm_model()
    return {"selected_model": selected}
