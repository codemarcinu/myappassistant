import logging
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Form, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession  # type: ignore

from backend.agents.interfaces import AgentType
from backend.agents.orchestrator_factory import create_orchestrator
from backend.core.database import get_db_with_error_handling
from backend.infrastructure.database.database import get_db

# Import MMLW client
try:
    from backend.core.mmlw_embedding_client import mmlw_client

    MMLW_AVAILABLE = True
except ImportError:
    MMLW_AVAILABLE = False

from backend.core.perplexity_client import perplexity_client

logger = logging.getLogger(__name__)

# Simple router without prefixes
router = APIRouter()


class OrchestratorRequest(BaseModel):
    task: str
    session_id: Optional[str] = None
    conversation_state: Optional[Dict[str, Any]] = None
    agent_states: Optional[Dict[str, bool]] = None
    usePerplexity: Optional[bool] = False
    useBielik: Optional[bool] = True  # Domyślnie używamy Bielika


class AgentResponse(BaseModel):
    success: bool
    response: Optional[str] = None
    error: Optional[str] = None
    data: Optional[Any] = None
    session_id: str
    conversation_state: Optional[Dict[str, Any]] = None


@router.post("/execute", response_model=AgentResponse)
async def execute_orchestrator_task(
    request: OrchestratorRequest,
    db: AsyncSession = Depends(get_db),
) -> AgentResponse:
    """
    Główny endpoint do zlecania zadań.
    Orchestrator sam decyduje, który agent wykona zadanie.
    """
    import time

    start_time = time.time()
    session_id = request.session_id or str(uuid.uuid4())

    logger.info(
        "Agent task received",
        extra={
            "session_id": session_id,
            "task_length": len(request.task),
            "use_perplexity": request.usePerplexity,
            "use_bielik": request.useBielik,
            "agent_states": request.agent_states,
            "agent_event": "task_received",
        },
    )

    try:
        # Użyj fabryki do utworzenia orchestrator z wymaganymi zależnościami
        orchestrator = create_orchestrator(db)

        # The process_command method handles state retrieval and message history
        agent_response = await orchestrator.process_command(
            user_command=request.task,
            session_id=session_id,
            agent_states=request.agent_states,
            use_perplexity=request.usePerplexity,
            use_bielik=request.useBielik,
        )

        # Logowanie zakończenia przetwarzania przez agenta
        processing_time = (time.time() - start_time) * 1000  # w ms
        response_text = agent_response.text or agent_response.message or ""

        logger.info(
            "Agent task completed",
            extra={
                "session_id": session_id,
                "success": agent_response.success,
                "response_length": len(response_text),
                "processing_time_ms": int(processing_time),
                "agent_event": "task_completed",
                "has_error": bool(agent_response.error),
            },
        )

        # Konwertuj AgentResponse na format oczekiwany przez endpoint
        return AgentResponse(
            success=agent_response.success,
            response=response_text,
            error=agent_response.error,
            data=agent_response.data,
            session_id=session_id,
            conversation_state=(
                agent_response.data.get("state")
                if hasattr(agent_response, "data") and agent_response.data
                else None
            ),
        )
    except Exception as e:
        # Logowanie błędu
        processing_time = (time.time() - start_time) * 1000  # w ms
        logger.error(
            f"Agent task error: {str(e)}",
            exc_info=True,
            extra={
                "session_id": session_id,
                "error_type": type(e).__name__,
                "error_message": str(e),
                "processing_time_ms": int(processing_time),
                "agent_event": "task_error",
            },
        )
        # Also return session_id on error so client can continue
        return AgentResponse(success=False, error=str(e), session_id=session_id)


