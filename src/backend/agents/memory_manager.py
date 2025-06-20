import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from backend.agents.interfaces import BaseAgent, IMemoryManager, MemoryContext

logger = logging.getLogger(__name__)


class MemoryManager(IMemoryManager):
    """Implementation of memory management for conversation context"""

    def __init__(self):
        self._contexts: Dict[str, MemoryContext] = {}
        self._max_contexts: int = 1000
        self._cleanup_threshold: int = 800

    async def store_context(self, context: MemoryContext) -> None:
        """Store context for later retrieval"""
        if len(self._contexts) >= self._max_contexts:
            await self._cleanup_old_contexts()

        self._contexts[context.session_id] = context
        context.last_updated = datetime.now()
        logger.debug(f"Stored context for session: {context.session_id}")

    async def retrieve_context(self, session_id: str) -> Optional[MemoryContext]:
        """Retrieve context for session if it exists"""
        context = self._contexts.get(session_id)
        if context:
            context.last_updated = datetime.now()
            logger.debug(f"Retrieved context for session: {session_id}")
        return context

    async def get_context(self, session_id: str) -> MemoryContext:
        """Get or create context for session"""
        context = await self.retrieve_context(session_id)
        if context is None:
            # Create new context if it doesn't exist
            context = MemoryContext(session_id)
            await self.store_context(context)
            logger.debug(f"Created new context for session: {session_id}")
        return context

    async def update_context(
        self, context: MemoryContext, new_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """Update existing context with new data"""
        if context.session_id in self._contexts:
            # Add new data to context history if provided
            if new_data:
                if not hasattr(context, "history"):
                    context.history = []
                context.history.append(
                    {"timestamp": datetime.now().isoformat(), "data": new_data}
                )

            self._contexts[context.session_id] = context
            context.last_updated = datetime.now()
            logger.debug(f"Updated context for session: {context.session_id}")

    async def clear_context(self, session_id: str) -> None:
        """Clear context for session"""
        if session_id in self._contexts:
            del self._contexts[session_id]
            logger.debug(f"Cleared context for session: {session_id}")

    async def _cleanup_old_contexts(self) -> None:
        """Remove old contexts when limit is reached"""
        if len(self._contexts) <= self._cleanup_threshold:
            return

        # Sort by last_updated and remove oldest
        sorted_contexts = sorted(
            self._contexts.items(), key=lambda x: x[1].last_updated, reverse=True
        )

        # Keep only the newest contexts
        contexts_to_keep = sorted_contexts[: self._cleanup_threshold]
        self._contexts = dict(contexts_to_keep)

        logger.info(
            f"Cleaned up {len(sorted_contexts) - self._cleanup_threshold} old contexts"
        )

    async def register_agent_state(
        self,
        context: MemoryContext,
        agent_type: str,
        agent: BaseAgent,
        state: Dict[str, Any],
    ) -> None:
        """Register agent state in context"""
        if not hasattr(context, "active_agents"):
            context.active_agents = {}

        context.active_agents[agent_type] = {
            "agent": agent,
            "state": state,
            "timestamp": datetime.now().isoformat(),
        }

    async def get_all_contexts(self) -> Dict[str, MemoryContext]:
        """Get all stored contexts (for debugging/monitoring)"""
        return self._contexts.copy()

    async def get_context_stats(self) -> Dict[str, Any]:
        """Get memory manager statistics"""
        return {
            "total_contexts": len(self._contexts),
            "max_contexts": self._max_contexts,
            "cleanup_threshold": self._cleanup_threshold,
            "oldest_context": min(
                (ctx.last_updated for ctx in self._contexts.values()), default=None
            ),
            "newest_context": max(
                (ctx.last_updated for ctx in self._contexts.values()), default=None
            ),
        }
