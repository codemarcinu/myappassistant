import json
import os
from typing import Dict, List

import httpx
import structlog
from fastapi import APIRouter, HTTPException

router = APIRouter()

LLM_SETTINGS_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "..",
    "data",
    "config",
    "llm_settings.json",
)

# Get Ollama URL from environment variables with fallback
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")

logger = structlog.get_logger(__name__)


@router.get("/llm-models", response_model=List[Dict[str, str]])
async def get_available_models() -> List[Dict[str, str]]:
    """Get list of available LLM models from Ollama."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{OLLAMA_URL}/api/tags")
            if response.status_code == 200:
                data = response.json()
                models = []
                for model in data.get("models", []):
                    models.append(
                        {
                            "name": model["name"],
                            "size": str(model.get("size", "Unknown")),
                            "modified_at": model.get("modified_at", ""),
                        }
                    )
                return models
            else:
                logger.error(
                    "Failed to fetch models from Ollama",
                    status_code=response.status_code,
                    detail=response.text,
                )
                raise HTTPException(
                    status_code=500, detail="Nie udało się pobrać listy modeli z Ollama"
                )
    except Exception as e:
        logger.error(f"Error fetching models: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Błąd podczas pobierania modeli: {e}"
        )


@router.get("/llm-model/selected")
async def get_selected_model() -> str:
    """Get currently selected LLM model."""
    try:
        if os.path.exists(LLM_SETTINGS_PATH):
            with open(LLM_SETTINGS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("selected_model", "")
        return ""
    except Exception as e:
        logger.error(f"Error reading selected model: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Błąd odczytu wybranego modelu: {e}"
        )


@router.post("/llm-model/selected")
async def set_selected_model(model_name: str) -> Dict[str, str]:
    """Set the selected LLM model with validation."""
    try:
        # Validate that the model exists in Ollama
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{OLLAMA_URL}/api/tags")
            if response.status_code != 200:
                logger.error(
                    "Failed to connect to Ollama for model validation",
                    status_code=response.status_code,
                    detail=response.text,
                )
                raise HTTPException(
                    status_code=500, detail="Nie udało się połączyć z Ollama"
                )

            data = response.json()
            available_models = [model["name"] for model in data.get("models", [])]

            if model_name not in available_models:
                logger.warning(
                    f"Model '{model_name}' not found in Ollama. Available: {available_models}"
                )
                raise HTTPException(
                    status_code=400,
                    detail=f"Model '{model_name}' nie jest dostępny w Ollama. Dostępne modele: {', '.join(available_models)}",
                )

        # Ensure config directory exists
        config_dir = os.path.dirname(LLM_SETTINGS_PATH)
        os.makedirs(config_dir, exist_ok=True)

        # Save the selected model
        settings_data = {"selected_model": model_name}
        with open(LLM_SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(settings_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Model '{model_name}' set as default")
        return {
            "message": f"Model '{model_name}' został ustawiony jako domyślny",
            "selected_model": model_name,
        }

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Error setting model: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Błąd podczas ustawiania modelu: {e}"
        )
