import logging
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from backend.agents.agent_router import AgentRouter
from backend.agents.intent_detector import SimpleIntentDetector
from backend.agents.memory_manager import MemoryManager
from backend.agents.orchestrator import Orchestrator
from backend.core.profile_manager import ProfileManager
from backend.core.response_generator import ResponseGenerator

from .agent_factory import AgentFactory
from .agent_registry import AgentRegistry


def create_orchestrator(db: AsyncSession) -> Orchestrator:
    """
    Fabryka tworząca instancję Orchestrator z wymaganymi zależnościami.

    Args:
        db: Sesja bazy danych (AsyncSession)

    Returns:
        Instancja Orchestrator
    """
    logger = logging.getLogger(__name__)

    # Utwórz menedżer profilów
    profile_manager = ProfileManager(db)
    logger.debug("ProfileManager created")

    # Utwórz detektor intencji
    intent_detector = SimpleIntentDetector()
    logger.debug("SimpleIntentDetector created")

    # Utwórz rejestr agentów i fabrykę
    agent_registry = AgentRegistry()
    agent_factory = AgentFactory(agent_registry=agent_registry)
    logger.debug("AgentRegistry and AgentFactory created")

    # Utwórz router agentów
    agent_router = AgentRouter()
    logger.debug("AgentRouter created")

    # Utwórz menedżera pamięci
    memory_manager = MemoryManager()
    logger.debug("MemoryManager created")

    # Utwórz generator odpowiedzi
    response_generator = ResponseGenerator()
    logger.debug("ResponseGenerator created")

    # Utwórz i zwróć orchestrator
    orchestrator = Orchestrator(
        db_session=db,
        profile_manager=profile_manager,
        intent_detector=intent_detector,
        agent_router=agent_router,
        memory_manager=memory_manager,
        response_generator=response_generator,
    )
    logger.debug("Orchestrator created successfully")

    return orchestrator
