import logging
import uuid
from typing import Any, Dict, List, Optional

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
)
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession  # type: ignore

from backend.agents.agent_registry import agent_registry
from backend.agents.interfaces import AgentType
from backend.agents.orchestrator_factory import create_orchestrator
from backend.api.food import get_db
from backend.config import settings
from backend.core.database import AsyncSessionLocal

# Import MMLW client
try:
    from backend.core.mmlw_embedding_client import mmlw_client

    MMLW_AVAILABLE = True
except ImportError:
    MMLW_AVAILABLE = False

from backend.core.perplexity_client import perplexity_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["agents"])


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


@router.post("/agents/agents/execute", response_model=AgentResponse)
async def execute_orchestrator_task(
    request: OrchestratorRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Główny endpoint do zlecania zadań.
    Orchestrator sam decyduje, który agent wykona zadanie.
    """
    session_id = request.session_id or str(uuid.uuid4())
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

        # Konwertuj AgentResponse na format oczekiwany przez endpoint
        return AgentResponse(
            success=agent_response.success,
            response=agent_response.text or agent_response.message,
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
        # Also return session_id on error so client can continue
        return AgentResponse(success=False, error=str(e), session_id=session_id)


@router.get("/agents", response_model=List[Dict[str, str]])
async def list_available_agents():
    """Zwraca listę wszystkich dostępnych intencji."""
    return [{"name": intent.value, "description": intent.value} for intent in AgentType]


@router.get("/mmlw/status")
async def get_mmlw_status():
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
async def initialize_mmlw():
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
async def test_mmlw_embedding():
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
        test_text = "To jest testowy tekst w języku polskim."
        embedding = await mmlw_client.embed_text(test_text)

        if embedding and len(embedding) == 768:
            return {
                "success": True,
                "message": "MMLW embedding test successful",
                "embedding_dimension": len(embedding),
                "test_text": test_text,
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
async def test_perplexity_api(query: str = Form(...)):
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
async def get_perplexity_status():
    """Sprawdza status Perplexity API"""
    return {
        "configured": perplexity_client.is_configured(),
        "available": perplexity_client.is_available,
        "api_key_present": bool(perplexity_client.api_key),
    }
