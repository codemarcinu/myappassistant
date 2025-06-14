from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict

# Importujemy instancję orchestratora zamiast konkretnego agenta
from ..agents.orchestrator import orchestrator
from ..agents.base_agent import AgentResponse

router = APIRouter()

class OrchestratorRequest(BaseModel):
    task: str

@router.post("/orchestrator/execute", response_model=AgentResponse)
async def execute_orchestrator_task(request: OrchestratorRequest):
    """
    Główny endpoint do zlecania zadań.
    Orchestrator sam decyduje, który agent wykona zadanie.
    """
    response = await orchestrator.route_task(request.task)

    if not response.success:
        # Używamy innego kodu błędu, jeśli agenta po prostu nie znaleziono
        status_code = 404 if "Nie znaleziono" in response.error else 500
        raise HTTPException(status_code=status_code, detail=response.error)

    return response

@router.get("/agents", response_model=List[Dict[str, str]])
async def list_available_agents():
    """Zwraca listę wszystkich zarejestrowanych agentów i ich opisy."""
    return orchestrator.get_available_agents()