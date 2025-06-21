import logging

logger = logging.getLogger(__name__)

from typing import Any, Dict, cast

from fastapi import APIRouter, BackgroundTasks, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.core.async_patterns import (
    CircuitBreakerConfig,
    timeout_context,
    with_backpressure,
    with_circuit_breaker,
)
from backend.core.llm_client import llm_client
from backend.infrastructure.database.database import get_db
from backend.orchestrator_management.orchestrator_pool import orchestrator_pool
from backend.orchestrator_management.request_queue import request_queue

# APIRouter działa jak "mini-aplikacja" FastAPI, grupując endpointy
router = APIRouter()


class ChatRequest(BaseModel):
    prompt: str
    model: str | None = None  # Pole opcjonalne


class MemoryChatRequest(BaseModel):
    message: str
    session_id: str  # Kluczowe do śledzenia i odróżniania konwersacji
    usePerplexity: bool = False  # Nowe pole


class MemoryChatResponse(BaseModel):
    reply: str
    history_length: int


# Circuit breaker dla LLM client
llm_circuit_breaker = CircuitBreakerConfig(
    failure_threshold=3, recovery_timeout=30.0, name="llm_client"
)


@with_circuit_breaker(llm_circuit_breaker)
@with_backpressure(max_concurrent=50)
@with_backpressure(max_concurrent=20)  # Ograniczenie dla memory chat
async def chat_response_generator(prompt: str, model: str):
    """
    Asynchroniczny generator. Pobiera kawałki odpowiedzi od klienta
    Ollama i od razu przesyła je dalej (yield).
    """
    try:
        async with timeout_context(30.0):  # 30 second timeout
            async for chunk in await llm_client.generate_stream(
                model=model, prompt=prompt, system_prompt=""
            ):
                if not isinstance(chunk, dict):
                    continue
                chunk_dict = cast(Dict[str, Any], chunk)
                if "response" in chunk_dict:
                    yield chunk_dict["response"]
    except Exception as e:
        logger.error(f"Błąd podczas streamowania: {e}")
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


import json


@with_backpressure(max_concurrent=20)  # Ograniczenie dla memory chat
async def memory_chat_generator(request: MemoryChatRequest, db: AsyncSession):
    """
    Generator for streaming responses from the orchestrator.
    Każdy yield to linia NDJSON: {"text": ...}
    """
    try:
        logger.debug(
            f"Starting memory chat generator for session: {request.session_id}"
        )

        # Get a healthy orchestrator from the pool
        logger.debug("Getting healthy orchestrator from pool...")
        orchestrator = await orchestrator_pool.get_healthy_orchestrator()
        logger.debug(f"Orchestrator result: {orchestrator}")

        if not orchestrator:
            logger.warning("No healthy orchestrator available, queuing request")

            # Check if request_queue is properly initialized
            if request_queue is None:
                logger.error("Request queue is not initialized")
                yield json.dumps(
                    {
                        "text": "Service temporarily unavailable. Request queue not initialized.",
                        "success": False,
                    }
                ) + "\n"
                return

            try:
                request_id = await request_queue.enqueue_request(
                    user_command=request.message, session_id=request.session_id
                )
                yield json.dumps(
                    {
                        "text": "Service temporarily unavailable. Request queued for processing.",
                        "request_id": request_id,
                        "success": False,
                    }
                ) + "\n"
            except Exception as e:
                logger.error(f"Error enqueueing request: {e}")
                yield json.dumps(
                    {
                        "text": "Service temporarily unavailable. Failed to queue request.",
                        "success": False,
                    }
                ) + "\n"
            return

        # Process with orchestrator
        async with timeout_context(60.0):  # 60 second timeout for memory chat
            response = await orchestrator.process_command(
                user_command=request.message, session_id=request.session_id
            )

            if response.success:
                yield json.dumps(
                    {
                        "text": response.text or response.message,
                        "success": True,
                        "session_id": request.session_id,
                    }
                ) + "\n"
            else:
                yield json.dumps(
                    {
                        "text": response.error or "An error occurred",
                        "success": False,
                        "session_id": request.session_id,
                    }
                ) + "\n"

    except Exception as e:
        logger.error(f"Error in memory_chat_generator: {str(e)}", exc_info=True)
        yield json.dumps(
            {"text": f"Wystąpił błąd serwera: {str(e)}", "success": False}
        ) + "\n"


@router.post("/memory_chat")
async def chat_with_memory(
    request: MemoryChatRequest,
    db: AsyncSession = Depends(get_db),
    background_tasks: BackgroundTasks = None,
):
    """
    Endpoint for conversing with an agent that remembers conversation history.
    Każda linia odpowiedzi to poprawny JSON (NDJSON).
    """
    generator = memory_chat_generator(request, db)
    return StreamingResponse(generator, media_type="application/x-ndjson")


@router.post("/test_simple_chat")
async def test_simple_chat():
    """
    Simple test endpoint for basic chat functionality
    """
    return {"message": "Chat endpoint is working correctly"}
