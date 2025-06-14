from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
import asyncio

from ..core.llm_client import ollama_client
from ..config import settings

# APIRouter działa jak "mini-aplikacja" FastAPI, grupując endpointy
router = APIRouter()

class ChatRequest(BaseModel):
    prompt: str
    model: str | None = None # Pole opcjonalne

async def chat_response_generator(prompt: str, model: str):
    """
    To jest asynchroniczny generator. Pobiera kawałki odpowiedzi od klienta
    Ollama i od razu przesyła je dalej (yield).
    """
    try:
        async for chunk in ollama_client.generate_stream(model=model, prompt=prompt):
            # Z całego obiektu JSON od Ollamy interesuje nas tylko pole 'response'
            if "response" in chunk:
                yield chunk["response"]
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