from typing import Any, Dict

from ..core.sqlalchemy_compat import AsyncSession
from ..core.vector_store import VectorStore


class AgentContainer:
    """Dependency Injection container for agent dependencies"""

    def __init__(self):
        self._services: Dict[str, Any] = {}

    def register(self, name: str, service: Any) -> None:
        """Register a service in the container"""
        self._services[name] = service

    def get(self, name: str) -> Any:
        """Get a registered service"""
        return self._services.get(name)

    def register_core_services(self, db: AsyncSession) -> None:
        """Register core services used by agents"""
        from ..core.hybrid_llm_client import hybrid_llm_client
        from ..core.profile_manager import ProfileManager
        from .adapters.alert_service import AlertService
        from .adapters.error_handler import ErrorHandler
        from .adapters.fallback_manager import FallbackManager
        from .interfaces import IAlertService, IErrorHandler, IFallbackProvider

        self.register("db", db)
        self.register("profile_manager", ProfileManager(db))
        self.register("llm_client", hybrid_llm_client)
        self.register("vector_store", VectorStore())

        # Register interface implementations
        self.register(IErrorHandler, ErrorHandler("global"))
        self.register(IAlertService, AlertService("global"))
        self.register(IFallbackProvider, FallbackManager())

        # Initialize vector store if needed
        if hasattr(self, "vector_store") and self.vector_store is None:
            self.vector_store = VectorStore()
