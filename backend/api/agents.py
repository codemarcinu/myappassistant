from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel

# Importujemy instancję orchestratora
from ..agents.orchestrator import IntentType, orchestrator
from ..agents.state import ConversationState

router = APIRouter()


class OrchestratorRequest(BaseModel):
    task: str
    conversation_state: Optional[Dict[str, Any]] = None


class AgentResponse(BaseModel):
    success: bool
    response: Optional[str] = None
    error: Optional[str] = None
    data: Optional[Any] = None
    conversation_state: Optional[Dict[str, Any]] = None


@router.post("/orchestrator/execute", response_model=AgentResponse)
async def execute_orchestrator_task(request: OrchestratorRequest):
    """
    Główny endpoint do zlecania zadań.
    Orchestrator sam decyduje, który agent wykona zadanie.
    """
    try:
        # Przywracamy stan konwersacji z poprzedniego requestu lub tworzymy nowy
        state = (
            ConversationState.from_dict(request.conversation_state)
            if request.conversation_state
            else ConversationState()
        )

        # Dodajemy wiadomość użytkownika do historii
        state.add_message("user", request.task)

        # Przetwarzamy polecenie
        response = await orchestrator.process_command(request.task, state)

        # Dodajemy odpowiedź asystenta do historii
        if isinstance(response, str):
            state.add_message("assistant", response)

        return AgentResponse(
            success=True,
            response=str(response) if isinstance(response, (str, list)) else None,
            data=response if isinstance(response, list) else None,
            conversation_state=state.to_dict(),
        )
    except Exception as e:
        return AgentResponse(success=False, error=str(e))


@router.get("/agents", response_model=List[Dict[str, str]])
async def list_available_agents():
    """Zwraca listę wszystkich dostępnych intencji."""
    return [{"name": intent.name, "description": intent.value} for intent in IntentType]
