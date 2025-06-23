import logging
from typing import Any, Dict, List

from backend.agents.interfaces import MemoryContext

logger = logging.getLogger(__name__)


class MemoryManager:
    """Core memory management for conversation context"""

    def __init__(self) -> None:
        self._contexts: Dict[str, MemoryContext] = {}

    def get_or_create_context(self, session_id: str) -> MemoryContext:
        """Get existing context or create new one"""
        if session_id not in self._contexts:
            self._contexts[session_id] = MemoryContext(session_id)
            logger.info(f"Created new memory context for session: {session_id}")
        return self._contexts[session_id]

    def update_context(self, session_id: str, data: Dict[str, Any]) -> None:
        """Update context with new data"""
        context = self.get_or_create_context(session_id)
        context.history.append(
            {"timestamp": context.last_updated.isoformat(), "data": data}
        )
        context.last_updated = context.last_updated

    def get_context_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Get conversation history for session"""
        context = self._contexts.get(session_id)
        return context.history if context else []

    def clear_context(self, session_id: str) -> None:
        """Clear context for session"""
        if session_id in self._contexts:
            del self._contexts[session_id]
            logger.info(f"Cleared memory context for session: {session_id}")

    def get_all_contexts(self) -> Dict[str, MemoryContext]:
        """Get all contexts (for debugging)"""
        return self._contexts.copy()
