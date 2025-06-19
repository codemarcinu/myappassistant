from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.agents.enhanced_orchestrator import EnhancedOrchestrator
# from src.backend.agents.intent_detector import SimpleIntentDetector # No longer needed
from src.backend.agents.router_service import AgentRouter
from src.backend.agents.agent_factory import AgentFactory
from src.backend.agents.agent_registry import AgentRegistry
from src.backend.core.memory import MemoryManager
from src.backend.core.profile_manager import ProfileManager
from src.backend.core.response_generator import ResponseGenerator


def create_enhanced_orchestrator(db: AsyncSession) -> EnhancedOrchestrator:
    """
    Fabryka tworząca instancję EnhancedOrchestrator z wymaganymi zależnościami.

    Args:
        db: Sesja bazy danych (AsyncSession)

    Returns:
        Instancja EnhancedOrchestrator
    """
    # Utwórz menedżer profilów
    profile_manager = ProfileManager(db)

    # Detektor intencji jest teraz zarządzany wewnętrznie przez EnhancedOrchestrator

    # Utwórz rejestr agentów i fabrykę
    agent_registry = AgentRegistry()
    agent_factory = AgentFactory(agent_registry=agent_registry)
    
    # Utwórz router agentów
    agent_router = AgentRouter(agent_factory=agent_factory, agent_registry=agent_registry)

    # Utwórz menedżera pamięci
    memory_manager = MemoryManager()

    # Utwórz generator odpowiedzi
    response_generator = ResponseGenerator()

    # Utwórz i zwróć orchestrator
    return EnhancedOrchestrator(
        db=db,
        profile_manager=profile_manager,
        # intent_detector parameter removed as it's now managed internally
        agent_router=agent_router,
        memory_manager=memory_manager,
        response_generator=response_generator,
    )
