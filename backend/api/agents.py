from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional, Any

# Importujemy instancję orchestratora
from ..agents.orchestrator import orchestrator, IntentType
from ..agents.state import ConversationState

router = APIRouter()

class OrchestratorRequest(BaseModel):
    task: str

class AgentResponse(BaseModel):
    success: bool
    response: Optional[str] = None
    error: Optional[str] = None
    data: Optional[Any] = None

@router.post("/orchestrator/execute", response_model=AgentResponse)
async def execute_orchestrator_task(request: OrchestratorRequest):
    """
    Główny endpoint do zlecania zadań.
    Orchestrator sam decyduje, który agent wykona zadanie.
    """
    try:
        state = ConversationState()
        response = await orchestrator.process_command(request.task, state)
        return AgentResponse(
            success=True,
            response=str(response) if isinstance(response, (str, list)) else None,
            data=response if isinstance(response, list) else None
        )
    except Exception as e:
        return AgentResponse(
            success=False,
            error=str(e)
        )

@router.get("/agents", response_model=List[Dict[str, str]])
async def list_available_agents():
    """Zwraca listę wszystkich dostępnych intencji."""
    return [{"name": intent.name, "description": intent.value} for intent in IntentType]