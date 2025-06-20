import logging

logger = logging.getLogger(__name__)

from typing import Any, Dict, cast

from fastapi import APIRouter, BackgroundTasks, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.infrastructure.database.database import get_db
from src.backend.orchestrator_management.orchestrator_pool import orchestrator_pool
from src.backend.orchestrator_management.request_queue import request_queue

from ..config import settings
from ..core.llm_client import llm_client

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


async def chat_response_generator(prompt: str, model: str):
    """
    Asynchroniczny generator. Pobiera kawałki odpowiedzi od klienta
    Ollama i od razu przesyła je dalej (yield).
    """
    try:
        async for chunk in await llm_client.generate_stream(
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


import json


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

        logger.debug(f"Processing command with orchestrator: {request.message}")
        agent_response = await orchestrator.process_command(
            user_command=request.message,
            session_id=request.session_id,
            agent_states=None,
            use_perplexity=request.usePerplexity,  # Przekazujemy flagę dalej
        )
        logger.debug(f"Agent response received: {agent_response}")
        logger.debug(f"Agent response type: {type(agent_response)}")
        logger.debug(f"Agent response attributes: {dir(agent_response)}")
        logger.debug(f"Agent response text: {getattr(agent_response, 'text', None)}")
        logger.debug(
            f"Agent response text_stream: {getattr(agent_response, 'text_stream', None)}"
        )
        logger.debug(f"Agent response data: {getattr(agent_response, 'data', None)}")
        logger.debug(
            f"Agent response success: {getattr(agent_response, 'success', None)}"
        )

        # Obsługa streamu tekstowego
        if hasattr(agent_response, "text_stream") and agent_response.text_stream:
            logger.debug("Using text stream from agent response")
            # Sprawdź czy text_stream jest async generatorem
            if hasattr(agent_response.text_stream, "__aiter__"):
                async for chunk in agent_response.text_stream:
                    # Każdy chunk zamieniamy na NDJSON z nową linią
                    yield json.dumps({"text": chunk, "success": True}) + "\n"
            else:
                # Jeśli text_stream nie jest async generatorem, traktuj jako zwykły tekst
                logger.debug("text_stream is not an async generator, treating as text")
                yield json.dumps(
                    {
                        "text": str(agent_response.text_stream),
                        "success": agent_response.success,
                    }
                ) + "\n"
        elif hasattr(agent_response, "text") and agent_response.text:
            logger.debug("Using text from agent response")
            yield json.dumps(
                {
                    "text": agent_response.text,
                    "success": agent_response.success,
                    "data": agent_response.data or {},
                }
            ) + "\n"
        elif hasattr(agent_response, "data") and agent_response.data:
            logger.debug("Using data from agent response")
            yield json.dumps(
                {
                    "text": agent_response.data.get("message", "Response received"),
                    "success": agent_response.success,
                    "data": agent_response.data,
                }
            ) + "\n"
        else:
            logger.debug("Using fallback response")
            yield json.dumps(
                {
                    "text": "No response generated",
                    "success": getattr(agent_response, "success", False),
                    "data": {},
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


@router.post("/test_simple")
async def test_simple_chat():
    """
    Simple test endpoint that doesn't use the orchestrator
    """
    return {"response": "Test endpoint working", "success": True}
