from typing import Any, Dict, cast

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..agents.orchestrator import Orchestrator
from ..config import settings
from ..core.database import get_db
from ..core.llm_client import llm_client

# APIRouter działa jak "mini-aplikacja" FastAPI, grupując endpointy
router = APIRouter()


class ChatRequest(BaseModel):
    prompt: str
    model: str | None = None  # Pole opcjonalne


class MemoryChatRequest(BaseModel):
    message: str
    session_id: str  # Kluczowe do śledzenia i odróżniania konwersacji


class MemoryChatResponse(BaseModel):
    reply: str
    history_length: int


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


@router.post("/memory_chat", response_model=MemoryChatResponse)
async def chat_with_memory(
    request: MemoryChatRequest, db: AsyncSession = Depends(get_db)
):
    """
    Endpoint do prowadzenia rozmowy z agentem, który zapamiętuje historię konwersacji.
    Każda konwersacja jest identyfikowana przez session_id.
    """
    orchestrator = Orchestrator(db)
    response_data = await orchestrator.process_command(
        user_command=request.message, session_id=request.session_id
    )

    # Assuming the response_data contains a "state" dictionary with a "history_length"
    history_length = response_data.get("history_length", 0)

    return MemoryChatResponse(
        reply=response_data.get("response", "No response from agent."),
        history_length=history_length,
    )