@router.post("/process_query", response_model=AgentResponse)
async def process_query(
    request: OrchestratorRequest,
    db: AsyncSession = Depends(get_db_with_error_handling),
) -> AgentResponse:
    """
    Endpoint do przetwarzania zapytań użytkownika.
    """
    import time

    start_time = time.time()
    session_id = request.session_id or str(uuid.uuid4())

    logger.info(
        "Query processing request received",
        extra={
            "session_id": session_id,
            "query_length": len(request.task),
            "agent_event": "query_received",
        },
    )

    try:
        # Użyj fabryki do utworzenia orchestrator z wymaganymi zależnościami
        orchestrator = create_orchestrator(db)

        # Use the process_query method
        agent_response = await orchestrator.process_query(
            query=request.task,
            session_id=session_id,
        )

        # Logowanie zakończenia przetwarzania
        processing_time = (time.time() - start_time) * 1000  # w ms
        response_text = agent_response.text or agent_response.message or ""

        logger.info(
            "Query processing completed",
            extra={
                "session_id": session_id,
                "success": agent_response.success,
                "response_length": len(response_text),
                "processing_time_ms": int(processing_time),
                "agent_event": "query_completed",
                "has_error": bool(agent_response.error),
            },
        )

        # Konwertuj AgentResponse na format oczekiwany przez endpoint
        return AgentResponse(
            success=agent_response.success,
            response=response_text,
            error=agent_response.error,
            data=agent_response.data,
            session_id=session_id,
            conversation_state=(
                agent_response.data.get("state")
                if hasattr(agent_response, "data") and agent_response.data
                else None
            ),
        )
    except Exception as e:
        # Logowanie błędu
        processing_time = (time.time() - start_time) * 1000  # w ms
        logger.error(
            f"Query processing error: {str(e)}",
            exc_info=True,
            extra={
                "session_id": session_id,
                "error_type": type(e).__name__,
                "error_message": str(e),
                "processing_time_ms": int(processing_time),
                "agent_event": "query_error",
            },
        )
        # Raise HTTPException for database connection errors
        if "DB connection error" in str(e) or "database" in str(e).lower():
            raise HTTPException(
                status_code=500,
                detail={
                    "error_code": "INTERNAL_SERVER_ERROR",
                    "message": "Database connection failed",
                    "session_id": session_id,
                },
            )
        # For other errors, return AgentResponse with success=False
        return AgentResponse(success=False, error=str(e), session_id=session_id)


@router.get("/agents", response_model=List[Dict[str, str]])
async def list_available_agents() -> List[Dict[str, str]]:
    """Zwraca listę wszystkich dostępnych intencji."""
    return [{"name": intent.value, "description": intent.value} for intent in AgentType]


@router.get("/mmlw/status")
async def get_mmlw_status() -> Dict[str, Any]:
    """Sprawdza stan modelu MMLW"""
    if not MMLW_AVAILABLE:
        return {
            "available": False,
            "error": "MMLW client not available - transformers library not installed",
        }

    try:
        status = await mmlw_client.health_check()
        return {"available": True, "status": status}
    except Exception as e:
        return {"available": False, "error": str(e)}


@router.post("/mmlw/initialize")
async def initialize_mmlw() -> Dict[str, Any]:
    """Inicjalizuje model MMLW"""
    if not MMLW_AVAILABLE:
        raise HTTPException(
            status_code=400,
            detail="MMLW client not available - transformers library not installed",
        )

    try:
        success = await mmlw_client.initialize()
        if success:
            return {"success": True, "message": "MMLW model initialized successfully"}
        else:
            raise HTTPException(
                status_code=500, detail="Failed to initialize MMLW model"
            )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error initializing MMLW model: {str(e)}"
        )


@router.post("/mmlw/test")
async def test_mmlw_embedding(text: str = Form(...)) -> Dict[str, Any]:
    """Testuje generowanie embeddingów przez model MMLW"""
    if not MMLW_AVAILABLE:
        raise HTTPException(
            status_code=400,
            detail="MMLW client not available - transformers library not installed",
        )

    try:
        if not mmlw_client.is_available():
            await mmlw_client.initialize()

        if not mmlw_client.is_available():
            raise HTTPException(
                status_code=500, detail="MMLW model not available after initialization"
            )

        # Test embedding
        embedding = await mmlw_client.embed_text(text)

        if embedding and len(embedding) == 768:
            return {
                "success": True,
                "message": "MMLW embedding test successful",
                "embedding_dimension": len(embedding),
                "text": text,
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Invalid embedding generated: expected 768 dimensions, got {len(embedding) if embedding else 0}",
            )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error testing MMLW embeddings: {str(e)}"
        )


@router.post("/perplexity/test")
async def test_perplexity_api(query: str = Form(...)) -> Dict[str, Any]:
    """Testuje Perplexity API"""
    try:
        if not perplexity_client.is_configured():
            raise HTTPException(
                status_code=400,
                detail="Perplexity API not configured - check PERPLEXITY_API_KEY",
            )

        # Test Perplexity search
        result = await perplexity_client.search(query, model="sonar-medium-online")

        if result.get("success"):
            return {
                "success": True,
                "message": "Perplexity API test successful",
                "query": query,
                "content_length": len(result.get("content", "")),
                "model": result.get("model"),
                "usage": result.get("usage"),
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Perplexity API test failed: {result.get('error', 'Unknown error')}",
            )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error testing Perplexity API: {str(e)}"
        )


@router.get("/perplexity/status")
async def get_perplexity_status() -> Dict[str, Any]:
    """Sprawdza status Perplexity API"""
    return {
        "configured": perplexity_client.is_configured(),
        "available": perplexity_client.is_available,
        "api_key_present": bool(perplexity_client.api_key),
    }
