from typing import Any, Dict, cast

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from ..config import settings
from ..core.llm_client import llm_client

# APIRouter działa jak "mini-aplikacja" FastAPI, grupując endpointy
router = APIRouter()


class ChatRequest(BaseModel):
    prompt: str
    model: str | None = None  # Pole opcjonalne


async def chat_response_generator(prompt: str, model: str):
    """
    Asynchroniczny generator. Pobiera kawałki odpowiedzi od klienta
    Ollama i od razu przesyła je dalej (yield).
    """
    try:
        async for chunk in llm_client.generate_stream(
            model=model, prompt=prompt, system_prompt=""
        ):
            if not isinstance(chunk, dict):
                continue
            chunk_dict = cast(Dict[str, Any], chunk)
            if "response" in chunk_dict:
                yield chunk_dict["response"]
    except Exception as e:
        print(f"Błąd podczas streamowania: {e}")
        yield "Wystąpił błąd serwera."


@router.post("/chat")
async def chat_with_model(request: ChatRequest):
    """
    Endpoint do prowadzenia rozmowy z modelem LLM.
    Dzięki StreamingResponse, odpowiedź jest wysyłana do klienta
    w czasie rzeczywistym, bez czekania na całą odpowiedź modelu.
    """
    # Jeśli w zapytaniu nie podano modelu, użyj domyślnego z konfiguracji
    model_to_use = request.model or settings.DEFAULT_CODE_MODEL
    generator = chat_response_generator(request.prompt, model_to_use)
    return StreamingResponse(generator, media_type="text/plain")
