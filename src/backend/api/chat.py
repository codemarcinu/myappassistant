import asyncio
import json
import logging
import os
from typing import Any, AsyncGenerator, Dict, cast

from fastapi import APIRouter, BackgroundTasks, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.async_patterns import (CircuitBreakerConfig, timeout_context,
                                         with_backpressure,
                                         with_circuit_breaker)
from backend.core.llm_client import llm_client
from backend.infrastructure.database.database import get_db
from backend.orchestrator_management.orchestrator_pool import orchestrator_pool
from backend.orchestrator_management.request_queue import request_queue

router = APIRouter()
logger = logging.getLogger(__name__)


def get_selected_model() -> str:
    """Get the selected model from config file or fallback to default"""
    try:
        # Path to the LLM settings file
        llm_settings_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "..",
            "data",
            "config",
            "llm_settings.json",
        )

        if os.path.exists(llm_settings_path):
            with open(llm_settings_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                selected_model = data.get("selected_model", "")
                if selected_model:
                    logger.info(f"Using selected model from config: {selected_model}")
                    return selected_model

        # Fallback to hardcoded default
        fallback_default = "SpeakLeash/bielik-4.5b-v3.0-instruct:Q8_0"
        logger.info(
            f"No valid selected model in config, using fallback: {fallback_default}"
        )
        return fallback_default

    except Exception as e:
        logger.warning(f"Error reading selected model from config: {e}")
        fallback_default = "SpeakLeash/bielik-4.5b-v3.0-instruct:Q8_0"
        logger.info(f"Using fallback default model: {fallback_default}")
        return fallback_default


class ChatRequest(BaseModel):
    prompt: str
    model: str | None = None  # Pole opcjonalne


class ChatResponse(BaseModel):
    response: str
    model: str


class WebSocketResponse(BaseModel):
    message: str
    type: str = "message"


class MemoryChatRequest(BaseModel):
    message: str
    session_id: str  # Kluczowe do śledzenia i odróżniania konwersacji
    usePerplexity: bool = False  # Nowe pole
    useBielik: bool = True  # Domyślnie używamy Bielika
    agent_states: Dict[str, bool] = {}  # Stany agentów


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
async def chat_response_generator(prompt: str, model: str) -> AsyncGenerator[str, None]:
    """
    Asynchroniczny generator. Pobiera kawałki odpowiedzi od klienta
    Ollama i od razu przesyła je dalej (yield).
    """
    try:
        async with timeout_context(30.0):  # 30 second timeout
            async for chunk in llm_client.generate_stream_from_prompt(
                model=model, prompt=prompt, system_prompt=""
            ):
                if not isinstance(chunk, dict):
                    continue
                chunk_dict = cast(Dict[str, Any], chunk)
                if "response" in chunk_dict:
                    yield chunk_dict["response"]
    except Exception as e:
        logger.error(f"Błąd podczas streamowania: {e}")
        yield f"Wystąpił błąd serwera: {str(e)}"
    # Jeśli nie było żadnego yielda (np. pusta odpowiedź)
    yield "[Brak odpowiedzi od modelu]"


@router.post("/chat")
async def chat_with_model(request: Request) -> StreamingResponse:
    body = await request.json()
    prompt = body.get("prompt")
    model = body.get("model") or get_selected_model()
    return StreamingResponse(
        chat_response_generator(prompt, model), media_type="text/plain"
    )


@with_backpressure(max_concurrent=20)  # Ograniczenie dla memory chat
async def memory_chat_generator(
    request: MemoryChatRequest, db: AsyncSession
) -> AsyncGenerator[str, None]:
    """
    Generator for streaming responses from the orchestrator.
    Każdy yield to linia NDJSON: {"text": ...}
    """
    start_time = asyncio.get_event_loop().time()  # Czas rozpoczęcia przetwarzania
    try:
        # Rozszerzone logowanie czatu
        logger.info(
            "Chat request received",
            extra={
                "session_id": request.session_id,
                "message_length": len(request.message),
                "use_perplexity": request.usePerplexity,
                "use_bielik": request.useBielik,
                "agent_states": request.agent_states,
                "chat_event": "request_received",
            },
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

        # Process with orchestrator using streaming
        async with timeout_context(60.0):  # 60 second timeout for memory chat
            # Create a list to collect chunks
            chunks = []

            # Define the callback function
            def handle_chunk(chunk) -> None:
                chunks.append(chunk)

            # Process the command with streaming
            response = await orchestrator.process_command(
                user_command=request.message,
                session_id=request.session_id,
                agent_states=request.agent_states,
                use_perplexity=request.usePerplexity,
                use_bielik=request.useBielik,
                stream=True,
                stream_callback=handle_chunk,
            )

            # If no chunks were collected, use the response
            if not chunks and response:
                response_text = response.text or ""
                logger.info(
                    "Chat response completed",
                    extra={
                        "session_id": request.session_id,
                        "response_length": len(response_text),
                        "success": response.success,
                        "chat_event": "response_completed",
                        "processing_time_ms": int(
                            (asyncio.get_event_loop().time() - start_time) * 1000
                        ),
                    },
                )
                yield json.dumps(
                    {
                        "text": response_text,
                        "success": response.success,
                        "session_id": request.session_id,
                        "data": response.data,
                    }
                ) + "\n"
            else:
                # Stream all collected chunks
                total_response_length = sum(
                    len(chunk.get("text", "")) for chunk in chunks
                )
                logger.info(
                    "Chat streaming response completed",
                    extra={
                        "session_id": request.session_id,
                        "chunks_count": len(chunks),
                        "total_response_length": total_response_length,
                        "success": all(chunk.get("success", True) for chunk in chunks),
                        "chat_event": "streaming_completed",
                        "processing_time_ms": int(
                            (asyncio.get_event_loop().time() - start_time) * 1000
                        ),
                    },
                )
                for chunk in chunks:
                    yield json.dumps(
                        {
                            "text": chunk.get("text", ""),
                            "success": chunk.get("success", True),
                            "session_id": request.session_id,
                            "data": chunk.get("data"),
                        }
                    ) + "\n"

    except asyncio.TimeoutError:
        logger.error(
            "Memory chat processing timed out",
            extra={
                "session_id": request.session_id,
                "chat_event": "timeout",
            },
        )
        yield json.dumps(
            {"text": "Processing timed out. Please try again.", "success": False}
        ) + "\n"
    except Exception as e:
        logger.error(
            f"An error occurred during memory chat processing: {e}",
            exc_info=True,
            extra={
                "session_id": request.session_id,
                "chat_event": "error",
                "error_message": str(e),
            },
        )
        yield json.dumps(
            {"text": f"An error occurred: {str(e)}", "success": False}
        ) + "\n"
    finally:
        if orchestrator:
            orchestrator_pool.release_orchestrator(orchestrator)
            logger.debug(
                f"Orchestrator {orchestrator.orchestrator_id} released from pool."
            )


@router.post("/memory_chat")
async def chat_with_memory(
    request: MemoryChatRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    # Dodaj zadanie w tle, aby monitorować i usuwać stare sesje, jeśli to konieczne
    # background_tasks.add_task(cleanup_old_sessions, request.session_id)
    return StreamingResponse(
        memory_chat_generator(request, db), media_type="application/x-ndjson"
    )


@router.post("/test_simple_chat")
async def test_simple_chat() -> Dict[str, Any]:
    return {"message": "Test simple chat endpoint"}


@router.post("/test_chat_simple")
async def test_chat_simple(request: ChatRequest) -> Dict[str, Any]:
    # Placeholder for actual chat logic
    return {"reply": f"You said: {request.prompt}", "model": request.model}
